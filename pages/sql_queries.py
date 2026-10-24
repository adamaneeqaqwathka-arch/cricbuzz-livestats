"""Streamlit page: run the SQL analytics questions and a custom query box."""

import re
from pathlib import Path

import mysql.connector
import pandas as pd
import streamlit as st

from utils.db_connection import get_connection

QUERY_FILE = Path(__file__).parent.parent / "sql" / "queries.sql"

# Matches title lines such as "-- Q3: Top 10 ODI run scorers"
TITLE_PATTERN = re.compile(r"^--\s*(Q\d+[^:]*):\s*(.*)$")

# The custom query box is read-only: these words are never allowed
FORBIDDEN_WORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|replace)\b",
    re.IGNORECASE,
)


@st.cache_data
def load_queries():
    """Read sql/queries.sql and return a list of {label, sql} dicts."""
    queries = []
    title, description = None, None
    buffer = []

    for line in QUERY_FILE.read_text(encoding="utf-8").splitlines():
        title_match = TITLE_PATTERN.match(line)
        if title_match:
            title = title_match.group(1).strip()
            description = title_match.group(2).strip()
            buffer = []
            continue

        # Skip other comments and blank lines
        if not line.strip() or line.strip().startswith("--"):
            continue

        buffer.append(line)
        if line.rstrip().endswith(";") and title:
            sql = "\n".join(buffer).strip().rstrip(";")
            queries.append({"label": f"{title}: {description}", "sql": sql})
            buffer = []

    return queries


@st.cache_data(ttl=60)
def run_query(sql):
    """Run one SELECT query and return the result as a DataFrame."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        if cursor.description is None:
            return pd.DataFrame()
        columns = [column[0] for column in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columns)
    finally:
        conn.close()


def show_result(sql):
    """Run a query and display the table, handling database errors."""
    try:
        df = run_query(sql)
    except mysql.connector.Error as error:
        st.error(f"Database error: {error}")
        return
    except Exception as error:  # keep the page alive for any other problem
        st.error(f"Could not run the query: {error}")
        return

    if df.empty:
        st.warning(
            "The query ran but returned no rows. This usually means the "
            "data it needs has not been loaded yet."
        )
    else:
        st.success(f"{len(df)} rows returned")
        st.dataframe(df, use_container_width=True)


st.title("SQL Queries & Analytics")

if not QUERY_FILE.exists():
    st.error(f"Query file not found: {QUERY_FILE}")
    st.stop()

queries = load_queries()
labels = [q["label"] for q in queries]

choice = st.selectbox("Choose a question", labels)
selected = queries[labels.index(choice)]

st.code(selected["sql"], language="sql")

if st.button("Run query", type="primary"):
    show_result(selected["sql"])

st.divider()

with st.expander("Run your own SELECT query"):
    custom_sql = st.text_area(
        "SQL (SELECT or WITH queries only)",
        value="SELECT * FROM teams LIMIT 10",
        height=120,
    )
    if st.button("Run custom query"):
        cleaned = custom_sql.strip().rstrip(";")
        if not cleaned.lower().startswith(("select", "with")):
            st.error("Only SELECT queries are allowed here.")
        elif FORBIDDEN_WORDS.search(cleaned) or ";" in cleaned:
            st.error("This query contains a word or character that is not allowed.")
        else:
            show_result(cleaned)