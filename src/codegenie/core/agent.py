"""
Main Claude Code Agent implementation.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .config import Config
from .memory import Memory
from .reasoning import ReasoningEngine, ReasoningTrace
from .session import SessionManager
from ..models.model_manager import ModelManager
from ..models.model_router import ModelRouter
from ..models.ollama_client import OllamaMessage

logger = logging.getLogger(__name__)


class CodeGenieAgent:
    """Main CodeGenie Agent class."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.config = session_manager.config
        self.memory = session_manager.memory
        
        # Initialize model components
        self.model_manager = ModelManager(self.config)
        self.model_router = ModelRouter(self.model_manager)
        self.reasoning_engine = ReasoningEngine(self.model_router)
        
        # Agent state
        self._initialized = False
        self._current_task = None
        self._is_thinking = False
    
    async def initialize(self) -> None:
        """Initialize the agent."""
        if self._initialized:
            return
        
        logger.info("Initializing CodeGenie Agent...")
        
        # Initialize model manager
        await self.model_manager.initialize()
        
        # Load relevant memories
        await self._load_relevant_memories()
        
        self._initialized = True
        logger.info("CodeGenie Agent initialized successfully")
    
    async def _load_relevant_memories(self) -> None:
        """Load memories relevant to the current project."""
        
        context = self.session_manager.get_context()
        
        # Load project-specific memories
        project_memories = self.memory.get_memory(
            tags=[context.get("project_type", "unknown")],
            limit=10
        )
        
        # Load recent error patterns
        error_memories = self.memory.get_memory(
            memory_type="error",
            limit=5
        )
        
        # Load user preferences
        preference_memories = self.memory.get_memory(
            memory_type="preference",
            limit=5
        )
        
        logger.debug(f"Loaded {len(project_memories)} project memories, {len(error_memories)} error memories, {len(preference_memories)} preference memories")
    
    async def process_user_input(self, user_input: str) -> str:
        """Process user input and generate response."""
        
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Processing user input: {user_input[:100]}...")
        
        try:
            # Set thinking state
            self._is_thinking = True
            self._current_task = user_input
            
            # Get session context
            context = self.session_manager.get_context()
            recent_context = self.session_manager.get_recent_context()
            
            # Combine contexts
            full_context = {**context, **recent_context}
            
            # Step 1: Reason about the task
            reasoning_trace = await self.reasoning_engine.reason_about_task(
                task=user_input,
                context=full_context
            )
            
            # Step 2: Validate reasoning
            is_valid, issues = await self.reasoning_engine.validate_reasoning(
                reasoning_trace, full_context
            )
            
            # Step 3: Improve reasoning if needed
            if not is_valid:
                logger.warning(f"Reasoning validation failed: {issues}")
                reasoning_trace = await self.reasoning_engine.improve_reasoning(
                    reasoning_trace, issues, full_context
                )
            
            # Step 4: Generate response based on reasoning
            response = await self._generate_response(
                user_input=user_input,
                reasoning_trace=reasoning_trace,
                context=full_context
            )
            
            # Step 5: Record the interaction
            self.session_manager.add_conversation_turn(
                user_input=user_input,
                agent_response=response,
                reasoning_trace=reasoning_trace.dict(),
                success=True
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            
            # Record the error
            self.session_manager.add_conversation_turn(
                user_input=user_input,
                agent_response=f"I encountered an error: {str(e)}",
                errors_encountered=[str(e)],
                success=False
            )
            
            return f"I encountered an error while processing your request: {str(e)}"
        
        finally:
            self._is_thinking = False
            self._current_task = None
    
    async def _analyze_input(self, user_input: str) -> Dict[str, Any]:
        """Analyze user input to determine type and complexity."""
        
        analysis = {
            "type": "general",
            "complexity": "simple",
            "requires_code": False,
            "requires_execution": False,
            "requires_file_ops": False,
            "keywords": [],
            "intent": "unknown"
        }
        
        # Analyze input type
        input_lower = user_input.lower()
        
        # Code-related keywords
        code_keywords = ["function", "class", "method", "code", "program", "script", "algorithm", "implement", "write", "create"]
        if any(keyword in input_lower for keyword in code_keywords):
            analysis["requires_code"] = True
            analysis["type"] = "code_generation"
        
        # Execution-related keywords
        exec_keywords = ["run", "execute", "test", "debug", "fix", "error", "problem", "issue"]
        if any(keyword in input_lower for keyword in exec_keywords):
            analysis["requires_execution"] = True
            analysis["type"] = "code_execution"
        
        # File operation keywords
        file_keywords = ["file", "directory", "folder", "create", "delete", "modify", "edit", "save", "load"]
        if any(keyword in input_lower for keyword in file_keywords):
            analysis["requires_file_ops"] = True
            analysis["type"] = "file_operations"
        
        # Complexity analysis
        if len(user_input.split()) > 20 or any(word in input_lower for word in ["complex", "advanced", "sophisticated", "multiple", "several"]):
            analysis["complexity"] = "complex"
        elif len(user_input.split()) > 10:
            analysis["complexity"] = "medium"
        
        # Intent analysis
        if "?" in user_input or any(word in input_lower for word in ["what", "how", "why", "when", "where", "explain", "describe"]):
            analysis["intent"] = "question"
        elif any(word in input_lower for word in ["help", "assist", "support", "guide"]):
            analysis["intent"] = "help_request"
        elif any(word in input_lower for word in ["create", "make", "build", "generate", "write"]):
            analysis["intent"] = "creation_request"
        
        return analysis
    
    async def _post_process_response(self, response: str, input_analysis: Dict[str, Any]) -> str:
        """Post-process response for better formatting and functionality."""
        
        # Add code execution suggestions if needed
        if input_analysis.get("requires_execution", False):
            response += "\n\n💡 **Execution Tips:**\n"
            response += "- Use `codegenie execute <command>` to run code safely\n"
            response += "- Use `codegenie test` to run tests\n"
            response += "- Use `codegenie debug` for debugging assistance\n"
        
        # Add file operation suggestions if needed
        if input_analysis.get("requires_file_ops", False):
            response += "\n\n📁 **File Operations:**\n"
            response += "- Use `codegenie create <file>` to create files\n"
            response += "- Use `codegenie edit <file>` to modify files\n"
            response += "- Use `codegenie analyze <file>` to analyze code\n"
        
        # Add helpful context based on intent
        if input_analysis.get("intent") == "help_request":
            response += "\n\n🆘 **Need More Help?**\n"
            response += "- Type `help` for available commands\n"
            response += "- Type `examples` for usage examples\n"
            response += "- Type `status` to see current project status\n"
        
        return response
    
    async def _handle_error_recovery(self, error: Exception, user_input: str) -> str:
        """Handle error recovery with intelligent fallback strategies."""
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Store error in memory for learning
        await self.memory.store_memory(
            content=f"Error: {error_type} - {error_message}",
            memory_type="error",
            tags=["error", error_type.lower(), "recovery"]
        )
        
        # Different recovery strategies based on error type
        if "ConnectionError" in error_type or "TimeoutError" in error_type:
            return self._get_connection_error_response()
        elif "ValidationError" in error_type:
            return self._get_validation_error_response()
        elif "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            return self._get_import_error_response()
        else:
            return self._get_generic_error_response(error_message)
    
    def _get_connection_error_response(self) -> str:
        """Get response for connection errors."""
        return """🔌 **Connection Error Detected**

I'm having trouble connecting to the Ollama service. Here's how to fix this:

1. **Check if Ollama is running:**
   ```bash
   ollama serve
   ```

2. **Verify Ollama is accessible:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Install required models:**
   ```bash
   ollama pull llama3.2:latest
   ollama pull gpt-oss:latest
   ```

4. **Restart CodeGenie:**
   ```bash
   codegenie start
   ```

Once Ollama is running, I'll be able to help you with your coding tasks! 🚀"""
    
    def _get_validation_error_response(self) -> str:
        """Get response for validation errors."""
        return """⚠️ **Input Validation Error**

It looks like there might be an issue with the input format. Please try:

1. **Rephrase your request** in a clearer way
2. **Break down complex requests** into smaller parts
3. **Use specific examples** when asking for code

For example, instead of "make it work", try:
- "Create a Python function that calculates the factorial of a number"
- "Fix the syntax error in my Python script"
- "Add error handling to this function"

I'm here to help once you provide more specific details! 🤝"""
    
    def _get_import_error_response(self) -> str:
        """Get response for import errors."""
        return """📦 **Module Import Error**

It seems there's a missing dependency. Here's how to resolve this:

1. **Install missing packages:**
   ```bash
   pip install <package-name>
   ```

2. **Check your virtual environment:**
   ```bash
   source venv/bin/activate  # Linux/Mac
   venv\\Scripts\\activate   # Windows
   ```

3. **Update requirements:**
   ```bash
   pip install -r requirements.txt
   ```

4. **For CodeGenie specifically:**
   ```bash
   pip install -e .
   ```

Let me know what specific package is missing, and I can help you install it! 🔧"""
    
    def _get_generic_error_response(self, error_message: str) -> str:
        """Get response for generic errors."""
        return f"""❌ **Unexpected Error**

I encountered an unexpected error: `{error_message}`

**What you can do:**
1. **Try again** - Sometimes errors are temporary
2. **Simplify your request** - Break it into smaller parts
3. **Check the logs** - Run with `--verbose` for more details
4. **Report the issue** - Help me improve by reporting this error

**Quick fixes to try:**
- Restart CodeGenie: `codegenie start`
- Check Ollama: `ollama serve`
- Update dependencies: `pip install -e .`

I'm constantly learning and improving. Let's try a different approach! 🛠️"""
    
    async def _generate_response(
        self,
        user_input: str,
        reasoning_trace: ReasoningTrace,
        context: Dict[str, Any]
    ) -> str:
        """Generate response based on reasoning trace."""
        
        # Create response prompt
        response_prompt = self._create_response_prompt(
            user_input=user_input,
            reasoning_trace=reasoning_trace,
            context=context
        )
        
        # Create messages
        messages = [
            OllamaMessage(
                role="system",
                content=self._get_system_prompt(context)
            ),
            OllamaMessage(
                role="user",
                content=response_prompt
            )
        ]
        
        # Generate response
        response = await self.model_router.route_request(
            user_input=user_input,
            messages=messages,
            context=context
        )
        
        return response.message.content
    
    def _create_response_prompt(
        self,
        user_input: str,
        reasoning_trace: ReasoningTrace,
        context: Dict[str, Any]
    ) -> str:
        """Create prompt for response generation."""
        
        prompt_parts = [
            f"User Request: {user_input}",
            "",
            "My Analysis:",
        ]
        
        # Add reasoning steps
        for step in reasoning_trace.steps:
            prompt_parts.append(f"{step.step_number}. {step.description}")
            prompt_parts.append(f"   Reasoning: {step.reasoning}")
            prompt_parts.append(f"   Conclusion: {step.conclusion}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            f"Final Conclusion: {reasoning_trace.final_conclusion}",
            "",
            "Now provide a helpful response to the user. Be specific, actionable, and professional. If you need to write code, provide complete, working examples. If you need to explain something, be clear and thorough.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Get system prompt based on context."""
        
        base_prompt = """You are Claude Code, an expert AI coding assistant. You help developers write, debug, and understand code. You are:

- Knowledgeable about multiple programming languages and frameworks
- Patient and thorough in your explanations
- Focused on writing clean, maintainable code
- Proactive in suggesting improvements and best practices
- Careful about security and performance considerations

Always provide complete, working code examples when possible. Explain your reasoning and suggest alternatives when appropriate."""

        # Add project-specific context
        if context.get("project_type"):
            base_prompt += f"\n\nCurrent project: {context['project_type']} project"
        
        if context.get("languages"):
            base_prompt += f" using {', '.join(context['languages'])}"
        
        if context.get("frameworks"):
            base_prompt += f" with {', '.join(context['frameworks'])}"
        
        # Add recent context
        if context.get("recent_errors"):
            base_prompt += f"\n\nRecent errors encountered: {', '.join(context['recent_errors'][:3])}"
        
        if context.get("current_goal"):
            base_prompt += f"\n\nCurrent goal: {context['current_goal']}"
        
        return base_prompt
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        
        status = {
            "initialized": self._initialized,
            "thinking": self._is_thinking,
            "current_task": self._current_task,
            "session_stats": self.session_manager.get_session_stats(),
            "model_stats": self.model_manager.get_model_stats(),
            "memory_stats": self.memory.get_memory_stats(),
        }
        
        return status
    
    async def set_goal(self, goal: str) -> None:
        """Set a goal for the current session."""
        
        self.session_manager.set_current_goal(goal)
        
        # Add goal to memory
        self.memory.add_memory(
            memory_type="goal",
            content={"goal": goal, "timestamp": time.time()},
            importance=3.0,
            tags=["goal", "planning"]
        )
        
        logger.info(f"Set session goal: {goal}")
    
    async def get_suggestions(self, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get suggestions based on current context."""
        
        if not context:
            context = self.session_manager.get_context()
        
        suggestions = []
        
        # Project-specific suggestions
        if context.get("project_type") == "python":
            if not context.get("has_tests"):
                suggestions.append("Consider adding unit tests with pytest")
            if not context.get("has_docs"):
                suggestions.append("Add documentation with docstrings and README")
        
        elif context.get("project_type") == "nodejs":
            if not context.get("has_tests"):
                suggestions.append("Consider adding tests with Jest or Mocha")
            if not context.get("has_docs"):
                suggestions.append("Add documentation with JSDoc and README")
        
        # General suggestions
        if context.get("file_count", 0) > 50:
            suggestions.append("Consider organizing code into modules/packages")
        
        if not context.get("git_repo"):
            suggestions.append("Initialize git repository for version control")
        
        # Memory-based suggestions
        recent_errors = self.memory.get_memory(memory_type="error", limit=3)
        if recent_errors:
            suggestions.append("Review and fix recent errors to improve code quality")
        
        return suggestions
    
    async def learn_from_feedback(
        self,
        user_input: str,
        agent_response: str,
        feedback: str,
        is_positive: bool
    ) -> None:
        """Learn from user feedback."""
        
        # Add feedback to memory
        self.memory.add_memory(
            memory_type="feedback",
            content={
                "user_input": user_input,
                "agent_response": agent_response,
                "feedback": feedback,
                "is_positive": is_positive,
                "timestamp": time.time()
            },
            importance=2.0 if is_positive else 1.5,
            tags=["feedback", "learning"]
        )
        
        # Update model performance if applicable
        if is_positive:
            # Find the model used for this response
            # This would need to be tracked in the conversation turn
            pass
        
        logger.info(f"Learned from {'positive' if is_positive else 'negative'} feedback")
    
    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code safely with comprehensive error handling."""
        
        try:
            # Import safe executor
            from ..utils.safe_executor import SafeExecutor
            
            executor = SafeExecutor()
            context = {
                "working_directory": str(self.session_manager.project_path),
                "timeout": 30,
                "memory_limit": 100 * 1024 * 1024,  # 100MB
                "allowed_imports": ["os", "sys", "math", "json", "datetime", "pathlib"],
                "blocked_imports": ["subprocess", "os.system", "eval", "exec"]
            }
            
            result = await executor.execute_code(code, language, context)
            
            # Store execution result in memory
            await self.memory.store_memory(
                content=f"Code execution: {result.get('success', False)} - {result.get('output', '')}",
                memory_type="execution",
                tags=["code_execution", language, "success" if result.get('success') else "error"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": 0
            }
    
    async def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Analyze code file for issues, patterns, and suggestions."""
        
        try:
            from ..utils.code_analyzer import CodeAnalyzer
            
            analyzer = CodeAnalyzer()
            analysis = analyzer.analyze_file(file_path)
            
            # Store analysis in memory
            await self.memory.store_memory(
                content=f"Code analysis for {file_path}: {len(analysis.get('issues', []))} issues found",
                memory_type="analysis",
                tags=["code_analysis", file_path.split('.')[-1], "file"]
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "suggestions": []
            }
    
    async def create_file(self, file_path: str, content: str, file_type: str = "text") -> Dict[str, Any]:
        """Create a new file with content."""
        
        try:
            from ..utils.enhanced_file_ops import EnhancedFileOperations
            
            file_ops = EnhancedFileOperations()
            result = file_ops.safe_create_file(file_path, content)
            
            # Store file creation in memory
            await self.memory.store_memory(
                content=f"Created file: {file_path} ({len(content)} characters)",
                memory_type="file_operation",
                tags=["file_creation", file_type, "success" if result.get('success') else "error"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    async def run_tests(self, test_path: str = None) -> Dict[str, Any]:
        """Run tests for the project."""
        
        try:
            from ..utils.testing_framework import TestingFramework
            
            tester = TestingFramework()
            result = await tester.run_tests(test_path or str(self.session_manager.project_path))
            
            # Store test results in memory
            await self.memory.store_memory(
                content=f"Test run: {result.get('passed', 0)}/{result.get('total', 0)} tests passed",
                memory_type="testing",
                tags=["test_execution", "success" if result.get('all_passed') else "failure"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                "success": False,
                "error": str(e),
                "passed": 0,
                "total": 0,
                "all_passed": False
            }
    
    async def get_project_insights(self) -> Dict[str, Any]:
        """Get comprehensive project insights and recommendations."""
        
        try:
            from ..utils.project_analyzer import ProjectAnalyzer
            
            analyzer = ProjectAnalyzer()
            insights = analyzer.analyze_project(self.session_manager.project_path)
            
            # Store insights in memory
            self.memory.add_memory(
                content={
                    "summary": f"Project insights: {insights.get('project_type', 'unknown')} project with {insights.get('file_count', 0)} files",
                    "project_type": insights.get('project_type', 'unknown'),
                    "file_count": insights.get('file_count', 0),
                    "languages": insights.get('languages', []),
                    "recommendations": insights.get('recommendations', [])
                },
                memory_type="project_analysis",
                tags=["project_insights", insights.get('project_type', 'unknown')]
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting project insights: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_type": "unknown",
                "file_count": 0,
                "recommendations": []
            }
    
    async def get_learning_suggestions(self) -> List[str]:
        """Get personalized learning suggestions based on user interactions."""
        
        try:
            # Get recent memories
            recent_memories = self.memory.get_memory(limit=20)
            
            # Analyze patterns
            suggestions = []
            
            # Check for common error patterns
            error_memories = [m for m in recent_memories if m.get('memory_type') == 'error']
            if len(error_memories) > 3:
                suggestions.append("Consider reviewing error handling patterns in your code")
            
            # Check for code complexity
            code_memories = [m for m in recent_memories if 'code' in m.get('tags', [])]
            if len(code_memories) > 10:
                suggestions.append("You're writing a lot of code! Consider adding more tests")
            
            # Check for testing patterns
            test_memories = [m for m in recent_memories if 'test' in m.get('tags', [])]
            if len(test_memories) < 2:
                suggestions.append("Consider adding more tests to improve code reliability")
            
            # Add general suggestions
            suggestions.extend([
                "Try using type hints to improve code clarity",
                "Consider adding docstrings to your functions",
                "Use version control to track your changes",
                "Regular code reviews can help catch issues early"
            ])
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting learning suggestions: {e}")
            return ["Keep practicing and learning new programming concepts!"]
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully."""
        
        logger.info("Shutting down CodeGenie Agent...")
        
        # Save final session state
        self.session_manager._save_session()
        
        # Save memory
        self.memory._save_memory()
        
        logger.info("CodeGenie Agent shutdown complete")
