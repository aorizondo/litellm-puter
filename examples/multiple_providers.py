"""
Multiple Providers Example - Puter LLM Provider
===============================================

This example demonstrates using different LLM providers through Puter.
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

# Define models from different providers
models = [
    {
        "name": "DeepSeek (via OpenRouter)",
        "model": "puter/openrouter:deepseek/deepseek-chat",
        "prompt": "Say 'Hello' in Japanese"
    },
    {
        "name": "Claude Sonnet",
        "model": "puter/claude-sonnet-4-5-20250929",
        "prompt": "Say 'Hello' in French"
    },
    {
        "name": "GPT-4 (via OpenAI)",
        "model": "puter/openai:gpt-4",
        "prompt": "Say 'Hello' in Spanish"
    },
]

print("🌍 Testing multiple providers through Puter...\n")

for config in models:
    print(f"📡 Provider: {config['name']}")
    print(f"   Model: {config['model']}")
    
    try:
        response = litellm.completion(
            model=config['model'],
            messages=[{"role": "user", "content": config['prompt']}],
        )
        
        print(f"   ✅ Response: {response.choices[0].message.content}")
        print(f"   📊 Tokens: {response.usage.total_tokens}\n")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
