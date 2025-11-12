"""
Comprehensive end-to-end integration tests for the complete CodeGenie system.
Tests real-world scenarios and full system integration.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import json

from src.codegenie.core.agent import CodeGenieAgent
from src.codegenie.core.config import Config
from src.codegenie.core.session import SessionManager
from src.codegenie.core.end_to_end_workflows import (
    EndToEndWorkflowOrchestrator,
    WorkflowType
)
from src.codegenie.core.workflow_engine import WorkflowEngine
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.core.learning_engine import LearningEngine
from src.codegenie.agents.coordinator import AgentCoordinator
from src.codegenie.core.advanced_config import (
    AdvancedConfigurationManager,
    ConfigScope,
    UserPreferences
)


class TestRealWorldScenarios:
    """Test real-world development scenarios end-to-end."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create realistic project structure
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "api").mkdir()
        (temp_dir / "src" / "models").mkdir()
        (temp_dir / "src" / "utils").mkdir()
        (temp_dir / "tests").mkdir()
        (temp_dir / "docs").mkdir()
        
        # Create sample files
        (temp_dir / "README.md").write_text("# Sample Project\n")
        (temp_dir / "requirements.txt").write_text("fastapi\npydantic\npytest\n")
        (temp_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def complete_system(self, temp_project):
        """Set up complete CodeGenie system."""
        
        config = Mock()
        config.models = Mock()
        config.models.default = "llama3.1:8b"
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        config.adaptive_learning = True
        config.debug = False
        
        session_manager = SessionManager(temp_project, config)
        
        workflow_engine = WorkflowEngine(config)
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        # Mock successful execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=5.0)
        )
        agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="developer", completed=True)]
        )
        agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        learning_engine.learn_from_workflow = AsyncMock()
        learning_engine.get_user_profile = AsyncMock(
            return_value={"skill_level": "intermediate"}
        )
        
        agent = CodeGenieAgent(
            session_manager,
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        return {
            'agent': agent,
            'orchestrator': orchestrator,
            'session_manager': session_manager,
            'project_path': temp_project,
            'config': config
        }
    
    @pytest.mark.asyncio
    async def test_new_feature_development_scenario(self, complete_system):
        """Test complete new feature development from requirements to deployment."""
        
        orchestrator = complete_system['orchestrator']
        
        # Scenario: Developer wants to add user authentication feature
        goal = """
        Add user authentication feature with:
        - User registration and login endpoints
        - JWT token-based authentication
        - Password hashing with bcrypt
        - Email verification
        - Password reset functionality
        """
        
        context = {
            "feature_type": "authentication",
            "framework": "fastapi",
            "database": "postgresql",
            "security_level": "high"
        }
        
        # Create workflow
        workflow = await orchestrator.create_workflow(
            WorkflowType.FEATURE_DEVELOPMENT,
            goal,
            context
        )
        
        assert workflow is not None
        assert len(workflow.steps) > 0
        
        # Execute workflow
        result = await orchestrator.execute_workflow(
            workflow.id,
            autonomous=True
        )
        
        # Verify successful completion
        assert result.success
        assert workflow.status == "completed"
        
        # Verify expected workflow steps were included
        step_names = [step.name.lower() for step in workflow.steps]
        expected_keywords = ["requirements", "implement", "security", "test"]
        
        for keyword in expected_keywords:
            assert any(keyword in name for name in step_names)
    
    @pytest.mark.asyncio
    async def test_bug_fix_scenario(self, complete_system):
        """Test bug identification and fix workflow."""
        
        orchestrator = complete_system['orchestrator']
        
        # Scenario: Developer reports a bug
        bug_description = """
        Bug: API endpoint /users/{id} returns 500 error when user doesn't exist
        Expected: Should return 404 with appropriate error message
        Current: Server crashes with KeyError
        """
        
        context = {
            "bug_type": "error_handling",
            "severity": "high",
            "affected_endpoint": "/users/{id}",
            "error_type": "KeyError"
        }
        
        # Create bug fix workflow
        workflow = await orchestrator.create_workflow(
            WorkflowType.BUG_FIX,
            bug_description,
            context
        )
        
        assert workflow is not None
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Verify bug fix workflow completed
        assert result.success
        
        # Verify workflow included debugging and testing steps
        step_names = [step.name.lower() for step in workflow.steps]
        assert any("debug" in name or "analyze" in name for name in step_names)
        assert any("test" in name or "verify" in name for name in step_names)
    
    @pytest.mark.asyncio
    async def test_code_refactoring_scenario(self, complete_system):
        """Test code refactoring workflow."""
        
        orchestrator = complete_system['orchestrator']
        
        # Scenario: Developer wants to refactor legacy code
        refactoring_goal = """
        Refactor user service module:
        - Extract database operations into repository pattern
        - Separate business logic from API handlers
        - Add proper error handling
        - Improve code documentation
        - Maintain backward compatibility
        """
        
        context = {
            "refactoring_type": "architectural",
            "module": "user_service",
            "maintain_compatibility": True,
            "add_tests": True
        }
        
        # Create refactoring workflow
        workflow = await orchestrator.create_workflow(
            WorkflowType.CODE_REFACTORING,
            refactoring_goal,
            context
        )
        
        assert workflow is not None
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Verify refactoring completed
        assert result.success
        
        # Verify workflow included analysis and testing
        step_names = [step.name.lower() for step in workflow.steps]
        assert any("analyze" in name or "review" in name for name in step_names)
        assert any("test" in name for name in step_names)
    
    @pytest.mark.asyncio
    async def test_performance_optimization_scenario(self, complete_system):
        """Test performance optimization workflow."""
        
        orchestrator = complete_system['orchestrator']
        
        # Scenario: API response times are slow
        optimization_goal = """
        Optimize API performance:
        - Identify slow database queries
        - Add database indexes
        - Implement caching for frequently accessed data
        - Optimize N+1 query problems
        - Add query result pagination
        """
        
        context = {
            "optimization_type": "performance",
            "target_improvement": "50%",
            "focus_areas": ["database", "caching", "queries"]
        }
        
        # Create optimization workflow
        workflow = await orchestrator.create_workflow(
            WorkflowType.PERFORMANCE_OPTIMIZATION,
            optimization_goal,
            context
        )
        
        assert workflow is not None
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Verify optimization completed
        assert result.success
        
        # Verify workflow included profiling and benchmarking
        step_names = [step.name.lower() for step in workflow.steps]
        assert any("analyze" in name or "profile" in name for name in step_names)
        assert any("optimize" in name or "improve" in name for name in step_names)
    
    @pytest.mark.asyncio
    async def test_security_audit_scenario(self, complete_system):
        """Test security audit and remediation workflow."""
        
        orchestrator = complete_system['orchestrator']
        
        # Scenario: Security audit before production deployment
        security_goal = """
        Perform comprehensive security audit:
        - Scan for SQL injection vulnerabilities
        - Check authentication and authorization
        - Review data encryption practices
        - Audit dependency vulnerabilities
        - Verify input validation
        """
        
        context = {
            "audit_type": "comprehensive",
            "compliance_requirements": ["OWASP Top 10"],
            "auto_fix": True
        }
        
        # Create security audit workflow
        workflow = await orchestrator.create_workflow(
            WorkflowType.SECURITY_AUDIT,
            security_goal,
            context
        )
        
        assert workflow is not None
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Verify audit completed
        assert result.success
        
        # Verify workflow included scanning and remediation
        step_names = [step.name.lower() for step in workflow.steps]
        assert any("scan" in name or "audit" in name for name in step_names)
        assert any("fix" in name or "remediate" in name for name in step_names)


class TestSystemIntegration:
    """Test integration between all system components."""
    
    @pytest.fixture
    def integrated_system(self, tmp_path):
        """Set up fully integrated system."""
        
        config = Mock()
        config.models = Mock()
        config.models.default = "llama3.1:8b"
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        config.adaptive_learning = True
        
        # Create all components
        workflow_engine = WorkflowEngine(config)
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        config_manager = AdvancedConfigurationManager(base_path=tmp_path / ".codegenie")
        
        # Mock execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=3.0)
        )
        agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="test", completed=True)]
        )
        agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        
        return {
            'workflow_engine': workflow_engine,
            'context_engine': context_engine,
            'learning_engine': learning_engine,
            'agent_coordinator': agent_coordinator,
            'config_manager': config_manager,
            'config': config
        }
    
    @pytest.mark.asyncio
    async def test_workflow_context_integration(self, integrated_system):
        """Test integration between workflow engine and context engine."""
        
        workflow_engine = integrated_system['workflow_engine']
        context_engine = integrated_system['context_engine']
        
        # Store context
        await context_engine.store_interaction({
            'type': 'user_request',
            'content': 'Create REST API',
            'timestamp': '2024-01-01T00:00:00'
        })
        
        # Retrieve context for workflow
        context = await context_engine.retrieve_relevant_context('REST API development')
        
        assert context is not None
        assert len(context.conversation_history) > 0
        
        # Create workflow using context
        from src.codegenie.core.workflow_engine import WorkflowPlan
        
        plan = WorkflowPlan(
            id="test_plan",
            goal="Create REST API",
            tasks=[],
            context=context
        )
        
        # Execute with context
        result = await workflow_engine.execute_plan(plan)
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_learning_workflow_integration(self, integrated_system):
        """Test integration between learning engine and workflow execution."""
        
        workflow_engine = integrated_system['workflow_engine']
        learning_engine = integrated_system['learning_engine']
        
        # Mock user profile
        learning_engine.get_user_profile = AsyncMock(
            return_value={
                'coding_style': 'pep8',
                'skill_level': 'expert',
                'preferred_patterns': ['factory', 'singleton']
            }
        )
        
        # Get user profile
        profile = await learning_engine.get_user_profile()
        
        assert profile['skill_level'] == 'expert'
        assert 'factory' in profile['preferred_patterns']
        
        # Create workflow adapted to user profile
        from src.codegenie.core.workflow_engine import WorkflowPlan
        
        plan = WorkflowPlan(
            id="adaptive_plan",
            goal="Implement design pattern",
            tasks=[],
            user_profile=profile
        )
        
        result = await workflow_engine.execute_plan(plan)
        
        assert result.success
        
        # Learn from workflow execution
        await learning_engine.learn_from_workflow({
            'workflow_id': plan.id,
            'success': result.success,
            'user_feedback': {'rating': 5}
        })
    
    @pytest.mark.asyncio
    async def test_agent_coordination_integration(self, integrated_system):
        """Test integration between agent coordinator and workflow engine."""
        
        workflow_engine = integrated_system['workflow_engine']
        agent_coordinator = integrated_system['agent_coordinator']
        
        # Create task requiring multiple agents
        from src.codegenie.agents.base_agent import Task
        
        task = Task(
            description="Comprehensive code review",
            task_type="review",
            context={
                'review_aspects': ['security', 'performance', 'quality']
            }
        )
        
        # Delegate to multiple agents
        assignments = await agent_coordinator.delegate_task(task)
        
        assert len(assignments) > 0
        
        # Coordinate execution
        result = await agent_coordinator.coordinate_execution(assignments)
        
        assert result.success
    
    def test_configuration_system_integration(self, integrated_system):
        """Test configuration system integration with other components."""
        
        config_manager = integrated_system['config_manager']
        
        # Set user preferences
        preferences = UserPreferences(
            coding_style="black",
            preferred_languages=["python", "typescript"],
            skill_level="expert",
            interface_theme="dark",
            learning_enabled=True
        )
        
        config_manager.save_user_preferences(preferences)
        
        # Retrieve and verify
        loaded_prefs = config_manager.get_user_preferences()
        
        assert loaded_prefs.coding_style == "black"
        assert loaded_prefs.skill_level == "expert"
        assert loaded_prefs.learning_enabled is True
        
        # Set workflow configuration
        config_manager.set_config(
            "workflows.autonomous.enabled",
            True,
            ConfigScope.USER
        )
        
        # Verify workflow config
        workflow_enabled = config_manager.get_config("workflows.autonomous.enabled")
        
        assert workflow_enabled is True


class TestDataFlowIntegration:
    """Test data flow through the entire system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_data_flow(self, tmp_path):
        """Test data flow from user input to final output."""
        
        # Set up system
        config = Mock()
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        
        workflow_engine = WorkflowEngine(config)
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        # Mock execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=2.0, output="Generated code")
        )
        agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="developer", completed=True, output="Code implementation")]
        )
        agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True, results=["Result 1", "Result 2"])
        )
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        # 1. User input
        user_input = "Create a REST API endpoint for user management"
        
        # 2. Store in context
        await context_engine.store_interaction({
            'type': 'user_request',
            'content': user_input,
            'timestamp': '2024-01-01T00:00:00'
        })
        
        # 3. Create workflow
        workflow = await orchestrator.create_workflow(
            WorkflowType.FEATURE_DEVELOPMENT,
            user_input,
            {}
        )
        
        assert workflow is not None
        
        # 4. Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        assert result.success
        
        # 5. Store result in context
        await context_engine.store_interaction({
            'type': 'workflow_result',
            'workflow_id': workflow.id,
            'result': result,
            'timestamp': '2024-01-01T00:05:00'
        })
        
        # 6. Learn from execution
        await learning_engine.learn_from_workflow({
            'workflow_id': workflow.id,
            'workflow_type': WorkflowType.FEATURE_DEVELOPMENT.value,
            'success': result.success,
            'execution_time': result.execution_time
        })
        
        # 7. Retrieve context for next interaction
        context = await context_engine.retrieve_relevant_context('user management')
        
        assert context is not None
        assert len(context.conversation_history) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
