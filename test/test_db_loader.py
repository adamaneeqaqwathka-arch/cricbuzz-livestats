from utils.api_client import fetch_live_matches
from utils.db_loader import save_live_matches


if __name__ == "__main__":
    matches = fetch_live_matches()
    print(f"Fetched {len(matches)} matches")

    save_live_matches(matches)