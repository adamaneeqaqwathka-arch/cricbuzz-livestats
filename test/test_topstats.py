import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# 1. Setup
load_dotenv(Path(__file__).parent / ".env")

HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}

# Paste the scorecard URL you used before (the one that returned "scorecard")
URL = "https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/40381/scard"
PARAMS = {}

# 2. Request
response = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=10)
print(response.status_code)
response.raise_for_status()

# 3. Save the response so we don't spend more quota while developing
data = response.json()
Path("data").mkdir(exist_ok=True)
with open("data/scorecard_sample.json", "w") as f:
    json.dump(data, f, indent=2)

print("Top-level keys:", list(data.keys()))
first = data["scorecard"][0]
print("Innings keys:", list(first.keys()))
print("Batsmen in innings 1:", len(first["batsman"]))