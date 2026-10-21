"""Parse a Cricbuzz scorecard response into rows for the innings tables."""


def overs_to_balls(overs):
    """Convert cricket overs (e.g. 18.5 = 18 overs 5 balls) to balls."""
    if overs is None:
        return None
    whole, _, part = str(overs).partition(".")
    try:
        return int(whole) * 6 + (int(part) if part else 0)
    except ValueError:
        return None


def _extras_total(extras):
    """Return the total extras whether the API sends a number or a dict."""
    if isinstance(extras, dict):
        return extras.get("total")
    return extras


def parse_scorecard(data, match_id, team_ids):
    """Flatten a scorecard into rows for the innings tables.

    team_ids is a dict like {"Ireland": 27, "USA": 99} for this match,
    so we can turn a team name into a team_id.

    Returns four lists: batting, bowling, partnerships, team_innings.
    """
    batting, bowling, partnerships, team_innings = [], [], [], []

    innings_list = data.get("scorecard", [])
    if not innings_list:
        return batting, bowling, partnerships, team_innings

    # The team that batted in the first innings is the team that batted first
    first_team_id = team_ids.get(innings_list[0].get("batteamname"))

    for inn in innings_list:
        innings_no = inn["inningsid"]
        team_id = team_ids.get(inn.get("batteamname"))

        # The bowling team is the other team in this match
        others = [tid for tid in team_ids.values() if tid != team_id]
        bowling_team_id = others[0] if others else None

        team_innings.append({
            "match_id": match_id,
            "innings_no": innings_no,
            "team_id": team_id,
            "runs": inn.get("score"),
            "wickets": inn.get("wickets"),
            "balls": overs_to_balls(inn.get("overs")),
            "extras": _extras_total(inn.get("extras")),
            "batting_first": team_id == first_team_id,
        })

        # Batting
        position_of = {}
        for position, b in enumerate(inn.get("batsman", []), start=1):
            # Players who did not bat have an empty dismissal text
            if not b.get("outdec"):
                continue
            position_of[b["id"]] = position
            batting.append({
                "match_id": match_id,
                "innings_no": innings_no,
                "player_id": b["id"],
                "player_name": b["name"],
                "team_id": team_id,
                "batting_position": position,
                "runs": b.get("runs"),
                "balls": b.get("balls"),
                "fours": b.get("fours"),
                "sixes": b.get("sixes"),
                "is_out": b.get("outdec") != "not out",
                "dismissal_type": b.get("outdec"),
            })

        # Bowling (the API already gives balls bowled)
        for bw in inn.get("bowler", []):
            bowling.append({
                "match_id": match_id,
                "innings_no": innings_no,
                "player_id": bw["id"],
                "player_name": bw["name"],
                "team_id": bowling_team_id,
                "balls_bowled": bw.get("balls"),
                "maidens": bw.get("maidens"),
                "runs_conceded": bw.get("runs"),
                "wickets": bw.get("wickets"),
            })

        # Partnerships (wicket number = order in the list)
        partnership_data = inn.get("partnership", {})
        # The API nests the list: {"partnership": [ ... ]}
        if isinstance(partnership_data, dict):
            partnership_list = partnership_data.get("partnership", [])
        else:
            partnership_list = partnership_data

        for wicket_no, p in enumerate(partnership_list, start=1):
            partnerships.append({
                "match_id": match_id,
                "innings_no": innings_no,
                "team_id": team_id,
                "player1_id": p.get("bat1id"),
                "player2_id": p.get("bat2id"),
                "player1_position": position_of.get(p.get("bat1id")),
                "player2_position": position_of.get(p.get("bat2id")),
                "wicket_number": wicket_no,
                "runs": p.get("totalruns"),
                "balls": p.get("totalballs"),
            })

    return batting, bowling, partnerships, team_innings