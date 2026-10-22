-- ============================================================
-- Cricbuzz LiveStats: the 25 SQL analytics questions (MySQL 8+)
-- Run prepare_data.sql and seed_venues.sql first.
-- Formats in player_career_stats are stored as 'Test', 'ODI', 'T20I'.
-- ============================================================


-- ===================== BEGINNER (Q1-Q8) =====================

-- Q1: Players who represent India
SELECT
    player_name   AS full_name,
    role          AS playing_role,
    batting_style,
    bowling_style
FROM players
WHERE country = 'India'
ORDER BY player_name;


-- Q2: Matches played in the last 30 days, most recent first
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


-- Q3: Top 10 ODI run scorers
SELECT
    p.player_name,
    pcs.runs        AS total_runs,
    pcs.batting_avg AS batting_average,
    pcs.centuries
FROM player_career_stats pcs
JOIN players p ON pcs.player_id = p.player_id
WHERE pcs.format = 'ODI'
ORDER BY pcs.runs DESC
LIMIT 10;


-- Q4: Venues with capacity above 50,000
SELECT venue_name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;


-- Q5: Matches won by each team
SELECT
    t.team_name,
    COUNT(*) AS total_wins
FROM matches m
JOIN teams t ON m.winner_team_id = t.team_id
GROUP BY t.team_id, t.team_name
ORDER BY total_wins DESC, t.team_name ASC;


-- Q6: Number of players in each playing role
-- (players without a profile have no role, so they are shown as 'Unknown')
SELECT
    COALESCE(role, 'Unknown') AS playing_role,
    COUNT(*)                  AS player_count
FROM players
GROUP BY COALESCE(role, 'Unknown')
ORDER BY player_count DESC;


-- Q7: Highest individual batting score in each format
SELECT
    format,
    MAX(highest_score) AS highest_score
FROM player_career_stats
GROUP BY format
ORDER BY highest_score DESC;


-- Q8: Series that started in 2024
-- NOTE: series.start_date etc. are empty until the loader stores them.
SELECT
    series_name,
    host_country,
    match_type,
    start_date,
    total_matches
FROM series
WHERE start_date >= '2024-01-01'
  AND start_date <  '2025-01-01'
ORDER BY start_date;


-- ================== INTERMEDIATE (Q9-Q16) ===================

-- Q9: All-rounders with more than 1000 runs AND more than 50 wickets
-- (Cricbuzz roles look like 'Batting Allrounder' / 'Bowling Allrounder')
SELECT
    p.player_name,
    c.runs   AS total_runs,
    c.wickets AS total_wickets,
    c.format
FROM player_career_stats c
JOIN players p ON c.player_id = p.player_id
WHERE p.role LIKE '%rounder%'
  AND c.runs > 1000
  AND c.wickets > 50
ORDER BY c.runs DESC;


-- Q10: Last 20 completed matches with winner, margin and venue
SELECT
    m.match_desc,
    t1.team_name AS team1,
    t2.team_name AS team2,
    w.team_name  AS winning_team,
    m.victory_margin,
    m.victory_type,
    v.venue_name
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
JOIN teams w  ON m.winner_team_id = w.team_id
LEFT JOIN venues v ON m.venue_id = v.venue_id
WHERE m.winner_team_id IS NOT NULL
ORDER BY m.match_date DESC
LIMIT 20;


-- Q11: Runs per format and overall batting average for players with 2+ formats.
-- Dismissals in a format = runs / average, so the overall average is
-- total runs / total dismissals across formats.
SELECT
    p.player_name,
    SUM(CASE WHEN c.format = 'Test' THEN c.runs END) AS test_runs,
    SUM(CASE WHEN c.format = 'ODI'  THEN c.runs END) AS odi_runs,
    SUM(CASE WHEN c.format = 'T20I' THEN c.runs END) AS t20i_runs,
    ROUND(SUM(c.runs) / SUM(c.runs / NULLIF(c.batting_avg, 0)), 2)
        AS overall_batting_avg
FROM player_career_stats c
JOIN players p ON c.player_id = p.player_id
GROUP BY p.player_id, p.player_name
HAVING COUNT(DISTINCT c.format) >= 2
ORDER BY overall_batting_avg DESC;


-- Q12: Home vs away wins for each international team
-- Home = venue country equals the team's country.
SELECT
    t.team_name,
    SUM(v.country =  t.country) AS home_wins,
    SUM(v.country <> t.country) AS away_wins
FROM matches m
JOIN teams t  ON t.team_id = m.winner_team_id
JOIN venues v ON v.venue_id = m.venue_id
WHERE t.is_international = TRUE
  AND t.country IS NOT NULL
  AND v.country IS NOT NULL
GROUP BY t.team_id, t.team_name
ORDER BY home_wins + away_wins DESC;


-- Q13: Partnerships of 100+ between consecutive batters in the same innings
SELECT
    p1.player_name AS batter_1,
    p2.player_name AS batter_2,
    pt.runs        AS partnership_runs,
    pt.innings_no,
    pt.match_id
FROM partnerships pt
JOIN players p1 ON p1.player_id = pt.player1_id
JOIN players p2 ON p2.player_id = pt.player2_id
WHERE ABS(pt.player1_position - pt.player2_position) = 1
  AND pt.runs >= 100
ORDER BY pt.runs DESC;


-- Q14: Bowling at venues: bowlers with 3+ matches at the same venue,
-- counting only innings with at least 4 overs (24 balls).
-- Economy = runs conceded * 6 / balls bowled.
SELECT
    p.player_name,
    v.venue_name,
    COUNT(DISTINCT b.match_id) AS matches_played,
    SUM(b.wickets)             AS total_wickets,
    ROUND(AVG(b.runs_conceded * 6 / b.balls_bowled), 2) AS avg_economy
FROM bowling_innings b
JOIN players p ON p.player_id = b.player_id
JOIN matches m ON m.match_id  = b.match_id
JOIN venues  v ON v.venue_id  = m.venue_id
WHERE b.balls_bowled >= 24
GROUP BY p.player_id, p.player_name, v.venue_id, v.venue_name
HAVING COUNT(DISTINCT b.match_id) >= 3
ORDER BY avg_economy ASC;


-- Q15: Players in close matches (won by < 50 runs OR < 5 wickets)
SELECT
    p.player_name,
    ROUND(AVG(b.runs), 2)      AS avg_runs_per_innings,
    COUNT(DISTINCT b.match_id) AS close_matches_played,
    COUNT(DISTINCT CASE WHEN b.team_id = m.winner_team_id
                        THEN b.match_id END) AS close_matches_won
FROM batting_innings b
JOIN matches m ON m.match_id  = b.match_id
JOIN players p ON p.player_id = b.player_id
WHERE m.winner_team_id IS NOT NULL
  AND (   (m.victory_type = 'runs'    AND m.victory_margin < 50)
       OR (m.victory_type = 'wickets' AND m.victory_margin < 5))
GROUP BY p.player_id, p.player_name
ORDER BY avg_runs_per_innings DESC;


-- Q16: Yearly batting trend since 2020 (players with 5+ matches in the year)
-- Strike rate = total runs * 100 / total balls.
SELECT
    p.player_name,
    YEAR(m.match_date) AS match_year,
    ROUND(SUM(b.runs) / COUNT(DISTINCT b.match_id), 2) AS avg_runs_per_match,
    ROUND(SUM(b.runs) * 100 / NULLIF(SUM(b.balls), 0), 2) AS avg_strike_rate
FROM batting_innings b
JOIN matches m ON m.match_id  = b.match_id
JOIN players p ON p.player_id = b.player_id
WHERE m.match_date >= '2020-01-01'
GROUP BY p.player_id, p.player_name, YEAR(m.match_date)
HAVING COUNT(DISTINCT b.match_id) >= 5
ORDER BY match_year, avg_runs_per_match DESC;


-- =================== ADVANCED (Q17-Q25) =====================

-- Q17: Does winning the toss help? Toss winner's win % by toss decision.
-- NOTE: needs toss_winner_team_id and toss_decision filled in.
SELECT
    m.toss_decision,
    COUNT(*) AS matches,
    SUM(m.toss_winner_team_id = m.winner_team_id) AS toss_winner_won,
    ROUND(100 * SUM(m.toss_winner_team_id = m.winner_team_id) / COUNT(*), 2)
        AS win_percentage
FROM matches m
WHERE m.toss_winner_team_id IS NOT NULL
  AND m.winner_team_id IS NOT NULL
GROUP BY m.toss_decision;


-- Q18: Most economical bowlers in ODI and T20 (10+ matches, 2+ overs a match)
SELECT
    p.player_name,
    ROUND(SUM(b.runs_conceded) * 6 / SUM(b.balls_bowled), 2) AS economy_rate,
    SUM(b.wickets)             AS total_wickets,
    COUNT(DISTINCT b.match_id) AS matches_bowled
FROM bowling_innings b
JOIN matches m ON m.match_id  = b.match_id
JOIN players p ON p.player_id = b.player_id
WHERE m.match_format IN ('ODI', 'T20')
GROUP BY p.player_id, p.player_name
HAVING COUNT(DISTINCT b.match_id) >= 10
   AND SUM(b.balls_bowled) / COUNT(DISTINCT b.match_id) >= 12
ORDER BY economy_rate ASC;

-- Q18 (career-stats version): works with the player profiles we loaded
SELECT
    p.player_name,
    c.format,
    c.economy AS economy_rate,
    c.wickets AS total_wickets,
    c.matches
FROM player_career_stats c
JOIN players p ON p.player_id = c.player_id
WHERE c.format IN ('ODI', 'T20I')
  AND c.matches >= 10
    AND c.wickets > 0
  AND c.economy IS NOT NULL
ORDER BY c.economy ASC
LIMIT 10;


-- Q19: Most consistent batters since 2022 (innings of 10+ balls).
-- Lower standard deviation = more consistent.
SELECT
    p.player_name,
    ROUND(AVG(b.runs), 2)         AS avg_runs,
    ROUND(STDDEV_SAMP(b.runs), 2) AS runs_std_dev,
    COUNT(*)                      AS innings
FROM batting_innings b
JOIN matches m ON m.match_id  = b.match_id
JOIN players p ON p.player_id = b.player_id
WHERE b.balls >= 10
  AND m.match_date >= '2022-01-01'
GROUP BY p.player_id, p.player_name
HAVING COUNT(*) >= 2          -- use a bigger number with real data
ORDER BY runs_std_dev ASC;


-- Q20: Matches and batting average per format (players with 20+ matches)
SELECT
    p.player_name,
    SUM(CASE WHEN c.format = 'Test' THEN c.matches END) AS test_matches,
    SUM(CASE WHEN c.format = 'ODI'  THEN c.matches END) AS odi_matches,
    SUM(CASE WHEN c.format = 'T20I' THEN c.matches END) AS t20_matches,
    MAX(CASE WHEN c.format = 'Test' THEN c.batting_avg END) AS test_avg,
    MAX(CASE WHEN c.format = 'ODI'  THEN c.batting_avg END) AS odi_avg,
    MAX(CASE WHEN c.format = 'T20I' THEN c.batting_avg END) AS t20_avg
FROM player_career_stats c
JOIN players p ON p.player_id = c.player_id
GROUP BY p.player_id, p.player_name
HAVING SUM(c.matches) >= 20
ORDER BY SUM(c.matches) DESC;


-- Q21: Weighted performance ranking per format (top 10 in each)
-- Players with no wickets get 0 bowling points; missing fielding data counts as 0.
WITH scored AS (
    SELECT
        p.player_name,
        c.format,
        COALESCE(c.runs, 0) * 0.01
          + COALESCE(c.batting_avg, 0) * 0.5
          + COALESCE(c.strike_rate, 0) * 0.3 AS batting_points,
        CASE
            WHEN COALESCE(c.wickets, 0) = 0 THEN 0
            ELSE c.wickets * 2
               + (50 - COALESCE(c.bowling_avg, 50)) * 0.5
               + (6 - COALESCE(c.economy, 6)) * 2
        END AS bowling_points,
        COALESCE(c.catches, 0) * 3 + COALESCE(c.stumpings, 0) * 5
            AS fielding_points
    FROM player_career_stats c
    JOIN players p ON p.player_id = c.player_id
),
ranked AS (
    SELECT
        s.*,
        s.batting_points + s.bowling_points + s.fielding_points AS total_points,
        RANK() OVER (
            PARTITION BY s.format
            ORDER BY s.batting_points + s.bowling_points + s.fielding_points DESC
        ) AS rank_in_format
    FROM scored s
)
SELECT
    format,
    rank_in_format,
    player_name,
    ROUND(batting_points, 2)  AS batting_points,
    ROUND(bowling_points, 2)  AS bowling_points,
    ROUND(fielding_points, 2) AS fielding_points,
    ROUND(total_points, 2)    AS total_points
FROM ranked
WHERE rank_in_format <= 10
ORDER BY format, rank_in_format;


-- Q22: Head-to-head analysis for team pairs with 5+ matches in the last 3 years
WITH pair_matches AS (
    SELECT
        m.match_id,
        LEAST(m.team1_id, m.team2_id)    AS team_a,
        GREATEST(m.team1_id, m.team2_id) AS team_b,
        m.winner_team_id,
        m.victory_margin,
        m.victory_type
    FROM matches m
    WHERE m.match_date >= NOW() - INTERVAL 3 YEAR
      AND m.match_date <= NOW()
      AND m.state = 'Complete'
)
SELECT
    ta.team_name AS team_a,
    tb.team_name AS team_b,
    COUNT(*)     AS total_matches,
    SUM(pm.winner_team_id = pm.team_a) AS team_a_wins,
    SUM(pm.winner_team_id = pm.team_b) AS team_b_wins,
    ROUND(AVG(CASE WHEN pm.winner_team_id = pm.team_a AND pm.victory_type = 'runs'
                   THEN pm.victory_margin END), 1) AS team_a_avg_runs_margin,
    ROUND(AVG(CASE WHEN pm.winner_team_id = pm.team_a AND pm.victory_type = 'wickets'
                   THEN pm.victory_margin END), 1) AS team_a_avg_wkts_margin,
    ROUND(AVG(CASE WHEN pm.winner_team_id = pm.team_b AND pm.victory_type = 'runs'
                   THEN pm.victory_margin END), 1) AS team_b_avg_runs_margin,
    ROUND(AVG(CASE WHEN pm.winner_team_id = pm.team_b AND pm.victory_type = 'wickets'
                   THEN pm.victory_margin END), 1) AS team_b_avg_wkts_margin,
    ROUND(100 * SUM(pm.winner_team_id = pm.team_a) / COUNT(*), 2) AS team_a_win_pct,
    ROUND(100 * SUM(pm.winner_team_id = pm.team_b) / COUNT(*), 2) AS team_b_win_pct
FROM pair_matches pm
JOIN teams ta ON ta.team_id = pm.team_a
JOIN teams tb ON tb.team_id = pm.team_b
GROUP BY pm.team_a, pm.team_b, ta.team_name, tb.team_name
HAVING COUNT(*) >= 5
ORDER BY total_matches DESC;

-- Q22 (part 2): batting first vs bowling first, by venue
SELECT
    ta.team_name AS team_a,
    tb.team_name AS team_b,
    v.venue_name,
    COUNT(*) AS matches,
    SUM(m.winner_team_id = ti.team_id) AS wins_batting_first,
    SUM(m.winner_team_id IS NOT NULL
        AND m.winner_team_id <> ti.team_id) AS wins_bowling_first
FROM matches m
JOIN team_innings ti ON ti.match_id = m.match_id AND ti.innings_no = 1
JOIN teams ta ON ta.team_id = LEAST(m.team1_id, m.team2_id)
JOIN teams tb ON tb.team_id = GREATEST(m.team1_id, m.team2_id)
JOIN venues v ON v.venue_id = m.venue_id
WHERE m.match_date >= NOW() - INTERVAL 3 YEAR
  AND m.state = 'Complete'
GROUP BY ta.team_id, ta.team_name, tb.team_id, tb.team_name,
         v.venue_id, v.venue_name
ORDER BY team_a, team_b, matches DESC;


-- Q23: Recent form from each player's last 10 batting innings
-- Form thresholds use the last-5 average: 50+ Excellent, 35+ Good, 20+ Average.
WITH recent AS (
    SELECT
        b.player_id,
        b.runs,
        b.balls,
        ROW_NUMBER() OVER (
            PARTITION BY b.player_id
            ORDER BY m.match_date DESC, b.innings_no DESC
        ) AS rn
    FROM batting_innings b
    JOIN matches m ON m.match_id = b.match_id
)
SELECT
    p.player_name,
    ROUND(AVG(CASE WHEN r.rn <= 5 THEN r.runs END), 2) AS avg_last_5,
    ROUND(AVG(r.runs), 2)                              AS avg_last_10,
    ROUND(SUM(CASE WHEN r.rn <= 5 THEN r.runs END) * 100
          / NULLIF(SUM(CASE WHEN r.rn <= 5 THEN r.balls END), 0), 2)
                                                       AS strike_rate_last_5,
    ROUND(SUM(r.runs) * 100 / NULLIF(SUM(r.balls), 0), 2)
                                                       AS strike_rate_last_10,
    SUM(r.runs >= 50)                                  AS scores_50_plus,
    ROUND(STDDEV_SAMP(r.runs), 2)                      AS consistency_std_dev,
    CASE
        WHEN AVG(CASE WHEN r.rn <= 5 THEN r.runs END) >= 50 THEN 'Excellent Form'
        WHEN AVG(CASE WHEN r.rn <= 5 THEN r.runs END) >= 35 THEN 'Good Form'
        WHEN AVG(CASE WHEN r.rn <= 5 THEN r.runs END) >= 20 THEN 'Average Form'
        ELSE 'Poor Form'
    END AS form_category
FROM recent r
JOIN players p ON p.player_id = r.player_id
WHERE r.rn <= 10
GROUP BY p.player_id, p.player_name
HAVING COUNT(*) >= 2          -- use 5+ with real data
ORDER BY avg_last_5 DESC;


-- Q24: Best batting partnerships between consecutive batters (5+ partnerships)
WITH pairs AS (
    SELECT
        LEAST(pt.player1_id, pt.player2_id)    AS player_a,
        GREATEST(pt.player1_id, pt.player2_id) AS player_b,
        pt.runs
    FROM partnerships pt
    WHERE ABS(pt.player1_position - pt.player2_position) = 1
),
stats AS (
    SELECT
        player_a,
        player_b,
        COUNT(*)                                  AS partnerships,
        ROUND(AVG(runs), 2)                       AS avg_runs,
        SUM(runs > 50)                            AS partnerships_over_50,
        MAX(runs)                                 AS highest_partnership,
        ROUND(100 * SUM(runs > 50) / COUNT(*), 2) AS success_rate
    FROM pairs
    GROUP BY player_a, player_b
    HAVING COUNT(*) >= 5
)
SELECT
    RANK() OVER (ORDER BY s.success_rate DESC, s.avg_runs DESC) AS ranking,
    p1.player_name AS batter_1,
    p2.player_name AS batter_2,
    s.partnerships,
    s.avg_runs,
    s.partnerships_over_50,
    s.highest_partnership,
    s.success_rate
FROM stats s
JOIN players p1 ON p1.player_id = s.player_a
JOIN players p2 ON p2.player_id = s.player_b
ORDER BY ranking;


-- Q25 (part 1): Quarterly batting trend per player
-- Players need 6+ quarters, each with 3+ matches.
-- Change vs previous quarter: +10% = Improving, -10% = Declining, else Stable.
WITH quarterly AS (
    SELECT
        b.player_id,
        YEAR(m.match_date)    AS yr,
        QUARTER(m.match_date) AS qtr,
        COUNT(DISTINCT b.match_id) AS matches,
        SUM(b.runs) / COUNT(DISTINCT b.match_id) AS avg_runs,
        SUM(b.runs) * 100 / NULLIF(SUM(b.balls), 0) AS strike_rate
    FROM batting_innings b
    JOIN matches m ON m.match_id = b.match_id
    GROUP BY b.player_id, YEAR(m.match_date), QUARTER(m.match_date)
    HAVING COUNT(DISTINCT b.match_id) >= 3
),
eligible AS (
    SELECT player_id FROM quarterly GROUP BY player_id HAVING COUNT(*) >= 6
),
trend AS (
    SELECT
        q.*,
        LAG(q.avg_runs)    OVER (PARTITION BY q.player_id ORDER BY q.yr, q.qtr) AS prev_avg_runs,
        LAG(q.strike_rate) OVER (PARTITION BY q.player_id ORDER BY q.yr, q.qtr) AS prev_strike_rate
    FROM quarterly q
    JOIN eligible e ON e.player_id = q.player_id
)
SELECT
    p.player_name,
    t.yr,
    t.qtr,
    ROUND(t.avg_runs, 2)    AS avg_runs,
    ROUND(t.strike_rate, 2) AS strike_rate,
    ROUND(t.avg_runs - t.prev_avg_runs, 2) AS runs_change,
    CASE
        WHEN t.prev_avg_runs IS NULL THEN 'First quarter'
        WHEN t.avg_runs > t.prev_avg_runs * 1.10 THEN 'Improving'
        WHEN t.avg_runs < t.prev_avg_runs * 0.90 THEN 'Declining'
        ELSE 'Stable'
    END AS trend
FROM trend t
JOIN players p ON p.player_id = t.player_id
ORDER BY p.player_name, t.yr, t.qtr;

-- Q25 (part 2): Career phase = first 3 quarters vs latest 3 quarters
WITH quarterly AS (
    SELECT
        b.player_id,
        YEAR(m.match_date)    AS yr,
        QUARTER(m.match_date) AS qtr,
        SUM(b.runs) / COUNT(DISTINCT b.match_id) AS avg_runs
    FROM batting_innings b
    JOIN matches m ON m.match_id = b.match_id
    GROUP BY b.player_id, YEAR(m.match_date), QUARTER(m.match_date)
    HAVING COUNT(DISTINCT b.match_id) >= 3
),
eligible AS (
    SELECT player_id FROM quarterly GROUP BY player_id HAVING COUNT(*) >= 6
),
ordered AS (
    SELECT
        q.*,
        ROW_NUMBER() OVER (PARTITION BY q.player_id ORDER BY q.yr, q.qtr)           AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY q.player_id ORDER BY q.yr DESC, q.qtr DESC) AS rn_last
    FROM quarterly q
    JOIN eligible e ON e.player_id = q.player_id
)
SELECT
    p.player_name,
    ROUND(AVG(CASE WHEN o.rn_first <= 3 THEN o.avg_runs END), 2) AS early_avg_runs,
    ROUND(AVG(CASE WHEN o.rn_last  <= 3 THEN o.avg_runs END), 2) AS recent_avg_runs,
    CASE
        WHEN AVG(CASE WHEN o.rn_last <= 3 THEN o.avg_runs END)
           > AVG(CASE WHEN o.rn_first <= 3 THEN o.avg_runs END) * 1.10
            THEN 'Career Ascending'
        WHEN AVG(CASE WHEN o.rn_last <= 3 THEN o.avg_runs END)
           < AVG(CASE WHEN o.rn_first <= 3 THEN o.avg_runs END) * 0.90
            THEN 'Career Declining'
        ELSE 'Career Stable'
    END AS career_phase
FROM ordered o
JOIN players p ON p.player_id = o.player_id
GROUP BY p.player_id, p.player_name
ORDER BY p.player_name;
