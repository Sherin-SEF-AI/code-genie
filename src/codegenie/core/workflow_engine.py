"""
Workflow engine for autonomous task planning and execution.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4

from ..agents.base_agent import Task, TaskPriority, AgentResult
from ..agents.coordinator import AgentCoordinator, CoordinationPlan, CoordinationStrategy

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    
    CREATED = "created"
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk levels for workflow operations."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    task: Optional[Task] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 60.0  # seconds
    risk_level: RiskLevel = RiskLevel.LOW
    rollback_strategy: Optional[str] = None
    success_criteria: List[str] = field(default_factory=list)
    
    # Execution state
    status: WorkflowStatus = WorkflowStatus.CREATED
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[AgentResult] = None
    error: Optional[str] = None


@dataclass
class Checkpoint:
    """Represents a checkpoint in workflow execution."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str = ""
    step_id: str = ""
    timestamp: float = field(default_factory=time.time)
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    completed_steps: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class WorkflowPlan:
    """Complete workflow execution plan."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    goal: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    checkpoints: List[Checkpoint] = field(default_factory=list)
    
    # Execution metadata
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    
    # Risk and rollback
    overall_risk: RiskLevel = RiskLevel.LOW
    rollback_plan: Optional[str] = None
    
    # Results
    success: bool = False
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    # Autonomous planning enhancements
    schedule: Dict[str, Any] = field(default_factory=dict)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    risk_mitigation_strategies: List[str] = field(default_factory=list)


class TaskPlanner:
    """Plans and decomposes complex tasks into executable workflows."""
    
    def __init__(self, agent_coordinator: AgentCoordinator):
        self.agent_coordinator = agent_coordinator
        self.planning_strategies: Dict[str, Callable] = {
            "hierarchical": self._plan_hierarchical,
            "sequential": self._plan_sequential,
            "parallel": self._plan_parallel,
            "hybrid": self._plan_hybrid
        }
        
        # Autonomous planning capabilities
        self.dependency_analyzer = DependencyAnalyzer()
        self.task_scheduler = TaskScheduler()
        self.milestone_tracker = MilestoneTracker()
        self.progress_monitor = ProgressMonitor()
        
        logger.info("Initialized TaskPlanner with autonomous capabilities")
    
    async def create_workflow_plan(
        self,
        goal: str,
        context: Dict[str, Any] = None,
        strategy: str = "hierarchical"
    ) -> WorkflowPlan:
        """
        Create a workflow plan for achieving a goal.
        
        Args:
            goal: The high-level goal to achieve
            context: Additional context for planning
            strategy: Planning strategy to use
            
        Returns:
            WorkflowPlan for achieving the goal
        """
        logger.info(f"Creating autonomous workflow plan for goal: {goal}")
        
        context = context or {}
        
        # Analyze the goal
        goal_analysis = await self._analyze_goal(goal, context)
        
        # Create base plan
        plan = WorkflowPlan(
            name=f"Workflow for: {goal[:50]}...",
            description=f"Automated workflow to achieve: {goal}",
            goal=goal,
            overall_risk=goal_analysis.get("risk_level", RiskLevel.MEDIUM)
        )
        
        # Use appropriate planning strategy
        if strategy in self.planning_strategies:
            await self.planning_strategies[strategy](plan, goal_analysis, context)
        else:
            logger.warning(f"Unknown planning strategy: {strategy}, using hierarchical")
            await self._plan_hierarchical(plan, goal_analysis, context)
        
        # Enhanced autonomous planning
        await self._enhance_with_autonomous_planning(plan, goal_analysis, context)
        
        plan.status = WorkflowStatus.READY
        
        logger.info(f"Created autonomous workflow plan with {len(plan.steps)} steps")
        return plan
    
    async def _enhance_with_autonomous_planning(
        self,
        plan: WorkflowPlan,
        goal_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Enhance workflow plan with autonomous planning capabilities."""
        
        # 1. Intelligent dependency analysis
        dependencies = self.dependency_analyzer.analyze_dependencies(plan.steps)
        plan.dependencies = dependencies
        
        # 2. Create optimal schedule
        schedule = self.task_scheduler.create_schedule(plan.steps, dependencies)
        plan.schedule = schedule
        
        # 3. Create milestones for progress tracking
        milestones = self.milestone_tracker.create_milestones(plan)
        plan.milestones = milestones
        
        # 4. Estimate durations with advanced analysis
        self._estimate_durations_advanced(plan, schedule)
        
        # 5. Create intelligent checkpoints
        self._create_intelligent_checkpoints(plan, schedule)
        
        # 6. Add risk mitigation planning
        self._add_risk_mitigation_planning(plan, goal_analysis)
    
    async def _analyze_goal(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a goal to understand its complexity and requirements."""
        analysis = {
            "complexity": "medium",
            "risk_level": RiskLevel.MEDIUM,
            "estimated_steps": 5,
            "required_capabilities": [],
            "potential_issues": [],
            "success_criteria": []
        }
        
        goal_lower = goal.lower()
        
        # Analyze complexity
        complexity_indicators = {
            "simple": ["fix", "update", "change", "modify"],
            "medium": ["implement", "create", "build", "develop"],
            "complex": ["design", "architect", "refactor", "migrate", "integrate"]
        }
        
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in goal_lower for indicator in indicators):
                analysis["complexity"] = complexity
                break
        
        # Analyze risk level
        high_risk_indicators = ["delete", "remove", "migrate", "refactor", "production"]
        if any(indicator in goal_lower for indicator in high_risk_indicators):
            analysis["risk_level"] = RiskLevel.HIGH
        
        # Estimate steps based on complexity
        if analysis["complexity"] == "simple":
            analysis["estimated_steps"] = 3
        elif analysis["complexity"] == "complex":
            analysis["estimated_steps"] = 10
        
        # Identify required capabilities
        capability_keywords = {
            "code": ["code", "implement", "develop", "program"],
            "test": ["test", "verify", "validate", "check"],
            "security": ["security", "secure", "vulnerability", "auth"],
            "performance": ["performance", "optimize", "speed", "efficient"],
            "documentation": ["document", "doc", "readme", "guide"]
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in goal_lower for keyword in keywords):
                analysis["required_capabilities"].append(capability)
        
        return analysis
    
    async def _plan_hierarchical(
        self,
        plan: WorkflowPlan,
        goal_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Plan using hierarchical decomposition."""
        # Break down goal into major phases
        phases = self._identify_phases(plan.goal, goal_analysis)
        
        for phase_name, phase_description in phases.items():
            # Create phase step
            phase_step = WorkflowStep(
                name=phase_name,
                description=phase_description,
                risk_level=goal_analysis["risk_level"]
            )
            
            # Decompose phase into tasks
            phase_tasks = await self._decompose_phase(phase_description, goal_analysis, context)
            
            for task_desc in phase_tasks:
                task_step = WorkflowStep(
                    name=f"{phase_name} - {task_desc[:30]}...",
                    description=task_desc,
                    task=Task(
                        description=task_desc,
                        task_type=self._infer_task_type(task_desc),
                        priority=TaskPriority.MEDIUM,
                        context=context
                    ),
                    dependencies=[phase_step.id] if plan.steps else [],
                    risk_level=self._assess_task_risk(task_desc)
                )
                plan.steps.append(task_step)
            
            plan.steps.append(phase_step)
    
    async def _plan_sequential(
        self,
        plan: WorkflowPlan,
        goal_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Plan using sequential task decomposition."""
        tasks = await self._decompose_goal_sequentially(plan.goal, goal_analysis, context)
        
        previous_step_id = None
        for i, task_desc in enumerate(tasks):
            step = WorkflowStep(
                name=f"Step {i+1}",
                description=task_desc,
                task=Task(
                    description=task_desc,
                    task_type=self._infer_task_type(task_desc),
                    priority=TaskPriority.MEDIUM,
                    context=context
                ),
                dependencies=[previous_step_id] if previous_step_id else [],
                risk_level=self._assess_task_risk(task_desc)
            )
            
            plan.steps.append(step)
            previous_step_id = step.id
    
    async def _plan_parallel(
        self,
        plan: WorkflowPlan,
        goal_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Plan using parallel task decomposition."""
        tasks = await self._decompose_goal_parallel(plan.goal, goal_analysis, context)
        
        for i, task_desc in enumerate(tasks):
            step = WorkflowStep(
                name=f"Parallel Task {i+1}",
                description=task_desc,
                task=Task(
                    description=task_desc,
                    task_type=self._infer_task_type(task_desc),
                    priority=TaskPriority.MEDIUM,
                    context=context
                ),
                dependencies=[],  # No dependencies for parallel execution
                risk_level=self._assess_task_risk(task_desc)
            )
            
            plan.steps.append(step)
    
    async def _plan_hybrid(
        self,
        plan: WorkflowPlan,
        goal_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Plan using hybrid approach combining multiple strategies."""
        # Start with hierarchical decomposition
        await self._plan_hierarchical(plan, goal_analysis, context)
        
        # Identify opportunities for parallelization
        self._optimize_for_parallelization(plan)
    
    def _identify_phases(self, goal: str, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Identify major phases for a goal."""
        phases = {}
        
        goal_lower = goal.lower()
        
        # Common development phases
        if any(word in goal_lower for word in ["implement", "create", "build", "develop"]):
            phases["Planning"] = "Analyze requirements and create implementation plan"
            phases["Implementation"] = "Implement the core functionality"
            phases["Testing"] = "Test and validate the implementation"
            phases["Documentation"] = "Create documentation and finalize"
        
        # Refactoring phases
        elif any(word in goal_lower for word in ["refactor", "improve", "optimize"]):
            phases["Analysis"] = "Analyze current code and identify improvements"
            phases["Refactoring"] = "Apply refactoring changes"
            phases["Validation"] = "Validate that functionality is preserved"
        
        # Bug fixing phases
        elif any(word in goal_lower for word in ["fix", "debug", "resolve"]):
            phases["Investigation"] = "Investigate and identify root cause"
            phases["Fix"] = "Implement the fix"
            phases["Verification"] = "Verify the fix works correctly"
        
        # Default phases
        else:
            phases["Preparation"] = "Prepare for task execution"
            phases["Execution"] = "Execute the main task"
            phases["Completion"] = "Complete and verify the task"
        
        return phases
    
    async def _decompose_phase(
        self,
        phase_description: str,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Decompose a phase into specific tasks."""
        tasks = []
        
        phase_lower = phase_description.lower()
        
        if "planning" in phase_lower or "analysis" in phase_lower:
            tasks.extend([
                "Analyze existing codebase and requirements",
                "Identify key components and dependencies",
                "Create detailed implementation strategy"
            ])
        
        elif "implementation" in phase_lower or "execution" in phase_lower:
            tasks.extend([
                "Set up necessary project structure",
                "Implement core functionality",
                "Handle edge cases and error conditions"
            ])
        
        elif "testing" in phase_lower or "validation" in phase_lower:
            tasks.extend([
                "Create comprehensive test cases",
                "Run tests and validate functionality",
                "Fix any issues found during testing"
            ])
        
        elif "documentation" in phase_lower:
            tasks.extend([
                "Create user documentation",
                "Add code comments and docstrings",
                "Update project README and guides"
            ])
        
        else:
            # Generic task decomposition
            tasks.extend([
                f"Prepare for {phase_description.lower()}",
                f"Execute {phase_description.lower()}",
                f"Verify {phase_description.lower()} completion"
            ])
        
        return tasks
    
    async def _decompose_goal_sequentially(
        self,
        goal: str,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Decompose goal into sequential tasks."""
        tasks = []
        
        # Add preparation task
        tasks.append(f"Prepare environment and dependencies for: {goal}")
        
        # Add main implementation tasks based on complexity
        if analysis["complexity"] == "simple":
            tasks.extend([
                f"Implement solution for: {goal}",
                f"Test and validate: {goal}"
            ])
        elif analysis["complexity"] == "medium":
            tasks.extend([
                f"Design approach for: {goal}",
                f"Implement core functionality for: {goal}",
                f"Add error handling and edge cases",
                f"Test and validate implementation"
            ])
        else:  # complex
            tasks.extend([
                f"Research and analyze requirements for: {goal}",
                f"Design architecture for: {goal}",
                f"Implement core components",
                f"Integrate components and handle dependencies",
                f"Comprehensive testing and validation",
                f"Documentation and finalization"
            ])
        
        return tasks
    
    async def _decompose_goal_parallel(
        self,
        goal: str,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Decompose goal into parallel tasks."""
        tasks = []
        
        # Identify parallelizable aspects
        capabilities = analysis.get("required_capabilities", [])
        
        for capability in capabilities:
            if capability == "code":
                tasks.append(f"Implement code components for: {goal}")
            elif capability == "test":
                tasks.append(f"Create test suite for: {goal}")
            elif capability == "documentation":
                tasks.append(f"Create documentation for: {goal}")
            elif capability == "security":
                tasks.append(f"Implement security measures for: {goal}")
            elif capability == "performance":
                tasks.append(f"Optimize performance for: {goal}")
        
        # If no specific capabilities identified, create generic parallel tasks
        if not tasks:
            tasks.extend([
                f"Implement main functionality for: {goal}",
                f"Create tests for: {goal}",
                f"Add documentation for: {goal}"
            ])
        
        return tasks
    
    def _infer_task_type(self, task_description: str) -> str:
        """Infer task type from description."""
        desc_lower = task_description.lower()
        
        if any(word in desc_lower for word in ["test", "validate", "verify"]):
            return "testing"
        elif any(word in desc_lower for word in ["document", "doc", "readme"]):
            return "documentation"
        elif any(word in desc_lower for word in ["security", "secure", "auth"]):
            return "security"
        elif any(word in desc_lower for word in ["optimize", "performance", "speed"]):
            return "performance"
        elif any(word in desc_lower for word in ["implement", "code", "develop"]):
            return "code_generation"
        elif any(word in desc_lower for word in ["design", "architect", "plan"]):
            return "architecture_design"
        else:
            return "general"
    
    def _assess_task_risk(self, task_description: str) -> RiskLevel:
        """Assess risk level for a task."""
        desc_lower = task_description.lower()
        
        high_risk_keywords = ["delete", "remove", "migrate", "refactor", "production", "deploy"]
        medium_risk_keywords = ["modify", "change", "update", "integrate"]
        
        if any(keyword in desc_lower for keyword in high_risk_keywords):
            return RiskLevel.HIGH
        elif any(keyword in desc_lower for keyword in medium_risk_keywords):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_dependencies(self, plan: WorkflowPlan) -> None:
        """Calculate and optimize dependencies between steps."""
        # Build dependency graph
        for step in plan.steps:
            plan.dependencies[step.id] = step.dependencies.copy()
        
        # Optimize dependencies (remove redundant ones)
        self._optimize_dependencies(plan)
    
    def _optimize_dependencies(self, plan: WorkflowPlan) -> None:
        """Optimize dependencies to remove redundant ones."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated dependency optimization
        pass
    
    def _estimate_durations(self, plan: WorkflowPlan) -> None:
        """Estimate duration for each step and overall plan."""
        total_duration = 0.0
        
        for step in plan.steps:
            # Base estimation on task complexity and type
            if step.task:
                task_type = step.task.task_type
                base_duration = {
                    "testing": 30.0,
                    "documentation": 45.0,
                    "security": 60.0,
                    "performance": 90.0,
                    "code_generation": 120.0,
                    "architecture_design": 180.0,
                    "general": 60.0
                }.get(task_type, 60.0)
                
                # Adjust for risk level
                risk_multiplier = {
                    RiskLevel.LOW: 1.0,
                    RiskLevel.MEDIUM: 1.5,
                    RiskLevel.HIGH: 2.0,
                    RiskLevel.CRITICAL: 3.0
                }.get(step.risk_level, 1.0)
                
                step.estimated_duration = base_duration * risk_multiplier
            
            total_duration += step.estimated_duration
        
        plan.estimated_duration = total_duration
    
    def _create_checkpoints(self, plan: WorkflowPlan) -> None:
        """Create checkpoints for rollback capability."""
        # Create checkpoints at key milestones
        checkpoint_intervals = max(1, len(plan.steps) // 4)  # Every 25% of steps
        
        for i in range(0, len(plan.steps), checkpoint_intervals):
            if i < len(plan.steps):
                step = plan.steps[i]
                checkpoint = Checkpoint(
                    workflow_id=plan.id,
                    step_id=step.id,
                    description=f"Checkpoint after {step.name}"
                )
                plan.checkpoints.append(checkpoint)
    
    def _optimize_for_parallelization(self, plan: WorkflowPlan) -> None:
        """Optimize plan for parallel execution where possible."""
        # Identify steps that can run in parallel
        # This is a simplified implementation
        independent_steps = []
        
        for step in plan.steps:
            if not step.dependencies:
                independent_steps.append(step)
        
        # Group independent steps for parallel execution
        # Implementation would depend on specific requirements
    
    def _estimate_durations_advanced(self, plan: WorkflowPlan, schedule: Dict[str, Any]) -> None:
        """Advanced duration estimation using schedule analysis."""
        # Use schedule information to refine estimates
        if "total_estimated_time" in schedule:
            plan.estimated_duration = schedule["total_estimated_time"]
        
        # Adjust individual step estimates based on dependencies and resources
        for step in plan.steps:
            # Find step in schedule batches
            for batch in schedule.get("batches", []):
                for task_info in batch.get("tasks", []):
                    if task_info["task_id"] == step.id:
                        # Use scheduled duration if available
                        step.estimated_duration = task_info["end_time"] - task_info["start_time"]
                        break
    
    def _create_intelligent_checkpoints(self, plan: WorkflowPlan, schedule: Dict[str, Any]) -> None:
        """Create intelligent checkpoints based on schedule and risk analysis."""
        checkpoints = []
        
        # Create checkpoints at critical path milestones
        critical_path = schedule.get("critical_path", [])
        
        for i, step_id in enumerate(critical_path):
            if i % 3 == 0:  # Every 3rd step on critical path
                step = next((s for s in plan.steps if s.id == step_id), None)
                if step:
                    checkpoint = Checkpoint(
                        workflow_id=plan.id,
                        step_id=step.id,
                        description=f"Critical path checkpoint at {step.name}"
                    )
                    checkpoints.append(checkpoint)
        
        # Add checkpoints before high-risk steps
        for step in plan.steps:
            if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                checkpoint = Checkpoint(
                    workflow_id=plan.id,
                    step_id=step.id,
                    description=f"Pre-risk checkpoint before {step.name}"
                )
                checkpoints.append(checkpoint)
        
        plan.checkpoints = checkpoints
    
    def _add_risk_mitigation_planning(self, plan: WorkflowPlan, goal_analysis: Dict[str, Any]) -> None:
        """Add risk mitigation strategies to the workflow plan."""
        mitigation_strategies = []
        
        # Analyze overall workflow risk
        high_risk_steps = [step for step in plan.steps if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        if high_risk_steps:
            mitigation_strategies.extend([
                "Create backup before executing high-risk steps",
                "Implement rollback mechanisms for critical operations",
                "Add user approval gates for high-risk operations",
                "Monitor execution closely with automated alerts"
            ])
        
        # Add specific mitigations based on goal analysis
        if "potential_issues" in goal_analysis:
            for issue in goal_analysis["potential_issues"]:
                mitigation_strategies.append(f"Mitigate risk: {issue}")
        
        plan.risk_mitigation_strategies = mitigation_strategies


class ExecutionEngine:
    """Executes workflow plans with monitoring and error handling."""
    
    def __init__(self, agent_coordinator: AgentCoordinator):
        self.agent_coordinator = agent_coordinator
        self.active_workflows: Dict[str, WorkflowPlan] = {}
        self.execution_history: List[WorkflowPlan] = []
        
        # Rollback and recovery capabilities
        self.checkpoint_manager = CheckpointManager()
        self.rollback_manager = RollbackManager()
        self.state_manager = StateManager()
        self.recovery_engine = RecoveryEngine()
        
        # User intervention and approval capabilities
        self.intervention_manager = UserInterventionManager()
        self.approval_manager = ApprovalWorkflowManager(self.intervention_manager)
        self.notification_manager = NotificationManager()
        self.override_manager = ManualOverrideManager()
        
        logger.info("Initialized ExecutionEngine with rollback and intervention capabilities")
    
    async def execute_workflow(self, plan: WorkflowPlan) -> bool:
        """
        Execute a workflow plan with rollback capabilities.
        
        Args:
            plan: The workflow plan to execute
            
        Returns:
            True if execution was successful, False otherwise
        """
        logger.info(f"Starting execution of workflow with rollback: {plan.name}")
        
        plan.status = WorkflowStatus.EXECUTING
        plan.started_at = time.time()
        self.active_workflows[plan.id] = plan
        
        # Initialize state management
        self.state_manager.initialize_workflow_state(plan)
        
        # Send workflow start notification
        self.notification_manager.send_notification(
            workflow_id=plan.id,
            notification_type="workflow_started",
            title=f"Workflow Started: {plan.name}",
            message=f"Autonomous workflow execution has begun for: {plan.goal}",
            priority="normal"
        )
        
        try:
            # Execute workflow with safe execution and checkpointing
            success = await self._execute_workflow_with_rollback(plan)
            
            # Update workflow status
            plan.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
            plan.success = success
            plan.completed_at = time.time()
            plan.actual_duration = plan.completed_at - plan.started_at
            
            # Clean up state
            self.state_manager.cleanup_workflow_state(plan.id)
            
            # Move to history
            self.execution_history.append(plan)
            del self.active_workflows[plan.id]
            
            logger.info(f"Workflow execution completed with success: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            
            # Attempt recovery
            recovery_success = await self._handle_workflow_failure(plan, e)
            
            plan.status = WorkflowStatus.FAILED
            plan.errors.append(str(e))
            plan.completed_at = time.time()
            plan.actual_duration = plan.completed_at - plan.started_at
            
            # Clean up state
            self.state_manager.cleanup_workflow_state(plan.id)
            
            # Move to history
            self.execution_history.append(plan)
            del self.active_workflows[plan.id]
            
            return recovery_success
    
    async def _execute_workflow_with_rollback(self, plan: WorkflowPlan) -> bool:
        """Execute workflow with checkpointing and rollback capabilities."""
        
        # Create initial checkpoint
        initial_state = self.state_manager.create_state_snapshot(plan.id)
        initial_checkpoint = self.checkpoint_manager.create_checkpoint(
            plan.id,
            "initial",
            initial_state,
            "Initial workflow state"
        )
        
        # Execute steps with checkpointing
        for i, step in enumerate(plan.steps):
            try:
                # Update state for step start
                self.state_manager.update_step_state(plan.id, step, "started")
                
                # Create checkpoint before high-risk steps
                if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    current_state = self.state_manager.create_state_snapshot(plan.id)
                    checkpoint = self.checkpoint_manager.create_checkpoint(
                        plan.id,
                        step.id,
                        current_state,
                        f"Pre-execution checkpoint for {step.name}"
                    )
                
                # Request approval for critical operations
                if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    approval_result = await self.approval_manager.request_approval(
                        plan.id, step, "step_execution"
                    )
                    
                    if not approval_result["approved"]:
                        if approval_result["action"] == "pause":
                            plan.status = WorkflowStatus.PAUSED
                            return False
                        elif approval_result["action"] == "skip":
                            logger.info(f"Skipping step {step.name} due to user rejection")
                            continue
                        else:
                            return False
                
                # Execute the step
                result = await self._execute_step_safely(step, plan)
                
                # Update state for step completion
                self.state_manager.update_step_state(plan.id, step, "completed", result)
                
                # Send progress update
                progress = ((i + 1) / len(plan.steps)) * 100
                self.notification_manager.send_progress_update(
                    workflow_id=plan.id,
                    progress_percentage=progress,
                    current_step=step.name
                )
                
                if not result.success:
                    # Handle step failure with recovery
                    recovery_action = await self._handle_step_failure(step, plan, result)
                    
                    if recovery_action["action"] == "rollback":
                        rollback_success = await self._perform_rollback(plan.id, recovery_action)
                        if not rollback_success:
                            return False
                    
                    elif recovery_action["action"] == "skip":
                        logger.info(f"Skipping failed step: {step.name}")
                        continue
                    
                    elif recovery_action["action"] == "retry":
                        # Retry the step
                        retry_result = await self._retry_step(step, plan, recovery_action)
                        if not retry_result.success:
                            return False
                
                # Create periodic checkpoints
                if i % 3 == 0 and i > 0:  # Every 3 steps
                    current_state = self.state_manager.create_state_snapshot(plan.id)
                    self.checkpoint_manager.create_checkpoint(
                        plan.id,
                        step.id,
                        current_state,
                        f"Periodic checkpoint after step {i+1}"
                    )
                
            except Exception as e:
                logger.error(f"Error executing step {step.name}: {e}")
                
                # Handle step failure
                workflow_state = self.state_manager.get_current_state(plan.id)
                recovery_action = await self.recovery_engine.handle_step_failure(
                    step, e, workflow_state
                )
                
                if recovery_action["action"] == "rollback":
                    rollback_success = await self._perform_rollback(plan.id, recovery_action)
                    if not rollback_success:
                        return False
                else:
                    # Update state for step failure
                    self.state_manager.update_step_state(plan.id, step, "failed")
                    
                    if recovery_action["action"] != "skip":
                        return False
        
        return True
    
    async def _execute_step_safely(self, step: WorkflowStep, plan: WorkflowPlan) -> AgentResult:
        """Execute a single step safely with error handling."""
        try:
            if step.task:
                # Execute through agent coordinator
                coordination_plan = await self._create_step_coordination_plan(step, plan)
                success = await self.agent_coordinator.execute_coordination_plan(coordination_plan)
                
                return AgentResult(
                    agent_name="workflow_engine",
                    task_id=step.task.id,
                    success=success,
                    output=f"Step {step.name} executed",
                    confidence=0.9 if success else 0.1,
                    reasoning=f"Executed step: {step.description}"
                )
            else:
                # Direct step execution
                return AgentResult(
                    agent_name="workflow_engine",
                    task_id=step.id,
                    success=True,
                    output=f"Step {step.name} completed",
                    confidence=0.8,
                    reasoning=f"Direct execution: {step.description}"
                )
                
        except Exception as e:
            return AgentResult(
                agent_name="workflow_engine",
                task_id=step.task.id if step.task else step.id,
                success=False,
                output=None,
                confidence=0.0,
                reasoning=f"Step execution failed: {str(e)}",
                error=str(e)
            )
    
    async def _create_step_coordination_plan(self, step: WorkflowStep, plan: WorkflowPlan):
        """Create coordination plan for a single step."""
        # This would create a coordination plan for the specific step
        # Implementation depends on the agent coordinator interface
        return None
    
    async def _handle_step_failure(
        self,
        step: WorkflowStep,
        plan: WorkflowPlan,
        result: AgentResult
    ) -> Dict[str, Any]:
        """Handle failure of a workflow step."""
        workflow_state = self.state_manager.get_current_state(plan.id)
        
        # Create exception from result
        error = Exception(result.error or f"Step {step.name} failed")
        
        # Use recovery engine to determine action
        recovery_action = await self.recovery_engine.handle_step_failure(
            step, error, workflow_state
        )
        
        return recovery_action
    
    async def _perform_rollback(self, workflow_id: str, recovery_action: Dict[str, Any]) -> bool:
        """Perform rollback operation."""
        try:
            if recovery_action.get("rollback_target") == "latest_checkpoint":
                checkpoint = self.checkpoint_manager.get_latest_checkpoint(workflow_id)
                if checkpoint:
                    checkpoint_data = self.checkpoint_manager.get_checkpoint_data(checkpoint.id)
                    if checkpoint_data:
                        return await self.rollback_manager.rollback_to_checkpoint(
                            checkpoint, checkpoint_data
                        )
            
            return False
            
        except Exception as e:
            logger.error(f"Error performing rollback for workflow {workflow_id}: {e}")
            return False
    
    async def _retry_step(
        self,
        step: WorkflowStep,
        plan: WorkflowPlan,
        recovery_action: Dict[str, Any]
    ) -> AgentResult:
        """Retry a failed step with backoff."""
        delay = recovery_action.get("delay", 1)
        
        logger.info(f"Retrying step {step.name} after {delay} seconds")
        await asyncio.sleep(delay)
        
        return await self._execute_step_safely(step, plan)
    
    async def _handle_workflow_failure(self, plan: WorkflowPlan, error: Exception) -> bool:
        """Handle overall workflow failure."""
        try:
            # Attempt to rollback to latest checkpoint
            checkpoint = self.checkpoint_manager.get_latest_checkpoint(plan.id)
            if checkpoint:
                checkpoint_data = self.checkpoint_manager.get_checkpoint_data(checkpoint.id)
                if checkpoint_data:
                    rollback_success = await self.rollback_manager.rollback_to_checkpoint(
                        checkpoint, checkpoint_data
                    )
                    
                    if rollback_success:
                        logger.info(f"Successfully rolled back workflow {plan.id} after failure")
                        return True
            
            logger.error(f"Could not recover workflow {plan.id} from failure: {error}")
            return False
            
        except Exception as e:
            logger.error(f"Error handling workflow failure for {plan.id}: {e}")
            return False
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """
        Pause an active workflow.
        
        Args:
            workflow_id: ID of the workflow to pause
            
        Returns:
            True if paused successfully, False otherwise
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Cannot pause workflow {workflow_id}: not found")
            return False
        
        plan = self.active_workflows[workflow_id]
        plan.status = WorkflowStatus.PAUSED
        
        logger.info(f"Paused workflow: {plan.name}")
        return True
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resume a paused workflow.
        
        Args:
            workflow_id: ID of the workflow to resume
            
        Returns:
            True if resumed successfully, False otherwise
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Cannot resume workflow {workflow_id}: not found")
            return False
        
        plan = self.active_workflows[workflow_id]
        if plan.status != WorkflowStatus.PAUSED:
            logger.warning(f"Cannot resume workflow {workflow_id}: not paused")
            return False
        
        plan.status = WorkflowStatus.EXECUTING
        
        logger.info(f"Resumed workflow: {plan.name}")
        return True
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel an active workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if workflow_id not in self.active_workflows:
            logger.warning(f"Cannot cancel workflow {workflow_id}: not found")
            return False
        
        plan = self.active_workflows[workflow_id]
        plan.status = WorkflowStatus.CANCELLED
        plan.completed_at = time.time()
        plan.actual_duration = plan.completed_at - plan.started_at
        
        # Move to history
        self.execution_history.append(plan)
        del self.active_workflows[workflow_id]
        
        logger.info(f"Cancelled workflow: {plan.name}")
        return True
    
    async def _create_coordination_plan(self, workflow_plan: WorkflowPlan) -> CoordinationPlan:
        """Create a coordination plan from a workflow plan."""
        # Convert workflow steps to tasks
        tasks = []
        for step in workflow_plan.steps:
            if step.task:
                tasks.append(step.task)
        
        # Determine coordination strategy
        strategy = self._determine_coordination_strategy(workflow_plan)
        
        # Create coordination plan
        coordination_plan = await self.agent_coordinator.coordinate_complex_task(
            description=workflow_plan.description,
            subtasks=tasks,
            strategy=strategy,
            dependencies=workflow_plan.dependencies
        )
        
        return coordination_plan
    
    def _determine_coordination_strategy(self, plan: WorkflowPlan) -> CoordinationStrategy:
        """Determine the best coordination strategy for a workflow."""
        # Analyze dependencies to determine strategy
        has_dependencies = any(step.dependencies for step in plan.steps)
        
        if not has_dependencies:
            return CoordinationStrategy.PARALLEL
        elif plan.overall_risk == RiskLevel.HIGH:
            return CoordinationStrategy.SEQUENTIAL
        else:
            return CoordinationStrategy.PIPELINE
    
    def get_active_workflows(self) -> List[WorkflowPlan]:
        """Get list of active workflows."""
        return list(self.active_workflows.values())
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow."""
        if workflow_id in self.active_workflows:
            plan = self.active_workflows[workflow_id]
        else:
            # Check history
            plan = next((p for p in self.execution_history if p.id == workflow_id), None)
        
        if not plan:
            return None
        
        return {
            "id": plan.id,
            "name": plan.name,
            "status": plan.status.value,
            "progress": self._calculate_progress(plan),
            "estimated_duration": plan.estimated_duration,
            "actual_duration": plan.actual_duration,
            "success": plan.success,
            "errors": plan.errors
        }
    
    def _calculate_progress(self, plan: WorkflowPlan) -> float:
        """Calculate progress percentage for a workflow."""
        if not plan.steps:
            return 0.0
        
        completed_steps = sum(1 for step in plan.steps if step.status == WorkflowStatus.COMPLETED)
        return (completed_steps / len(plan.steps)) * 100.0
    
    async def rollback_workflow(self, workflow_id: str, checkpoint_id: str = None) -> bool:
        """
        Rollback a workflow to a specific checkpoint.
        
        Args:
            workflow_id: ID of the workflow to rollback
            checkpoint_id: Specific checkpoint ID, or None for latest
            
        Returns:
            True if rollback was successful, False otherwise
        """
        try:
            if checkpoint_id:
                checkpoint_data = self.checkpoint_manager.get_checkpoint_data(checkpoint_id)
                if not checkpoint_data:
                    logger.error(f"Checkpoint {checkpoint_id} not found")
                    return False
                
                checkpoint = checkpoint_data["checkpoint"]
            else:
                checkpoint = self.checkpoint_manager.get_latest_checkpoint(workflow_id)
                if not checkpoint:
                    logger.error(f"No checkpoints found for workflow {workflow_id}")
                    return False
                
                checkpoint_data = self.checkpoint_manager.get_checkpoint_data(checkpoint.id)
            
            # Perform rollback
            rollback_success = await self.rollback_manager.rollback_to_checkpoint(
                checkpoint, checkpoint_data
            )
            
            if rollback_success:
                # Restore workflow state
                state_snapshot = checkpoint.state_snapshot
                self.state_manager.restore_state_snapshot(workflow_id, state_snapshot)
                
                logger.info(f"Successfully rolled back workflow {workflow_id} to checkpoint {checkpoint.id}")
            
            return rollback_success
            
        except Exception as e:
            logger.error(f"Error rolling back workflow {workflow_id}: {e}")
            return False
    
    def get_rollback_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get rollback history for a workflow."""
        return self.rollback_manager.get_rollback_history(workflow_id)
    
    def get_checkpoints(self, workflow_id: str) -> List[Checkpoint]:
        """Get all checkpoints for a workflow."""
        return self.checkpoint_manager.get_checkpoints(workflow_id)
    
    def create_intervention_point(
        self,
        workflow_id: str,
        step_id: str,
        message: str,
        options: List[str] = None
    ) -> str:
        """Create a user intervention point."""
        return self.intervention_manager.create_intervention_point(
            workflow_id, step_id, "user_input", message, options
        )
    
    def respond_to_intervention(self, intervention_id: str, response: str) -> bool:
        """Respond to a user intervention."""
        return self.intervention_manager.respond_to_intervention(intervention_id, response)
    
    def get_pending_interventions(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get pending interventions."""
        return self.intervention_manager.get_pending_interventions(workflow_id)
    
    def get_pending_approvals(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get pending approval requests."""
        return self.approval_manager.get_pending_approvals(workflow_id)
    
    def configure_approval_rules(self, rules: Dict[str, Dict[str, Any]]) -> None:
        """Configure approval rules."""
        self.approval_manager.configure_approval_rules(rules)
    
    def register_notification_handler(self, handler: Callable) -> None:
        """Register a notification handler."""
        self.notification_manager.register_notification_handler(handler)
    
    def request_manual_override(
        self,
        workflow_id: str,
        step_id: str,
        operation_type: str,
        reason: str
    ) -> str:
        """Request manual override for an operation."""
        return self.override_manager.request_manual_override(
            workflow_id, step_id, operation_type, reason
        )
    
    async def execute_manual_override(
        self,
        override_id: str,
        user_instructions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a manual override."""
        return await self.override_manager.execute_manual_override(override_id, user_instructions)


class RiskAssessor:
    """Assesses and manages risks in workflow execution."""
    
    def __init__(self):
        self.risk_patterns: Dict[str, RiskLevel] = {
            "delete": RiskLevel.HIGH,
            "remove": RiskLevel.HIGH,
            "drop": RiskLevel.HIGH,
            "truncate": RiskLevel.CRITICAL,
            "format": RiskLevel.CRITICAL,
            "migrate": RiskLevel.HIGH,
            "refactor": RiskLevel.MEDIUM,
            "deploy": RiskLevel.MEDIUM,
            "production": RiskLevel.HIGH
        }
        
        logger.info("Initialized RiskAssessor")
    
    def assess_workflow_risk(self, plan: WorkflowPlan) -> RiskLevel:
        """
        Assess overall risk level for a workflow.
        
        Args:
            plan: The workflow plan to assess
            
        Returns:
            Overall risk level for the workflow
        """
        max_risk = RiskLevel.LOW
        
        for step in plan.steps:
            step_risk = self.assess_step_risk(step)
            if step_risk.value > max_risk.value:
                max_risk = step_risk
        
        plan.overall_risk = max_risk
        return max_risk
    
    def assess_step_risk(self, step: WorkflowStep) -> RiskLevel:
        """
        Assess risk level for a workflow step.
        
        Args:
            step: The workflow step to assess
            
        Returns:
            Risk level for the step
        """
        if step.risk_level != RiskLevel.LOW:
            return step.risk_level
        
        # Analyze step description for risk patterns
        desc_lower = step.description.lower()
        
        for pattern, risk_level in self.risk_patterns.items():
            if pattern in desc_lower:
                step.risk_level = risk_level
                return risk_level
        
        # Check task context for additional risk factors
        if step.task and step.task.context:
            context = step.task.context
            
            if context.get("affects_production", False):
                step.risk_level = RiskLevel.HIGH
                return RiskLevel.HIGH
            
            if context.get("modifies_data", False):
                step.risk_level = RiskLevel.MEDIUM
                return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def create_risk_mitigation_plan(self, plan: WorkflowPlan) -> Dict[str, Any]:
        """
        Create a risk mitigation plan for a workflow.
        
        Args:
            plan: The workflow plan to create mitigation for
            
        Returns:
            Risk mitigation plan
        """
        mitigation_plan = {
            "overall_risk": plan.overall_risk.value,
            "high_risk_steps": [],
            "mitigation_strategies": [],
            "rollback_points": [],
            "monitoring_requirements": []
        }
        
        for step in plan.steps:
            step_risk = self.assess_step_risk(step)
            
            if step_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                mitigation_plan["high_risk_steps"].append({
                    "step_id": step.id,
                    "name": step.name,
                    "risk_level": step_risk.value,
                    "description": step.description
                })
                
                # Add specific mitigation strategies
                if step_risk == RiskLevel.CRITICAL:
                    mitigation_plan["mitigation_strategies"].extend([
                        f"Create backup before {step.name}",
                        f"Require manual approval for {step.name}",
                        f"Test {step.name} in staging environment first"
                    ])
                    mitigation_plan["rollback_points"].append(step.id)
                
                elif step_risk == RiskLevel.HIGH:
                    mitigation_plan["mitigation_strategies"].extend([
                        f"Create checkpoint before {step.name}",
                        f"Monitor {step.name} execution closely"
                    ])
        
        # Add general monitoring requirements
        if plan.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            mitigation_plan["monitoring_requirements"].extend([
                "Real-time execution monitoring",
                "Automated rollback triggers",
                "User notification on critical steps"
            ])
        
        return mitigation_plan
    
    def should_require_approval(self, step: WorkflowStep) -> bool:
        """
        Determine if a step should require user approval.
        
        Args:
            step: The workflow step to check
            
        Returns:
            True if approval is required, False otherwise
        """
        step_risk = self.assess_step_risk(step)
        return step_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class WorkflowEngine:
    """Main workflow engine that coordinates planning, execution, and monitoring."""
    
    def __init__(self, agent_coordinator: AgentCoordinator):
        self.task_planner = TaskPlanner(agent_coordinator)
        self.execution_engine = ExecutionEngine(agent_coordinator)
        self.risk_assessor = RiskAssessor()
        self.agent_coordinator = agent_coordinator
        
        logger.info("Initialized WorkflowEngine")
    
    async def create_and_execute_workflow(
        self,
        goal: str,
        context: Dict[str, Any] = None,
        strategy: str = "hierarchical",
        auto_execute: bool = False
    ) -> WorkflowPlan:
        """
        Create and optionally execute a workflow for a goal.
        
        Args:
            goal: The goal to achieve
            context: Additional context
            strategy: Planning strategy
            auto_execute: Whether to execute automatically
            
        Returns:
            The created (and possibly executed) workflow plan
        """
        # Create workflow plan
        plan = await self.task_planner.create_workflow_plan(goal, context, strategy)
        
        # Assess risks
        risk_level = self.risk_assessor.assess_workflow_risk(plan)
        
        # Create risk mitigation plan
        mitigation_plan = self.risk_assessor.create_risk_mitigation_plan(plan)
        
        logger.info(f"Created workflow with risk level: {risk_level.value}")
        
        # Execute if requested and risk is acceptable
        if auto_execute and risk_level != RiskLevel.CRITICAL:
            success = await self.execution_engine.execute_workflow(plan)
            logger.info(f"Auto-executed workflow with success: {success}")
        
        return plan
    
    async def execute_workflow(self, plan: WorkflowPlan) -> bool:
        """Execute a workflow plan."""
        return await self.execution_engine.execute_workflow(plan)
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow engine statistics."""
        active_workflows = self.execution_engine.get_active_workflows()
        history = self.execution_engine.execution_history
        
        successful_workflows = sum(1 for w in history if w.success)
        total_workflows = len(history)
        
        return {
            "active_workflows": len(active_workflows),
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "success_rate": successful_workflows / max(total_workflows, 1),
            "average_duration": sum(w.actual_duration for w in history if w.actual_duration) / max(total_workflows, 1)
        }


class DependencyAnalyzer:
    """Analyzes and manages task dependencies for autonomous planning."""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        
        logger.info("Initialized DependencyAnalyzer")
    
    def analyze_dependencies(self, tasks: List[WorkflowStep]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between tasks and create dependency graph.
        
        Args:
            tasks: List of workflow steps to analyze
            
        Returns:
            Dictionary mapping task IDs to their dependencies
        """
        dependencies = {}
        
        # Build dependency graph
        for task in tasks:
            task_id = task.id
            dependencies[task_id] = []
            
            # Analyze task description for implicit dependencies
            implicit_deps = self._detect_implicit_dependencies(task, tasks)
            dependencies[task_id].extend(implicit_deps)
            
            # Add explicit dependencies
            dependencies[task_id].extend(task.dependencies)
            
            # Remove duplicates
            dependencies[task_id] = list(set(dependencies[task_id]))
        
        # Validate and optimize dependencies
        dependencies = self._optimize_dependencies(dependencies, tasks)
        
        return dependencies
    
    def _detect_implicit_dependencies(self, task: WorkflowStep, all_tasks: List[WorkflowStep]) -> List[str]:
        """Detect implicit dependencies based on task content and type."""
        implicit_deps = []
        task_desc = task.description.lower()
        
        # Common dependency patterns
        dependency_patterns = {
            "test": ["implement", "code", "develop"],  # Testing depends on implementation
            "deploy": ["test", "build", "package"],    # Deployment depends on testing
            "document": ["implement", "complete"],     # Documentation depends on implementation
            "integrate": ["implement", "test"],        # Integration depends on components
            "validate": ["implement", "test"],         # Validation depends on implementation
        }
        
        for other_task in all_tasks:
            if other_task.id == task.id:
                continue
            
            other_desc = other_task.description.lower()
            
            # Check for dependency patterns
            for dependent_keyword, prerequisite_keywords in dependency_patterns.items():
                if dependent_keyword in task_desc:
                    for prereq_keyword in prerequisite_keywords:
                        if prereq_keyword in other_desc:
                            implicit_deps.append(other_task.id)
                            break
        
        return implicit_deps
    
    def _optimize_dependencies(self, dependencies: Dict[str, List[str]], tasks: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Optimize dependencies by removing redundant ones."""
        optimized = {}
        
        for task_id, deps in dependencies.items():
            # Remove transitive dependencies
            direct_deps = []
            
            for dep in deps:
                is_transitive = False
                
                # Check if this dependency is reachable through another dependency
                for other_dep in deps:
                    if other_dep != dep and self._is_reachable(other_dep, dep, dependencies):
                        is_transitive = True
                        break
                
                if not is_transitive:
                    direct_deps.append(dep)
            
            optimized[task_id] = direct_deps
        
        return optimized
    
    def _is_reachable(self, start: str, target: str, dependencies: Dict[str, List[str]]) -> bool:
        """Check if target is reachable from start through dependencies."""
        visited = set()
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            if current == target:
                return True
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current in dependencies:
                queue.extend(dependencies[current])
        
        return False
    
    def get_execution_order(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """
        Get optimal execution order for tasks based on dependencies.
        
        Args:
            dependencies: Task dependencies mapping
            
        Returns:
            List of task batches that can be executed in parallel
        """
        # Topological sort with parallel batching
        in_degree = {}
        
        # Initialize in-degree count
        for task_id in dependencies:
            in_degree[task_id] = 0
        
        # Calculate in-degrees
        for task_id, deps in dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[task_id] += 1
        
        # Generate execution batches
        execution_order = []
        remaining_tasks = set(dependencies.keys())
        
        while remaining_tasks:
            # Find tasks with no dependencies
            ready_tasks = [task_id for task_id in remaining_tasks if in_degree[task_id] == 0]
            
            if not ready_tasks:
                # Circular dependency detected - break it
                ready_tasks = [min(remaining_tasks)]
                logger.warning(f"Circular dependency detected, forcing execution of {ready_tasks[0]}")
            
            execution_order.append(ready_tasks)
            
            # Remove ready tasks and update in-degrees
            for task_id in ready_tasks:
                remaining_tasks.remove(task_id)
                
                # Update in-degrees for dependent tasks
                for other_task, deps in dependencies.items():
                    if task_id in deps and other_task in remaining_tasks:
                        in_degree[other_task] -= 1
        
        return execution_order


class TaskScheduler:
    """Schedules tasks for optimal execution based on resources and constraints."""
    
    def __init__(self):
        self.resource_constraints: Dict[str, int] = {
            "cpu_intensive": 2,      # Max 2 CPU intensive tasks
            "memory_intensive": 1,   # Max 1 memory intensive task
            "io_intensive": 3,       # Max 3 I/O intensive tasks
            "network_intensive": 2   # Max 2 network intensive tasks
        }
        
        logger.info("Initialized TaskScheduler")
    
    def create_schedule(
        self,
        tasks: List[WorkflowStep],
        dependencies: Dict[str, List[str]],
        resource_constraints: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Create an optimal execution schedule for tasks.
        
        Args:
            tasks: List of workflow steps
            dependencies: Task dependencies
            resource_constraints: Resource constraints for scheduling
            
        Returns:
            Execution schedule with timing and resource allocation
        """
        if resource_constraints:
            self.resource_constraints.update(resource_constraints)
        
        # Analyze task resource requirements
        task_resources = self._analyze_task_resources(tasks)
        
        # Create dependency analyzer for execution order
        dependency_analyzer = DependencyAnalyzer()
        execution_batches = dependency_analyzer.get_execution_order(dependencies)
        
        # Schedule tasks within resource constraints
        schedule = {
            "batches": [],
            "total_estimated_time": 0.0,
            "resource_utilization": {},
            "critical_path": [],
            "parallel_opportunities": []
        }
        
        current_time = 0.0
        
        for batch_index, batch in enumerate(execution_batches):
            batch_schedule = self._schedule_batch(
                batch, tasks, task_resources, current_time
            )
            
            schedule["batches"].append(batch_schedule)
            current_time = batch_schedule["end_time"]
        
        schedule["total_estimated_time"] = current_time
        schedule["critical_path"] = self._find_critical_path(tasks, dependencies)
        schedule["parallel_opportunities"] = self._identify_parallel_opportunities(execution_batches, tasks)
        
        return schedule
    
    def _analyze_task_resources(self, tasks: List[WorkflowStep]) -> Dict[str, Dict[str, Any]]:
        """Analyze resource requirements for each task."""
        task_resources = {}
        
        for task in tasks:
            resources = {
                "cpu_intensive": False,
                "memory_intensive": False,
                "io_intensive": False,
                "network_intensive": False,
                "estimated_duration": task.estimated_duration
            }
            
            # Analyze task description for resource patterns
            desc_lower = task.description.lower()
            
            if any(keyword in desc_lower for keyword in ["compile", "build", "analyze", "process"]):
                resources["cpu_intensive"] = True
            
            if any(keyword in desc_lower for keyword in ["large", "dataset", "memory", "cache"]):
                resources["memory_intensive"] = True
            
            if any(keyword in desc_lower for keyword in ["file", "read", "write", "disk", "storage"]):
                resources["io_intensive"] = True
            
            if any(keyword in desc_lower for keyword in ["download", "upload", "api", "network", "remote"]):
                resources["network_intensive"] = True
            
            task_resources[task.id] = resources
        
        return task_resources
    
    def _schedule_batch(
        self,
        batch: List[str],
        tasks: List[WorkflowStep],
        task_resources: Dict[str, Dict[str, Any]],
        start_time: float
    ) -> Dict[str, Any]:
        """Schedule tasks within a batch considering resource constraints."""
        batch_schedule = {
            "batch_index": len(batch),
            "tasks": [],
            "start_time": start_time,
            "end_time": start_time,
            "resource_usage": {resource: 0 for resource in self.resource_constraints}
        }
        
        # Sort tasks by priority and resource requirements
        task_objects = [task for task in tasks if task.id in batch]
        task_objects.sort(key=lambda t: (t.risk_level.value, -t.estimated_duration))
        
        scheduled_tasks = []
        current_resources = {resource: 0 for resource in self.resource_constraints}
        
        for task in task_objects:
            resources = task_resources[task.id]
            
            # Check if task can be scheduled with current resource usage
            can_schedule = True
            required_resources = {}
            
            for resource_type, is_required in resources.items():
                if is_required and resource_type in self.resource_constraints:
                    if current_resources[resource_type] >= self.resource_constraints[resource_type]:
                        can_schedule = False
                        break
                    required_resources[resource_type] = 1
            
            if can_schedule:
                # Schedule the task
                task_schedule = {
                    "task_id": task.id,
                    "task_name": task.name,
                    "start_time": start_time,
                    "end_time": start_time + task.estimated_duration,
                    "resources": required_resources
                }
                
                scheduled_tasks.append(task_schedule)
                
                # Update resource usage
                for resource_type, usage in required_resources.items():
                    current_resources[resource_type] += usage
                
                # Update batch end time
                batch_schedule["end_time"] = max(
                    batch_schedule["end_time"],
                    task_schedule["end_time"]
                )
        
        batch_schedule["tasks"] = scheduled_tasks
        batch_schedule["resource_usage"] = current_resources
        
        return batch_schedule
    
    def _find_critical_path(self, tasks: List[WorkflowStep], dependencies: Dict[str, List[str]]) -> List[str]:
        """Find the critical path through the task dependency graph."""
        # Calculate longest path through dependency graph
        task_dict = {task.id: task for task in tasks}
        
        # Calculate earliest start times
        earliest_start = {}
        
        def calculate_earliest_start(task_id: str) -> float:
            if task_id in earliest_start:
                return earliest_start[task_id]
            
            if task_id not in dependencies or not dependencies[task_id]:
                earliest_start[task_id] = 0.0
                return 0.0
            
            max_predecessor_end = 0.0
            for dep_id in dependencies[task_id]:
                if dep_id in task_dict:
                    dep_end = calculate_earliest_start(dep_id) + task_dict[dep_id].estimated_duration
                    max_predecessor_end = max(max_predecessor_end, dep_end)
            
            earliest_start[task_id] = max_predecessor_end
            return max_predecessor_end
        
        # Calculate for all tasks
        for task in tasks:
            calculate_earliest_start(task.id)
        
        # Find critical path by following longest path
        critical_path = []
        
        # Start with task that has the latest finish time
        latest_task = max(tasks, key=lambda t: earliest_start[t.id] + t.estimated_duration)
        
        current_task = latest_task.id
        while current_task:
            critical_path.append(current_task)
            
            # Find predecessor on critical path
            next_task = None
            if current_task in dependencies:
                for dep_id in dependencies[current_task]:
                    if dep_id in task_dict:
                        dep_finish = earliest_start[dep_id] + task_dict[dep_id].estimated_duration
                        if abs(dep_finish - earliest_start[current_task]) < 0.1:  # On critical path
                            next_task = dep_id
                            break
            
            current_task = next_task
        
        critical_path.reverse()
        return critical_path
    
    def _identify_parallel_opportunities(
        self,
        execution_batches: List[List[str]],
        tasks: List[WorkflowStep]
    ) -> List[Dict[str, Any]]:
        """Identify opportunities for parallel execution."""
        opportunities = []
        
        for batch_index, batch in enumerate(execution_batches):
            if len(batch) > 1:
                opportunities.append({
                    "batch_index": batch_index,
                    "parallel_tasks": len(batch),
                    "task_ids": batch,
                    "estimated_time_saved": self._calculate_time_saved(batch, tasks)
                })
        
        return opportunities
    
    def _calculate_time_saved(self, batch: List[str], tasks: List[WorkflowStep]) -> float:
        """Calculate time saved by parallel execution."""
        task_dict = {task.id: task for task in tasks}
        
        total_sequential_time = sum(
            task_dict[task_id].estimated_duration
            for task_id in batch
            if task_id in task_dict
        )
        
        max_parallel_time = max(
            task_dict[task_id].estimated_duration
            for task_id in batch
            if task_id in task_dict
        ) if batch else 0.0
        
        return total_sequential_time - max_parallel_time


class MilestoneTracker:
    """Tracks milestones and progress in autonomous workflows."""
    
    def __init__(self):
        self.milestones: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Initialized MilestoneTracker")
    
    def create_milestones(self, workflow_plan: WorkflowPlan) -> List[Dict[str, Any]]:
        """
        Create milestones for a workflow plan.
        
        Args:
            workflow_plan: The workflow plan to create milestones for
            
        Returns:
            List of milestone definitions
        """
        milestones = []
        
        # Create milestones based on workflow phases
        total_steps = len(workflow_plan.steps)
        milestone_intervals = [0.25, 0.5, 0.75, 1.0]  # 25%, 50%, 75%, 100%
        
        for i, percentage in enumerate(milestone_intervals):
            step_index = int(total_steps * percentage) - 1
            if step_index >= 0 and step_index < total_steps:
                step = workflow_plan.steps[step_index]
                
                milestone = {
                    "id": f"milestone_{i+1}",
                    "name": f"Milestone {i+1} ({int(percentage*100)}%)",
                    "description": f"Complete {int(percentage*100)}% of workflow steps",
                    "target_step_id": step.id,
                    "target_percentage": percentage,
                    "criteria": self._define_milestone_criteria(step, percentage),
                    "status": "pending",
                    "achieved_at": None
                }
                
                milestones.append(milestone)
        
        self.milestones[workflow_plan.id] = milestones
        return milestones
    
    def _define_milestone_criteria(self, step: WorkflowStep, percentage: float) -> List[str]:
        """Define criteria for milestone achievement."""
        criteria = []
        
        if percentage <= 0.25:
            criteria.extend([
                "Initial setup and preparation completed",
                "Dependencies identified and resolved",
                "Basic project structure established"
            ])
        elif percentage <= 0.5:
            criteria.extend([
                "Core functionality implementation started",
                "Key components developed",
                "Initial testing framework in place"
            ])
        elif percentage <= 0.75:
            criteria.extend([
                "Major features implemented",
                "Integration testing completed",
                "Documentation started"
            ])
        else:
            criteria.extend([
                "All features implemented and tested",
                "Documentation completed",
                "Final validation and cleanup done"
            ])
        
        return criteria
    
    def check_milestone_achievement(
        self,
        workflow_id: str,
        completed_steps: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Check if any milestones have been achieved.
        
        Args:
            workflow_id: ID of the workflow
            completed_steps: List of completed step IDs
            
        Returns:
            List of newly achieved milestones
        """
        if workflow_id not in self.milestones:
            return []
        
        achieved_milestones = []
        
        for milestone in self.milestones[workflow_id]:
            if milestone["status"] == "pending":
                if milestone["target_step_id"] in completed_steps:
                    milestone["status"] = "achieved"
                    milestone["achieved_at"] = time.time()
                    achieved_milestones.append(milestone)
        
        return achieved_milestones
    
    def get_progress_summary(self, workflow_id: str) -> Dict[str, Any]:
        """Get progress summary for a workflow."""
        if workflow_id not in self.milestones:
            return {"progress": 0.0, "milestones": []}
        
        milestones = self.milestones[workflow_id]
        achieved_count = sum(1 for m in milestones if m["status"] == "achieved")
        
        return {
            "progress": (achieved_count / len(milestones)) * 100.0 if milestones else 0.0,
            "milestones": milestones,
            "achieved_count": achieved_count,
            "total_count": len(milestones)
        }


class ProgressMonitor:
    """Monitors progress of autonomous workflow execution."""
    
    def __init__(self):
        self.progress_data: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized ProgressMonitor")
    
    def start_monitoring(self, workflow_plan: WorkflowPlan) -> None:
        """Start monitoring a workflow."""
        self.progress_data[workflow_plan.id] = {
            "workflow_id": workflow_plan.id,
            "start_time": time.time(),
            "total_steps": len(workflow_plan.steps),
            "completed_steps": 0,
            "failed_steps": 0,
            "current_step": None,
            "progress_percentage": 0.0,
            "estimated_completion": None,
            "step_history": [],
            "performance_metrics": {
                "average_step_time": 0.0,
                "success_rate": 0.0,
                "efficiency_score": 0.0
            }
        }
    
    def update_step_progress(
        self,
        workflow_id: str,
        step: WorkflowStep,
        status: str,
        result: Optional[AgentResult] = None
    ) -> None:
        """Update progress for a specific step."""
        if workflow_id not in self.progress_data:
            return
        
        progress = self.progress_data[workflow_id]
        
        # Update step history
        step_update = {
            "step_id": step.id,
            "step_name": step.name,
            "status": status,
            "timestamp": time.time(),
            "duration": None,
            "success": None
        }
        
        if status == "started":
            progress["current_step"] = step.id
            step.started_at = time.time()
        
        elif status == "completed":
            if step.started_at:
                step_update["duration"] = time.time() - step.started_at
            
            if result:
                step_update["success"] = result.success
                if result.success:
                    progress["completed_steps"] += 1
                else:
                    progress["failed_steps"] += 1
        
        progress["step_history"].append(step_update)
        
        # Update progress percentage
        progress["progress_percentage"] = (
            progress["completed_steps"] / progress["total_steps"] * 100.0
        )
        
        # Update estimated completion
        if progress["completed_steps"] > 0:
            elapsed_time = time.time() - progress["start_time"]
            avg_time_per_step = elapsed_time / progress["completed_steps"]
            remaining_steps = progress["total_steps"] - progress["completed_steps"]
            progress["estimated_completion"] = time.time() + (avg_time_per_step * remaining_steps)
        
        # Update performance metrics
        self._update_performance_metrics(workflow_id)
    
    def _update_performance_metrics(self, workflow_id: str) -> None:
        """Update performance metrics for a workflow."""
        progress = self.progress_data[workflow_id]
        
        completed_steps = [
            step for step in progress["step_history"]
            if step["status"] == "completed" and step["duration"] is not None
        ]
        
        if completed_steps:
            # Average step time
            total_time = sum(step["duration"] for step in completed_steps)
            progress["performance_metrics"]["average_step_time"] = total_time / len(completed_steps)
            
            # Success rate
            successful_steps = sum(1 for step in completed_steps if step.get("success", False))
            progress["performance_metrics"]["success_rate"] = successful_steps / len(completed_steps)
            
            # Efficiency score (based on actual vs estimated time)
            # This would require estimated times for each step
            progress["performance_metrics"]["efficiency_score"] = min(
                progress["performance_metrics"]["success_rate"] * 100.0, 100.0
            )
    
    def get_progress_report(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress report for a workflow."""
        if workflow_id not in self.progress_data:
            return None
        
        progress = self.progress_data[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "progress_percentage": progress["progress_percentage"],
            "completed_steps": progress["completed_steps"],
            "total_steps": progress["total_steps"],
            "failed_steps": progress["failed_steps"],
            "current_step": progress["current_step"],
            "estimated_completion": progress["estimated_completion"],
            "performance_metrics": progress["performance_metrics"],
            "recent_activity": progress["step_history"][-5:] if progress["step_history"] else []
        }
    
    def stop_monitoring(self, workflow_id: str) -> Dict[str, Any]:
        """Stop monitoring and return final report."""
        if workflow_id not in self.progress_data:
            return {}
        
        final_report = self.get_progress_report(workflow_id)
        final_report["end_time"] = time.time()
        final_report["total_duration"] = final_report["end_time"] - self.progress_data[workflow_id]["start_time"]
        
        # Clean up monitoring data
        del self.progress_data[workflow_id]
        
        return final_report


class UserInterventionManager:
    """Manages user intervention points and approval workflows."""
    
    def __init__(self):
        self.pending_interventions: Dict[str, Dict[str, Any]] = {}
        self.intervention_history: Dict[str, List[Dict[str, Any]]] = {}
        self.approval_callbacks: Dict[str, Callable] = {}
        
        logger.info("Initialized UserInterventionManager")
    
    def create_intervention_point(
        self,
        workflow_id: str,
        step_id: str,
        intervention_type: str,
        message: str,
        options: List[str] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Create an intervention point requiring user input.
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the current step
            intervention_type: Type of intervention needed
            message: Message to display to user
            options: Available options for user
            context: Additional context information
            
        Returns:
            Intervention ID
        """
        intervention_id = str(uuid4())
        
        intervention = {
            "id": intervention_id,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "type": intervention_type,
            "message": message,
            "options": options or ["continue", "pause", "cancel"],
            "context": context or {},
            "created_at": time.time(),
            "status": "pending",
            "user_response": None,
            "responded_at": None
        }
        
        self.pending_interventions[intervention_id] = intervention
        
        logger.info(f"Created intervention point {intervention_id} for workflow {workflow_id}")
        return intervention_id
    
    def get_pending_interventions(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get pending interventions, optionally filtered by workflow."""
        interventions = list(self.pending_interventions.values())
        
        if workflow_id:
            interventions = [i for i in interventions if i["workflow_id"] == workflow_id]
        
        return interventions
    
    def respond_to_intervention(
        self,
        intervention_id: str,
        response: str,
        additional_data: Dict[str, Any] = None
    ) -> bool:
        """
        Respond to a pending intervention.
        
        Args:
            intervention_id: ID of the intervention
            response: User's response
            additional_data: Additional data from user
            
        Returns:
            True if response was processed successfully
        """
        if intervention_id not in self.pending_interventions:
            logger.error(f"Intervention {intervention_id} not found")
            return False
        
        intervention = self.pending_interventions[intervention_id]
        
        # Validate response
        if response not in intervention["options"]:
            logger.error(f"Invalid response '{response}' for intervention {intervention_id}")
            return False
        
        # Update intervention
        intervention["user_response"] = response
        intervention["additional_data"] = additional_data or {}
        intervention["responded_at"] = time.time()
        intervention["status"] = "responded"
        
        # Move to history
        workflow_id = intervention["workflow_id"]
        if workflow_id not in self.intervention_history:
            self.intervention_history[workflow_id] = []
        
        self.intervention_history[workflow_id].append(intervention)
        del self.pending_interventions[intervention_id]
        
        # Execute callback if registered
        if intervention_id in self.approval_callbacks:
            callback = self.approval_callbacks[intervention_id]
            try:
                callback(intervention)
            except Exception as e:
                logger.error(f"Error executing intervention callback: {e}")
            finally:
                del self.approval_callbacks[intervention_id]
        
        logger.info(f"User responded to intervention {intervention_id} with: {response}")
        return True
    
    def register_approval_callback(self, intervention_id: str, callback: Callable) -> None:
        """Register a callback to be executed when intervention is responded to."""
        self.approval_callbacks[intervention_id] = callback
    
    def cancel_intervention(self, intervention_id: str) -> bool:
        """Cancel a pending intervention."""
        if intervention_id not in self.pending_interventions:
            return False
        
        intervention = self.pending_interventions[intervention_id]
        intervention["status"] = "cancelled"
        intervention["responded_at"] = time.time()
        
        # Move to history
        workflow_id = intervention["workflow_id"]
        if workflow_id not in self.intervention_history:
            self.intervention_history[workflow_id] = []
        
        self.intervention_history[workflow_id].append(intervention)
        del self.pending_interventions[intervention_id]
        
        logger.info(f"Cancelled intervention {intervention_id}")
        return True
    
    def get_intervention_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get intervention history for a workflow."""
        return self.intervention_history.get(workflow_id, [])


class ApprovalWorkflowManager:
    """Manages approval workflows for critical decisions."""
    
    def __init__(self, intervention_manager: UserInterventionManager):
        self.intervention_manager = intervention_manager
        self.approval_rules: Dict[str, Dict[str, Any]] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized ApprovalWorkflowManager")
    
    def configure_approval_rules(self, rules: Dict[str, Dict[str, Any]]) -> None:
        """Configure approval rules for different types of operations."""
        self.approval_rules.update(rules)
        logger.info(f"Configured {len(rules)} approval rules")
    
    async def request_approval(
        self,
        workflow_id: str,
        step: WorkflowStep,
        operation_type: str,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Request approval for a critical operation.
        
        Args:
            workflow_id: ID of the workflow
            step: The workflow step requiring approval
            operation_type: Type of operation needing approval
            details: Additional details about the operation
            
        Returns:
            Approval result
        """
        # Check if approval is required
        if not self._requires_approval(step, operation_type):
            return {"approved": True, "reason": "No approval required"}
        
        # Create approval request
        approval_id = str(uuid4())
        approval_request = {
            "id": approval_id,
            "workflow_id": workflow_id,
            "step_id": step.id,
            "operation_type": operation_type,
            "step_name": step.name,
            "step_description": step.description,
            "risk_level": step.risk_level.value,
            "details": details or {},
            "created_at": time.time(),
            "status": "pending"
        }
        
        self.pending_approvals[approval_id] = approval_request
        
        # Create intervention point
        message = self._create_approval_message(approval_request)
        options = ["approve", "reject", "modify", "pause"]
        
        intervention_id = self.intervention_manager.create_intervention_point(
            workflow_id=workflow_id,
            step_id=step.id,
            intervention_type="approval_request",
            message=message,
            options=options,
            context={"approval_id": approval_id}
        )
        
        # Wait for user response
        approval_result = await self._wait_for_approval_response(intervention_id, approval_id)
        
        return approval_result
    
    def _requires_approval(self, step: WorkflowStep, operation_type: str) -> bool:
        """Check if an operation requires approval based on rules."""
        
        # High-risk steps always require approval
        if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        # Check specific approval rules
        if operation_type in self.approval_rules:
            rule = self.approval_rules[operation_type]
            
            # Check risk level requirement
            if "min_risk_level" in rule:
                min_risk = RiskLevel(rule["min_risk_level"])
                if step.risk_level.value >= min_risk.value:
                    return True
            
            # Check step type requirement
            if "step_types" in rule and step.task:
                if step.task.task_type in rule["step_types"]:
                    return True
            
            # Check description patterns
            if "description_patterns" in rule:
                step_desc = step.description.lower()
                for pattern in rule["description_patterns"]:
                    if pattern.lower() in step_desc:
                        return True
        
        return False
    
    def _create_approval_message(self, approval_request: Dict[str, Any]) -> str:
        """Create approval message for user."""
        step_name = approval_request["step_name"]
        operation_type = approval_request["operation_type"]
        risk_level = approval_request["risk_level"]
        description = approval_request["step_description"]
        
        message = f"""
Approval Required: {operation_type}

Step: {step_name}
Risk Level: {risk_level}
Description: {description}

This operation requires your approval before proceeding. Please review the details and choose an action:

- Approve: Continue with the operation as planned
- Reject: Skip this operation and continue with workflow
- Modify: Provide modified parameters for the operation
- Pause: Pause the workflow for manual review
        """.strip()
        
        return message
    
    async def _wait_for_approval_response(
        self,
        intervention_id: str,
        approval_id: str,
        timeout: float = 300.0  # 5 minutes default timeout
    ) -> Dict[str, Any]:
        """Wait for user response to approval request."""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if intervention has been responded to
            if intervention_id not in self.intervention_manager.pending_interventions:
                # Find response in history
                for workflow_id, history in self.intervention_manager.intervention_history.items():
                    for intervention in history:
                        if intervention["id"] == intervention_id:
                            return self._process_approval_response(approval_id, intervention)
            
            # Wait a bit before checking again
            await asyncio.sleep(1.0)
        
        # Timeout - default to rejection for safety
        logger.warning(f"Approval request {approval_id} timed out")
        return {
            "approved": False,
            "reason": "Approval request timed out",
            "action": "reject"
        }
    
    def _process_approval_response(
        self,
        approval_id: str,
        intervention: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user response to approval request."""
        
        response = intervention["user_response"]
        additional_data = intervention.get("additional_data", {})
        
        # Update approval request
        if approval_id in self.pending_approvals:
            approval_request = self.pending_approvals[approval_id]
            approval_request["status"] = "responded"
            approval_request["user_response"] = response
            approval_request["responded_at"] = time.time()
            del self.pending_approvals[approval_id]
        
        # Process response
        if response == "approve":
            return {
                "approved": True,
                "reason": "User approved the operation",
                "action": "proceed"
            }
        
        elif response == "reject":
            return {
                "approved": False,
                "reason": "User rejected the operation",
                "action": "skip"
            }
        
        elif response == "modify":
            return {
                "approved": True,
                "reason": "User approved with modifications",
                "action": "modify",
                "modifications": additional_data.get("modifications", {})
            }
        
        elif response == "pause":
            return {
                "approved": False,
                "reason": "User requested workflow pause",
                "action": "pause"
            }
        
        else:
            return {
                "approved": False,
                "reason": f"Unknown response: {response}",
                "action": "reject"
            }
    
    def get_pending_approvals(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get pending approval requests."""
        approvals = list(self.pending_approvals.values())
        
        if workflow_id:
            approvals = [a for a in approvals if a["workflow_id"] == workflow_id]
        
        return approvals


class NotificationManager:
    """Manages notifications and progress updates for users."""
    
    def __init__(self):
        self.notification_handlers: List[Callable] = []
        self.notification_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Initialized NotificationManager")
    
    def register_notification_handler(self, handler: Callable) -> None:
        """Register a notification handler."""
        self.notification_handlers.append(handler)
    
    def send_notification(
        self,
        workflow_id: str,
        notification_type: str,
        title: str,
        message: str,
        priority: str = "normal",
        data: Dict[str, Any] = None
    ) -> None:
        """
        Send a notification to registered handlers.
        
        Args:
            workflow_id: ID of the workflow
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level (low, normal, high, critical)
            data: Additional notification data
        """
        notification = {
            "id": str(uuid4()),
            "workflow_id": workflow_id,
            "type": notification_type,
            "title": title,
            "message": message,
            "priority": priority,
            "data": data or {},
            "timestamp": time.time()
        }
        
        # Store in history
        if workflow_id not in self.notification_history:
            self.notification_history[workflow_id] = []
        
        self.notification_history[workflow_id].append(notification)
        
        # Send to handlers
        for handler in self.notification_handlers:
            try:
                handler(notification)
            except Exception as e:
                logger.error(f"Error in notification handler: {e}")
        
        logger.info(f"Sent {priority} notification for workflow {workflow_id}: {title}")
    
    def send_progress_update(
        self,
        workflow_id: str,
        progress_percentage: float,
        current_step: str,
        estimated_completion: Optional[float] = None
    ) -> None:
        """Send a progress update notification."""
        message = f"Workflow progress: {progress_percentage:.1f}% complete"
        if current_step:
            message += f" (Current: {current_step})"
        
        if estimated_completion:
            eta_minutes = (estimated_completion - time.time()) / 60
            message += f" (ETA: {eta_minutes:.1f} minutes)"
        
        self.send_notification(
            workflow_id=workflow_id,
            notification_type="progress_update",
            title="Workflow Progress Update",
            message=message,
            priority="low",
            data={
                "progress_percentage": progress_percentage,
                "current_step": current_step,
                "estimated_completion": estimated_completion
            }
        )
    
    def send_milestone_notification(
        self,
        workflow_id: str,
        milestone: Dict[str, Any]
    ) -> None:
        """Send a milestone achievement notification."""
        self.send_notification(
            workflow_id=workflow_id,
            notification_type="milestone_achieved",
            title=f"Milestone Achieved: {milestone['name']}",
            message=milestone["description"],
            priority="normal",
            data={"milestone": milestone}
        )
    
    def send_error_notification(
        self,
        workflow_id: str,
        error: str,
        step_name: str = None
    ) -> None:
        """Send an error notification."""
        title = "Workflow Error"
        if step_name:
            title += f" in {step_name}"
        
        self.send_notification(
            workflow_id=workflow_id,
            notification_type="error",
            title=title,
            message=error,
            priority="high",
            data={"error": error, "step_name": step_name}
        )
    
    def get_notification_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get notification history for a workflow."""
        return self.notification_history.get(workflow_id, [])


class ManualOverrideManager:
    """Manages manual override capabilities for autonomous operations."""
    
    def __init__(self):
        self.override_handlers: Dict[str, Callable] = {}
        self.active_overrides: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized ManualOverrideManager")
    
    def register_override_handler(self, operation_type: str, handler: Callable) -> None:
        """Register a handler for manual overrides of specific operations."""
        self.override_handlers[operation_type] = handler
    
    def request_manual_override(
        self,
        workflow_id: str,
        step_id: str,
        operation_type: str,
        reason: str,
        override_data: Dict[str, Any] = None
    ) -> str:
        """
        Request manual override for an autonomous operation.
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the step
            operation_type: Type of operation to override
            reason: Reason for the override
            override_data: Data for the override
            
        Returns:
            Override request ID
        """
        override_id = str(uuid4())
        
        override_request = {
            "id": override_id,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "operation_type": operation_type,
            "reason": reason,
            "override_data": override_data or {},
            "created_at": time.time(),
            "status": "pending"
        }
        
        self.active_overrides[override_id] = override_request
        
        logger.info(f"Manual override requested for {operation_type} in workflow {workflow_id}")
        return override_id
    
    async def execute_manual_override(
        self,
        override_id: str,
        user_instructions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a manual override with user instructions.
        
        Args:
            override_id: ID of the override request
            user_instructions: Instructions from the user
            
        Returns:
            Override execution result
        """
        if override_id not in self.active_overrides:
            return {"success": False, "error": "Override request not found"}
        
        override_request = self.active_overrides[override_id]
        operation_type = override_request["operation_type"]
        
        try:
            # Execute override using registered handler
            if operation_type in self.override_handlers:
                handler = self.override_handlers[operation_type]
                result = await handler(override_request, user_instructions)
            else:
                result = await self._default_override_handler(override_request, user_instructions)
            
            # Update override status
            override_request["status"] = "completed"
            override_request["completed_at"] = time.time()
            override_request["result"] = result
            
            # Clean up
            del self.active_overrides[override_id]
            
            logger.info(f"Manual override {override_id} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing manual override {override_id}: {e}")
            
            override_request["status"] = "failed"
            override_request["error"] = str(e)
            
            return {"success": False, "error": str(e)}
    
    async def _default_override_handler(
        self,
        override_request: Dict[str, Any],
        user_instructions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Default handler for manual overrides."""
        return {
            "success": True,
            "message": f"Manual override applied for {override_request['operation_type']}",
            "instructions_applied": user_instructions
        }
    
    def get_active_overrides(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get active override requests."""
        overrides = list(self.active_overrides.values())
        
        if workflow_id:
            overrides = [o for o in overrides if o["workflow_id"] == workflow_id]
        
        return overrides


class CheckpointManager:
    """Manages checkpoints for workflow rollback capabilities."""
    
    def __init__(self):
        self.checkpoints: Dict[str, List[Checkpoint]] = {}
        self.checkpoint_data: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized CheckpointManager")
    
    def create_checkpoint(
        self,
        workflow_id: str,
        step_id: str,
        state_snapshot: Dict[str, Any],
        description: str = ""
    ) -> Checkpoint:
        """
        Create a checkpoint for rollback capability.
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the current step
            state_snapshot: Current state to save
            description: Description of the checkpoint
            
        Returns:
            Created checkpoint
        """
        checkpoint = Checkpoint(
            workflow_id=workflow_id,
            step_id=step_id,
            state_snapshot=state_snapshot,
            description=description or f"Checkpoint at step {step_id}"
        )
        
        if workflow_id not in self.checkpoints:
            self.checkpoints[workflow_id] = []
        
        self.checkpoints[workflow_id].append(checkpoint)
        
        # Store detailed checkpoint data
        self.checkpoint_data[checkpoint.id] = {
            "checkpoint": checkpoint,
            "file_states": self._capture_file_states(state_snapshot),
            "environment_state": self._capture_environment_state(),
            "agent_states": self._capture_agent_states(state_snapshot)
        }
        
        logger.info(f"Created checkpoint {checkpoint.id} for workflow {workflow_id}")
        return checkpoint
    
    def _capture_file_states(self, state_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Capture current file states for rollback."""
        file_states = {}
        
        # Capture modified files from state snapshot
        if "modified_files" in state_snapshot:
            for file_path in state_snapshot["modified_files"]:
                try:
                    # In a real implementation, you'd read the actual file content
                    file_states[file_path] = {
                        "content": f"<content_of_{file_path}>",
                        "timestamp": time.time(),
                        "size": 0  # Would be actual file size
                    }
                except Exception as e:
                    logger.warning(f"Could not capture state for file {file_path}: {e}")
        
        return file_states
    
    def _capture_environment_state(self) -> Dict[str, Any]:
        """Capture current environment state."""
        return {
            "timestamp": time.time(),
            "working_directory": ".",  # Would be actual working directory
            "environment_variables": {},  # Would capture relevant env vars
            "process_states": {}  # Would capture running processes
        }
    
    def _capture_agent_states(self, state_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Capture current agent states."""
        return {
            "active_agents": state_snapshot.get("active_agents", []),
            "agent_contexts": state_snapshot.get("agent_contexts", {}),
            "task_assignments": state_snapshot.get("task_assignments", {})
        }
    
    def get_checkpoints(self, workflow_id: str) -> List[Checkpoint]:
        """Get all checkpoints for a workflow."""
        return self.checkpoints.get(workflow_id, [])
    
    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        """Get the latest checkpoint for a workflow."""
        checkpoints = self.get_checkpoints(workflow_id)
        return checkpoints[-1] if checkpoints else None
    
    def get_checkpoint_data(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed data for a specific checkpoint."""
        return self.checkpoint_data.get(checkpoint_id)
    
    def cleanup_checkpoints(self, workflow_id: str, keep_count: int = 5) -> None:
        """Clean up old checkpoints, keeping only the most recent ones."""
        if workflow_id not in self.checkpoints:
            return
        
        checkpoints = self.checkpoints[workflow_id]
        if len(checkpoints) > keep_count:
            # Remove old checkpoints
            old_checkpoints = checkpoints[:-keep_count]
            self.checkpoints[workflow_id] = checkpoints[-keep_count:]
            
            # Clean up checkpoint data
            for checkpoint in old_checkpoints:
                if checkpoint.id in self.checkpoint_data:
                    del self.checkpoint_data[checkpoint.id]
            
            logger.info(f"Cleaned up {len(old_checkpoints)} old checkpoints for workflow {workflow_id}")


class RollbackManager:
    """Manages rollback operations for failed workflow steps."""
    
    def __init__(self):
        self.rollback_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Initialized RollbackManager")
    
    async def rollback_to_checkpoint(
        self,
        checkpoint: Checkpoint,
        checkpoint_data: Dict[str, Any]
    ) -> bool:
        """
        Rollback workflow state to a specific checkpoint.
        
        Args:
            checkpoint: The checkpoint to rollback to
            checkpoint_data: Detailed checkpoint data
            
        Returns:
            True if rollback was successful, False otherwise
        """
        logger.info(f"Starting rollback to checkpoint {checkpoint.id}")
        
        try:
            rollback_operations = []
            
            # 1. Rollback file states
            file_rollback_success = await self._rollback_file_states(
                checkpoint_data.get("file_states", {})
            )
            rollback_operations.append(("file_states", file_rollback_success))
            
            # 2. Rollback environment state
            env_rollback_success = await self._rollback_environment_state(
                checkpoint_data.get("environment_state", {})
            )
            rollback_operations.append(("environment_state", env_rollback_success))
            
            # 3. Rollback agent states
            agent_rollback_success = await self._rollback_agent_states(
                checkpoint_data.get("agent_states", {})
            )
            rollback_operations.append(("agent_states", agent_rollback_success))
            
            # Check if all rollback operations succeeded
            all_success = all(success for _, success in rollback_operations)
            
            # Record rollback operation
            self._record_rollback_operation(checkpoint, rollback_operations, all_success)
            
            if all_success:
                logger.info(f"Successfully rolled back to checkpoint {checkpoint.id}")
            else:
                logger.error(f"Partial rollback failure for checkpoint {checkpoint.id}")
            
            return all_success
            
        except Exception as e:
            logger.error(f"Error during rollback to checkpoint {checkpoint.id}: {e}")
            return False
    
    async def _rollback_file_states(self, file_states: Dict[str, Any]) -> bool:
        """Rollback file states to checkpoint values."""
        try:
            for file_path, file_data in file_states.items():
                # In a real implementation, you'd restore the actual file content
                logger.info(f"Rolling back file: {file_path}")
                # Example: write file_data["content"] to file_path
            
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back file states: {e}")
            return False
    
    async def _rollback_environment_state(self, env_state: Dict[str, Any]) -> bool:
        """Rollback environment state to checkpoint values."""
        try:
            # Restore working directory
            if "working_directory" in env_state:
                logger.info(f"Rolling back working directory to: {env_state['working_directory']}")
            
            # Restore environment variables
            if "environment_variables" in env_state:
                logger.info("Rolling back environment variables")
            
            # Restore process states
            if "process_states" in env_state:
                logger.info("Rolling back process states")
            
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back environment state: {e}")
            return False
    
    async def _rollback_agent_states(self, agent_states: Dict[str, Any]) -> bool:
        """Rollback agent states to checkpoint values."""
        try:
            # Restore agent contexts
            if "agent_contexts" in agent_states:
                logger.info("Rolling back agent contexts")
            
            # Restore task assignments
            if "task_assignments" in agent_states:
                logger.info("Rolling back task assignments")
            
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back agent states: {e}")
            return False
    
    def _record_rollback_operation(
        self,
        checkpoint: Checkpoint,
        operations: List[tuple],
        success: bool
    ) -> None:
        """Record rollback operation for audit purposes."""
        workflow_id = checkpoint.workflow_id
        
        if workflow_id not in self.rollback_history:
            self.rollback_history[workflow_id] = []
        
        rollback_record = {
            "checkpoint_id": checkpoint.id,
            "timestamp": time.time(),
            "operations": operations,
            "success": success,
            "description": checkpoint.description
        }
        
        self.rollback_history[workflow_id].append(rollback_record)
    
    def get_rollback_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get rollback history for a workflow."""
        return self.rollback_history.get(workflow_id, [])


class StateManager:
    """Manages workflow execution state for complex workflows."""
    
    def __init__(self):
        self.workflow_states: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized StateManager")
    
    def initialize_workflow_state(self, workflow_plan: WorkflowPlan) -> None:
        """Initialize state tracking for a workflow."""
        self.workflow_states[workflow_plan.id] = {
            "workflow_id": workflow_plan.id,
            "current_step": None,
            "completed_steps": [],
            "failed_steps": [],
            "step_results": {},
            "execution_context": {},
            "modified_files": [],
            "created_resources": [],
            "active_agents": [],
            "agent_contexts": {},
            "task_assignments": {},
            "state_history": []
        }
    
    def update_step_state(
        self,
        workflow_id: str,
        step: WorkflowStep,
        status: str,
        result: Optional[AgentResult] = None,
        context_updates: Dict[str, Any] = None
    ) -> None:
        """Update state for a workflow step."""
        if workflow_id not in self.workflow_states:
            return
        
        state = self.workflow_states[workflow_id]
        
        if status == "started":
            state["current_step"] = step.id
        
        elif status == "completed":
            state["completed_steps"].append(step.id)
            if step.id == state["current_step"]:
                state["current_step"] = None
            
            if result:
                state["step_results"][step.id] = {
                    "success": result.success,
                    "output": result.output,
                    "confidence": result.confidence,
                    "execution_time": result.execution_time
                }
                
                if not result.success:
                    state["failed_steps"].append(step.id)
        
        elif status == "failed":
            state["failed_steps"].append(step.id)
            if step.id == state["current_step"]:
                state["current_step"] = None
        
        # Update execution context
        if context_updates:
            state["execution_context"].update(context_updates)
        
        # Record state change
        state["state_history"].append({
            "timestamp": time.time(),
            "step_id": step.id,
            "status": status,
            "context_snapshot": state["execution_context"].copy()
        })
    
    def get_current_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current state for a workflow."""
        return self.workflow_states.get(workflow_id)
    
    def create_state_snapshot(self, workflow_id: str) -> Dict[str, Any]:
        """Create a snapshot of current workflow state."""
        state = self.workflow_states.get(workflow_id, {})
        
        return {
            "timestamp": time.time(),
            "workflow_id": workflow_id,
            "current_step": state.get("current_step"),
            "completed_steps": state.get("completed_steps", []).copy(),
            "failed_steps": state.get("failed_steps", []).copy(),
            "execution_context": state.get("execution_context", {}).copy(),
            "modified_files": state.get("modified_files", []).copy(),
            "active_agents": state.get("active_agents", []).copy(),
            "agent_contexts": state.get("agent_contexts", {}).copy(),
            "task_assignments": state.get("task_assignments", {}).copy()
        }
    
    def restore_state_snapshot(self, workflow_id: str, snapshot: Dict[str, Any]) -> bool:
        """Restore workflow state from a snapshot."""
        try:
            if workflow_id not in self.workflow_states:
                self.workflow_states[workflow_id] = {}
            
            state = self.workflow_states[workflow_id]
            
            # Restore state from snapshot
            state["current_step"] = snapshot.get("current_step")
            state["completed_steps"] = snapshot.get("completed_steps", []).copy()
            state["failed_steps"] = snapshot.get("failed_steps", []).copy()
            state["execution_context"] = snapshot.get("execution_context", {}).copy()
            state["modified_files"] = snapshot.get("modified_files", []).copy()
            state["active_agents"] = snapshot.get("active_agents", []).copy()
            state["agent_contexts"] = snapshot.get("agent_contexts", {}).copy()
            state["task_assignments"] = snapshot.get("task_assignments", {}).copy()
            
            logger.info(f"Restored state for workflow {workflow_id} from snapshot")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring state snapshot for workflow {workflow_id}: {e}")
            return False
    
    def cleanup_workflow_state(self, workflow_id: str) -> None:
        """Clean up state data for a completed workflow."""
        if workflow_id in self.workflow_states:
            del self.workflow_states[workflow_id]
            logger.info(f"Cleaned up state for workflow {workflow_id}")


class RecoveryEngine:
    """Handles recovery strategies for different types of failures."""
    
    def __init__(self):
        self.recovery_strategies: Dict[str, Callable] = {
            "retry": self._retry_strategy,
            "skip": self._skip_strategy,
            "rollback": self._rollback_strategy,
            "alternative": self._alternative_strategy,
            "manual_intervention": self._manual_intervention_strategy
        }
        
        logger.info("Initialized RecoveryEngine")
    
    async def handle_step_failure(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any],
        recovery_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle failure of a workflow step and determine recovery action.
        
        Args:
            step: The failed workflow step
            error: The error that occurred
            workflow_state: Current workflow state
            recovery_context: Additional context for recovery
            
        Returns:
            Recovery action plan
        """
        logger.info(f"Handling failure for step {step.id}: {error}")
        
        recovery_context = recovery_context or {}
        
        # Analyze the failure
        failure_analysis = self._analyze_failure(step, error, workflow_state)
        
        # Determine recovery strategy
        strategy = self._determine_recovery_strategy(failure_analysis, step)
        
        # Execute recovery strategy
        if strategy in self.recovery_strategies:
            recovery_action = await self.recovery_strategies[strategy](
                step, error, workflow_state, failure_analysis, recovery_context
            )
        else:
            recovery_action = await self._default_recovery_strategy(
                step, error, workflow_state, failure_analysis, recovery_context
            )
        
        return recovery_action
    
    def _analyze_failure(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the failure to determine appropriate recovery strategy."""
        analysis = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "step_risk_level": step.risk_level.value,
            "failure_category": "unknown",
            "is_recoverable": True,
            "retry_recommended": False,
            "rollback_recommended": False
        }
        
        error_message = str(error).lower()
        
        # Categorize the failure
        if any(keyword in error_message for keyword in ["network", "connection", "timeout"]):
            analysis["failure_category"] = "network"
            analysis["retry_recommended"] = True
        
        elif any(keyword in error_message for keyword in ["permission", "access", "denied"]):
            analysis["failure_category"] = "permission"
            analysis["is_recoverable"] = False
        
        elif any(keyword in error_message for keyword in ["syntax", "parse", "invalid"]):
            analysis["failure_category"] = "syntax"
            analysis["rollback_recommended"] = True
        
        elif any(keyword in error_message for keyword in ["resource", "memory", "disk"]):
            analysis["failure_category"] = "resource"
            analysis["retry_recommended"] = True
        
        elif any(keyword in error_message for keyword in ["dependency", "missing", "not found"]):
            analysis["failure_category"] = "dependency"
            analysis["is_recoverable"] = True
        
        # Consider step risk level
        if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            analysis["rollback_recommended"] = True
        
        return analysis
    
    def _determine_recovery_strategy(
        self,
        failure_analysis: Dict[str, Any],
        step: WorkflowStep
    ) -> str:
        """Determine the best recovery strategy based on failure analysis."""
        
        # High-risk steps should generally rollback
        if step.risk_level == RiskLevel.CRITICAL:
            return "rollback"
        
        # Check failure category
        category = failure_analysis["failure_category"]
        
        if category == "network" and failure_analysis["retry_recommended"]:
            return "retry"
        
        elif category == "permission":
            return "manual_intervention"
        
        elif category == "syntax" or failure_analysis["rollback_recommended"]:
            return "rollback"
        
        elif category == "dependency":
            return "alternative"
        
        elif failure_analysis["retry_recommended"]:
            return "retry"
        
        else:
            return "skip"
    
    async def _retry_strategy(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any],
        failure_analysis: Dict[str, Any],
        recovery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retry strategy with exponential backoff."""
        max_retries = recovery_context.get("max_retries", 3)
        current_retry = recovery_context.get("current_retry", 0)
        
        if current_retry < max_retries:
            backoff_time = 2 ** current_retry  # Exponential backoff
            
            return {
                "action": "retry",
                "delay": backoff_time,
                "retry_count": current_retry + 1,
                "max_retries": max_retries,
                "reason": f"Retrying step due to {failure_analysis['failure_category']} error"
            }
        else:
            return {
                "action": "skip",
                "reason": f"Max retries ({max_retries}) exceeded for step {step.id}"
            }
    
    async def _skip_strategy(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any],
        failure_analysis: Dict[str, Any],
        recovery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Skip the failed step and continue."""
        return {
            "action": "skip",
            "reason": f"Skipping step {step.id} due to {failure_analysis['error_type']}",
            "impact": "Step will be marked as skipped, workflow continues"
        }
    
    async def _rollback_strategy(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any],
        failure_analysis: Dict[str, Any],
        recovery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rollback to previous checkpoint."""
        return {
            "action": "rollback",
            "reason": f"Rolling back due to {failure_analysis['failure_category']} error in high-risk step",
            "rollback_target": "latest_checkpoint",
            "impact": "Workflow will be restored to previous safe state"
        }
    
    async def _alternative_strategy(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any],
        failure_analysis: Dict[str, Any],
        recovery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try an alternative approach for the step."""
        return {
            "action": "alternative",
            "reason": f"Trying alternative approach due to {failure_analysis['failure_category']} error",
            "alternative_description": "Use fallback implementation or different approach",
            "impact": "Step will be attempted with modified parameters or approach"
        }
    
    async def _manual_intervention_strategy(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any],
        failure_analysis: Dict[str, Any],
        recovery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request manual intervention from user."""
        return {
            "action": "manual_intervention",
            "reason": f"Manual intervention required due to {failure_analysis['failure_category']} error",
            "intervention_type": "user_approval",
            "message": f"Step {step.id} failed with error: {error}. Please review and decide how to proceed.",
            "options": ["retry", "skip", "rollback", "modify_and_retry"]
        }
    
    async def _default_recovery_strategy(
        self,
        step: WorkflowStep,
        error: Exception,
        workflow_state: Dict[str, Any],
        failure_analysis: Dict[str, Any],
        recovery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Default recovery strategy when no specific strategy applies."""
        return {
            "action": "manual_intervention",
            "reason": f"Unknown error type, requesting manual intervention",
            "error_details": {
                "error_type": failure_analysis["error_type"],
                "error_message": failure_analysis["error_message"],
                "step_id": step.id,
                "step_name": step.name
            }
        }