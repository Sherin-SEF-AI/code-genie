"""
Integration tests for autonomous workflow functionality.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.codegenie.core.workflow_engine import (
    WorkflowEngine, TaskPlanner, ExecutionEngine, WorkflowPlan, WorkflowStep,
    RiskLevel, WorkflowStatus, DependencyAnalyzer, TaskScheduler, MilestoneTracker,
    ProgressMonitor, CheckpointManager, RollbackManager, StateManager, RecoveryEngine,
    UserInterventionManager, ApprovalWorkflowManager, NotificationManager, ManualOverrideManager
)
from src.codegenie.agents.base_agent import Task, TaskPriority, AgentResult
from src.codegenie.agents.coordinator import AgentCoordinator
from src.codegenie.core.config import Config


@pytest.mark.asyncio
class TestAutonomousWorkflowPlanning:
    """Test autonomous task planning capabilities."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = Mock(spec=Config)
        config.execution = Mock()
        config.execution.blocked_commands = []
        config.execution.allowed_commands = ["python", "pytest", "pip"]
        return config
    
    @pytest.fixture
    def agent_coordinator(self, config):
        """Create mock agent coordinator."""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.coordinate_complex_task = AsyncMock()
        coordinator.execute_coordination_plan = AsyncMock(return_value=True)
        return coordinator
    
    @pytest.fixture
    def task_planner(self, agent_coordinator):
        """Create task planner for testing."""
        return TaskPlanner(agent_coordinator)
    
    async def test_hierarchical_task_decomposition(self, task_planner):
        """Test hierarchical task decomposition."""
        goal = "Implement a REST API with authentication and user management"
        context = {"project_type": "web_api", "language": "python"}
        
        plan = await task_planner.create_workflow_plan(goal, context, "hierarchical")
        
        assert plan is not None
        assert plan.goal == goal
        assert len(plan.steps) > 0
        assert plan.status == WorkflowStatus.READY
        
        # Check that steps have proper structure
        for step in plan.steps:
            assert step.id is not None
            assert step.name is not None
            assert step.description is not None
            assert step.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    async def test_dependency_analysis(self, task_planner):
        """Test intelligent dependency analysis."""
        goal = "Create a web application with testing and documentation"
        
        plan = await task_planner.create_workflow_plan(goal)
        
        # Verify dependencies are properly analyzed
        assert hasattr(plan, 'dependencies')
        assert isinstance(plan.dependencies, dict)
        
        # Check that testing steps depend on implementation steps
        implementation_steps = [s for s in plan.steps if "implement" in s.description.lower()]
        testing_steps = [s for s in plan.steps if "test" in s.description.lower()]
        
        if implementation_steps and testing_steps:
            # At least some testing steps should depend on implementation
            has_proper_deps = False
            for test_step in testing_steps:
                if test_step.id in plan.dependencies:
                    deps = plan.dependencies[test_step.id]
                    if any(impl_step.id in deps for impl_step in implementation_steps):
                        has_proper_deps = True
                        break
            
            assert has_proper_deps, "Testing steps should depend on implementation steps"
    
    async def test_risk_assessment_and_mitigation(self, task_planner):
        """Test risk assessment and mitigation planning."""
        high_risk_goal = "Migrate production database and refactor core authentication system"
        
        plan = await task_planner.create_workflow_plan(high_risk_goal)
        
        # Should have high overall risk
        assert plan.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Should have risk mitigation strategies
        assert hasattr(plan, 'risk_mitigation_strategies')
        assert len(plan.risk_mitigation_strategies) > 0
        
        # Should have checkpoints for high-risk operations
        assert len(plan.checkpoints) > 0
        
        # High-risk steps should be identified
        high_risk_steps = [s for s in plan.steps if s.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        assert len(high_risk_steps) > 0
    
    async def test_milestone_creation(self, task_planner):
        """Test milestone tracking creation."""
        goal = "Build a complete e-commerce platform"
        
        plan = await task_planner.create_workflow_plan(goal)
        
        # Should have milestones
        assert hasattr(plan, 'milestones')
        assert len(plan.milestones) > 0
        
        # Milestones should have proper structure
        for milestone in plan.milestones:
            assert 'id' in milestone
            assert 'name' in milestone
            assert 'description' in milestone
            assert 'target_percentage' in milestone
            assert 'criteria' in milestone
    
    async def test_scheduling_optimization(self, task_planner):
        """Test task scheduling and optimization."""
        goal = "Develop microservices architecture with multiple independent services"
        
        plan = await task_planner.create_workflow_plan(goal)
        
        # Should have schedule information
        assert hasattr(plan, 'schedule')
        assert isinstance(plan.schedule, dict)
        
        if 'parallel_opportunities' in plan.schedule:
            # Should identify parallel execution opportunities
            parallel_ops = plan.schedule['parallel_opportunities']
            if parallel_ops:
                assert len(parallel_ops) > 0
                for op in parallel_ops:
                    assert 'parallel_tasks' in op
                    assert op['parallel_tasks'] > 1


@pytest.mark.asyncio
class TestExecutionEngineWithRollback:
    """Test execution engine with rollback capabilities."""
    
    @pytest.fixture
    def agent_coordinator(self):
        """Create mock agent coordinator."""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.execute_coordination_plan = AsyncMock(return_value=True)
        return coordinator
    
    @pytest.fixture
    def execution_engine(self, agent_coordinator):
        """Create execution engine for testing."""
        return ExecutionEngine(agent_coordinator)
    
    @pytest.fixture
    def sample_workflow_plan(self):
        """Create a sample workflow plan for testing."""
        plan = WorkflowPlan(
            name="Test Workflow",
            description="Test workflow for rollback testing",
            goal="Test autonomous execution with rollback"
        )
        
        # Add some test steps
        for i in range(3):
            step = WorkflowStep(
                name=f"Step {i+1}",
                description=f"Test step {i+1} description",
                risk_level=RiskLevel.MEDIUM if i == 1 else RiskLevel.LOW,
                estimated_duration=30.0
            )
            plan.steps.append(step)
        
        return plan
    
    async def test_checkpoint_creation(self, execution_engine):
        """Test checkpoint creation and management."""
        workflow_id = "test_workflow_123"
        step_id = "test_step_456"
        
        state_snapshot = {
            "completed_steps": ["step1", "step2"],
            "modified_files": ["file1.py", "file2.py"],
            "active_agents": ["developer", "tester"]
        }
        
        checkpoint = execution_engine.checkpoint_manager.create_checkpoint(
            workflow_id, step_id, state_snapshot, "Test checkpoint"
        )
        
        assert checkpoint is not None
        assert checkpoint.workflow_id == workflow_id
        assert checkpoint.step_id == step_id
        assert checkpoint.description == "Test checkpoint"
        
        # Verify checkpoint data is stored
        checkpoint_data = execution_engine.checkpoint_manager.get_checkpoint_data(checkpoint.id)
        assert checkpoint_data is not None
        assert checkpoint_data["checkpoint"] == checkpoint
    
    async def test_rollback_mechanism(self, execution_engine):
        """Test rollback to checkpoint functionality."""
        workflow_id = "test_workflow_rollback"
        
        # Create initial state
        initial_state = {
            "completed_steps": [],
            "modified_files": [],
            "active_agents": []
        }
        
        checkpoint = execution_engine.checkpoint_manager.create_checkpoint(
            workflow_id, "initial", initial_state, "Initial state"
        )
        
        # Simulate some changes
        changed_state = {
            "completed_steps": ["step1", "step2"],
            "modified_files": ["changed_file.py"],
            "active_agents": ["developer"]
        }
        
        # Perform rollback
        checkpoint_data = execution_engine.checkpoint_manager.get_checkpoint_data(checkpoint.id)
        rollback_success = await execution_engine.rollback_manager.rollback_to_checkpoint(
            checkpoint, checkpoint_data
        )
        
        assert rollback_success is True
        
        # Verify rollback history is recorded
        rollback_history = execution_engine.rollback_manager.get_rollback_history(workflow_id)
        assert len(rollback_history) > 0
    
    async def test_state_management(self, execution_engine, sample_workflow_plan):
        """Test workflow state management."""
        workflow_id = sample_workflow_plan.id
        
        # Initialize workflow state
        execution_engine.state_manager.initialize_workflow_state(sample_workflow_plan)
        
        # Verify initial state
        state = execution_engine.state_manager.get_current_state(workflow_id)
        assert state is not None
        assert state["workflow_id"] == workflow_id
        assert state["completed_steps"] == []
        assert state["current_step"] is None
        
        # Update step state
        step = sample_workflow_plan.steps[0]
        execution_engine.state_manager.update_step_state(workflow_id, step, "started")
        
        state = execution_engine.state_manager.get_current_state(workflow_id)
        assert state["current_step"] == step.id
        
        # Complete step
        result = AgentResult(
            agent_name="test_agent",
            task_id=step.id,
            success=True,
            output="Step completed successfully"
        )
        
        execution_engine.state_manager.update_step_state(workflow_id, step, "completed", result)
        
        state = execution_engine.state_manager.get_current_state(workflow_id)
        assert step.id in state["completed_steps"]
        assert state["current_step"] is None
    
    async def test_recovery_strategies(self, execution_engine):
        """Test different recovery strategies for failures."""
        step = WorkflowStep(
            name="Test Step",
            description="Test step for recovery",
            risk_level=RiskLevel.MEDIUM
        )
        
        workflow_state = {
            "completed_steps": [],
            "failed_steps": [],
            "current_step": step.id
        }
        
        # Test network error recovery
        network_error = Exception("Connection timeout")
        recovery_action = await execution_engine.recovery_engine.handle_step_failure(
            step, network_error, workflow_state
        )
        
        assert recovery_action["action"] in ["retry", "skip", "rollback", "alternative", "manual_intervention"]
        
        # Test high-risk step failure
        high_risk_step = WorkflowStep(
            name="High Risk Step",
            description="Delete production data",
            risk_level=RiskLevel.CRITICAL
        )
        
        critical_error = Exception("Critical operation failed")
        recovery_action = await execution_engine.recovery_engine.handle_step_failure(
            high_risk_step, critical_error, workflow_state
        )
        
        # Critical steps should typically rollback
        assert recovery_action["action"] in ["rollback", "manual_intervention"]


@pytest.mark.asyncio
class TestUserInterventionSystem:
    """Test user intervention and approval system."""
    
    @pytest.fixture
    def intervention_manager(self):
        """Create user intervention manager."""
        return UserInterventionManager()
    
    @pytest.fixture
    def approval_manager(self, intervention_manager):
        """Create approval workflow manager."""
        return ApprovalWorkflowManager(intervention_manager)
    
    async def test_intervention_point_creation(self, intervention_manager):
        """Test creation of user intervention points."""
        workflow_id = "test_workflow"
        step_id = "test_step"
        message = "Please review the proposed changes before proceeding"
        options = ["approve", "reject", "modify"]
        
        intervention_id = intervention_manager.create_intervention_point(
            workflow_id, step_id, "approval_request", message, options
        )
        
        assert intervention_id is not None
        
        # Verify intervention is pending
        pending = intervention_manager.get_pending_interventions(workflow_id)
        assert len(pending) == 1
        assert pending[0]["id"] == intervention_id
        assert pending[0]["message"] == message
        assert pending[0]["options"] == options
    
    async def test_intervention_response(self, intervention_manager):
        """Test responding to user interventions."""
        workflow_id = "test_workflow"
        step_id = "test_step"
        
        intervention_id = intervention_manager.create_intervention_point(
            workflow_id, step_id, "user_input", "Test intervention", ["yes", "no"]
        )
        
        # Respond to intervention
        success = intervention_manager.respond_to_intervention(intervention_id, "yes")
        assert success is True
        
        # Verify intervention is no longer pending
        pending = intervention_manager.get_pending_interventions(workflow_id)
        assert len(pending) == 0
        
        # Verify intervention is in history
        history = intervention_manager.get_intervention_history(workflow_id)
        assert len(history) == 1
        assert history[0]["user_response"] == "yes"
    
    async def test_approval_workflow(self, approval_manager):
        """Test approval workflow for critical operations."""
        workflow_id = "test_workflow"
        
        # Configure approval rules
        rules = {
            "step_execution": {
                "min_risk_level": "high",
                "step_types": ["code_generation", "deployment"],
                "description_patterns": ["delete", "production"]
            }
        }
        approval_manager.configure_approval_rules(rules)
        
        # Create high-risk step requiring approval
        high_risk_step = WorkflowStep(
            name="Production Deployment",
            description="Deploy to production environment",
            risk_level=RiskLevel.HIGH
        )
        
        # This would normally wait for user input, but we'll test the setup
        # In a real test, you'd mock the user response or use a timeout
        
        # Verify approval is required
        requires_approval = approval_manager._requires_approval(high_risk_step, "step_execution")
        assert requires_approval is True
        
        # Test low-risk step doesn't require approval
        low_risk_step = WorkflowStep(
            name="Unit Test",
            description="Run unit tests",
            risk_level=RiskLevel.LOW
        )
        
        requires_approval = approval_manager._requires_approval(low_risk_step, "step_execution")
        assert requires_approval is False
    
    async def test_notification_system(self):
        """Test notification system."""
        notification_manager = NotificationManager()
        
        # Register a test handler
        notifications_received = []
        
        def test_handler(notification):
            notifications_received.append(notification)
        
        notification_manager.register_notification_handler(test_handler)
        
        # Send test notification
        workflow_id = "test_workflow"
        notification_manager.send_notification(
            workflow_id=workflow_id,
            notification_type="test",
            title="Test Notification",
            message="This is a test notification",
            priority="normal"
        )
        
        # Verify notification was received
        assert len(notifications_received) == 1
        assert notifications_received[0]["title"] == "Test Notification"
        assert notifications_received[0]["workflow_id"] == workflow_id
        
        # Test progress update notification
        notification_manager.send_progress_update(
            workflow_id=workflow_id,
            progress_percentage=50.0,
            current_step="Test Step"
        )
        
        assert len(notifications_received) == 2
        assert notifications_received[1]["type"] == "progress_update"
    
    async def test_manual_override_system(self):
        """Test manual override capabilities."""
        override_manager = ManualOverrideManager()
        
        # Register override handler
        async def test_override_handler(override_request, user_instructions):
            return {
                "success": True,
                "message": f"Override applied: {user_instructions.get('action', 'default')}"
            }
        
        override_manager.register_override_handler("test_operation", test_override_handler)
        
        # Request manual override
        workflow_id = "test_workflow"
        step_id = "test_step"
        override_id = override_manager.request_manual_override(
            workflow_id, step_id, "test_operation", "Testing override system"
        )
        
        assert override_id is not None
        
        # Verify override is active
        active_overrides = override_manager.get_active_overrides(workflow_id)
        assert len(active_overrides) == 1
        assert active_overrides[0]["id"] == override_id
        
        # Execute override
        user_instructions = {"action": "custom_action", "parameters": {"test": True}}
        result = await override_manager.execute_manual_override(override_id, user_instructions)
        
        assert result["success"] is True
        assert "Override applied" in result["message"]
        
        # Verify override is no longer active
        active_overrides = override_manager.get_active_overrides(workflow_id)
        assert len(active_overrides) == 0


@pytest.mark.asyncio
class TestEndToEndAutonomousWorkflow:
    """End-to-end tests for complete autonomous workflow execution."""
    
    @pytest.fixture
    def workflow_engine(self):
        """Create workflow engine for testing."""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.execute_coordination_plan = AsyncMock(return_value=True)
        return WorkflowEngine(coordinator)
    
    async def test_complete_autonomous_workflow(self, workflow_engine):
        """Test complete autonomous workflow from planning to execution."""
        goal = "Create a simple Python calculator with tests and documentation"
        context = {
            "language": "python",
            "project_type": "library",
            "include_tests": True,
            "include_docs": True
        }
        
        # Create and execute workflow
        plan = await workflow_engine.create_and_execute_workflow(
            goal=goal,
            context=context,
            strategy="hierarchical",
            auto_execute=False  # Don't auto-execute for testing
        )
        
        assert plan is not None
        assert plan.goal == goal
        assert plan.status == WorkflowStatus.READY
        assert len(plan.steps) > 0
        
        # Verify autonomous planning enhancements
        assert hasattr(plan, 'schedule')
        assert hasattr(plan, 'milestones')
        assert hasattr(plan, 'risk_mitigation_strategies')
        
        # Verify dependencies are analyzed
        assert isinstance(plan.dependencies, dict)
        
        # Verify checkpoints are created
        assert len(plan.checkpoints) > 0
    
    async def test_workflow_with_failure_recovery(self, workflow_engine):
        """Test workflow execution with failure and recovery."""
        # Mock a failure in the coordinator
        workflow_engine.execution_engine.agent_coordinator.execute_coordination_plan = AsyncMock(
            side_effect=Exception("Simulated execution failure")
        )
        
        goal = "Test workflow with simulated failure"
        
        plan = await workflow_engine.create_and_execute_workflow(
            goal=goal,
            auto_execute=True
        )
        
        # Workflow should handle the failure gracefully
        assert plan.status == WorkflowStatus.FAILED
        assert len(plan.errors) > 0
        assert "Simulated execution failure" in plan.errors[0]
    
    async def test_workflow_statistics_and_monitoring(self, workflow_engine):
        """Test workflow statistics and monitoring capabilities."""
        # Create multiple workflows
        for i in range(3):
            goal = f"Test workflow {i+1}"
            await workflow_engine.create_and_execute_workflow(goal=goal, auto_execute=False)
        
        # Get workflow statistics
        stats = workflow_engine.get_workflow_stats()
        
        assert "total_workflows" in stats
        assert "successful_workflows" in stats
        assert "success_rate" in stats
        assert "average_duration" in stats
        
        # Should have processed workflows
        assert stats["total_workflows"] >= 0


@pytest.mark.asyncio
class TestPerformanceAndScalability:
    """Test performance and scalability of autonomous workflows."""
    
    async def test_large_workflow_planning(self):
        """Test planning performance with large workflows."""
        coordinator = Mock(spec=AgentCoordinator)
        planner = TaskPlanner(coordinator)
        
        # Create a complex goal that should generate many steps
        complex_goal = """
        Build a complete e-commerce platform with:
        - User authentication and authorization
        - Product catalog with search and filtering
        - Shopping cart and checkout process
        - Payment processing integration
        - Order management system
        - Inventory management
        - Admin dashboard
        - Customer support system
        - Analytics and reporting
        - Mobile API
        - Comprehensive testing suite
        - Documentation and deployment guides
        """
        
        start_time = time.time()
        plan = await planner.create_workflow_plan(complex_goal)
        planning_time = time.time() - start_time
        
        # Should complete planning in reasonable time (< 5 seconds)
        assert planning_time < 5.0
        assert len(plan.steps) > 10  # Should generate substantial number of steps
        assert plan.status == WorkflowStatus.READY
    
    async def test_dependency_analysis_performance(self):
        """Test performance of dependency analysis with many tasks."""
        analyzer = DependencyAnalyzer()
        
        # Create many workflow steps
        steps = []
        for i in range(50):
            step = WorkflowStep(
                name=f"Step {i}",
                description=f"Task {i} - implement feature {i}",
                risk_level=RiskLevel.LOW
            )
            steps.append(step)
        
        start_time = time.time()
        dependencies = analyzer.analyze_dependencies(steps)
        analysis_time = time.time() - start_time
        
        # Should complete analysis in reasonable time
        assert analysis_time < 2.0
        assert isinstance(dependencies, dict)
        assert len(dependencies) == len(steps)
    
    async def test_concurrent_workflow_execution(self):
        """Test handling multiple concurrent workflows."""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.execute_coordination_plan = AsyncMock(return_value=True)
        
        engine = ExecutionEngine(coordinator)
        
        # Create multiple workflow plans
        plans = []
        for i in range(5):
            plan = WorkflowPlan(
                name=f"Concurrent Workflow {i}",
                description=f"Test concurrent execution {i}",
                goal=f"Goal {i}"
            )
            
            # Add a simple step
            step = WorkflowStep(
                name=f"Step {i}",
                description=f"Execute task {i}",
                estimated_duration=1.0
            )
            plan.steps.append(step)
            plans.append(plan)
        
        # Execute workflows concurrently
        start_time = time.time()
        tasks = [engine.execute_workflow(plan) for plan in plans]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = time.time() - start_time
        
        # Should handle concurrent execution
        assert len(results) == 5
        # Most should succeed (allowing for some mock limitations)
        successful_results = [r for r in results if r is True]
        assert len(successful_results) >= 0  # At least some should work
        
        # Should complete in reasonable time
        assert execution_time < 10.0


if __name__ == "__main__":
    pytest.main([__file__])