import json
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

# Original captured request URL. parse_qs decodes the percent-encoded payload.
captured_url = (
    "https://draftoutmc.com/_serverFn/42e288c1135f9c3702288b6b0e9f218434409d98553a57a05c021a9726f8d6ae"
    "?payload=%7B%22t%22%3A%7B%22t%22%3A10%2C%22i%22%3A0%2C%22p%22%3A%7B%22k%22%3A%5B%22data%22%5D%2C%22v%22%3A%5B%7B%22t%22%3A10%2C%22i%22%3A1%2C%22p%22%3A%7B%22k%22%3A%5B%22metric%22%2C%22eraId%22%2C%22inactive%22%5D%2C%22v%22%3A%5B%7B%22t%22%3A1%2C%22s%22%3A%22rating%22%7D%2C%7B%22t%22%3A2%2C%22s%22%3A1%7D%2C%7B%22t%22%3A2%2C%22s%22%3A1%7D%5D%7D%2C%22o%22%3A0%7D%5D%7D%2C%22o%22%3A0%7D%2C%22f%22%3A63%2C%22m%22%3A%5B%5D%7D"
)

parsed_url = urlparse(captured_url)
payload_text = parse_qs(parsed_url.query)["payload"][0]
payload = json.loads(payload_text)

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
    data = json.loads(response.read().decode("utf-8"))
    print(json.dumps(data, indent=2))
