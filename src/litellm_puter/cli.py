#!/usr/bin/env python3
"""
Command-line interface for LiteLLM Puter
"""

import click
import sys
from pathlib import Path


@click.group()
@click.version_option(version="2.2.0", prog_name="litellm-puter")
def main():
    """LiteLLM Puter - Unified AI Gateway

    Access 488+ AI models through Puter's unified API.
    """
    pass


@main.command()
@click.option(
    '--config',
    '-c',
    default='/etc/litellm-puter/config.yaml',
    help='Path to configuration file',
    type=click.Path(exists=True)
)
@click.option(
    '--host',
    default='0.0.0.0',
    help='Host to bind to',
    show_default=True
)
@click.option(
    '--port',
    default=4000,
    help='Port to bind to',
    show_default=True,
    type=int
)
@click.option(
    '--reload',
    is_flag=True,
    help='Enable auto-reload for development'
)
def start(config, host, port, reload):
    """Start the LiteLLM Puter gateway"""
    from .gateway import start_gateway
    
    click.echo(f"🚀 Starting LiteLLM Puter Gateway...")
    click.echo(f"📝 Config: {config}")
    click.echo(f"🌐 Server: http://{host}:{port}")
    
    try:
        start_gateway(config_path=config, host=host, port=port, reload=reload)
    except KeyboardInterrupt:
        click.echo("\n👋 Gateway stopped")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    '--format',
    '-f',
    type=click.Choice(['table', 'json', 'yaml']),
    default='table',
    help='Output format'
)
def list_models(format):
    """List all available models"""
    from .models_cache import get_all_model_drivers
    import os
    import json
    import yaml
    
    api_key = os.getenv('PUTER_API_KEY')
    if not api_key:
        click.echo("❌ PUTER_API_KEY not set", err=True)
        sys.exit(1)
    
    click.echo("📡 Fetching models from Puter API...")
    models = get_all_model_drivers(api_key)
    
    if format == 'json':
        click.echo(json.dumps(models, indent=2))
    elif format == 'yaml':
        click.echo(yaml.dump(models, default_flow_style=False))
    else:
        # Table format
        click.echo(f"\n✅ Found {len(models)} models:\n")
        click.echo(f"{'Model ID':<50} {'Driver':<20}")
        click.echo("=" * 70)
        for model_id, driver in sorted(models.items()):
            click.echo(f"{model_id:<50} {driver:<20}")


@main.command()
def version():
    """Show version information"""
    from . import __version__
    click.echo(f"LiteLLM Puter v{__version__}")


@main.command()
@click.option(
    '--output',
    '-o',
    default='litellm_config.yaml',
    help='Output file path',
    type=click.Path()
)
def generate_config(output):
    """Generate a sample configuration file"""
    import yaml
    
    config = {
        "model_list": [
            {
                "model_name": "gpt-4o",
                "litellm_params": {
                    "model": "puter/openai/gpt-4o",
                    "api_key": "os.environ/PUTER_API_KEY"
                }
            },
            {
                "model_name": "claude-3-5-sonnet",
                "litellm_params": {
                    "model": "puter/anthropic/claude-3-5-sonnet-20241022",
                    "api_key": "os.environ/PUTER_API_KEY"
                }
            },
            {
                "model_name": "deepseek-chat",
                "litellm_params": {
                    "model": "puter/deepseek/deepseek-chat",
                    "api_key": "os.environ/PUTER_API_KEY"
                }
            },
        ]
    }
    
    with open(output, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"✅ Configuration file generated: {output}")


if __name__ == '__main__':
    main()
