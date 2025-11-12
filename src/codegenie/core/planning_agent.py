"""
Planning Agent for intelligent task decomposition and execution planning.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions that can be performed."""
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    EXECUTE_COMMAND = "execute_command"
    INSTALL_DEPENDENCY = "install_dependency"
    REFACTOR_CODE = "refactor_code"
    GENERATE_DOCS = "generate_docs"
    RUN_TESTS = "run_tests"


class RiskLevel(Enum):
    """Risk levels for operations."""
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    def __lt__(self, other):
        if isinstance(other, RiskLevel):
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, RiskLevel):
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if isinstance(other, RiskLevel):
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if isinstance(other, RiskLevel):
            return self.value >= other.value
        return NotImplemented


class StepStatus(Enum):
    """Status of execution steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    """A single step in an execution plan."""
    id: str
    description: str
    action_type: ActionType
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    risk_level: RiskLevel = RiskLevel.LOW
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        risk_names = {0: 'safe', 1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        return {
            'id': self.id,
            'description': self.description,
            'action_type': self.action_type.value,
            'parameters': self.parameters,
            'dependencies': self.dependencies,
            'estimated_duration': self.estimated_duration.total_seconds(),
            'risk_level': risk_names[self.risk_level.value],
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
        }


@dataclass
class ComplexityEstimate:
    """Complexity estimation for a plan."""
    total_steps: int
    estimated_duration: timedelta
    risk_score: float  # 0.0 to 1.0
    complexity_level: str  # simple, moderate, complex, very_complex
    confidence: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_steps': self.total_steps,
            'estimated_duration': self.estimated_duration.total_seconds(),
            'risk_score': self.risk_score,
            'complexity_level': self.complexity_level,
            'confidence': self.confidence,
        }


@dataclass
class ValidationResult:
    """Result of plan validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan for a user request."""
    id: str
    description: str
    steps: List[Step]
    estimated_duration: timedelta
    risk_level: RiskLevel
    affected_files: List[Path] = field(default_factory=list)
    required_approvals: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    complexity: Optional[ComplexityEstimate] = None
    validation: Optional[ValidationResult] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary."""
        risk_names = {0: 'safe', 1: 'low', 2: 'medium', 3: 'high', 4: 'critical'}
        return {
            'id': self.id,
            'description': self.description,
            'steps': [step.to_dict() for step in self.steps],
            'estimated_duration': self.estimated_duration.total_seconds(),
            'risk_level': risk_names[self.risk_level.value],
            'affected_files': [str(f) for f in self.affected_files],
            'required_approvals': self.required_approvals,
            'dependencies': self.dependencies,
            'created_at': self.created_at,
            'complexity': self.complexity.to_dict() if self.complexity else None,
            'validation': self.validation.to_dict() if self.validation else None,
        }


@dataclass
class ExecutionResult:
    """Result of plan execution."""
    plan_id: str
    success: bool
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    total_duration: timedelta
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'plan_id': self.plan_id,
            'success': self.success,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'skipped_steps': self.skipped_steps,
            'total_duration': self.total_duration.total_seconds(),
            'step_results': self.step_results,
            'error_message': self.error_message,
        }


class PlanningAgent:
    """
    Intelligent planning agent that creates detailed execution plans.
    
    The planning agent analyzes user requests, breaks them down into
    actionable steps, estimates complexity, and manages execution.
    """
    
    def __init__(self, model_client=None):
        """
        Initialize the planning agent.
        
        Args:
            model_client: Optional AI model client for intelligent planning
        """
        self.model_client = model_client
        self.plans: Dict[str, ExecutionPlan] = {}
        self.execution_history: List[ExecutionResult] = []
        
        logger.info("Planning Agent initialized")
    
    def create_plan(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Create an execution plan from a user request.
        
        Args:
            user_request: Natural language description of what to do
            context: Optional context about the project
            
        Returns:
            ExecutionPlan with detailed steps
        """
        logger.info(f"Creating plan for request: {user_request}")
        
        # Generate plan ID
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        # Break down the request into tasks
        tasks = self.break_down_task(user_request, context)
        
        # Convert tasks to steps
        steps = []
        for i, task in enumerate(tasks):
            step = Step(
                id=f"step_{i+1}",
                description=task['description'],
                action_type=task['action_type'],
                parameters=task['parameters'],
                dependencies=task.get('dependencies', []),
                estimated_duration=task.get('estimated_duration', timedelta(seconds=30)),
                risk_level=task.get('risk_level', RiskLevel.LOW),
            )
            steps.append(step)
        
        # Calculate overall metrics
        total_duration = sum((s.estimated_duration for s in steps), timedelta())
        max_risk = max((s.risk_level for s in steps), default=RiskLevel.SAFE)
        
        # Identify affected files
        affected_files = self._extract_affected_files(steps)
        
        # Identify required approvals
        required_approvals = self._identify_required_approvals(steps)
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(steps)
        
        # Create the plan
        plan = ExecutionPlan(
            id=plan_id,
            description=user_request,
            steps=steps,
            estimated_duration=total_duration,
            risk_level=max_risk,
            affected_files=affected_files,
            required_approvals=required_approvals,
            dependencies=dependencies,
        )
        
        # Estimate complexity
        plan.complexity = self.estimate_complexity(plan)
        
        # Validate the plan
        plan.validation = self.validate_plan(plan)
        
        # Store the plan
        self.plans[plan_id] = plan
        
        logger.info(f"Created plan {plan_id} with {len(steps)} steps")
        
        return plan
    
    def break_down_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Break down a high-level task into specific steps.
        
        Args:
            task: Task description
            context: Optional context information
            
        Returns:
            List of task dictionaries with details
        """
        # This is a simplified implementation
        # In a real system, this would use AI to intelligently decompose tasks
        
        tasks = []
        
        # Analyze the task to determine what needs to be done
        task_lower = task.lower()
        
        if "create" in task_lower and "project" in task_lower:
            # Project creation workflow
            tasks.extend(self._plan_project_creation(task, context))
        elif "refactor" in task_lower:
            # Refactoring workflow
            tasks.extend(self._plan_refactoring(task, context))
        elif "add" in task_lower or "implement" in task_lower:
            # Feature addition workflow
            tasks.extend(self._plan_feature_addition(task, context))
        elif "fix" in task_lower or "bug" in task_lower:
            # Bug fix workflow
            tasks.extend(self._plan_bug_fix(task, context))
        else:
            # Generic workflow
            tasks.append({
                'description': task,
                'action_type': ActionType.EXECUTE_COMMAND,
                'parameters': {'command': 'echo "Task analysis needed"'},
                'risk_level': RiskLevel.LOW,
            })
        
        return tasks
    
    def _plan_project_creation(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Plan steps for project creation."""
        return [
            {
                'description': 'Analyze project requirements',
                'action_type': ActionType.EXECUTE_COMMAND,
                'parameters': {'analysis': True},
                'risk_level': RiskLevel.SAFE,
                'estimated_duration': timedelta(seconds=5),
            },
            {
                'description': 'Create project directory structure',
                'action_type': ActionType.CREATE_FILE,
                'parameters': {'type': 'directory_structure'},
                'risk_level': RiskLevel.LOW,
                'estimated_duration': timedelta(seconds=10),
                'dependencies': ['step_1'],
            },
            {
                'description': 'Generate configuration files',
                'action_type': ActionType.CREATE_FILE,
                'parameters': {'type': 'config_files'},
                'risk_level': RiskLevel.LOW,
                'estimated_duration': timedelta(seconds=15),
                'dependencies': ['step_2'],
            },
            {
                'description': 'Initialize version control',
                'action_type': ActionType.EXECUTE_COMMAND,
                'parameters': {'command': 'git init'},
                'risk_level': RiskLevel.LOW,
                'estimated_duration': timedelta(seconds=5),
                'dependencies': ['step_3'],
            },
            {
                'description': 'Install dependencies',
                'action_type': ActionType.INSTALL_DEPENDENCY,
                'parameters': {'auto_install': True},
                'risk_level': RiskLevel.MEDIUM,
                'estimated_duration': timedelta(seconds=60),
                'dependencies': ['step_4'],
            },
        ]
    
    def _plan_refactoring(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Plan steps for refactoring."""
        return [
            {
                'description': 'Analyze code structure',
                'action_type': ActionType.EXECUTE_COMMAND,
                'parameters': {'analysis': True},
                'risk_level': RiskLevel.SAFE,
            },
            {
                'description': 'Identify refactoring opportunities',
                'action_type': ActionType.REFACTOR_CODE,
                'parameters': {'analyze_only': True},
                'risk_level': RiskLevel.SAFE,
                'dependencies': ['step_1'],
            },
            {
                'description': 'Apply refactoring changes',
                'action_type': ActionType.MODIFY_FILE,
                'parameters': {'refactor': True},
                'risk_level': RiskLevel.MEDIUM,
                'dependencies': ['step_2'],
            },
            {
                'description': 'Run tests to verify changes',
                'action_type': ActionType.RUN_TESTS,
                'parameters': {'test_suite': 'all'},
                'risk_level': RiskLevel.LOW,
                'dependencies': ['step_3'],
            },
        ]
    
    def _plan_feature_addition(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Plan steps for adding a feature."""
        return [
            {
                'description': 'Design feature architecture',
                'action_type': ActionType.EXECUTE_COMMAND,
                'parameters': {'design': True},
                'risk_level': RiskLevel.SAFE,
            },
            {
                'description': 'Create new files for feature',
                'action_type': ActionType.CREATE_FILE,
                'parameters': {'feature': True},
                'risk_level': RiskLevel.LOW,
                'dependencies': ['step_1'],
            },
            {
                'description': 'Integrate with existing code',
                'action_type': ActionType.MODIFY_FILE,
                'parameters': {'integration': True},
                'risk_level': RiskLevel.MEDIUM,
                'dependencies': ['step_2'],
            },
            {
                'description': 'Add tests for new feature',
                'action_type': ActionType.CREATE_FILE,
                'parameters': {'tests': True},
                'risk_level': RiskLevel.LOW,
                'dependencies': ['step_3'],
            },
            {
                'description': 'Update documentation',
                'action_type': ActionType.GENERATE_DOCS,
                'parameters': {'feature_docs': True},
                'risk_level': RiskLevel.SAFE,
                'dependencies': ['step_4'],
            },
        ]
    
    def _plan_bug_fix(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Plan steps for fixing a bug."""
        return [
            {
                'description': 'Reproduce and analyze bug',
                'action_type': ActionType.EXECUTE_COMMAND,
                'parameters': {'debug': True},
                'risk_level': RiskLevel.SAFE,
            },
            {
                'description': 'Identify root cause',
                'action_type': ActionType.EXECUTE_COMMAND,
                'parameters': {'analysis': True},
                'risk_level': RiskLevel.SAFE,
                'dependencies': ['step_1'],
            },
            {
                'description': 'Apply fix',
                'action_type': ActionType.MODIFY_FILE,
                'parameters': {'fix': True},
                'risk_level': RiskLevel.MEDIUM,
                'dependencies': ['step_2'],
            },
            {
                'description': 'Verify fix with tests',
                'action_type': ActionType.RUN_TESTS,
                'parameters': {'regression': True},
                'risk_level': RiskLevel.LOW,
                'dependencies': ['step_3'],
            },
        ]
    
    def estimate_complexity(self, plan: ExecutionPlan) -> ComplexityEstimate:
        """
        Estimate the complexity of an execution plan.
        
        Args:
            plan: The execution plan to analyze
            
        Returns:
            ComplexityEstimate with metrics
        """
        total_steps = len(plan.steps)
        total_duration = plan.estimated_duration
        
        # Calculate risk score (0.0 to 1.0)
        risk_scores = {
            RiskLevel.SAFE: 0.0,
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0,
        }
        
        avg_risk = sum(risk_scores[step.risk_level] for step in plan.steps) / total_steps
        
        # Determine complexity level
        if total_steps <= 3 and avg_risk < 0.3:
            complexity_level = "simple"
            confidence = 0.9
        elif total_steps <= 7 and avg_risk < 0.5:
            complexity_level = "moderate"
            confidence = 0.8
        elif total_steps <= 15 and avg_risk < 0.7:
            complexity_level = "complex"
            confidence = 0.7
        else:
            complexity_level = "very_complex"
            confidence = 0.6
        
        return ComplexityEstimate(
            total_steps=total_steps,
            estimated_duration=total_duration,
            risk_score=avg_risk,
            complexity_level=complexity_level,
            confidence=confidence,
        )
    
    def validate_plan(self, plan: ExecutionPlan) -> ValidationResult:
        """
        Validate an execution plan for potential issues.
        
        Args:
            plan: The plan to validate
            
        Returns:
            ValidationResult with errors, warnings, and suggestions
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Check for circular dependencies
        if self._has_circular_dependencies(plan):
            errors.append("Plan contains circular dependencies")
        
        # Check for missing dependencies
        all_step_ids = {step.id for step in plan.steps}
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in all_step_ids:
                    errors.append(f"Step {step.id} depends on non-existent step {dep}")
        
        # Check for high-risk operations
        high_risk_steps = [s for s in plan.steps if s.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        if high_risk_steps:
            warnings.append(f"Plan contains {len(high_risk_steps)} high-risk operations")
        
        # Check for long duration
        if plan.estimated_duration > timedelta(minutes=30):
            warnings.append(f"Plan estimated to take {plan.estimated_duration.total_seconds()/60:.1f} minutes")
        
        # Suggest optimizations
        if len(plan.steps) > 10:
            suggestions.append("Consider breaking this into smaller sub-plans")
        
        # Check for parallel execution opportunities
        independent_steps = self._find_independent_steps(plan)
        if len(independent_steps) > 1:
            suggestions.append(f"{len(independent_steps)} steps could potentially run in parallel")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )
    
    def execute_plan(
        self,
        plan: ExecutionPlan,
        approval_callback: Optional[Callable[[Step], bool]] = None,
        progress_callback: Optional[Callable[[Step, int, int], None]] = None
    ) -> ExecutionResult:
        """
        Execute a plan step by step.
        
        Args:
            plan: The plan to execute
            approval_callback: Optional callback for step approval
            progress_callback: Optional callback for progress updates
            
        Returns:
            ExecutionResult with execution details
        """
        logger.info(f"Executing plan {plan.id}")
        
        start_time = time.time()
        completed = 0
        failed = 0
        skipped = 0
        step_results = []
        
        # Execute steps in dependency order
        executed_steps = set()
        
        for i, step in enumerate(plan.steps):
            # Check if dependencies are met
            if not all(dep in executed_steps for dep in step.dependencies):
                logger.warning(f"Skipping step {step.id} - dependencies not met")
                step.status = StepStatus.SKIPPED
                skipped += 1
                continue
            
            # Request approval if callback provided
            if approval_callback and step.risk_level != RiskLevel.SAFE:
                if not approval_callback(step):
                    logger.info(f"Step {step.id} not approved by user")
                    step.status = StepStatus.SKIPPED
                    skipped += 1
                    continue
            
            # Update progress
            if progress_callback:
                progress_callback(step, i + 1, len(plan.steps))
            
            # Execute the step
            try:
                step.status = StepStatus.IN_PROGRESS
                step.started_at = time.time()
                
                # Simulate execution (in real implementation, this would call actual executors)
                result = self._execute_step(step)
                
                step.result = result
                step.status = StepStatus.COMPLETED
                step.completed_at = time.time()
                completed += 1
                executed_steps.add(step.id)
                
                logger.info(f"Completed step {step.id}: {step.description}")
                
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                step.completed_at = time.time()
                failed += 1
                
                logger.error(f"Failed step {step.id}: {e}")
                
                # Decide whether to continue or abort
                if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    logger.error("Aborting plan due to critical step failure")
                    break
            
            step_results.append(step.to_dict())
        
        end_time = time.time()
        total_duration = timedelta(seconds=end_time - start_time)
        
        success = failed == 0 and completed > 0
        
        result = ExecutionResult(
            plan_id=plan.id,
            success=success,
            completed_steps=completed,
            failed_steps=failed,
            skipped_steps=skipped,
            total_duration=total_duration,
            step_results=step_results,
            error_message=None if success else "One or more steps failed",
        )
        
        self.execution_history.append(result)
        
        logger.info(f"Plan execution completed: {completed} completed, {failed} failed, {skipped} skipped")
        
        return result
    
    def _execute_step(self, step: Step) -> Any:
        """
        Execute a single step (placeholder for actual execution).
        
        Args:
            step: The step to execute
            
        Returns:
            Execution result
        """
        # This is a placeholder - actual implementation would delegate to
        # appropriate executors (FileCreator, CommandExecutor, etc.)
        
        logger.debug(f"Executing step: {step.description}")
        
        # Simulate some work
        time.sleep(0.1)
        
        return {
            'status': 'success',
            'action': step.action_type.value,
            'description': step.description,
        }
    
    def _extract_affected_files(self, steps: List[Step]) -> List[Path]:
        """Extract list of files that will be affected."""
        files = set()
        
        for step in steps:
            if step.action_type in [ActionType.CREATE_FILE, ActionType.MODIFY_FILE, ActionType.DELETE_FILE]:
                if 'file_path' in step.parameters:
                    files.add(Path(step.parameters['file_path']))
                elif 'files' in step.parameters:
                    files.update(Path(f) for f in step.parameters['files'])
        
        return sorted(files)
    
    def _identify_required_approvals(self, steps: List[Step]) -> List[str]:
        """Identify which steps require user approval."""
        approvals = []
        
        for step in steps:
            if step.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
                approvals.append(step.id)
        
        return approvals
    
    def _build_dependency_graph(self, steps: List[Step]) -> Dict[str, List[str]]:
        """Build a dependency graph for the steps."""
        graph = {}
        
        for step in steps:
            graph[step.id] = step.dependencies
        
        return graph
    
    def _has_circular_dependencies(self, plan: ExecutionPlan) -> bool:
        """Check if the plan has circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            for dep in plan.dependencies.get(step_id, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in plan.steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    return True
        
        return False
    
    def _find_independent_steps(self, plan: ExecutionPlan) -> List[Step]:
        """Find steps that have no dependencies and could run in parallel."""
        return [step for step in plan.steps if not step.dependencies]
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get a plan by ID."""
        return self.plans.get(plan_id)
    
    def list_plans(self) -> List[ExecutionPlan]:
        """List all plans."""
        return list(self.plans.values())
    
    def get_execution_history(self) -> List[ExecutionResult]:
        """Get execution history."""
        return self.execution_history
