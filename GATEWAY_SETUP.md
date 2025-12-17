# LiteLLM Gateway with Puter Provider

This guide explains how to run LiteLLM as a proxy/gateway server that exposes an OpenAI-compatible API using Puter as the backend provider.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install 'litellm[proxy]'
```

### 2. Configure Environment

Create a `.env` file with your Puter API key:

```bash
PUTER_API_KEY=your_puter_api_key_here
# Optional: Set a master key for authentication
LITELLM_MASTER_KEY=your_secret_key_here
```

### 3. Start the Gateway

```bash
python start_gateway.py
```

Or with custom port:

```bash
python start_gateway.py --port 8080
```

The server will start on `http://0.0.0.0:12000` by default.

## How It Works

The gateway automatically translates between OpenAI-compatible requests and Puter's format:

1. **Client sends**: Standard model name (e.g., `gpt-4o-mini`, `claude-3-5-sonnet-20241022`)
2. **Gateway converts**: To Puter format `puter/<provider>/<model>` (e.g., `puter/openai/gpt-4o-mini`)
3. **LiteLLM processes**: Uses the correct provider handler to parse Puter's response
4. **Client receives**: Standard OpenAI-compatible response

The provider is automatically determined from the model name using Puter's model cache.

## Usage

Once the gateway is running, you can use it like any OpenAI API:

### Using cURL

```bash
curl http://localhost:12000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello! How are you?"}
    ]
  }'
```

### Using Python OpenAI SDK

```python
from openai import OpenAI

# Point to your local LiteLLM gateway
client = OpenAI(
    base_url="http://localhost:12000/v1",
    api_key="anything"  # Not needed if LITELLM_MASTER_KEY not set
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Streaming Responses

```python
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Tell me a story"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

## Available Models

The gateway exposes these Puter models through the OpenAI-compatible API:

### OpenAI Models
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-3.5-turbo`

### Anthropic Models
- `claude-3-5-sonnet-20241022`
- `claude-opus-4-5`

### DeepSeek
- `deepseek-chat`

### Google
- `gemini-1.5-flash`
- `gemini-1.5-pro`

### Mistral
- `mistral-large-latest`

### xAI
- `grok-2-1212`

## Configuration

### Custom Configuration

Edit `litellm_config.yaml` to add more models or change settings:

```yaml
model_list:
  - model_name: your-model-name
    litellm_params:
      model: puter/your-model-name
      api_key: os.environ/PUTER_API_KEY
```

### Authentication

If you set `LITELLM_MASTER_KEY`, clients must include it in requests:

```python
client = OpenAI(
    base_url="http://localhost:12000/v1",
    api_key="your-master-key"
)
```

## API Documentation

Once the server is running, visit:
- `http://localhost:12000/` - Gateway info
- `http://localhost:12000/docs` - Interactive API documentation (Swagger UI)

## Advanced Usage

### Custom Port and Host

```bash
python start_gateway.py --port 8080 --host 127.0.0.1
```

### Custom Config File

```bash
python start_gateway.py --config my_config.yaml
```

### Direct LiteLLM Command

```bash
litellm --config litellm_config.yaml --port 12000 --host 0.0.0.0
```

## Features

✅ **OpenAI-Compatible API** - Drop-in replacement for OpenAI API  
✅ **Multiple Providers** - Access GPT, Claude, Gemini, and more through one API  
✅ **Streaming Support** - Real-time response streaming  
✅ **Authentication** - Optional master key for security  
✅ **Auto-Documentation** - Built-in Swagger UI  
✅ **Load Balancing** - Can configure multiple endpoints per model  
✅ **Cost Tracking** - Optional database integration for usage tracking  

## Troubleshooting

### Port Already in Use

If port 12000 is already in use, specify a different port:

```bash
python start_gateway.py --port 8080
```

### Puter API Key Not Set

Make sure your `.env` file contains:

```bash
PUTER_API_KEY=your_key_here
```

Or export it:

```bash
export PUTER_API_KEY=your_key_here
python start_gateway.py
```

### Module Not Found

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
pip install 'litellm[proxy]'
```

## Benefits of Gateway Mode

1. **OpenAI Compatibility** - Use any tool/library that supports OpenAI API
2. **Centralized Configuration** - Manage all models in one config file
3. **Easy Integration** - No code changes needed in client applications
4. **Multiple Clients** - One gateway serves multiple applications
5. **Load Balancing** - Distribute requests across multiple providers
6. **Cost Tracking** - Monitor usage across all applications

## Next Steps

- Add more models to `litellm_config.yaml`
- Set up authentication with `LITELLM_MASTER_KEY`
- Configure database for usage tracking
- Set up load balancing for high availability
- Add custom callbacks for logging/monitoring

## Support

For issues or questions:
- Puter Provider: https://github.com/aorizondo/litellm-puter
- LiteLLM Documentation: https://docs.litellm.ai/docs/proxy/quick_start
- Puter Documentation: https://docs.puter.com
