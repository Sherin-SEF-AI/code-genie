"""
Unit tests for terminal integration components.

Tests cover:
- Natural language command parsing
- Terminal output formatting
- Context management
- Command execution
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.codegenie.integrations.terminal_integration import (
    NaturalLanguageCommandParser,
    TerminalOutputFormatter,
    TerminalContextManager,
    TerminalInterface,
    CommandIntent,
    ParsedCommand,
    CommandContext
)
from src.codegenie.core.tool_executor import CommandResult, CommandStatus


class TestNaturalLanguageCommandParser:
    """Test natural language command parser."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return NaturalLanguageCommandParser()
    
    @pytest.mark.asyncio
    async def test_parse_file_operation_intent(self, parser):
        """Test parsing file operation commands."""
        command = "create a file called test.py"
        intent = await parser.parse_intent(command)
        assert intent == CommandIntent.FILE_OPERATION
    
    @pytest.mark.asyncio
    async def test_parse_git_operation_intent(self, parser):
        """Test parsing git operation commands."""
        command = "show git status"
        intent = await parser.parse_intent(command)
        assert intent == CommandIntent.GIT_OPERATION
    
    @pytest.mark.asyncio
    async def test_parse_test_execution_intent(self, parser):
        """Test parsing test execution commands."""
        command = "run tests"
        intent = await parser.parse_intent(command)
        assert intent == CommandIntent.TEST_EXECUTION
    
    @pytest.mark.asyncio
    async def test_parse_search_intent(self, parser):
        """Test parsing search commands."""
        command = "find all Python files"
        intent = await parser.parse_intent(command)
        assert intent == CommandIntent.SEARCH
    
    @pytest.mark.asyncio
    async def test_extract_filename_parameter(self, parser):
        """Test extracting filename from command."""
        command = "create a file called test.py"
        intent = CommandIntent.FILE_OPERATION
        params = await parser.extract_parameters(command, intent)
        assert 'filename' in params
        assert params['filename'] == 'test.py'
    
    @pytest.mark.asyncio
    async def test_extract_git_commit_message(self, parser):
        """Test extracting git commit message."""
        command = 'commit with message "Initial commit"'
        intent = CommandIntent.GIT_OPERATION
        params = await parser.extract_parameters(command, intent)
        assert 'message' in params
        assert params['message'] == 'Initial commit'
    
    @pytest.mark.asyncio
    async def test_convert_file_create_to_executable(self, parser):
        """Test converting file creation to executable command."""
        intent = CommandIntent.FILE_OPERATION
        params = {'filename': 'test.py'}
        command = "create a file called test.py"
        
        executable = await parser.convert_to_executable(intent, params, command)
        assert executable is not None
        assert 'touch' in executable
        assert 'test.py' in executable
    
    @pytest.mark.asyncio
    async def test_convert_git_status_to_executable(self, parser):
        """Test converting git status to executable command."""
        intent = CommandIntent.GIT_OPERATION
        params = {}
        command = "show git status"
        
        executable = await parser.convert_to_executable(intent, params, command)
        assert executable == 'git status'
    
    @pytest.mark.asyncio
    async def test_parse_command_full_flow(self, parser):
        """Test full command parsing flow."""
        command = "create a file called test.py"
        parsed = await parser.parse_command(command)
        
        assert isinstance(parsed, ParsedCommand)
        assert parsed.intent == CommandIntent.FILE_OPERATION
        assert parsed.executable_command is not None
        assert parsed.confidence > 0.5


class TestTerminalOutputFormatter:
    """Test terminal output formatter."""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance."""
        return TerminalOutputFormatter()
    
    def test_format_command_result_success(self, formatter):
        """Test formatting successful command result."""
        result = CommandResult(
            command='ls -la',
            exit_code=0,
            stdout='file1.txt\nfile2.txt',
            stderr='',
            duration=0.5,
            success=True,
            status=CommandStatus.SUCCESS
        )
        
        formatted = formatter.format_command_result(result)
        assert 'ls -la' in formatted
        assert 'Success' in formatted
        assert 'file1.txt' in formatted
    
    def test_format_command_result_failure(self, formatter):
        """Test formatting failed command result."""
        result = CommandResult(
            command='invalid_command',
            exit_code=1,
            stdout='',
            stderr='command not found',
            duration=0.1,
            success=False,
            status=CommandStatus.FAILURE
        )
        
        formatted = formatter.format_command_result(result)
        assert 'invalid_command' in formatted
        assert 'Failed' in formatted
        assert 'command not found' in formatted
    
    def test_format_parsed_command(self, formatter):
        """Test formatting parsed command."""
        parsed = ParsedCommand(
            original_text='create file test.py',
            intent=CommandIntent.FILE_OPERATION,
            action='Create file',
            parameters={'filename': 'test.py'},
            confidence=0.9,
            executable_command='touch test.py'
        )
        
        formatted = formatter.format_parsed_command(parsed)
        assert 'file_operation' in formatted.lower()
        assert 'test.py' in formatted
        assert '90' in formatted  # confidence percentage
    
    def test_format_error(self, formatter):
        """Test formatting error message."""
        error = "Command failed"
        details = "File not found"
        
        formatted = formatter.format_error(error, details)
        assert 'Error' in formatted
        assert 'Command failed' in formatted
        assert 'File not found' in formatted
    
    def test_format_success(self, formatter):
        """Test formatting success message."""
        message = "Operation completed"
        formatted = formatter.format_success(message)
        assert 'Operation completed' in formatted


class TestTerminalContextManager:
    """Test terminal context manager."""
    
    @pytest.fixture
    def context_manager(self, tmp_path):
        """Create context manager instance."""
        return TerminalContextManager(working_directory=tmp_path)
    
    def test_initialization(self, context_manager, tmp_path):
        """Test context manager initialization."""
        context = context_manager.get_context()
        assert isinstance(context, CommandContext)
        assert context.working_directory == tmp_path
        assert context.shell_type in ['bash', 'zsh', 'fish', 'sh']
    
    def test_add_to_history(self, context_manager):
        """Test adding command to history."""
        result = CommandResult(
            command='ls',
            exit_code=0,
            stdout='',
            stderr='',
            duration=0.1,
            success=True,
            status=CommandStatus.SUCCESS
        )
        
        context_manager.add_to_history('ls', result)
        history = context_manager.get_history()
        
        assert len(history) == 1
        assert history[0] == 'ls'
    
    def test_get_last_result(self, context_manager):
        """Test getting last command result."""
        result = CommandResult(
            command='pwd',
            exit_code=0,
            stdout='/home/user',
            stderr='',
            duration=0.1,
            success=True,
            status=CommandStatus.SUCCESS
        )
        
        context_manager.add_to_history('pwd', result)
        last_result = context_manager.get_last_result()
        
        assert last_result is not None
        assert last_result.command == 'pwd'
    
    def test_set_and_get_context_data(self, context_manager):
        """Test storing and retrieving context data."""
        context_manager.set_context_data('key1', 'value1')
        value = context_manager.get_context_data('key1')
        
        assert value == 'value1'
    
    def test_clear_history(self, context_manager):
        """Test clearing command history."""
        result = CommandResult(
            command='ls',
            exit_code=0,
            stdout='',
            stderr='',
            duration=0.1,
            success=True,
            status=CommandStatus.SUCCESS
        )
        
        context_manager.add_to_history('ls', result)
        context_manager.clear_history()
        history = context_manager.get_history()
        
        assert len(history) == 0
    
    def test_update_working_directory(self, context_manager, tmp_path):
        """Test updating working directory."""
        new_dir = tmp_path / 'subdir'
        new_dir.mkdir()
        
        context_manager.update_working_directory(new_dir)
        context = context_manager.get_context()
        
        assert context.working_directory == new_dir


class TestTerminalInterface:
    """Test terminal interface."""
    
    @pytest.fixture
    def terminal_interface(self, tmp_path):
        """Create terminal interface instance."""
        return TerminalInterface(working_directory=tmp_path)
    
    @pytest.mark.asyncio
    async def test_process_simple_command(self, terminal_interface):
        """Test processing simple shell command."""
        with patch.object(terminal_interface.tool_executor.terminal, 'run_command') as mock_run:
            mock_run.return_value = CommandResult(
                command='ls',
                exit_code=0,
                stdout='file1.txt',
                stderr='',
                duration=0.1,
                success=True,
                status=CommandStatus.SUCCESS
            )
            
            result = await terminal_interface.process_natural_language_command('ls')
            
            assert result['success']
            assert 'result' in result
    
    @pytest.mark.asyncio
    async def test_process_natural_language_command(self, terminal_interface):
        """Test processing natural language command."""
        with patch.object(terminal_interface.tool_executor.terminal, 'run_command') as mock_run:
            mock_run.return_value = CommandResult(
                command='touch test.py',
                exit_code=0,
                stdout='',
                stderr='',
                duration=0.1,
                success=True,
                status=CommandStatus.SUCCESS
            )
            
            result = await terminal_interface.process_natural_language_command(
                'create a file called test.py',
                auto_execute=True
            )
            
            assert 'parsed' in result
            assert result['parsed'].intent == CommandIntent.FILE_OPERATION
    
    @pytest.mark.asyncio
    async def test_command_requires_confirmation(self, terminal_interface):
        """Test command that requires confirmation."""
        result = await terminal_interface.process_natural_language_command(
            'delete all files',
            auto_execute=False
        )
        
        # Should require confirmation for destructive operations
        assert 'requires_confirmation' in result or not result.get('success')
    
    @pytest.mark.asyncio
    async def test_execute_in_terminal(self, terminal_interface):
        """Test executing command in terminal."""
        with patch.object(terminal_interface.tool_executor.terminal, 'run_command') as mock_run:
            mock_run.return_value = CommandResult(
                command='echo test',
                exit_code=0,
                stdout='test',
                stderr='',
                duration=0.1,
                success=True,
                status=CommandStatus.SUCCESS
            )
            
            result = await terminal_interface.execute_in_terminal('echo test')
            
            assert result.success
            assert result.stdout == 'test'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
