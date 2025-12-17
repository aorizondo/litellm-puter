"""
Async Usage Example - Puter LLM Provider
========================================

This example demonstrates asynchronous usage of Puter with LiteLLM.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
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


async def make_completion(prompt: str, model: str):
    """Make an async completion request."""
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response


async def main():
    """Run multiple async requests concurrently."""
    print("🚀 Making concurrent requests to Puter API...\n")
    
    # Define multiple requests
    requests = [
        ("What is 2+2?", "puter/anthropic/claude-sonnet-4-5-20250929"),
        ("Name a color.", "puter/anthropic/claude-sonnet-4-5-20250929"),
        ("What's the capital of France?", "puter/anthropic/claude-sonnet-4-5-20250929"),
    ]
    
    # Execute all requests concurrently
    tasks = [make_completion(prompt, model) for prompt, model in requests]
    responses = await asyncio.gather(*tasks)
    
    # Print results
    print("✅ All responses received:\n")
    for i, (prompt, _) in enumerate(requests):
        print(f"Question {i+1}: {prompt}")
        print(f"Answer: {responses[i].choices[0].message.content}")
        print(f"Tokens: {responses[i].usage}\n")


if __name__ == "__main__":
    asyncio.run(main())
