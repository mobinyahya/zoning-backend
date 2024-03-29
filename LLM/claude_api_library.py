import anthropic
from LLM.config import ANTHROPIC_API_KEY


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

Prompt = "how far is the sun. Return an single integer number"

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": Prompt}
    ]
)
print(message.content[0].text)


# def v1():
#     # Set up the API endpoint and headers
#     api_endpoint = "https://api.anthropic.com/v1/complete"
#     api_key = ANTHROPIC_API_KEY
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {api_key}"
#     }
#
#     payload = {
#         "prompt": "How far is the sun?",
#         "max_tokens_to_sample": 500,  # Adjust the desired response length
#         "model": "claude-v1.3"
#     }
#
#     # Send the API request
#     response = requests.post(api_endpoint, json=payload, headers=headers)
#
#     # Check the response status
#     if response.status_code == 200:
#         # Parse the API response
#         api_response = response.json()
#         assistant_reply = api_response["completion"]
#         print("Claude's response:")
#         print(assistant_reply)
#     else:
#         print("Error occurred during API call:", response.status_code)