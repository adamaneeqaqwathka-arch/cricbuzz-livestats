import json

with open("data/scorecard_sample.json") as f:
    data = json.load(f)

inn = data["scorecard"][0]

print("Complete?", data["ismatchcomplete"], "|", data["status"])
print("Batting team:", inn["batteamname"], inn["batteamsname"])
print("Score:", inn["score"], inn["wickets"], inn["overs"])

print("\n--- one bowler ---")
print(inn["bowler"][0])

print("\n--- partnership ---")
print(json.dumps(inn["partnership"], indent=2)[:800])

print("\n--- outdec of every batter ---")
for b in inn["batsman"]:
    print(repr(b["outdec"]))