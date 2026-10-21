"""Download a small set of players from the Cricbuzz API and save them to MySQL.

Each player costs up to 4 API calls (search, profile, batting, bowling).
Responses are cached in data/players/, so re-running never repeats a call
that already succeeded.

Usage:  python load_players.py
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from utils.player_loader import save_player

load_dotenv(Path(__file__).parent / ".env")

HOST = os.getenv("RAPIDAPI_HOST")
HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": HOST,
}
BASE_URL = f"https://{HOST}"
CACHE_DIR = Path("data") / "players"
PAUSE_SECONDS = 1.5  # be gentle with the free-plan rate limit

# (search name, country). Virat Kohli (1413) is already loaded.
PLAYERS = [
    ("Rohit Sharma", "India"),
    ("Jasprit Bumrah", "India"),
    ("Ravindra Jadeja", "India"),
    ("MS Dhoni", "India"),
    ("Ben Stokes", "England"),
    ("Pat Cummins", "Australia"),
    ("Steve Smith", "Australia"),
    ("Kane Williamson", "New Zealand"),
    ("Steven Peter Devereux Smith", "Australia"),
]


class QuotaError(Exception):
    """Raised when the API says we have run out of requests."""


def api_get(path, params=None):
    """GET one API path and return the parsed JSON."""
    response = requests.get(
        BASE_URL + path, headers=HEADERS, params=params, timeout=10
    )
    time.sleep(PAUSE_SECONDS)
    if response.status_code == 429:
        raise QuotaError("Rate or monthly limit reached (HTTP 429)")
    response.raise_for_status()
    return response.json()


def cached(file_name, path, params=None):
    """Return cached JSON if we already have it, otherwise call the API."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = CACHE_DIR / file_name

    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    data = api_get(path, params)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def find_player_id(name, country):
    """Search by name and return the id whose name and team match exactly."""
    safe = name.lower().replace(" ", "_")
    results = cached(f"search_{safe}.json", "/stats/v1/player/search", {"plrN": name})

    for candidate in results.get("player", []):
        same_name = candidate.get("name", "").lower() == name.lower()
        same_team = candidate.get("teamName", "").lower() == country.lower()
        if same_name and same_team:
            return int(candidate["id"])
    return None


def main():
    saved, skipped = 0, []

    for name, country in PLAYERS:
        try:
            player_id = find_player_id(name, country)
            if player_id is None:
                print(f"SKIP {name}: no exact name + team match in search results")
                skipped.append(name)
                continue

            profile = cached(f"{player_id}_profile.json", f"/stats/v1/player/{player_id}")
            batting = cached(f"{player_id}_batting.json", f"/stats/v1/player/{player_id}/batting")
            bowling = cached(f"{player_id}_bowling.json", f"/stats/v1/player/{player_id}/bowling")

            save_player(profile, batting, bowling)
            saved += 1

        except QuotaError as error:
            print("STOP:", error)
            break
        except Exception as error:  # keep going if one player fails
            print(f"FAILED {name}: {error}")
            skipped.append(name)

    print(f"\nDone. Saved {saved} players. Skipped or failed: {skipped or 'none'}")


if __name__ == "__main__":
    main()