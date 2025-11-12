"""
Base agent architecture for the multi-agent system.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

from ..core.config import Config
from ..models.model_router import ModelRouter

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Enumeration of agent capabilities."""
    
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    PROJECT_PLANNING = "project_planning"


class AgentStatus(Enum):
    """Agent status enumeration."""
    
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """Task priority levels."""
    
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """Represents a task that can be assigned to an agent."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    task_type: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    success: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentResult:
    """Result returned by an agent after task execution."""
    
    agent_name: str
    task_id: str
    success: bool
    output: Any = None
    confidence: float = 0.0
    reasoning: str = ""
    suggestions: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[str] = None


@dataclass
class CollaborationRequest:
    """Request for collaboration between agents."""
    
    requesting_agent: str
    target_agent: str
    task: Task
    collaboration_type: str  # "consultation", "delegation", "joint_execution"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationResult:
    """Result of collaboration between agents."""
    
    success: bool
    output: Any = None
    participating_agents: List[str] = field(default_factory=list)
    reasoning: str = ""
    recommendations: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""
    
    def __init__(
        self,
        name: str,
        capabilities: List[AgentCapability],
        config: Config,
        model_router: ModelRouter
    ):
        self.name = name
        self.capabilities = set(capabilities)
        self.config = config
        self.model_router = model_router
        
        # Agent state
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Task] = None
        self.task_history: List[Task] = []
        self.performance_metrics: Dict[str, float] = {}
        
        # Communication
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.collaboration_handlers: Dict[str, callable] = {}
        
        # Context and memory
        self.context: Dict[str, Any] = {}
        self.working_memory: Dict[str, Any] = {}
        
        logger.info(f"Initialized agent '{name}' with capabilities: {[c.value for c in capabilities]}")
    
    @abstractmethod
    async def can_handle_task(self, task: Task) -> bool:
        """
        Determine if this agent can handle the given task.
        
        Args:
            task: The task to evaluate
            
        Returns:
            True if the agent can handle the task, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: Task) -> AgentResult:
        """
        Execute the given task.
        
        Args:
            task: The task to execute
            
        Returns:
            AgentResult containing the execution results
        """
        pass
    
    async def start_task(self, task: Task) -> None:
        """Start executing a task."""
        if self.status != AgentStatus.IDLE:
            raise RuntimeError(f"Agent {self.name} is not idle (status: {self.status})")
        
        self.status = AgentStatus.BUSY
        self.current_task = task
        task.assigned_agent = self.name
        task.started_at = time.time()
        
        logger.info(f"Agent {self.name} started task: {task.description}")
    
    async def complete_task(self, result: AgentResult) -> None:
        """Complete the current task."""
        if not self.current_task:
            raise RuntimeError(f"Agent {self.name} has no current task to complete")
        
        self.current_task.completed_at = time.time()
        self.current_task.success = result.success
        self.current_task.result = result.output
        self.current_task.error = result.error
        
        # Update performance metrics
        execution_time = self.current_task.completed_at - (self.current_task.started_at or 0)
        self._update_performance_metrics(execution_time, result.success)
        
        # Move to history
        self.task_history.append(self.current_task)
        self.current_task = None
        self.status = AgentStatus.IDLE
        
        logger.info(f"Agent {self.name} completed task with success: {result.success}")
    
    async def handle_error(self, error: Exception) -> None:
        """Handle an error during task execution."""
        self.status = AgentStatus.ERROR
        
        if self.current_task:
            self.current_task.error = str(error)
            self.current_task.success = False
            self.current_task.completed_at = time.time()
            
            # Move to history
            self.task_history.append(self.current_task)
            self.current_task = None
        
        logger.error(f"Agent {self.name} encountered error: {error}")
        
        # Reset to idle after error handling
        self.status = AgentStatus.IDLE
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if the agent has a specific capability."""
        return capability in self.capabilities
    
    def add_capability(self, capability: AgentCapability) -> None:
        """Add a capability to the agent."""
        self.capabilities.add(capability)
        logger.info(f"Added capability {capability.value} to agent {self.name}")
    
    def remove_capability(self, capability: AgentCapability) -> None:
        """Remove a capability from the agent."""
        self.capabilities.discard(capability)
        logger.info(f"Removed capability {capability.value} from agent {self.name}")
    
    async def collaborate_with(
        self,
        other_agent: 'BaseAgent',
        task: Task,
        collaboration_type: str = "consultation"
    ) -> CollaborationResult:
        """
        Collaborate with another agent on a task.
        
        Args:
            other_agent: The agent to collaborate with
            task: The task to collaborate on
            collaboration_type: Type of collaboration
            
        Returns:
            CollaborationResult with the outcome
        """
        logger.info(f"Agent {self.name} collaborating with {other_agent.name} on task: {task.description}")
        
        try:
            if collaboration_type == "consultation":
                return await self._handle_consultation(other_agent, task)
            elif collaboration_type == "delegation":
                return await self._handle_delegation(other_agent, task)
            elif collaboration_type == "joint_execution":
                return await self._handle_joint_execution(other_agent, task)
            else:
                raise ValueError(f"Unknown collaboration type: {collaboration_type}")
        
        except Exception as e:
            logger.error(f"Collaboration failed between {self.name} and {other_agent.name}: {e}")
            return CollaborationResult(
                success=False,
                participating_agents=[self.name, other_agent.name],
                reasoning=f"Collaboration failed: {str(e)}"
            )
    
    async def _handle_consultation(self, other_agent: 'BaseAgent', task: Task) -> CollaborationResult:
        """Handle consultation collaboration."""
        # Ask for expertise from the other agent
        expertise_response = await other_agent.provide_expertise(task.description)
        
        return CollaborationResult(
            success=True,
            output=expertise_response,
            participating_agents=[self.name, other_agent.name],
            reasoning=f"Consulted {other_agent.name} for expertise on {task.task_type}",
            recommendations=expertise_response.get("recommendations", [])
        )
    
    async def _handle_delegation(self, other_agent: 'BaseAgent', task: Task) -> CollaborationResult:
        """Handle delegation collaboration."""
        # Check if other agent can handle the task
        can_handle = await other_agent.can_handle_task(task)
        
        if not can_handle:
            return CollaborationResult(
                success=False,
                participating_agents=[self.name, other_agent.name],
                reasoning=f"Agent {other_agent.name} cannot handle the delegated task"
            )
        
        # Delegate the task
        result = await other_agent.execute_task(task)
        
        return CollaborationResult(
            success=result.success,
            output=result.output,
            participating_agents=[self.name, other_agent.name],
            reasoning=f"Delegated task to {other_agent.name}",
            recommendations=result.suggestions
        )
    
    async def _handle_joint_execution(self, other_agent: 'BaseAgent', task: Task) -> CollaborationResult:
        """Handle joint execution collaboration."""
        # Execute task collaboratively
        my_result = await self.execute_task(task)
        other_result = await other_agent.execute_task(task)
        
        # Combine results
        combined_output = {
            "primary_result": my_result.output,
            "secondary_result": other_result.output,
            "combined_confidence": (my_result.confidence + other_result.confidence) / 2
        }
        
        success = my_result.success and other_result.success
        
        return CollaborationResult(
            success=success,
            output=combined_output,
            participating_agents=[self.name, other_agent.name],
            reasoning=f"Joint execution between {self.name} and {other_agent.name}",
            recommendations=my_result.suggestions + other_result.suggestions
        )
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """
        Provide expertise on a specific question or topic.
        
        Args:
            question: The question or topic to provide expertise on
            
        Returns:
            Dictionary containing expertise response
        """
        # Default implementation - subclasses should override
        return {
            "expertise": f"General guidance from {self.name}",
            "confidence": 0.5,
            "recommendations": [
                "Consider breaking down the problem into smaller parts",
                "Review existing patterns and best practices",
                "Test thoroughly before implementation"
            ]
        }
    
    def _update_performance_metrics(self, execution_time: float, success: bool) -> None:
        """Update performance metrics for the agent."""
        if "total_tasks" not in self.performance_metrics:
            self.performance_metrics["total_tasks"] = 0
            self.performance_metrics["successful_tasks"] = 0
            self.performance_metrics["average_execution_time"] = 0.0
            self.performance_metrics["success_rate"] = 0.0
        
        self.performance_metrics["total_tasks"] += 1
        
        if success:
            self.performance_metrics["successful_tasks"] += 1
        
        # Update average execution time
        total_tasks = self.performance_metrics["total_tasks"]
        current_avg = self.performance_metrics["average_execution_time"]
        self.performance_metrics["average_execution_time"] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
        
        # Update success rate
        self.performance_metrics["success_rate"] = (
            self.performance_metrics["successful_tasks"] / total_tasks
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        return {
            "name": self.name,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "current_task": self.current_task.description if self.current_task else None,
            "task_history_count": len(self.task_history),
            "performance_metrics": self.performance_metrics.copy(),
            "context_size": len(self.context),
            "working_memory_size": len(self.working_memory)
        }
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """Update the agent's context."""
        self.context.update(context)
    
    def clear_working_memory(self) -> None:
        """Clear the agent's working memory."""
        self.working_memory.clear()
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully."""
        logger.info(f"Shutting down agent {self.name}")
        
        # Complete any current task with error
        if self.current_task:
            await self.handle_error(Exception("Agent shutdown"))
        
        self.status = AgentStatus.OFFLINE