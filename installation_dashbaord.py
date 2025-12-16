import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import re
import base64
import requests

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="AS Maven Installation Dashboard",
    layout="wide"
)

# ======================================================
# COLUMN NORMALIZATION (CRITICAL FIX)
# ======================================================
def normalize_columns(df):
    column_map = {
        "Maven Code": "MavenCode",
        "Partner Name": "Partner Store Name",
        "Store code - Oneplus": "Store Code",
        "Installation Completed ?": "Installation Status",
        "If installation not done, please mention the reason ?": "Reason",
        "Store front image(With Date & Time)": "Store Front Image",
        "Before image(With Date & Time)": "Before Image",
        "After image(With Date & Time)": "After Image",
        "Reporting form image(With Date & Time)": "Reporting Form Image",
    }

    for excel_col, std_col in column_map.items():
        if excel_col in df.columns:
            df[std_col] = df[excel_col]

    return df

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel("Macan-KVInstallation.xlsx")
    df.columns = [str(c).strip() for c in df.columns]
    df = normalize_columns(df)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Excel file not found. Please upload 'Maven-data-installation.xlsx'")
    st.stop()

# ======================================================
# HEADER
# ======================================================
col_logo, col_title = st.columns([0.12, 0.88])

with col_logo:
    try:
        st.image("maven-logo.jpeg", width=90)
    except:
        st.write("AS Maven")

with col_title:
    st.markdown(
        """
        <h2 style='margin-bottom:0;'>AS Maven Store Installation Dashboard</h2>
        <p style='margin-top:4px;font-size:18px;color:#888;'>Project Macan – KV Installation</p>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ======================================================
# INSTALLATION STATUS STANDARDIZATION
# ======================================================
df["Installation Status"] = (
    df["Installation Status"]
    .astype(str)
    .str.upper()
    .map({
        "YES": "Completed",
        "Y": "Completed",
        "DONE": "Completed",
        "COMPLETED": "Completed",
        "NO": "Not Completed",
        "N": "Not Completed",
    })
    .fillna("Pending")
)

# ======================================================
# KPI METRICS
# ======================================================
total_stores = len(df)
completed = (df["Installation Status"] == "Completed").sum()
not_completed = (df["Installation Status"] == "Not Completed").sum()
pending = total_stores - (completed + not_completed)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Stores", 858)
c2.metric("Completed", total_stores)
c3.metric("Not Deployed", not_completed)
c4.metric("Pending", 858 - total_stores)

st.markdown("---")

# ======================================================
# SIDEBAR FILTERS (SAFE)
# ======================================================
st.sidebar.header("🔍 Filters")

states = st.sidebar.multiselect(
    "State", df["State"].dropna().unique() if "State" in df.columns else []
)
cities = st.sidebar.multiselect(
    "City", df["City"].dropna().unique() if "City" in df.columns else []
)
partners = st.sidebar.multiselect(
    "Partner Store Name",
    df["Partner Store Name"].dropna().unique() if "Partner Store Name" in df.columns else []
)

filtered_df = df.copy()
if states:
    filtered_df = filtered_df[filtered_df["State"].isin(states)]
if cities:
    filtered_df = filtered_df[filtered_df["City"].isin(cities)]
if partners:
    filtered_df = filtered_df[filtered_df["Partner Store Name"].isin(partners)]

# ======================================================
# BAR CHART – STATUS BY STATE
# ======================================================
grouped = (
    filtered_df
    .groupby(["State", "Installation Status"])
    .size()
    .reset_index(name="Count")
)

fig = px.bar(
    grouped,
    x="State",
    y="Count",
    color="Installation Status",
    barmode="group",
    text_auto=True,
    title="Installation Status by State"
)
fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)

# ======================================================
# STORE DATA TABLE
# ======================================================
st.header("📊 Store Data Details")

st.dataframe(
    filtered_df[
        [
            "MavenCode",
            "Partner Store Name",
            "Store Code",
            "State",
            "City",
            "Installation Status",
        ]
    ],
    use_container_width=True,
)

# ======================================================
# NOT DEPLOYED TABLE WITH REASON
# ======================================================
st.header("📍 Not Deployed Stores")

not_deployed_df = filtered_df[filtered_df["Installation Status"] == "Not Completed"]

if not not_deployed_df.empty:
    st.dataframe(
        not_deployed_df[
            [
                "MavenCode",
                "Store Code",
                "Partner Store Name",
                "State",
                "City",
                "Reason",
            ]
        ],
        use_container_width=True,
    )
else:
    st.info("All stores are completed 🎉")

# # ======================================================
# # IMAGE HELPERS
# # ======================================================
# def convert_photo_url(url):
#     if pd.isna(url) or not str(url).strip():
#         return None

#     url = str(url).strip()

#     match = re.search(r"[-\w]{25,}", url)
#     if match:
#         return f"https://drive.google.com/uc?export=view&id={match.group(0)}"

#     return url

# @st.cache_data(show_spinner=False)
# def fetch_image(url):
#     try:
#         r = requests.get(url, timeout=6)
#         if r.status_code == 200:
#             return "data:image/jpeg;base64," + base64.b64encode(r.content).decode()
#     except:
#         pass
#     return None

# # ======================================================
# # STORE IMAGE VIEWER
# # ======================================================
# st.header("📸 Store Images Viewer")

# store_list = filtered_df["MavenCode"].dropna().unique().tolist()

# if "store_index" not in st.session_state:
#     st.session_state.store_index = 0

# c_prev, c_mid, c_next = st.columns([1, 2, 1])

# with c_prev:
#     if st.button("⬅ Previous") and st.session_state.store_index > 0:
#         st.session_state.store_index -= 1

# with c_mid:
#     st.markdown(
#         f"<h4 style='text-align:center;'>Store {st.session_state.store_index+1} of {len(store_list)}</h4>",
#         unsafe_allow_html=True
#     )

# with c_next:
#     if st.button("Next ➡") and st.session_state.store_index < len(store_list) - 1:
#         st.session_state.store_index += 1

# row = filtered_df[filtered_df["MavenCode"] == store_list[st.session_state.store_index]].iloc[0]

# st.markdown(
#     f"### 🏬 **{row['Partner Store Name']}** — *{row['City']}, {row['State']}* ({row['MavenCode']})"
# )

# images = {
#     "Store Front": row.get("Store Front Image"),
#     "Before Installation": row.get("Before Image"),
#     "After Installation": row.get("After Image"),
#     "Reporting Form": row.get("Reporting Form Image"),
# }

# cols = st.columns(4)
# for col, (label, url) in zip(cols, images.items()):
#     with col:
#         img = fetch_image(convert_photo_url(url))
#         if img:
#             st.markdown(
#                 f"""
#                 <img src="{img}" style="width:100%;height:220px;object-fit:cover;border-radius:8px;border:1px solid #444;">
#                 <p style="text-align:center;color:#aaa;">{label}</p>
#                 """,
#                 unsafe_allow_html=True
#             )
#         else:
#             st.warning(f"{label} not available")
