"""
Ollama client for interacting with local LLM models.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx
import ollama
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OllamaMessage(BaseModel):
    """Message for Ollama API."""
    
    role: str  # "system", "user", "assistant"
    content: str


class OllamaResponse(BaseModel):
    """Response from Ollama API."""
    
    model: str
    message: OllamaMessage
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaClient:
    """Client for interacting with Ollama models."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def health_check(self) -> bool:
        """Check if Ollama service is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            if self._client:
                response = await self._client.get("/api/tags")
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
            
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            logger.info(f"Pulling model: {model_name}")
            
            if self._client:
                response = await self._client.post(
                    "/api/pull",
                    json={"name": model_name},
                    timeout=None,  # No timeout for long operations
                )
            else:
                async with httpx.AsyncClient(timeout=None) as client:
                    response = await client.post(
                        f"{self.base_url}/api/pull",
                        json={"name": model_name},
                    )
            
            response.raise_for_status()
            
            # Stream the response to show progress
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        if "status" in data:
                            logger.info(f"Pull status: {data['status']}")
                        if data.get("done", False):
                            logger.info(f"Successfully pulled model: {model_name}")
                            return True
                    except json.JSONDecodeError:
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def generate(
        self,
        model: str,
        messages: List[OllamaMessage],
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Union[OllamaResponse, AsyncGenerator[OllamaResponse, None]]:
        """Generate response from model."""
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": [msg.dict() for msg in messages],
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            if self._client:
                response = await self._client.post(
                    "/api/chat",
                    json=payload,
                    timeout=None if stream else self.timeout,
                )
            else:
                async with httpx.AsyncClient(timeout=None if stream else self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                    )
            
            response.raise_for_status()
            
            if stream:
                return self._stream_response(response)
            else:
                data = response.json()
                return OllamaResponse(**data)
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    async def _stream_response(
        self, 
        response: httpx.Response
    ) -> AsyncGenerator[OllamaResponse, None]:
        """Stream response from Ollama."""
        try:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        yield OllamaResponse(**data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            raise
    
    async def generate_completion(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate completion for a prompt (simpler interface)."""
        
        messages = [OllamaMessage(role="user", content=prompt)]
        
        if stream:
            async def stream_generator():
                async for response in await self.generate(
                    model, messages, temperature, max_tokens, stream=True
                ):
                    if response.message.content:
                        yield response.message.content
            return stream_generator()
        else:
            response = await self.generate(
                model, messages, temperature, max_tokens, stream=False
            )
            return response.message.content
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model (synchronous)."""
        try:
            # Use the synchronous ollama client for this
            models = ollama.list()
            for model in models.get('models', []):
                if model['name'] == model_name:
                    return model
            return None
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            return None
    
    async def delete_model(self, model_name: str) -> bool:
        """Delete a model."""
        try:
            if self._client:
                response = await self._client.delete(f"/api/delete", json={"name": model_name})
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.delete(
                        f"{self.base_url}/api/delete",
                        json={"name": model_name}
                    )
            
            response.raise_for_status()
            logger.info(f"Successfully deleted model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return False


class OllamaClientSync:
    """Synchronous wrapper for Ollama client."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
    
    def health_check(self) -> bool:
        """Check if Ollama service is running."""
        try:
            self.client.list()
            return True
        except Exception:
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = self.client.list()
            return response.get('models', [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate response from model."""
        try:
            options = {"temperature": temperature}
            if max_tokens:
                options["num_predict"] = max_tokens
            
            response = self.client.chat(
                model=model,
                messages=messages,
                options=options,
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    def generate_completion(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion for a prompt."""
        messages = [{"role": "user", "content": prompt}]
        return self.generate(model, messages, temperature, max_tokens)
