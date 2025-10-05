"""
Basic tests for Claude Code Agent.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from codegenie.core.config import Config
from codegenie.core.session import SessionManager
from codegenie.core.agent import CodeGenieAgent


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = Config.create_default()
        
        assert config.models.default == "llama3.1:8b"
        assert config.ui.theme == "dark"
        assert config.execution.sandbox_mode is True
        assert config.learning.save_corrections is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = Config.create_default()
        
        # Test model selection
        model = config.get_model_for_task("code_generation")
        assert model == config.models.code_generation
        
        # Test command validation
        assert config.is_command_allowed("git status") is True
        assert config.is_command_allowed("rm -rf /") is False
        
        # Test file validation
        assert config.is_file_allowed(Path("test.py")) is True
        assert config.is_file_allowed(Path("test.exe")) is False


class TestSessionManager:
    """Test session management."""
    
    def test_session_creation(self, tmp_path):
        """Test session creation."""
        config = Config.create_default()
        config.cache_dir = tmp_path / "cache"
        
        session_manager = SessionManager(tmp_path, config)
        
        assert session_manager.session is not None
        assert session_manager.session.session_id is not None
        assert session_manager.session.project_context.project_path == tmp_path
    
    def test_context_analysis(self, tmp_path):
        """Test project context analysis."""
        # Create a simple Python project
        (tmp_path / "main.py").write_text("print('Hello, World!')")
        (tmp_path / "requirements.txt").write_text("requests==2.28.0")
        
        config = Config.create_default()
        config.cache_dir = tmp_path / "cache"
        
        session_manager = SessionManager(tmp_path, config)
        
        context = session_manager.get_context()
        
        assert context["project_type"] == "python"
        assert "python" in context["languages"]
        assert context["file_count"] >= 2


class TestAgent:
    """Test Claude Code Agent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, tmp_path):
        """Test agent initialization."""
        config = Config.create_default()
        config.cache_dir = tmp_path / "cache"
        
        session_manager = SessionManager(tmp_path, config)
        agent = CodeGenieAgent(session_manager)
        
        # Mock the model manager to avoid Ollama dependency
        agent.model_manager = Mock()
        agent.model_manager.initialize = AsyncMock()
        
        await agent.initialize()
        
        assert agent._initialized is True
    
    @pytest.mark.asyncio
    async def test_agent_status(self, tmp_path):
        """Test agent status retrieval."""
        config = Config.create_default()
        config.cache_dir = tmp_path / "cache"
        
        session_manager = SessionManager(tmp_path, config)
        agent = CodeGenieAgent(session_manager)
        
        # Mock components
        agent.model_manager = Mock()
        agent.model_manager.get_model_stats.return_value = {"models": {}}
        agent.memory.get_memory_stats.return_value = {"total_entries": 0}
        
        status = await agent.get_status()
        
        assert "initialized" in status
        assert "session_stats" in status
        assert "model_stats" in status
        assert "memory_stats" in status


if __name__ == "__main__":
    pytest.main([__file__])
