import json

from utils.scorecard_loader import save_scorecard

MATCH_ID = 168090  # must exist in the matches table

with open(f"data/scorecard_{MATCH_ID}.json", encoding="utf-8") as file:
    data = json.load(file)

print("Scorecard batting teams:")
for inn in data.get("scorecard", []):
    print(" ", repr(inn.get("batteamname")))

save_scorecard(MATCH_ID, data)