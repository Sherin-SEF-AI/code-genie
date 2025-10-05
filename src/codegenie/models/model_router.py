"""
Intelligent model routing based on task type and complexity.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .model_manager import ModelManager
from .ollama_client import OllamaMessage

logger = logging.getLogger(__name__)


class TaskComplexity:
    """Task complexity levels."""
    
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class TaskType:
    """Task type categories."""
    
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    DEBUGGING = "debugging"
    PLANNING = "planning"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    OPTIMIZATION = "optimization"
    ANALYSIS = "analysis"


class ModelRouter:
    """Routes tasks to appropriate models based on type and complexity."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        
        # Task complexity heuristics
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "simple", "basic", "easy", "quick", "small", "minor",
                "add comment", "format", "rename", "move file"
            ],
            TaskComplexity.COMPLEX: [
                "complex", "advanced", "difficult", "major", "architecture",
                "refactor", "optimize", "debug", "analyze", "design",
                "implement", "create", "build", "develop"
            ]
        }
        
        # Task type detection patterns
        self.task_patterns = {
            TaskType.CODE_GENERATION: [
                "write", "create", "implement", "generate", "build", "develop",
                "add function", "add class", "add method", "new feature"
            ],
            TaskType.DEBUGGING: [
                "debug", "fix", "error", "bug", "issue", "problem", "broken",
                "not working", "failing", "exception", "crash"
            ],
            TaskType.REASONING: [
                "analyze", "understand", "explain", "why", "how", "what",
                "reasoning", "logic", "decision", "strategy"
            ],
            TaskType.PLANNING: [
                "plan", "design", "architecture", "structure", "organize",
                "break down", "steps", "approach", "strategy"
            ],
            TaskType.DOCUMENTATION: [
                "document", "readme", "comment", "explain", "describe",
                "docstring", "api docs", "tutorial", "guide"
            ],
            TaskType.TESTING: [
                "test", "testing", "unit test", "integration test",
                "test case", "coverage", "pytest", "unittest"
            ],
            TaskType.REFACTORING: [
                "refactor", "restructure", "reorganize", "clean up",
                "improve", "modernize", "update", "migrate"
            ],
            TaskType.OPTIMIZATION: [
                "optimize", "performance", "speed", "memory", "efficiency",
                "faster", "better", "improve performance"
            ],
            TaskType.ANALYSIS: [
                "analyze", "review", "inspect", "examine", "evaluate",
                "assess", "audit", "check", "scan"
            ]
        }
    
    def analyze_task(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """Analyze user input to determine task type and complexity."""
        
        # Normalize input
        input_lower = user_input.lower()
        
        # Determine task type
        task_type = self._detect_task_type(input_lower, context)
        
        # Determine complexity
        complexity = self._detect_complexity(input_lower, context)
        
        logger.debug(f"Task analysis: type={task_type}, complexity={complexity}")
        return task_type, complexity
    
    def _detect_task_type(self, input_lower: str, context: Optional[Dict[str, Any]]) -> str:
        """Detect the type of task from user input."""
        
        # Check for explicit task type indicators
        for task_type, patterns in self.task_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                return task_type
        
        # Use context clues if available
        if context:
            # Check file types being worked with
            file_extensions = context.get("file_extensions", [])
            if any(ext in [".md", ".rst", ".txt"] for ext in file_extensions):
                return TaskType.DOCUMENTATION
            
            # Check if we're in a test directory
            if context.get("in_test_directory", False):
                return TaskType.TESTING
            
            # Check if we're working with configuration files
            config_files = [".yaml", ".yml", ".json", ".toml", ".ini"]
            if any(ext in file_extensions for ext in config_files):
                return TaskType.ANALYSIS
        
        # Default to code generation for most tasks
        return TaskType.CODE_GENERATION
    
    def _detect_complexity(self, input_lower: str, context: Optional[Dict[str, Any]]) -> str:
        """Detect the complexity of the task."""
        
        # Check for complexity indicators
        for complexity, indicators in self.complexity_indicators.items():
            if any(indicator in input_lower for indicator in indicators):
                return complexity
        
        # Use context clues
        if context:
            # Check file count
            file_count = context.get("file_count", 0)
            if file_count > 10:
                return TaskComplexity.COMPLEX
            elif file_count > 3:
                return TaskComplexity.MEDIUM
            
            # Check if multiple languages involved
            languages = context.get("languages", [])
            if len(languages) > 2:
                return TaskComplexity.COMPLEX
            
            # Check project size
            project_size = context.get("project_size", "small")
            if project_size == "large":
                return TaskComplexity.COMPLEX
            elif project_size == "medium":
                return TaskComplexity.MEDIUM
        
        # Default to medium complexity
        return TaskComplexity.MEDIUM
    
    async def route_request(
        self,
        user_input: str,
        messages: List[OllamaMessage],
        context: Optional[Dict[str, Any]] = None,
        preferred_model: Optional[str] = None,
    ) -> Any:
        """Route a request to the appropriate model."""
        
        # Analyze the task
        task_type, complexity = self.analyze_task(user_input, context)
        
        # Get the best model for this task
        model_name = await self.model_manager.get_best_model(
            task_type=task_type,
            complexity=complexity,
            preferred_model=preferred_model,
        )
        
        # Adjust parameters based on task type
        temperature, max_tokens = self._get_optimal_parameters(task_type, complexity)
        
        logger.info(f"Routing {task_type} task (complexity: {complexity}) to model: {model_name}")
        
        # Generate response with fallback
        return await self.model_manager.generate_with_fallback(
            messages=messages,
            task_type=task_type,
            complexity=complexity,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    def _get_optimal_parameters(self, task_type: str, complexity: str) -> Tuple[float, Optional[int]]:
        """Get optimal parameters for the task type and complexity."""
        
        # Base parameters
        temperature = 0.1
        max_tokens = None
        
        # Adjust for task type
        if task_type == TaskType.CODE_GENERATION:
            temperature = 0.1  # Low temperature for consistent code
            max_tokens = 2000 if complexity == TaskComplexity.COMPLEX else 1000
        elif task_type == TaskType.REASONING:
            temperature = 0.3  # Higher temperature for creative reasoning
            max_tokens = 1500
        elif task_type == TaskType.DEBUGGING:
            temperature = 0.1  # Low temperature for precise debugging
            max_tokens = 1000
        elif task_type == TaskType.PLANNING:
            temperature = 0.2  # Moderate temperature for planning
            max_tokens = 2000
        elif task_type == TaskType.DOCUMENTATION:
            temperature = 0.2  # Moderate temperature for documentation
            max_tokens = 1500
        elif task_type == TaskType.TESTING:
            temperature = 0.1  # Low temperature for test generation
            max_tokens = 1000
        elif task_type == TaskType.REFACTORING:
            temperature = 0.1  # Low temperature for refactoring
            max_tokens = 2000
        elif task_type == TaskType.OPTIMIZATION:
            temperature = 0.1  # Low temperature for optimization
            max_tokens = 1500
        elif task_type == TaskType.ANALYSIS:
            temperature = 0.2  # Moderate temperature for analysis
            max_tokens = 1500
        
        # Adjust for complexity
        if complexity == TaskComplexity.COMPLEX:
            max_tokens = int(max_tokens * 1.5) if max_tokens else 3000
        elif complexity == TaskComplexity.SIMPLE:
            max_tokens = int(max_tokens * 0.7) if max_tokens else 500
        
        return temperature, max_tokens
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about model routing."""
        return {
            "task_types": list(self.task_patterns.keys()),
            "complexity_levels": list(self.complexity_indicators.keys()),
            "model_stats": self.model_manager.get_model_stats(),
        }
