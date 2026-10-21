import pandas as pd
import streamlit as st

from utils.api_client import fetch_live_matches


@st.cache_data(ttl=60)
def load_matches():
    return fetch_live_matches()


st.title("Live Matches")

if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()

df = pd.DataFrame(load_matches())

if df.empty:
    st.warning("Could not load matches")
    st.stop()

formats = sorted(df["format"].dropna().unique().tolist())
choice = st.selectbox("Filter by format", ["All"] + formats)

if choice != "All":
    df = df[df["format"] == choice]

st.write(f"Showing {len(df)} matches")
st.dataframe(df[["series_name", "team1", "team2", "venue", "status"]])