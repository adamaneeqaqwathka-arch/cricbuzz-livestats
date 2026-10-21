
-- =====================================================
-- Cricbuzz Cricket Analytics Database
-- File: cricbuzz_schema.sql
-- =====================================================

CREATE DATABASE IF NOT EXISTS cricbuzz_analytics;
USE cricbuzz_analytics;

-- =====================================================
-- 1. TEAMS
-- =====================================================

CREATE TABLE IF NOT EXISTS teams (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_short_name VARCHAR(20),
    country VARCHAR(100),
    is_international BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB;

-- =====================================================
-- 2. VENUES
-- =====================================================

CREATE TABLE IF NOT EXISTS venues (
    venue_id INT PRIMARY KEY,
    venue_name VARCHAR(200) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    capacity INT NULL,
    timezone VARCHAR(10)
) ENGINE=InnoDB;

-- =====================================================
-- 3. SERIES
-- =====================================================

CREATE TABLE IF NOT EXISTS series (
    series_id INT PRIMARY KEY,
    series_name VARCHAR(200) NOT NULL,
    host_country VARCHAR(100),
    start_date DATE,
    end_date DATE,
    total_matches INT
) ENGINE=InnoDB;

-- =====================================================
-- 4. PLAYERS
-- =====================================================

CREATE TABLE IF NOT EXISTS players (
    player_id INT PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    role VARCHAR(50),
    batting_style VARCHAR(50),
    bowling_style VARCHAR(50),
    date_of_birth DATE NULL
) ENGINE=InnoDB;

-- =====================================================
-- 5. MATCHES
-- =====================================================

CREATE TABLE IF NOT EXISTS matches (
    match_id INT PRIMARY KEY,
    series_id INT,
    team1_id INT,
    team2_id INT,
    venue_id INT,
    match_desc VARCHAR(100),
    match_format VARCHAR(20),
    match_date DATETIME,
    match_status VARCHAR(200),
    state VARCHAR(30),
    toss_winner_team_id INT NULL,
    toss_decision VARCHAR(10) NULL,
    winner_team_id INT NULL,
    victory_margin INT NULL,
    victory_type VARCHAR(10) NULL,

    FOREIGN KEY (series_id)
        REFERENCES series(series_id),

    FOREIGN KEY (team1_id)
        REFERENCES teams(team_id),

    FOREIGN KEY (team2_id)
        REFERENCES teams(team_id),

    FOREIGN KEY (venue_id)
        REFERENCES venues(venue_id),

    FOREIGN KEY (toss_winner_team_id)
        REFERENCES teams(team_id),

    FOREIGN KEY (winner_team_id)
        REFERENCES teams(team_id)
) ENGINE=InnoDB;

-- =====================================================
-- 6. TEAM INNINGS
-- =====================================================

CREATE TABLE IF NOT EXISTS team_innings (
    team_innings_id INT PRIMARY KEY AUTO_INCREMENT,
    match_id INT,
    innings_no INT NOT NULL,
    team_id INT,
    runs INT,
    wickets INT,
    balls INT,
    extras INT,
    batting_first BOOLEAN,

    UNIQUE (match_id, innings_no),

    FOREIGN KEY (match_id)
        REFERENCES matches(match_id),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
) ENGINE=InnoDB;

-- =====================================================
-- 7. BATTING INNINGS
-- =====================================================

CREATE TABLE IF NOT EXISTS batting_innings (
    batting_id INT PRIMARY KEY AUTO_INCREMENT,
    match_id INT,
    innings_no INT NOT NULL,
    player_id INT,
    team_id INT,
    batting_position INT,
    runs INT,
    balls INT,
    fours INT,
    sixes INT,
    is_out BOOLEAN,
    dismissal_type VARCHAR(50) NULL,

    UNIQUE (match_id, innings_no, player_id),

    FOREIGN KEY (match_id)
        REFERENCES matches(match_id),

    FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
) ENGINE=InnoDB;

-- =====================================================
-- 8. BOWLING INNINGS
-- =====================================================

CREATE TABLE IF NOT EXISTS bowling_innings (
    bowling_id INT PRIMARY KEY AUTO_INCREMENT,
    match_id INT,
    innings_no INT NOT NULL,
    player_id INT,
    team_id INT,
    balls_bowled INT,
    maidens INT,
    runs_conceded INT,
    wickets INT,

    UNIQUE (match_id, innings_no, player_id),

    FOREIGN KEY (match_id)
        REFERENCES matches(match_id),

    FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
) ENGINE=InnoDB;

-- =====================================================
-- 9. PARTNERSHIPS
-- =====================================================

CREATE TABLE IF NOT EXISTS partnerships (
    partnership_id INT PRIMARY KEY AUTO_INCREMENT,
    match_id INT,
    innings_no INT NOT NULL,
    team_id INT,
    player1_id INT,
    player2_id INT,
    player1_position INT,
    player2_position INT,
    wicket_number INT,
    runs INT,
    balls INT,

    FOREIGN KEY (match_id)
        REFERENCES matches(match_id),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id),

    FOREIGN KEY (player1_id)
        REFERENCES players(player_id),

    FOREIGN KEY (player2_id)
        REFERENCES players(player_id)
) ENGINE=InnoDB;

-- =====================================================
-- 10. PLAYER CAREER STATS
-- =====================================================

CREATE TABLE IF NOT EXISTS player_career_stats (
    player_id INT,
    format VARCHAR(10),
    matches INT,
    innings INT,
    runs INT,
    batting_avg DECIMAL(6,2),
    strike_rate DECIMAL(6,2),
    highest_score INT,
    centuries INT,
    fifties INT,
    wickets INT,
    bowling_avg DECIMAL(6,2),
    economy DECIMAL(4,2),
    catches INT,
    stumpings INT,

    PRIMARY KEY (player_id, format),

    FOREIGN KEY (player_id)
        REFERENCES players(player_id)
) ENGINE=InnoDB;

-- =====================================================
-- VERIFY TABLES
-- =====================================================

SHOW TABLES;
