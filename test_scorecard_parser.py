import json

from utils.scorecard_parser import parse_scorecard

with open("data/scorecard_sample.json", encoding="utf-8") as file:
    data = json.load(file)

# Team names that batted in this scorecard, in order
team_names = list(dict.fromkeys(
    inn.get("batteamname")
    for inn in data.get("scorecard", [])
    if inn.get("batteamname")
))
print("Teams in scorecard:", team_names)

# Example IDs only. We will use the real team IDs when saving to MySQL.
team_ids = {name: index + 1 for index, name in enumerate(team_names)}

batting, bowling, partnerships, team_innings = parse_scorecard(
    data,
    match_id=1,  # placeholder, replace with the real Cricbuzz match ID later
    team_ids=team_ids,
)

print("\n--- Parser Results ---")
print("Batting rows:", len(batting))
print("Bowling rows:", len(bowling))
print("Partnership rows:", len(partnerships))
print("Team innings rows:", len(team_innings))

if batting:
    print("\nFirst batting row:", batting[0])
if bowling:
    print("\nFirst bowling row:", bowling[0])
if partnerships:
    print("\nFirst partnership row:", partnerships[0])
if team_innings:
    print("\nFirst team innings row:", team_innings[0])