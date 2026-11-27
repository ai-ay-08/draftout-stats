"""Fetch and print one Draftout match's decoded detail response.

This probes the match detail server function used to discover the fields that
contain the per-goal game history.
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


FUNCTION_URL = (
    "https://draftoutmc.com/_serverFn/"
    "8ee4bc64962305ab33f0c0ac06a0fa18e5970aa40a84f81ccf2c979202c9e62b"
)
PLAYER_ID = "bing_pigs"
MATCH_ID = 504897


def decode_tss(value, references=None):
    """Decode the TSS tagged values returned by Draftout's server function."""
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
        properties = value.get("p", {})
        result = {}
        object_id = value.get("i")
        if object_id is not None:
            references[object_id] = result
        for key, item in zip(properties.get("k", []), properties.get("v", [])):
            result[key] = decode_tss(item, references)
        return result

    return value


def main():
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
                            {"t": 1, "s": PLAYER_ID},
                            {"t": 0, "s": MATCH_ID},
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

    url = f"{FUNCTION_URL}?{urlencode({'payload': json.dumps(payload, separators=(',', ':'))})}"
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
    print(json.dumps(decoded, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
