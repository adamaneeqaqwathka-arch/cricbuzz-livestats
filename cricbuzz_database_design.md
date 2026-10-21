# Phase 4: MySQL Database Design — Cricbuzz Cricket Analytics

> **Status:** Revised draft (v2). Checked against all 25 SQL questions. Review the open items in Section 8 before writing the `CREATE TABLE` statements.

## 1. Design principles

- **Use Cricbuzz IDs as primary keys** (`matchId`, `teamId`, venue `id`, `playerId`) instead of `AUTO_INCREMENT`. Re-fetching data then uses `INSERT ... ON DUPLICATE KEY UPDATE` and never creates duplicates.
- **Store balls, not overs.** Cricbuzz overs such as `19.6` are awkward to calculate with. Store `balls_bowled` and convert for display.
- **Model innings explicitly.** Several questions are "per innings", so player and team data hang off an innings, not just a match.
- **Career totals are their own table.** Questions about career runs, averages, and centuries cannot be rebuilt from partial match data.

## 2. Entities

| Table | Purpose |
|---|---|
| `teams` | Team names, abbreviations, country, international flag |
| `venues` | Ground, city, country, capacity |
| `series` | Series name, host country, match type, dates, planned matches |
| `players` | Player profile, role, batting and bowling style |
| `matches` | Match header, teams, venue, toss, result |
| `team_innings` | One row per team per innings: score, wickets, balls, batting-first flag |
| `batting_innings` | One row per batter per innings |
| `bowling_innings` | One row per bowler per innings |
| `partnerships` | Batting partnerships per innings |
| `player_career_stats` | Career totals per player per format |

## 3. Table definitions

### 3.1 `teams`

```text
team_id            INT, PRIMARY KEY (Cricbuzz teamId)
team_name          VARCHAR(100), NOT NULL
team_short_name    VARCHAR(20)
country            VARCHAR(100)
is_international   BOOLEAN, DEFAULT FALSE   -- needed for home/away (Q12)
```

### 3.2 `venues`

```text
venue_id           INT, PRIMARY KEY (Cricbuzz venue id)
venue_name         VARCHAR(200), NOT NULL
city               VARCHAR(100)
country            VARCHAR(100)
capacity           INT, nullable
timezone           VARCHAR(10)
```

### 3.3 `series`

```text
series_id          INT, PRIMARY KEY
series_name        VARCHAR(200), NOT NULL
host_country       VARCHAR(100)
match_type         VARCHAR(20)        -- Test / ODI / T20I / Domestic
start_date         DATE
end_date           DATE
total_matches      INT                -- planned matches (Q8)
```

### 3.4 `players`

```text
player_id          INT, PRIMARY KEY
player_name        VARCHAR(100), NOT NULL
country            VARCHAR(100)
role               VARCHAR(50)        -- Batsman / Bowler / All-rounder / Wicket-keeper
batting_style      VARCHAR(50)
bowling_style      VARCHAR(50)
date_of_birth      DATE, nullable
```

### 3.5 `matches`

```text
match_id              INT, PRIMARY KEY
series_id             INT, FOREIGN KEY -> series.series_id
team1_id              INT, FOREIGN KEY -> teams.team_id
team2_id              INT, FOREIGN KEY -> teams.team_id
venue_id              INT, FOREIGN KEY -> venues.venue_id
match_desc            VARCHAR(100)       -- e.g. "2nd Test" (Q2, Q10)
match_format          VARCHAR(20)        -- TEST / ODI / T20
match_date            DATETIME
match_status          VARCHAR(200)
state                 VARCHAR(30)        -- Live / Complete / Upcoming
toss_winner_team_id   INT, FOREIGN KEY -> teams.team_id, nullable   (Q17)
toss_decision         VARCHAR(10), nullable                         -- bat / bowl
winner_team_id        INT, FOREIGN KEY -> teams.team_id, nullable
victory_margin        INT, nullable                                 (Q10, Q15, Q22)
victory_type          VARCHAR(10), nullable                         -- runs / wickets
```

`team1_id` and `team2_id` both reference `teams.team_id`. They are two roles of the same entity.

### 3.6 `team_innings`

```text
team_innings_id    INT, PRIMARY KEY AUTO_INCREMENT
match_id           INT, FOREIGN KEY -> matches.match_id
innings_no         INT, NOT NULL
team_id            INT, FOREIGN KEY -> teams.team_id
runs               INT
wickets            INT
balls              INT
extras             INT
batting_first      BOOLEAN            -- needed for Q22
UNIQUE (match_id, innings_no)
```

### 3.7 `batting_innings`

```text
batting_id         INT, PRIMARY KEY AUTO_INCREMENT
match_id           INT, FOREIGN KEY -> matches.match_id
innings_no         INT, NOT NULL
player_id          INT, FOREIGN KEY -> players.player_id
team_id            INT, FOREIGN KEY -> teams.team_id
batting_position   INT                -- Q13, Q24 (consecutive batsmen)
runs               INT
balls              INT
fours              INT
sixes              INT
is_out             BOOLEAN            -- batting average denominator
dismissal_type     VARCHAR(50), nullable
UNIQUE (match_id, innings_no, player_id)
```

### 3.8 `bowling_innings`

```text
bowling_id         INT, PRIMARY KEY AUTO_INCREMENT
match_id           INT, FOREIGN KEY -> matches.match_id
innings_no         INT, NOT NULL
player_id          INT, FOREIGN KEY -> players.player_id
team_id            INT, FOREIGN KEY -> teams.team_id
balls_bowled       INT
maidens            INT
runs_conceded      INT
wickets            INT
UNIQUE (match_id, innings_no, player_id)
```

### 3.9 `partnerships`

```text
partnership_id     INT, PRIMARY KEY AUTO_INCREMENT
match_id           INT, FOREIGN KEY -> matches.match_id
innings_no         INT, NOT NULL
team_id            INT, FOREIGN KEY -> teams.team_id
player1_id         INT, FOREIGN KEY -> players.player_id
player2_id         INT, FOREIGN KEY -> players.player_id
player1_position   INT
player2_position   INT
wicket_number      INT
runs               INT
balls              INT
```

### 3.10 `player_career_stats`

```text
player_id          INT, FOREIGN KEY -> players.player_id
format             VARCHAR(10)        -- TEST / ODI / T20I
matches            INT
innings            INT
runs               INT
batting_avg        DECIMAL(6,2)
strike_rate        DECIMAL(6,2)
highest_score      INT
centuries          INT
fifties            INT
wickets            INT
bowling_avg        DECIMAL(6,2)
economy            DECIMAL(4,2)
catches            INT
stumpings          INT
PRIMARY KEY (player_id, format)
```

## 4. Relationships

```text
series 1 ───────< matches >─────── 1 venues
                     │
              ┌──────┴──────┐
            teams         teams
          (team1_id)    (team2_id)

matches 1 ───< team_innings
matches 1 ───< batting_innings >─── 1 players
matches 1 ───< bowling_innings >─── 1 players
matches 1 ───< partnerships    >─── 2 players
players 1 ───< player_career_stats
```

- One series has many matches.
- Each match has two teams, one venue, and optionally one winner and one toss winner.
- A match has one or more innings. Each innings has batting rows, bowling rows, and partnerships.
- A player has one career row per format.

## 5. Indexes

| Index | Used by |
|---|---|
| `matches(match_date)` | Q2, Q10, Q16 (date filters, recent matches) |
| `matches(venue_id)` | Q4, Q12, Q14 |
| `matches(series_id)` | Q8 |
| `batting_innings(player_id, match_id)` | Q11, Q15, Q19, Q23, Q25 |
| `bowling_innings(player_id, match_id)` | Q14, Q18 |
| `partnerships(match_id, innings_no)` | Q13, Q24 |
| `players(country)` | Q1 |

Primary keys and foreign keys are indexed automatically in InnoDB.

## 6. Constraints

- `NOT NULL` on names and on columns used in joins.
- `UNIQUE` on `(match_id, innings_no, player_id)` for batting and bowling rows.
- `CHECK (runs >= 0)` and similar checks for non-negative stats (MySQL 8.0.16+).
- Use `ON DELETE RESTRICT` for most foreign keys, so a team or player in use cannot be deleted. The CRUD page should show a clear message when a delete is blocked.

## 7. Question-to-table mapping

| Questions | Tables |
|---|---|
| Q1, Q6 | `players` |
| Q2, Q10 | `matches`, `teams`, `venues` |
| Q3, Q7, Q9, Q20, Q21 | `player_career_stats`, `players` (Q21 also needs fielding columns) |
| Q4 | `venues` |
| Q5 | `matches`, `teams` |
| Q8 | `series` |
| Q11 | `player_career_stats` |
| Q12 | `matches`, `teams`, `venues` |
| Q13, Q24 | `partnerships`, `players` (or `batting_innings` for positions) |
| Q14, Q18 | `bowling_innings`, `matches`, `venues` |
| Q15, Q16, Q19, Q23, Q25 | `batting_innings`, `matches`, `players` |
| Q17 | `matches` (toss columns) |
| Q22 | `matches`, `team_innings`, `venues` |

## 8. Open items and risks

1. **Free API quota:** the free plan has a small request limit, so full historical data will not be available. Plan on loading what the API provides, plus seed or sample data for the heavy analytics queries (Q22–Q25). The project asks for sample data anyway.
2. **API gaps:** the live matches endpoint only fills `teams`, `venues`, `series`, and `matches`. Players, scorecards, partnerships, and career stats need other Cricbuzz endpoints (player info, match scorecard, player career stats).
3. **Venue capacity and country** are not in the live matches response. They may need another endpoint or manual seed data (Q4, Q12).
4. **Team country** must be filled for international teams so home/away can be compared with the venue country (Q12).
5. **Verify the exact wording** of each question once more before finalizing columns, especially Q21 (fielding stats) and Q9 (which format a player's totals belong to).

## 9. Next steps

1. Confirm MySQL is running: `mysql -u root -p`.
2. Create the database: `CREATE DATABASE cricbuzz_db;`.
3. Write the `CREATE TABLE` statements in `sql/schema.sql`, starting with the tables that have no foreign keys: `teams`, `venues`, `series`, `players`. Then `matches`, then the innings tables, partnerships, and career stats.
4. Write `utils/db_connection.py` and test the connection from Python.
5. Insert the 25 live matches from `fetch_live_matches()` into `teams`, `venues`, `series`, and `matches`.