"""Turn Cricbuzz player responses into rows for players and player_career_stats."""

# API column name -> value stored in player_career_stats.format
# (IPL and other leagues are skipped on purpose)
FORMAT_MAP = {"Test": "Test", "ODI": "ODI", "T20": "T20I"}


def _to_number(text, cast=float):
    """Convert API text like '46.85' or '-' to a number, or None."""
    if text is None:
        return None
    text = str(text).strip()
    if text in ("", "-", "--", "N/A"):
        return None
    try:
        return cast(text)
    except ValueError:
        return None


def table_to_dict(table):
    """Pivot a Cricbuzz stats table into {column: {row label: value}}.

    The API sends {"headers": ["ROWHEADER", "Test", "ODI", ...],
    "values": [{"values": ["Matches", "123", "317", ...]}, ...]}.
    The result looks like {"Test": {"Matches": "123", "Runs": "9230"}, ...}.
    """
    headers = table.get("headers", [])[1:]
    result = {header: {} for header in headers}

    for row in table.get("values", []):
        cells = row.get("values", [])
        if not cells:
            continue
        label = cells[0]
        for header, value in zip(headers, cells[1:]):
            result[header][label] = value

    return result


def parse_player_profile(profile):
    """Return one dict for the players table from a player profile response."""
    return {
        "player_id": _to_number(profile.get("id"), int),
        "player_name": profile.get("fullName") or profile.get("name"),
        "country": profile.get("intlTeam"),
        "role": profile.get("role"),
        "batting_style": profile.get("bat"),
        "bowling_style": profile.get("bowl"),
    }


def parse_career_stats(player_id, batting_table, bowling_table):
    """Return a list of dicts for player_career_stats, one per format."""
    batting = table_to_dict(batting_table)
    bowling = table_to_dict(bowling_table)

    rows = []
    for api_format, db_format in FORMAT_MAP.items():
        bat = batting.get(api_format)
        bowl = bowling.get(api_format, {})
        if not bat:
            continue

        wickets = _to_number(bowl.get("Wickets"), int)

        rows.append({
            "player_id": player_id,
            "format": db_format,
            "matches": _to_number(bat.get("Matches"), int),
            "innings": _to_number(bat.get("Innings"), int),
            "runs": _to_number(bat.get("Runs"), int),
            "batting_avg": _to_number(bat.get("Average")),
            "strike_rate": _to_number(bat.get("SR")),
            "highest_score": _to_number(bat.get("Highest"), int),
            "centuries": _to_number(bat.get("100s"), int),
            "fifties": _to_number(bat.get("50s"), int),
            "wickets": wickets,
            # A bowling average of 0.0 with no wickets is meaningless
            "bowling_avg": _to_number(bowl.get("Avg")) if wickets else None,
            "economy": _to_number(bowl.get("Eco")),
            # Not available from the API; filled later from sample data
            "catches": None,
            "stumpings": None,
        })

    return rows

