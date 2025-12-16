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
        """
        # Redirect to Puter's unified endpoint
        url = 'https://api.puter.com/drivers/call'
        
        # Parse request data
        model = loads(data).get('model') if isinstance(data, (str, bytes)) else json.get('model')

        # Determine the appropriate driver for this model
        driver = PuterClient().model_to_driver.get(model, "openai-completion")
        
        # Construct Puter API payload
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": json or loads(data),
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
            json=json,
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
            
        # Transform response based on driver type
        response_json = puter_response.json()
        
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
        """
        # Redirect to Puter's unified endpoint
        url = 'https://api.puter.com/drivers/call'
        
        # Parse request data
        request_data = loads(data) if isinstance(data, (str, bytes)) else data
        model = request_data.get('model')
        
        # Determine the appropriate driver for this model
        driver = PuterClient().model_to_driver.get(model, "openai-completion")
        
        # Construct Puter API payload
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": request_data,
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
            json,
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
            
        # Transform response based on driver type
        response_json = puter_response.json()
        
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
    
    def completion(self, *args, **kwargs) -> ModelResponse:
        """
        Handle synchronous completion requests.
        
        Transforms model names from "puter/provider:model" format to the
        appropriate format for the underlying provider.
        """
        import os
        
        # Extract and transform model name
        # Input:  "puter/openrouter:deepseek/deepseek-chat"
        # Output: "openrouter/openrouter:deepseek/deepseek-chat"
        original_model = kwargs.get('model', '')
        
        if original_model.startswith('puter/'):
            # Remove "puter/" prefix
            puter_model = original_model[6:]
            
            # Detect provider from model string
            if ':' in puter_model:
                # Format: "openrouter:deepseek/deepseek-chat"
                provider = puter_model.split(':')[0]
                transformed_model = f"{provider}/{puter_model}"
            else:
                # Format: "claude-sonnet-4-5-20250929"
                transformed_model = f"anthropic/{puter_model}"
            
            kwargs['model'] = transformed_model
        
        # Get API key from environment
        api_key = os.getenv("PUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "PUTER_API_KEY environment variable is required. "
                "Get your API key from https://puter.com/app/settings"
            )
        
        # Enable experimental HTTP handler support
        os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"
        
        # Create HTTP client with Puter handler
        kwargs['client'] = PuterHTTPHandler(api_key=api_key)
        kwargs['api_key'] = "none"  # Placeholder, actual auth is in handler
        
        # Make the request through LiteLLM
        return litellm.completion(*args, **kwargs)

    async def acompletion(self, *args, **kwargs) -> ModelResponse:
        """
        Handle asynchronous completion requests.
        
        Transforms model names from "puter/provider:model" format to the
        appropriate format for the underlying provider.
        """
        import os
        
        # Get API key from environment
        api_key = os.getenv("PUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "PUTER_API_KEY environment variable is required. "
                "Get your API key from https://puter.com/app/settings"
            )
        
        # Enable experimental HTTP handler support
        os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"
        
        # Create async HTTP client with Puter handler
        kwargs['api_key'] = "none"
        
        # Make the async request through LiteLLM
        return await litellm.acompletion(
            client=PuterAsyncHTTPHandler(api_key=api_key),
            api_key=api_key,
            base_url='https://api.puter.com/drivers/call',
            extra_headers={
                "Content-Type": "application/json",
                "Origin": "https://puter.com",
                "Referer": "https://puter.com/",
                "Authorization": "Bearer " + api_key
            },
            model=kwargs['model'],
            stream=False,
            messages=kwargs['messages']
        )


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
