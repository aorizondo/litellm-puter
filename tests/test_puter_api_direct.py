import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PUTER_API_KEY")
print(f"✅ Using API key (length: {len(api_key)})")

url = "https://api.puter.com/drivers/call"

payload = {
    "interface": "puter-chat-completion",
    "driver": "openrouter",
    "method": "complete",
    "args": {
        "model": "openrouter:deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": "Say hello in Spanish"}
        ]
    },
    "stream": False,
    "test_mode": False
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Origin": "https://puter.com",
    "Referer": "https://puter.com/"
}

print(f"\n🚀 Making direct API call to Puter...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = httpx.post(url, json=payload, headers=headers, timeout=30)
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\n📄 Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
        
    if response.status_code == 403:
        print("\n⚠️  403 Forbidden - Possible reasons:")
        print("  1. API key is invalid or expired")
        print("  2. API key doesn't have permission for this operation")
        print("  3. IP address is blocked")
        print("  4. Missing required headers")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
