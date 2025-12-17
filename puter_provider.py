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
from typing import Optional, List, Dict, Any, Union
from json import dumps, loads

from litellm import CustomLLM, ModelResponse
from litellm.llms.custom_httpx.http_handler import HTTPHandler, AsyncHTTPHandler
from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObject
from httpx._types import RequestFiles
from puter_models_cache import get_model_driver


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
    
    def _build_puter_payload(
        self,
        request_data: dict,
        stream: bool = False
    ) -> tuple[str, dict]:
        """
        Build the payload for Puter API call.
        
        Args:
            request_data: The original request data
            stream: Whether streaming is enabled
            
        Returns:
            Tuple of (serialized_data, model)
        """
        model = request_data.get('model')
        
        # Filter to only valid model parameters
        filtered_args = filter_model_params(request_data)
        
        # Determine the appropriate driver for this model
        # Using our own cache instead of putergenai dependency
        puter_token = os.getenv("PUTER_TOKEN") or os.getenv("PUTER_API_KEY")
        driver = get_model_driver(model, token=puter_token)
        
        # Construct Puter API payload with filtered arguments
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": filtered_args,
            "stream": stream,
            "test_mode": False,
        }
        
        return dumps(payload), model, driver
    
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
        response_json: dict,
        model: str,
        driver: str,
        puter_response: Any
    ) -> Any:
        """
        Handle and transform Puter API response.
        
        Args:
            response_json: Parsed JSON response from Puter
            model: Model name used
            driver: Driver name used
            puter_response: The original HTTP response object
            
        Returns:
            Transformed response
        """
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
        if driver == 'claude':
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
                'model': model,
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
    """
    
    def __init__(self, api_key: str, *args, **kwargs):
        """
        Initialize the async HTTP handler.
        
        Args:
            api_key: Puter API key for authentication
            *args, **kwargs: Additional arguments passed to parent class
        """
        PuterHTTPHandlerBase.__init__(self, api_key)
        AsyncHTTPHandler.__init__(self, *args, **kwargs)

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
        # Redirect to Puter's unified endpoint
        url = 'https://api.puter.com/drivers/call'
        
        # Parse request data
        request_data = loads(data) if isinstance(data, (str, bytes)) else (json or {})
        
        # Build Puter payload using base class method
        data, model, driver = self._build_puter_payload(request_data, stream)
        
        # Get headers using base class method
        headers = self._get_headers()
        
        # Make the actual request
        puter_response = await super().post(
            url=url,
            data=data,
            json=None,  # Don't pass json, we're using data
            params=params,
            headers=headers,
            timeout=timeout,
            stream=stream,
            logging_obj=logging_obj,
            files=files,
            content=content,
        )
        
        # For streaming, Puter returns NDJSON format directly
        # No transformation needed - return as-is
        if stream:
            return puter_response
            
        # Parse Puter's response for non-streaming
        response_json = puter_response.json()
        
        # Handle response using base class method
        return self._handle_puter_response(response_json, model, driver, puter_response)


class PuterHTTPHandler(HTTPHandler, PuterHTTPHandlerBase):
    """
    Synchronous HTTP handler for Puter API requests.
    
    This handler intercepts LiteLLM's HTTP calls and redirects them to Puter's
    unified AI API endpoint, handling authentication and request transformation.
    Supports both streaming and non-streaming responses.
    """
    
    def __init__(self, api_key: str, *args, **kwargs):
        """
        Initialize the sync HTTP handler.
        
        Args:
            api_key: Puter API key for authentication
            *args, **kwargs: Additional arguments passed to parent class
        """
        PuterHTTPHandlerBase.__init__(self, api_key)
        HTTPHandler.__init__(self, *args, **kwargs)

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
        # Redirect to Puter's unified endpoint
        url = 'https://api.puter.com/drivers/call'
        
        # Parse request data
        request_data = loads(data) if isinstance(data, (str, bytes)) else (json or data or {})
        
        # Build Puter payload using base class method
        data, model, driver = self._build_puter_payload(request_data, stream)
        
        # Get headers using base class method
        headers = self._get_headers()
        
        # Make the actual request
        puter_response = super().post(
            url,
            data,
            None,  # Don't pass json, we're using data
            params,
            headers,
            stream,
            timeout,
            files,
            content,
            logging_obj
        )
        
        # For streaming, Puter returns NDJSON format directly
        # No transformation needed - return as-is
        if stream:
            return puter_response
            
        # Parse Puter's response for non-streaming
        response_json = puter_response.json()
        
        # Handle response using base class method
        return self._handle_puter_response(response_json, model, driver, puter_response)


class PuterLLM(CustomLLM):
    """
    Custom LLM implementation for Puter provider.
    
    This class integrates with LiteLLM's custom provider system, allowing
    Puter to be used as a first-class provider alongside OpenAI, Anthropic, etc.
    """
    def puter_completion_args(self, *args, **kwargs):
        """
        Transforms model names and filters parameters for Puter API.
        
        Only passes valid model parameters to avoid errors from LiteLLM internal params.
        """
        import os

        # Get API key from environment
        api_key = os.getenv("PUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "PUTER_API_KEY environment variable is required. "
                "Get your API key from https://puter.com/"
            )

        # Enable experimental HTTP handler support
        os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"

        # Filter kwargs to only include valid model parameters
        filtered_kwargs = filter_model_params(kwargs)
        
        # Build completion arguments with only necessary parameters
        completion_args = {
            'client': kwargs['client'](api_key=api_key),
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
        Handle synchronous completion requests.
        """
        kwargs['client'] = PuterHTTPHandler
        new_kwargs = self.puter_completion_args(*args, **kwargs)
        return litellm.completion(**new_kwargs)


    async def acompletion(self, *args, **kwargs) -> ModelResponse:
        """
        Handle asynchronous completion requests.
        """
        kwargs['client'] = PuterAsyncHTTPHandler
        kwargs = self.puter_completion_args(*args, **kwargs)
        return await litellm.acompletion(**kwargs)


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
    litellm.custom_provider_map = [
        {"provider": "puter", "custom_handler": puter_llm}
    ]
    return puter_llm
