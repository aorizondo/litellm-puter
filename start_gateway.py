#!/usr/bin/env python3
"""
LiteLLM Gateway with Puter Provider
====================================

This script starts an OpenAI-compatible API server using Puter as the backend provider.

Usage:
    python start_gateway.py [--port PORT] [--host HOST]

Environment Variables:
    PUTER_API_KEY: Your Puter API key (required)
    LITELLM_MASTER_KEY: Optional master key for gateway authentication
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Register Puter provider
from puter_provider import setup_puter_provider
from puter_models_cache import get_model_provider
import litellm
import os

# Register the Puter provider with LiteLLM
setup_puter_provider()

# Models configuration
AVAILABLE_MODELS = [
    # OpenAI
    "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo",
    # Claude
    "claude-3-5-sonnet-20241022", "claude-opus-4-5", "claude-3-opus-20240229",
    "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
    # DeepSeek
    "deepseek-chat", "deepseek-coder",
    # Google
    "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro",
    # Mistral
    "mistral-large-latest", "mistral-medium", "mistral-small",
    # xAI
    "grok-2-1212", "grok-beta",
    # Others
    "llama-3.1-70b", "llama-3.1-8b",
]

# Pydantic models for request/response
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int = 1677610602
    owned_by: str = "puter"

class ModelList(BaseModel):
    object: str = "list"
    data: List[Model]

# Create FastAPI app
app = FastAPI(
    title="LiteLLM Gateway with Puter",
    description="OpenAI-compatible API using Puter as backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware
def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify API key if LITELLM_MASTER_KEY is set"""
    master_key = os.getenv("LITELLM_MASTER_KEY")
    if master_key:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        # Support both "Bearer token" and "token" formats
        token = authorization.replace("Bearer ", "")
        if token != master_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/")
async def root():
    """Gateway information"""
    return {
        "service": "LiteLLM Gateway with Puter Provider",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health"
        },
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/v1/models", response_model=ModelList)
async def list_models(authorization: Optional[str] = Header(None)):
    """List available models"""
    verify_auth(authorization)
    
    models = [
        Model(id=model_id, owned_by="puter")
        for model_id in AVAILABLE_MODELS
    ]
    
    return ModelList(data=models)

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """Handle chat completion requests"""
    verify_auth(authorization)
    
    try:
        # Convert Pydantic models to dicts
        messages = [msg.model_dump() for msg in request.messages]
        
        # Get the API key for provider lookup
        puter_token = os.getenv("PUTER_TOKEN") or os.getenv("PUTER_API_KEY")
        
        # Determine the provider for this model
        # This is crucial: Puter requires format "puter/<provider>/<model>"
        # where provider is determined by the driver (e.g., openai, anthropic, deepseek)
        provider = get_model_provider(request.model, token=puter_token)
        
        # Construct the full model name in Puter format
        # Format: puter/<provider>/<model>
        # Examples:
        #   - gpt-4o -> puter/openai/gpt-4o
        #   - claude-3-5-sonnet-20241022 -> puter/anthropic/claude-3-5-sonnet-20241022
        #   - deepseek-chat -> puter/deepseek/deepseek-chat
        #   - openrouter:deepseek/deepseek-chat -> puter/openrouter/openrouter:deepseek/deepseek-chat
        puter_model = f"puter/{provider}/{request.model}"
        
        # Prepare kwargs for litellm.acompletion()
        kwargs = {
            "model": puter_model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": request.stream,
        }
        
        # Add optional parameters if provided
        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens
        if request.stop:
            kwargs["stop"] = request.stop
        if request.presence_penalty:
            kwargs["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty:
            kwargs["frequency_penalty"] = request.frequency_penalty
        if request.user:
            kwargs["user"] = request.user
        
        # Handle streaming
        if request.stream:
            async def generate():
                try:
                    response = await litellm.acompletion(**kwargs)
                    async for chunk in response:
                        yield f"data: {chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    error_data = {
                        "error": {
                            "message": str(e),
                            "type": "puter_error",
                            "code": "internal_error"
                        }
                    }
                    yield f"data: {error_data}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        
        # Non-streaming response
        response = await litellm.acompletion(**kwargs)
        return JSONResponse(content=response.model_dump())
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "puter_error",
                    "code": "internal_error"
                }
            }
        )

def main():
    parser = argparse.ArgumentParser(description='Start LiteLLM Gateway with Puter provider')
    parser.add_argument('--port', type=int, default=12000, help='Port to run the server on (default: 12000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    # Verify Puter API key is set
    if not os.getenv('PUTER_API_KEY'):
        print("❌ Error: PUTER_API_KEY environment variable is required")
        print("   Get your API key from: https://puter.com/")
        sys.exit(1)

    print("=" * 70)
    print("🚀 Starting LiteLLM Gateway with Puter Provider")
    print("=" * 70)
    print(f"🌐 Server: http://{args.host}:{args.port}")
    print(f"🔑 Puter API Key: {'✅ Set' if os.getenv('PUTER_API_KEY') else '❌ Not Set'}")
    print(f"🔐 Master Key: {'✅ Set' if os.getenv('LITELLM_MASTER_KEY') else '⚠️  Not Set (optional)'}")
    print("=" * 70)
    print("\n📚 API Documentation available at:")
    print(f"   http://{args.host}:{args.port}/")
    print(f"   http://{args.host}:{args.port}/docs")
    print("\n💡 Example usage:")
    print("   curl http://localhost:12000/v1/chat/completions \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print('       "model": "gpt-4o-mini",')
    print('       "messages": [{"role": "user", "content": "Hello!"}]')
    print("     }'")
    print("\n" + "=" * 70)
    print("⏳ Starting server...\n")

    # Start the server
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == '__main__':
    main()
