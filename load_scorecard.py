"""Download (or reuse) a match scorecard and save it to MySQL.

Usage:  python load_scorecard.py 163721 163691 163761
Each match must already exist in the matches table.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from utils.scorecard_loader import save_scorecard

load_dotenv(Path(__file__).parent / ".env")

HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}
URL_TEMPLATE = "https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"


def get_scorecard(match_id):
    """Return the scorecard JSON, using the saved file when it exists."""
    file_path = Path("data") / f"scorecard_{match_id}.json"

    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    response = requests.get(
        URL_TEMPLATE.format(match_id=match_id), headers=HEADERS, timeout=10
    )
    response.raise_for_status()
    data = response.json()

    Path("data").mkdir(exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    time.sleep(1.5)
    return data


def main():
    match_ids = sys.argv[1:]
    if not match_ids:
        print("Usage: python load_scorecard.py <match_id> [<match_id> ...]")
        return

    for match_id in match_ids:
        try:
            data = get_scorecard(match_id)
            save_scorecard(int(match_id), data)
        except Exception as error:  # keep going if one match fails
            print(f"FAILED match {match_id}: {error}")


if __name__ == "__main__":
    main()