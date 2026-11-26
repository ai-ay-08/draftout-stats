import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FUNCTION_URL = (
    "https://draftoutmc.com/_serverFn/"
    "1bfa5793a2c7d16813601250d9f624b5aac7fc555ced2c73b76ddd190ea473d6"
)

# Request payload as ordinary JSON data; place the entered username in playerId.
# Currently outputs match history. Would also like to output goal history per game.
# Also only supports era 1 and match type competitive for the MVP.

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


@app.post("/api/matches")
def get_matches():
    username = (request.json or {}).get("username", "").strip()
    if not username:
        return jsonify({"error": "Enter a username."}), 400

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

    url = f"{FUNCTION_URL}?{urlencode({
        'payload': json.dumps(payload, separators=(',', ':'))
    })}"

    upstream_request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "x-tsr-serverFn": "true",
        },
    )

    try:
        with urlopen(upstream_request, timeout=20) as response:
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

        return jsonify({"matches": matches})

    except Exception as error:
        app.logger.exception("Could not fetch match history")
        return jsonify({"error": f"Could not fetch match history: {error}"}), 502


if __name__ == "__main__":
    app.run(port=5000, debug=True)