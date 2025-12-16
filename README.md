
# Puter AI Provider for LiteLLM

This project implements a custom provider for [LiteLLM](https://github.com/BerriAI/litellm) to interact with Puter.com's AI API.

## Features
- Compatibility with LiteLLM's standard interface
- Support for both synchronous and asynchronous requests
- Automatic driver selection based on model
- Stream handling for compatible models

## Installation
```bash
pip install litellm httpx putergenai
```

## Configuration
Set your Puter API key as environment variable:
```bash
export PUTER_API_KEY="your_api_key_here"
```

## Usage
```python
import litellm
from puter_provider import puter_llm

# Register the custom provider
litellm.custom_provider_map = [
    {"provider": "puter", "custom_handler": puter_llm}
]

# Make a completion request
response = litellm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello world!"}],
)

print(response)
```

## Supported Models
The provider supports models available through Puter's API including:
- OpenRouter models
- Claude models
- OpenAI-compatible models

## Development
```bash
git clone https://github.com/yourusername/puter-litellm-provider.git
cd puter-litellm-provider
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
