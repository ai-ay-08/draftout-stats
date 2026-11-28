# TO GRADERS: AI GENERATED TEST FILE.

"""List the distinct goal IDs found in a player's competitive match history.

Usage:
    python backend/scripts/goal_ids_test.py <username>

This inspects the matches returned by Draftout's era 1 competitive history
endpoint, then fetches each match board and prints the unique goal IDs as JSON.
"""

import argparse
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MATCHES_URL = (
    "https://draftoutmc.com/_serverFn/"
    "1bfa5793a2c7d16813601250d9f624b5aac7fc555ced2c73b76ddd190ea473d6"
)
MATCH_DETAILS_URL = (
    "https://draftoutmc.com/_serverFn/"
    "8ee4bc64962305ab33f0c0ac06a0fa18e5970aa40a84f81ccf2c979202c9e62b"
)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def decode_tss(value, references=None):
    """Decode the tagged structured serialization used by Draftout."""
    if references is None:
        references = {}
    if not isinstance(value, dict):
        return value

    tag = value.get("t")
    if tag in (0, 1, 2):
        return value.get("s")
    if tag == 4:
        return references.get(value.get("i"), value)
    if tag == 9:
        return [decode_tss(item, references) for item in value.get("a", [])]
    if tag in (10, 11):
        object_id = value.get("i")
        result = {}
        if object_id is not None:
            references[object_id] = result
        properties = value.get("p", {})
        for key, item in zip(properties.get("k", []), properties.get("v", [])):
            result[key] = decode_tss(item, references)
        return result
    return value


def fetch_decoded(url, payload):
    """Fetch a Draftout server function response and decode its TSS body."""
    request_url = f"{url}?{urlencode({'payload': json.dumps(payload, separators=(',', ':'))})}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "x-tsr-serverFn": "true",
        },
    )
    with urlopen(request, timeout=20) as response:
        response_data = json.loads(response.read().decode("utf-8"))
    return decode_tss(response_data)


def get_matches(username):
    payload = {
        "t": {
            "t": 10,
            "i": 0,
            "p": {
                "k": ["data"],
                "v": [{
                    "t": 10,
                    "i": 1,
                    "p": {
                        "k": ["playerId", "matchType", "eraId"],
                        "v": [
                            {"t": 1, "s": username},
                            {"t": 1, "s": "competitive"},
                            {"t": 2, "s": 1},
                        ],
                    },
                    "o": 0,
                }],
            },
            "o": 0,
        },
        "f": 63,
        "m": [],
    }
    decoded = fetch_decoded(MATCHES_URL, payload)
    return ((decoded.get("result") or {}).get("series") or [])


def get_match_board(username, match_id):
    payload = {
        "t": {
            "t": 10,
            "i": 0,
            "p": {
                "k": ["data"],
                "v": [{
                    "t": 11,
                    "i": 1,
                    "p": {
                        "k": ["playerId", "matchId"],
                        "v": [
                            {"t": 1, "s": username},
                            {"t": 0, "s": match_id},
                        ],
                    },
                    "o": 0,
                }],
            },
            "o": 0,
        },
        "f": 63,
        "m": [],
    }
    decoded = fetch_decoded(MATCH_DETAILS_URL, payload)
    match = (decoded.get("result") or {}).get("match") or {}
    return match.get("finalBoard") or []


def collect_goal_ids(username):
    """Return distinct IDs and the number of matches where each appeared."""
    matches = get_matches(username)
    if not matches:
        raise RuntimeError(f"No competitive matches found for {username!r}.")

    goal_matches = {}
    for match in matches:
        match_id = match.get("matchId")
        if match_id is None:
            continue
        board = get_match_board(username, match_id)
        ids_in_match = {
            goal.get("id")
            for goal in board
            if isinstance(goal, dict) and goal.get("id") is not None
        }
        for goal_id in ids_in_match:
            goal_matches.setdefault(str(goal_id), set()).add(str(match_id))

    return {
        "username": username,
        "matches_checked": len(matches),
        "unique_goal_count": len(goal_matches),
        "goals": [
            {
                "goal_id": goal_id,
                "matches_found": len(match_ids),
                "match_ids": sorted(match_ids),
            }
            for goal_id, match_ids in sorted(goal_matches.items())
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", help="Draftout username to inspect")
    args = parser.parse_args()

    try:
        results = collect_goal_ids(args.username.strip())
    except Exception as error:
        raise SystemExit(f"Could not collect goal IDs: {error}") from error
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
