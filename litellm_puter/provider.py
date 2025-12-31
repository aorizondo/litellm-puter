"""
Puter LLM Provider for LiteLLM
================================

This module provides integration between LiteLLM and Puter's AI API,
allowing access to multiple LLM providers (OpenAI, Anthropic, OpenRouter, etc.)
through a unified interface.

Author: Puter Team
License: MIT
"""

import os

import httpx
import litellm
from typing import List, Any, Union, Optional
from json import dumps, loads
from litellm import CustomLLM, ModelResponse
from litellm.llms.custom_httpx.http_handler import HTTPHandler, AsyncHTTPHandler
from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObject
from httpx._types import RequestFiles

from .models_cache import get_model_driver


# Valid model parameters that should be passed to the LLM provider
VALID_MODEL_PARAMS = {
    'messages',
    'model',
    'max_tokens',
    'temperature',
    'top_p',
    'frequency_penalty',
    'presence_penalty',
    'stop',
    'n',
    'stream',
    'user',
    'tools',
    'tool_choice',
    'response_format',
    'seed',
    'logprobs',
    'top_logprobs',
    'logit_bias',
    'optional_params',
}

# LiteLLM internal parameters that should NOT be passed to the provider
LITELLM_INTERNAL_PARAMS = {
    'custom_llm_provider',
    'litellm_params',
    'api_key',
    'api_base',
    'api_version',
    'client',
    'acompletion',
    'extra_headers',
    'timeout',
    'base_url',
    'organization',
    'max_retries',
    'default_headers',
    'caching',
    'metadata',
    'mock_response',
    'force_timeout',
    'num_retries',
    'context_window_fallback_dict',
}


def filter_model_params(params: dict) -> dict:
    """
    Filter request parameters to only include valid model parameters.
    
    Removes LiteLLM internal parameters that shouldn't be passed to the provider.
    
    IMPORTANT: max_tokens handling
    ------------------------------
    Puter automatically calculates max_tokens based on:
    - Model's max_tokens limit (from OpenRouter API)
    - User's available credits
    - Approximate token count of the prompt
    
    See: puter/src/backend/src/services/ai/chat/AIChatService.ts:359-361
    
    Therefore, we should NOT send max_tokens unless explicitly specified by the user.
    If max_tokens is sent and exceeds the model's limit, OpenRouter will return:
    "Error 400: Invalid max_tokens value, the valid range is [1, X]"
    
    Args:
        params: Original parameters dictionary
        
    Returns:
        Filtered parameters dictionary with only valid model parameters
    """
    filtered = {
        key: value
        for key, value in params.items()
        if key in VALID_MODEL_PARAMS and value is not None
    }

    # Special handling for max_tokens:
    # IMPORTANT: Puter calculates max_tokens automatically on the server side.
    # Sending max_tokens can cause errors if it exceeds the model's limit.
    # 
    # Best practice: DON'T send max_tokens unless absolutely necessary.
    # Let Puter handle it automatically based on model limits and user credits.
    #
    # We remove max_tokens in these cases:
    # 1. It's None
    # 2. It's extremely high (>100,000) - likely a default
    # 3. It's in the "dangerous zone" (>8000) where it might exceed model limits
    #
    # We keep max_tokens only if:
    # - User explicitly sets a reasonable value (1-8000)
    # - This gives user control while avoiding most errors
    if 'max_tokens' in filtered:
        max_tokens_value = filtered['max_tokens']

        if max_tokens_value is None:
            # None means not set, remove it
            del filtered['max_tokens']
        elif max_tokens_value > 8000:
            # Values >8000 are risky for many OpenRouter models
            # Let Puter calculate the safe value
            del filtered['max_tokens']

    return filtered


class PuterHTTPHandlerBase:
    """
    Base class for Puter HTTP handlers with common logic.
    
    This class contains shared functionality for both sync and async handlers,
    eliminating code duplication and ensuring consistent behavior.
    """

    def __init__(self, api_key: str):
        """
        Initialize the base handler.
        
        Args:
            api_key: Puter API key for authentication
            
        Raises:
            ValueError: If API key is invalid or missing
        """
        if not api_key or api_key == "None":
            raise ValueError("Valid Puter API key is required")
        self.api_key = api_key
        self.token_index = 0

    def _build_puter_request(
            self,
            url: str = 'https://api.puter.com/drivers/call',
            data: Optional[Union[dict, str, bytes]] = None,
            json: Optional[Union[dict, str, List]] = None,
            params: Optional[dict] = None,
            headers: Optional[dict] = None,
            stream: bool = False,
            timeout: Optional[Union[float, httpx.Timeout]] = None,
            files: Optional[Union[dict, RequestFiles]] = None,
            content: Any = None,
            logging_obj: Optional[LiteLLMLoggingObject] = None,
    ) -> dict:
        request_data = loads(data) if isinstance(data, (str, bytes)) else (json or {})
        model = request_data.get('model')

        # Filter to only valid model parameters
        filtered_args = filter_model_params(request_data)

        # Determine the appropriate driver for this model
        # Using our own cache instead of putergenai dependency
        driver = get_model_driver(model, token=self.api_key)

        # Construct Puter API payload with filtered arguments
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": filtered_args,
            "stream": stream,
            "test_mode": False,
            # "auth_token": self.api_key,
        }
        puter_headers = self._get_headers()
        headers.update(puter_headers)
        puter_request = dict(
            url=url,
            data=dumps(payload),
            params=params,
            headers=puter_headers,
            timeout=timeout,
            stream=stream,
            logging_obj=logging_obj,
            files=files,
            content=content,
        )
        return puter_request

    def _get_headers(self) -> dict:
        """
        Get the required headers for Puter API requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Origin": "https://puter.com",
            "Referer": "https://puter.com/",
        }

    def _handle_puter_response(
            self,
            puter_response: httpx.Response
    ) -> Any:
        if loads(puter_response.request.content).get('stream'):
            return puter_response
        response_json = puter_response.json()
        # Check if Puter returned an error
        if not response_json.get('success', True):
            # Return only the error content for LiteLLM to parse
            error_content = response_json.get('error', {})
            # puter_response._content = bytes(dumps(error_content).encode())
            # Set appropriate status code if available
            if 'status' in error_content:
                puter_response.status_code = error_content['status']
            return puter_response

        # Transform successful response based on driver type
        if loads(puter_response.request.content).get('driver') == 'claude':
            # Claude returns response in a different format
            puter_response._content = bytes(
                dumps(response_json['result']['message']).encode()
            )
        else:
            # Standard OpenAI-compatible format
            result = response_json['result']
            usage = result.pop('usage', {})

            transformed_response = {
                'choices': [result],
                'model': loads(puter_response.request.content).get('args')['model'],
                'usage': usage
            }
            puter_response._content = bytes(dumps(transformed_response).encode())

        return puter_response


class PuterAsyncHTTPHandler(AsyncHTTPHandler, PuterHTTPHandlerBase):
    """
    Async HTTP handler for Puter API requests.
    
    This handler intercepts LiteLLM's HTTP calls and redirects them to Puter's
    unified AI API endpoint, handling authentication and request transformation.
    Supports both streaming and non-streaming responses.
    Supports proxy configuration via custom_httpx_client.
    """

    def __init__(self, api_key: str, *args, custom_httpx_client=None, **kwargs):
        """
        Initialize the async HTTP handler.
        
        Args:
            api_key: Puter API key for authentication
            custom_httpx_client: Optional custom httpx.AsyncClient (for proxy support, etc.)
            *args, **kwargs: Additional arguments passed to parent class
        """
        PuterHTTPHandlerBase.__init__(self, api_key)
        AsyncHTTPHandler.__init__(self, *args, **kwargs)

        # Override the client if a custom one was provided
        if custom_httpx_client:
            self.client = custom_httpx_client

    async def post(
            self,
            url: str,
            data: Optional[Union[dict, str, bytes]] = None,
            json: Optional[Union[dict, str, List]] = None,
            params: Optional[dict] = None,
            headers: Optional[dict] = None,
            stream: bool = False,
            timeout: Optional[Union[float, httpx.Timeout]] = None,
            files: Optional[Union[dict, RequestFiles]] = None,
            content: Any = None,
            logging_obj: Optional[LiteLLMLoggingObject] = None,
    ):
        """
        Override POST method to redirect requests to Puter API.
        
        Transforms standard LLM API requests into Puter's driver-based format.
        Filters parameters to only include valid model parameters.
        Supports streaming responses from Puter.
        """
        puter_request = self._build_puter_request(
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
            stream=stream,
            logging_obj=logging_obj,
            files=files,
            content=content,
        )
        puter_response = await super().post(
            **puter_request,
        )
        parsed_response = self._handle_puter_response(puter_response)
        try:
            if "You have reached your AI usage limit for this account" in str(puter_response.json()):
                with open('token.txt', 'r') as f:
                    tokens = f.readlines()
                for token in range(len(tokens)):
                    result = tokens[token].strip()
                    usage = await super().get("https://api.puter.com/metering/usage",
                        headers={
                            "accept": "*/*",
                            "accept-language": "es-ES,es;q=0.9,ru;q=0.8,en;q=0.7",
                            "authorization": "Bearer " + result,
                            "referrer": "https://puter.com/",
                        },
                    )
                    usage = usage.json()
                    remaining = usage['allowanceInfo']['remaining']
                    print(f"index {self.token_index} token {token+1} usage {usage['allowanceInfo']['remaining']}")
                    if token < self.token_index or result == self.api_key or not result or not remaining:
                        continue
                    self.token_index = token
                    self.api_key = os.environ["PUTER_API_KEY"] = os.environ["PUTER_TOKEN"] = result
                    return await self.post(
                        url=url,
                        data=data,
                        json=json,
                        params=params,
                        headers=headers,
                        timeout=timeout,
                        stream=stream,
                        logging_obj=logging_obj,
                        files=files,
                        content=content,
                    )
                else:
                    self.token_index = 0
        except Exception as e:
            print(e)
            # raise

        # Handle response using base class method
        return parsed_response


class PuterHTTPHandler(HTTPHandler, PuterHTTPHandlerBase):
    """
    Synchronous HTTP handler for Puter API requests.
    
    This handler intercepts LiteLLM's HTTP calls and redirects them to Puter's
    unified AI API endpoint, handling authentication and request transformation.
    Supports both streaming and non-streaming responses.
    Supports proxy configuration via custom_httpx_client.
    """

    def __init__(self, api_key: str, *args, custom_httpx_client=None, **kwargs):
        """
        Initialize the sync HTTP handler.
        
        Args:
            api_key: Puter API key for authentication
            custom_httpx_client: Optional custom httpx.Client (for proxy support, etc.)
            *args, **kwargs: Additional arguments passed to parent class
        """
        PuterHTTPHandlerBase.__init__(self, api_key)
        HTTPHandler.__init__(self, *args, **kwargs)

        # Override the client if a custom one was provided
        if custom_httpx_client:
            self.client = custom_httpx_client

    def post(
            self,
            url: str,
            data: Optional[Union[dict, str, bytes]] = None,
            json: Optional[Union[dict, str, List]] = None,
            params: Optional[dict] = None,
            headers: Optional[dict] = None,
            stream: bool = False,
            timeout: Optional[Union[float, httpx.Timeout]] = None,
            files: Optional[Union[dict, RequestFiles]] = None,
            content: Any = None,
            logging_obj: Optional[LiteLLMLoggingObject] = None,
    ):
        """
        Override POST method to redirect requests to Puter API.
        
        Transforms standard LLM API requests into Puter's driver-based format.
        Filters parameters to only include valid model parameters.
        Supports streaming responses from Puter.
        """
        puter_request = self._build_puter_request(
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
            stream=stream,
            logging_obj=logging_obj,
            files=files,
            content=content,
        )

        # Make the actual request
        puter_response = super().post(
            **puter_request,
        )
        parsed_response = self._handle_puter_response(puter_response)

        return parsed_response


class PuterLLM(CustomLLM):
    """
    Custom LLM implementation for Puter provider.
    
    This class integrates with LiteLLM's custom provider system, allowing
    Puter to be used as a first-class provider alongside OpenAI, Anthropic, etc.
    Supports HTTP/HTTPS/SOCKS5 proxies via environment variables.
    """

    def _get_proxy_config(self) -> Optional[str]:
        """
        Get proxy configuration from environment variables.
        
        Checks in order: SOCKS5_PROXY, HTTPS_PROXY, HTTP_PROXY, ALL_PROXY
        
        Returns:
            Proxy URL string or None if no proxy configured
        """
        import os
        return (
            os.getenv("SOCKS5_PROXY") or 
            os.getenv("HTTPS_PROXY") or 
            os.getenv("HTTP_PROXY") or 
            os.getenv("ALL_PROXY")
        )

    def _create_http_client(self) -> Optional[httpx.Client]:
        """
        Create httpx.Client with proxy support if configured.
        
        Supports HTTP, HTTPS, and SOCKS5 proxies.
        For SOCKS5 proxies, SSL verification is disabled to avoid connection issues.
        
        Returns:
            httpx.Client instance with proxy or None if no proxy configured
        """
        proxy_url = self._get_proxy_config()
        if not proxy_url:
            return None
        
        # Configure client based on proxy type
        client_kwargs = {"proxy": proxy_url}
        
        # Disable SSL verification for SOCKS proxies to avoid connection issues
        if proxy_url.startswith('socks'):
            client_kwargs["verify"] = False
        
        return httpx.Client(**client_kwargs)

    def _create_async_http_client(self) -> Optional[httpx.AsyncClient]:
        """
        Create httpx.AsyncClient with proxy support if configured.
        
        Supports HTTP, HTTPS, and SOCKS5 proxies.
        For SOCKS5 proxies, SSL verification is disabled to avoid connection issues.
        
        Returns:
            httpx.AsyncClient instance with proxy or None if no proxy configured
        """
        proxy_url = self._get_proxy_config()
        if not proxy_url:
            return None
        
        # Configure client based on proxy type
        client_kwargs = {"proxy": proxy_url}
        
        # Disable SSL verification for SOCKS proxies to avoid connection issues
        if proxy_url.startswith('socks'):
            client_kwargs["verify"] = False
        
        return httpx.AsyncClient(**client_kwargs)

    def _build_completion_args(self, http_client, **kwargs):
        """
        Build common completion arguments for both sync and async requests.
        
        Args:
            http_client: httpx.Client or httpx.AsyncClient instance (or None)
            **kwargs: Additional parameters from completion call
            
        Returns:
            Dictionary with completion arguments
        """
        import os

        # Get API key from environment
        api_key = os.getenv("PUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "PUTER_API_KEY environment variable is required. "
                "Get your API key from https://puter.com/"
            )

        # Filter kwargs to only include valid model parameters
        filtered_kwargs = filter_model_params(kwargs)
        if 'optional_params' in kwargs:
            filtered_kwargs.update(**kwargs['optional_params'])
            filtered_kwargs['optional_params'] = kwargs['optional_params']
        
        # Build completion arguments with only necessary parameters
        client_args = {'api_key': api_key}
        if http_client:
            client_args['custom_httpx_client'] = http_client

        completion_args = {
            'client': kwargs['client'](**client_args),
            'api_key': api_key,
            'base_url': 'https://api.puter.com/drivers/call',
            'extra_headers': {
                "Content-Type": "application/json",
                "Origin": "https://puter.com",
                "Referer": "https://puter.com/",
                "Authorization": "Bearer " + api_key
            },
        }

        # Add all filtered model parameters
        completion_args.update(filtered_kwargs)

        return completion_args

    def completion(self, *args, **kwargs) -> ModelResponse:
        """
        Handle synchronous completion requests with optional proxy support.
        
        Proxy configuration via environment variables:
        - SOCKS5_PROXY: socks5://host:port
        - HTTPS_PROXY: https://host:port
        - HTTP_PROXY: http://host:port
        - ALL_PROXY: any of the above
        """
        import os
        
        # Enable experimental HTTP handler support
        os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"
        
        # Create HTTP client with proxy support
        http_client = self._create_http_client()
        
        kwargs['client'] = PuterHTTPHandler
        new_kwargs = self._build_completion_args(http_client, **kwargs)
        return litellm.completion(**new_kwargs)

    async def acompletion(self, *args, **kwargs) -> ModelResponse:
        """
        Handle asynchronous completion requests with optional proxy support.
        
        Proxy configuration via environment variables:
        - SOCKS5_PROXY: socks5://host:port
        - HTTPS_PROXY: https://host:port
        - HTTP_PROXY: http://host:port
        - ALL_PROXY: any of the above
        """
        import os
        
        # Enable experimental HTTP handler support
        os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"
        
        # Create async HTTP client with proxy support
        http_client = self._create_async_http_client()
        
        kwargs['client'] = PuterAsyncHTTPHandler
        new_kwargs = self._build_completion_args(http_client, **kwargs)
        return await litellm.acompletion(**new_kwargs)


# Global instance for easy import
puter_llm = PuterLLM()


# Convenience function for quick setup
def setup_puter_provider():
    """
    Register Puter as a custom provider in LiteLLM.
    
    Usage:
        from puter_provider import setup_puter_provider
        setup_puter_provider()
        
        # Now you can use Puter models directly
        response = litellm.completion(
            model="puter/openrouter:deepseek/deepseek-chat",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    # Get existing custom providers or create new list
    if not hasattr(litellm, 'custom_provider_map') or litellm.custom_provider_map is None:
        litellm.custom_provider_map = []

    # Check if puter is already registered
    puter_registered = any(
        provider.get('provider') == 'puter'
        for provider in litellm.custom_provider_map
    )

    if not puter_registered:
        litellm.custom_provider_map.append(
            {"provider": "puter", "custom_handler": puter_llm}
        )

    return puter_llm
