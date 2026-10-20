#import os
#from datetime import datetime
#from pathlib import Path
#import pandas as pd
#
#import requests
#from dotenv import load_dotenv
#
## 1. Load the API key from the .env file next to this script
#load_dotenv(Path(__file__).parent / ".env")
#
#URL = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
#HEADERS = {
#    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
#    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
#}
#
#
#def epoch_ms_to_datetime(ms):
#    """Convert epoch milliseconds (string or int) to a datetime, or None."""
#    try:
#        return datetime.fromtimestamp(int(ms) / 1000)
#    except (TypeError, ValueError):
#        return None
#
#
#def parse_live_matches(data):
#    """Flatten the nested live-matches JSON into a list of match dicts."""
#    matches_list = []
#
#    for type_block in data.get("typeMatches", []):
#        for series in type_block.get("seriesMatches", []):
#            # Some entries are ads, so skip them
#            if "seriesAdWrapper" not in series:
#                continue
#
#            wrapper = series["seriesAdWrapper"]
#            series_name = wrapper.get("seriesName")
#
#            for match in wrapper.get("matches", []):
#                info = match.get("matchInfo", {})
#                team1 = info.get("team1", {})
#                team2 = info.get("team2", {})
#                venue = info.get("venueInfo", {})
#
#                row = {
#                    "match_id": info.get("matchId"),
#                    "series_name": series_name,
#                    "match_desc": info.get("matchDesc"),
#                    "format": info.get("matchFormat"),
#                    "team1": team1.get("teamName"),
#                    "team2": team2.get("teamName"),
#                    "venue": venue.get("ground"),
#                    "city": venue.get("city"),
#                    "status": info.get("status"),
#                    "start_date": epoch_ms_to_datetime(info.get("startDate")),
#                }
#                matches_list.append(row)
#
#    return matches_list
#
#
#def main():
#    response = requests.get(URL, headers=HEADERS, timeout=10)
#    print("Status code:", response.status_code)
#    response.raise_for_status()
#
#    matches = parse_live_matches(response.json())
#    print("Matches found:", len(matches))
#    if matches:
#           df = pd.DataFrame(matches)
#           print(df.shape)
#           print(df.head())
#           print(df["format"].value_counts())
#
#if __name__ == "__main__":
#    main()

from utils.api_client import fetch_live_matches

matches = fetch_live_matches()
print(len(matches))