import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import re
import base64
from PIL import Image
import os

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="AS Maven Installation Dashboard", layout="wide")

# ----------------------------
# Cached Data Load
# ----------------------------
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel("Maven-data-installation.xlsx")
    df.columns = [str(c).replace('\n', ' ').replace('\r', '').replace('\xa0', ' ').strip() for c in df.columns]
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Excel file not found! Please make sure 'Maven-data-installation.xlsx' is in the same folder.")
    st.stop()

# ----------------------------
# ✨ Header Section (Balanced, Professional Look)
# ----------------------------
col_logo, col_title = st.columns([0.15, 0.85])
with col_logo:
    try:
        logo = Image.open("maven-logo.jpeg")
        st.image(logo, width=90)
    except:
        st.write("🧩 AS Maven")
with col_title:
    st.markdown(
        """
        <h2 style='margin-bottom:0;color:#f5f5f5;'>AS Maven Store Installation Dashboard</h2>
        <p style='margin-top:4px;font-size:18px;color:#aaa;'>Project Infiniti</p>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr style='margin-top:5px;margin-bottom:20px;border:1px solid #444;'/>", unsafe_allow_html=True)

# ----------------------------
# Validate Columns
# ----------------------------
required_columns = [
    'Timestamp', 'MavenCode', 'Partner Store Name', 'Store code', 'State', 'City',
    'Have you completed the installation at the store?',
    'Store image - Front (With Date and Time)',
    'After work photo (With Date and Time)',
    'Reporting form (With Date and Time)'
]
missing = [c for c in required_columns if c not in df.columns]
if missing:
    st.error("⚠️ Missing required columns in Excel file:")
    for c in missing:
        st.write(f"- {c}")
    st.stop()

# ----------------------------
# KPIs
# ----------------------------
st.markdown("### 📈 Installation Summary")

total_stores = len(df)
completed = df['Have you completed the installation at the store?'].astype(str).str.upper().value_counts().get('YES', 0)
not_completed = df['Have you completed the installation at the store?'].astype(str).str.upper().value_counts().get('NO', 0)
pending = total_stores - (completed + not_completed)
rate = (completed / total_stores) * 100 if total_stores > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stores", total_stores)
col2.metric("Stores Completed", completed)
col3.metric("Not Deployed", not_completed)
col4.metric("Pending", pending)

st.progress(int(rate))
st.caption(f"✅ Installation Progress: {rate:.1f}% completed")
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
# Installation Status by State
# ----------------------------
filtered_df['Installation Status'] = (
    filtered_df['Have you completed the installation at the store?']
    .astype(str)
    .str.strip()
    .str.lower()
    .map({'yes': 'Yes', 'no': 'No'})
    .fillna('Unknown')
)

grouped_state = (
    filtered_df.groupby(['State', 'Installation Status'])
    .size()
    .reset_index(name='Count')
)
grouped_state = grouped_state[grouped_state['State'].notna() & (grouped_state['State'] != '')]

inline_bar = px.bar(
    grouped_state,
    x='State', y='Count', color='Installation Status',
    barmode='group', text_auto=True,
    title="Installation Status by State"
)
inline_bar.update_layout(
    xaxis_title="State", yaxis_title="Number of Stores",
    template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(inline_bar, use_container_width=True)

# ----------------------------
# Installation Status Pie Chart
# ----------------------------
status_fig = px.pie(
    filtered_df, names='Have you completed the installation at the store?',
    title="Installation Status Distribution", hole=0.4
)
st.plotly_chart(status_fig, use_container_width=True)

# ----------------------------
# Store Data Table
# ----------------------------
st.header("📊 Store Data Details")
st.dataframe(
    filtered_df[['MavenCode', 'Partner Store Name', 'Store code', 'State', 'City', 'Have you completed the installation at the store?']],
    use_container_width=True
)

# ----------------------------
# Not Deployed Stores
# ----------------------------
status_col = None
for col in df.columns:
    if "installation" in col.lower() and "store" in col.lower():
        status_col = col
        break

if status_col:
    not_deployed = df[df[status_col].str.lower() != "yes"]
    required_cols = [
        "MavenCode", "Store code", "Partner Store Name", "State", "City", "If installation not done, Reason ?"
    ]
    existing = [c for c in required_cols if c in not_deployed.columns]
    rename = {"If installation not done, Reason ?": "Reason", "Store code": "Store Code"}
    st.markdown("## 📍 Not Deployed Store Details")
    st.dataframe(not_deployed[existing].rename(columns=rename), use_container_width=True)

# ----------------------------
# Helper: Google Drive URL Converter + Cached Image Fetch
# ----------------------------
def convert_drive_url(url):
    if pd.isna(url) or not str(url).strip():
        return None
    url = str(url).strip()
    match = re.search(r"[-\w]{25,}", url)
    if match:
        return f"https://drive.google.com/uc?export=view&id={match.group(0)}"
    elif any(ext in url for ext in [".jpg", ".jpeg", ".png", ".webp", "lh3.googleusercontent.com"]):
        return url
    return None

@st.cache_data(show_spinner=False)
def fetch_image_base64(url):
    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            encoded = base64.b64encode(response.content).decode()
            mime = response.headers.get("Content-Type", "image/jpeg")
            return f"data:{mime};base64,{encoded}"
    except Exception:
        pass
    return None

# ----------------------------
# 📸 Store Images (Dynamic Limit)
# ----------------------------
st.header("📸 Store Images")

if len(filtered_df) > 20:
    view_option = st.radio("Select view limit:", ["Preview 20", "Show All"], horizontal=True)
    max_images = 20 if view_option == "Preview 20" else len(filtered_df)
else:
    max_images = len(filtered_df)

for i, (_, row) in enumerate(filtered_df.iterrows()):
    if i >= max_images:
        break

    partner = str(row.get("Partner Store Name", "Unknown Partner"))
    state = str(row.get("State", "Unknown State"))
    st.markdown(f"### 🏬 {partner} – {state}")

    image_columns = [
        ("Store image - Front (With Date and Time)", "Store Front"),
        ("Reporting form (With Date and Time)", "Reporting Form"),
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
                        """, unsafe_allow_html=True
                    )
                else:
                    st.info(f"⚠️ {label}: Image not accessible.")
            else:
                st.info(f"❌ {label}: Image link missing.")
    st.markdown("---")
