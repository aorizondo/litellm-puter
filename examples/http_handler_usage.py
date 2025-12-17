"""
HTTP Handler Usage Example - Puter LLM Provider
===============================================

This example demonstrates direct usage of PuterHTTPHandler,
useful for fine-grained control over requests.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import litellm
from puter_provider import PuterHTTPHandler

# Load environment variables
load_dotenv()

# Verify API key is set
api_key = os.getenv("PUTER_API_KEY")
if not api_key:
    print("❌ Error: PUTER_API_KEY not found in environment")
    print("Please set it in your .env file or export it:")
    print("  export PUTER_API_KEY='your-api-key-here'")
    exit(1)

# Enable experimental HTTP handler support
os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"

print("🚀 Making request using PuterHTTPHandler directly...\n")

# Create completion with custom HTTP handler
response = litellm.completion(
    client=PuterHTTPHandler(api_key=api_key),
    model="openrouter/openrouter/openrouter:deepseek/deepseek-chat",
    api_key="none",  # Not used, authentication is handled by PuterHTTPHandler
    messages=[
        {
            "role": "user",
            "content": "What are the main benefits of using Puter for AI development?"
        }
    ],
)

# Print the response
print("✅ Response received:")
print(response.choices[0].message.content)
print(f"\n📊 Token usage: {response.usage}")
print(f"💰 Model used: {response.model}")
