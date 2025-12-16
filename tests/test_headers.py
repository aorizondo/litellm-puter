import os
import httpx
from unittest.mock import patch
from puter_provider import PuterHTTPHandler
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PUTER_API_KEY")
print(f"✅ Using API key (length: {len(api_key)})")

# Interceptar la llamada para ver los headers
original_post = httpx.Client.post

def intercepted_post(self, *args, **kwargs):
    print("\n🔍 Intercepted HTTP POST call:")
    print(f"URL: {args[0] if args else kwargs.get('url', 'N/A')}")
    print(f"\n📋 Headers being sent:")
    headers = kwargs.get('headers', {})
    for key, value in headers.items():
        if key.lower() == 'authorization':
            print(f"  {key}: Bearer {value[7:20]}... (truncated)")
        else:
            print(f"  {key}: {value}")
    
    # Verificar que Origin esté presente
    if 'Origin' not in headers and 'origin' not in headers:
        print("\n⚠️  WARNING: 'Origin' header is MISSING!")
    else:
        print("\n✅ 'Origin' header is present")
    
    return original_post(self, *args, **kwargs)

# Patch httpx.Client.post
with patch.object(httpx.Client, 'post', intercepted_post):
    print("\n🚀 Making test call with PuterHTTPHandler...")
    
    try:
        import litellm
        os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"
        
        response = litellm.completion(
            client=PuterHTTPHandler(api_key=api_key),
            model="openrouter/openrouter:deepseek/deepseek-chat",
            api_key="None",
            messages=[{"role": "user", "content": "Test"}],
        )
        
        print("\n✅ Request completed!")
        print(f"Response status: Success")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
