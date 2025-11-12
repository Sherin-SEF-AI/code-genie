"""
Unit tests for Planning Agent.

Tests the planning agent's ability to create execution plans,
break down tasks, estimate complexity, and validate plans.
"""

import pytest
import time
from datetime import timedelta
from pathlib import Path

from src.codegenie.core.planning_agent import (
    PlanningAgent, ExecutionPlan, Step, ActionType, RiskLevel,
    StepStatus, ComplexityEstimate, ValidationResult, ExecutionResult
)


class TestPlanningAgent:
    """Test suite for Planning Agent."""
    
    @pytest.fixture
    def planning_agent(self):
        """Create a planning agent instance."""
        return PlanningAgent()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample project context."""
        return {
            'project_type': 'python',
            'framework': 'fastapi',
            'existing_files': ['main.py', 'requirements.txt']
        }
    
    def test_initialization(self, planning_agent):
        """Test planning agent initialization."""
        assert planning_agent is not None
        assert planning_agent.plans == {}
        assert planning_agent.execution_history == []
    
    def test_create_plan_project_creation(self, planning_agent, sample_context):
        """Test creating a plan for project creation."""
        plan = planning_agent.create_plan(
            "Create a new FastAPI project",
            sample_context
        )
        
        assert isinstance(plan, ExecutionPlan)
        assert plan.id.startswith('plan_')
        assert len(plan.steps) > 0
        assert plan.estimated_duration > timedelta(0)
        assert plan.complexity is not None
        assert plan.validation is not None
    
    def test_create_plan_refactoring(self, planning_agent):
        """Test creating a plan for refactoring."""
        plan = planning_agent.create_plan("Refactor the authentication module")
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
        assert any(step.action_type == ActionType.REFACTOR_CODE for step in plan.steps)
    
    def test_create_plan_feature_addition(self, planning_agent):
        """Test creating a plan for adding a feature."""
        plan = planning_agent.create_plan("Add user authentication feature")
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
        assert any(step.action_type == ActionType.CREATE_FILE for step in plan.steps)
    
    def test_create_plan_bug_fix(self, planning_agent):
        """Test creating a plan for bug fix."""
        plan = planning_agent.create_plan("Fix the login bug")
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
        assert any(step.action_type == ActionType.MODIFY_FILE for step in plan.steps)
    
    def test_break_down_task_project_creation(self, planning_agent):
        """Test task breakdown for project creation."""
        tasks = planning_agent.break_down_task("Create a new project")
        
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert all('description' in task for task in tasks)
        assert all('action_type' in task for task in tasks)
    
    def test_estimate_complexity_simple(self, planning_agent):
        """Test complexity estimation for simple plan."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Simple task",
            steps=[
                Step(
                    id="step_1",
                    description="Do something",
                    action_type=ActionType.EXECUTE_COMMAND,
                    parameters={},
                    risk_level=RiskLevel.LOW
                )
            ],
            estimated_duration=timedelta(seconds=30),
            risk_level=RiskLevel.LOW
        )
        
        complexity = planning_agent.estimate_complexity(plan)
        
        assert isinstance(complexity, ComplexityEstimate)
        assert complexity.total_steps == 1
        assert complexity.complexity_level == "simple"
        assert complexity.confidence > 0.8
    
    def test_estimate_complexity_complex(self, planning_agent):
        """Test complexity estimation for complex plan."""
        steps = [
            Step(
                id=f"step_{i}",
                description=f"Step {i}",
                action_type=ActionType.MODIFY_FILE,
                parameters={},
                risk_level=RiskLevel.HIGH if i % 3 == 0 else RiskLevel.MEDIUM
            )
            for i in range(20)
        ]
        
        plan = ExecutionPlan(
            id="test_plan",
            description="Complex task",
            steps=steps,
            estimated_duration=timedelta(minutes=30),
            risk_level=RiskLevel.HIGH
        )
        
        complexity = planning_agent.estimate_complexity(plan)
        
        assert complexity.total_steps == 20
        assert complexity.complexity_level in ["complex", "very_complex"]
        assert complexity.risk_score > 0.5
    
    def test_validate_plan_valid(self, planning_agent):
        """Test validation of a valid plan."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Valid plan",
            steps=[
                Step(
                    id="step_1",
                    description="First step",
                    action_type=ActionType.CREATE_FILE,
                    parameters={},
                    dependencies=[]
                ),
                Step(
                    id="step_2",
                    description="Second step",
                    action_type=ActionType.MODIFY_FILE,
                    parameters={},
                    dependencies=["step_1"]
                )
            ],
            estimated_duration=timedelta(seconds=60),
            risk_level=RiskLevel.LOW,
            dependencies={"step_1": [], "step_2": ["step_1"]}
        )
        
        validation = planning_agent.validate_plan(plan)
        
        assert isinstance(validation, ValidationResult)
        assert validation.is_valid
        assert len(validation.errors) == 0
    
    def test_validate_plan_circular_dependency(self, planning_agent):
        """Test validation detects circular dependencies."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Plan with circular dependency",
            steps=[
                Step(
                    id="step_1",
                    description="First step",
                    action_type=ActionType.CREATE_FILE,
                    parameters={},
                    dependencies=["step_2"]
                ),
                Step(
                    id="step_2",
                    description="Second step",
                    action_type=ActionType.MODIFY_FILE,
                    parameters={},
                    dependencies=["step_1"]
                )
            ],
            estimated_duration=timedelta(seconds=60),
            risk_level=RiskLevel.LOW,
            dependencies={"step_1": ["step_2"], "step_2": ["step_1"]}
        )
        
        validation = planning_agent.validate_plan(plan)
        
        assert not validation.is_valid
        assert any("circular" in error.lower() for error in validation.errors)
    
    def test_validate_plan_missing_dependency(self, planning_agent):
        """Test validation detects missing dependencies."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Plan with missing dependency",
            steps=[
                Step(
                    id="step_1",
                    description="First step",
                    action_type=ActionType.CREATE_FILE,
                    parameters={},
                    dependencies=["step_nonexistent"]
                )
            ],
            estimated_duration=timedelta(seconds=30),
            risk_level=RiskLevel.LOW,
            dependencies={"step_1": ["step_nonexistent"]}
        )
        
        validation = planning_agent.validate_plan(plan)
        
        assert not validation.is_valid
        assert any("non-existent" in error.lower() for error in validation.errors)
    
    def test_execute_plan_success(self, planning_agent):
        """Test successful plan execution."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Simple plan",
            steps=[
                Step(
                    id="step_1",
                    description="First step",
                    action_type=ActionType.EXECUTE_COMMAND,
                    parameters={'command': 'echo test'},
                    risk_level=RiskLevel.SAFE
                )
            ],
            estimated_duration=timedelta(seconds=10),
            risk_level=RiskLevel.SAFE,
            dependencies={"step_1": []}
        )
        
        result = planning_agent.execute_plan(plan)
        
        assert isinstance(result, ExecutionResult)
        assert result.plan_id == plan.id
        assert result.completed_steps == 1
        assert result.failed_steps == 0
        assert result.success
    
    def test_execute_plan_with_approval(self, planning_agent):
        """Test plan execution with approval callback."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Plan requiring approval",
            steps=[
                Step(
                    id="step_1",
                    description="Risky step",
                    action_type=ActionType.DELETE_FILE,
                    parameters={},
                    risk_level=RiskLevel.HIGH
                )
            ],
            estimated_duration=timedelta(seconds=10),
            risk_level=RiskLevel.HIGH,
            dependencies={"step_1": []}
        )
        
        # Approval callback that rejects
        def reject_callback(step):
            return False
        
        result = planning_agent.execute_plan(plan, approval_callback=reject_callback)
        
        assert result.skipped_steps == 1
        assert result.completed_steps == 0
    
    def test_execute_plan_with_progress(self, planning_agent):
        """Test plan execution with progress callback."""
        progress_calls = []
        
        def progress_callback(step, current, total):
            progress_calls.append((step.id, current, total))
        
        plan = ExecutionPlan(
            id="test_plan",
            description="Plan with progress tracking",
            steps=[
                Step(
                    id=f"step_{i}",
                    description=f"Step {i}",
                    action_type=ActionType.EXECUTE_COMMAND,
                    parameters={},
                    risk_level=RiskLevel.SAFE
                )
                for i in range(3)
            ],
            estimated_duration=timedelta(seconds=30),
            risk_level=RiskLevel.SAFE,
            dependencies={f"step_{i}": [] for i in range(3)}
        )
        
        result = planning_agent.execute_plan(plan, progress_callback=progress_callback)
        
        assert len(progress_calls) == 3
        assert result.completed_steps == 3
    
    def test_get_plan(self, planning_agent):
        """Test retrieving a plan by ID."""
        plan = planning_agent.create_plan("Test task")
        
        retrieved = planning_agent.get_plan(plan.id)
        
        assert retrieved is not None
        assert retrieved.id == plan.id
    
    def test_list_plans(self, planning_agent):
        """Test listing all plans."""
        planning_agent.create_plan("Task 1")
        planning_agent.create_plan("Task 2")
        
        plans = planning_agent.list_plans()
        
        assert len(plans) == 2
    
    def test_execution_history(self, planning_agent):
        """Test execution history tracking."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Test plan",
            steps=[
                Step(
                    id="step_1",
                    description="Test step",
                    action_type=ActionType.EXECUTE_COMMAND,
                    parameters={},
                    risk_level=RiskLevel.SAFE
                )
            ],
            estimated_duration=timedelta(seconds=10),
            risk_level=RiskLevel.SAFE,
            dependencies={"step_1": []}
        )
        
        planning_agent.execute_plan(plan)
        
        history = planning_agent.get_execution_history()
        
        assert len(history) == 1
        assert history[0].plan_id == plan.id
    
    def test_step_to_dict(self):
        """Test Step serialization."""
        step = Step(
            id="step_1",
            description="Test step",
            action_type=ActionType.CREATE_FILE,
            parameters={'file': 'test.py'},
            risk_level=RiskLevel.LOW
        )
        
        step_dict = step.to_dict()
        
        assert step_dict['id'] == "step_1"
        assert step_dict['action_type'] == "create_file"
        assert step_dict['risk_level'] == "low"
    
    def test_plan_to_dict(self):
        """Test ExecutionPlan serialization."""
        plan = ExecutionPlan(
            id="test_plan",
            description="Test plan",
            steps=[],
            estimated_duration=timedelta(seconds=60),
            risk_level=RiskLevel.MEDIUM
        )
        
        plan_dict = plan.to_dict()
        
        assert plan_dict['id'] == "test_plan"
        assert plan_dict['risk_level'] == "medium"
        assert plan_dict['estimated_duration'] == 60.0
    
    def test_risk_level_comparison(self):
        """Test RiskLevel enum comparisons."""
        assert RiskLevel.SAFE < RiskLevel.LOW
        assert RiskLevel.LOW < RiskLevel.MEDIUM
        assert RiskLevel.MEDIUM < RiskLevel.HIGH
        assert RiskLevel.HIGH < RiskLevel.CRITICAL
        
        assert RiskLevel.CRITICAL > RiskLevel.SAFE
        assert RiskLevel.HIGH >= RiskLevel.MEDIUM
