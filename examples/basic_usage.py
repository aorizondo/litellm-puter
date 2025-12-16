"""
Basic Usage Example - Puter LLM Provider
=========================================

This example demonstrates the simplest way to use Puter with LiteLLM.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import litellm
from puter_provider import setup_puter_provider

# Load environment variables
load_dotenv()

# Verify API key is set
if not os.getenv("PUTER_API_KEY"):
    print("❌ Error: PUTER_API_KEY not found in environment")
    print("Please set it in your .env file or export it:")
    print("  export PUTER_API_KEY='your-api-key-here'")
    exit(1)

# Register Puter as a custom provider
setup_puter_provider()

print("🚀 Making request to Puter API...\n")

# Make a simple completion request
response = litellm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[
        {
            "role": "user",
            "content": "Explain what Puter is in one sentence."
        }
    ],
)

# Print the response
print("✅ Response received:")
print(response.choices[0].message.content)
print(f"\n📊 Token usage: {response.usage}")
