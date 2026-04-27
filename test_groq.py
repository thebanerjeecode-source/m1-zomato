import os
import requests

api_key = None
with open(".env") as f:
    for line in f:
        if line.startswith("GROQ_API_KEY="):
            api_key = line.strip().split("=")[1]

if not api_key:
    print("API key not found")
    exit(1)

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hi"}
    ],
    "temperature": 0.2
}
resp = requests.post(url, headers=headers, json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")
