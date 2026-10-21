"""Save a player profile and career stats into MySQL."""

from utils.db_connection import get_connection
from utils.player_parser import parse_career_stats, parse_player_profile


def save_player(profile, batting_table, bowling_table):
    """Save one player and their career stats, transactionally.

    Safe to run more than once: existing rows are updated, not duplicated.
    """
    player = parse_player_profile(profile)
    if player["player_id"] is None:
        raise ValueError("Profile has no player id")

    career_rows = parse_career_stats(
        player["player_id"], batting_table, bowling_table
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Player first (player_career_stats has a foreign key to players)
        cursor.execute(
            """
            INSERT INTO players (
                player_id, player_name, country, role,
                batting_style, bowling_style
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                player_name = VALUES(player_name),
                country = VALUES(country),
                role = VALUES(role),
                batting_style = VALUES(batting_style),
                bowling_style = VALUES(bowling_style)
            """,
            (
                player["player_id"],
                player["player_name"],
                player["country"],
                player["role"],
                player["batting_style"],
                player["bowling_style"],
            ),
        )

        # 2. One career row per format.
        # catches and stumpings are inserted but not overwritten on update,
        # because the API does not provide them and they may be filled in
        # later from sample data.
        for row in career_rows:
            cursor.execute(
                """
                INSERT INTO player_career_stats (
                    player_id, format, matches, innings, runs,
                    batting_avg, strike_rate, highest_score,
                    centuries, fifties, wickets, bowling_avg,
                    economy, catches, stumpings
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    matches = VALUES(matches),
                    innings = VALUES(innings),
                    runs = VALUES(runs),
                    batting_avg = VALUES(batting_avg),
                    strike_rate = VALUES(strike_rate),
                    highest_score = VALUES(highest_score),
                    centuries = VALUES(centuries),
                    fifties = VALUES(fifties),
                    wickets = VALUES(wickets),
                    bowling_avg = VALUES(bowling_avg),
                    economy = VALUES(economy)
                """,
                (
                    row["player_id"],
                    row["format"],
                    row["matches"],
                    row["innings"],
                    row["runs"],
                    row["batting_avg"],
                    row["strike_rate"],
                    row["highest_score"],
                    row["centuries"],
                    row["fifties"],
                    row["wickets"],
                    row["bowling_avg"],
                    row["economy"],
                    row["catches"],
                    row["stumpings"],
                ),
            )

        conn.commit()
        print(
            f"Saved {player['player_name']} "
            f"with {len(career_rows)} career format rows."
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()