import json
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

# Original captured request URL. parse_qs decodes the percent-encoded payload.
captured_url = (
    "https://draftoutmc.com/_serverFn/1bfa5793a2c7d16813601250d9f624b5aac7fc555ced2c73b76ddd190ea473d6"
    "?payload=%7B%22t%22%3A%7B%22t%22%3A10%2C%22i%22%3A0%2C%22p%22%3A%7B%22k%22%3A%5B%22data%22%5D%2C%22v%22%3A%5B%7B%22t%22%3A10%2C%22i%22%3A1%2C%22p%22%3A%7B%22k%22%3A%5B%22playerId%22%2C%22matchType%22%2C%22eraId%22%5D%2C%22v%22%3A%5B%7B%22t%22%3A1%2C%22s%22%3A%22Snakezy%22%7D%2C%7B%22t%22%3A1%2C%22s%22%3A%22competitive%22%7D%2C%7B%22t%22%3A2%2C%22s%22%3A1%7D%5D%7D%2C%22o%22%3A0%7D%5D%7D%2C%22o%22%3A0%7D%2C%22f%22%3A63%2C%22m%22%3A%5B%5D%7D"
)

parsed_url = urlparse(captured_url)
payload_text = parse_qs(parsed_url.query)["payload"][0]
payload = json.loads(payload_text)


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
    captured_url,
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
    print(json.dumps(decoded, indent=2))
    raise SystemExit("No games found.")

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
