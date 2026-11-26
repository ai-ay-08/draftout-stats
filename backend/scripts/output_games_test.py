import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

username = input("Enter username: ").strip()

function_url = "https://draftoutmc.com/_serverFn/1bfa5793a2c7d16813601250d9f624b5aac7fc555ced2c73b76ddd190ea473d6"

# Request payload as ordinary JSON data; place the entered username in playerId.
# Currently outputs match history. Would also like to output goal history per game.
# Also only supports era 1 and match type competitive for the MVP.
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

url = f"{function_url}?{urlencode({'payload': json.dumps(payload, separators=(',', ':'))})}"

# Decode TSS into a python dict using recursion.
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


request = Request(
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

with urlopen(request, timeout=20) as response:
    response_data = json.loads(response.read().decode("utf-8"))

decoded = decode_tss(response_data)
result = decoded.get("result") or {}
games = result.get("series") or []

if not games:
    raise SystemExit("No games found.")

# Output Match ID: then result, opponent, and rating change
for game in games:
    score = game.get("score")
    opponent_score = game.get("opponentScore")
    if score is not None and opponent_score is not None:
        game_result = "W" if score > opponent_score else "L" if score < opponent_score else "D"
        score_text = f"{score}-{opponent_score}"
    else:
        game_result = game.get("outcome", "?")
        score_text = "score unknown"

    print(
        f"Match {game.get('matchId', '?')}: {game_result} {score_text} "
        f"vs {game.get('opponentName', 'unknown')} "
        f"(rating change: {game.get('ratingChange', '?')})"
    )
