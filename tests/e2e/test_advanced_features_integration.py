"""
End-to-end tests for advanced features integration.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.codegenie.core.end_to_end_workflows import (
    EndToEndWorkflowOrchestrator,
    WorkflowContext,
    WorkflowResult
)
from src.codegenie.core.plugin_system import PluginManager, Plugin, PluginMetadata
from src.codegenie.core.permissions import PermissionManager, Permission
from src.codegenie.ui.onboarding import OnboardingSystem, TutorialSystem
from src.codegenie.ui.themes import ThemeManager


class TestEndToEndWorkflows:
    """Test end-to-end workflow orchestration."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            "tool_executor": AsyncMock(),
            "agentic_search": AsyncMock(),
            "proactive_assistant": AsyncMock(),
            "workflow_engine": AsyncMock(),
            "agent_coordinator": AsyncMock(),
            "learning_engine": AsyncMock(),
            "context_engine": AsyncMock()
        }
    
    @pytest.fixture
    def orchestrator(self, mock_components):
        """Create workflow orchestrator."""
        return EndToEndWorkflowOrchestrator(**mock_components)
    
    @pytest.mark.asyncio
    async def test_complete_workflow_execution(self, orchestrator, tmp_path):
        """Test complete workflow execution."""
        
        # Setup mocks
        orchestrator.agentic_search.search_codebase = AsyncMock(return_value={
            "files": ["test.py"],
            "symbols": ["test_function"],
            "dependencies": []
        })
        
        orchestrator.proactive_assistant.analyze_context = AsyncMock(return_value=[])
        orchestrator.context_engine.retrieve_relevant_context = AsyncMock(return_value={})
        orchestrator.workflow_engine.create_execution_plan = AsyncMock(return_value={
            "steps": [
                {"id": "step1", "type": "command", "command": "echo test", "critical": False}
            ]
        })
        
        orchestrator.tool_executor.execute_command = AsyncMock(return_value=Mock(success=True))
        orchestrator.workflow_engine.result_verifier.verify_result = AsyncMock(
            return_value=Mock(success=True)
        )
        
        # Execute workflow
        result = await orchestrator.execute_complete_workflow(
            goal="Test workflow",
            project_path=tmp_path
        )
        
        # Verify
        assert isinstance(result, WorkflowResult)
        assert result.goal == "Test workflow"
    
    @pytest.mark.asyncio
    async def test_workflow_with_error_recovery(self, orchestrator, tmp_path):
        """Test workflow with error recovery."""
        
        # Setup mocks for failure then success
        orchestrator.agentic_search.search_codebase = AsyncMock(return_value={})
        orchestrator.proactive_assistant.analyze_context = AsyncMock(return_value=[])
        orchestrator.context_engine.retrieve_relevant_context = AsyncMock(return_value={})
        orchestrator.workflow_engine.create_execution_plan = AsyncMock(return_value={
            "steps": [
                {"id": "step1", "type": "command", "command": "test", "critical": False}
            ]
        })
        
        # First attempt fails, recovery succeeds
        orchestrator.tool_executor.execute_command = AsyncMock(return_value=Mock(success=False))
        orchestrator.workflow_engine.result_verifier.verify_result = AsyncMock(
            return_value=Mock(success=False, errors=["Test error"])
        )
        orchestrator.tool_executor.fix_and_retry = AsyncMock(
            return_value=Mock(success=True)
        )
        
        result = await orchestrator.execute_complete_workflow(
            goal="Test recovery",
            project_path=tmp_path
        )
        
        assert isinstance(result, WorkflowResult)


class TestPluginSystem:
    """Test plugin system."""
    
    @pytest.fixture
    def plugins_dir(self, tmp_path):
        """Create temporary plugins directory."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        return plugins_dir
    
    @pytest.fixture
    def plugin_manager(self, plugins_dir):
        """Create plugin manager."""
        return PluginManager(plugins_dir)
    
    def test_plugin_manager_initialization(self, plugin_manager, plugins_dir):
        """Test plugin manager initialization."""
        assert plugin_manager.plugins_dir == plugins_dir
        assert len(plugin_manager.plugins) == 0
    
    @pytest.mark.asyncio
    async def test_load_plugins(self, plugin_manager, plugins_dir):
        """Test loading plugins."""
        
        # Create a test plugin file
        plugin_code = '''
from src.codegenie.core.plugin_system import Plugin, PluginMetadata

class TestPlugin(Plugin):
    def get_metadata(self):
        return PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            enabled=True
        )
    
    async def initialize(self, context):
        pass
    
    async def shutdown(self):
        pass
'''
        
        plugin_file = plugins_dir / "test_plugin.py"
        plugin_file.write_text(plugin_code)
        
        await plugin_manager.load_plugins()
        
        assert "test" in plugin_manager.plugins
    
    def test_list_plugins(self, plugin_manager):
        """Test listing plugins."""
        plugins = plugin_manager.list_plugins()
        assert isinstance(plugins, list)


class TestPermissionSystem:
    """Test permission system."""
    
    @pytest.fixture
    def permission_manager(self):
        """Create permission manager."""
        return PermissionManager()
    
    def test_default_permissions(self, permission_manager):
        """Test default permissions."""
        assert permission_manager.check_permission(Permission.FILE_READ)
        assert permission_manager.check_permission(Permission.FILE_WRITE)
        assert not permission_manager.check_permission(Permission.COMMAND_SUDO)
    
    def test_grant_permission(self, permission_manager):
        """Test granting permission."""
        permission_manager.grant_permission(Permission.COMMAND_SUDO)
        assert permission_manager.check_permission(Permission.COMMAND_SUDO)
    
    def test_revoke_permission(self, permission_manager):
        """Test revoking permission."""
        permission_manager.revoke_permission(Permission.FILE_READ)
        assert not permission_manager.check_permission(Permission.FILE_READ)
    
    def test_check_command(self, permission_manager):
        """Test command checking."""
        assert not permission_manager.check_command("sudo rm -rf /")
        assert permission_manager.check_command("ls -la")
    
    def test_check_file_access(self, permission_manager, tmp_path):
        """Test file access checking."""
        test_file = tmp_path / "test.txt"
        assert permission_manager.check_file_access(test_file, Permission.FILE_READ)
    
    @pytest.mark.asyncio
    async def test_request_permission_with_approval(self, permission_manager):
        """Test requesting permission with approval."""
        
        # Register approval callback
        async def approve(context):
            return True
        
        permission_manager.register_approval_callback(Permission.FILE_DELETE, approve)
        
        result = await permission_manager.request_permission(Permission.FILE_DELETE)
        assert result is True


class TestOnboardingSystem:
    """Test onboarding system."""
    
    @pytest.fixture
    def console_mock(self):
        """Create mock console."""
        return Mock()
    
    @pytest.fixture
    def onboarding(self, console_mock):
        """Create onboarding system."""
        return OnboardingSystem(console_mock)
    
    def test_onboarding_initialization(self, onboarding):
        """Test onboarding initialization."""
        assert onboarding.user_preferences == {}
    
    @pytest.mark.asyncio
    async def test_onboarding_flow(self, onboarding, tmp_path):
        """Test onboarding flow."""
        
        # Mock user inputs
        with patch('rich.prompt.Confirm.ask', return_value=False):
            with pytest.raises(KeyboardInterrupt):
                await onboarding.run_onboarding(tmp_path)


class TestTutorialSystem:
    """Test tutorial system."""
    
    @pytest.fixture
    def console_mock(self):
        """Create mock console."""
        return Mock()
    
    @pytest.fixture
    def tutorial_system(self, console_mock):
        """Create tutorial system."""
        return TutorialSystem(console_mock)
    
    def test_list_tutorials(self, tutorial_system):
        """Test listing tutorials."""
        tutorial_system.list_tutorials()
        assert tutorial_system.console.print.called
    
    @pytest.mark.asyncio
    async def test_run_tutorial(self, tutorial_system):
        """Test running tutorial."""
        
        with patch('rich.prompt.Confirm.ask', return_value=False):
            await tutorial_system.run_tutorial("basics")
            assert tutorial_system.console.print.called


class TestThemeSystem:
    """Test theme system."""
    
    @pytest.fixture
    def theme_manager(self):
        """Create theme manager."""
        return ThemeManager()
    
    def test_default_theme(self, theme_manager):
        """Test default theme."""
        assert theme_manager.current_theme == "dark"
    
    def test_get_theme(self, theme_manager):
        """Test getting theme."""
        theme = theme_manager.get_theme("dark")
        assert theme.name == "dark"
    
    def test_set_theme(self, theme_manager):
        """Test setting theme."""
        theme_manager.set_theme("light")
        assert theme_manager.current_theme == "light"
    
    def test_list_themes(self, theme_manager):
        """Test listing themes."""
        themes = theme_manager.list_themes()
        assert "dark" in themes
        assert "light" in themes
        assert "monokai" in themes
    
    def test_get_current_theme(self, theme_manager):
        """Test getting current theme."""
        theme = theme_manager.get_current_theme()
        assert theme.name == "dark"


class TestIntegratedWorkflow:
    """Test integrated workflow with all components."""
    
    @pytest.mark.asyncio
    async def test_full_feature_development_workflow(self, tmp_path):
        """Test complete feature development workflow."""
        
        # Create mock components
        tool_executor = AsyncMock()
        agentic_search = AsyncMock()
        proactive_assistant = AsyncMock()
        workflow_engine = AsyncMock()
        agent_coordinator = AsyncMock()
        learning_engine = AsyncMock()
        context_engine = AsyncMock()
        
        # Setup mocks
        agentic_search.search_codebase = AsyncMock(return_value={
            "files": ["feature.py"],
            "symbols": ["FeatureClass"],
            "dependencies": []
        })
        
        proactive_assistant.analyze_context = AsyncMock(return_value=[
            {"type": "suggestion", "message": "Consider adding tests"}
        ])
        
        context_engine.retrieve_relevant_context = AsyncMock(return_value={
            "previous_features": []
        })
        
        workflow_engine.create_execution_plan = AsyncMock(return_value={
            "steps": [
                {"id": "design", "type": "agent_task", "agent": "architect", "task": "design"},
                {"id": "implement", "type": "agent_task", "agent": "developer", "task": "implement"},
                {"id": "test", "type": "agent_task", "agent": "tester", "task": "test"}
            ]
        })
        
        agent_coordinator.delegate_task = AsyncMock(return_value=[])
        agent_coordinator.execute_agent_task = AsyncMock(return_value={"success": True})
        
        workflow_engine.result_verifier.verify_result = AsyncMock(
            return_value=Mock(success=True)
        )
        
        tool_executor.execute_command = AsyncMock(return_value=Mock(success=True))
        
        learning_engine.record_workflow_execution = AsyncMock()
        
        # Create orchestrator
        orchestrator = EndToEndWorkflowOrchestrator(
            tool_executor=tool_executor,
            agentic_search=agentic_search,
            proactive_assistant=proactive_assistant,
            workflow_engine=workflow_engine,
            agent_coordinator=agent_coordinator,
            learning_engine=learning_engine,
            context_engine=context_engine
        )
        
        # Execute workflow
        result = await orchestrator.execute_complete_workflow(
            goal="Create a new user authentication feature",
            project_path=tmp_path,
            workflow_type="feature_development"
        )
        
        # Verify
        assert isinstance(result, WorkflowResult)
        assert result.goal == "Create a new user authentication feature"
        
        # Verify all components were called
        agentic_search.search_codebase.assert_called_once()
        proactive_assistant.analyze_context.assert_called_once()
        context_engine.retrieve_relevant_context.assert_called_once()
        workflow_engine.create_execution_plan.assert_called_once()
        learning_engine.record_workflow_execution.assert_called_once()
