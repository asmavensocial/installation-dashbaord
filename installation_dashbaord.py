import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import re
import base64
import requests

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
    st.error("❌ Excel file not found! Make sure 'Maven-data-installation.xlsx' is in this folder.")
    st.stop()

# ----------------------------
# Header
# ----------------------------
col_logo, col_title = st.columns([0.15, 0.85])
with col_logo:
    try:
        logo = Image.open("maven-logo.jpeg")
        st.image(logo, width=90)
    except:
        st.write("AS Maven")

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
# KPI Summary
# ----------------------------
total_stores = len(df)
completed = df['Have you completed the installation at the store?'].astype(str).str.upper().value_counts().get('YES', 0)
not_completed = df['Have you completed the installation at the store?'].astype(str).str.upper().value_counts().get('NO', 0)
pending = total_stores - (completed + not_completed)
rate = (completed / total_stores) * 100 if total_stores else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stores", 861)
col2.metric("Stores Completed", 861)
col3.metric("Not Deployed", 0)
col4.metric("Pending", 0)

st.progress(int(rate))
st.caption(f"✅ Installation Progress: 100% completed")
st.header("Overall launch metrics")
st.caption(f"Total Stores in scope = 861 ((842 + 19(new stores added)")
st.caption(f"Total Stores revisit = 32")
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
# Charts
# ----------------------------
filtered_df['Installation Status'] = (
    filtered_df['Have you completed the installation at the store?']
    .astype(str).str.lower().map({'yes': 'Yes', 'no': 'No'}).fillna('Unknown')
)

grouped_state = filtered_df.groupby(['State', 'Installation Status']).size().reset_index(name='Count')
grouped_state = grouped_state[grouped_state['State'].notna()]

chart = px.bar(grouped_state, x='State', y='Count', color='Installation Status', barmode='group', text_auto=True,
               title="Installation Status by State")
chart.update_layout(template="plotly_dark")
st.plotly_chart(chart, use_container_width=True)

# ----------------------------
# Data Table
# ----------------------------
st.header("📊 Store Data Details")
st.dataframe(
    filtered_df[['MavenCode', 'Partner Store Name', 'Store code', 'State', 'City',
                 'Have you completed the installation at the store?']],
    use_container_width=True
)

# # ----------------------------
# # ✅ Not Deployed Stores Table (Restored)
# # ----------------------------
# st.markdown("## 📍 Not Deployed Store Details")

# status_col = "Have you completed the installation at the store?"
# if status_col in filtered_df.columns:
#     not_deployed_df = filtered_df[filtered_df[status_col].astype(str).str.lower() != "yes"]

#     required_cols = ["MavenCode", "Store code", "Partner Store Name", "State", "City",
#                      "If installation not done, Reason ?"]
#     existing = [c for c in required_cols if c in not_deployed_df.columns]

#     rename_map = {"Store code": "Store Code", "If installation not done, Reason ?": "Reason"}
#     not_deployed_df = not_deployed_df[existing].rename(columns=rename_map)

#     st.dataframe(not_deployed_df, use_container_width=True)

# ----------------------------
# Convert Links → Viewable Image URLs
# ----------------------------
def convert_photo_url(url):
    if pd.isna(url) or not str(url).strip():
        return None
    url = str(url).strip()

    if "googleusercontent" in url:
        return url + "=w1200-h800"

    match = re.search(r"AF1Qip[A-Za-z0-9\-_]+", url)
    if match:
        return f"https://lh3.googleusercontent.com/{match.group(0)}=w1200-h800"

    match2 = re.search(r"[-\w]{25,}", url)
    if match2:
        return f"https://drive.google.com/uc?export=view&id={match2.group(0)}"

    return url

@st.cache_data(show_spinner=False)
def fetch_image_base64(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return "data:image/jpeg;base64," + base64.b64encode(r.content).decode()
    except:
        return None
    return None

def preload_images_batch(df, store_list, start_index, batch_size=10):
    """Preload images for a batch of stores"""
    end_index = min(start_index + batch_size, len(store_list))
    
    for i in range(start_index, end_index):
        store_code = store_list[i]
        row = df[df['MavenCode'] == store_code].iloc[0]
        
        # Preload all 3 images for this store
        urls = [
            convert_photo_url(row.get("Store image - Front (With Date and Time)")),
            convert_photo_url(row.get("Reporting form (With Date and Time)")),
            convert_photo_url(row.get("After work photo (With Date and Time)")),
        ]
        
        for url in urls:
            if url:
                fetch_image_base64(url)  # This will cache the image

# ----------------------------
# 📸 Store-by-Store Viewer
# ----------------------------
st.header("📸 Store Images Viewer")

store_list = list(filtered_df['MavenCode'].dropna().unique())

if "store_index" not in st.session_state:
    st.session_state.store_index = 0
if "preloaded_batches" not in st.session_state:
    st.session_state.preloaded_batches = set()

col_prev, col_mid, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("⬅️ Previous") and st.session_state.store_index > 0:
        st.session_state.store_index -= 1

with col_mid:
    st.markdown(f"<h4 style='text-align:center;'>Store {st.session_state.store_index+1} of {len(store_list)}</h4>", 
                unsafe_allow_html=True)

with col_next:
    if st.button("Next ➡️") and st.session_state.store_index < len(store_list) - 1:
        st.session_state.store_index += 1

# Preload images for current batch only if not already loaded
BATCH_SIZE = 5  # Load 5 stores at a time (15 images)
current_batch = st.session_state.store_index // BATCH_SIZE
if current_batch not in st.session_state.preloaded_batches:
    current_batch_start = current_batch * BATCH_SIZE
    with st.spinner(f"Loading images for stores {current_batch_start+1}-{min(current_batch_start+BATCH_SIZE, len(store_list))}..."):
        preload_images_batch(filtered_df, store_list, current_batch_start, batch_size=BATCH_SIZE)
        st.session_state.preloaded_batches.add(current_batch)

selected_store = store_list[st.session_state.store_index]
row = filtered_df[filtered_df['MavenCode'] == selected_store].iloc[0]

st.markdown(f"### 🏬 **{row['Partner Store Name']}** — *{row['City']}, {row['State']}* ({row['MavenCode']})")

images = {
    "Store Front Image": convert_photo_url(row.get("Store image - Front (With Date and Time)")),
    "Reporting Form Image": convert_photo_url(row.get("Reporting form (With Date and Time)")),
    "After Installation Image": convert_photo_url(row.get("After work photo (With Date and Time)")),
}

cols = st.columns(3)
for col, (label, url) in zip(cols, images.items()):
    with col:
        img_data = fetch_image_base64(url)
        if img_data:
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <img src="{img_data}" style="width:100%;height:260px;object-fit:cover;border-radius:10px;border:1px solid #444;"/>
                    <p style="font-size:14px;color:#ccc;">{label}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning(f"⚠️ {label} Not Available")



