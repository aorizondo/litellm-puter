# 🚀 LiteLLM Puter - Unified AI Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/packaging-poetry-blue)](https://python-poetry.org/)
[![Debian](https://img.shields.io/badge/debian-12%20%7C%2013-red)](https://www.debian.org/)

A professional, production-ready integration between [LiteLLM](https://github.com/BerriAI/litellm) and [Puter's AI API](https://puter.com), providing unified access to **488+ AI models** from OpenAI, Anthropic, DeepSeek, xAI, Google, Mistral, and more through a single gateway.

## ✨ Features

- 🎯 **488+ AI Models**: Access models from 8+ providers through one API
- 📦 **Easy Deployment**: Debian package with systemd service included  
- 🔄 **Production Ready**: Async support, streaming, error handling
- 🔐 **Secure**: FHS-compliant configuration, dedicated system user
- 🛠️ **CLI Tools**: Built-in commands for management and configuration
- 🌐 **OpenAI Compatible**: Drop-in replacement for OpenAI API
- 📊 **Monitoring**: Systemd integration with journald logging
- 🔌 **Proxy Support**: Optional SOCKS5/HTTP/HTTPS proxy support

## 📦 Supported Models

### Priority Providers (65 models configured)

| Provider | Models | Examples |
|----------|---------|----------|
| **OpenAI** | 23 | gpt-4o, gpt-5, o1, o3, o4 |
| **Anthropic** | 10 | claude-3-5-sonnet, claude-4, claude-opus |
| **DeepSeek** | 2 | deepseek-chat, deepseek-reasoner |
| **xAI** | 8 | grok-2, grok-3, grok-beta |
| **Google Gemini** | 6 | gemini-2.5-pro, gemini-3-preview |
| **Mistral AI** | 16 | mistral-large, codestral, ministral |

### Additional Providers (423+ models)

- **OpenRouter**: 348 models from various providers
- **Together AI**: 71 models

**Total: 488+ models available!** 🎉

See [docs/api/RESUMEN_MODELOS.md](docs/api/RESUMEN_MODELOS.md) for the complete list.

## 🚀 Quick Start

### Option 1: Debian Package (Recommended)

Perfect for Debian 12/13 servers:

```bash
# Install the package
sudo dpkg -i litellm-puter_2.2.0-1_all.deb
sudo apt-get install -f

# Configure your API key
sudo nano /etc/litellm-puter/environment
# Add: PUTER_API_KEY=your_key_here

# Start the service
sudo systemctl enable litellm-puter
sudo systemctl start litellm-puter

# Check status
sudo systemctl status litellm-puter

# Access the gateway
curl http://localhost:4000/health
```

📚 See [docs/setup/DEBIAN_PACKAGE.md](docs/setup/DEBIAN_PACKAGE.md) for detailed instructions.

### Option 2: Poetry (Development)

```bash
# Install dependencies
poetry install

# Set up environment
cp config/.env.example .env
nano .env  # Add your PUTER_API_KEY

# Start the gateway
poetry run litellm-puter-gateway --config config/litellm_config.yaml
```

### Option 3: Pip Install

```bash
# Install from source
pip install -e .

# Configure environment
export PUTER_API_KEY=your_key_here

# Start the gateway
litellm-puter-gateway --config config/litellm_config.yaml
```

## 💻 Usage Examples

### Python SDK

```python
import litellm
from litellm_puter import puter_llm

# Register the provider
litellm.custom_provider_map = [
    {"provider": "puter", "custom_handler": puter_llm}
]

# Use any model
response = litellm.completion(
    model="puter/openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### REST API

Once the gateway is running:

```bash
# Chat completion
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Streaming
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true
  }'
```

### OpenAI Python Client

```python
from openai import OpenAI

# Point to your gateway
client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="dummy"  # Not used, but required by SDK
)

# Use any configured model
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## 🛠️ CLI Commands

```bash
# Start the gateway
litellm-puter-gateway --config /etc/litellm-puter/config.yaml

# List available models
litellm-puter list-models

# List models in JSON format
litellm-puter list-models --format json

# Generate sample configuration
litellm-puter generate-config -o my_config.yaml

# Show version
litellm-puter version

# Get help
litellm-puter --help
```

## 📂 Project Structure

```
litellm-puter/
├── src/litellm_puter/       # Python package source
│   ├── __init__.py          # Package initialization
│   ├── provider.py          # Puter LLM provider implementation
│   ├── models_cache.py      # Model caching and discovery
│   ├── cli.py               # Command-line interface
│   └── gateway.py           # Gateway server module
├── config/                  # Configuration files
│   ├── litellm_config.yaml  # Model configuration (65 models)
│   └── .env.example         # Environment variables template
├── docs/                    # Documentation
│   ├── setup/               # Installation guides
│   ├── configuration/       # Configuration guides
│   ├── api/                 # API documentation
│   └── troubleshooting/     # Troubleshooting guides
├── debian/                  # Debian package files
│   ├── control              # Package metadata
│   ├── rules                # Build rules
│   ├── postinst             # Post-installation script
│   ├── prerm                # Pre-removal script
│   ├── postrm               # Post-removal script
│   └── litellm-puter.service  # Systemd service
├── tests/                   # Test suite
├── pyproject.toml           # Poetry configuration
└── README.md                # This file
```

## 📚 Documentation

- **[Debian Package Guide](docs/setup/DEBIAN_PACKAGE.md)** - Building and installing the .deb package
- **[Gateway Setup](docs/setup/GATEWAY_SETUP.md)** - Setting up the gateway server
- **[Dependencies](docs/setup/INSTALACION_DEPENDENCIAS.md)** - Manual dependency installation
- **[Proxy Configuration](docs/configuration/PROXY_USAGE.md)** - Configuring proxy support
- **[Model List](docs/api/RESUMEN_MODELOS.md)** - Complete list of 488+ models
- **[Changelog](docs/troubleshooting/COMPLETE_CHANGELOG_v2.2.0.md)** - Complete changelog

## 🔧 Configuration

### Debian Package

Configuration files are in `/etc/litellm-puter/`:

- **`environment`** - API keys and environment variables
- **`config.yaml`** - Model configuration

```bash
# Edit environment
sudo nano /etc/litellm-puter/environment

# Edit model configuration  
sudo nano /etc/litellm-puter/config.yaml

# Restart after changes
sudo systemctl restart litellm-puter
```

### Development/Standalone

Use `.env` file in project root:

```bash
cp config/.env.example .env
nano .env
```

Required variables:

```bash
PUTER_API_KEY=your_puter_api_key_here
```

Optional variables:

```bash
USE_PROXY=false
SOCKS5_PROXY=socks5://proxy.server:port
```

## 🔐 Security

### Debian Package Security

- Dedicated system user (`litellm-puter`)
- Configuration in `/etc/litellm-puter/` with restricted permissions (750)
- API keys stored in environment file with mode 640
- Systemd service with security hardening:
  - `NoNewPrivileges=true`
  - `PrivateTmp=true`
  - `ProtectSystem=strict`
  - `ProtectHome=true`

### Production Recommendations

1. **Use a reverse proxy** (nginx/apache) with SSL
2. **Firewall rules** to restrict access
3. **API authentication** for external access
4. **Rate limiting** to prevent abuse
5. **Monitor logs** regularly

Example nginx configuration:

```nginx
server {
    listen 443 ssl;
    server_name ai-gateway.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring

### Systemd Service

```bash
# Service status
sudo systemctl status litellm-puter

# Real-time logs
sudo journalctl -u litellm-puter -f

# Recent logs
sudo journalctl -u litellm-puter -n 100

# Logs since last boot
sudo journalctl -u litellm-puter -b
```

### Health Check

```bash
curl http://localhost:4000/health
```

### Metrics

The gateway exposes metrics at:

- `/metrics` - Prometheus-compatible metrics
- `/health` - Health check endpoint

## 🧪 Testing

```bash
# Run tests with Poetry
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=litellm_puter --cov-report=html

# Run specific test
poetry run pytest tests/test_simple.py -v
```

## 🏗️ Building

### Build Debian Package

```bash
# Install build dependencies
sudo apt install -y debhelper dh-python python3-all python3-setuptools build-essential

# Build the package
dpkg-buildpackage -us -uc -b

# Package will be in parent directory
cd ..
ls -lh litellm-puter_*.deb
```

### Build Python Wheel

```bash
# Build with Poetry
poetry build

# Outputs to dist/
ls -lh dist/
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/aorizondo/litellm-puter.git
cd litellm-puter

# Install with dev dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black src/

# Lint
poetry run ruff check src/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LiteLLM](https://github.com/BerriAI/litellm) - Universal LLM API interface
- [Puter](https://puter.com) - AI API aggregation platform
- All the amazing AI providers making their models accessible

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/aorizondo/litellm-puter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aorizondo/litellm-puter/discussions)

## 🗺️ Roadmap

- [x] Poetry-based package management
- [x] Debian package with systemd service
- [x] 488+ models support
- [x] Proxy support (SOCKS5/HTTP/HTTPS)
- [x] Comprehensive CLI tools
- [x] Production-ready documentation
- [ ] Docker image
- [ ] Kubernetes Helm chart
- [ ] Monitoring dashboard
- [ ] Rate limiting per model
- [ ] Cost tracking and analytics

---

**Made with ❤️ by [aorizondo](https://github.com/aorizondo)**

**⭐ Star this project if you find it useful!**
