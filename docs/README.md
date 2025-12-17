# LiteLLM Puter Documentation

Welcome to the LiteLLM Puter documentation! This directory contains comprehensive guides for installation, configuration, API usage, and troubleshooting.

## 📚 Documentation Structure

### 🚀 Setup & Installation

- **[DEBIAN_PACKAGE.md](setup/DEBIAN_PACKAGE.md)** - Building and installing the Debian package
- **[GATEWAY_SETUP.md](setup/GATEWAY_SETUP.md)** - Setting up the LiteLLM gateway
- **[INSTALACION_DEPENDENCIAS.md](setup/INSTALACION_DEPENDENCIAS.md)** - Installing dependencies manually

### ⚙️ Configuration

- **[PROXY_USAGE.md](configuration/PROXY_USAGE.md)** - Configuring proxy support (SOCKS5/HTTP/HTTPS)
- Configuration files location: `/etc/litellm-puter/` (Debian package)

### 📖 API Documentation

- **[RESUMEN_MODELOS.md](api/RESUMEN_MODELOS.md)** - Complete list of 488+ available models
- API endpoints: http://localhost:4000/docs (Swagger UI)

### 🔧 Troubleshooting

- **[COMPLETE_CHANGELOG_v2.2.0.md](troubleshooting/COMPLETE_CHANGELOG_v2.2.0.md)** - Complete changelog
- **[FIXES_MAX_TOKENS_OPENROUTER.md](troubleshooting/FIXES_MAX_TOKENS_OPENROUTER.md)** - OpenRouter max_tokens fixes
- **[FIXES_PARAMETER_FILTERING.md](troubleshooting/FIXES_PARAMETER_FILTERING.md)** - Parameter filtering fixes
- **[PUTER_PROVIDERS_MAX_TOKENS.md](troubleshooting/PUTER_PROVIDERS_MAX_TOKENS.md)** - Provider-specific max_tokens handling
- **[REFACTORING_AND_STREAMING.md](troubleshooting/REFACTORING_AND_STREAMING.md)** - Streaming support refactoring

## 🎯 Quick Start

### Option 1: Debian Package (Recommended for Debian 12/13)

```bash
# Install the package
sudo dpkg -i litellm-puter_2.2.0-1_all.deb
sudo apt-get install -f

# Configure API key
sudo nano /etc/litellm-puter/environment
# Add: PUTER_API_KEY=your_key_here

# Start the service
sudo systemctl enable litellm-puter
sudo systemctl start litellm-puter

# Check status
sudo systemctl status litellm-puter
```

See [DEBIAN_PACKAGE.md](setup/DEBIAN_PACKAGE.md) for detailed instructions.

### Option 2: Poetry Installation

```bash
# Install with Poetry
poetry install

# Start the gateway
poetry run litellm-puter-gateway --config config/litellm_config.yaml
```

### Option 3: Pip Installation

```bash
# Install from source
pip install -e .

# Start the gateway
litellm-puter-gateway --config config/litellm_config.yaml
```

## 📦 Available Models

The gateway provides access to **488+ AI models** from:

- **OpenAI**: 23 models (GPT-4, GPT-5, o1, o3, o4)
- **Anthropic**: 10 models (Claude 3, 4, Opus)
- **DeepSeek**: 2 models (chat, reasoner)
- **xAI**: 8 models (Grok 2, 3)
- **Google Gemini**: 6 models
- **Mistral AI**: 16 models
- **OpenRouter**: 348 models
- **Together AI**: 71 models

See [RESUMEN_MODELOS.md](api/RESUMEN_MODELOS.md) for the complete list.

## 🛠️ CLI Commands

```bash
# Start the gateway
litellm-puter-gateway --config /etc/litellm-puter/config.yaml

# List available models
litellm-puter list-models

# Generate sample configuration
litellm-puter generate-config -o my_config.yaml

# Show version
litellm-puter version
```

## 🌐 API Usage

Once the gateway is running:

```bash
# Test the gateway
curl http://localhost:4000/health

# Chat completion
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 📂 File Locations (Debian Package)

| Purpose | Location |
|---------|----------|
| Configuration | `/etc/litellm-puter/config.yaml` |
| Environment vars | `/etc/litellm-puter/environment` |
| Service file | `/lib/systemd/system/litellm-puter.service` |
| Documentation | `/usr/share/doc/litellm-puter/` |
| Logs | `journalctl -u litellm-puter` |

## 🔐 Security

The Debian package follows security best practices:

- Dedicated system user (`litellm-puter`)
- Configuration in `/etc/litellm-puter/` with restricted permissions
- API keys stored securely in environment file (mode 640)
- Systemd service with security hardening
- No unnecessary privileges

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
sudo journalctl -u litellm-puter -f

# Recent logs
sudo journalctl -u litellm-puter -n 100
```

### Service Status

```bash
sudo systemctl status litellm-puter
```

## 🤝 Contributing

Contributions are welcome! Please see the main [README.md](../README.md) for contribution guidelines.

## 📞 Support

- **GitHub Issues**: https://github.com/aorizondo/litellm-puter/issues
- **Documentation**: You're reading it! 📖
- **Examples**: See the [tests/](../tests/) directory

## 📝 License

MIT License - see [LICENSE](../LICENSE) file for details.
