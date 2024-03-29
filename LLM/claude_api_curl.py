import requests
from LLM.config import ANTHROPIC_API_KEY

API_URL = "https://api.anthropic.com/v1/messages"

headers = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

data = {
    "model": "claude-3-opus-20240229",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "what is the distance from earth to sun? Your response should be only a single integer which is the distance in miles"}
    ]
}

response = requests.post(API_URL, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    print("text: ", result["content"][0]['text'])
else:
    print(f"Error: {response.status_code} - {response.text}")

