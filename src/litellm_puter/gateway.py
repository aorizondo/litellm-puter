#!/usr/bin/env python3
"""
Gateway module for starting the LiteLLM proxy server
"""

import os
import sys
import uvicorn
import litellm
from pathlib import Path
from typing import Optional


def start_gateway(
    config_path: str = "/etc/litellm-puter/config.yaml",
    host: str = "0.0.0.0",
    port: int = 4000,
    reload: bool = False
):
    """
    Start the LiteLLM gateway server
    
    Args:
        config_path: Path to the configuration YAML file
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    # Register the Puter provider
    from .provider import puter_llm
    
    litellm.custom_provider_map = [
        {"provider": "puter", "custom_handler": puter_llm}
    ]
    
    # Check if config file exists
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"⚠️  Config file not found: {config_path}")
        print(f"   Creating default config...")
        
        # Create directory if it doesn't exist
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy default config
        import shutil
        default_config = Path(__file__).parent.parent.parent / "config" / "litellm_config.yaml"
        if default_config.exists():
            shutil.copy(default_config, config_file)
            print(f"✅ Default config created at: {config_path}")
        else:
            print(f"❌ Default config not found at: {default_config}")
            sys.exit(1)
    
    # Start the proxy server
    print(f"\n🚀 Starting LiteLLM Proxy Server...")
    print(f"📝 Config: {config_path}")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"\n⏳ Loading models...")
    
    # Use LiteLLM's built-in proxy server
    os.environ['CONFIG_FILE'] = str(config_path)
    
    try:
        # Start uvicorn server with LiteLLM
        from litellm.proxy.proxy_server import app, initialize
        
        # Initialize the proxy
        initialize()
        
        # Run the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        print(f"\n❌ Error starting gateway: {e}")
        raise


def start():
    """Entry point for litellm-puter-gateway command"""
    import click
    
    @click.command()
    @click.option('--config', '-c', default='/etc/litellm-puter/config.yaml')
    @click.option('--host', default='0.0.0.0')
    @click.option('--port', default=4000, type=int)
    @click.option('--reload', is_flag=True)
    def run(config, host, port, reload):
        start_gateway(config, host, port, reload)
    
    run()


if __name__ == "__main__":
    start()
