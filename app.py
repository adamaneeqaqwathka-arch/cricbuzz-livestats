import streamlit as st

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")

pages = [
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/live_matches.py", title="Live Matches"),
    st.Page("pages/crud_operations.py", title="CRUD Operations"),
    st.Page("pages/top_stats.py", title="Top Stats"),
]

st.navigation(pages).run()