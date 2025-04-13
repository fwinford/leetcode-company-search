import streamlit as st
import pandas as pd
import requests
from io import StringIO
import os

# --- GitHub Info ---
REPO = "liquidslr/leetcode-company-wise-problems"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
RAW_URL_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
LOCAL_CSV_CACHE = "merged_problems.csv"

# --- Fetch CSV paths ---
def get_all_csv_paths():
    res = requests.get(API_URL)
    if res.status_code != 200:
        st.error("❌ Failed to fetch file list from GitHub.")
        return []
    data = res.json()
    # Only keep "All.csv" files
    return [file["path"] for file in data["tree"] if file["path"].endswith("All.csv")]

# --- Load from GitHub ---
def load_all_csvs():
    all_data = []
    for path in get_all_csv_paths():
        url = RAW_URL_BASE + path
        res = requests.get(url)
        if res.status_code == 200:
            try:
                df = pd.read_csv(StringIO(res.text))
                df["Company"] = path.split("/")[0].capitalize()
                df["SourceFile"] = path
                all_data.append(df)
            except Exception as e:
                print(f"⚠️ Skipped {path} due to error: {e}")
    merged = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    merged.to_csv(LOCAL_CSV_CACHE, index=False)
    return merged

# --- Load from local CSV ---
def load_data():
    if os.path.exists(LOCAL_CSV_CACHE):
        return pd.read_csv(LOCAL_CSV_CACHE)
    else:
        return load_all_csvs()

# ========== Streamlit App ==========
st.set_page_config(page_title="LeetCode Company Finder", layout="wide")

st.title("💼 LeetCode Company Problem Finder")
st.caption("Quickly find which companies have asked a LeetCode problem. Data pulled from GitHub.")
st.markdown('🔗 [View GitHub Repo](https://github.com/liquidslr/leetcode-company-wise-problems)')

# --- Load cached or refresh ---
df = load_data()

# --- Sidebar Filters ---
with st.sidebar:
    st.header("🔍 Filters")
    selected_company = st.selectbox("Company", ["All"] + sorted(df["Company"].dropna().unique()))
    query = st.text_input("Search problem name", placeholder="e.g. Two Sum")
    time_filter = st.selectbox("Frequency Range", ["All Time", "Last 6 Months", "Last 3 Months"])

    if time_filter == "Last 3 Months":
        filtered_df = filtered_df[filtered_df["Frequency"] >= 80]
    elif time_filter == "Last 6 Months":
        filtered_df = filtered_df[filtered_df["Frequency"] >= 60]


# --- Filter logic ---
if not df.empty:
    filtered_df = df.copy()

    if selected_company != "All":
        filtered_df = filtered_df[filtered_df["Company"] == selected_company]

    if query:
        mask = filtered_df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)
        filtered_df = filtered_df[mask]

    # ✅ Move frequency filter here:
    time_filter = st.sidebar.selectbox("Frequency Range", ["All Time", "Last 6 Months", "Last 3 Months"], key="freq_filter")
    if time_filter == "Last 3 Months":
        filtered_df = filtered_df[filtered_df["Frequency"] >= 80]
    elif time_filter == "Last 6 Months":
        filtered_df = filtered_df[filtered_df["Frequency"] >= 60]

    # --- Display results
    if not filtered_df.empty:
        cols = ['Company'] + [col for col in filtered_df.columns if col != 'Company']
        st.success(f"✅ Found {len(filtered_df)} matching result(s)")
        st.dataframe(filtered_df[cols])
    else:
        st.warning("⚠️ No results found. Try adjusting your search or filter.")

# --- Main display ---
if not filtered_df.empty:
    st.success(f"✅ Found {len(filtered_df)} matching result(s)")
    cols = ['Company'] + [col for col in filtered_df.columns if col != 'Company']
    st.dataframe(filtered_df[cols])
else:
    st.warning("⚠️ No results found. Try adjusting your search or filter.")

# --- Manual refresh ---
st.markdown("---")
if st.button("🔄 Refresh data from GitHub"):
    with st.spinner("Refreshing from GitHub... ⏳"):
        df = load_all_csvs()
        st.success("✅ Refreshed data from GitHub!")
