import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

HEADERS = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}

# Copy the exact URL and any query parameters from the RapidAPI snippet
URL = "https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/40381/scard"
PARAMS = {}  # e.g. the stats type, if the endpoint needs one

response = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=10)
print(response.status_code)
print(response.text[:1500])