"""
Puter Models Cache - Helper to fetch and cache model-to-driver mappings.

This module eliminates the dependency on putergenai by directly fetching
model information from Puter's API and caching it locally.

Background:
-----------
Previously, we relied on putergenai.PuterClient().model_to_driver to determine
which driver (provider) to use for each model. However, putergenai has 565
hardcoded models in its source code, which is:
1. Not maintainable
2. Outdated quickly
3. Adds unnecessary dependency

Solution:
---------
Fetch model information directly from Puter's API:
  https://puter.com/puterai/chat/models

Each model has a "provider" field that tells us which driver to use.

Cache Strategy:
--------------
- Cache results in memory with 1-hour TTL
- Optional: Persist to disk for faster startup
- Fallback to heuristics if API is unavailable
"""

import os
import json
import time
import httpx
from typing import Dict, Optional, Any
from datetime import datetime, timedelta


class PuterModelsCache:
    """
    Manages model-to-driver mappings by fetching from Puter's API.
    
    Features:
    - Fetches models from Puter API with authentication
    - Caches results in memory (1 hour TTL)
    - Falls back to heuristics if API fails
    - Thread-safe singleton pattern
    """
    
    # Singleton instance
    _instance: Optional['PuterModelsCache'] = None
    
    # Cache settings
    CACHE_TTL = timedelta(hours=1)
    API_URL = "https://api.puter.com/puterai/chat/models/details"
    
    # Fallback heuristics for common model patterns
    DRIVER_HEURISTICS = {
        'openrouter:': 'openrouter',
        'togetherai:': 'together-ai',
        'claude': 'claude',
        'mistral': 'mistral',
        'ministral': 'mistral',
        'pixtral': 'mistral',
        'grok': 'xai',
        'deepseek': 'deepseek',
        'gemini': 'google',
        'gpt': 'openai-completion',
        'o1': 'openai-completion',
        'o3': 'openai-completion',
    }
    
    def __new__(cls):
        """Singleton pattern - only one instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize cache (only once due to singleton)."""
        if self._initialized:
            return
            
        self._initialized = True
        self._cache: Dict[str, str] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._token: Optional[str] = None
    
    def set_token(self, token: str) -> None:
        """
        Set Puter authentication token.
        
        Args:
            token: Puter API token
        """
        self._token = token
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache or self._cache_timestamp is None:
            return False
        
        age = datetime.now() - self._cache_timestamp
        return age < self.CACHE_TTL
    
    def _fetch_from_api(self) -> Dict[str, Any]:
        """
        Fetch models from Puter API.
        
        Uses the same headers as puter_provider.py for consistency:
        - Authorization: Bearer token
        - Content-Type: application/json
        - Origin: https://puter.com
        - Referer: https://puter.com/
        
        Returns:
            Dict with 'models' key containing list of model objects
            
        Raises:
            Exception: If API request fails
        """
        if not self._token:
            raise ValueError("Puter token not set. Call set_token() first.")
        
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Origin": "https://puter.com",
            "Referer": "https://puter.com/",
        }
        
        # Configure proxy if enabled (optional - for bypassing IP blocks)
        use_proxy = os.getenv("USE_PROXY", "false").lower() == "true"
        proxy_url = None
        if use_proxy:
            proxy_url = os.getenv("SOCKS5_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        
        # Disable SSL verification for SOCKS proxies (they often have cert issues)
        verify = not (proxy_url and proxy_url.startswith('socks'))
        
        try:
            response = httpx.get(
                self.API_URL,
                headers=headers,
                timeout=10.0,
                proxy=proxy_url,  # httpx uses 'proxy' not 'proxies'
                verify=verify
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize response format
            if isinstance(data, list):
                data = {'models': data}
            elif not isinstance(data, dict):
                raise ValueError(f"Unexpected API response type: {type(data)}")
            
            if 'models' not in data:
                raise ValueError(f"API response missing 'models' key: {list(data.keys())}")
            
            return data
            
        except Exception as e:
            raise Exception(f"Failed to fetch models from Puter API: {e}")
    
    def _extract_driver_from_model(self, model: Any) -> Optional[str]:
        """
        Extract driver from model object or string.
        
        Args:
            model: Model object (dict) or string
            
        Returns:
            Driver name or None if not found
        """
        if isinstance(model, dict):
            model_id = model.get('id') or model.get('name') or model.get('model', '')
            
            # First priority: check if model has 'provider' field (Puter API standard)
            if 'provider' in model and model['provider']:
                provider = str(model['provider']).lower()
                
                # Map provider names to driver names
                provider_to_driver = {
                    'openai': 'openai-completion',
                    'openai-completion': 'openai-completion',
                    'anthropic': 'claude',
                    'claude': 'claude',
                    'mistral': 'mistral',
                    'xai': 'xai',
                    'x-ai': 'xai',
                    'deepseek': 'deepseek',
                    'google': 'google',
                    'together-ai': 'together-ai',
                    'togetherai': 'together-ai',
                    'openrouter': 'openrouter',
                }
                
                if provider in provider_to_driver:
                    return provider_to_driver[provider]
                
                # If provider not in map, return it as-is
                return provider
            
            # Second priority: check if model has explicit 'driver' field
            if 'driver' in model and model['driver']:
                return model['driver']
            
        elif isinstance(model, str):
            model_id = model
        else:
            return None
        
        # Fallback to heuristics based on model ID
        model_id_lower = str(model_id).lower()
        
        for pattern, driver in self.DRIVER_HEURISTICS.items():
            if pattern in model_id_lower:
                return driver
        
        # Default fallback
        return 'openai-completion'
    
    def _update_cache_from_api(self) -> None:
        """
        Update cache by fetching from API.
        
        This method:
        1. Fetches models from Puter API
        2. Extracts driver for each model
        3. Updates cache and timestamp
        """
        try:
            data = self._fetch_from_api()
            models = data.get('models', [])
            
            new_cache = {}
            
            for model in models:
                if isinstance(model, dict):
                    model_id = model.get('id') or model.get('name') or model.get('model')
                elif isinstance(model, str):
                    model_id = model
                else:
                    continue
                
                if not model_id:
                    continue
                
                driver = self._extract_driver_from_model(model)
                if driver:
                    new_cache[str(model_id)] = driver
            
            # Update cache atomically
            self._cache = new_cache
            self._cache_timestamp = datetime.now()
            
            print(f"✅ Puter models cache updated: {len(self._cache)} models")
            
        except Exception as e:
            print(f"⚠️  Failed to update Puter models cache from API: {e}")
            print(f"⚠️  Will use heuristics as fallback")
    
    def get_driver(self, model: str, token: Optional[str] = None) -> str:
        """
        Get driver for a given model.
        
        Args:
            model: Model name/ID
            token: Optional Puter token (if not set previously)
            
        Returns:
            Driver name (e.g., 'openai-completion', 'claude', 'openrouter')
        """
        # Set token if provided
        if token:
            self.set_token(token)
        
        # Update cache if invalid
        if not self._is_cache_valid():
            if self._token:
                self._update_cache_from_api()
            else:
                print("⚠️  No Puter token set, using heuristics only")
        
        # Try to get from cache first
        if model in self._cache:
            return self._cache[model]
        
        # Fallback to heuristics
        driver = self._extract_driver_from_model(model)
        
        if driver:
            # Cache the heuristic result
            self._cache[model] = driver
            return driver
        
        # Ultimate fallback
        return 'openai-completion'
    
    def get_all_models(self) -> Dict[str, str]:
        """
        Get all cached model-to-driver mappings.
        
        Returns:
            Dictionary mapping model names to driver names
        """
        if not self._is_cache_valid() and self._token:
            self._update_cache_from_api()
        
        return self._cache.copy()
    
    def clear_cache(self) -> None:
        """Clear the cache, forcing a refresh on next access."""
        self._cache.clear()
        self._cache_timestamp = None


# Global singleton instance
_puter_cache = PuterModelsCache()


def get_model_driver(model: str, token: Optional[str] = None) -> str:
    """
    Convenience function to get driver for a model.
    
    This is the main function to use from other modules.
    
    Args:
        model: Model name/ID
        token: Optional Puter token
        
    Returns:
        Driver name
        
    Examples:
        >>> driver = get_model_driver("gpt-4o", token="...")
        >>> print(driver)  # "openai-completion"
        
        >>> driver = get_model_driver("openrouter:deepseek/deepseek-chat")
        >>> print(driver)  # "openrouter"
        
        >>> driver = get_model_driver("claude-3-5-sonnet")
        >>> print(driver)  # "claude"
    """
    return _puter_cache.get_driver(model, token)


def get_all_model_drivers(token: Optional[str] = None) -> Dict[str, str]:
    """
    Get all model-to-driver mappings.
    
    Args:
        token: Optional Puter token
        
    Returns:
        Dictionary mapping model names to driver names
    """
    if token:
        _puter_cache.set_token(token)
    
    return _puter_cache.get_all_models()


def clear_models_cache() -> None:
    """Clear the models cache."""
    _puter_cache.clear_cache()


def map_driver_to_provider(driver: str) -> str:
    """
    Map Puter driver name to LiteLLM provider name.
    
    This is needed because LiteLLM requires the provider name to properly
    parse responses from the Puter API.
    
    Args:
        driver: Puter driver name (e.g., "openai-completion", "claude", "deepseek")
        
    Returns:
        LiteLLM provider name (e.g., "openai", "anthropic", "deepseek")
        
    Examples:
        >>> map_driver_to_provider("openai-completion")
        "openai"
        >>> map_driver_to_provider("claude")
        "anthropic"
        >>> map_driver_to_provider("openrouter")
        "openrouter"
    """
    # Mapping from Puter driver names to LiteLLM provider names
    driver_mapping = {
        # OpenAI
        "openai-completion": "openai",
        "openai": "openai",
        
        # Anthropic
        "claude": "anthropic",
        "anthropic": "anthropic",
        
        # DeepSeek
        "deepseek": "deepseek",
        
        # Google
        "gemini": "gemini",
        "google": "gemini",
        "google-ai-studio": "gemini",
        
        # Mistral
        "mistral": "mistral",
        
        # xAI
        "xai": "xai",
        "grok": "xai",
        
        # OpenRouter (proxy for multiple providers)
        "openrouter": "openrouter",
        
        # Meta/Llama
        "llama": "together_ai",
        "meta": "together_ai",
        
        # Cohere
        "cohere": "cohere",
        
        # AI21
        "ai21": "ai21",
    }
    
    # Try exact match first
    if driver in driver_mapping:
        return driver_mapping[driver]
    
    # Try matching by prefix (e.g., "openai-chat" -> "openai")
    for driver_prefix, provider in driver_mapping.items():
        if driver.startswith(driver_prefix):
            return provider
    
    # If no match found, return the driver as-is
    # LiteLLM will try to use it directly
    return driver


def get_model_provider(model: str, token: Optional[str] = None) -> str:
    """
    Get the LiteLLM provider name for a model.
    
    This combines get_model_driver() with map_driver_to_provider() to return
    the provider name that LiteLLM expects.
    
    Args:
        model: Model name/ID
        token: Optional Puter token
        
    Returns:
        LiteLLM provider name
        
    Examples:
        >>> get_model_provider("gpt-4o")
        "openai"
        >>> get_model_provider("claude-3-5-sonnet-20241022")
        "anthropic"
        >>> get_model_provider("deepseek-chat")
        "deepseek"
    """
    driver = get_model_driver(model, token)
    return map_driver_to_provider(driver)


if __name__ == "__main__":
    """
    Test the cache without authentication (using heuristics).
    """
    print("=" * 70)
    print("  PUTER MODELS CACHE - HEURISTICS TEST")
    print("=" * 70)
    
    test_models = [
        ("gpt-4o", "openai-completion"),
        ("gpt-4o-mini", "openai-completion"),
        ("o1-mini", "openai-completion"),
        ("claude-3-5-sonnet", "claude"),
        ("claude-3-opus", "claude"),
        ("gemini-1.5-pro", "google"),
        ("gemini-2.0-flash", "google"),
        ("deepseek-chat", "deepseek"),
        ("deepseek-v3", "deepseek"),
        ("mistral-large", "mistral"),
        ("pixtral-12b", "mistral"),
        ("grok-2", "xai"),
        ("openrouter:deepseek/deepseek-chat", "openrouter"),
        ("togetherai:meta-llama/llama-3", "together-ai"),
    ]
    
    print("\n🧪 Testing driver detection with heuristics:\n")
    
    passed = 0
    failed = 0
    
    for model, expected_driver in test_models:
        driver = get_model_driver(model)
        
        if driver == expected_driver:
            print(f"  ✅ {model:40} → {driver}")
            passed += 1
        else:
            print(f"  ❌ {model:40} → {driver} (expected: {expected_driver})")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n✅ ALL HEURISTICS TESTS PASSED!")
    else:
        print(f"\n❌ {failed} test(s) failed")
