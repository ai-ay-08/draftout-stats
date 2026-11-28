# TODO: Add error handling for both endpoints 

import json
import os
import random
from collections import Counter

import psycopg

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


"""CONFIGURATION VARS"""

GET_MATCHES_URL = (
    "https://draftoutmc.com/_serverFn/"
    "1bfa5793a2c7d16813601250d9f624b5aac7fc555ced2c73b76ddd190ea473d6"
)

GET_MATCH_DETAILS_URL = (
    "https://draftoutmc.com/_serverFn/"
    "8ee4bc64962305ab33f0c0ac06a0fa18e5970aa40a84f81ccf2c979202c9e62b"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Request payload as ordinary JSON data; place the entered username in playerId
# Also request payload using matchId for match details / goal history.
# Also only supports era 1 and match type competitive for the MVP.


"""HELPERS"""

# decode_tss decodes TSS (Typed Structured Serialization) into a Python dict using recursion.

def decode_tss(value, references=None):
    if references is None:
        references = {}

    tag = value.get("t")

    if tag in (0, 1, 2):
        return value.get("s")
    if tag == 4:
        return references.get(value.get("i"), value)
    if tag == 9:
        return [decode_tss(item, references) for item in value.get("a", [])]
    if tag == 10:
        object_id = value.get("i")
        result = {}
        if object_id is not None:
            references[object_id] = result

        properties = value.get("p", {})
        for key, item in zip(properties.get("k", []), properties.get("v", [])):
            result[key] = decode_tss(item, references)
        return result
    if tag == 11:
        return {}

    return value


# get_goal_categories loads goal categories from Supabase.

def get_goal_categories():
    database_url = os.environ["DATABASE_URL"]

    with psycopg.connect(database_url, connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT goal_id, category FROM public.goals")
            return {
                str(goal_id): category
                for goal_id, category in cursor.fetchall()
            }


# fetch_matches fetches the matches for a given username.

def fetch_matches(username):
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

    request_url = f"{GET_MATCHES_URL}?{urlencode({
        'payload': json.dumps(payload, separators=(',', ':'))
    })}"

    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "x-tsr-serverFn": "true",
        }
    )

    with urlopen(request, timeout=20) as response:
        response_data = json.loads(response.read().decode("utf-8"))

    decoded = decode_tss(response_data)
    result = decoded.get("result") or {}
    games = result.get("series") or []

    matches = []
    for game in games:
        score = game.get("score")
        opponent_score = game.get("opponentScore")

        if score is not None and opponent_score is not None:
            outcome = (
                "W" if score > opponent_score
                else "L" if score < opponent_score
                else "D"
            )
            score_text = f"{score}-{opponent_score}"
        else:
            outcome = game.get("outcome", "?")
            score_text = "score unknown"

        matches.append({
            "matchId": game.get("matchId", "?"),
            "outcome": outcome,
            "score": score_text,
            "opponent": game.get("opponentName", "unknown"),
            "ratingChange": game.get("ratingChange", "?"),
        })

    return matches


# fetch_match fetches match details / goal history for a given username and match_id.

def fetch_match(username, match_id):
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

    request_url = f"{GET_MATCH_DETAILS_URL}?{urlencode({
        'payload': json.dumps(payload, separators=(',', ':'))
    })}"

    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "x-tsr-serverFn": "true",
        }
    )

    with urlopen(request, timeout=20) as response:
        response_data = json.loads(response.read().decode("utf-8"))

    decoded = decode_tss(response_data)
    match = (decoded.get("result") or {}).get("match") or {}

    return match 


"""API ENDPOINTS"""

# Handle the POST request to this API endpoint
# Send a request and decode the response into the matches list, and return it as JSON.

@app.post("/api/matches")
def get_matches():
    data = request.json or {}
    username = data.get("username", "").strip()

    return jsonify({"matches": fetch_matches(username)})


# Handle the POST request to this API endpoint
# The POST request contains username and matchId, and this function sends a request which
# returns the match details for the specific username and matchId.  

@app.post("/api/match-details")
def get_match_details():
    data = request.json or {}
    username = data.get("username", "").strip()
    match_id = data.get("matchId")

    match = fetch_match(username, match_id)

    # Get the player names from the JSON
    player_names = {
        player.get("uuid"): player.get("username", player.get("uuid"))
        for player in match.get("participants", [])
    }

    # Sort the completed goals
    events = [
        goal for goal in match.get("finalBoard", [])
        if goal.get("completedAtMs") is not None
        and goal.get("completedByUuid")
    ]
    events.sort(key=lambda goal: goal["completedAtMs"])

    # Keep a running list of the score (this will be displayed in the frontend)
    running_scores = {}
    goal_history = []

    for goal in events:
        player_uuid = goal["completedByUuid"]
        running_scores[player_uuid] = running_scores.get(player_uuid, 0) + 1

        time_ms = goal["completedAtMs"]
        total_seconds = time_ms // 1000
        minutes, seconds = divmod(total_seconds, 60)

        goal_history.append({
            "player": player_names.get(player_uuid, player_uuid),
            "goal": goal.get("id", "Unknown goal"),
            "time": f"{minutes}:{seconds:02d}",
            "score": " - ".join(
                str(running_scores.get(player.get("uuid"), 0))
                for player in match.get("participants", [])
            ),
        })

    return jsonify({"goalHistory": goal_history})


# Handle the POST request to this API endpoint
# The POST request contains username, and this function samples 30 matches from the 
# match history and counts the number of goals completed by category, and returns it as JSON.

@app.post("/api/category-sample")
def category_sample():
    data = request.json or {}
    username = data.get("username", "").strip()

    # Fetch a sample of 30 matches
    categories_by_goal = get_goal_categories()
    all_matches = fetch_matches(username)
    sample = random.sample(all_matches, min(30, len(all_matches)))

    goals_seen = Counter()
    goals_completed = Counter()

    # For each goal history in the sample, add goals to both ALL goals seen and 
    # COMPLETED goals by the player
    for match_summary in sample:
        match_id = match_summary.get("matchId")

        match = fetch_match(username, match_id)
        participants = match.get("participants") or []

        player_uuids = {
            str(player.get("uuid"))
            for player in participants
            if str(player.get("username", "")) == username
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

    # Convert the Counter instance to a dict that tracks the number of times a goal category appears.
    def counts_by_category(goal_occurrences):
        counts = Counter()

        for goal_id, occurrences in goal_occurrences.items():
            category = categories_by_goal.get(goal_id)
            if category is not None:
                counts[category] += occurrences

        return dict(sorted(counts.items()))

    return jsonify({
        "username": username,
        "matches_sampled": len(sample),
        "goals_seen": counts_by_category(goals_seen),
        "goals_completed": counts_by_category(goals_completed),
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)