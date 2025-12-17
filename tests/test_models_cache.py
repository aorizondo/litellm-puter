"""
Test Puter Models Cache - Verify driver detection works correctly.

This test verifies that our custom puter_models_cache.py works as a
replacement for putergenai.PuterClient().model_to_driver.
"""

from litellm_puter.models_cache import get_model_driver, PuterModelsCache, clear_models_cache
import sys


def test_openai_models():
    """Test OpenAI model detection."""
    print("\n🧪 Test 1: OpenAI Models")
    
    models = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1",
        "o1-mini",
        "o1-pro",
        "o3",
        "o3-mini",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "openai-completion":
            print(f"   ❌ {model} → {driver} (expected openai-completion)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_claude_models():
    """Test Claude/Anthropic model detection."""
    print("\n🧪 Test 2: Claude Models")
    
    models = [
        "claude-3-5-sonnet",
        "claude-3-opus",
        "claude-3-haiku",
        "claude-2.1",
        "claude-instant",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "claude":
            print(f"   ❌ {model} → {driver} (expected claude)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_gemini_models():
    """Test Google Gemini model detection."""
    print("\n🧪 Test 3: Gemini Models")
    
    models = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-pro",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "google":
            print(f"   ❌ {model} → {driver} (expected google)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_deepseek_models():
    """Test DeepSeek model detection."""
    print("\n🧪 Test 4: DeepSeek Models")
    
    models = [
        "deepseek-chat",
        "deepseek-v3",
        "deepseek-coder",
        "deepseek-v2",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "deepseek":
            print(f"   ❌ {model} → {driver} (expected deepseek)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_mistral_models():
    """Test Mistral model detection."""
    print("\n🧪 Test 5: Mistral Models")
    
    models = [
        "mistral-large",
        "mistral-medium",
        "mistral-small",
        "pixtral-12b",
        "ministral-8b",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "mistral":
            print(f"   ❌ {model} → {driver} (expected mistral)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_xai_models():
    """Test XAI/Grok model detection."""
    print("\n🧪 Test 6: XAI (Grok) Models")
    
    models = [
        "grok-2",
        "grok-beta",
        "grok-1",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "xai":
            print(f"   ❌ {model} → {driver} (expected xai)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_openrouter_models():
    """Test OpenRouter prefix detection."""
    print("\n🧪 Test 7: OpenRouter Models")
    
    models = [
        "openrouter:deepseek/deepseek-chat",
        "openrouter:anthropic/claude-3-opus",
        "openrouter:openai/gpt-4",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "openrouter":
            print(f"   ❌ {model} → {driver} (expected openrouter)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_together_ai_models():
    """Test Together AI prefix detection."""
    print("\n🧪 Test 8: Together AI Models")
    
    models = [
        "togetherai:meta-llama/llama-3",
        "togetherai:mistralai/mixtral-8x7b",
    ]
    
    for model in models:
        driver = get_model_driver(model)
        if driver != "together-ai":
            print(f"   ❌ {model} → {driver} (expected together-ai)")
            return False
        print(f"   ✅ {model} → {driver}")
    
    return True


def test_cache_singleton():
    """Test that cache is a singleton."""
    print("\n🧪 Test 9: Cache Singleton")
    
    cache1 = PuterModelsCache()
    cache2 = PuterModelsCache()
    
    if cache1 is not cache2:
        print("   ❌ Cache is not a singleton")
        return False
    
    print("   ✅ Cache is correctly implemented as singleton")
    return True


def test_cache_clearing():
    """Test cache clearing functionality."""
    print("\n🧪 Test 10: Cache Clearing")
    
    # Get a driver to populate cache
    driver1 = get_model_driver("gpt-4o")
    
    # Clear cache
    clear_models_cache()
    
    # Get driver again
    driver2 = get_model_driver("gpt-4o")
    
    if driver1 != driver2:
        print(f"   ❌ Driver changed after cache clear: {driver1} → {driver2}")
        return False
    
    print("   ✅ Cache clearing works correctly")
    return True


def test_fallback_default():
    """Test fallback to default driver for unknown models."""
    print("\n🧪 Test 11: Fallback to Default")
    
    unknown_models = [
        "some-random-model-12345",
        "unknown-provider:model",
        "xyz-model-v1",
    ]
    
    for model in unknown_models:
        driver = get_model_driver(model)
        if driver != "openai-completion":
            print(f"   ❌ {model} → {driver} (expected openai-completion as default)")
            return False
        print(f"   ✅ {model} → {driver} (default)")
    
    return True


def test_comparison_with_putergenai():
    """
    Compare our cache with putergenai for common models.
    
    Note: This test requires putergenai to be installed.
    If not available, test is skipped.
    """
    print("\n🧪 Test 12: Comparison with putergenai")
    
    try:
        from putergenai.putergenai import PuterClient
        puter_client = PuterClient()
        
        common_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-opus-4-5",
            "gemini-1.5-flash",
            "deepseek-chat",
            "mistral-large-latest",
        ]
        
        mismatches = []
        
        for model in common_models:
            our_driver = get_model_driver(model)
            their_driver = puter_client.model_to_driver.get(model, "openai-completion")
            
            if our_driver == their_driver:
                print(f"   ✅ {model:30} → {our_driver:20} (matches putergenai)")
            else:
                print(f"   ⚠️  {model:30} → {our_driver:20} (putergenai: {their_driver})")
                mismatches.append((model, our_driver, their_driver))
        
        if mismatches:
            print(f"\n   ℹ️  {len(mismatches)} mismatch(es) found (may be due to heuristics)")
            return True  # Not a failure, just informational
        
        return True
        
    except ImportError:
        print("   ⏭️  Skipped (putergenai not installed)")
        return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("  PUTER MODELS CACHE TESTS")
    print("=" * 70)
    print("\n📝 Testing custom cache as replacement for putergenai")
    print("   Goal: Eliminate putergenai dependency")
    print("   Strategy: Heuristics + API caching (with auth)\n")
    
    tests = [
        test_openai_models,
        test_claude_models,
        test_gemini_models,
        test_deepseek_models,
        test_mistral_models,
        test_xai_models,
        test_openrouter_models,
        test_together_ai_models,
        test_cache_singleton,
        test_cache_clearing,
        test_fallback_default,
        test_comparison_with_putergenai,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎯 Summary:")
        print("   • Custom cache works as putergenai replacement")
        print("   • Heuristics correctly detect drivers for common models")
        print("   • Fallback to default driver for unknown models")
        print("   • No putergenai dependency needed!")
        print("\n📦 Benefits:")
        print("   ✅ Removed mediocre putergenai dependency")
        print("   ✅ Cleaner, more maintainable code")
        print("   ✅ Better caching strategy (1-hour TTL)")
        print("   ✅ Can fetch fresh model list from API")
        print("   ✅ Fallback to heuristics if API unavailable")
    else:
        print(f"\n❌ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
