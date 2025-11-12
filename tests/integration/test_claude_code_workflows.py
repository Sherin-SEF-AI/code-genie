"""
Integration tests for Claude Code features workflows.

Tests end-to-end workflows combining multiple components:
- Planning + File Creation + Command Execution
- Approval workflows across components
- Error recovery scenarios
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import timedelta

from src.codegenie.core.planning_agent import PlanningAgent, ActionType, RiskLevel
from src.codegenie.core.file_creator import FileCreator
from src.codegenie.core.command_executor import CommandExecutor
from src.codegenie.core.approval_system import ApprovalSystem, Operation, OperationType


class TestProjectCreationWorkflow:
    """Test complete project creation workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def planning_agent(self):
        """Create planning agent."""
        return PlanningAgent()
    
    @pytest.fixture
    def file_creator(self):
        """Create file creator."""
        return FileCreator(preview_by_default=False)
    
    @pytest.fixture
    async def command_executor(self):
        """Create command executor."""
        return CommandExecutor(default_timeout=10)
    
    @pytest.fixture
    def approval_system(self, temp_dir):
        """Create approval system."""
        return ApprovalSystem(
            preferences_file=temp_dir / "prefs.json",
            auto_approve_safe=True
        )
    
    def test_plan_and_create_project_structure(
        self,
        planning_agent,
        file_creator,
        temp_dir
    ):
        """Test planning and creating project structure."""
        # Create plan
        plan = planning_agent.create_plan(
            "Create a new Python project with FastAPI",
            {'project_type': 'python', 'framework': 'fastapi'}
        )
        
        assert plan is not None
        assert len(plan.steps) > 0
        
        # Create project structure based on plan
        structure = {
            'src': {
                'main.py': '# FastAPI application\n',
                '__init__.py': ''
            },
            'tests': {
                '__init__.py': '',
                'test_main.py': '# Tests\n'
            },
            'requirements.txt': 'fastapi\nuvicorn\n',
            'README.md': '# Project\n'
        }
        
        operations = file_creator.create_directory_structure(structure, temp_dir)
        
        assert len(operations) > 0
        assert all(op.status.value == "completed" for op in operations)
        assert (temp_dir / 'src' / 'main.py').exists()
        assert (temp_dir / 'requirements.txt').exists()
    
    @pytest.mark.asyncio
    async def test_plan_execute_and_verify(
        self,
        planning_agent,
        command_executor,
        temp_dir
    ):
        """Test planning, executing commands, and verifying results."""
        # Create a simple plan
        plan = planning_agent.create_plan(
            "Create a directory and list its contents"
        )
        
        # Execute commands based on plan
        test_dir = temp_dir / "test_project"
        
        # Create directory
        result1 = await command_executor.execute_command(
            f"mkdir -p {test_dir}",
            require_approval=False
        )
        
        assert result1.success
        assert test_dir.exists()
        
        # List directory
        result2 = await command_executor.execute_command(
            f"ls -la {test_dir}",
            require_approval=False
        )
        
        assert result2.success
    
    def test_approval_workflow_integration(
        self,
        approval_system,
        file_creator,
        temp_dir
    ):
        """Test approval system integration with file operations."""
        # Create file operation
        file_path = temp_dir / "test.txt"
        
        # Request approval through approval system
        operation = Operation(
            id="file_op_1",
            operation_type=OperationType.FILE_CREATE,
            description="Create test file",
            target=str(file_path),
            risk_level="low"
        )
        
        decision = approval_system.request_approval(operation)
        
        # Should be auto-approved
        assert decision.value in ["approved", "auto_approved"]
        
        # Now create the file
        file_op = file_creator.create_file(file_path, "Test content")
        
        assert file_op.status.value == "completed"
        assert file_path.exists()


class TestRefactoringWorkflow:
    """Test refactoring workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def planning_agent(self):
        """Create planning agent."""
        return PlanningAgent()
    
    @pytest.fixture
    def file_creator(self):
        """Create file creator."""
        return FileCreator(preview_by_default=False)
    
    def test_refactoring_plan_and_execution(
        self,
        planning_agent,
        file_creator,
        temp_dir
    ):
        """Test creating and executing a refactoring plan."""
        # Create initial file
        original_file = temp_dir / "module.py"
        original_content = """
def old_function():
    return "old"

def another_function():
    return old_function()
"""
        original_file.write_text(original_content)
        
        # Create refactoring plan
        plan = planning_agent.create_plan(
            "Refactor old_function to new_function"
        )
        
        assert plan is not None
        assert any(
            step.action_type == ActionType.REFACTOR_CODE
            for step in plan.steps
        )
        
        # Apply refactoring
        refactored_content = original_content.replace(
            "old_function",
            "new_function"
        )
        
        operation = file_creator.modify_file(original_file, refactored_content)
        
        assert operation.status.value == "completed"
        assert "new_function" in original_file.read_text()


class TestErrorRecoveryWorkflow:
    """Test error recovery workflows."""
    
    @pytest.fixture
    async def command_executor(self):
        """Create command executor."""
        return CommandExecutor(default_timeout=5)
    
    @pytest.mark.asyncio
    async def test_command_failure_and_recovery(self, command_executor):
        """Test command failure detection and recovery suggestions."""
        # Execute a command that will fail
        result = await command_executor.execute_command(
            "nonexistent_command",
            require_approval=False
        )
        
        assert not result.success
        assert result.error_analysis is not None
        assert result.error_analysis.error_type == "missing_command"
        assert len(result.recovery_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, command_executor):
        """Test automatic retry mechanism."""
        # This will fail but test retry logic
        result = await command_executor.execute_with_retry(
            "exit 1",
            max_retries=2
        )
        
        assert not result.success
        # Should have multiple attempts in history
        history = command_executor.get_command_history()
        assert len(history) >= 2


class TestComponentInteraction:
    """Test interactions between components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def planning_agent(self):
        """Create planning agent."""
        return PlanningAgent()
    
    @pytest.fixture
    def file_creator(self):
        """Create file creator with preview."""
        return FileCreator(preview_by_default=True)
    
    @pytest.fixture
    def approval_system(self, temp_dir):
        """Create approval system."""
        return ApprovalSystem(
            preferences_file=temp_dir / "prefs.json",
            auto_approve_safe=False
        )
    
    def test_plan_with_approval_gates(
        self,
        planning_agent,
        approval_system
    ):
        """Test plan execution with approval gates."""
        # Create a plan with risky operations
        plan = planning_agent.create_plan(
            "Delete old files and create new ones"
        )
        
        # Identify steps that need approval
        risky_steps = [
            step for step in plan.steps
            if step.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        ]
        
        # Request approval for risky steps
        for step in risky_steps:
            operation = Operation(
                id=step.id,
                operation_type=OperationType.CUSTOM,
                description=step.description,
                target=str(step.parameters),
                risk_level=step.risk_level.name.lower()
            )
            
            # In real scenario, this would prompt user
            decision = approval_system.request_approval(operation)
            
            # For test, we just verify the mechanism works
            assert decision is not None
    
    def test_file_operations_with_undo(
        self,
        file_creator,
        approval_system,
        temp_dir
    ):
        """Test file operations with undo capability."""
        # Create initial state
        file_path = temp_dir / "test.txt"
        file_path.write_text("Original content")
        
        # Create undo point
        from src.codegenie.core.approval_system import Operation, OperationType
        
        undo_point = approval_system.create_undo_point(
            operations=[],
            state_snapshot={'file_content': file_path.read_text()},
            description="Before modification"
        )
        
        # Modify file
        operation = file_creator.modify_file(file_path, "Modified content")
        
        assert operation.status.value == "previewed"
        
        # Approve and execute
        file_creator.approve_operation(operation)
        
        assert file_path.read_text() == "Modified content"
        
        # Verify undo point exists
        assert len(approval_system.undo_history) == 1


class TestBatchOperations:
    """Test batch operations across components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def file_creator(self):
        """Create file creator with preview."""
        return FileCreator(preview_by_default=True)
    
    @pytest.fixture
    def approval_system(self, temp_dir):
        """Create approval system."""
        return ApprovalSystem(preferences_file=temp_dir / "prefs.json")
    
    def test_batch_file_creation_with_approval(
        self,
        file_creator,
        approval_system,
        temp_dir
    ):
        """Test batch file creation with approval."""
        # Create multiple files
        files = [
            (temp_dir / f"file{i}.txt", f"Content {i}")
            for i in range(5)
        ]
        
        operations = []
        for file_path, content in files:
            op = file_creator.create_file(file_path, content)
            operations.append(op)
        
        # All should be pending
        assert len(file_creator.pending_operations) == 5
        
        # Batch approve
        results = file_creator.approve_all_pending()
        
        assert results['successful'] == 5
        assert all(f.exists() for f, _ in files)
    
    def test_conflict_detection_in_batch(
        self,
        approval_system
    ):
        """Test conflict detection in batch operations."""
        # Create conflicting operations
        operations = [
            Operation(
                id="op_1",
                operation_type=OperationType.FILE_MODIFY,
                description="Modify file",
                target="test.txt",
                risk_level="low"
            ),
            Operation(
                id="op_2",
                operation_type=OperationType.FILE_DELETE,
                description="Delete file",
                target="test.txt",
                risk_level="medium"
            )
        ]
        
        conflicts = approval_system.detect_conflicts(operations)
        
        assert len(conflicts) > 0
        assert not conflicts[0].resolved


class TestComplexWorkflows:
    """Test complex multi-step workflows."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def planning_agent(self):
        """Create planning agent."""
        return PlanningAgent()
    
    @pytest.fixture
    def file_creator(self):
        """Create file creator."""
        return FileCreator(preview_by_default=False)
    
    @pytest.fixture
    async def command_executor(self):
        """Create command executor."""
        return CommandExecutor(default_timeout=10)
    
    @pytest.mark.asyncio
    async def test_full_feature_implementation_workflow(
        self,
        planning_agent,
        file_creator,
        command_executor,
        temp_dir
    ):
        """Test complete feature implementation workflow."""
        # Step 1: Create plan
        plan = planning_agent.create_plan(
            "Add a new API endpoint for user authentication"
        )
        
        assert plan is not None
        assert plan.validation.is_valid
        
        # Step 2: Create necessary files
        api_file = temp_dir / "api.py"
        file_creator.create_file(
            api_file,
            """
from fastapi import APIRouter

router = APIRouter()

@router.post("/auth/login")
async def login(username: str, password: str):
    # Authentication logic here
    return {"token": "dummy_token"}
"""
        )
        
        assert api_file.exists()
        
        # Step 3: Create test file
        test_file = temp_dir / "test_api.py"
        file_creator.create_file(
            test_file,
            """
def test_login():
    # Test authentication endpoint
    assert True
"""
        )
        
        assert test_file.exists()
        
        # Step 4: Verify files were created
        result = await command_executor.execute_command(
            f"ls -la {temp_dir}",
            require_approval=False
        )
        
        assert result.success
        assert "api.py" in result.stdout
        assert "test_api.py" in result.stdout
    
    def test_plan_validation_and_execution(
        self,
        planning_agent
    ):
        """Test plan validation before execution."""
        # Create a complex plan
        plan = planning_agent.create_plan(
            "Refactor the entire authentication system"
        )
        
        # Validate the plan
        assert plan.validation is not None
        
        if not plan.validation.is_valid:
            # Should have error messages
            assert len(plan.validation.errors) > 0
        
        # Check complexity estimate
        assert plan.complexity is not None
        assert plan.complexity.total_steps > 0
        assert plan.complexity.complexity_level in [
            "simple", "moderate", "complex", "very_complex"
        ]
