"""
End-to-end tests for the complete advanced CodeGenie system.
"""

import pytest
import asyncio
import tempfile
import shutil
import subprocess
import time
import requests
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import json
import yaml

from src.codegenie.core.agent import CodeGenieAgent
from src.codegenie.core.config import Config
from src.codegenie.core.session import SessionManager
from src.codegenie.core.end_to_end_workflows import (
    EndToEndWorkflowOrchestrator,
    WorkflowType
)
from src.codegenie.core.advanced_config import (
    AdvancedConfigurationManager,
    ConfigScope,
    UserPreferences
)
from src.codegenie.ui.web_interface import WebInterface
from src.codegenie.cli import app


class TestCompleteSystemE2E:
    """End-to-end tests for the complete system."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create basic project structure
        (temp_dir / "src").mkdir()
        (temp_dir / "tests").mkdir()
        (temp_dir / "docs").mkdir()
        
        # Create basic files
        (temp_dir / "README.md").write_text("# Test Project\n")
        (temp_dir / "requirements.txt").write_text("pytest\nrequests\n")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.models = Mock()
        config.models.default = "llama3.1:8b"
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        config.adaptive_learning = True
        config.debug = False
        config.verbose = False
        return config


class TestCLIIntegration(TestCompleteSystemE2E):
    """Test CLI integration with advanced features."""
    
    def test_cli_help_command(self):
        """Test CLI help command shows advanced features."""
        
        # This would test the actual CLI in a real scenario
        # For now, we'll test the command structure
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "workflow" in result.stdout
        assert "agents" in result.stdout
        assert "learning" in result.stdout
        assert "config" in result.stdout
    
    def test_workflow_cli_commands(self):
        """Test workflow CLI commands."""
        
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Test workflow help
        result = runner.invoke(app, ["workflow", "--help"])
        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "list" in result.stdout
        assert "execute" in result.stdout
    
    def test_agents_cli_commands(self):
        """Test agents CLI commands."""
        
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Test agents help
        result = runner.invoke(app, ["agents", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "coordinate" in result.stdout
        assert "status" in result.stdout
    
    def test_config_cli_commands(self):
        """Test configuration CLI commands."""
        
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Test config help
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "init" in result.stdout
        assert "show" in result.stdout
        assert "set" in result.stdout


class TestWebInterfaceE2E(TestCompleteSystemE2E):
    """Test web interface end-to-end functionality."""
    
    @pytest.fixture
    def web_server(self, mock_config, temp_project):
        """Start web server for testing."""
        
        # Mock agent
        agent = Mock()
        agent.get_status = AsyncMock(return_value={"initialized": True})
        agent.process_user_input = AsyncMock(return_value="Test response")
        
        # Create web interface
        web_interface = WebInterface(agent, mock_config)
        
        # In a real test, we would start the actual server
        # For now, we'll return the interface for testing
        return web_interface
    
    def test_web_interface_static_files(self, web_server):
        """Test web interface static file generation."""
        
        # Test HTML generation
        html_content = web_server._generate_html_interface()
        assert "<!DOCTYPE html>" in html_content
        assert "CodeGenie" in html_content
        assert "chat-tab" in html_content
        
        # Test CSS generation
        css_content = web_server._generate_css()
        assert "body" in css_content
        assert "tab-button" in css_content
        
        # Test JavaScript generation
        js_content = web_server._generate_javascript()
        assert "function" in js_content
        assert "WebSocket" in js_content
    
    @pytest.mark.asyncio
    async def test_web_api_endpoints(self, web_server):
        """Test web API endpoints."""
        
        # Test status endpoint
        request = Mock()
        response = await web_server.get_status(request)
        assert response is not None
        
        # Test chat endpoint
        request.json = AsyncMock(return_value={"message": "Hello"})
        response = await web_server.handle_chat(request)
        assert response is not None
        
        # Test workflows endpoint
        response = await web_server.get_workflows(request)
        assert response is not None
        
        # Test agents endpoint
        response = await web_server.get_agents(request)
        assert response is not None


class TestCompleteWorkflowE2E(TestCompleteSystemE2E):
    """Test complete workflow execution end-to-end."""
    
    @pytest.fixture
    def complete_system(self, temp_project, mock_config):
        """Set up complete system for testing."""
        
        # Create session manager
        session_manager = SessionManager(temp_project, mock_config)
        
        # Create engines
        from src.codegenie.core.workflow_engine import WorkflowEngine
        from src.codegenie.core.context_engine import ContextEngine
        from src.codegenie.core.learning_engine import LearningEngine
        from src.codegenie.agents.coordinator import AgentCoordinator
        
        workflow_engine = WorkflowEngine(mock_config)
        context_engine = ContextEngine(mock_config)
        learning_engine = LearningEngine(mock_config)
        agent_coordinator = AgentCoordinator(mock_config)
        
        # Create main agent
        agent = CodeGenieAgent(
            session_manager,
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
        
        # Create workflow orchestrator
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
            'project_path': temp_project
        }
    
    @pytest.mark.asyncio
    async def test_autonomous_development_workflow_e2e(self, complete_system):
        """Test complete autonomous development workflow."""
        
        orchestrator = complete_system['orchestrator']
        
        # Mock successful execution at each step
        orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=10.0)
        )
        orchestrator.agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="developer", completed=True)]
        )
        orchestrator.agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        
        # Create workflow
        goal = "Create a complete REST API with authentication, testing, and documentation"
        context = {
            "project_type": "web_api",
            "language": "python",
            "framework": "fastapi",
            "database": "postgresql",
            "authentication": "jwt"
        }
        
        workflow = await orchestrator.create_workflow(
            WorkflowType.AUTONOMOUS_DEVELOPMENT,
            goal,
            context
        )
        
        # Verify workflow structure
        assert workflow is not None
        assert len(workflow.steps) > 5  # Should have multiple steps
        
        # Check for expected steps
        step_names = [step.name.lower() for step in workflow.steps]
        expected_steps = [
            "requirements", "architecture", "implement", "security", 
            "performance", "test", "documentation"
        ]
        
        for expected in expected_steps:
            assert any(expected in name for name in step_names)
        
        # Execute workflow
        result = await orchestrator.execute_workflow(
            workflow.id,
            autonomous=True,
            user_approval_required=False
        )
        
        # Verify successful completion
        assert result.success
        assert workflow.status == "completed"
        assert len(workflow.completed_steps) == len(workflow.steps)
        assert len(workflow.failed_steps) == 0
    
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_e2e(self, complete_system):
        """Test multi-agent collaboration end-to-end."""
        
        orchestrator = complete_system['orchestrator']
        
        # Mock agent coordination
        orchestrator.agent_coordinator.delegate_task = AsyncMock(
            return_value=[
                Mock(agent_name="architect", task_description="Design system", completed=True),
                Mock(agent_name="security", task_description="Security review", completed=True),
                Mock(agent_name="performance", task_description="Performance optimization", completed=True)
            ]
        )
        orchestrator.agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True, agent_results=[])
        )
        
        # Create multi-agent workflow
        goal = "Comprehensive system review and optimization"
        context = {
            "review_type": "comprehensive",
            "focus_areas": ["security", "performance", "architecture"],
            "priority": "high"
        }
        
        workflow = await orchestrator.create_workflow(
            WorkflowType.MULTI_AGENT_COLLABORATION,
            goal,
            context
        )
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Verify coordination occurred
        assert result.success
        orchestrator.agent_coordinator.delegate_task.assert_called()
        orchestrator.agent_coordinator.coordinate_execution.assert_called()
    
    @pytest.mark.asyncio
    async def test_learning_adaptation_e2e(self, complete_system):
        """Test learning adaptation end-to-end."""
        
        orchestrator = complete_system['orchestrator']
        
        # Mock learning engine
        learning_data = []
        
        async def mock_learn_from_workflow(data):
            learning_data.append(data)
        
        orchestrator.learning_engine.learn_from_workflow = mock_learn_from_workflow
        orchestrator.learning_engine.get_user_profile = AsyncMock(
            return_value={"coding_style": "pep8", "skill_level": "advanced"}
        )
        
        # Mock workflow execution
        orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=15.0)
        )
        
        # Create learning workflow
        goal = "Adapt to user preferences and improve suggestions"
        context = {
            "user_feedback": [
                {"suggestion_id": "1", "rating": 5, "comment": "Excellent"},
                {"suggestion_id": "2", "rating": 3, "comment": "Could be better"}
            ]
        }
        
        workflow = await orchestrator.create_workflow(
            WorkflowType.LEARNING_ADAPTATION,
            goal,
            context
        )
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Verify learning occurred
        assert result.success
        assert len(learning_data) > 0
        assert learning_data[0]["workflow_type"] == WorkflowType.LEARNING_ADAPTATION.value


class TestConfigurationIntegrationE2E(TestCompleteSystemE2E):
    """Test configuration integration end-to-end."""
    
    @pytest.fixture
    def config_system(self, temp_project):
        """Set up configuration system."""
        
        config_manager = AdvancedConfigurationManager(
            base_path=temp_project / ".codegenie"
        )
        
        return config_manager
    
    def test_complete_configuration_workflow(self, config_system, temp_project):
        """Test complete configuration workflow."""
        
        # Initialize project configuration
        from src.codegenie.ui.configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        config_manager.initialize_project_config(temp_project, "full")
        
        # Verify configuration files created
        config_file = temp_project / ".codegenie" / "config.yaml"
        assert config_file.exists()
        
        # Set user preferences
        preferences = UserPreferences(
            coding_style="black",
            preferred_languages=["python", "typescript"],
            skill_level="expert",
            interface_theme="dark",
            learning_enabled=True
        )
        
        config_system.save_user_preferences(preferences)
        
        # Verify preferences saved and loaded
        loaded_preferences = config_system.get_user_preferences()
        assert loaded_preferences.coding_style == "black"
        assert "python" in loaded_preferences.preferred_languages
        assert loaded_preferences.skill_level == "expert"
        
        # Test configuration hierarchy
        config_system.set_config("test.value", "global", ConfigScope.GLOBAL)
        config_system.set_config("test.value", "project", ConfigScope.PROJECT, temp_project)
        
        # Project scope should override global
        value = config_system.get_config("test.value", project_path=temp_project)
        assert value == "project"
        
        # Test configuration backup and restore
        original_value = config_system.get_config("test.value", project_path=temp_project)
        
        backup_path = config_system.backup_configuration("test_backup")
        assert backup_path.exists()
        
        # Modify configuration
        config_system.set_config("test.value", "modified", ConfigScope.PROJECT, temp_project)
        modified_value = config_system.get_config("test.value", project_path=temp_project)
        assert modified_value == "modified"
        
        # Restore from backup
        config_system.restore_configuration("test_backup")
        restored_value = config_system.get_config("test.value", project_path=temp_project)
        assert restored_value == original_value
    
    def test_plugin_system_e2e(self, config_system):
        """Test plugin system end-to-end."""
        
        from src.codegenie.core.advanced_config import PluginConfiguration
        
        # Register plugin
        plugin_config = PluginConfiguration(
            plugin_id="test_e2e_plugin",
            name="Test E2E Plugin",
            version="1.0.0",
            enabled=True,
            settings={
                "feature_enabled": True,
                "max_iterations": 10
            },
            permissions=["read_files", "write_files"]
        )
        
        config_system.register_plugin(plugin_config)
        
        # Verify plugin registration
        loaded_plugin = config_system.get_plugin_configuration("test_e2e_plugin")
        assert loaded_plugin is not None
        assert loaded_plugin.enabled is True
        
        # Test plugin management
        plugins = config_system.list_plugins(enabled_only=True)
        plugin_ids = [p.plugin_id for p in plugins]
        assert "test_e2e_plugin" in plugin_ids
        
        # Test disable/enable cycle
        assert config_system.disable_plugin("test_e2e_plugin")
        disabled_plugin = config_system.get_plugin_configuration("test_e2e_plugin")
        assert disabled_plugin.enabled is False
        
        assert config_system.enable_plugin("test_e2e_plugin")
        enabled_plugin = config_system.get_plugin_configuration("test_e2e_plugin")
        assert enabled_plugin.enabled is True


class TestSystemPerformanceE2E(TestCompleteSystemE2E):
    """Test system performance end-to-end."""
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, complete_system):
        """Test concurrent workflow execution performance."""
        
        orchestrator = complete_system['orchestrator']
        
        # Mock fast execution
        orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.1)
        )
        
        # Create multiple workflows
        workflows = []
        start_time = time.time()
        
        for i in range(10):
            workflow = await orchestrator.create_workflow(
                WorkflowType.LEARNING_ADAPTATION,
                f"Performance test workflow {i}",
                {"test_id": i}
            )
            workflows.append(workflow)
        
        creation_time = time.time() - start_time
        
        # Execute workflows concurrently
        start_time = time.time()
        
        tasks = [
            orchestrator.execute_workflow(workflow.id)
            for workflow in workflows
        ]
        
        results = await asyncio.gather(*tasks)
        
        execution_time = time.time() - start_time
        
        # Verify performance
        assert all(result.success for result in results)
        assert creation_time < 5.0  # Should create 10 workflows in under 5 seconds
        assert execution_time < 10.0  # Should execute 10 workflows in under 10 seconds
    
    def test_configuration_performance(self, config_system):
        """Test configuration system performance."""
        
        # Test large configuration handling
        start_time = time.time()
        
        # Set many configuration values
        for i in range(1000):
            config_system.set_config(f"perf.test.{i}", f"value_{i}", ConfigScope.USER)
        
        set_time = time.time() - start_time
        
        # Test retrieval performance
        start_time = time.time()
        
        for i in range(1000):
            value = config_system.get_config(f"perf.test.{i}")
            assert value == f"value_{i}"
        
        get_time = time.time() - start_time
        
        # Performance assertions
        assert set_time < 30.0  # Should set 1000 values in under 30 seconds
        assert get_time < 5.0   # Should get 1000 values in under 5 seconds (cached)


class TestSystemReliabilityE2E(TestCompleteSystemE2E):
    """Test system reliability and error handling."""
    
    @pytest.mark.asyncio
    async def test_workflow_failure_recovery_e2e(self, complete_system):
        """Test workflow failure and recovery end-to-end."""
        
        orchestrator = complete_system['orchestrator']
        
        # Mock intermittent failures
        call_count = 0
        
        async def mock_execute_with_failures(plan):
            nonlocal call_count
            call_count += 1
            
            # Fail first two attempts, succeed on third
            if call_count <= 2:
                raise Exception(f"Simulated failure {call_count}")
            
            return Mock(success=True, execution_time=5.0)
        
        orchestrator.workflow_engine.execute_plan = mock_execute_with_failures
        
        # Create workflow with retry configuration
        goal = "Test reliability and recovery"
        workflow = await orchestrator.create_workflow(
            WorkflowType.AUTONOMOUS_DEVELOPMENT,
            goal,
            {}
        )
        
        # Configure retry settings
        for step in workflow.steps:
            step.retry_count = 3
            step.failure_recovery = "retry"
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Should eventually succeed after retries
        assert result.success
        assert call_count >= 3  # Verify retries occurred
    
    def test_configuration_corruption_recovery(self, config_system, temp_project):
        """Test configuration corruption recovery."""
        
        # Create valid configuration
        config_system.set_config("test.recovery", "original_value", ConfigScope.USER)
        
        # Create backup
        backup_path = config_system.backup_configuration("corruption_test")
        
        # Simulate configuration corruption
        user_config_file = config_system.base_path / "user" / "config.yaml"
        with open(user_config_file, 'w') as f:
            f.write("corrupted: yaml: content: [unclosed")
        
        # Verify corruption is detected
        errors = config_system.validate_config_file(user_config_file)
        assert len(errors) > 0
        
        # Restore from backup
        config_system.restore_configuration("corruption_test")
        
        # Verify recovery
        recovered_value = config_system.get_config("test.recovery")
        assert recovered_value == "original_value"


class TestUserExperienceE2E(TestCompleteSystemE2E):
    """Test user experience end-to-end scenarios."""
    
    @pytest.mark.asyncio
    async def test_new_user_onboarding_e2e(self, temp_project):
        """Test complete new user onboarding experience."""
        
        # Initialize configuration system
        config_manager = AdvancedConfigurationManager(
            base_path=temp_project / ".codegenie"
        )
        
        # Simulate new user setup
        from src.codegenie.ui.configuration_manager import ConfigurationManager
        
        ui_config_manager = ConfigurationManager()
        ui_config_manager.initialize_project_config(temp_project, "default")
        
        # Set initial user preferences
        preferences = UserPreferences(
            coding_style="pep8",
            preferred_languages=["python"],
            skill_level="beginner",
            interface_theme="light",
            learning_enabled=True,
            show_suggestions=True
        )
        
        config_manager.save_user_preferences(preferences)
        
        # Verify onboarding completed successfully
        loaded_preferences = config_manager.get_user_preferences()
        assert loaded_preferences.skill_level == "beginner"
        assert loaded_preferences.learning_enabled is True
        
        # Verify project configuration exists
        project_config = temp_project / ".codegenie" / "config.yaml"
        assert project_config.exists()
    
    @pytest.mark.asyncio
    async def test_experienced_user_workflow_e2e(self, complete_system):
        """Test experienced user workflow customization."""
        
        orchestrator = complete_system['orchestrator']
        
        # Mock advanced user preferences
        orchestrator.learning_engine.get_user_profile = AsyncMock(
            return_value={
                "coding_style": "black",
                "skill_level": "expert",
                "preferred_patterns": ["factory", "observer", "strategy"],
                "optimization_preferences": ["performance", "readability"]
            }
        )
        
        # Mock successful execution
        orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=8.0)
        )
        orchestrator.agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="architect", completed=True)]
        )
        orchestrator.agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        
        # Create advanced workflow
        goal = "Implement microservices architecture with advanced patterns"
        context = {
            "architecture_type": "microservices",
            "patterns": ["CQRS", "Event Sourcing", "Saga"],
            "scalability": "high",
            "complexity": "advanced"
        }
        
        workflow = await orchestrator.create_workflow(
            WorkflowType.COMPLETE_PROJECT_SETUP,
            goal,
            context
        )
        
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow.id)
        
        # Verify advanced workflow execution
        assert result.success
        assert len(workflow.steps) > 5  # Should have comprehensive steps
        
        # Verify learning engine was consulted
        orchestrator.learning_engine.get_user_profile.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])