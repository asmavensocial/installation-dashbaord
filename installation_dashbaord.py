import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO
from PIL import Image

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

# Check for missing columns
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error("⚠️ Some required columns are missing in your Excel file:")
    for col in missing_columns:
        suggestions = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
        st.write(f"Missing: '{col}'", f"Possible matches in Excel: {suggestions}" if suggestions else "")
    st.stop()

# ----------------------------
# Helper: Get Image from Google Drive
# ----------------------------
def get_image_from_drive(url):
    """Fetch image from Google Drive shared URL."""
    if pd.isna(url) or str(url).strip() == "":
        return None
    url = str(url).strip()

    file_id = None
    if "drive.google.com/file/d/" in url:
        file_id = url.split("drive.google.com/file/d/")[1].split("/")[0]
    elif "id=" in url:
        file_id = url.split("id=")[1].split("&")[0]
    elif "uc?id=" in url:
        file_id = url.split("uc?id=")[1].split("&")[0]

    if not file_id:
        return None

    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        response = requests.get(download_url, stream=True, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error loading image: {e}")
    return None

# ----------------------------
# Header with Logo + Title
# ----------------------------
logo_url = "https://drive.google.com/file/d/1PXbI1KB1vd5YM7Q2fe2azBGaRPrbewpZ/view?usp=sharing"
logo_img = get_image_from_drive(logo_url)

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if logo_img:
        st.image(logo_img, width=100)
with col_title:
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
# Charts
# ----------------------------
status_fig = px.pie(
    filtered_df,
    names='Have you deployed the branding at the store?',
    title="Deployment Status",
    color_discrete_sequence=px.colors.qualitative.Set3
)
st.plotly_chart(status_fig, use_container_width=True)

zone_fig = px.bar(
    filtered_df,
    x='Zone',
    color='Have you deployed the branding at the store?',
    barmode='group',
    title="Deployment Status by Zone",
    color_discrete_sequence=px.colors.qualitative.Safe
)
st.plotly_chart(zone_fig, use_container_width=True)

# ----------------------------
# Store-wise Table
# ----------------------------
st.header("📋 Store-wise Details")
st.dataframe(filtered_df[
    ['Timestamp', 'Channel', 'Denave Code', 'Codes', 'Store Name', 'Zone', 'State', 'City',
     'Location', 'Have you deployed the branding at the store?', 'Reason', 'Remarks']
])

# ----------------------------
# Store Images Gallery
# ----------------------------
st.header("📸 Store Deployment Images")

for i, row in filtered_df.iterrows():
    store_name = str(row.get("Store Name", "")).strip()
    city = str(row.get("City", "")).strip()

    with st.expander(f"🏬 {store_name} – {city}", expanded=False):
        st.markdown("#### Store Photo Gallery")

        image_columns = [
            ("Store Front Image With Date Time", "Store Front"),
            ("Deployment Image 1 With Date Time", "Deployment 1"),
            ("Deployment Image 2 With Date Time", "Deployment 2"),
            ("Deployment Image 3 With Date Time", "Deployment 3"),
        ]

        col_grid = [st.columns(2), st.columns(2)]
        all_cols = [c for sub in col_grid for c in sub]

        for col, (col_name, label) in zip(all_cols, image_columns):
            with col:
                img = get_image_from_drive(row.get(col_name))
                if img:
                    st.image(img, caption=label, use_container_width=True)
                else:
                    st.info(f"No {label} image found or invalid link.")
