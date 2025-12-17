"""
Puter LLM Provider for LiteLLM
================================

This module provides integration between LiteLLM and Puter's AI API,
allowing access to multiple LLM providers (OpenAI, Anthropic, OpenRouter, etc.)
through a unified interface.

Author: Puter Team
License: MIT
"""

import httpx
import litellm
from typing import Optional, List, Dict, Any, Union
from json import dumps, loads

from litellm import CustomLLM, ModelResponse
from litellm.llms.custom_httpx.http_handler import HTTPHandler, AsyncHTTPHandler
from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObject
from httpx._types import RequestFiles
from putergenai.putergenai import PuterClient


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
    
    Args:
        params: Original parameters dictionary
        
    Returns:
        Filtered parameters dictionary with only valid model parameters
    """
    return {
        key: value 
        for key, value in params.items() 
        if key in VALID_MODEL_PARAMS and value is not None
    }


class PuterAsyncHTTPHandler(AsyncHTTPHandler):
    """
    Async HTTP handler for Puter API requests.
    
    This handler intercepts LiteLLM's HTTP calls and redirects them to Puter's
    unified AI API endpoint, handling authentication and request transformation.
    """
    
    def __init__(self, api_key: str, *args, **kwargs):
        """
        Initialize the async HTTP handler.
        
        Args:
            api_key: Puter API key for authentication
            *args, **kwargs: Additional arguments passed to parent class
        """
        if not api_key or api_key == "None":
            raise ValueError("Valid Puter API key is required")
            
        self.api_key = api_key
        super().__init__(*args, **kwargs)

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
        """
        # Redirect to Puter's unified endpoint
        url = 'https://api.puter.com/drivers/call'
        
        # Parse request data
        request_data = loads(data) if isinstance(data, (str, bytes)) else (json or {})
        model = request_data.get('model')

        # Filter to only valid model parameters
        filtered_args = filter_model_params(request_data)

        # Determine the appropriate driver for this model
        driver = PuterClient().model_to_driver.get(model, "openai-completion")
        
        # Construct Puter API payload with filtered arguments
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": filtered_args,
            "stream": stream,
            "test_mode": False,
        }
        
        # Serialize payload
        data = dumps(payload)
        
        # Set required headers for Puter API
        # Note: Origin header is CRITICAL for Puter authentication
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Origin": "https://puter.com",
            "Referer": "https://puter.com/",
        }
        
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
        
        # Handle streaming responses
        if stream:
            return puter_response
            
        # Parse Puter's response
        response_json = puter_response.json()
        
        # Check if Puter returned an error
        if not response_json.get('success', True):
            # Return only the error content for LiteLLM to parse
            error_content = response_json.get('error', {})
            puter_response._content = bytes(dumps(error_content).encode())
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


class PuterHTTPHandler(HTTPHandler):
    """
    Synchronous HTTP handler for Puter API requests.
    
    This handler intercepts LiteLLM's HTTP calls and redirects them to Puter's
    unified AI API endpoint, handling authentication and request transformation.
    """
    
    def __init__(self, api_key: str, *args, **kwargs):
        """
        Initialize the sync HTTP handler.
        
        Args:
            api_key: Puter API key for authentication
            *args, **kwargs: Additional arguments passed to parent class
        """
        if not api_key or api_key == "None":
            raise ValueError("Valid Puter API key is required")
            
        self.api_key = api_key
        super().__init__(*args, **kwargs)

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
        """
        # Redirect to Puter's unified endpoint
        url = 'https://api.puter.com/drivers/call'
        
        # Parse request data
        request_data = loads(data) if isinstance(data, (str, bytes)) else (json or data or {})
        model = request_data.get('model')
        
        # Filter to only valid model parameters
        filtered_args = filter_model_params(request_data)
        
        # Determine the appropriate driver for this model
        driver = PuterClient().model_to_driver.get(model, "openai-completion")
        
        # Construct Puter API payload with filtered arguments
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": filtered_args,
            "stream": stream,
            "test_mode": False,
        }
        
        # Serialize payload
        data = dumps(payload)
        
        # Set required headers for Puter API
        # Note: Origin header is CRITICAL for Puter authentication
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Origin": "https://puter.com",
            "Referer": "https://puter.com/",
        }
        
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
        
        # Handle streaming responses
        if stream:
            return puter_response
            
        # Parse Puter's response
        response_json = puter_response.json()
        
        # Check if Puter returned an error
        if not response_json.get('success', True):
            # Return only the error content for LiteLLM to parse
            error_content = response_json.get('error', {})
            puter_response._content = bytes(dumps(error_content).encode())
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
