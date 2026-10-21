"""Save a parsed Cricbuzz scorecard into MySQL."""

from utils.db_connection import get_connection
from utils.scorecard_parser import parse_scorecard


def save_scorecard(match_id, data):
    """Save a Cricbuzz scorecard for one match, transactionally.

    The match must already exist in the matches table (with both teams).
    Safe to run more than once: rows are updated, not duplicated.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Find the match's two teams so scorecard names map to team IDs
        cursor.execute(
            """
            SELECT t1.team_id, t1.team_name, t2.team_id, t2.team_name
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE m.match_id = %s
            """,
            (match_id,),
        )
        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Match {match_id} was not found, or its teams "
                "are missing from the teams table."
            )

        team_ids = {row[1]: row[0], row[3]: row[2]}

        # 2. Parse the scorecard
        batting, bowling, partnerships, team_innings = parse_scorecard(
            data, match_id, team_ids
        )

        # 3. Validate team mappings before inserting anything
        for innings in team_innings:
            if innings["team_id"] is None:
                raise ValueError(
                    "Could not map a scorecard batting team to a database "
                    f"team. Database teams: {list(team_ids)}. "
                    f"Scorecard team: {innings}"
                )

        for record in bowling:
            if record["team_id"] is None:
                raise ValueError(f"Could not identify the bowling team: {record}")

        # 4. Players first (batting and bowling rows reference them)
        players = {}
        for record in batting + bowling:
            if record.get("player_id") is not None and record.get("player_name"):
                players[record["player_id"]] = record["player_name"]

        for player_id, player_name in players.items():
            cursor.execute(
                """
                INSERT INTO players (player_id, player_name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE player_name = VALUES(player_name)
                """,
                (player_id, player_name),
            )

        # 5. Team innings
        for record in team_innings:
            cursor.execute(
                """
                INSERT INTO team_innings (
                    match_id, innings_no, team_id,
                    runs, wickets, balls, extras, batting_first
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    team_id = VALUES(team_id),
                    runs = VALUES(runs),
                    wickets = VALUES(wickets),
                    balls = VALUES(balls),
                    extras = VALUES(extras),
                    batting_first = VALUES(batting_first)
                """,
                (
                    record["match_id"],
                    record["innings_no"],
                    record["team_id"],
                    record["runs"],
                    record["wickets"],
                    record["balls"],
                    record["extras"],
                    record["batting_first"],
                ),
            )

        # 6. Batting innings (player names live in the players table)
        for record in batting:
            cursor.execute(
                """
                INSERT INTO batting_innings (
                    match_id, innings_no, player_id, team_id,
                    batting_position, runs, balls, fours, sixes,
                    is_out, dismissal_type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    team_id = VALUES(team_id),
                    batting_position = VALUES(batting_position),
                    runs = VALUES(runs),
                    balls = VALUES(balls),
                    fours = VALUES(fours),
                    sixes = VALUES(sixes),
                    is_out = VALUES(is_out),
                    dismissal_type = VALUES(dismissal_type)
                """,
                (
                    record["match_id"],
                    record["innings_no"],
                    record["player_id"],
                    record["team_id"],
                    record["batting_position"],
                    record["runs"],
                    record["balls"],
                    record["fours"],
                    record["sixes"],
                    record["is_out"],
                    record["dismissal_type"],
                ),
            )

        # 7. Bowling innings
        for record in bowling:
            cursor.execute(
                """
                INSERT INTO bowling_innings (
                    match_id, innings_no, player_id, team_id,
                    balls_bowled, maidens, runs_conceded, wickets
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    team_id = VALUES(team_id),
                    balls_bowled = VALUES(balls_bowled),
                    maidens = VALUES(maidens),
                    runs_conceded = VALUES(runs_conceded),
                    wickets = VALUES(wickets)
                """,
                (
                    record["match_id"],
                    record["innings_no"],
                    record["player_id"],
                    record["team_id"],
                    record["balls_bowled"],
                    record["maidens"],
                    record["runs_conceded"],
                    record["wickets"],
                ),
            )

        # 8. Partnerships: replace this match's rows to avoid duplicates
        cursor.execute("DELETE FROM partnerships WHERE match_id = %s", (match_id,))

        for record in partnerships:
            cursor.execute(
                """
                INSERT INTO partnerships (
                    match_id, innings_no, team_id, wicket_number,
                    player1_id, player2_id,
                    player1_position, player2_position,
                    runs, balls
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record["match_id"],
                    record["innings_no"],
                    record["team_id"],
                    record["wicket_number"],
                    record["player1_id"],
                    record["player2_id"],
                    record["player1_position"],
                    record["player2_position"],
                    record["runs"],
                    record["balls"],
                ),
            )

        conn.commit()
        print(
            f"Saved scorecard for match {match_id}: "
            f"{len(batting)} batting, {len(bowling)} bowling, "
            f"{len(partnerships)} partnerships, {len(team_innings)} team innings."
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
        