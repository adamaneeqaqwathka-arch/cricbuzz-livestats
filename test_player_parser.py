import json
from utils.player_parser import parse_career_stats

with open("data/explore_stats_v1_player_1413_batting.json", encoding="utf-8") as f:
    batting = json.load(f)
with open("data/explore_stats_v1_player_1413_bowling.json", encoding="utf-8") as f:
    bowling = json.load(f)

for row in parse_career_stats(1413, batting, bowling):
    print(row)