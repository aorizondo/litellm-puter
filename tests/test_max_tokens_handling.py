"""
Test max_tokens handling to avoid OpenRouter errors.

Background:
----------
Puter automatically calculates max_tokens based on:
1. Model's max_tokens limit (from OpenRouter API)  
2. User's available credits
3. Approximate token count of the prompt

See: puter/src/backend/src/services/ai/chat/AIChatService.ts:359-361

Problem:
--------
If we send max_tokens that exceeds the model's limit, OpenRouter returns:
"Error 400: Invalid max_tokens value, the valid range is [1, X]"

Solution:
---------
Only send max_tokens if explicitly specified by user with reasonable value.
Let Puter calculate it automatically otherwise.
"""

from puter_provider import filter_model_params


def test_max_tokens_not_specified():
    """When max_tokens is not specified, don't send it to Puter."""
    print("\n🧪 Test 1: max_tokens not specified")
    
    params = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'temperature': 0.7,
    }
    
    filtered = filter_model_params(params)
    
    if 'max_tokens' in filtered:
        print("   ❌ max_tokens should NOT be in filtered params")
        return False
    
    print("   ✅ max_tokens correctly omitted (Puter will calculate it)")
    return True


def test_max_tokens_explicitly_set_reasonable():
    """When user explicitly sets reasonable max_tokens, include it."""
    print("\n🧪 Test 2: max_tokens explicitly set (reasonable value)")
    
    params = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 100,  # User explicitly wants 100 tokens
    }
    
    filtered = filter_model_params(params)
    
    if 'max_tokens' not in filtered:
        print("   ❌ max_tokens should be in filtered params")
        return False
    
    if filtered['max_tokens'] != 100:
        print(f"   ❌ max_tokens should be 100, got {filtered['max_tokens']}")
        return False
    
    print("   ✅ max_tokens=100 correctly included")
    return True


def test_max_tokens_extremely_high():
    """When max_tokens is extremely high (default from LiteLLM), remove it."""
    print("\n🧪 Test 3: max_tokens extremely high (likely default)")
    
    params = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 999999,  # Likely a default value
    }
    
    filtered = filter_model_params(params)
    
    if 'max_tokens' in filtered:
        print(f"   ❌ max_tokens={params['max_tokens']} should be removed (too high)")
        return False
    
    print("   ✅ Extremely high max_tokens correctly removed")
    return True


def test_max_tokens_8192():
    """When user sets max_tokens to 8192, it's filtered (risky for OpenRouter)."""
    print("\n🧪 Test 4: max_tokens = 8192 (>8000, will be filtered)")
    
    params = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 8192,
    }
    
    filtered = filter_model_params(params)
    
    if 'max_tokens' in filtered:
        print("   ❌ max_tokens=8192 should be filtered (risky for OpenRouter)")
        return False
    
    print("   ✅ max_tokens=8192 correctly filtered (Puter will calculate safe value)")
    return True


def test_max_tokens_16384():
    """When user sets max_tokens to 16384, it's filtered (risky for OpenRouter)."""
    print("\n🧪 Test 5: max_tokens = 16384 (>8000, will be filtered)")
    
    params = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 16384,
    }
    
    filtered = filter_model_params(params)
    
    if 'max_tokens' in filtered:
        print("   ❌ max_tokens=16384 should be filtered (risky for OpenRouter)")
        return False
    
    print("   ✅ max_tokens=16384 correctly filtered (Puter will calculate safe value)")
    return True


def test_max_tokens_safe_value():
    """When user sets max_tokens to safe value (<=8000), include it."""
    print("\n🧪 Test 6: max_tokens = 1000 (safe value, will be included)")
    
    params = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 1000,
    }
    
    filtered = filter_model_params(params)
    
    if 'max_tokens' not in filtered:
        print("   ❌ max_tokens=1000 should be included (safe value)")
        return False
    
    if filtered['max_tokens'] != 1000:
        print(f"   ❌ max_tokens should be 1000, got {filtered['max_tokens']}")
        return False
    
    print("   ✅ max_tokens=1000 correctly included (safe for all models)")
    return True


def test_max_tokens_none():
    """When max_tokens is None, don't send it."""
    print("\n🧪 Test 7: max_tokens = None")
    
    params = {
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': None,
    }
    
    filtered = filter_model_params(params)
    
    if 'max_tokens' in filtered:
        print("   ❌ max_tokens=None should not be in filtered params")
        return False
    
    print("   ✅ max_tokens=None correctly omitted")
    return True


def test_documentation():
    """Document the max_tokens behavior."""
    print("\n📝 max_tokens Behavior Documentation")
    print("=" * 70)
    print("""
HOW PUTER HANDLES max_tokens:
-----------------------------

1. Puter calculates max_tokens automatically in AIChatService.ts:
   
   parameters.max_tokens = Math.floor(
       Math.min(
           parameters.max_tokens ?? Number.POSITIVE_INFINITY,
           maxAllowedOutputTokens,  // Based on user credits
           maxTokens - approximateTokenCount  // Model limit - prompt
       )
   );

2. This means Puter will:
   - Use the model's max_tokens limit (from OpenRouter API)
   - Consider user's available credits
   - Subtract approximate prompt token count
   - Use the MINIMUM of these values

3. Our strategy:
   - Don't send max_tokens unless user explicitly specifies it
   - If user specifies a safe value (<=8000), send it
   - If user specifies >8000, filter it (risky for OpenRouter models)
   - Puter will calculate the safe value automatically
   - If value is extremely high (>100,000), omit it (likely default)

4. Why this works:
   ✅ User can explicitly control max_tokens if needed
   ✅ Puter's automatic calculation handles credits/limits
   ✅ Avoids "Invalid max_tokens value" errors from OpenRouter
   ✅ Works with all providers (OpenRouter, OpenAI, Claude, etc.)

EXAMPLES:
---------

Example 1: No max_tokens specified
>>> response = litellm.completion(
...     model="puter/openrouter:deepseek/deepseek-chat",
...     messages=[{"role": "user", "content": "Hello"}]
... )
✅ Puter calculates optimal max_tokens automatically

Example 2: Explicit max_tokens (safe value)
>>> response = litellm.completion(
...     model="puter/openrouter:deepseek/deepseek-chat",
...     messages=[{"role": "user", "content": "Hello"}],
...     max_tokens=1000  # User wants ~1000 tokens
... )
✅ Puter will use 1000 (or less if credits/model limits require)

Example 3: High max_tokens (will be filtered)
>>> response = litellm.completion(
...     model="puter/openrouter:deepseek/deepseek-chat",
...     messages=[{"role": "user", "content": "Hello"}],
...     max_tokens=16384  # Too high, risky for OpenRouter
... )
✅ Our filter removes this, Puter calculates safe value

Example 4: Extremely high max_tokens (will be filtered)
>>> response = litellm.completion(
...     model="puter/openrouter:deepseek/deepseek-chat",
...     messages=[{"role": "user", "content": "Hello"}],
...     max_tokens=999999  # Likely a default value
... )
✅ Our filter removes this, Puter calculates optimal value
""")
    print("=" * 70)
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("  MAX_TOKENS HANDLING TESTS")
    print("=" * 70)
    
    tests = [
        test_max_tokens_not_specified,
        test_max_tokens_explicitly_set_reasonable,
        test_max_tokens_extremely_high,
        test_max_tokens_8192,
        test_max_tokens_16384,
        test_max_tokens_safe_value,
        test_max_tokens_none,
        test_documentation,
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
        print("\n🎯 Key Points:")
        print("   • Don't send max_tokens unless user specifies it")
        print("   • Let Puter calculate optimal value automatically")
        print("   • Filter out extremely high values (>100,000)")
        print("   • This avoids OpenRouter 'Invalid max_tokens' errors")
    else:
        print(f"\n❌ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
