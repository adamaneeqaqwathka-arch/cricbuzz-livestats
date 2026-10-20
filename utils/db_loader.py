from utils.db_connection import get_connection


def save_live_matches(matches):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for m in matches:
            # 1. Insert or update team 1
            if m.get("team1_id") is not None:
                cursor.execute(
                    """
                    INSERT INTO teams (
                        team_id, team_name, team_short_name
                    )
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        team_name = VALUES(team_name),
                        team_short_name = VALUES(team_short_name)
                    """,
                    (
                        m["team1_id"],
                        m.get("team1"),
                        m.get("team1_short"),
                    ),
                )

            # 2. Insert or update team 2
            if m.get("team2_id") is not None:
                cursor.execute(
                    """
                    INSERT INTO teams (
                        team_id, team_name, team_short_name
                    )
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        team_name = VALUES(team_name),
                        team_short_name = VALUES(team_short_name)
                    """,
                    (
                        m["team2_id"],
                        m.get("team2"),
                        m.get("team2_short"),
                    ),
                )

            # 3. Insert or update venue
            if m.get("venue_id") is not None:
                cursor.execute(
                    """
                    INSERT INTO venues (
                        venue_id, venue_name, city, country
                    )
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        venue_name = VALUES(venue_name)
                    """,
                    (
                        m["venue_id"],
                        m.get("venue"),
                        m.get("city"),
                        m.get("country"),
                    ),
                )

            # 4. Insert or update series
            if m.get("series_id") is not None:
                cursor.execute(
                    """
                    INSERT INTO series (
                        series_id, series_name
                    )
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        series_name = VALUES(series_name)
                    """,
                    (
                        m["series_id"],
                        m.get("series_name") or "Unknown Series",
                    ),
                )

            # 5. Insert or update match
            cursor.execute(
                """
                INSERT INTO matches (
                    match_id,
                    series_id,
                    team1_id,
                    team2_id,
                    venue_id,
                    match_desc,
                    match_format,
                    match_date,
                    match_status,
                    state
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    match_format = VALUES(match_format),
                    match_date = VALUES(match_date),
                    series_id = VALUES(series_id),
                    team1_id = VALUES(team1_id),
                    team2_id = VALUES(team2_id),
                    venue_id = VALUES(venue_id),
                    match_status = VALUES(match_status),
                    state = VALUES(state)
                """,
                (
                    m["match_id"],
                    m.get("series_id"),
                    m.get("team1_id"),
                    m.get("team2_id"),
                    m.get("venue_id"),
                    m.get("match_desc"),
                    m.get("format"),
                    m.get("start_date"),
                    m.get("status"),
                    m.get("state"),
                ),
            )

        conn.commit()
        print(f"Successfully saved {len(matches)} live matches.")

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()