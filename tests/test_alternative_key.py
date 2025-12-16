import httpx
import json

# Probar con la API key alternativa del ejemplo
api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicyIsInYiOiIwLjAuMCIsInUiOiJMSUVzc25uUlFMNnN4ZDJRMlNyNVh3PT0iLCJ1dSI6InlDTTJicHdpVHRldDhVWllNUEtEUlE9PSIsImlhdCI6MTc2NDkxMTI1NX0.spJRzTXi0VNB5eoyO9XP9_x3dchRvVYQsLJYuxKWy4w"

print(f"✅ Testing alternative API key from example2.py")
print(f"Key length: {len(api_key)}")

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

print(f"\n🚀 Making API call to Puter...")

try:
    response = httpx.post(url, json=payload, headers=headers, timeout=30)
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS!")
        result = response.json()
        print(f"\n📄 Response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
