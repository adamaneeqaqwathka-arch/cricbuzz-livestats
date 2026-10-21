--Q1: List all players from India with their playing role, batting style, and bowling style
SELECT
player_name AS full_name,
role AS playing_role,
batting_style,
bowling_style
FROM players
WHERE country = 'India';

CREATE INDEX idx_players_country ON players (country);

-- Q2: Show cricket matches played in the last 30 days
SELECT
    m.match_desc,
    t1.team_name AS team1,
    t2.team_name AS team2,
    v.venue_name,
    v.city,
    m.match_date
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN venues v ON m.venue_id = v.venue_id
WHERE m.match_date >= NOW() - INTERVAL 30 DAY
  AND m.match_date <= NOW()
ORDER BY m.match_date DESC;

-- Q3: Top 10 highest run scorers in ODI cricket
SELECT
    p.player_name AS player_name,
    pcs.runs AS total_runs,
    pcs.batting_avg AS batting_average,
    pcs.centuries AS centuries
FROM player_career_stats pcs
JOIN players p
    ON pcs.player_id = p.player_id
WHERE pcs.format = 'ODI'
ORDER BY pcs.runs DESC
LIMIT 10;

-- Q4: Display venues with seating capacity greater than 50,000
SELECT
    venue_name AS venue_name,
    city AS city,
    country AS country,
    capacity AS capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;

-- Q5: Count wins for each team
SELECT
    t.team_name AS team_name,
    COUNT(*) AS total_wins
FROM matches m
JOIN teams t
    ON m.winner_team_id = t.team_id
GROUP BY t.team_id, t.team_name
ORDER BY total_wins DESC, t.team_name ASC;