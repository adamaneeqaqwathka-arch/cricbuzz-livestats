import streamlit as st
import pandas as pd
from utils.api_client import fetch_live_matches

st.title("Live Matches")

matches = fetch_live_matches()
df = pd.DataFrame(matches)

st.selectbox("Filter by format", options=["All"] + df["format"].unique().tolist(), key="format_filter")
st.button("Refresh")
st.warning("Could not load matches") if df.empty else st.dataframe(df)

#Then try writing pages/live_matches.py yourself, using these pieces:
#
#import streamlit as st, import pandas as pd, and from utils.api_client import fetch_live_matches.
#st.title("Live Matches").
#Call fetch_live_matches(), turn the result into a DataFrame, and show it with st.dataframe(df).
#Add a st.selectbox to filter by format (TEST, T20, ODI), and a st.button("Refresh") that re-fetches.
#If the list is empty, show st.warning("Could not load matches").
#Run it with streamlit run pages/live_matches.py. Paste your code and what you see, and we’ll turn it into the multi-page app with app.py and home.py after.

