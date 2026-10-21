import json
from utils.player_loader import save_player

def load(name):
    with open(f"data/{name}.json", encoding="utf-8") as f:
        return json.load(f)

save_player(
    load("explore_stats_v1_player_1413"),
    load("explore_stats_v1_player_1413_batting"),
    load("explore_stats_v1_player_1413_bowling"),
)