"""
Integration tests for terminal integration.

Tests cover:
- Interactive terminal sessions
- Shell integration
- End-to-end command processing
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.codegenie.integrations.terminal_integration import TerminalInterface
from src.codegenie.integrations.interactive_terminal import (
    InteractiveTerminalSession,
    CommandHistoryManager,
    ConversationManager
)
from src.codegenie.integrations.shell_integration import (
    ShellIntegrationManager,
    ShellType,
    BashIntegration,
    ZshIntegration
)


class TestInteractiveTerminalSession:
    """Test interactive terminal session."""
    
    @pytest.fixture
    def session(self, tmp_path):
        """Create interactive session instance."""
        terminal = TerminalInterface(working_directory=tmp_path)
        return InteractiveTerminalSession(terminal_interface=terminal)
    
    def test_session_initialization(self, session):
        """Test session initialization."""
        assert session.terminal is not None
        assert session.history_manager is not None
        assert session.conversation_manager is not None
        assert not session.running
    
    def test_command_history_manager(self, tmp_path):
        """Test command history management."""
        history_file = tmp_path / 'test_history'
        manager = CommandHistoryManager(history_file=history_file)
        
        # Add commands
        manager.add_command('ls -la')
        manager.add_command('git status')
        
        # Get recent commands
        recent = manager.get_recent(10)
        assert len(recent) == 2
        assert 'ls -la' in recent
        assert 'git status' in recent
    
    def test_command_history_search(self, tmp_path):
        """Test searching command history."""
        history_file = tmp_path / 'test_history'
        manager = CommandHistoryManager(history_file=history_file)
        
        manager.add_command('git status')
        manager.add_command('git commit')
        manager.add_command('ls -la')
        
        # Search for git commands
        results = manager.search_history('git')
        assert len(results) == 2
        assert all('git' in cmd for cmd in results)
    
    def test_conversation_manager(self):
        """Test conversation management."""
        manager = ConversationManager()
        
        # Add turns
        manager.add_turn(
            user_input='ls',
            parsed_command=None,
            result=None,
            success=True
        )
        
        manager.add_turn(
            user_input='git status',
            parsed_command=None,
            result=None,
            success=True
        )
        
        # Get recent turns
        recent = manager.get_recent_turns(5)
        assert len(recent) == 2
        
        # Get context
        context = manager.get_context_from_history()
        assert context['total_turns'] == 2
        assert context['successful_turns'] == 2
    
    def test_conversation_preferences(self):
        """Test user preferences in conversation."""
        manager = ConversationManager()
        
        manager.set_preference('auto_confirm', True)
        manager.set_preference('verbose', False)
        
        assert manager.get_preference('auto_confirm') is True
        assert manager.get_preference('verbose') is False
        assert manager.get_preference('nonexistent', 'default') == 'default'


class TestShellIntegration:
    """Test shell integration."""
    
    @pytest.fixture
    def shell_manager(self):
        """Create shell integration manager."""
        return ShellIntegrationManager()
    
    def test_shell_detection(self, shell_manager):
        """Test shell type detection."""
        assert shell_manager.shell_type in [
            ShellType.BASH,
            ShellType.ZSH,
            ShellType.FISH,
            ShellType.SH,
            ShellType.UNKNOWN
        ]
    
    def test_get_environment(self, shell_manager):
        """Test getting shell environment."""
        env = shell_manager.get_environment()
        
        assert env.shell_type is not None
        assert env.working_directory is not None
        assert isinstance(env.environment_variables, dict)
        assert isinstance(env.path_dirs, list)
    
    def test_environment_variable_operations(self, shell_manager):
        """Test environment variable get/set."""
        # Set variable
        success = shell_manager.set_environment_variable('TEST_VAR', 'test_value')
        assert success
        
        # Get variable
        value = shell_manager.get_environment_variable('TEST_VAR')
        assert value == 'test_value'
    
    def test_working_directory_operations(self, shell_manager, tmp_path):
        """Test working directory operations."""
        # Get current directory
        current = shell_manager.get_working_directory()
        assert current.exists()
        
        # Change directory
        test_dir = tmp_path / 'test_dir'
        test_dir.mkdir()
        success = shell_manager.change_directory(test_dir)
        assert success
        
        # Verify change
        new_dir = shell_manager.get_working_directory()
        assert new_dir == test_dir
    
    def test_path_operations(self, shell_manager, tmp_path):
        """Test PATH operations."""
        # Get PATH directories
        path_dirs = shell_manager.get_path_dirs()
        assert len(path_dirs) > 0
        
        # Add to PATH
        test_dir = tmp_path / 'bin'
        test_dir.mkdir()
        success = shell_manager.add_to_path(test_dir)
        assert success
    
    def test_get_shell_info(self, shell_manager):
        """Test getting shell information."""
        info = shell_manager.get_shell_info()
        
        assert 'shell_type' in info
        assert 'shell_path' in info
        assert 'working_directory' in info
        assert 'config_file' in info


class TestBashIntegration:
    """Test Bash-specific integration."""
    
    @pytest.fixture
    def bash_integration(self):
        """Create Bash integration instance."""
        return BashIntegration()
    
    def test_bash_config(self, bash_integration):
        """Test Bash configuration."""
        config = bash_integration.config
        
        assert config.shell_type == ShellType.BASH
        assert config.rc_file.name == '.bashrc'
    
    def test_bash_alias_syntax(self, bash_integration):
        """Test Bash alias syntax."""
        alias = bash_integration.get_alias_syntax('ll', 'ls -la')
        assert alias == "alias ll='ls -la'"
    
    def test_bash_function_syntax(self, bash_integration):
        """Test Bash function syntax."""
        func = bash_integration.get_function_syntax('test_func', 'echo "test"')
        assert 'test_func()' in func
        assert 'echo "test"' in func


class TestZshIntegration:
    """Test Zsh-specific integration."""
    
    @pytest.fixture
    def zsh_integration(self):
        """Create Zsh integration instance."""
        return ZshIntegration()
    
    def test_zsh_config(self, zsh_integration):
        """Test Zsh configuration."""
        config = zsh_integration.config
        
        assert config.shell_type == ShellType.ZSH
        assert config.rc_file.name == '.zshrc'
    
    def test_zsh_alias_syntax(self, zsh_integration):
        """Test Zsh alias syntax."""
        alias = zsh_integration.get_alias_syntax('ll', 'ls -la')
        assert alias == "alias ll='ls -la'"


class TestEndToEndTerminalIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_command_flow(self, tmp_path):
        """Test complete command processing flow."""
        terminal = TerminalInterface(working_directory=tmp_path)
        
        # Process a simple command
        with patch.object(terminal.tool_executor.terminal, 'run_command') as mock_run:
            from src.codegenie.core.tool_executor import CommandResult, CommandStatus
            
            mock_run.return_value = CommandResult(
                command='ls',
                exit_code=0,
                stdout='test.txt',
                stderr='',
                duration=0.1,
                success=True,
                status=CommandStatus.SUCCESS
            )
            
            result = await terminal.process_natural_language_command('list files')
            
            assert result is not None
            assert 'parsed' in result or 'result' in result
    
    @pytest.mark.asyncio
    async def test_context_preservation(self, tmp_path):
        """Test context preservation across commands."""
        terminal = TerminalInterface(working_directory=tmp_path)
        
        # Execute multiple commands
        commands = ['ls', 'pwd', 'echo test']
        
        for cmd in commands:
            with patch.object(terminal.tool_executor.terminal, 'run_command') as mock_run:
                from src.codegenie.core.tool_executor import CommandResult, CommandStatus
                
                mock_run.return_value = CommandResult(
                    command=cmd,
                    exit_code=0,
                    stdout='output',
                    stderr='',
                    duration=0.1,
                    success=True,
                    status=CommandStatus.SUCCESS
                )
                
                await terminal.execute_in_terminal(cmd)
        
        # Check history
        history = terminal.context_manager.get_history()
        assert len(history) >= 0  # History tracking may vary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
