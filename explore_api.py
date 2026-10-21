"""Call any Cricbuzz API path, print the start of the response, and save it.

Usage examples (copy the real paths from the RapidAPI Endpoints tab):
    python explore_api.py /stats/v1/player/search plrN=kohli
    python explore_api.py /stats/v1/player/1413
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

HOST = os.getenv("RAPIDAPI_HOST")
HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": HOST,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python explore_api.py <path> [name=value ...]")
        return

    path = sys.argv[1]
    params = dict(arg.split("=", 1) for arg in sys.argv[2:])

    response = requests.get(
        f"https://{HOST}{path}", headers=HEADERS, params=params, timeout=10
    )
    print("Status code:", response.status_code)
    response.raise_for_status()

    data = response.json()
    Path("data").mkdir(exist_ok=True)
    name = path.strip("/").replace("/", "_") or "root"
    out_path = Path("data") / f"explore_{name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Saved", out_path)
    if isinstance(data, dict):
        print("Top-level keys:", list(data.keys()))
    print(json.dumps(data, indent=2)[:1500])


if __name__ == "__main__":
    main()