"""
LiteLLM Puter Provider

A LiteLLM integration for Puter AI, providing access to 488+ AI models
through a unified gateway interface.
"""

__version__ = "2.2.0"
__author__ = "aorizondo"

from .provider import puter_llm, PuterLLM

__all__ = ["puter_llm", "PuterLLM", "__version__"]
