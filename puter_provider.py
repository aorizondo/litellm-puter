# puter_provider.py
import httpx
import litellm
from boto3 import client
from httpx._types import RequestFiles
from litellm import CustomLLM, ModelResponse, get_llm_provider, Choices, Message, BaseLLMHTTPHandler, HTTPHandler, AsyncHTTPHandler
from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObject
from litellm.llms.base_llm.chat.transformation import BaseConfig
from litellm.llms.custom_httpx.llm_http_handler import LiteLLMLoggingObj
from litellm.types.utils import GenericStreamingChunk, Usage
from typing import Optional, List, Dict, Any, Union, Iterator, AsyncIterator
import asyncio
from json import dumps, loads
from putergenai.putergenai import PuterClient


class PuterAsyncHTTPHandler(AsyncHTTPHandler):
    def __init__(self, api_key, *args, **kwargs):
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
        url = 'https://api.puter.com/drivers/call'
        model = loads(data)['model']
        driver = PuterClient().model_to_driver.get(model, "openai-completion")
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": loads(data),
            "stream": stream,
            "test_mode": False,
        }
        data = dumps(payload)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            'Origin': 'https://puter.com',
            'Referer': 'https://puter.com/',
        }
        puter_response = await super().post(
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
        if driver == 'claude':
            puter_response._content = bytes(dumps(puter_response.json()['result']['message']).encode())
        else:
            response_json = puter_response.json()['result']
            usage = response_json.pop('usage')
            response_json = {
                'choices': [response_json],
                'model': model,
                'usage': usage
            }
            puter_response._content = bytes(dumps(response_json).encode())
        return puter_response


class PuterHTTPHandler(HTTPHandler):
    def __init__(self, api_key, *args, **kwargs):
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
        url = 'https://api.puter.com/drivers/call'
        model = loads(data)['model']
        driver = PuterClient().model_to_driver.get(model, "openai-completion")
        payload = {
            "interface": "puter-chat-completion",
            "driver": driver,
            "method": "complete",
            "args": loads(data),
            "stream": stream,
            "test_mode": False,
        }
        data = dumps(payload)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            'Origin': 'https://puter.com',
            'Referer': 'https://puter.com/',
        }
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
        if stream:
            return puter_response
        if driver == 'claude':
            puter_response._content = bytes(dumps(puter_response.json()['result']['message']).encode())
        else:
            response_json = puter_response.json()['result']
            usage = response_json.pop('usage')
            response_json = {
                'choices': [response_json],
                'model': model,
                'usage': usage
            }
            puter_response._content = bytes(dumps(response_json).encode())
        return puter_response


class PuterLLM(CustomLLM):
    def completion(self, *args, **kwargs) -> litellm.ModelResponse:
        model = kwargs.get('model')
        provider = model.split('/')[0].split(':')[0]
        model = provider + '/' + model.split('/')[-1]

        kwargs.update(client=PuterHTTPHandler(
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicyIsInYiOiIwLjAuMCIsInUiOiJYWUsyZHUycFFiV2sxL1QybDRxZWVBPT0iLCJ1dSI6ImdxeE5nOU45U2llUkZtUzI2S0VucVE9PSIsImlhdCI6MTc2NDg3NzYxNX0.BuR-Z3hWX-iiKLcI2Zqq8W7z0zlnJK_TXwIs3DepJZc"),
            model=model
        )
        return litellm.completion(*args, **kwargs)

    async def acompletion(self, *args, **kwargs):
        model = kwargs.get('model')
        provider = model.split('/')[0].split(':')[0]
        model = provider + '/' + model.split('/')[-1]

        kwargs.update(client=PuterAsyncHTTPHandler(
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicyIsInYiOiIwLjAuMCIsInUiOiJYWUsyZHUycFFiV2sxL1QybDRxZWVBPT0iLCJ1dSI6ImdxeE5nOU45U2llUkZtUzI2S0VucVE9PSIsImlhdCI6MTc2NDg3NzYxNX0.BuR-Z3hWX-iiKLcI2Zqq8W7z0zlnJK_TXwIs3DepJZc"),
            model=model
        )
        return litellm.acompletion(*args, **kwargs)

    def streaming(self, *args, **kwargs) -> Iterator[GenericStreamingChunk]:
        generic_streaming_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": str(int(time.time())),
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        return generic_streaming_chunk  # type: ignore


puter_llm = PuterLLM()

if __name__ == '__main__':
    litellm.custom_provider_map = [  # 👈 KEY STEP - REGISTER HANDLER
        {"provider": "puter", "custom_handler": puter_llm}
    ]

    resp = litellm.completion(
        model="puter/openrouter:deepseek/deepseek-chat",
        messages=[{"role": "user", "content": "Hello world!"}],
    )
    print(resp)
