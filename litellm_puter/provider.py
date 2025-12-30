"""
Puter LLM Provider for LiteLLM
================================

This module provides integration between LiteLLM and Puter's AI API,
allowing access to multiple LLM providers (OpenAI, Anthropic, OpenRouter, etc.)
through a unified interface.

Author: Puter Team
License: MIT
"""

import asyncio
import os
import re

import httpx
import litellm
from typing import List, Any, Union, Optional
from json import dumps, loads
from litellm import CustomLLM, ModelResponse
from litellm.llms.custom_httpx.http_handler import HTTPHandler, AsyncHTTPHandler
from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObject
from httpx._types import RequestFiles
from patchright._impl._errors import TargetClosedError
# from xvfbwrapper import Xvfb

from .models_cache import get_model_driver
from patchright.async_api import async_playwright, expect, Request, Response, ProxySettings
import random


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


class AsyncPuterWebLogin:
    def __init__(self, debug: bool = False, headless: Optional[bool] = False, useragent: Optional[str] = None):
        self.debug = debug
        self.browser_type = "chrome"
        self.headless = headless
        self.useragent = useragent
        self.browser_args = []
        if useragent:
            self.browser_args.append(f"--user-agent={useragent}")
        self.stop = False
        self.token = None

    async def get_temp_token(self, url: str = 'https://puter.com', max_attempts: int = 10, proxy: str | None = None) -> str | None:
        locator_str = "//*[@id='captcha-widget-turnstile-challenge-modal']"
        timeout = 1000 * 60 * 10
        url_with_slash = url + "/" if not url.endswith("/") else url
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                channel=self.browser_type,
                headless=self.headless,
                args=self.browser_args,
            )
            if proxy:
                context = await browser.new_context(proxy={"server": proxy})
            else:
                context = browser.contexts[0] if len(browser.contexts) else await browser.new_context()

            # await context.clear_cookies()
            page = context.pages[0] if len(context.pages) else await context.new_page()

            try:
                await page.goto(url_with_slash, timeout=0, wait_until='domcontentloaded')
            except Exception as e:
                print(e)
                return
            page.on("requestfinished", self.on_requestfinished)
            locator = page.locator(locator_str)
            modal = False
            click = False
            turnstile_response = False
            for _ in range(max_attempts):
                if self.stop:
                    break
                try:
                    if not modal:
                        await locator.wait_for(state="attached", timeout=0)
                        modal = True
                        await page.locator("//*[@data-sitekey='0x4AAAAAABvMyOLo9EwjFVzC']").wait_for(state="attached", timeout=100)
                    await page.wait_for_timeout(random.randint(700, 3000))
                    if not click:
                        try:
                            await locator.click(timeout=500)
                        except:
                            pass
                        try:
                            await locator.wait_for(state="detached", timeout=500)
                            click = True
                        except:
                            pass
                    try:
                        if not turnstile_response:
                            await expect(page.locator("[name=cf-turnstile-response]")).to_have_value(re.compile(r"."), timeout=500)
                            turnstile_response = True
                    except:
                        pass
                    for cookie in await context.cookies():
                        if cookie['name'] == 'puter_auth_token':
                            return cookie['value']
                    if self.token:
                        return self.token
                except TargetClosedError as e:
                    return
                except Exception as e:
                    print(e)
                    continue
            while not self.stop:
                continue
            await browser.close()
        return None

    async def on_requestfinished(self, request: Request):
        if 'puter.com/signup' in request.url:
            try:
                response: Response = await request.response()
                # await response.finished()
                print(str(await response.body()))
                r_json = await response.json()
                print(r_json)
                self.token = r_json['token']
            except:
                pass
            self.stop = True

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
                    print(usage['allowanceInfo']['remaining'])
                    if token < self.token_index or result == self.api_key or not result:
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
    """

    def puter_completion_args(self, *args, **kwargs):
        """
        Transforms model names and filters parameters for Puter API.
        
        Only passes valid model parameters to avoid errors from LiteLLM internal params.
        
        Note: LiteLLM automatically strips the 'puter/' prefix before calling this method,
        so we receive the model in format '<provider>/<model>' (e.g., 'openai/gpt-4o')
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

        # Configure proxy if enabled (optional - for bypassing IP blocks)
        use_proxy = os.getenv("USE_PROXY", "false").lower() == "true"
        http_client = None

        if use_proxy:
            proxy_url = os.getenv("SOCKS5_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
            if proxy_url:
                # httpx will use ALL_PROXY for all protocols including HTTPS
                os.environ['ALL_PROXY'] = proxy_url

                # Create custom httpx client with proxy and disabled SSL verification for SOCKS
                if proxy_url.startswith('socks'):
                    http_client = httpx.Client(proxy=proxy_url, verify=False)

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
        new_kwargs = self.puter_completion_args(*args, **kwargs)
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
