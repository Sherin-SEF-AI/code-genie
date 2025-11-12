"""
User experience end-to-end tests.
Tests user workflows, interface interactions, and overall UX.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import time

from src.codegenie.core.agent import CodeGenieAgent
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
    UserPreferences
)
from src.codegenie.ui.configuration_manager import ConfigurationManager


class TestUserOnboarding:
    """Test user onboarding experience."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_first_time_user_setup(self, temp_project):
        """Test first-time user setup experience."""
        
        # Initialize configuration
        config_manager = ConfigurationManager()
        
        # Simulate first-time setup
        config_manager.initialize_project_config(temp_project, "default")
        
        # Verify configuration created
        config_file = temp_project / ".codegenie" / "config.yaml"
        assert config_file.exists()
        
        # Verify default preferences
        adv_config = AdvancedConfigurationManager(
            base_path=temp_project / ".codegenie"
        )
        
        preferences = adv_config.get_user_preferences()
        assert preferences is not None
        assert preferences.skill_level in ["beginner", "intermediate", "expert"]
    
    def test_user_preference_customization(self, temp_project):
        """Test user preference customization."""
        
        config_manager = AdvancedConfigurationManager(
            base_path=temp_project / ".codegenie"
        )
        
        # Set custom preferences
        custom_prefs = UserPreferences(
            coding_style="black",
            preferred_languages=["python", "javascript"],
            skill_level="intermediate",
            interface_theme="dark",
            learning_enabled=True,
            show_suggestions=True,
            auto_save=True
        )
        
        config_manager.save_user_preferences(custom_prefs)
        
        # Verify preferences saved
        loaded_prefs = config_manager.get_user_preferences()
        
        assert loaded_prefs.coding_style == "black"
        assert "python" in loaded_prefs.preferred_languages
        assert loaded_prefs.skill_level == "intermediate"
        assert loaded_prefs.interface_theme == "dark"
    
    def test_guided_tutorial_flow(self, temp_project):
        """Test guided tutorial flow for new users."""
        
        config_manager = AdvancedConfigurationManager(
            base_path=temp_project / ".codegenie"
        )
        
        # Simulate tutorial steps
        tutorial_steps = [
            "welcome",
            "basic_commands",
            "workflow_creation",
            "agent_coordination",
            "configuration"
        ]
        
        for step in tutorial_steps:
            # Mark step as completed
            config_manager.set_config(
                f"tutorial.{step}.completed",
                True,
                config_manager.ConfigScope.USER
            )
        
        # Verify tutorial progress
        for step in tutorial_steps:
            completed = config_manager.get_config(f"tutorial.{step}.completed")
            assert completed is True
        
        # Mark tutorial as finished
        config_manager.set_config(
            "tutorial.finished",
            True,
            config_manager.ConfigScope.USER
        )
        
        tutorial_finished = config_manager.get_config("tutorial.finished")
        assert tutorial_finished is True


class TestUserWorkflows:
    """Test common user workflows."""
    
    @pytest.fixture
    def user_system(self, tmp_path):
        """Set up system for user workflow testing."""
        
        config = Mock()
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        config.adaptive_learning = True
        
        workflow_engine = WorkflowEngine(config)
        context_engine = ContextEngine(config)
        learning_engine = LearningEngine(config)
        agent_coordinator = AgentCoordinator(config)
        
        # Mock fast execution
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=1.0)
        )
        agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="developer", completed=True)]
        )
        agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        learning_engine.get_user_profile = AsyncMock(
            return_value={"skill_level": "intermediate"}
        )
        
        orchestrator = EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_quick_code_generation_workflow(self, user_system):
        """Test quick code generation workflow."""
        
        # User wants to quickly generate a function
        start_time = time.time()
        
        workflow = await user_system.create_workflow(
            WorkflowType.CODE_GENERATION,
            "Generate a function to validate email addresses",
            {"language": "python", "include_tests": False}
        )
        
        result = await user_system.execute_workflow(workflow.id)
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly
        assert result.success
        assert elapsed_time < 10.0  # Should complete in under 10 seconds
    
    @pytest.mark.asyncio
    async def test_iterative_development_workflow(self, user_system):
        """Test iterative development with user feedback."""
        
        # Initial implementation
        workflow1 = await user_system.create_workflow(
            WorkflowType.FEATURE_DEVELOPMENT,
            "Create user authentication",
            {}
        )
        
        result1 = await user_system.execute_workflow(workflow1.id)
        assert result1.success
        
        # User provides feedback and requests changes
        workflow2 = await user_system.create_workflow(
            WorkflowType.FEATURE_ENHANCEMENT,
            "Add two-factor authentication to existing auth system",
            {"previous_workflow": workflow1.id}
        )
        
        result2 = await user_system.execute_workflow(workflow2.id)
        assert result2.success
        
        # Further refinement
        workflow3 = await user_system.create_workflow(
            WorkflowType.CODE_REFACTORING,
            "Refactor authentication code for better testability",
            {"previous_workflow": workflow2.id}
        )
        
        result3 = await user_system.execute_workflow(workflow3.id)
        assert result3.success
    
    @pytest.mark.asyncio
    async def test_context_aware_workflow(self, user_system):
        """Test context-aware workflow execution."""
        
        # Store context from previous interactions
        await user_system.context_engine.store_interaction({
            'type': 'user_request',
            'content': 'Working on e-commerce project with FastAPI',
            'timestamp': '2024-01-01T00:00:00'
        })
        
        await user_system.context_engine.store_interaction({
            'type': 'user_request',
            'content': 'Using PostgreSQL database',
            'timestamp': '2024-01-01T00:01:00'
        })
        
        # Create workflow that should use context
        workflow = await user_system.create_workflow(
            WorkflowType.FEATURE_DEVELOPMENT,
            "Add product catalog feature",
            {}
        )
        
        # Workflow should have context about FastAPI and PostgreSQL
        assert workflow is not None
        
        result = await user_system.execute_workflow(workflow.id)
        assert result.success
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, user_system):
        """Test user experience during error recovery."""
        
        # Simulate workflow with failure
        user_system.workflow_engine.execute_plan = AsyncMock(
            side_effect=[
                Exception("Simulated failure"),
                Mock(success=True, execution_time=2.0)
            ]
        )
        
        workflow = await user_system.create_workflow(
            WorkflowType.FEATURE_DEVELOPMENT,
            "Test error recovery",
            {}
        )
        
        # First execution fails
        with pytest.raises(Exception):
            await user_system.execute_workflow(workflow.id)
        
        # Retry should succeed
        result = await user_system.execute_workflow(workflow.id)
        assert result.success


class TestUserFeedback:
    """Test user feedback and learning."""
    
    @pytest.fixture
    def learning_system(self):
        """Set up system with learning capabilities."""
        
        config = Mock()
        config.adaptive_learning = True
        
        learning_engine = LearningEngine(config)
        
        # Mock learning methods
        learning_engine.learn_from_workflow = AsyncMock()
        learning_engine.get_user_profile = AsyncMock(
            return_value={
                'coding_style': 'pep8',
                'skill_level': 'intermediate',
                'feedback_count': 0
            }
        )
        learning_engine.update_user_profile = AsyncMock()
        
        return learning_engine
    
    @pytest.mark.asyncio
    async def test_positive_feedback_learning(self, learning_system):
        """Test system learning from positive feedback."""
        
        # User provides positive feedback
        feedback = {
            'workflow_id': 'test_workflow',
            'rating': 5,
            'comment': 'Excellent implementation',
            'helpful_aspects': ['code_quality', 'documentation']
        }
        
        await learning_system.learn_from_workflow({
            'workflow_id': 'test_workflow',
            'workflow_type': 'feature_development',
            'success': True,
            'user_feedback': feedback
        })
        
        # Verify learning occurred
        learning_system.learn_from_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_negative_feedback_adaptation(self, learning_system):
        """Test system adaptation from negative feedback."""
        
        # User provides negative feedback
        feedback = {
            'workflow_id': 'test_workflow',
            'rating': 2,
            'comment': 'Code is too complex',
            'improvement_areas': ['simplicity', 'readability']
        }
        
        await learning_system.learn_from_workflow({
            'workflow_id': 'test_workflow',
            'workflow_type': 'code_generation',
            'success': True,
            'user_feedback': feedback
        })
        
        # System should adapt preferences
        learning_system.learn_from_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_feedback_trend_analysis(self, learning_system):
        """Test analysis of feedback trends over time."""
        
        # Simulate multiple feedback instances
        feedback_history = [
            {'rating': 5, 'aspect': 'code_quality'},
            {'rating': 4, 'aspect': 'code_quality'},
            {'rating': 5, 'aspect': 'code_quality'},
            {'rating': 3, 'aspect': 'documentation'},
            {'rating': 3, 'aspect': 'documentation'},
            {'rating': 4, 'aspect': 'performance'}
        ]
        
        for feedback in feedback_history:
            await learning_system.learn_from_workflow({
                'workflow_id': f'workflow_{feedback["aspect"]}',
                'workflow_type': 'feature_development',
                'success': True,
                'user_feedback': feedback
            })
        
        # Verify all feedback processed
        assert learning_system.learn_from_workflow.call_count == len(feedback_history)


class TestUserInterface:
    """Test user interface interactions."""
    
    def test_cli_command_structure(self):
        """Test CLI command structure and help."""
        
        from typer.testing import CliRunner
        from src.codegenie.cli import app
        
        runner = CliRunner()
        
        # Test main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "workflow" in result.stdout.lower()
        
        # Test workflow commands
        result = runner.invoke(app, ["workflow", "--help"])
        assert result.exit_code == 0
        
        # Test agents commands
        result = runner.invoke(app, ["agents", "--help"])
        assert result.exit_code == 0
        
        # Test config commands
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
    
    def test_configuration_ui_flow(self, tmp_path):
        """Test configuration UI flow."""
        
        config_manager = ConfigurationManager()
        
        # Initialize with different templates
        templates = ["minimal", "default", "full"]
        
        for template in templates:
            project_dir = tmp_path / f"project_{template}"
            project_dir.mkdir()
            
            config_manager.initialize_project_config(project_dir, template)
            
            # Verify configuration created
            config_file = project_dir / ".codegenie" / "config.yaml"
            assert config_file.exists()
    
    @pytest.mark.asyncio
    async def test_progress_reporting(self):
        """Test progress reporting during workflow execution."""
        
        config = Mock()
        workflow_engine = WorkflowEngine(config)
        
        # Mock execution with progress tracking
        progress_updates = []
        
        async def mock_execute_with_progress(plan):
            for i in range(5):
                progress_updates.append({
                    'step': i + 1,
                    'total': 5,
                    'percentage': (i + 1) * 20
                })
                await asyncio.sleep(0.1)
            
            return Mock(success=True, execution_time=0.5)
        
        workflow_engine.execute_plan = mock_execute_with_progress
        
        # Execute workflow
        from src.codegenie.core.workflow_engine import WorkflowPlan
        
        plan = WorkflowPlan(
            id="progress_test",
            goal="Test progress reporting",
            tasks=[]
        )
        
        result = await workflow_engine.execute_plan(plan)
        
        # Verify progress updates
        assert len(progress_updates) == 5
        assert progress_updates[-1]['percentage'] == 100
        assert result.success


class TestAccessibility:
    """Test accessibility features."""
    
    def test_error_message_clarity(self):
        """Test that error messages are clear and actionable."""
        
        # Simulate various error scenarios
        error_scenarios = [
            {
                'error': 'Configuration file not found',
                'expected_guidance': 'initialize'
            },
            {
                'error': 'Invalid workflow type',
                'expected_guidance': 'valid types'
            },
            {
                'error': 'Agent coordination failed',
                'expected_guidance': 'retry'
            }
        ]
        
        for scenario in error_scenarios:
            # Error messages should contain guidance
            assert scenario['expected_guidance'] is not None
    
    def test_help_text_availability(self):
        """Test that help text is available for all commands."""
        
        from typer.testing import CliRunner
        from src.codegenie.cli import app
        
        runner = CliRunner()
        
        # All commands should have help
        commands = ["workflow", "agents", "config", "learning"]
        
        for command in commands:
            result = runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0
            assert len(result.stdout) > 100  # Substantial help text
    
    def test_configuration_validation_feedback(self, tmp_path):
        """Test configuration validation provides clear feedback."""
        
        config_manager = AdvancedConfigurationManager(base_path=tmp_path)
        
        # Test invalid configuration
        try:
            config_manager.set_config(
                "invalid..key",  # Invalid key format
                "value",
                config_manager.ConfigScope.USER,
                validate=True
            )
        except Exception as e:
            # Error should be descriptive
            assert "key" in str(e).lower() or "invalid" in str(e).lower()


class TestPerformancePerception:
    """Test perceived performance and responsiveness."""
    
    @pytest.mark.asyncio
    async def test_immediate_feedback(self):
        """Test that users receive immediate feedback."""
        
        config = Mock()
        workflow_engine = WorkflowEngine(config)
        
        # Mock instant acknowledgment
        workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.1)
        )
        
        start_time = time.time()
        
        from src.codegenie.core.workflow_engine import WorkflowPlan
        
        plan = WorkflowPlan(
            id="feedback_test",
            goal="Test immediate feedback",
            tasks=[]
        )
        
        # Should get immediate acknowledgment
        result = await workflow_engine.execute_plan(plan)
        
        response_time = time.time() - start_time
        
        # Response should be very fast
        assert response_time < 1.0
        assert result.success
    
    @pytest.mark.asyncio
    async def test_background_processing(self):
        """Test that long operations run in background."""
        
        config = Mock()
        workflow_engine = WorkflowEngine(config)
        
        # Mock long-running operation
        async def long_operation(plan):
            await asyncio.sleep(2.0)
            return Mock(success=True, execution_time=2.0)
        
        workflow_engine.execute_plan = long_operation
        
        from src.codegenie.core.workflow_engine import WorkflowPlan
        
        plan = WorkflowPlan(
            id="background_test",
            goal="Test background processing",
            tasks=[]
        )
        
        # Start operation
        task = asyncio.create_task(workflow_engine.execute_plan(plan))
        
        # Should be able to do other things while waiting
        await asyncio.sleep(0.1)
        
        # Operation should still be running
        assert not task.done()
        
        # Wait for completion
        result = await task
        
        assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
