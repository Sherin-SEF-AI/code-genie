"""
Model management system for intelligent model selection and fallback.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from .ollama_client import OllamaClient, OllamaMessage

logger = logging.getLogger(__name__)


class ModelInfo:
    """Information about a model."""
    
    def __init__(
        self,
        name: str,
        size: Optional[int] = None,
        capabilities: Optional[List[str]] = None,
        performance_score: float = 1.0,
        last_used: Optional[float] = None,
    ):
        self.name = name
        self.size = size
        self.capabilities = capabilities or []
        self.performance_score = performance_score
        self.last_used = last_used
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "capabilities": self.capabilities,
            "performance_score": self.performance_score,
            "last_used": self.last_used,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            size=data.get("size"),
            capabilities=data.get("capabilities", []),
            performance_score=data.get("performance_score", 1.0),
            last_used=data.get("last_used"),
        )


class ModelManager:
    """Manages Ollama models with intelligent selection and fallback."""
    
    def __init__(self, config):
        self.config = config
        self.client = OllamaClient()
        self.models: Dict[str, ModelInfo] = {}
        self.model_capabilities = {
            "code_generation": ["codellama", "deepseek-coder", "starcoder"],
            "reasoning": ["llama3.1", "mistral", "qwen"],
            "debugging": ["llama3.1", "codellama", "deepseek-coder"],
            "planning": ["llama3.1", "mistral", "qwen"],
            "documentation": ["llama3.1", "mistral"],
            "testing": ["codellama", "deepseek-coder"],
        }
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the model manager."""
        if self._initialized:
            return
        
        logger.info("Initializing model manager...")
        
        # Check Ollama health
        if not await self.client.health_check():
            raise RuntimeError("Ollama service is not running. Please start it with 'ollama serve'")
        
        # Load available models
        await self._load_available_models()
        
        # Ensure we have at least one model
        if not self.models:
            logger.warning("No models found. Installing default models...")
            await self._install_default_models()
        
        self._initialized = True
        logger.info(f"Model manager initialized with {len(self.models)} models")
    
    async def _load_available_models(self) -> None:
        """Load available models from Ollama."""
        try:
            models_data = await self.client.list_models()
            
            for model_data in models_data:
                name = model_data.get('name', '')
                size = model_data.get('size')
                
                # Determine capabilities based on model name
                capabilities = self._determine_capabilities(name)
                
                model_info = ModelInfo(
                    name=name,
                    size=size,
                    capabilities=capabilities,
                )
                
                self.models[name] = model_info
                logger.debug(f"Loaded model: {name} with capabilities: {capabilities}")
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def _determine_capabilities(self, model_name: str) -> List[str]:
        """Determine model capabilities based on name."""
        capabilities = []
        model_lower = model_name.lower()
        
        for capability, keywords in self.model_capabilities.items():
            if any(keyword in model_lower for keyword in keywords):
                capabilities.append(capability)
        
        # All models can do basic tasks
        if not capabilities:
            capabilities = ["code_generation", "reasoning"]
        
        return capabilities
    
    async def _install_default_models(self) -> None:
        """Install default models if none are available."""
        default_models = [
            "llama3.1:8b",
            "codellama:7b",
        ]
        
        for model_name in default_models:
            try:
                logger.info(f"Installing default model: {model_name}")
                success = await self.client.pull_model(model_name)
                if success:
                    # Reload models after installation
                    await self._load_available_models()
                    break
            except Exception as e:
                logger.error(f"Failed to install model {model_name}: {e}")
                continue
    
    async def get_best_model(
        self,
        task_type: str,
        complexity: str = "medium",
        preferred_model: Optional[str] = None,
    ) -> str:
        """Get the best model for a specific task."""
        await self.initialize()
        
        # If preferred model is specified and available, use it
        if preferred_model and preferred_model in self.models:
            return preferred_model
        
        # Get models capable of the task
        capable_models = [
            name for name, info in self.models.items()
            if task_type in info.capabilities
        ]
        
        if not capable_models:
            # Fallback to any available model
            capable_models = list(self.models.keys())
        
        if not capable_models:
            raise RuntimeError("No models available")
        
        # Select based on complexity and performance
        if complexity == "simple":
            # Prefer smaller, faster models
            best_model = min(
                capable_models,
                key=lambda name: self.models[name].size or float('inf')
            )
        elif complexity == "complex":
            # Prefer larger, more capable models
            best_model = max(
                capable_models,
                key=lambda name: self.models[name].performance_score
            )
        else:
            # Medium complexity - balance size and performance
            best_model = max(
                capable_models,
                key=lambda name: (
                    self.models[name].performance_score,
                    -(self.models[name].size or 0)  # Prefer smaller size
                )
            )
        
        logger.debug(f"Selected model {best_model} for {task_type} task (complexity: {complexity})")
        return best_model
    
    async def generate_with_fallback(
        self,
        messages: List[OllamaMessage],
        task_type: str = "code_generation",
        complexity: str = "medium",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Any:
        """Generate response with automatic fallback to other models."""
        await self.initialize()
        
        # Get primary model
        primary_model = await self.get_best_model(task_type, complexity)
        
        # Try primary model first
        try:
            logger.debug(f"Trying primary model: {primary_model}")
            return await self.client.generate(
                model=primary_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
        except Exception as e:
            logger.warning(f"Primary model {primary_model} failed: {e}")
        
        # Try fallback models
        fallback_models = [
            model for model in self.config.models.fallback
            if model in self.models and model != primary_model
        ]
        
        for fallback_model in fallback_models:
            try:
                logger.debug(f"Trying fallback model: {fallback_model}")
                return await self.client.generate(
                    model=fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )
            except Exception as e:
                logger.warning(f"Fallback model {fallback_model} failed: {e}")
                continue
        
        # If all models fail, raise the last exception
        raise RuntimeError("All models failed to generate response")
    
    async def generate_completion_with_fallback(
        self,
        prompt: str,
        task_type: str = "code_generation",
        complexity: str = "medium",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Any:
        """Generate completion with automatic fallback."""
        messages = [OllamaMessage(role="user", content=prompt)]
        return await self.generate_with_fallback(
            messages=messages,
            task_type=task_type,
            complexity=complexity,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
    
    def update_model_performance(self, model_name: str, success: bool, response_time: float) -> None:
        """Update model performance metrics."""
        if model_name not in self.models:
            return
        
        model_info = self.models[model_name]
        
        # Update performance score based on success and response time
        if success:
            # Reward successful responses, penalize slow ones
            time_factor = max(0.1, 1.0 - (response_time / 30.0))  # 30s baseline
            model_info.performance_score = min(2.0, model_info.performance_score + 0.1 * time_factor)
        else:
            # Penalize failed responses
            model_info.performance_score = max(0.1, model_info.performance_score - 0.2)
        
        # Update last used timestamp
        import time
        model_info.last_used = time.time()
        
        logger.debug(f"Updated performance for {model_name}: {model_info.performance_score}")
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about available models."""
        stats = {
            "total_models": len(self.models),
            "models": {},
            "capabilities": {},
        }
        
        for name, info in self.models.items():
            stats["models"][name] = info.to_dict()
            
            for capability in info.capabilities:
                if capability not in stats["capabilities"]:
                    stats["capabilities"][capability] = []
                stats["capabilities"][capability].append(name)
        
        return stats
    
    async def ensure_model_available(self, model_name: str) -> bool:
        """Ensure a specific model is available, install if needed."""
        await self.initialize()
        
        if model_name in self.models:
            return True
        
        try:
            logger.info(f"Model {model_name} not found, attempting to install...")
            success = await self.client.pull_model(model_name)
            if success:
                await self._load_available_models()
                return model_name in self.models
        except Exception as e:
            logger.error(f"Failed to install model {model_name}: {e}")
        
        return False
