# TO GRADERS: AI GENERATED TEST FILE.

import json
import os
import random
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen 

import psycopg


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
    """Decode Draftout's tagged structured serialization."""
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
    """Fetch and decode one Draftout server-function response."""
    request_url = f"{url}?{urlencode({
        'payload': json.dumps(payload, separators=(',', ':'))
    })}"
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
    return (decoded.get("result") or {}).get("series") or []


def get_match(username, match_id):
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
    return (decoded.get("result") or {}).get("match") or {}


def get_goal_categories():
    """Return a mapping from goal ID to category using Supabase Postgres."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Set the DATABASE_URL environment variable first.")

    with psycopg.connect(database_url, connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT goal_id, category FROM public.goals")
            return {str(goal_id): category for goal_id, category in cursor.fetchall()}


def count_by_category(goal_occurrences, categories_by_goal):
    """Count mapped goal occurrences, grouped by category."""
    counts = Counter()

    for goal_id, occurrences in goal_occurrences.items():
        category = categories_by_goal.get(goal_id)
        if category is not None:
            counts[category] += occurrences

    return counts


def main():
    username = "Snakezy"
    categories_by_goal = get_goal_categories()

    # These counters count every goal entry across all fetched match boards.
    goals_seen = Counter()
    goals_completed = Counter()

    all_matches = get_matches(username)
    matches = random.sample(all_matches, min(30, len(all_matches)))

    for index, match_summary in enumerate(matches, start=1):
        match_id = match_summary.get("matchId")
        if match_id is None:
            continue

        match = get_match(username, match_id)
        participants = match.get("participants") or []

        # Find Snakezy's participant UUID to identify goals they completed.
        player_uuids = {
            str(player.get("uuid"))
            for player in participants
            if str(player.get("username", "")).casefold() == username.casefold()
        }

        for goal in match.get("finalBoard") or []:
            if not isinstance(goal, dict) or goal.get("id") is None:
                continue

            goal_id = str(goal["id"])
            goals_seen[goal_id] += 1

            if (
                goal.get("completedAtMs") is not None
                and str(goal.get("completedByUuid")) in player_uuids
            ):
                goals_completed[goal_id] += 1

        print(f"Fetched sampled match {index}/{len(matches)}", flush=True)

    seen_counts = count_by_category(goals_seen, categories_by_goal)
    completed_counts = count_by_category(goals_completed, categories_by_goal)

    print(f"\nPlayer: {username}")
    print(f"Matches sampled: {len(matches)} of {len(all_matches)}")
    print(f"Goal appearances counted: {sum(goals_seen.values())}")
    print(f"Goals completed counted: {sum(goals_completed.values())}")

    print("\nGoal appearances by category:")
    for category, count in sorted(seen_counts.items()):
        print(f"{category}: {count}")

    print("\nGoals completed by Snakezy by category:")
    for category, count in sorted(completed_counts.items()):
        print(f"{category}: {count}")

if __name__ == "__main__":
    main()
