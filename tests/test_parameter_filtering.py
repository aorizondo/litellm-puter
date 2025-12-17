#!/usr/bin/env python3
"""
Test script to verify parameter filtering works correctly.
"""

from puter_provider import filter_model_params, VALID_MODEL_PARAMS, LITELLM_INTERNAL_PARAMS


def test_filter_model_params():
    """Test that filtering removes LiteLLM internal parameters."""
    
    # Simulate a typical LiteLLM request with mixed parameters
    test_params = {
        # Valid model parameters
        'model': 'puter/openrouter:deepseek/deepseek-chat',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 100,
        'temperature': 0.7,
        'top_p': 0.9,
        'stream': False,
        
        # LiteLLM internal parameters (should be filtered out)
        'custom_llm_provider': 'puter',
        'litellm_params': {'some': 'data'},
        'api_key': 'test_key',
        'api_base': 'https://api.puter.com',
        'client': 'SomeClient',
        'extra_headers': {'X-Custom': 'value'},
        'timeout': 30,
    }
    
    # Filter parameters
    filtered = filter_model_params(test_params)
    
    print("=" * 80)
    print("PARAMETER FILTERING TEST")
    print("=" * 80)
    print()
    
    print("📥 INPUT PARAMETERS:")
    for key, value in test_params.items():
        print(f"  • {key}: {value}")
    print()
    
    print("📤 FILTERED PARAMETERS (what gets sent to Puter):")
    for key, value in filtered.items():
        print(f"  • {key}: {value}")
    print()
    
    print("❌ REMOVED PARAMETERS:")
    removed = set(test_params.keys()) - set(filtered.keys())
    for key in removed:
        print(f"  • {key}")
    print()
    
    # Verify filtering worked correctly
    assert 'model' in filtered, "model should be included"
    assert 'messages' in filtered, "messages should be included"
    assert 'max_tokens' in filtered, "max_tokens should be included"
    assert 'temperature' in filtered, "temperature should be included"
    assert 'top_p' in filtered, "top_p should be included"
    
    assert 'custom_llm_provider' not in filtered, "custom_llm_provider should be removed"
    assert 'litellm_params' not in filtered, "litellm_params should be removed"
    assert 'api_key' not in filtered, "api_key should be removed"
    assert 'api_base' not in filtered, "api_base should be removed"
    assert 'client' not in filtered, "client should be removed"
    assert 'extra_headers' not in filtered, "extra_headers should be removed"
    assert 'timeout' not in filtered, "timeout should be removed"
    
    print("✅ ALL TESTS PASSED!")
    print()
    print("=" * 80)
    print()
    print("📋 VALID MODEL PARAMETERS (allowed):")
    for param in sorted(VALID_MODEL_PARAMS):
        print(f"  • {param}")
    print()
    
    print("🚫 LITELLM INTERNAL PARAMETERS (filtered out):")
    for param in sorted(LITELLM_INTERNAL_PARAMS):
        print(f"  • {param}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    test_filter_model_params()
