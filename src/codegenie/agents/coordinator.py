"""
Agent coordinator for task delegation and multi-agent coordination.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .base_agent import BaseAgent, Task, TaskPriority, AgentResult, AgentCapability
from .communication import AgentCommunicationBus, Message, MessageType

logger = logging.getLogger(__name__)


class CoordinationStrategy(Enum):
    """Strategies for coordinating multiple agents."""
    
    SEQUENTIAL = "sequential"  # Execute tasks one after another
    PARALLEL = "parallel"     # Execute tasks in parallel
    PIPELINE = "pipeline"     # Pipeline execution with dependencies
    CONSENSUS = "consensus"   # Require consensus from multiple agents
    COMPETITION = "competition"  # Multiple agents compete, best result wins


@dataclass
class AgentAssignment:
    """Represents an assignment of a task to an agent."""
    
    agent_name: str
    task: Task
    assignment_time: float = field(default_factory=time.time)
    estimated_completion: Optional[float] = None
    actual_completion: Optional[float] = None
    result: Optional[AgentResult] = None


@dataclass
class CoordinationPlan:
    """Plan for coordinating multiple agents on a complex task."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL
    assignments: List[AgentAssignment] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # task_id -> [dependency_task_ids]
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    success: bool = False
    results: Dict[str, AgentResult] = field(default_factory=dict)


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicts between agents."""
    
    PRIORITY_BASED = "priority_based"  # Use agent priority/expertise
    CONSENSUS = "consensus"            # Require majority agreement
    EXPERT_DECISION = "expert_decision"  # Defer to most expert agent
    USER_DECISION = "user_decision"    # Ask user to decide
    HYBRID_APPROACH = "hybrid_approach"  # Combine multiple approaches


@dataclass
class AgentConflict:
    """Represents a conflict between agent recommendations."""
    
    task_id: str
    conflicting_agents: List[str]
    conflicting_results: List[AgentResult]
    conflict_type: str  # "recommendation", "approach", "priority"
    resolution_strategy: Optional[ConflictResolutionStrategy] = None
    resolution: Optional[AgentResult] = None
    resolved_at: Optional[float] = None


class AgentCoordinator:
    """Coordinates multiple agents for complex task execution."""
    
    def __init__(self, communication_bus: AgentCommunicationBus):
        self.communication_bus = communication_bus
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, Set[AgentCapability]] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        self.active_plans: Dict[str, CoordinationPlan] = {}
        self.conflict_history: List[AgentConflict] = []
        
        # Default conflict resolution preferences
        self.default_conflict_strategy = ConflictResolutionStrategy.EXPERT_DECISION
        self.agent_priorities: Dict[str, int] = {}  # Higher number = higher priority
        
        logger.info("Initialized AgentCoordinator")
    
    def register_agent(self, agent: BaseAgent, priority: int = 1) -> None:
        """
        Register an agent with the coordinator.
        
        Args:
            agent: The agent to register
            priority: Priority level for conflict resolution (higher = more priority)
        """
        self.agents[agent.name] = agent
        self.agent_capabilities[agent.name] = agent.capabilities.copy()
        self.agent_priorities[agent.name] = priority
        self.agent_performance[agent.name] = agent.performance_metrics.copy()
        
        # Register with communication bus
        self.communication_bus.register_agent(agent.name, agent)
        
        logger.info(f"Registered agent {agent.name} with priority {priority}")
    
    def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister an agent from the coordinator.
        
        Args:
            agent_name: Name of the agent to unregister
        """
        self.agents.pop(agent_name, None)
        self.agent_capabilities.pop(agent_name, None)
        self.agent_priorities.pop(agent_name, None)
        self.agent_performance.pop(agent_name, None)
        
        # Unregister from communication bus
        self.communication_bus.unregister_agent(agent_name)
        
        logger.info(f"Unregistered agent {agent_name}")
    
    async def delegate_task(self, task: Task) -> Optional[AgentAssignment]:
        """
        Delegate a task to the most suitable agent.
        
        Args:
            task: The task to delegate
            
        Returns:
            AgentAssignment if successful, None otherwise
        """
        # Find suitable agents
        suitable_agents = await self._find_suitable_agents(task)
        
        if not suitable_agents:
            logger.warning(f"No suitable agents found for task: {task.description}")
            return None
        
        # Select best agent
        best_agent = self._select_best_agent(suitable_agents, task)
        
        # Create assignment
        assignment = AgentAssignment(
            agent_name=best_agent.name,
            task=task,
            estimated_completion=time.time() + self._estimate_task_duration(best_agent, task)
        )
        
        logger.info(f"Delegated task '{task.description}' to agent {best_agent.name}")
        return assignment
    
    async def coordinate_complex_task(
        self,
        description: str,
        subtasks: List[Task],
        strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL,
        dependencies: Optional[Dict[str, List[str]]] = None
    ) -> CoordinationPlan:
        """
        Coordinate multiple agents for a complex task.
        
        Args:
            description: Description of the complex task
            subtasks: List of subtasks to coordinate
            strategy: Coordination strategy to use
            dependencies: Task dependencies (task_id -> [dependency_task_ids])
            
        Returns:
            CoordinationPlan for the complex task
        """
        plan = CoordinationPlan(
            description=description,
            strategy=strategy,
            dependencies=dependencies or {}
        )
        
        # Create assignments for each subtask
        for subtask in subtasks:
            assignment = await self.delegate_task(subtask)
            if assignment:
                plan.assignments.append(assignment)
            else:
                logger.error(f"Failed to assign subtask: {subtask.description}")
        
        # Store active plan
        self.active_plans[plan.id] = plan
        
        logger.info(f"Created coordination plan '{description}' with {len(plan.assignments)} assignments")
        return plan
    
    async def execute_coordination_plan(self, plan: CoordinationPlan) -> bool:
        """
        Execute a coordination plan.
        
        Args:
            plan: The coordination plan to execute
            
        Returns:
            True if execution was successful, False otherwise
        """
        plan.started_at = time.time()
        
        try:
            if plan.strategy == CoordinationStrategy.SEQUENTIAL:
                success = await self._execute_sequential(plan)
            elif plan.strategy == CoordinationStrategy.PARALLEL:
                success = await self._execute_parallel(plan)
            elif plan.strategy == CoordinationStrategy.PIPELINE:
                success = await self._execute_pipeline(plan)
            elif plan.strategy == CoordinationStrategy.CONSENSUS:
                success = await self._execute_consensus(plan)
            elif plan.strategy == CoordinationStrategy.COMPETITION:
                success = await self._execute_competition(plan)
            else:
                logger.error(f"Unknown coordination strategy: {plan.strategy}")
                success = False
            
            plan.completed_at = time.time()
            plan.success = success
            
            logger.info(f"Coordination plan '{plan.description}' completed with success: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Error executing coordination plan: {e}")
            plan.completed_at = time.time()
            plan.success = False
            return False
    
    async def _execute_sequential(self, plan: CoordinationPlan) -> bool:
        """Execute assignments sequentially."""
        for assignment in plan.assignments:
            agent = self.agents[assignment.agent_name]
            
            try:
                await agent.start_task(assignment.task)
                result = await agent.execute_task(assignment.task)
                await agent.complete_task(result)
                
                assignment.result = result
                assignment.actual_completion = time.time()
                plan.results[assignment.task.id] = result
                
                if not result.success:
                    logger.error(f"Task failed in sequential execution: {assignment.task.description}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error in sequential execution: {e}")
                await agent.handle_error(e)
                return False
        
        return True
    
    async def _execute_parallel(self, plan: CoordinationPlan) -> bool:
        """Execute assignments in parallel."""
        tasks = []
        
        for assignment in plan.assignments:
            task_coroutine = self._execute_assignment(assignment)
            tasks.append(task_coroutine)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success = True
        for i, result in enumerate(results):
            assignment = plan.assignments[i]
            
            if isinstance(result, Exception):
                logger.error(f"Parallel execution error for {assignment.task.description}: {result}")
                success = False
            else:
                assignment.result = result
                assignment.actual_completion = time.time()
                plan.results[assignment.task.id] = result
                
                if not result.success:
                    success = False
        
        return success
    
    async def _execute_pipeline(self, plan: CoordinationPlan) -> bool:
        """Execute assignments in pipeline with dependencies."""
        completed_tasks = set()
        remaining_assignments = plan.assignments.copy()
        
        while remaining_assignments:
            # Find assignments that can be executed (dependencies met)
            ready_assignments = []
            
            for assignment in remaining_assignments:
                task_id = assignment.task.id
                dependencies = plan.dependencies.get(task_id, [])
                
                if all(dep_id in completed_tasks for dep_id in dependencies):
                    ready_assignments.append(assignment)
            
            if not ready_assignments:
                logger.error("Pipeline execution deadlock - no ready assignments")
                return False
            
            # Execute ready assignments in parallel
            tasks = [self._execute_assignment(assignment) for assignment in ready_assignments]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                assignment = ready_assignments[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Pipeline execution error: {result}")
                    return False
                
                assignment.result = result
                assignment.actual_completion = time.time()
                plan.results[assignment.task.id] = result
                completed_tasks.add(assignment.task.id)
                remaining_assignments.remove(assignment)
                
                if not result.success:
                    logger.error(f"Task failed in pipeline: {assignment.task.description}")
                    return False
        
        return True
    
    async def _execute_consensus(self, plan: CoordinationPlan) -> bool:
        """Execute with consensus requirement."""
        # Group assignments by task type for consensus
        task_groups = {}
        for assignment in plan.assignments:
            task_type = assignment.task.task_type
            if task_type not in task_groups:
                task_groups[task_type] = []
            task_groups[task_type].append(assignment)
        
        # Execute each group and require consensus
        for task_type, assignments in task_groups.items():
            if len(assignments) < 2:
                # Single assignment, execute normally
                result = await self._execute_assignment(assignments[0])
                plan.results[assignments[0].task.id] = result
                continue
            
            # Execute all assignments in parallel
            tasks = [self._execute_assignment(assignment) for assignment in assignments]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for consensus
            valid_results = [r for r in results if not isinstance(r, Exception) and r.success]
            
            if len(valid_results) < len(assignments) // 2 + 1:  # Majority required
                logger.error(f"Consensus not reached for task type: {task_type}")
                return False
            
            # Use best result (highest confidence)
            best_result = max(valid_results, key=lambda r: r.confidence)
            
            for assignment in assignments:
                plan.results[assignment.task.id] = best_result
        
        return True
    
    async def _execute_competition(self, plan: CoordinationPlan) -> bool:
        """Execute with competition - best result wins."""
        # Execute all assignments in parallel
        tasks = [self._execute_assignment(assignment) for assignment in plan.assignments]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find best result
        valid_results = []
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result.success:
                valid_results.append((result, plan.assignments[i]))
        
        if not valid_results:
            logger.error("No valid results in competition execution")
            return False
        
        # Select winner based on confidence and performance
        best_result, best_assignment = max(
            valid_results,
            key=lambda x: x[0].confidence * self._get_agent_performance_score(x[1].agent_name)
        )
        
        # Store winning result for all tasks
        for assignment in plan.assignments:
            plan.results[assignment.task.id] = best_result
        
        logger.info(f"Competition won by agent {best_assignment.agent_name}")
        return True
    
    async def _execute_assignment(self, assignment: AgentAssignment) -> AgentResult:
        """Execute a single assignment."""
        agent = self.agents[assignment.agent_name]
        
        await agent.start_task(assignment.task)
        result = await agent.execute_task(assignment.task)
        await agent.complete_task(result)
        
        return result
    
    async def resolve_conflict(self, conflict: AgentConflict) -> Optional[AgentResult]:
        """
        Resolve a conflict between agents.
        
        Args:
            conflict: The conflict to resolve
            
        Returns:
            Resolved result or None if resolution failed
        """
        strategy = conflict.resolution_strategy or self.default_conflict_strategy
        
        try:
            if strategy == ConflictResolutionStrategy.PRIORITY_BASED:
                resolution = self._resolve_by_priority(conflict)
            elif strategy == ConflictResolutionStrategy.CONSENSUS:
                resolution = self._resolve_by_consensus(conflict)
            elif strategy == ConflictResolutionStrategy.EXPERT_DECISION:
                resolution = self._resolve_by_expertise(conflict)
            elif strategy == ConflictResolutionStrategy.HYBRID_APPROACH:
                resolution = self._resolve_hybrid(conflict)
            else:
                logger.error(f"Unsupported conflict resolution strategy: {strategy}")
                return None
            
            conflict.resolution = resolution
            conflict.resolved_at = time.time()
            self.conflict_history.append(conflict)
            
            logger.info(f"Resolved conflict for task {conflict.task_id} using {strategy.value}")
            return resolution
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return None
    
    def _resolve_by_priority(self, conflict: AgentConflict) -> AgentResult:
        """Resolve conflict based on agent priority."""
        highest_priority = -1
        best_result = None
        
        for i, agent_name in enumerate(conflict.conflicting_agents):
            priority = self.agent_priorities.get(agent_name, 0)
            if priority > highest_priority:
                highest_priority = priority
                best_result = conflict.conflicting_results[i]
        
        return best_result
    
    def _resolve_by_consensus(self, conflict: AgentConflict) -> AgentResult:
        """Resolve conflict by finding consensus."""
        # Simple implementation: return result with highest confidence
        return max(conflict.conflicting_results, key=lambda r: r.confidence)
    
    def _resolve_by_expertise(self, conflict: AgentConflict) -> AgentResult:
        """Resolve conflict by deferring to most expert agent."""
        best_score = -1
        best_result = None
        
        for i, agent_name in enumerate(conflict.conflicting_agents):
            score = self._get_agent_performance_score(agent_name)
            if score > best_score:
                best_score = score
                best_result = conflict.conflicting_results[i]
        
        return best_result
    
    def _resolve_hybrid(self, conflict: AgentConflict) -> AgentResult:
        """Resolve conflict using hybrid approach."""
        # Combine priority, expertise, and confidence
        best_score = -1
        best_result = None
        
        for i, agent_name in enumerate(conflict.conflicting_agents):
            result = conflict.conflicting_results[i]
            
            priority_score = self.agent_priorities.get(agent_name, 0) / 10.0
            expertise_score = self._get_agent_performance_score(agent_name)
            confidence_score = result.confidence
            
            combined_score = (priority_score + expertise_score + confidence_score) / 3
            
            if combined_score > best_score:
                best_score = combined_score
                best_result = result
        
        return best_result
    
    async def _find_suitable_agents(self, task: Task) -> List[BaseAgent]:
        """Find agents suitable for a task."""
        suitable_agents = []
        
        for agent in self.agents.values():
            if await agent.can_handle_task(task):
                suitable_agents.append(agent)
        
        return suitable_agents
    
    def _select_best_agent(self, suitable_agents: List[BaseAgent], task: Task) -> BaseAgent:
        """Select the best agent from suitable candidates."""
        if len(suitable_agents) == 1:
            return suitable_agents[0]
        
        # Score agents based on performance, priority, and current load
        best_score = -1
        best_agent = suitable_agents[0]
        
        for agent in suitable_agents:
            performance_score = self._get_agent_performance_score(agent.name)
            priority_score = self.agent_priorities.get(agent.name, 0) / 10.0
            load_score = 1.0 if agent.current_task is None else 0.5  # Prefer idle agents
            
            combined_score = (performance_score + priority_score + load_score) / 3
            
            if combined_score > best_score:
                best_score = combined_score
                best_agent = agent
        
        return best_agent
    
    def _get_agent_performance_score(self, agent_name: str) -> float:
        """Get performance score for an agent."""
        performance = self.agent_performance.get(agent_name, {})
        success_rate = performance.get("success_rate", 0.5)
        return success_rate
    
    def _estimate_task_duration(self, agent: BaseAgent, task: Task) -> float:
        """Estimate task duration for an agent."""
        # Simple estimation based on agent performance
        base_duration = 60.0  # 1 minute base
        
        performance = self.agent_performance.get(agent.name, {})
        avg_time = performance.get("average_execution_time", base_duration)
        
        # Adjust based on task priority
        if task.priority == TaskPriority.CRITICAL:
            return avg_time * 0.8  # Rush job
        elif task.priority == TaskPriority.LOW:
            return avg_time * 1.2  # Take more time
        
        return avg_time
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics."""
        total_plans = len(self.active_plans)
        completed_plans = sum(1 for plan in self.active_plans.values() if plan.completed_at is not None)
        successful_plans = sum(1 for plan in self.active_plans.values() if plan.success)
        
        return {
            "registered_agents": len(self.agents),
            "active_plans": total_plans,
            "completed_plans": completed_plans,
            "successful_plans": successful_plans,
            "success_rate": successful_plans / max(completed_plans, 1),
            "total_conflicts": len(self.conflict_history),
            "agent_performance": self.agent_performance.copy()
        }