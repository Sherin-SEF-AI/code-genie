"""
Comprehensive integration tests for advanced features integration.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import json
import yaml

from src.codegenie.core.end_to_end_workflows import (
    EndToEndWorkflowOrchestrator,
    WorkflowType,
    EndToEndWorkflow,
    WorkflowStep
)
from src.codegenie.core.advanced_config import (
    AdvancedConfigurationManager,
    ConfigScope,
    UserPreferences,
    TeamConfiguration,
    PluginConfiguration
)
from src.codegenie.ui.web_interface import WebInterface
from src.codegenie.ui.configuration_manager import ConfigurationManager
from src.codegenie.core.workflow_engine import WorkflowEngine
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.core.learning_engine import LearningEngine
from src.codegenie.agents.coordinator import AgentCoordinator


class TestAdvancedFeaturesIntegration:
    """Test advanced features integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.autonomous_workflows = True
        config.multi_agent_coordination = True
        config.adaptive_learning = True
        config.debug = False
        config.verbose = False
        return config
    
    @pytest.fixture
    def workflow_engine(self, mock_config):
        """Create workflow engine."""
        return WorkflowEngine(mock_config)
    
    @pytest.fixture
    def context_engine(self, mock_config):
        """Create context engine."""
        return ContextEngine(mock_config)
    
    @pytest.fixture
    def learning_engine(self, mock_config):
        """Create learning engine."""
        return LearningEngine(mock_config)
    
    @pytest.fixture
    def agent_coordinator(self, mock_config):
        """Create agent coordinator."""
        return AgentCoordinator(mock_config)
    
    @pytest.fixture
    def workflow_orchestrator(
        self,
        workflow_engine,
        context_engine,
        learning_engine,
        agent_coordinator
    ):
        """Create workflow orchestrator."""
        return EndToEndWorkflowOrchestrator(
            workflow_engine=workflow_engine,
            context_engine=context_engine,
            learning_engine=learning_engine,
            agent_coordinator=agent_coordinator
        )
    
    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create configuration manager."""
        return AdvancedConfigurationManager(base_path=temp_dir)


class TestEndToEndWorkflows(TestAdvancedFeaturesIntegration):
    """Test end-to-end workflow functionality."""
    
    @pytest.mark.asyncio
    async def test_create_autonomous_development_workflow(self, workflow_orchestrator):
        """Test creating autonomous development workflow."""
        
        goal = "Create a REST API with authentication"
        context = {"project_type": "web_api", "language": "python"}
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.AUTONOMOUS_DEVELOPMENT,
            goal,
            context
        )
        
        assert workflow is not None
        assert workflow.workflow_type == WorkflowType.AUTONOMOUS_DEVELOPMENT
        assert goal in workflow.name
        assert len(workflow.steps) > 0
        assert workflow.status == "created"
        
        # Check that steps have proper dependencies
        step_ids = [step.id for step in workflow.steps]
        for step in workflow.steps:
            for dep in step.dependencies:
                assert dep in step_ids
    
    @pytest.mark.asyncio
    async def test_create_multi_agent_collaboration_workflow(self, workflow_orchestrator):
        """Test creating multi-agent collaboration workflow."""
        
        goal = "Implement comprehensive security audit"
        context = {"security_level": "high", "compliance": ["OWASP", "SOC2"]}
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.MULTI_AGENT_COLLABORATION,
            goal,
            context
        )
        
        assert workflow is not None
        assert workflow.workflow_type == WorkflowType.MULTI_AGENT_COLLABORATION
        assert len(workflow.steps) > 0
        
        # Check that workflow includes coordination steps
        step_names = [step.name.lower() for step in workflow.steps]
        assert any("coordination" in name for name in step_names)
    
    @pytest.mark.asyncio
    async def test_workflow_execution_with_mocked_agents(self, workflow_orchestrator):
        """Test workflow execution with mocked agent responses."""
        
        # Mock agent coordinator methods
        workflow_orchestrator.agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="test_agent", completed=True)]
        )
        workflow_orchestrator.agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True, agent_results=[])
        )
        
        # Mock workflow engine methods
        workflow_orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=10.0)
        )
        
        goal = "Simple test workflow"
        context = {}
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.FEATURE_DEVELOPMENT,
            goal,
            context
        )
        
        result = await workflow_orchestrator.execute_workflow(
            workflow.id,
            autonomous=True,
            user_approval_required=False
        )
        
        assert result.success
        assert workflow.status == "completed"
        assert len(workflow.completed_steps) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_failure_and_recovery(self, workflow_orchestrator):
        """Test workflow failure handling and recovery."""
        
        # Mock a failing step
        workflow_orchestrator.workflow_engine.execute_plan = AsyncMock(
            side_effect=Exception("Simulated failure")
        )
        
        goal = "Test failure recovery"
        context = {}
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.AUTONOMOUS_DEVELOPMENT,
            goal,
            context
        )
        
        result = await workflow_orchestrator.execute_workflow(
            workflow.id,
            autonomous=True
        )
        
        assert not result.success
        assert workflow.status == "failed"
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_workflow_progress_callbacks(self, workflow_orchestrator):
        """Test workflow progress callback functionality."""
        
        progress_events = []
        
        async def progress_callback(event):
            progress_events.append(event)
        
        workflow_orchestrator.add_progress_callback(progress_callback)
        
        # Mock successful execution
        workflow_orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=5.0)
        )
        
        goal = "Test progress tracking"
        context = {}
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.LEARNING_ADAPTATION,
            goal,
            context
        )
        
        await workflow_orchestrator.execute_workflow(workflow.id)
        
        # Check that progress events were fired
        assert len(progress_events) > 0
        event_types = [event['event_type'] for event in progress_events]
        assert 'completed' in event_types
    
    @pytest.mark.asyncio
    async def test_workflow_template_save_and_load(self, workflow_orchestrator, temp_dir):
        """Test saving and loading workflow templates."""
        
        goal = "Template test workflow"
        context = {}
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.COMPLETE_PROJECT_SETUP,
            goal,
            context
        )
        
        # Save as template
        template_name = "test_template"
        await workflow_orchestrator.save_workflow_template(
            template_name,
            workflow,
            "Test template description"
        )
        
        # Load template
        loaded_workflow = await workflow_orchestrator.load_workflow_template(template_name)
        
        assert loaded_workflow is not None
        assert loaded_workflow.workflow_type == workflow.workflow_type
        assert len(loaded_workflow.steps) == len(workflow.steps)


class TestAdvancedConfiguration(TestAdvancedFeaturesIntegration):
    """Test advanced configuration management."""
    
    def test_configuration_hierarchy(self, config_manager):
        """Test configuration hierarchy resolution."""
        
        # Set values at different scopes
        config_manager.set_config("test.value", "global", ConfigScope.GLOBAL)
        config_manager.set_config("test.value", "user", ConfigScope.USER)
        
        # User scope should override global
        value = config_manager.get_config("test.value")
        assert value == "user"
        
        # Explicit global scope should return global value
        global_value = config_manager.get_config("test.value", ConfigScope.GLOBAL)
        assert global_value == "global"
    
    def test_user_preferences_management(self, config_manager):
        """Test user preferences management."""
        
        # Create and save preferences
        preferences = UserPreferences(
            coding_style="black",
            preferred_languages=["python", "javascript"],
            skill_level="advanced",
            interface_theme="dark"
        )
        
        config_manager.save_user_preferences(preferences)
        
        # Load and verify preferences
        loaded_preferences = config_manager.get_user_preferences()
        
        assert loaded_preferences.coding_style == "black"
        assert "python" in loaded_preferences.preferred_languages
        assert loaded_preferences.skill_level == "advanced"
        assert loaded_preferences.interface_theme == "dark"
    
    def test_team_configuration_management(self, config_manager):
        """Test team configuration management."""
        
        # Create team configuration
        team_config = config_manager.create_team_configuration(
            team_id="test_team",
            team_name="Test Team",
            coding_standards={"style": "pep8", "max_line_length": 88},
            security_policies={"require_2fa": True}
        )
        
        assert team_config.team_id == "test_team"
        assert team_config.team_name == "Test Team"
        
        # Load team configuration
        loaded_config = config_manager.get_team_configuration("test_team")
        
        assert loaded_config is not None
        assert loaded_config.team_id == "test_team"
        assert loaded_config.coding_standards["style"] == "pep8"
        assert loaded_config.security_policies["require_2fa"] is True
    
    def test_plugin_management(self, config_manager):
        """Test plugin management functionality."""
        
        # Register plugin
        plugin_config = PluginConfiguration(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            enabled=True,
            settings={"debug": True},
            permissions=["read_files", "execute_code"]
        )
        
        config_manager.register_plugin(plugin_config)
        
        # Verify plugin registration
        loaded_plugin = config_manager.get_plugin_configuration("test_plugin")
        
        assert loaded_plugin is not None
        assert loaded_plugin.plugin_id == "test_plugin"
        assert loaded_plugin.enabled is True
        assert loaded_plugin.settings["debug"] is True
        
        # Test plugin listing
        plugins = config_manager.list_plugins()
        plugin_ids = [p.plugin_id for p in plugins]
        assert "test_plugin" in plugin_ids
        
        # Test plugin disable/enable
        assert config_manager.disable_plugin("test_plugin")
        disabled_plugin = config_manager.get_plugin_configuration("test_plugin")
        assert disabled_plugin.enabled is False
        
        assert config_manager.enable_plugin("test_plugin")
        enabled_plugin = config_manager.get_plugin_configuration("test_plugin")
        assert enabled_plugin.enabled is True
    
    def test_configuration_validation(self, config_manager):
        """Test configuration validation."""
        
        # Test valid configuration
        config_manager.set_config("learning_rate", 0.5, ConfigScope.USER)
        value = config_manager.get_config("learning_rate")
        assert value == 0.5
        
        # Test invalid configuration
        with pytest.raises(ValueError):
            config_manager.set_config("learning_rate", 2.0, ConfigScope.USER)  # Invalid range
    
    def test_configuration_watching(self, config_manager):
        """Test configuration change watching."""
        
        watched_changes = []
        
        def config_watcher(key, value, scope):
            watched_changes.append((key, value, scope))
        
        config_manager.watch_config("test.watched", config_watcher)
        
        # Make configuration change
        config_manager.set_config("test.watched", "new_value", ConfigScope.USER)
        
        # Verify watcher was called
        assert len(watched_changes) == 1
        assert watched_changes[0][0] == "test.watched"
        assert watched_changes[0][1] == "new_value"
        assert watched_changes[0][2] == ConfigScope.USER
    
    def test_configuration_backup_and_restore(self, config_manager):
        """Test configuration backup and restore."""
        
        # Set some configuration
        config_manager.set_config("backup.test", "original_value", ConfigScope.USER)
        
        # Create backup
        backup_path = config_manager.backup_configuration("test_backup")
        assert backup_path.exists()
        
        # Modify configuration
        config_manager.set_config("backup.test", "modified_value", ConfigScope.USER)
        assert config_manager.get_config("backup.test") == "modified_value"
        
        # Restore from backup
        config_manager.restore_configuration("test_backup")
        
        # Verify restoration
        restored_value = config_manager.get_config("backup.test")
        assert restored_value == "original_value"
    
    def test_theme_management(self, config_manager):
        """Test theme management functionality."""
        
        # Test built-in themes
        themes = config_manager.get_available_themes()
        assert "light" in themes
        assert "dark" in themes
        
        # Test theme configuration
        dark_theme = config_manager.get_theme_configuration("dark")
        assert dark_theme is not None
        assert "colors" in dark_theme
        
        # Test custom theme
        custom_theme = {
            "name": "Custom Theme",
            "colors": {
                "primary": "#ff0000",
                "background": "#000000"
            }
        }
        
        config_manager.save_theme_configuration("custom", custom_theme)
        
        loaded_theme = config_manager.get_theme_configuration("custom")
        assert loaded_theme["name"] == "Custom Theme"
        assert loaded_theme["colors"]["primary"] == "#ff0000"


class TestWebInterface(TestAdvancedFeaturesIntegration):
    """Test web interface functionality."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        agent = Mock()
        agent.get_status = AsyncMock(return_value={"initialized": True})
        agent.process_user_input = AsyncMock(return_value="Test response")
        agent.workflow_engine = Mock()
        agent.agent_coordinator = Mock()
        agent.learning_engine = Mock()
        return agent
    
    def test_web_interface_initialization(self, mock_agent, mock_config):
        """Test web interface initialization."""
        
        web_interface = WebInterface(mock_agent, mock_config)
        
        assert web_interface.agent == mock_agent
        assert web_interface.config == mock_config
        assert web_interface.active_workflows == {}
    
    @pytest.mark.asyncio
    async def test_api_status_endpoint(self, mock_agent, mock_config):
        """Test status API endpoint."""
        
        web_interface = WebInterface(mock_agent, mock_config)
        
        # Mock request
        request = Mock()
        
        response = await web_interface.get_status(request)
        
        # Verify response
        assert hasattr(response, 'body')
        mock_agent.get_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_api_chat_endpoint(self, mock_agent, mock_config):
        """Test chat API endpoint."""
        
        web_interface = WebInterface(mock_agent, mock_config)
        
        # Mock request with JSON data
        request = Mock()
        request.json = AsyncMock(return_value={"message": "Hello"})
        
        response = await web_interface.handle_chat(request)
        
        # Verify agent was called
        mock_agent.process_user_input.assert_called_once_with("Hello")
    
    def test_html_interface_generation(self, mock_agent, mock_config):
        """Test HTML interface generation."""
        
        web_interface = WebInterface(mock_agent, mock_config)
        
        html_content = web_interface._generate_html_interface()
        
        assert "CodeGenie" in html_content
        assert "chat-tab" in html_content
        assert "workflows-tab" in html_content
        assert "agents-tab" in html_content
    
    def test_css_generation(self, mock_agent, mock_config):
        """Test CSS generation."""
        
        web_interface = WebInterface(mock_agent, mock_config)
        
        css_content = web_interface._generate_css()
        
        assert "body" in css_content
        assert "tab-button" in css_content
        assert "workflow-item" in css_content
    
    def test_javascript_generation(self, mock_agent, mock_config):
        """Test JavaScript generation."""
        
        web_interface = WebInterface(mock_agent, mock_config)
        
        js_content = web_interface._generate_javascript()
        
        assert "function" in js_content
        assert "WebSocket" in js_content
        assert "sendMessage" in js_content


class TestConfigurationManager(TestAdvancedFeaturesIntegration):
    """Test configuration manager functionality."""
    
    def test_configuration_templates(self, temp_dir):
        """Test configuration template functionality."""
        
        config_manager = ConfigurationManager()
        
        # Test template listing
        templates = config_manager.list_templates()
        assert "default" in templates
        assert "minimal" in templates
        assert "full" in templates
        
        # Test template descriptions
        description = config_manager.get_template_description("default")
        assert len(description) > 0
    
    def test_project_initialization(self, temp_dir):
        """Test project configuration initialization."""
        
        config_manager = ConfigurationManager()
        
        # Initialize project with default template
        config_manager.initialize_project_config(temp_dir, "default")
        
        # Verify configuration files were created
        config_file = temp_dir / ".codegenie" / "config.yaml"
        assert config_file.exists()
        
        # Verify content
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        assert "models:" in config_content
        assert "autonomous_workflows:" in config_content
    
    def test_configuration_validation(self, temp_dir):
        """Test configuration file validation."""
        
        config_manager = ConfigurationManager()
        
        # Create valid configuration
        config_manager.initialize_project_config(temp_dir, "default")
        config_file = temp_dir / ".codegenie" / "config.yaml"
        
        # Validate configuration
        errors = config_manager.validate_config_file(config_file)
        assert len(errors) == 0
        
        # Create invalid configuration
        invalid_config = temp_dir / "invalid_config.yaml"
        with open(invalid_config, 'w') as f:
            f.write("invalid: yaml: content:")
        
        errors = config_manager.validate_config_file(invalid_config)
        assert len(errors) > 0


class TestIntegrationScenarios(TestAdvancedFeaturesIntegration):
    """Test complete integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_autonomous_development_scenario(
        self,
        workflow_orchestrator,
        config_manager,
        temp_dir
    ):
        """Test complete autonomous development scenario."""
        
        # Setup configuration
        config_manager.set_config("autonomous_workflows", True, ConfigScope.PROJECT, temp_dir)
        config_manager.set_config("multi_agent_coordination", True, ConfigScope.PROJECT, temp_dir)
        
        # Setup user preferences
        preferences = UserPreferences(
            coding_style="black",
            preferred_languages=["python"],
            skill_level="advanced"
        )
        config_manager.save_user_preferences(preferences)
        
        # Mock successful workflow execution
        workflow_orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=30.0)
        )
        workflow_orchestrator.agent_coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="developer", completed=True)]
        )
        workflow_orchestrator.agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        
        # Create and execute workflow
        goal = "Create a complete REST API with authentication and testing"
        context = {
            "project_type": "web_api",
            "language": "python",
            "framework": "fastapi"
        }
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.AUTONOMOUS_DEVELOPMENT,
            goal,
            context
        )
        
        result = await workflow_orchestrator.execute_workflow(
            workflow.id,
            autonomous=True
        )
        
        # Verify successful completion
        assert result.success
        assert workflow.status == "completed"
        assert len(workflow.completed_steps) > 0
        
        # Verify configuration was used
        autonomous_enabled = config_manager.get_config(
            "autonomous_workflows",
            ConfigScope.PROJECT,
            temp_dir
        )
        assert autonomous_enabled is True
    
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_with_learning(
        self,
        workflow_orchestrator,
        config_manager
    ):
        """Test multi-agent collaboration with learning adaptation."""
        
        # Mock learning engine
        learning_data = []
        
        async def mock_learn_from_workflow(data):
            learning_data.append(data)
        
        workflow_orchestrator.learning_engine.learn_from_workflow = mock_learn_from_workflow
        
        # Mock agent coordination
        workflow_orchestrator.agent_coordinator.delegate_task = AsyncMock(
            return_value=[
                Mock(agent_name="security", completed=True),
                Mock(agent_name="performance", completed=True)
            ]
        )
        workflow_orchestrator.agent_coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True, agent_results=[])
        )
        
        # Create and execute workflow
        goal = "Comprehensive code review and optimization"
        context = {"code_quality": "high", "performance_critical": True}
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.MULTI_AGENT_COLLABORATION,
            goal,
            context
        )
        
        result = await workflow_orchestrator.execute_workflow(workflow.id)
        
        # Verify execution and learning
        assert result.success
        assert len(learning_data) > 0
        assert learning_data[0]["workflow_type"] == WorkflowType.MULTI_AGENT_COLLABORATION.value
    
    @pytest.mark.asyncio
    async def test_configuration_driven_workflow_customization(
        self,
        workflow_orchestrator,
        config_manager,
        temp_dir
    ):
        """Test workflow customization based on configuration."""
        
        # Setup team configuration with specific preferences
        team_config = TeamConfiguration(
            team_id="dev_team",
            team_name="Development Team",
            coding_standards={
                "style": "black",
                "max_line_length": 88,
                "type_hints": True
            },
            workflow_templates=["secure_development"],
            security_policies={
                "require_security_review": True,
                "vulnerability_scanning": True
            }
        )
        
        config_manager.save_team_configuration(team_config)
        
        # Mock workflow execution with security requirements
        workflow_orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=45.0)
        )
        
        # Create workflow
        goal = "Develop secure payment processing feature"
        context = {
            "team_id": "dev_team",
            "security_level": "high",
            "compliance": ["PCI-DSS"]
        }
        
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.FEATURE_DEVELOPMENT,
            goal,
            context
        )
        
        # Verify security steps are included
        step_names = [step.name.lower() for step in workflow.steps]
        security_steps = [name for name in step_names if "security" in name]
        assert len(security_steps) > 0
        
        # Execute workflow
        result = await workflow_orchestrator.execute_workflow(workflow.id)
        assert result.success


class TestPerformanceAndScalability(TestAdvancedFeaturesIntegration):
    """Test performance and scalability aspects."""
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, workflow_orchestrator):
        """Test concurrent execution of multiple workflows."""
        
        # Mock fast execution
        workflow_orchestrator.workflow_engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=1.0)
        )
        
        # Create multiple workflows
        workflows = []
        for i in range(5):
            workflow = await workflow_orchestrator.create_workflow(
                WorkflowType.LEARNING_ADAPTATION,
                f"Test workflow {i}",
                {"test_id": i}
            )
            workflows.append(workflow)
        
        # Execute workflows concurrently
        tasks = [
            workflow_orchestrator.execute_workflow(workflow.id)
            for workflow in workflows
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all workflows completed successfully
        assert all(result.success for result in results)
        assert len(results) == 5
    
    def test_configuration_caching_performance(self, config_manager):
        """Test configuration caching performance."""
        
        # Set configuration value
        config_manager.set_config("performance.test", "cached_value", ConfigScope.USER)
        
        # First access (should cache)
        value1 = config_manager.get_config("performance.test")
        
        # Second access (should use cache)
        value2 = config_manager.get_config("performance.test")
        
        assert value1 == value2 == "cached_value"
        
        # Verify cache is working by checking internal cache
        cache_key = "auto:performance.test"
        assert cache_key in config_manager.config_cache
    
    def test_large_configuration_handling(self, config_manager):
        """Test handling of large configuration structures."""
        
        # Create large configuration structure
        large_config = {
            f"section_{i}": {
                f"key_{j}": f"value_{i}_{j}"
                for j in range(100)
            }
            for i in range(50)
        }
        
        # Set large configuration
        for section, values in large_config.items():
            for key, value in values.items():
                config_manager.set_config(f"{section}.{key}", value, ConfigScope.USER)
        
        # Verify all values can be retrieved
        for section, values in large_config.items():
            for key, expected_value in values.items():
                actual_value = config_manager.get_config(f"{section}.{key}")
                assert actual_value == expected_value


class TestErrorHandlingAndRecovery(TestAdvancedFeaturesIntegration):
    """Test error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, workflow_orchestrator):
        """Test workflow error recovery mechanisms."""
        
        # Mock failing then succeeding execution
        call_count = 0
        
        async def mock_execute_plan(plan):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Simulated failure")
            return Mock(success=True, execution_time=5.0)
        
        workflow_orchestrator.workflow_engine.execute_plan = mock_execute_plan
        
        # Create workflow with retry enabled
        goal = "Test error recovery"
        workflow = await workflow_orchestrator.create_workflow(
            WorkflowType.AUTONOMOUS_DEVELOPMENT,
            goal,
            {}
        )
        
        # Set retry count on steps
        for step in workflow.steps:
            step.retry_count = 2
        
        result = await workflow_orchestrator.execute_workflow(workflow.id)
        
        # Should succeed after retry
        assert result.success
        assert call_count > 1  # Verify retry occurred
    
    def test_configuration_validation_error_handling(self, config_manager):
        """Test configuration validation error handling."""
        
        # Test invalid configuration values
        invalid_configs = [
            ("learning_rate", 2.0),  # Out of range
            ("skill_level", "invalid"),  # Invalid enum value
            ("timeout", -1),  # Negative timeout
        ]
        
        for key, invalid_value in invalid_configs:
            with pytest.raises(ValueError):
                config_manager.set_config(key, invalid_value, ConfigScope.USER)
    
    def test_configuration_file_corruption_handling(self, config_manager, temp_dir):
        """Test handling of corrupted configuration files."""
        
        # Create corrupted configuration file
        config_file = temp_dir / "corrupted_config.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        # Should handle corruption gracefully
        errors = config_manager.validate_config_file(config_file)
        assert len(errors) > 0
        assert "YAML" in errors[0] or "syntax" in errors[0].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])