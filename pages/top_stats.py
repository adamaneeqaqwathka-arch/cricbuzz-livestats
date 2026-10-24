"""Streamlit page: top batting and bowling statistics by format."""

import sys
from pathlib import Path

# Make the project root importable so "from utils..." works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mysql.connector
import pandas as pd
import streamlit as st

from utils.db_connection import get_connection

FORMATS = ["Test", "ODI", "T20I"]

# label -> (column, sort direction, extra condition)
# Columns and directions come from this fixed list only (never from user
# input), so building the SQL text with them is safe.
BATTING = {
    "Most runs": ("runs", "DESC", "c.runs IS NOT NULL"),
    "Highest score": ("highest_score", "DESC", "c.highest_score IS NOT NULL"),
    "Best batting average (min 20 innings)": (
        "batting_avg", "DESC", "c.innings >= 20"),
    "Highest strike rate (min 20 innings)": (
        "strike_rate", "DESC", "c.innings >= 20"),
    "Most centuries": ("centuries", "DESC", "c.centuries IS NOT NULL"),
    "Most fifties": ("fifties", "DESC", "c.fifties IS NOT NULL"),
}

BOWLING = {
    "Most wickets": ("wickets", "DESC", "c.wickets > 0"),
    "Best bowling average (min 20 wickets)": (
        "bowling_avg", "ASC", "c.wickets >= 20 AND c.bowling_avg IS NOT NULL"),
    "Best economy rate (min 20 wickets)": (
        "economy", "ASC", "c.wickets >= 20 AND c.economy IS NOT NULL"),
}


@st.cache_data(ttl=300)
def fetch_top(column, direction, condition, fmt, limit):
    """Return the top players for one statistic in one format."""
    sql = f"""
        SELECT p.player_name AS player,
               c.{column}    AS value,
               c.matches
        FROM player_career_stats c
        JOIN players p ON p.player_id = c.player_id
        WHERE c.format = %s AND {condition}
        ORDER BY c.{column} {direction}
        LIMIT %s
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (fmt, limit))
        return pd.DataFrame(cursor.fetchall(), columns=["player", "value", "matches"])
    finally:
        conn.close()


def render(stats, key_prefix):
    """Draw the controls, the table and the chart for one set of statistics."""
    col1, col2, col3 = st.columns([3, 2, 2])
    category = col1.selectbox("Statistic", list(stats), key=f"{key_prefix}_cat")
    fmt = col2.radio("Format", FORMATS, index=1, horizontal=True,
                     key=f"{key_prefix}_fmt")
    limit = col3.slider("Players to show", 3, 20, 10, key=f"{key_prefix}_n")

    column, direction, condition = stats[category]

    try:
        df = fetch_top(column, direction, condition, fmt, limit)
    except mysql.connector.Error as error:
        st.error(f"Database error: {error}")
        return

    if df.empty:
        st.warning("No players match this statistic and format yet.")
        return

    df["value"] = pd.to_numeric(df["value"])
    df.index = range(1, len(df) + 1)  # rank starts at 1

    left, right = st.columns([2, 3])
    left.dataframe(df.rename(columns={"value": category.split(" (")[0]}),
                   use_container_width=True)
    right.bar_chart(df.set_index("player")["value"])


st.title("Top Player Stats")
st.caption(
    "Career statistics loaded from the Cricbuzz API into the database. "
    "Only players whose profiles have been loaded appear here."
)

batting_tab, bowling_tab = st.tabs(["Batting", "Bowling"])

with batting_tab:
    render(BATTING, "bat")

with bowling_tab:
    render(BOWLING, "bowl")