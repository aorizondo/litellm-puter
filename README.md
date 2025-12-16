# 🚀 Puter LLM Provider for LiteLLM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A professional integration layer between [LiteLLM](https://github.com/BerriAI/litellm) and [Puter's AI API](https://puter.com), providing unified access to multiple LLM providers (OpenAI, Anthropic, OpenRouter, Google, and more) through a single interface.

## ✨ Features

- 🎯 **Unified Interface**: Access multiple LLM providers through Puter's API
- 🔄 **Async Support**: Full support for both synchronous and asynchronous requests
- 🔌 **Easy Integration**: Drop-in replacement for LiteLLM's standard providers
- 🛡️ **Type Safety**: Fully typed codebase with comprehensive documentation
- 📦 **Zero Config**: Works out of the box with minimal setup
- 🎨 **Multiple Providers**: Support for OpenAI, Anthropic, OpenRouter, Google, and more

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Supported Models](#-supported-models)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- A Puter API key ([Get one here](https://puter.com))

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/litellm-puter.git
cd litellm-puter

# Install required packages
pip install -r requirements.txt
```

### Required Packages

```
litellm>=1.80.0
httpx>=0.28.0
putergenai>=2.1.0
boto3>=1.42.0
python-dotenv>=1.0.0
```

## 🚀 Quick Start

### 1. Get Your API Key

1. Visit [puter.com](https://puter.com)
2. Sign in or create an account
3. Navigate to **Settings → API Keys**
4. Click **"Create new API key"**
5. Copy your API key

### 2. Configure Environment

Create a `.env` file in your project root:

```bash
PUTER_API_KEY=your_api_key_here
```

### 3. Basic Usage

```python
import litellm
from puter_provider import setup_puter_provider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Register Puter as a custom provider
setup_puter_provider()

# Make a completion request
response = litellm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
)

print(response.choices[0].message.content)
```

## 💡 Usage Examples

### Example 1: Custom Provider (Recommended)

This method registers Puter as a first-class provider in LiteLLM:

```python
import litellm
from puter_provider import setup_puter_provider
from dotenv import load_dotenv

load_dotenv()
setup_puter_provider()

response = litellm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
)
```

### Example 2: Direct HTTP Handler

For more control over the request configuration:

```python
import os
import litellm
from puter_provider import PuterHTTPHandler
from dotenv import load_dotenv

load_dotenv()
os.environ['EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER'] = "True"

response = litellm.completion(
    client=PuterHTTPHandler(api_key=os.getenv("PUTER_API_KEY")),
    model="openrouter/openrouter:deepseek/deepseek-chat",
    api_key="none",
    messages=[{"role": "user", "content": "Tell me a joke"}],
)
```

### Example 3: Async Usage

For concurrent requests and better performance:

```python
import asyncio
import litellm
from puter_provider import setup_puter_provider
from dotenv import load_dotenv

load_dotenv()
setup_puter_provider()

async def main():
    response = await litellm.acompletion(
        model="puter/openrouter:deepseek/deepseek-chat",
        messages=[{"role": "user", "content": "Hello async!"}],
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

### Example 4: Multiple Providers

Access different LLM providers through Puter:

```python
import litellm
from puter_provider import setup_puter_provider

setup_puter_provider()

# Use DeepSeek via OpenRouter
response1 = litellm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello"}]
)

# Use Claude directly
response2 = litellm.completion(
    model="puter/claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello"}]
)

# Use GPT-4 via OpenAI
response3 = litellm.completion(
    model="puter/openai:gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 🎯 Supported Models

### OpenRouter Models

Access any OpenRouter model using the format: `puter/openrouter:provider/model`

```python
"puter/openrouter:deepseek/deepseek-chat"
"puter/openrouter:google/gemini-pro"
"puter/openrouter:anthropic/claude-3-opus"
"puter/openrouter:meta-llama/llama-3-70b"
"puter/openrouter:mistralai/mixtral-8x7b"
```

### Anthropic/Claude Models

Direct access to Claude models:

```python
"puter/claude-sonnet-4-5-20250929"
"puter/claude-3-opus-20240229"
"puter/claude-3-sonnet-20240229"
"puter/claude-3-haiku-20240307"
```

### OpenAI Models

Access OpenAI models:

```python
"puter/openai:gpt-4"
"puter/openai:gpt-4-turbo"
"puter/openai:gpt-3.5-turbo"
```

### Google Models

Access Google's models:

```python
"puter/google:gemini-pro"
"puter/google:gemini-pro-vision"
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PUTER_API_KEY` | Yes | Your Puter API key |
| `EXPERIMENTAL_OPENAI_BASE_LLM_HTTP_HANDLER` | Auto-set | Enables custom HTTP handler (set automatically) |
| `LITELLM_ANTHROPIC_DISABLE_URL_SUFFIX` | Optional | Disables URL suffix for Anthropic models |

### Advanced Configuration

```python
import os
import litellm
from puter_provider import PuterHTTPHandler

# Custom timeout
os.environ['LITELLM_REQUEST_TIMEOUT'] = "60"

# Enable debug logging
litellm.set_verbose = True

# Use custom HTTP handler with options
client = PuterHTTPHandler(
    api_key=os.getenv("PUTER_API_KEY"),
)

response = litellm.completion(
    client=client,
    model="openrouter/openrouter:deepseek/deepseek-chat",
    api_key="none",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=1000,
)
```

## 📖 API Reference

### `setup_puter_provider()`

Registers Puter as a custom provider in LiteLLM.

```python
from puter_provider import setup_puter_provider

puter_llm = setup_puter_provider()
```

**Returns:** `PuterLLM` instance

---

### `PuterHTTPHandler`

Synchronous HTTP handler for Puter API requests.

```python
from puter_provider import PuterHTTPHandler

handler = PuterHTTPHandler(api_key="your_api_key")
```

**Parameters:**
- `api_key` (str): Your Puter API key

**Raises:**
- `ValueError`: If API key is None or "None"

---

### `PuterAsyncHTTPHandler`

Asynchronous HTTP handler for Puter API requests.

```python
from puter_provider import PuterAsyncHTTPHandler

handler = PuterAsyncHTTPHandler(api_key="your_api_key")
```

**Parameters:**
- `api_key` (str): Your Puter API key

**Raises:**
- `ValueError`: If API key is None or "None"

---

### `PuterLLM`

Custom LLM implementation for Puter provider.

```python
from puter_provider import PuterLLM

puter_llm = PuterLLM()

# Synchronous completion
response = puter_llm.completion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello"}]
)

# Asynchronous completion
response = await puter_llm.acompletion(
    model="puter/openrouter:deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 🔧 Troubleshooting

### Common Issues

#### 1. API Key Not Found

**Error:** `ValueError: PUTER_API_KEY environment variable is required`

**Solution:**
```bash
# Make sure .env file exists and contains your API key
echo "PUTER_API_KEY=your_api_key_here" > .env

# Or export it in your shell
export PUTER_API_KEY="your_api_key_here"
```

#### 2. HTTP 403 Forbidden

**Error:** `APIError: OpenrouterException - Forbidden`

**Possible Causes:**
- Invalid or expired API key
- API key doesn't have required permissions
- Rate limit exceeded

**Solution:**
1. Verify your API key is correct
2. Check your Puter account status
3. Generate a new API key if needed
4. Ensure you're not exceeding rate limits

#### 3. Module Import Error

**Error:** `ModuleNotFoundError: No module named 'puter_provider'`

**Solution:**
```bash
# Make sure puter_provider.py is in your Python path
import sys
sys.path.insert(0, '/path/to/litellm-puter')

# Or install as a package
cd litellm-puter
pip install -e .
```

#### 4. Origin Header Missing

**Error:** Authentication fails silently

**Solution:** The provider automatically includes the `Origin` header. If you're still having issues, verify that you're not overriding headers in custom code.

### Debug Mode

Enable verbose logging to diagnose issues:

```python
import litellm

# Enable debug mode
litellm.set_verbose = True

# Now make your request
response = litellm.completion(...)
```

### Getting Help

If you're still experiencing issues:

1. Check the [Issues page](https://github.com/yourusername/litellm-puter/issues)
2. Join the [Puter Discord](https://discord.gg/puter)
3. Contact [Puter Support](https://puter.com/support)

## 📝 Examples Directory

The `examples/` directory contains complete, runnable examples:

```
examples/
├── basic_usage.py          # Simple completion request
├── http_handler_usage.py   # Direct HTTP handler usage
├── async_usage.py          # Async/concurrent requests
└── multiple_providers.py   # Using different LLM providers
```

Run any example:

```bash
cd examples
python basic_usage.py
```

## 🧪 Testing

Run the test suite:

```bash
# Basic test
python test_simple.py

# Direct handler test
python test_direct.py

# API test
python test_puter_api_direct.py
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/litellm-puter.git
cd litellm-puter

# Install in editable mode
pip install -e .

# Install development dependencies
pip install pytest black isort mypy
```

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions
- Run `black` and `isort` before committing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LiteLLM](https://github.com/BerriAI/litellm) - Universal LLM API interface
- [Puter](https://puter.com) - Cloud platform and AI API
- [OpenRouter](https://openrouter.ai) - LLM routing service

## 🔗 Links

- [Puter Documentation](https://docs.puter.com)
- [LiteLLM Documentation](https://docs.litellm.ai)
- [Puter GitHub](https://github.com/heyputer/puter)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)

## 📮 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/litellm-puter/issues)
- **Discord**: [Puter Discord](https://discord.gg/puter)
- **Email**: support@puter.com

---

Made with ❤️ by the Puter community
