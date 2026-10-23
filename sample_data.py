"""Generate SAMPLE cricket data so that all 25 SQL questions can be tested.

Everything created here is synthetic. It is NOT real cricket data.
All sample rows use IDs >= 90,000,000, so they can never clash with real
Cricbuzz IDs, and they can be removed at any time.

What it creates:
  * 4 sample national teams (Sample India, Sample Australia, ...)
  * 44 sample players (11 per team, fixed batting order, bowlers at 6-10)
  * 3 sample series (2024, 2025, 2026)
  * 132 completed matches (2024 Q1 to 2026 Q3): every pair of teams plays
    twice per quarter, one ODI and one T20, each at the home team's venue
  * toss, results, team innings, batting, bowling and partnerships

Requirements: run sql/seed_venues.sql first (the home venues come from it).

Usage:
    python generate_sample_data.py           # (re)create the sample data
    python generate_sample_data.py --clean   # remove all sample data
"""

import random
import sys
from datetime import date, datetime, timedelta

from utils.db_connection import get_connection

BASE = 90_000_000
START_YEAR = 2024
QUARTERS = 11  # 2024 Q1 ... 2026 Q3

random.seed(2026)  # same data every run

# (team name, short name, country, home venue_id from seed_venues.sql)
TEAMS = [
    ("Sample India", "SIND", "India", 900003),               # Eden Gardens
    ("Sample Australia", "SAUS", "Australia", 900002),       # MCG
    ("Sample England", "SENG", "England", 900008),           # Lords
    ("Sample South Africa", "SRSA", "South Africa", 900009), # Newlands
]

# Roles by batting position 1..11. Positions 6-10 are the five bowlers.
ROLES = (
    ["Batsman"] * 3
    + ["WK-Batsman", "Batting Allrounder", "Bowling Allrounder"]
    + ["Bowler"] * 5
)
BOWLING_STYLES = ["Right-arm fast", "Right-arm medium", "Left-arm orthodox",
                  "Right-arm offbreak", "Right-arm legbreak"]

# Average runs by batting position (ODI scale; T20 is scaled by 0.6)
POSITION_MEAN = {1: 35, 2: 35, 3: 35, 4: 30, 5: 28, 6: 20,
                 7: 15, 8: 10, 9: 7, 10: 5, 11: 4}
FULL_BALLS = {"ODI": 300, "T20": 120}
FORMAT_SCALE = {"ODI": 1.0, "T20": 0.6}

DISMISSALS = ["b {b}", "c {f} b {b}", "lbw b {b}", "run out ({f})"]


def clean(cursor):
    """Delete all sample rows (children first, because of foreign keys)."""
    for table, column in [
        ("partnerships", "match_id"),
        ("batting_innings", "match_id"),
        ("bowling_innings", "match_id"),
        ("team_innings", "match_id"),
        ("matches", "match_id"),
        ("series", "series_id"),
        ("players", "player_id"),
        ("teams", "team_id"),
    ]:
        cursor.execute(f"DELETE FROM {table} WHERE {column} >= %s", (BASE,))


def quarter_start(index):
    year = START_YEAR + index // 4
    month = 1 + (index % 4) * 3
    return date(year, month, 1)


def gen_batting(squad, bowler_names, quarter_index, fmt, wickets, slopes):
    """Create batting rows for one innings. Returns (rows, extras, total)."""
    scale = FORMAT_SCALE[fmt]
    batted = min(wickets + 2, 11)
    rows = []

    for position in range(1, batted + 1):
        player_id, _ = squad[position - 1]
        # Each player drifts up or down over time, so trends exist (Q23, Q25)
        factor = max(0.2, 1 + slopes[player_id] * (quarter_index - 5) / 5)
        mean = max(1.0, POSITION_MEAN[position] * scale * factor)
        runs = min(160, int(random.expovariate(1.0 / mean)))

        if runs == 0:
            balls = random.randint(1, 8)
        else:
            if fmt == "ODI":
                strike_rate = random.uniform(70, 115)
            else:
                strike_rate = random.uniform(100, 160)
            balls = max(1, round(runs * 100 / strike_rate))

        is_out = position <= wickets
        if is_out:
            dismissal = random.choice(DISMISSALS).format(
                b=random.choice(bowler_names), f=random.choice(bowler_names)
            )
        else:
            dismissal = "not out"

        rows.append({
            "player_id": player_id,
            "position": position,
            "runs": runs,
            "balls": balls,
            "fours": int(runs * random.uniform(0.3, 0.5) / 4),
            "sixes": int(runs * random.uniform(0.0, 0.2) / 6),
            "is_out": is_out,
            "dismissal": dismissal,
        })

    extras = random.randint(2, 12)
    total = sum(r["runs"] for r in rows) + extras
    return rows, extras, total


def gen_bowling(bowlers, balls, runs, wickets):
    """Split an innings between five bowlers so the totals add up."""
    n = len(bowlers)
    per, remainder = divmod(balls, n)
    balls_each = [per + (1 if i < remainder else 0) for i in range(n)]

    wickets_each = [0] * n
    for _ in range(wickets):
        wickets_each[random.randrange(n)] += 1

    weights = [b * random.uniform(0.7, 1.3) for b in balls_each]
    weight_sum = sum(weights) or 1
    runs_each = [int(round(runs * w / weight_sum)) for w in weights]
    runs_each[-1] = max(0, runs - sum(runs_each[:-1]))

    rows = []
    for i, (player_id, _) in enumerate(bowlers):
        rows.append({
            "player_id": player_id,
            "balls": balls_each[i],
            "maidens": 1 if (balls_each[i] >= 6 and random.random() < 0.08) else 0,
            "runs": runs_each[i],
            "wickets": wickets_each[i],
        })
    return rows


def gen_partnerships(batters, batter_runs_total, innings_balls):
    """Partnerships between consecutive batting positions.

    Runs and balls are shared out in proportion to the two batters' scores,
    so the partnerships add up to the batters' runs.
    """
    pairs = list(zip(batters[:-1], batters[1:]))
    weights = [a["runs"] + b["runs"] + 1 for a, b in pairs]
    weight_sum = sum(weights)

    runs_each = [int(round(batter_runs_total * w / weight_sum)) for w in weights]
    runs_each[-1] = max(0, batter_runs_total - sum(runs_each[:-1]))
    balls_each = [max(1, int(round(innings_balls * w / weight_sum))) for w in weights]

    rows = []
    for index, (a, b) in enumerate(pairs):
        rows.append({
            "wicket_number": index + 1,
            "player1_id": a["player_id"],
            "player2_id": b["player_id"],
            "player1_position": a["position"],
            "player2_position": b["position"],
            "runs": runs_each[index],
            "balls": balls_each[index],
        })
    return rows


def generate(cursor):
    # Home venues must exist (they come from sql/seed_venues.sql)
    venue_ids = [t[3] for t in TEAMS]
    cursor.execute(
        "SELECT venue_id FROM venues WHERE venue_id IN (%s, %s, %s, %s)",
        venue_ids,
    )
    found = {row[0] for row in cursor.fetchall()}
    missing = set(venue_ids) - found
    if missing:
        raise RuntimeError(
            f"Venues {sorted(missing)} are missing. "
            "Run: mysql -u root -p cricbuzz_db < sql/seed_venues.sql"
        )

    clean(cursor)

    # ---- teams and players ----
    team_ids = [BASE + 1 + i for i in range(len(TEAMS))]
    squads = []  # squads[team_index] = [(player_id, player_name), ...]
    slopes = {}
    team_rows, player_rows = [], []

    for i, (name, short, country, _venue) in enumerate(TEAMS):
        team_rows.append((team_ids[i], name, short, country, True))
        squad = []
        for n in range(1, 12):
            player_id = BASE + 1000 + i * 100 + n
            player_name = f"{name} Player {n}"
            squad.append((player_id, player_name))
            slopes[player_id] = random.uniform(-0.6, 0.6)
            style = random.choice(BOWLING_STYLES) if 6 <= n <= 10 else None
            # country is left empty so that Q1 (players from India) only
            # returns real players
            player_rows.append(
                (player_id, player_name, None, ROLES[n - 1],
                 "Right Handed Bat", style)
            )
        squads.append(squad)

    cursor.executemany(
        "INSERT INTO teams (team_id, team_name, team_short_name, country, "
        "is_international) VALUES (%s, %s, %s, %s, %s)", team_rows)
    cursor.executemany(
        "INSERT INTO players (player_id, player_name, country, role, "
        "batting_style, bowling_style) VALUES (%s, %s, %s, %s, %s, %s)",
        player_rows)

    # ---- matches ----
    matches, team_innings, batting, bowling, partnerships = [], [], [], [], []
    matches_per_year = {}
    match_no = 0

    for q in range(QUARTERS):
        start = quarter_start(q)
        fixtures = []
        for a in range(4):
            for b in range(a + 1, 4):
                fixtures.append((a, b, "ODI"))   # home, away, format
                fixtures.append((b, a, "T20"))
        random.shuffle(fixtures)

        for slot, (home, away, fmt) in enumerate(fixtures):
            match_no += 1
            match_id = BASE + match_no
            match_date = datetime.combine(
                start + timedelta(days=3 + slot * 7), datetime.min.time()
            ).replace(hour=14)
            year = start.year
            series_id = BASE + 1 + (year - START_YEAR)
            matches_per_year[year] = matches_per_year.get(year, 0) + 1

            toss_winner = random.choice([home, away])
            decision = random.choice(["bat", "bowl"])
            other = away if toss_winner == home else home
            first = toss_winner if decision == "bat" else other
            second = other if first == toss_winner else toss_winner

            full = FULL_BALLS[fmt]
            first_bowlers = squads[second][5:10]
            second_bowlers = squads[first][5:10]

            # Innings 1
            w1 = random.randint(5, 10)
            bat1, extras1, total1 = gen_batting(
                squads[first], [n for _, n in first_bowlers], q, fmt, w1, slopes)
            balls1 = full if w1 < 10 else random.randint(int(full * 0.6), full - 1)

            # Innings 2: choose the result first, then simulate until it fits
            chaser_wins = random.random() < 0.5
            for _ in range(500):
                w2 = random.randint(4, 10)
                bat2, extras2, total2 = gen_batting(
                    squads[second], [n for _, n in second_bowlers], q, fmt, w2, slopes)
                wins = total2 > total1
                if total2 != total1 and wins == chaser_wins and (not wins or w2 <= 9):
                    break
            if total2 > total1:
                balls2 = random.randint(int(full * 0.6), full - 1)
            else:
                balls2 = full if w2 < 10 else random.randint(int(full * 0.6), full - 1)

            if total2 > total1:
                winner, vtype, margin = second, "wickets", max(1, 10 - w2)
            else:
                winner, vtype, margin = first, "runs", max(0, total1 - total2)
            unit = "wkts" if vtype == "wickets" else "runs"
            status = f"{TEAMS[winner][0]} won by {margin} {unit}"

            matches.append((
                match_id, series_id, team_ids[home], team_ids[away],
                TEAMS[home][3], f"Sample Match {match_no}", fmt, match_date,
                status, "Complete", team_ids[toss_winner], decision,
                team_ids[winner], margin, vtype,
            ))

            # Team innings
            team_innings.append((match_id, 1, team_ids[first], total1, w1, balls1, extras1, True))
            team_innings.append((match_id, 2, team_ids[second], total2, w2, balls2, extras2, False))

            # Batting, bowling and partnerships for both innings
            for innings_no, rows, team, opp_bowlers, balls, runs_total, extras, wk in [
                (1, bat1, first, first_bowlers, balls1, total1, extras1, w1),
                (2, bat2, second, second_bowlers, balls2, total2, extras2, w2),
            ]:
                for r in rows:
                    batting.append((
                        match_id, innings_no, r["player_id"], team_ids[team],
                        r["position"], r["runs"], r["balls"], r["fours"],
                        r["sixes"], r["is_out"], r["dismissal"]))

                bowling_team = second if innings_no == 1 else first
                for r in gen_bowling(opp_bowlers, balls, runs_total - extras, wk):
                    bowling.append((
                        match_id, innings_no, r["player_id"],
                        team_ids[bowling_team], r["balls"], r["maidens"],
                        r["runs"], r["wickets"]))

                batter_runs = sum(r["runs"] for r in rows)
                for p in gen_partnerships(rows, batter_runs, balls):
                    partnerships.append((
                        match_id, innings_no, team_ids[team], p["wicket_number"],
                        p["player1_id"], p["player2_id"], p["player1_position"],
                        p["player2_position"], p["runs"], p["balls"]))

    # ---- series (inserted after counting matches per year) ----
    series_rows = []
    for year, count in sorted(matches_per_year.items()):
        series_rows.append((
            BASE + 1 + (year - START_YEAR), f"Sample Series {year}", "Various",
            "ODI/T20", date(year, 1, 1), date(year, 12, 31), count))
    cursor.executemany(
        "INSERT INTO series (series_id, series_name, host_country, match_type, "
        "start_date, end_date, total_matches) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        series_rows)

    cursor.executemany(
        "INSERT INTO matches (match_id, series_id, team1_id, team2_id, venue_id, "
        "match_desc, match_format, match_date, match_status, state, "
        "toss_winner_team_id, toss_decision, winner_team_id, victory_margin, "
        "victory_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
        "%s, %s, %s)", matches)
    cursor.executemany(
        "INSERT INTO team_innings (match_id, innings_no, team_id, runs, wickets, "
        "balls, extras, batting_first) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        team_innings)
    cursor.executemany(
        "INSERT INTO batting_innings (match_id, innings_no, player_id, team_id, "
        "batting_position, runs, balls, fours, sixes, is_out, dismissal_type) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", batting)
    cursor.executemany(
        "INSERT INTO bowling_innings (match_id, innings_no, player_id, team_id, "
        "balls_bowled, maidens, runs_conceded, wickets) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", bowling)
    cursor.executemany(
        "INSERT INTO partnerships (match_id, innings_no, team_id, wicket_number, "
        "player1_id, player2_id, player1_position, player2_position, runs, balls) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", partnerships)

    print(
        f"Created {len(team_rows)} teams, {len(player_rows)} players, "
        f"{len(series_rows)} series, {len(matches)} matches, "
        f"{len(batting)} batting rows, {len(bowling)} bowling rows, "
        f"{len(partnerships)} partnerships."
    )


def main():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if "--clean" in sys.argv:
            clean(cursor)
            print("Sample data removed.")
        else:
            generate(cursor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()