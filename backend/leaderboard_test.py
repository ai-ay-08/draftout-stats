import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

function_id = "42e288c1135f9c3702288b6b0e9f218434409d98553a57a05c021a9726f8d6ae"

# Captured TSS payload: rating leaderboard, era 1, inactive flag set to 1.
# Modify this shit in the future because we will need a different payload shape
# for username input, match history, replay history.
payload = {
    "t": {
        "t": 10, "i": 0,
        "p": {
            "k": ["data"],
            "v": [{
                "t": 10, "i": 1,
                "p": {
                    "k": ["metric", "eraId", "inactive"],
                    "v": [
                        {"t": 1, "s": "rating"},
                        {"t": 2, "s": 1},
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

query = urlencode({"payload": json.dumps(payload, separators=(",", ":"))})
url = f"https://draftoutmc.com/_serverFn/{function_id}?{query}"
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
    print(f"HTTP {response.status}")
    print(response.read().decode("utf-8", errors="replace"))