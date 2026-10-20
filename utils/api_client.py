import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# .env lives in the project root, one folder above utils/
load_dotenv(Path(__file__).parent.parent / ".env")

URL = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}

def epoch_ms_to_datetime(ms):
    """Convert epoch milliseconds (string or int) to a datetime, or None."""
    try:
        return datetime.fromtimestamp(int(ms) / 1000)
    except (TypeError, ValueError):
        return None

def parse_live_matches(data):
    """Flatten nested live-matches JSON into a list of match dictionaries."""
    matches_list = []

    for type_block in data.get("typeMatches", []):
        for series in type_block.get("seriesMatches", []):
            # Skip entries that are ads rather than series
            if "seriesAdWrapper" not in series:
                continue

            wrapper = series["seriesAdWrapper"]
            series_name = wrapper.get("seriesName")
            series_id = wrapper.get("seriesId")

            for match in wrapper.get("matches", []):
                info = match.get("matchInfo", {})
                team1 = info.get("team1") or {}
                team2 = info.get("team2") or {}
                venue = info.get("venueInfo") or {}

                row = {
                    "match_id": info.get("matchId"),
                    "series_id": series_id,
                    "series_name": series_name,
                    "match_desc": info.get("matchDesc"),
                    "format": info.get("matchFormat"),
                    "team1_id": team1.get("teamId"),
                    "team1": team1.get("teamName"),
                    "team1_short": team1.get("teamSName"),
                    "team2_id": team2.get("teamId"),
                    "team2": team2.get("teamName"),
                    "team2_short": team2.get("teamSName"),
                    "venue_id": venue.get("id"),
                    "venue": venue.get("ground"),
                    "city": venue.get("city"),
                    "country": venue.get("country"),
                    "status": info.get("status"),
                    "state": info.get("state"),
                    "start_date": epoch_ms_to_datetime(
                        info.get("startDate")
                    ),
                }

                matches_list.append(row)

    return matches_list

def fetch_live_matches():
    """Fetch live matches from Cricbuzz and return a list of match dicts.

    Returns an empty list if the API call fails.
    """
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return parse_live_matches(response.json())
    except (requests.exceptions.RequestException, ValueError) as error:
        print(f"API error: {error}")
        return []