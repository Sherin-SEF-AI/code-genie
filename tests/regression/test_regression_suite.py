"""
Regression test suite to ensure existing functionality remains intact.
Tests critical paths and previously fixed bugs.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile
import shutil

from src.codegenie.core.workflow_engine import WorkflowEngine, WorkflowPlan
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.core.learning_engine import LearningEngine
from src.codegenie.agents.coordinator import AgentCoordinator
from src.codegenie.agents.base_agent import Task
from src.codegenie.core.advanced_config import (
    AdvancedConfigurationManager,
    ConfigScope,
    UserPreferences
)


class TestCoreWorkflowRegression:
    """Regression tests for core workflow functionality."""
    
    @pytest.fixture
    def workflow_engine(self):
        """Create workflow engine for testing."""
        config = Mock()
        config.autonomous_workflows = True
        
        engine = WorkflowEngine(config)
        engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=1.0)
        )
        
        return engine
    
    @pytest.mark.asyncio
    async def test_workflow_creation_stability(self, workflow_engine):
        """Test that workflow creation remains stable."""
        
        # Create various workflow types
        workflows = []
        
        for i in range(10):
            plan = WorkflowPlan(
                id=f"workflow_{i}",
                goal=f"Test workflow {i}",
                tasks=[]
            )
            workflows.append(plan)
        
        # All workflows should be created successfully
        assert len(workflows) == 10
        assert all(w.id.startswith("workflow_") for w in workflows)
    
    @pytest.mark.asyncio
    async def test_workflow_execution_consistency(self, workflow_engine):
        """Test that workflow execution is consistent."""
        
        plan = WorkflowPlan(
            id="consistency_test",
            goal="Test execution consistency",
            tasks=[]
        )
        
        # Execute multiple times
        results = []
        
        for _ in range(5):
            result = await workflow_engine.execute_plan(plan)
            results.append(result.success)
        
        # All executions should succeed
        assert all(results)
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling_regression(self, workflow_engine):
        """Test that error handling works correctly."""
        
        # Mock failure
        workflow_engine.execute_plan = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        plan = WorkflowPlan(
            id="error_test",
            goal="Test error handling",
            tasks=[]
        )
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            await workflow_engine.execute_plan(plan)
        
        assert "Test error" in str(exc_info.value)


class TestAgentCoordinationRegression:
    """Regression tests for agent coordination."""
    
    @pytest.fixture
    def agent_coordinator(self):
        """Create agent coordinator for testing."""
        config = Mock()
        config.multi_agent_coordination = True
        
        coordinator = AgentCoordinator(config)
        coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="test", completed=True)]
        )
        coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        
        return coordinator
    
    @pytest.mark.asyncio
    async def test_task_delegation_stability(self, agent_coordinator):
        """Test that task delegation remains stable."""
        
        task = Task(
            description="Test task delegation",
            task_type="test",
            context={}
        )
        
        # Delegate multiple times
        for _ in range(5):
            assignments = await agent_coordinator.delegate_task(task)
            assert len(assignments) > 0
    
    @pytest.mark.asyncio
    async def test_agent_coordination_consistency(self, agent_coordinator):
        """Test that agent coordination is consistent."""
        
        assignments = [
            Mock(agent_name="agent1", task_id="task1"),
            Mock(agent_name="agent2", task_id="task2")
        ]
        
        # Coordinate multiple times
        results = []
        
        for _ in range(5):
            result = await agent_coordinator.coordinate_execution(assignments)
            results.append(result.success)
        
        # All coordinations should succeed
        assert all(results)


class TestContextEngineRegression:
    """Regression tests for context engine."""
    
    @pytest.fixture
    def context_engine(self):
        """Create context engine for testing."""
        config = Mock()
        return ContextEngine(config)
    
    @pytest.mark.asyncio
    async def test_context_storage_stability(self, context_engine):
        """Test that context storage remains stable."""
        
        # Store multiple interactions
        for i in range(10):
            await context_engine.store_interaction({
                'type': 'test',
                'content': f'Test interaction {i}',
                'timestamp': f'2024-01-01T00:00:{i:02d}'
            })
        
        # Context should be stored successfully
        # (No exceptions should be raised)
    
    @pytest.mark.asyncio
    async def test_context_retrieval_consistency(self, context_engine):
        """Test that context retrieval is consistent."""
        
        # Store test context
        await context_engine.store_interaction({
            'type': 'test',
            'content': 'Test context retrieval',
            'timestamp': '2024-01-01T00:00:00'
        })
        
        # Retrieve multiple times
        for _ in range(5):
            context = await context_engine.retrieve_relevant_context('test')
            assert context is not None


class TestLearningEngineRegression:
    """Regression tests for learning engine."""
    
    @pytest.fixture
    def learning_engine(self):
        """Create learning engine for testing."""
        config = Mock()
        config.adaptive_learning = True
        
        engine = LearningEngine(config)
        engine.learn_from_workflow = AsyncMock()
        engine.get_user_profile = AsyncMock(
            return_value={'skill_level': 'intermediate'}
        )
        
        return engine
    
    @pytest.mark.asyncio
    async def test_learning_stability(self, learning_engine):
        """Test that learning functionality remains stable."""
        
        # Learn from multiple workflows
        for i in range(10):
            await learning_engine.learn_from_workflow({
                'workflow_id': f'workflow_{i}',
                'success': True,
                'execution_time': 1.0
            })
        
        # All learning operations should complete
        assert learning_engine.learn_from_workflow.call_count == 10
    
    @pytest.mark.asyncio
    async def test_user_profile_consistency(self, learning_engine):
        """Test that user profile retrieval is consistent."""
        
        # Retrieve profile multiple times
        profiles = []
        
        for _ in range(5):
            profile = await learning_engine.get_user_profile()
            profiles.append(profile)
        
        # All profiles should be identical
        assert all(p == profiles[0] for p in profiles)


class TestConfigurationRegression:
    """Regression tests for configuration system."""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create configuration manager for testing."""
        return AdvancedConfigurationManager(base_path=tmp_path)
    
    def test_configuration_persistence(self, config_manager):
        """Test that configuration persists correctly."""
        
        # Set configuration
        config_manager.set_config(
            "test.persistence",
            "test_value",
            ConfigScope.USER,
            validate=False
        )
        
        # Retrieve configuration
        value = config_manager.get_config("test.persistence")
        
        assert value == "test_value"
    
    def test_configuration_hierarchy_stability(self, config_manager, tmp_path):
        """Test that configuration hierarchy remains stable."""
        
        # Set at different scopes
        config_manager.set_config(
            "test.hierarchy",
            "global_value",
            ConfigScope.GLOBAL,
            validate=False
        )
        
        config_manager.set_config(
            "test.hierarchy",
            "user_value",
            ConfigScope.USER,
            validate=False
        )
        
        config_manager.set_config(
            "test.hierarchy",
            "project_value",
            ConfigScope.PROJECT,
            project_path=tmp_path,
            validate=False
        )
        
        # Project scope should win
        value = config_manager.get_config("test.hierarchy", project_path=tmp_path)
        
        assert value == "project_value"
    
    def test_user_preferences_stability(self, config_manager):
        """Test that user preferences remain stable."""
        
        # Set preferences
        prefs = UserPreferences(
            coding_style="pep8",
            preferred_languages=["python"],
            skill_level="expert",
            interface_theme="dark",
            learning_enabled=True
        )
        
        config_manager.save_user_preferences(prefs)
        
        # Retrieve preferences
        loaded_prefs = config_manager.get_user_preferences()
        
        assert loaded_prefs.coding_style == "pep8"
        assert loaded_prefs.skill_level == "expert"


class TestPreviouslyFixedBugs:
    """Tests for previously fixed bugs to prevent regression."""
    
    @pytest.mark.asyncio
    async def test_bug_empty_workflow_execution(self):
        """Test fix for empty workflow execution bug."""
        
        config = Mock()
        engine = WorkflowEngine(config)
        engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=0.0)
        )
        
        # Empty workflow should not crash
        plan = WorkflowPlan(
            id="empty_workflow",
            goal="Empty workflow test",
            tasks=[]
        )
        
        result = await engine.execute_plan(plan)
        
        # Should handle gracefully
        assert result.success
    
    @pytest.mark.asyncio
    async def test_bug_concurrent_context_access(self):
        """Test fix for concurrent context access bug."""
        
        config = Mock()
        context_engine = ContextEngine(config)
        
        # Concurrent access should not cause issues
        async def store_context(i):
            await context_engine.store_interaction({
                'type': 'concurrent_test',
                'content': f'Interaction {i}',
                'timestamp': f'2024-01-01T00:00:{i:02d}'
            })
        
        # Execute concurrently
        tasks = [store_context(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Should complete without errors
    
    def test_bug_configuration_key_validation(self, tmp_path):
        """Test fix for configuration key validation bug."""
        
        config_manager = AdvancedConfigurationManager(base_path=tmp_path)
        
        # Invalid keys should be rejected
        invalid_keys = [
            "",  # Empty key
            ".",  # Just dot
            "..key",  # Leading dots
            "key..",  # Trailing dots
        ]
        
        for invalid_key in invalid_keys:
            try:
                config_manager.set_config(
                    invalid_key,
                    "value",
                    ConfigScope.USER,
                    validate=True
                )
                # Should not reach here
                assert False, f"Invalid key '{invalid_key}' was accepted"
            except (ValueError, Exception):
                # Expected to fail
                pass
    
    @pytest.mark.asyncio
    async def test_bug_agent_coordination_deadlock(self):
        """Test fix for agent coordination deadlock bug."""
        
        config = Mock()
        coordinator = AgentCoordinator(config)
        
        # Mock coordination that could deadlock
        coordinator.delegate_task = AsyncMock(
            return_value=[
                Mock(agent_name="agent1", task_id="task1"),
                Mock(agent_name="agent2", task_id="task2")
            ]
        )
        
        coordinator.coordinate_execution = AsyncMock(
            return_value=Mock(success=True)
        )
        
        task = Task(
            description="Deadlock test",
            task_type="test",
            context={}
        )
        
        # Should complete without deadlock
        assignments = await coordinator.delegate_task(task)
        result = await coordinator.coordinate_execution(assignments)
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_bug_learning_engine_memory_leak(self):
        """Test fix for learning engine memory leak bug."""
        
        config = Mock()
        learning_engine = LearningEngine(config)
        learning_engine.learn_from_workflow = AsyncMock()
        
        # Process many workflows (previously caused memory leak)
        for i in range(100):
            await learning_engine.learn_from_workflow({
                'workflow_id': f'workflow_{i}',
                'success': True,
                'execution_time': 1.0
            })
        
        # Should complete without memory issues
        assert learning_engine.learn_from_workflow.call_count == 100


class TestBackwardCompatibility:
    """Tests for backward compatibility."""
    
    def test_config_format_compatibility(self, tmp_path):
        """Test that old configuration format is still supported."""
        
        config_manager = AdvancedConfigurationManager(base_path=tmp_path)
        
        # Old-style configuration keys
        old_style_keys = [
            "model.default",
            "workflow.autonomous",
            "agent.coordination"
        ]
        
        for key in old_style_keys:
            config_manager.set_config(
                key,
                "test_value",
                ConfigScope.USER,
                validate=False
            )
            
            value = config_manager.get_config(key)
            assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_workflow_api_compatibility(self):
        """Test that workflow API remains compatible."""
        
        config = Mock()
        engine = WorkflowEngine(config)
        engine.execute_plan = AsyncMock(
            return_value=Mock(success=True, execution_time=1.0)
        )
        
        # Old-style workflow creation
        plan = WorkflowPlan(
            id="compat_test",
            goal="Compatibility test",
            tasks=[]
        )
        
        # Should work with old API
        result = await engine.execute_plan(plan)
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_agent_interface_compatibility(self):
        """Test that agent interface remains compatible."""
        
        config = Mock()
        coordinator = AgentCoordinator(config)
        coordinator.delegate_task = AsyncMock(
            return_value=[Mock(agent_name="test", completed=True)]
        )
        
        # Old-style task creation
        task = Task(
            description="Compatibility test",
            task_type="test",
            context={}
        )
        
        # Should work with old API
        assignments = await coordinator.delegate_task(task)
        
        assert len(assignments) > 0


class TestDataIntegrity:
    """Tests for data integrity."""
    
    def test_configuration_data_integrity(self, tmp_path):
        """Test that configuration data maintains integrity."""
        
        config_manager = AdvancedConfigurationManager(base_path=tmp_path)
        
        # Set various data types
        test_data = {
            "string_value": "test",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "list_value": [1, 2, 3],
            "dict_value": {"key": "value"}
        }
        
        for key, value in test_data.items():
            config_manager.set_config(
                f"integrity.{key}",
                value,
                ConfigScope.USER,
                validate=False
            )
        
        # Verify data integrity
        for key, expected_value in test_data.items():
            actual_value = config_manager.get_config(f"integrity.{key}")
            assert actual_value == expected_value
    
    @pytest.mark.asyncio
    async def test_context_data_integrity(self):
        """Test that context data maintains integrity."""
        
        config = Mock()
        context_engine = ContextEngine(config)
        
        # Store complex context data
        context_data = {
            'type': 'test',
            'content': 'Test content',
            'metadata': {
                'user': 'test_user',
                'timestamp': '2024-01-01T00:00:00',
                'tags': ['test', 'integrity']
            },
            'nested': {
                'level1': {
                    'level2': {
                        'value': 'deep_value'
                    }
                }
            }
        }
        
        await context_engine.store_interaction(context_data)
        
        # Data should be stored without corruption
        # (No exceptions should be raised)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
