import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="AS Maven Store Branding Dashboard", layout="wide")

# ----------------------------
# Load Excel
# ----------------------------
try:
    df = pd.read_excel("data.xlsx")
except FileNotFoundError:
    st.error("❌ data.xlsx file not found! Make sure it's in the same folder as this script.")
    st.stop()

# ----------------------------
# Clean column names robustly
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
    'Timestamp', 'Channel', 'Denave Code', 'Codes', 'Store Name', 'Zone', 'State', 'City',
    'Location', 'Have you deployed the branding at the store?', 'Reason', 'Remarks',
    'Store Front Image With Date Time', 'Deployment Image 1 With Date Time',
    'Deployment Image 2 With Date Time', 'Deployment Image 3 With Date Time'
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("⚠️ Some required columns are missing in your Excel file:")
    for col in missing_columns:
        suggestions = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
        st.write(f"Missing: '{col}'", f"Possible matches in Excel: {suggestions}" if suggestions else "")
    st.stop()

# ----------------------------
# Title
# ----------------------------
st.title("🏪 AS Maven Store Branding Dashboard")
st.markdown("Interactive dashboard showing deployment status, store details, and images.")

# ----------------------------
# KPIs
# ----------------------------
total_stores = len(df)
deployed_count = df['Have you deployed the branding at the store?'].astype(str).str.upper().value_counts().get('YES', 0)
not_deployed_count = df['Have you deployed the branding at the store?'].astype(str).str.upper().value_counts().get('NO', 0)

col1, col2, col3 = st.columns(3)
col1.metric("Total Stores", total_stores)
col2.metric("Branding Deployed", deployed_count)
col3.metric("Not Deployed", not_deployed_count)

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("🔍 Filters")
zones = st.sidebar.multiselect("Select Zone(s)", df['Zone'].dropna().unique())
states = st.sidebar.multiselect("Select State(s)", df['State'].dropna().unique())
cities = st.sidebar.multiselect("Select City(s)", df['City'].dropna().unique())
channels = st.sidebar.multiselect("Select Channel(s)", df['Channel'].dropna().unique())

filtered_df = df.copy()
if zones:
    filtered_df = filtered_df[filtered_df['Zone'].isin(zones)]
if states:
    filtered_df = filtered_df[filtered_df['State'].isin(states)]
if cities:
    filtered_df = filtered_df[filtered_df['City'].isin(cities)]
if channels:
    filtered_df = filtered_df[filtered_df['Channel'].isin(channels)]

# ----------------------------
# Deployment Status Pie Chart
# ----------------------------
status_fig = px.pie(
    filtered_df,
    names='Have you deployed the branding at the store?',
    title="Deployment Status"
)
st.plotly_chart(status_fig, use_container_width=True)

# ----------------------------
# Deployment by Zone Bar Chart
# ----------------------------
zone_fig = px.bar(
    filtered_df,
    x='Zone',
    color='Have you deployed the branding at the store?',
    barmode='group',
    title="Deployment Status by Zone"
)
st.plotly_chart(zone_fig, use_container_width=True)

# ----------------------------
# Not Deployed Table (New Section)
# ----------------------------
st.subheader("📋 Not Deployed Store Details")

not_deployed_df = filtered_df[
    filtered_df['Have you deployed the branding at the store?'].astype(str).str.upper() == 'NO'
]

if not not_deployed_df.empty:
    st.dataframe(
        not_deployed_df[['Store Name', 'City', 'Zone', 'Reason', 'Remarks']],
        use_container_width=True,
        height=400
    )
else:
    st.success("✅ All stores have completed their branding deployment!")

# ----------------------------
# Store-wise Table
# ----------------------------
st.header("📑 All Store Details")
st.dataframe(
    filtered_df[
        ['Timestamp', 'Channel', 'Denave Code', 'Codes', 'Store Name', 'Zone', 'State', 'City',
         'Location', 'Have you deployed the branding at the store?', 'Reason', 'Remarks']
    ],
    use_container_width=True
)

# ----------------------------
# Helper: Convert Google Drive URLs → Direct Image Links
# ----------------------------
def convert_drive_url(url):
    """Convert Google Drive share links to direct-viewable image links."""
    if pd.isna(url) or str(url).strip() == "":
        return None
    url = str(url).strip()

    if "drive.google.com/file/d/" in url:
        try:
            file_id = url.split("drive.google.com/file/d/")[1].split("/")[0]
            return f"https://lh3.googleusercontent.com/d/{file_id}=w1000"
        except Exception:
            return None
    elif "open?id=" in url:
        try:
            file_id = url.split("open?id=")[1].split("&")[0]
            return f"https://lh3.googleusercontent.com/d/{file_id}=w1000"
        except Exception:
            return None
    elif "uc?id=" in url:
        try:
            file_id = url.split("uc?id=")[1].split("&")[0]
            return f"https://lh3.googleusercontent.com/d/{file_id}=w1000"
        except Exception:
            return None
    return url

# ----------------------------
# Store Images Section
# ----------------------------
st.header("📸 Store Images (Optional)")

for i, row in filtered_df.iterrows():
    store_name = str(row.get("Store Name", "")).strip()
    city = str(row.get("City", "")).strip()
    st.markdown(f"### 🏬 {store_name} – {city}")

    image_columns = [
        ("Store Front Image With Date Time", "Store Front"),
        ("Deployment Image 1 With Date Time", "Deployment 1"),
        ("Deployment Image 2 With Date Time", "Deployment 2"),
        ("Deployment Image 3 With Date Time", "Deployment 3"),
    ]

    cols = st.columns(len(image_columns))

    for col, (col_name, label) in zip(cols, image_columns):
        img_url = convert_drive_url(row.get(col_name))
        with col:
            if img_url:
                try:
                    st.image(img_url, caption=label, use_container_width=True)
                except Exception:
                    st.warning(f"⚠️ Could not load {label}")
            else:
                st.info(f"No {label} image")

    st.markdown("---")  # separator
