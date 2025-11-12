"""
Interactive Terminal Session with multi-turn conversation support.

This module provides enhanced interactive terminal capabilities including:
- Multi-turn conversation support
- Command history and context awareness
- Real-time output streaming
- Tab completion for common commands
"""

import asyncio
import readline
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .terminal_integration import (
    TerminalInterface,
    TerminalContextManager,
    CommandContext,
    ParsedCommand
)
from ..core.tool_executor import CommandResult


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    user_input: str
    parsed_command: Optional[ParsedCommand]
    result: Optional[CommandResult]
    timestamp: datetime
    success: bool
    context_snapshot: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """State of the interactive session."""
    session_id: str
    start_time: datetime
    turns: List[ConversationTurn] = field(default_factory=list)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    active: bool = True



class CommandHistoryManager:
    """Manages command history with search and recall capabilities."""
    
    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize history manager.
        
        Args:
            history_file: Path to history file for persistence
        """
        self.history_file = history_file or Path.home() / '.codegenie_history'
        self.history: List[str] = []
        self.history_index = 0
        self._load_history()
        self._setup_readline()
    
    def _load_history(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = [line.strip() for line in f.readlines()]
                    # Load into readline
                    for cmd in self.history:
                        readline.add_history(cmd)
            except Exception:
                pass
    
    def _save_history(self) -> None:
        """Save history to file."""
        try:
            with open(self.history_file, 'w') as f:
                for cmd in self.history[-1000:]:  # Keep last 1000 commands
                    f.write(f"{cmd}\n")
        except Exception:
            pass
    
    def _setup_readline(self) -> None:
        """Setup readline for command history and completion."""
        try:
            # Set history length
            readline.set_history_length(1000)
            
            # Enable tab completion
            readline.parse_and_bind('tab: complete')
            
            # Set up key bindings for history navigation
            readline.parse_and_bind(r'"\e[A": previous-history')  # Up arrow
            readline.parse_and_bind(r'"\e[B": next-history')      # Down arrow
            
        except Exception:
            pass
    
    def add_command(self, command: str) -> None:
        """
        Add command to history.
        
        Args:
            command: Command to add
        """
        if command and command.strip():
            self.history.append(command.strip())
            readline.add_history(command.strip())
            self._save_history()
    
    def search_history(self, pattern: str) -> List[str]:
        """
        Search history for pattern.
        
        Args:
            pattern: Search pattern
            
        Returns:
            List of matching commands
        """
        return [cmd for cmd in self.history if pattern.lower() in cmd.lower()]
    
    def get_recent(self, limit: int = 10) -> List[str]:
        """
        Get recent commands.
        
        Args:
            limit: Number of commands to return
            
        Returns:
            List of recent commands
        """
        return self.history[-limit:]
    
    def clear(self) -> None:
        """Clear command history."""
        self.history.clear()
        readline.clear_history()
        if self.history_file.exists():
            self.history_file.unlink()


class TabCompleter:
    """Provides tab completion for commands and file paths."""
    
    def __init__(self, context_manager: TerminalContextManager):
        """
        Initialize tab completer.
        
        Args:
            context_manager: Context manager for current directory info
        """
        self.context_manager = context_manager
        self.commands = self._load_common_commands()
        self.current_matches: List[str] = []
        
        # Set up readline completer
        readline.set_completer(self.complete)
        readline.set_completer_delims(' \t\n')
    
    def _load_common_commands(self) -> List[str]:
        """Load common commands for completion."""
        return [
            # File operations
            'create file', 'create directory', 'delete', 'copy', 'move',
            'list files', 'show files',
            
            # Git operations
            'git status', 'git commit', 'git push', 'git pull',
            'git diff', 'git log', 'git branch',
            
            # Code operations
            'analyze', 'refactor', 'test', 'debug',
            'generate', 'implement', 'create function',
            
            # Search operations
            'find', 'search', 'locate', 'grep',
            
            # Shell commands
            'ls', 'cd', 'pwd', 'cat', 'grep', 'find', 'mkdir', 'rm',
            'python', 'node', 'npm', 'pip',
            
            # Special commands
            'help', 'history', 'clear', 'exit', 'quit'
        ]
    
    def complete(self, text: str, state: int) -> Optional[str]:
        """
        Readline completion function.
        
        Args:
            text: Text to complete
            state: Completion state
            
        Returns:
            Completion suggestion or None
        """
        if state == 0:
            # Generate new matches
            line = readline.get_line_buffer()
            self.current_matches = self._get_matches(text, line)
        
        try:
            return self.current_matches[state]
        except IndexError:
            return None
    
    def _get_matches(self, text: str, line: str) -> List[str]:
        """
        Get completion matches.
        
        Args:
            text: Text to complete
            line: Full line buffer
            
        Returns:
            List of matches
        """
        matches = []
        
        # If at start of line, complete commands
        if line.strip() == text:
            matches.extend([cmd for cmd in self.commands if cmd.startswith(text)])
        
        # Complete file paths
        try:
            cwd = self.context_manager.get_context().working_directory
            
            # Handle relative paths
            if '/' in text or text.startswith('.'):
                path_part = Path(text)
                if path_part.is_absolute():
                    search_dir = path_part.parent
                    prefix = path_part.name
                else:
                    search_dir = cwd / path_part.parent
                    prefix = path_part.name
            else:
                search_dir = cwd
                prefix = text
            
            # Find matching files/directories
            if search_dir.exists():
                for item in search_dir.iterdir():
                    if item.name.startswith(prefix):
                        # Add trailing slash for directories
                        match = str(item.relative_to(cwd))
                        if item.is_dir():
                            match += '/'
                        matches.append(match)
        except Exception:
            pass
        
        return sorted(matches)



class OutputStreamer:
    """Handles real-time output streaming for long-running commands."""
    
    def __init__(self):
        """Initialize output streamer."""
        self.streaming = False
        self.buffer: List[str] = []
    
    async def stream_command_output(
        self,
        command: str,
        executor: Callable,
        callback: Optional[Callable[[str], None]] = None
    ) -> CommandResult:
        """
        Stream command output in real-time.
        
        Args:
            command: Command to execute
            executor: Async function to execute command
            callback: Optional callback for each line of output
            
        Returns:
            CommandResult after completion
        """
        self.streaming = True
        self.buffer.clear()
        
        def line_callback(line: str):
            """Handle each line of output."""
            self.buffer.append(line)
            print(line, flush=True)
            if callback:
                callback(line)
        
        try:
            result = await executor(command, line_callback)
            return result
        finally:
            self.streaming = False
    
    def get_buffer(self) -> List[str]:
        """
        Get buffered output.
        
        Returns:
            List of output lines
        """
        return self.buffer.copy()
    
    def clear_buffer(self) -> None:
        """Clear output buffer."""
        self.buffer.clear()


class ConversationManager:
    """Manages multi-turn conversation context and state."""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize conversation manager.
        
        Args:
            session_id: Optional session ID
        """
        self.session = SessionState(
            session_id=session_id or f"session_{datetime.now().timestamp()}",
            start_time=datetime.now()
        )
    
    def add_turn(
        self,
        user_input: str,
        parsed_command: Optional[ParsedCommand],
        result: Optional[CommandResult],
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation turn.
        
        Args:
            user_input: User's input
            parsed_command: Parsed command
            result: Command result
            success: Whether turn was successful
            context: Optional context snapshot
        """
        turn = ConversationTurn(
            user_input=user_input,
            parsed_command=parsed_command,
            result=result,
            timestamp=datetime.now(),
            success=success,
            context_snapshot=context or {}
        )
        self.session.turns.append(turn)
    
    def get_recent_turns(self, limit: int = 5) -> List[ConversationTurn]:
        """
        Get recent conversation turns.
        
        Args:
            limit: Number of turns to return
            
        Returns:
            List of recent turns
        """
        return self.session.turns[-limit:]
    
    def get_context_from_history(self) -> Dict[str, Any]:
        """
        Extract context from conversation history.
        
        Returns:
            Dictionary of context information
        """
        context = {
            'total_turns': len(self.session.turns),
            'successful_turns': sum(1 for t in self.session.turns if t.success),
            'failed_turns': sum(1 for t in self.session.turns if not t.success),
            'session_duration': (datetime.now() - self.session.start_time).total_seconds(),
        }
        
        # Extract common patterns
        recent_commands = [t.user_input for t in self.get_recent_turns(10)]
        context['recent_commands'] = recent_commands
        
        # Track working directories
        recent_dirs = []
        for turn in self.get_recent_turns(10):
            if turn.context_snapshot.get('working_directory'):
                recent_dirs.append(turn.context_snapshot['working_directory'])
        if recent_dirs:
            context['recent_directories'] = list(set(recent_dirs))
        
        return context
    
    def set_preference(self, key: str, value: Any) -> None:
        """
        Set user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.session.user_preferences[key] = value
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get user preference.
        
        Args:
            key: Preference key
            default: Default value
            
        Returns:
            Preference value or default
        """
        return self.session.user_preferences.get(key, default)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get session summary.
        
        Returns:
            Dictionary with session statistics
        """
        return {
            'session_id': self.session.session_id,
            'start_time': self.session.start_time.isoformat(),
            'duration': (datetime.now() - self.session.start_time).total_seconds(),
            'total_turns': len(self.session.turns),
            'successful_turns': sum(1 for t in self.session.turns if t.success),
            'failed_turns': sum(1 for t in self.session.turns if not t.success),
            'preferences': self.session.user_preferences
        }



class InteractiveTerminalSession:
    """
    Enhanced interactive terminal session with multi-turn conversation support.
    
    Provides:
    - Multi-turn conversation with context awareness
    - Command history with search and recall
    - Real-time output streaming
    - Tab completion for commands and paths
    """
    
    def __init__(
        self,
        terminal_interface: Optional[TerminalInterface] = None,
        working_directory: Optional[Path] = None
    ):
        """
        Initialize interactive session.
        
        Args:
            terminal_interface: TerminalInterface instance
            working_directory: Initial working directory
        """
        self.terminal = terminal_interface or TerminalInterface(working_directory=working_directory)
        self.history_manager = CommandHistoryManager()
        self.tab_completer = TabCompleter(self.terminal.context_manager)
        self.output_streamer = OutputStreamer()
        self.conversation_manager = ConversationManager()
        self.running = False
    
    async def start(self) -> None:
        """Start the interactive terminal session."""
        self.running = True
        
        # Display welcome message
        self._display_welcome()
        
        # Main interaction loop
        while self.running:
            try:
                # Get user input with prompt
                prompt = self._get_prompt()
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Add to history
                self.history_manager.add_command(user_input)
                
                # Handle special commands
                if await self._handle_special_command(user_input):
                    continue
                
                # Process command
                await self._process_command(user_input)
                
            except KeyboardInterrupt:
                print("\n" + self.terminal.formatter.format_info("Use 'exit' to quit"))
            except EOFError:
                print()
                break
            except Exception as e:
                print(self.terminal.formatter.format_error(f"Error: {e}"))
        
        # Display goodbye message
        self._display_goodbye()
    
    def _display_welcome(self) -> None:
        """Display welcome message."""
        context = self.terminal.context_manager.get_context()
        
        print("=" * 60)
        print("  CodeGenie Interactive Terminal")
        print("  Natural Language Command Interface")
        print("=" * 60)
        print()
        print(f"  Working Directory: {context.working_directory}")
        print(f"  Shell: {context.shell_type}")
        print(f"  Session ID: {self.conversation_manager.session.session_id}")
        print()
        print("  Commands:")
        print("    - Use natural language: 'create a file called test.py'")
        print("    - Use shell commands: 'ls -la'")
        print("    - Type 'help' for more information")
        print("    - Type 'exit' or press Ctrl+D to quit")
        print()
        print("  Features:")
        print("    - Tab completion for commands and paths")
        print("    - Command history (use up/down arrows)")
        print("    - Real-time output streaming")
        print("    - Context-aware suggestions")
        print()
    
    def _display_goodbye(self) -> None:
        """Display goodbye message with session summary."""
        summary = self.conversation_manager.get_session_summary()
        
        print()
        print("=" * 60)
        print("  Session Summary")
        print("=" * 60)
        print(f"  Duration: {summary['duration']:.1f} seconds")
        print(f"  Total Commands: {summary['total_turns']}")
        print(f"  Successful: {summary['successful_turns']}")
        print(f"  Failed: {summary['failed_turns']}")
        print()
        print("  Thank you for using CodeGenie!")
        print("=" * 60)
    
    def _get_prompt(self) -> str:
        """
        Get command prompt.
        
        Returns:
            Prompt string
        """
        context = self.terminal.context_manager.get_context()
        cwd = context.working_directory
        
        # Shorten path if too long
        cwd_str = str(cwd)
        home = str(Path.home())
        if cwd_str.startswith(home):
            cwd_str = '~' + cwd_str[len(home):]
        
        return f"\n{cwd_str} $ "
    
    async def _handle_special_command(self, command: str) -> bool:
        """
        Handle special commands.
        
        Args:
            command: Command to check
            
        Returns:
            True if command was handled, False otherwise
        """
        cmd_lower = command.lower().strip()
        
        if cmd_lower in ['exit', 'quit']:
            self.running = False
            return True
        
        if cmd_lower == 'help':
            self._show_help()
            return True
        
        if cmd_lower == 'history':
            self._show_history()
            return True
        
        if cmd_lower.startswith('history search '):
            pattern = cmd_lower[15:].strip()
            self._search_history(pattern)
            return True
        
        if cmd_lower == 'clear':
            os.system('clear' if os.name != 'nt' else 'cls')
            return True
        
        if cmd_lower == 'status':
            self._show_status()
            return True
        
        if cmd_lower == 'context':
            self._show_context()
            return True
        
        if cmd_lower.startswith('cd '):
            # Handle directory change
            new_dir = command[3:].strip()
            self._change_directory(new_dir)
            return True
        
        return False
    
    async def _process_command(self, command: str) -> None:
        """
        Process a user command.
        
        Args:
            command: Command to process
        """
        # Check if command should be streamed
        stream_output = self._should_stream_output(command)
        
        try:
            if stream_output:
                # Stream output in real-time
                print(self.terminal.formatter.format_info("Executing (streaming output)..."))
                result = await self.terminal.execute_in_terminal(command, stream_output=True)
                parsed = None
            else:
                # Process normally
                response = await self.terminal.process_natural_language_command(command)
                
                if response.get('requires_confirmation'):
                    # Ask for confirmation
                    print(self.terminal.formatter.format_warning(response['message']))
                    confirm = input("Execute? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print(self.terminal.formatter.format_info("Command cancelled"))
                        return
                    
                    # Re-process with auto-execute
                    response = await self.terminal.process_natural_language_command(command, auto_execute=True)
                
                # Display output
                if response.get('formatted_output'):
                    print(response['formatted_output'])
                
                result = response.get('result')
                parsed = response.get('parsed')
            
            # Add to conversation history
            success = result.success if result else response.get('success', False)
            self.conversation_manager.add_turn(
                user_input=command,
                parsed_command=parsed,
                result=result,
                success=success,
                context={
                    'working_directory': str(self.terminal.context_manager.get_context().working_directory)
                }
            )
            
        except Exception as e:
            print(self.terminal.formatter.format_error(f"Error: {e}"))
            self.conversation_manager.add_turn(
                user_input=command,
                parsed_command=None,
                result=None,
                success=False
            )
    
    def _should_stream_output(self, command: str) -> bool:
        """
        Determine if command output should be streamed.
        
        Args:
            command: Command to check
            
        Returns:
            True if output should be streamed
        """
        # Stream output for long-running commands
        streaming_commands = ['tail', 'watch', 'top', 'htop', 'npm run', 'python -m']
        return any(cmd in command.lower() for cmd in streaming_commands)
    
    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
╔════════════════════════════════════════════════════════════╗
║                    CodeGenie Terminal Help                  ║
╚════════════════════════════════════════════════════════════╝

Natural Language Commands:
  • "create a file called test.py"
  • "list all files in the current directory"
  • "show git status"
  • "run tests"
  • "find all Python files"
  • "analyze code in main.py"

Direct Shell Commands:
  • ls -la
  • git status
  • python script.py
  • npm test

Special Commands:
  • help              - Show this help
  • history           - Show command history
  • history search X  - Search history for X
  • status            - Show session status
  • context           - Show conversation context
  • clear             - Clear screen
  • exit / quit       - Exit terminal

Features:
  • Tab completion    - Press Tab to complete commands/paths
  • History recall    - Use Up/Down arrows for history
  • Real-time output  - Long commands stream output
  • Context aware     - Remembers your conversation
"""
        print(help_text)
    
    def _show_history(self) -> None:
        """Show command history."""
        recent = self.history_manager.get_recent(20)
        
        if not recent:
            print(self.terminal.formatter.format_info("No command history"))
            return
        
        print(self.terminal.formatter.format_info("Recent Commands:"))
        for i, cmd in enumerate(recent, 1):
            print(f"  {i:2d}. {cmd}")
    
    def _search_history(self, pattern: str) -> None:
        """
        Search command history.
        
        Args:
            pattern: Search pattern
        """
        matches = self.history_manager.search_history(pattern)
        
        if not matches:
            print(self.terminal.formatter.format_info(f"No matches found for '{pattern}'"))
            return
        
        print(self.terminal.formatter.format_info(f"Commands matching '{pattern}':"))
        for i, cmd in enumerate(matches, 1):
            print(f"  {i:2d}. {cmd}")
    
    def _show_status(self) -> None:
        """Show session status."""
        summary = self.conversation_manager.get_session_summary()
        context = self.terminal.context_manager.get_context()
        
        print(self.terminal.formatter.format_info("Session Status:"))
        print(f"  Session ID: {summary['session_id']}")
        print(f"  Duration: {summary['duration']:.1f}s")
        print(f"  Commands: {summary['total_turns']} (✓ {summary['successful_turns']}, ✗ {summary['failed_turns']})")
        print(f"  Working Dir: {context.working_directory}")
        print(f"  Shell: {context.shell_type}")
    
    def _show_context(self) -> None:
        """Show conversation context."""
        context = self.conversation_manager.get_context_from_history()
        
        print(self.terminal.formatter.format_info("Conversation Context:"))
        print(f"  Total Turns: {context['total_turns']}")
        print(f"  Success Rate: {context['successful_turns']}/{context['total_turns']}")
        
        if context.get('recent_commands'):
            print(f"\n  Recent Commands:")
            for cmd in context['recent_commands'][-5:]:
                print(f"    • {cmd}")
        
        if context.get('recent_directories'):
            print(f"\n  Recent Directories:")
            for dir in context['recent_directories']:
                print(f"    • {dir}")
    
    def _change_directory(self, path: str) -> None:
        """
        Change working directory.
        
        Args:
            path: New directory path
        """
        try:
            new_path = Path(path).expanduser().resolve()
            if new_path.exists() and new_path.is_dir():
                self.terminal.context_manager.update_working_directory(new_path)
                print(self.terminal.formatter.format_success(f"Changed directory to {new_path}"))
            else:
                print(self.terminal.formatter.format_error(f"Directory not found: {path}"))
        except Exception as e:
            print(self.terminal.formatter.format_error(f"Error changing directory: {e}"))
    
    def stop(self) -> None:
        """Stop the interactive session."""
        self.running = False
