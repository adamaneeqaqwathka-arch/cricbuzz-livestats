-- Sample data for venues (approximate public capacities, rounded).
-- Real Cricbuzz venue IDs are lower than 900000, so these cannot collide.
-- Document in the README that this venue data is sample data.

INSERT INTO venues (venue_id, venue_name, city, country, capacity) VALUES
    (900001, 'Narendra Modi Stadium', 'Ahmedabad', 'India', 132000),
    (900002, 'Melbourne Cricket Ground', 'Melbourne', 'Australia', 100000),
    (900003, 'Eden Gardens', 'Kolkata', 'India', 66000),
    (900004, 'Optus Stadium', 'Perth', 'Australia', 60000),
    (900005, 'Sydney Cricket Ground', 'Sydney', 'Australia', 48000),
    (900006, 'Gaddafi Stadium', 'Lahore', 'Pakistan', 34000),
    (900007, 'Wankhede Stadium', 'Mumbai', 'India', 33000),
    (900008, 'Lords', 'London', 'England', 31000),
    (900009, 'Newlands', 'Cape Town', 'South Africa', 25000),
    (900010, 'Galle International Stadium', 'Galle', 'Sri Lanka', 35000)
ON DUPLICATE KEY UPDATE
    venue_name = VALUES(venue_name),
    city = VALUES(city),
    country = VALUES(country),
    capacity = VALUES(capacity);

-- Fill in details for a venue that came from the live matches endpoint
UPDATE venues
SET country = 'Australia', capacity = 53500
WHERE venue_id = 40 AND venue_name = 'Adelaide Oval';