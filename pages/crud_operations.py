"""Streamlit page: create, read, update and delete player records."""

import sys
from datetime import date
from pathlib import Path

# Make the project root importable so "from utils..." works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mysql.connector
import pandas as pd
import streamlit as st

from utils.db_connection import get_connection

# Players added by hand get IDs in this range, so they can never clash with
# real Cricbuzz IDs (below 50 million) or the sample data (90 million and up).
MANUAL_ID_START = 50_000_000
MANUAL_ID_END = 89_999_999

ROLES = ["Batsman", "Bowler", "Batting Allrounder", "Bowling Allrounder",
         "WK-Batsman"]
BATTING_STYLES = ["Right Handed Bat", "Left Handed Bat"]
BOWLING_STYLES = ["None", "Right-arm fast", "Right-arm medium",
                  "Left-arm fast", "Left-arm medium", "Right-arm offbreak",
                  "Right-arm legbreak", "Left-arm orthodox",
                  "Left-arm wrist-spin"]


# ---------------------------------------------------------------- helpers

def fetch_players(search="", limit=200):
    """Return players whose name contains the search text."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT player_id, player_name, country, role,
                   batting_style, bowling_style, date_of_birth
            FROM players
            WHERE player_name LIKE %s
            ORDER BY player_name
            LIMIT %s
            """,
            (f"%{search.strip()}%", limit),
        )
        columns = ["player_id", "player_name", "country", "role",
                   "batting_style", "bowling_style", "date_of_birth"]
        return pd.DataFrame(cursor.fetchall(), columns=columns)
    finally:
        conn.close()


def validate(name, country):
    """Return a list of problems with the form values (empty list = valid)."""
    problems = []
    if not name.strip():
        problems.append("Player name is required.")
    elif len(name.strip()) > 100:
        problems.append("Player name must be 100 characters or fewer.")
    if len(country.strip()) > 100:
        problems.append("Country must be 100 characters or fewer.")
    return problems


def clean_values(country, bowling_style, dob):
    """Turn empty form values into NULL for the database."""
    return (
        country.strip() or None,
        None if bowling_style == "None" else bowling_style,
        dob,
    )


def next_manual_id(cursor):
    """Next free player id in the manual range."""
    cursor.execute(
        "SELECT MAX(player_id) FROM players WHERE player_id BETWEEN %s AND %s",
        (MANUAL_ID_START, MANUAL_ID_END),
    )
    current = cursor.fetchone()[0]
    return (current or MANUAL_ID_START - 1) + 1


def player_label(row):
    return f"{row.player_name} (id {row.player_id})"


def pick_player(key):
    """Search box + selectbox. Returns the chosen player row, or None."""
    search = st.text_input("Search by name", key=f"{key}_search")
    df = fetch_players(search, limit=100)
    if df.empty:
        st.info("No players match your search.")
        return None
    labels = [player_label(r) for r in df.itertuples()]
    choice = st.selectbox("Choose a player", labels, key=f"{key}_pick")
    return df.iloc[labels.index(choice)]


def style_index(options, value, default=0):
    return options.index(value) if value in options else default


# ------------------------------------------------------------------ page

st.title("Player Records (CRUD)")
st.caption("Create, view, edit and delete rows in the players table.")

view_tab, add_tab, edit_tab, delete_tab = st.tabs(
    ["View", "Add player", "Edit player", "Delete player"]
)

# ---- READ ----
with view_tab:
    search = st.text_input("Search by name", key="view_search")
    try:
        df = fetch_players(search)
        st.write(f"{len(df)} players shown (maximum 200)")
        st.dataframe(df, use_container_width=True, hide_index=True)
    except mysql.connector.Error as error:
        st.error(f"Database error: {error}")

# ---- CREATE ----
with add_tab:
    with st.form("add_player_form", clear_on_submit=True):
        name = st.text_input("Full name *")
        country = st.text_input("Country")
        role = st.selectbox("Playing role", ROLES)
        batting_style = st.selectbox("Batting style", BATTING_STYLES)
        bowling_style = st.selectbox("Bowling style", BOWLING_STYLES)
        has_dob = st.checkbox("Add date of birth")
        dob_value = st.date_input(
            "Date of birth", value=date(1995, 1, 1),
            min_value=date(1950, 1, 1), max_value=date.today(),
        )
        submitted = st.form_submit_button("Add player", type="primary")

    if submitted:
        problems = validate(name, country)
        if problems:
            for problem in problems:
                st.error(problem)
        else:
            country_v, bowling_v, _ = clean_values(country, bowling_style, None)
            dob_v = dob_value if has_dob else None
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM players "
                    "WHERE LOWER(player_name) = LOWER(%s) AND country <=> %s",
                    (name.strip(), country_v),
                )
                if cursor.fetchone()[0] > 0:
                    st.error("A player with this name and country already exists.")
                else:
                    new_id = next_manual_id(cursor)
                    cursor.execute(
                        """
                        INSERT INTO players (
                            player_id, player_name, country, role,
                            batting_style, bowling_style, date_of_birth
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (new_id, name.strip(), country_v, role,
                         batting_style, bowling_v, dob_v),
                    )
                    conn.commit()
                    st.success(f"Added {name.strip()} with id {new_id}.")
            except mysql.connector.Error as error:
                conn.rollback()
                st.error(f"Database error: {error}")
            finally:
                conn.close()

# ---- UPDATE ----
with edit_tab:
    player = pick_player("edit")
    if player is not None:
        with st.form(f"edit_form_{player.player_id}"):
            new_name = st.text_input("Full name *", value=player.player_name)
            new_country = st.text_input("Country", value=player.country or "")
            new_role = st.selectbox(
                "Playing role", ROLES,
                index=style_index(ROLES, player.role))
            new_bat = st.selectbox(
                "Batting style", BATTING_STYLES,
                index=style_index(BATTING_STYLES, player.batting_style))
            new_bowl = st.selectbox(
                "Bowling style", BOWLING_STYLES,
                index=style_index(BOWLING_STYLES, player.bowling_style))
            save = st.form_submit_button("Save changes", type="primary")

        if save:
            problems = validate(new_name, new_country)
            if problems:
                for problem in problems:
                    st.error(problem)
            else:
                country_v, bowling_v, _ = clean_values(new_country, new_bowl, None)
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE players
                        SET player_name = %s, country = %s, role = %s,
                            batting_style = %s, bowling_style = %s
                        WHERE player_id = %s
                        """,
                        (new_name.strip(), country_v, new_role, new_bat,
                         bowling_v, int(player.player_id)),
                    )
                    conn.commit()
                    st.success(f"Updated player {int(player.player_id)}.")
                except mysql.connector.Error as error:
                    conn.rollback()
                    st.error(f"Database error: {error}")
                finally:
                    conn.close()

# ---- DELETE ----
with delete_tab:
    player = pick_player("delete")
    if player is not None:
        st.warning(
            f"You are about to delete **{player.player_name}** "
            f"(id {int(player.player_id)}). This cannot be undone."
        )
        remove_stats = st.checkbox(
            "Also delete this player's career statistics", key="delete_stats")
        confirm = st.checkbox("I understand, delete this player", key="delete_ok")

        if st.button("Delete player", disabled=not confirm):
            conn = get_connection()
            try:
                cursor = conn.cursor()
                # Both deletes succeed together or not at all (one transaction)
                if remove_stats:
                    cursor.execute(
                        "DELETE FROM player_career_stats WHERE player_id = %s",
                        (int(player.player_id),),
                    )
                cursor.execute(
                    "DELETE FROM players WHERE player_id = %s",
                    (int(player.player_id),),
                )
                conn.commit()
                st.success(f"Deleted {player.player_name}.")
            except mysql.connector.IntegrityError:
                conn.rollback()
                st.error(
                    "This player cannot be deleted because other records still "
                    "refer to them (career statistics, batting, bowling or "
                    "partnership rows). Nothing was changed."
                )
            except mysql.connector.Error as error:
                conn.rollback()
                st.error(f"Database error: {error}")
            finally:
                conn.close()