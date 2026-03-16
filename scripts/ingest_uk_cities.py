import time
import requests

BASE_URL = "http://127.0.0.1:8000"

cities = [
    "London",
    "Manchester",
    "Birmingham",
    "Liverpool",
    "Leeds",
    "Sheffield",
    "Bristol",
    "Newcastle",
    "Nottingham",
    "Leicester",
    "Coventry",
    "Bradford",
    "Stoke-on-Trent",
    "Wolverhampton",
    "Derby",
    "Swansea",
    "Cardiff",
    "Belfast",
    "Glasgow",
    "Edinburgh",
    "Dundee",
    "Aberdeen",
    "York",
    "Bath",
    "Oxford",
    "Cambridge",
    "Reading",
    "Luton",
    "Milton Keynes",
    "Brighton",
    "Portsmouth",
    "Southampton",
    "Plymouth",
    "Exeter",
    "Norwich",
    "Peterborough",
    "Hull",
    "Lincoln",
    "Durham",
    "Sunderland",
]

# get token
token_response = requests.post(
    f"{BASE_URL}/auth/dev-token",
    params={"role": "admin"}
)
print("TOKEN RESPONSE:", token_response.status_code, token_response.text)

token = token_response.json()["token"]

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {token}",
}

for city in cities:
    r = requests.post(
        f"{BASE_URL}/ingest/openweather",
        headers=headers,
        params={"city": city},
    )
    print(f"{city}: {r.status_code}")
    print(r.text)
    time.sleep(1)