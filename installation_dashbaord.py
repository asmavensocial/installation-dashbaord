import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import re
import base64

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="AS Maven Installation Dashboard", layout="wide")

# ----------------------------
# Load Excel
# ----------------------------
try:
    df = pd.read_excel("Installation Data (Responses).xlsx")
except FileNotFoundError:
    st.error("❌ Excel file not found! Please make sure it's named 'Installation Data (Responses).xlsx' and is in the same folder.")
    st.stop()

# ----------------------------
# Clean column names
# ----------------------------
def clean_column(col_name):
    return (
        str(col_name)
        .replace('\n', ' ')
        .replace('\r', '')
        .replace('\xa0', ' ')
        .strip()
    )

df.columns = [clean_column(col) for col in df.columns]

# ----------------------------
# Required columns
# ----------------------------
required_columns = [
    'Timestamp', 'MavenCode', 'Partner Store Name', 'Store code', 'Store Name',
    'State', 'City', 'Have you completed the installation at the store?',
    'Store image - Front (With Date and Time)',
    'Before work photo (With Date and Time)',
    'After work photo (With Date and Time)',
    'Reporting form (With Date and Time)'
]

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error("⚠️ Missing required columns in Excel file:")
    for col in missing_columns:
        st.write(f"- {col}")
    st.stop()

# ----------------------------
# Title and Summary
# ----------------------------
st.title("AS Maven Store Installation Dashboard - Project Infiniti")
st.markdown("Interactive dashboard showing installation status, site details, and progress with photos.")
st.markdown("---")

# ----------------------------
# KPIs
# ----------------------------
total_stores = len(df)
completed_count = df['Have you completed the installation at the store?'].astype(str).str.upper().value_counts().get('YES', 0)
not_completed_count = df['Have you completed the installation at the store?'].astype(str).str.upper().value_counts().get('NO', 0)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stores", 842)
col2.metric("Stores Completed", completed_count)
col3.metric("Not Deployed", not_completed_count)
col4.metric("Pending", 842 - (completed_count + not_completed_count))

completion_rate = (completed_count / total_stores) * 100 if total_stores > 0 else 0
st.progress(int(completion_rate))
st.caption(f"✅ Installation Progress: {completion_rate:.1f}% completed")
st.markdown("---")

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("🔍 Filters")
states = st.sidebar.multiselect("Select State(s)", df['State'].dropna().unique())
cities = st.sidebar.multiselect("Select City(s)", df['City'].dropna().unique())
partners = st.sidebar.multiselect("Select Partner(s)", df['Partner Store Name'].dropna().unique())

filtered_df = df.copy()
if states:
    filtered_df = filtered_df[filtered_df['State'].isin(states)]
if cities:
    filtered_df = filtered_df[filtered_df['City'].isin(cities)]
if partners:
    filtered_df = filtered_df[filtered_df['Partner Store Name'].isin(partners)]

# ----------------------------
# Inline Bar Graph – Installation Status by State
# ----------------------------
if 'Reason' not in filtered_df.columns:
    filtered_df['Reason'] = "Not mentioned"

# Normalize Yes/No responses
filtered_df['Installation Status'] = (
    filtered_df['Have you completed the installation at the store?']
    .astype(str)
    .str.strip()
    .str.lower()
    .map({'yes': 'Yes', 'no': 'No'})
)

# Handle missing or unexpected values
filtered_df['Installation Status'] = filtered_df['Installation Status'].fillna('Unknown')

# Group cleanly for bar chart
grouped_state = (
    filtered_df.groupby(['State', 'Installation Status'])
    .size()
    .reset_index(name='Count')
)

# Remove NaN or empty states
grouped_state = grouped_state[grouped_state['State'].notna() & (grouped_state['State'] != '')]


inline_bar = px.bar(
    grouped_state,
    x='State',
    y='Count',
    color='Installation Status',
    barmode='group',   # or 'stack' if you prefer
    text_auto=True,
    title="Installation Status by State (Inline View)"
)

inline_bar.update_layout(
    xaxis_title="State",
    yaxis_title="Number of Stores",
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(inline_bar, use_container_width=True)


# ----------------------------
# Installation Status Pie Chart
# ----------------------------
status_fig = px.pie(
    filtered_df,
    names='Have you completed the installation at the store?',
    title="Installation Status Distribution",
    hole=0.4
)
st.plotly_chart(status_fig, use_container_width=True)

# ----------------------------
# 📋 Store Data Table Section
# ----------------------------
st.header("📊 Store Data Details")
store_table = filtered_df[['MavenCode', 'Partner Store Name', 'Store code', 'Store Name', 'State', 'City', 'Have you completed the installation at the store?']]
st.dataframe(store_table, use_container_width=True)

# ----------------------------
# ❌ Not Deployed Store Details
# ----------------------------
st.header("📊 Not Deployed Store Details")
not_deployed_df = filtered_df[filtered_df['Have you completed the installation at the store?'].astype(str).str.upper() == 'NO']
if 'Reason' in not_deployed_df.columns:
    not_deployed_table = not_deployed_df[['MavenCode', 'Store Name', 'State', 'City', 'Reason']]
else:
    not_deployed_table = not_deployed_df[['MavenCode', 'Store Name', 'State', 'City']]
st.dataframe(not_deployed_table, use_container_width=True)
st.markdown("---")

# ----------------------------
# Helper: Convert Google Drive URLs properly
# ----------------------------
def convert_drive_url(url):
    """Convert a Google Drive share link into a direct-viewable image URL."""
    if pd.isna(url) or not str(url).strip():
        return None
    url = str(url).strip()
    match = re.search(r"[-\w]{25,}", url)
    if match:
        file_id = match.group(0)
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    elif any(ext in url for ext in [".jpg", ".jpeg", ".png", ".webp", "lh3.googleusercontent.com"]):
        return url
    return None

@st.cache_data(show_spinner=False)
def fetch_image_base64(url):
    """Fetch and cache image as base64 for fast rendering."""
    try:
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            encoded = base64.b64encode(response.content).decode()
            mime_type = response.headers.get("Content-Type", "image/jpeg")
            return f"data:{mime_type};base64,{encoded}"
    except Exception:
        pass
    return None

# ----------------------------
# 📸 Store Images Section (With Reporting Form)
# ----------------------------
st.header("📸 Store Images")

for _, row in filtered_df.iterrows():
    store_name = str(row.get("Store Name", "")).strip()
    partner_name = str(row.get("Partner Store Name", "")).strip()
    city = str(row.get("City", "Unknown City")).strip() or "Unknown City"

    if not store_name or store_name.lower() == "nan":
        store_name = partner_name if partner_name else "Unnamed Store"

    st.markdown(f"### 🏬 {store_name} – {city}")

    image_columns = [
        ("Store image - Front (With Date and Time)", "Store Front"),
        ("Reporting form (With Date and Time)", "Reporting Form"),
        ("Before work photo (With Date and Time)", "Before Installation"),
        ("After work photo (With Date and Time)", "After Installation"),
    ]

    cols = st.columns(len(image_columns))

    for col, (col_name, label) in zip(cols, image_columns):
        img_url = convert_drive_url(row.get(col_name))
        with col:
            if img_url:
                img_data = fetch_image_base64(img_url)
                if img_data:
                    st.markdown(
                        f"""
                        <div style="text-align:center;">
                            <a href="{img_url}" target="_blank">
                                <img src="{img_data}" style="width:100%;border-radius:10px;border:1px solid #444;object-fit:cover;height:200px;"/>
                            </a>
                            <p style="font-size:13px;color:#ccc;">{label}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info(f"⚠️ {label}: Image not accessible or invalid link.")
            else:
                st.info(f"❌ {label}: Image link missing or invalid.")
    st.markdown("---")
