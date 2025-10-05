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
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully."""
        
        logger.info("Shutting down CodeGenie Agent...")
        
        # Save final session state
        self.session_manager._save_session()
        
        # Save memory
        self.memory._save_memory()
        
        logger.info("CodeGenie Agent shutdown complete")
