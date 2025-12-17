# Building and Installing the Debian Package

## Prerequisites

### On Debian 12/13 (Bookworm/Trixie)

```bash
sudo apt update
sudo apt install -y \
    debhelper \
    dh-python \
    python3-all \
    python3-setuptools \
    python3-pip \
    python3-poetry \
    build-essential \
    devscripts \
    fakeroot
```

## Building the Package

### 1. Clone the Repository

```bash
git clone https://github.com/aorizondo/litellm-puter.git
cd litellm-puter
git checkout develop
```

### 2. Install Poetry (if not already installed)

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Build the Debian Package

```bash
# Build the package
dpkg-buildpackage -us -uc -b

# The .deb file will be created in the parent directory
cd ..
ls -lh litellm-puter_*.deb
```

## Installing the Package

### Install

```bash
sudo dpkg -i litellm-puter_2.2.0-1_all.deb

# Install dependencies if needed
sudo apt-get install -f
```

### Configure

1. **Edit the environment file and add your Puter API key:**

```bash
sudo nano /etc/litellm-puter/environment
```

Add your API key:

```bash
PUTER_API_KEY=your_puter_api_key_here
```

2. **Optional: Customize the configuration:**

```bash
sudo nano /etc/litellm-puter/config.yaml
```

3. **Optional: Change server settings:**

The service runs on `0.0.0.0:4000` by default. To change:

```bash
sudo nano /etc/litellm-puter/environment
```

Add/modify:

```bash
HOST=127.0.0.1  # localhost only
PORT=8080       # custom port
```

## Managing the Service

### Start the Service

```bash
sudo systemctl start litellm-puter
```

### Enable Auto-start on Boot

```bash
sudo systemctl enable litellm-puter
```

### Check Status

```bash
sudo systemctl status litellm-puter
```

### View Logs

```bash
# Follow logs in real-time
sudo journalctl -u litellm-puter -f

# View recent logs
sudo journalctl -u litellm-puter -n 100

# View logs since boot
sudo journalctl -u litellm-puter -b
```

### Restart Service

```bash
sudo systemctl restart litellm-puter
```

### Stop Service

```bash
sudo systemctl stop litellm-puter
```

## Testing the Gateway

Once the service is running:

```bash
# Test the gateway
curl http://localhost:4000/health

# List available models
curl http://localhost:4000/models

# Test a completion
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Web Interface

The gateway provides a Swagger UI documentation interface:

```
http://localhost:4000/docs
```

## File Locations

| Purpose | Location |
|---------|----------|
| Configuration | `/etc/litellm-puter/config.yaml` |
| Environment | `/etc/litellm-puter/environment` |
| Service file | `/lib/systemd/system/litellm-puter.service` |
| Documentation | `/usr/share/doc/litellm-puter/` |
| Data directory | `/var/lib/litellm-puter/` |
| Log directory | `/var/log/litellm-puter/` |
| Python package | `/usr/lib/python3/dist-packages/litellm_puter/` |

## Uninstalling

### Remove Package (keep configuration)

```bash
sudo apt remove litellm-puter
```

### Purge Package (remove everything including configuration)

```bash
sudo apt purge litellm-puter

# Manual cleanup if needed
sudo rm -rf /etc/litellm-puter
```

## Troubleshooting

### Service Won't Start

1. Check if API key is set:

```bash
sudo cat /etc/litellm-puter/environment | grep PUTER_API_KEY
```

2. Check logs for errors:

```bash
sudo journalctl -u litellm-puter -n 50
```

3. Test configuration manually:

```bash
sudo -u litellm-puter litellm-puter-gateway \
    --config /etc/litellm-puter/config.yaml
```

### Permission Issues

```bash
# Fix permissions
sudo chown -R root:litellm-puter /etc/litellm-puter
sudo chmod 750 /etc/litellm-puter
sudo chmod 640 /etc/litellm-puter/environment
sudo chmod 640 /etc/litellm-puter/config.yaml

sudo chown -R litellm-puter:litellm-puter /var/lib/litellm-puter
sudo chown -R litellm-puter:litellm-puter /var/log/litellm-puter
```

### Port Already in Use

If port 4000 is already in use, change it:

```bash
sudo nano /etc/litellm-puter/environment
```

Set a different port:

```bash
PORT=8080
```

Then restart:

```bash
sudo systemctl restart litellm-puter
```

## Security Considerations

1. **API Key Protection**: The environment file is readable only by root and the litellm-puter group.

2. **Service User**: The service runs as a dedicated `litellm-puter` user with minimal privileges.

3. **Firewall**: If exposing externally, configure firewall:

```bash
# Allow only from specific IP
sudo ufw allow from 192.168.1.0/24 to any port 4000

# Or allow from anywhere (not recommended)
sudo ufw allow 4000
```

4. **Reverse Proxy**: For production, use nginx or apache as a reverse proxy with SSL:

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
    }
}
```

## Upgrading

```bash
# Download new .deb file
wget https://github.com/aorizondo/litellm-puter/releases/download/v2.2.0/litellm-puter_2.2.0-1_all.deb

# Install (will upgrade existing installation)
sudo dpkg -i litellm-puter_2.2.0-1_all.deb

# Restart service
sudo systemctl restart litellm-puter
```

## Building from Source with Custom Changes

```bash
# Make your changes
cd litellm-puter
# ... edit files ...

# Update version in pyproject.toml and debian/changelog

# Build
dpkg-buildpackage -us -uc -b

# Install
cd ..
sudo dpkg -i litellm-puter_*.deb
```

## Support

- **GitHub Issues**: https://github.com/aorizondo/litellm-puter/issues
- **Documentation**: `/usr/share/doc/litellm-puter/`
- **Logs**: `sudo journalctl -u litellm-puter -f`
