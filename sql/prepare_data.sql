-- ============================================================
-- Data preparation: run ONCE after loading matches/teams/venues.
-- Fills columns that the live API does not give us directly.
-- Run:  mysql -u root -p cricbuzz_db < sql/prepare_data.sql
-- ============================================================

-- 1. Winner of each completed match, taken from the status text
--    (e.g. "Bengal won by 60 runs")
UPDATE matches m
JOIN teams t
  ON m.match_status LIKE CONCAT(t.team_name, ' won%')
SET m.winner_team_id = t.team_id
WHERE m.winner_team_id IS NULL;

-- 2. Victory type and margin, taken from the same status text
--    ("won by 60 runs", "won by 9 wkts", "won by an innings and 66 runs")
UPDATE matches
SET victory_type = CASE
        WHEN match_status LIKE '%wkt%' THEN 'wickets'
        WHEN match_status LIKE '%run%' THEN 'runs'
    END,
    victory_margin = CAST(
        REGEXP_SUBSTR(
            REGEXP_SUBSTR(match_status, '[0-9]+ (runs?|wkts?)'),
            '[0-9]+'
        ) AS UNSIGNED
    )
WHERE winner_team_id IS NOT NULL
  AND victory_margin IS NULL;

-- 3. Mark national teams and their country (needed for Q12, home vs away)
UPDATE teams
SET country = team_name,
    is_international = TRUE
WHERE team_name IN (
    'India', 'Australia', 'England', 'South Africa', 'New Zealand',
    'Pakistan', 'Sri Lanka', 'Bangladesh', 'West Indies', 'Afghanistan',
    'Ireland', 'United States', 'Zimbabwe'
);

-- 4. Country for a live-data venue (more can be added the same way)
UPDATE venues
SET country = 'South Africa'
WHERE venue_name = 'St George''s Park' AND country IS NULL;
