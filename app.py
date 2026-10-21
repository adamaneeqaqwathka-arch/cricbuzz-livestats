import streamlit as st

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")

pages = [
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/live_matches.py", title="Live Matches"),
]

st.navigation(pages).run()