"""Download one match scorecard from the Cricbuzz API and save it to data/.

Usage:  python fetch_scorecard.py 168090
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}

# Check this against the URL in your test_topstats.py (only the match ID
# part changes). If your URL path differs, edit this line.
URL_TEMPLATE = "https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"


def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_scorecard.py <match_id>")
        return

    match_id = sys.argv[1]
    response = requests.get(
        URL_TEMPLATE.format(match_id=match_id), headers=HEADERS, timeout=10
    )
    print("Status code:", response.status_code)
    response.raise_for_status()

    data = response.json()
    Path("data").mkdir(exist_ok=True)
    out_path = Path("data") / f"scorecard_{match_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Saved", out_path)
    print("Teams:", [i.get("batteamname") for i in data.get("scorecard", [])])


if __name__ == "__main__":
    main()