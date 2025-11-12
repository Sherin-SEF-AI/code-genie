"""
Terminal Integration for natural language command processing.

This module provides a native terminal interface where developers can interact
with CodeGenie using natural language commands, similar to Claude Code's terminal experience.
"""

import asyncio
import os
import re
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.tool_executor import ToolExecutor, CommandResult


class CommandIntent(Enum):
    """Types of command intents."""
    FILE_OPERATION = "file_operation"
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    TEST_EXECUTION = "test_execution"
    GIT_OPERATION = "git_operation"
    SEARCH = "search"
    REFACTOR = "refactor"
    DEBUG = "debug"
    EXPLAIN = "explain"
    SHELL_COMMAND = "shell_command"
    UNKNOWN = "unknown"


@dataclass
class CommandContext:
    """Context for terminal command execution."""
    working_directory: Path
    environment_variables: Dict[str, str]
    shell_type: str
    history: List[str] = field(default_factory=list)
    session_id: str = ""
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedCommand:
    """Parsed natural language command."""
    original_text: str
    intent: CommandIntent
    action: str
    parameters: Dict[str, Any]
    confidence: float
    executable_command: Optional[str] = None
    requires_confirmation: bool = False



class NaturalLanguageCommandParser:
    """Parses natural language commands into executable actions."""
    
    def __init__(self):
        """Initialize command parser with patterns."""
        self.intent_patterns = self._load_intent_patterns()
        self.action_templates = self._load_action_templates()
    
    def _load_intent_patterns(self) -> Dict[CommandIntent, List[str]]:
        """Load regex patterns for intent recognition."""
        return {
            CommandIntent.FILE_OPERATION: [
                r'(create|make|generate)\s+(a\s+)?(file|directory|folder)',
                r'(delete|remove|rm)\s+',
                r'(copy|cp|move|mv)\s+',
                r'(list|ls|show)\s+(files|directories)',
            ],
            CommandIntent.CODE_GENERATION: [
                r'(write|create|generate|implement)\s+(a\s+)?(function|class|method|api)',
                r'(add|create)\s+(a\s+)?(test|unit test|integration test)',
                r'(scaffold|setup|initialize)\s+',
            ],
            CommandIntent.CODE_ANALYSIS: [
                r'(analyze|check|review|inspect)\s+',
                r'(find|search for)\s+(bugs|issues|problems|errors)',
                r'(what|how)\s+(does|is)\s+',
                r'(explain|describe)\s+',
            ],
            CommandIntent.TEST_EXECUTION: [
                r'(run|execute)\s+(tests|test suite)',
                r'(test|check)\s+',
            ],
            CommandIntent.GIT_OPERATION: [
                r'(git|commit|push|pull|branch|merge)',
                r'(create|make)\s+(a\s+)?commit',
                r'(show|display)\s+(git\s+)?(status|diff|log)',
            ],
            CommandIntent.SEARCH: [
                r'(find|search|locate|grep)\s+',
                r'(where|which)\s+(is|are)\s+',
            ],
            CommandIntent.REFACTOR: [
                r'(refactor|restructure|reorganize|optimize)',
                r'(rename|extract|inline)\s+',
            ],
            CommandIntent.DEBUG: [
                r'(debug|fix|solve)\s+',
                r'(why|what)\s+(is|are)\s+(wrong|broken|failing)',
            ],
            CommandIntent.SHELL_COMMAND: [
                r'^(ls|cd|pwd|cat|grep|find|echo|mkdir|rm|cp|mv)',
            ],
        }
    
    def _load_action_templates(self) -> Dict[CommandIntent, Dict[str, str]]:
        """Load action templates for command execution."""
        return {
            CommandIntent.FILE_OPERATION: {
                'create_file': 'touch {filename}',
                'create_directory': 'mkdir -p {dirname}',
                'delete': 'rm -rf {path}',
                'copy': 'cp -r {source} {destination}',
                'move': 'mv {source} {destination}',
                'list': 'ls -la {path}',
            },
            CommandIntent.GIT_OPERATION: {
                'status': 'git status',
                'diff': 'git diff',
                'log': 'git log --oneline -10',
                'commit': 'git commit -m "{message}"',
                'push': 'git push',
                'pull': 'git pull',
            },
            CommandIntent.TEST_EXECUTION: {
                'run_tests': 'pytest',
                'run_specific_test': 'pytest {test_file}',
            },
        }
    
    async def parse_intent(self, command: str) -> CommandIntent:
        """
        Parse command to determine intent.
        
        Args:
            command: Natural language command
            
        Returns:
            CommandIntent enum value
        """
        command_lower = command.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command_lower):
                    return intent
        
        return CommandIntent.UNKNOWN
    
    async def extract_parameters(
        self,
        command: str,
        intent: CommandIntent
    ) -> Dict[str, Any]:
        """
        Extract parameters from command based on intent.
        
        Args:
            command: Natural language command
            intent: Detected command intent
            
        Returns:
            Dictionary of extracted parameters
        """
        parameters = {}
        command_lower = command.lower().strip()
        
        # Extract file/directory names
        if intent in [CommandIntent.FILE_OPERATION, CommandIntent.CODE_GENERATION]:
            # Look for quoted strings or file paths
            quoted = re.findall(r'["\']([^"\']+)["\']', command)
            if quoted:
                parameters['filename'] = quoted[0]
            else:
                # Look for file extensions
                files = re.findall(r'\b[\w/.-]+\.\w+\b', command)
                if files:
                    parameters['filename'] = files[0]
                
                # Look for directory names
                dirs = re.findall(r'\b[\w/-]+/\b', command)
                if dirs:
                    parameters['dirname'] = dirs[0]
        
        # Extract git commit messages
        if intent == CommandIntent.GIT_OPERATION:
            if 'commit' in command_lower:
                # Extract message in quotes
                messages = re.findall(r'["\']([^"\']+)["\']', command)
                if messages:
                    parameters['message'] = messages[0]
                else:
                    # Use everything after "commit"
                    match = re.search(r'commit\s+(.+)', command_lower)
                    if match:
                        parameters['message'] = match.group(1).strip()
        
        # Extract search terms
        if intent == CommandIntent.SEARCH:
            # Extract quoted search terms
            terms = re.findall(r'["\']([^"\']+)["\']', command)
            if terms:
                parameters['search_term'] = terms[0]
            else:
                # Extract term after "find" or "search"
                match = re.search(r'(?:find|search|locate|grep)\s+(?:for\s+)?(.+)', command_lower)
                if match:
                    parameters['search_term'] = match.group(1).strip()
        
        # Extract function/class names
        if intent in [CommandIntent.CODE_GENERATION, CommandIntent.REFACTOR]:
            # Look for identifiers
            identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', command)
            if identifiers:
                # Filter out common words
                common_words = {'create', 'make', 'generate', 'function', 'class', 'method', 'a', 'the', 'for', 'in'}
                filtered = [id for id in identifiers if id.lower() not in common_words]
                if filtered:
                    parameters['identifier'] = filtered[0]
        
        return parameters

    async def convert_to_executable(
        self,
        intent: CommandIntent,
        params: Dict[str, Any],
        command: str
    ) -> Optional[str]:
        """
        Convert intent and parameters to executable command.
        
        Args:
            intent: Command intent
            params: Extracted parameters
            command: Original command text
            
        Returns:
            Executable shell command or None
        """
        # For shell commands, return as-is
        if intent == CommandIntent.SHELL_COMMAND:
            return command.strip()
        
        # Get action templates for intent
        templates = self.action_templates.get(intent, {})
        
        # Determine specific action
        command_lower = command.lower()
        
        if intent == CommandIntent.FILE_OPERATION:
            if 'create' in command_lower or 'make' in command_lower:
                if 'directory' in command_lower or 'folder' in command_lower:
                    dirname = params.get('dirname', params.get('filename', 'new_directory'))
                    return templates['create_directory'].format(dirname=dirname)
                else:
                    filename = params.get('filename', 'new_file.txt')
                    return templates['create_file'].format(filename=filename)
            elif 'delete' in command_lower or 'remove' in command_lower:
                path = params.get('filename', params.get('dirname', '.'))
                return templates['delete'].format(path=path)
            elif 'list' in command_lower or 'ls' in command_lower:
                path = params.get('dirname', '.')
                return templates['list'].format(path=path)
        
        elif intent == CommandIntent.GIT_OPERATION:
            if 'status' in command_lower:
                return templates['status']
            elif 'diff' in command_lower:
                return templates['diff']
            elif 'log' in command_lower:
                return templates['log']
            elif 'commit' in command_lower:
                message = params.get('message', 'Update')
                return templates['commit'].format(message=message)
            elif 'push' in command_lower:
                return templates['push']
            elif 'pull' in command_lower:
                return templates['pull']
        
        elif intent == CommandIntent.TEST_EXECUTION:
            if 'test_file' in params:
                return templates['run_specific_test'].format(test_file=params['test_file'])
            else:
                return templates['run_tests']
        
        return None
    
    async def parse_command(self, command: str) -> ParsedCommand:
        """
        Parse natural language command into structured format.
        
        Args:
            command: Natural language command
            
        Returns:
            ParsedCommand with intent, parameters, and executable command
        """
        # Detect intent
        intent = await self.parse_intent(command)
        
        # Extract parameters
        parameters = await self.extract_parameters(command, intent)
        
        # Convert to executable command
        executable = await self.convert_to_executable(intent, parameters, command)
        
        # Determine action description
        action = self._describe_action(intent, parameters)
        
        # Calculate confidence
        confidence = 0.9 if executable else 0.5
        
        # Determine if confirmation is needed
        requires_confirmation = intent in [
            CommandIntent.FILE_OPERATION,
            CommandIntent.GIT_OPERATION,
            CommandIntent.REFACTOR
        ] and any(word in command.lower() for word in ['delete', 'remove', 'rm', 'commit', 'push'])
        
        return ParsedCommand(
            original_text=command,
            intent=intent,
            action=action,
            parameters=parameters,
            confidence=confidence,
            executable_command=executable,
            requires_confirmation=requires_confirmation
        )
    
    def _describe_action(self, intent: CommandIntent, params: Dict[str, Any]) -> str:
        """Generate human-readable action description."""
        if intent == CommandIntent.FILE_OPERATION:
            if 'filename' in params:
                return f"File operation on {params['filename']}"
            return "File operation"
        elif intent == CommandIntent.CODE_GENERATION:
            return "Generate code"
        elif intent == CommandIntent.CODE_ANALYSIS:
            return "Analyze code"
        elif intent == CommandIntent.TEST_EXECUTION:
            return "Run tests"
        elif intent == CommandIntent.GIT_OPERATION:
            return "Git operation"
        elif intent == CommandIntent.SEARCH:
            term = params.get('search_term', 'content')
            return f"Search for '{term}'"
        elif intent == CommandIntent.REFACTOR:
            return "Refactor code"
        elif intent == CommandIntent.DEBUG:
            return "Debug code"
        elif intent == CommandIntent.SHELL_COMMAND:
            return "Execute shell command"
        else:
            return "Process command"



class TerminalOutputFormatter:
    """Formats output for user-friendly terminal display."""
    
    def __init__(self):
        """Initialize output formatter."""
        self.use_colors = self._check_color_support()
    
    def _check_color_support(self) -> bool:
        """Check if terminal supports colors."""
        return os.getenv('TERM', '').lower() not in ['dumb', ''] and hasattr(os.sys.stdout, 'isatty') and os.sys.stdout.isatty()
    
    def format_command_result(self, result: CommandResult) -> str:
        """
        Format command execution result for display.
        
        Args:
            result: CommandResult to format
            
        Returns:
            Formatted string for terminal display
        """
        lines = []
        
        # Add command
        lines.append(self._format_header("Command"))
        lines.append(f"  {result.command}")
        lines.append("")
        
        # Add status
        status_symbol = "✓" if result.success else "✗"
        status_text = "Success" if result.success else "Failed"
        lines.append(self._format_header("Status"))
        lines.append(f"  {status_symbol} {status_text} (exit code: {result.exit_code})")
        lines.append(f"  Duration: {result.duration:.2f}s")
        lines.append("")
        
        # Add output
        if result.stdout:
            lines.append(self._format_header("Output"))
            for line in result.stdout.strip().split('\n'):
                lines.append(f"  {line}")
            lines.append("")
        
        # Add errors
        if result.stderr:
            lines.append(self._format_header("Errors"))
            for line in result.stderr.strip().split('\n'):
                lines.append(f"  {line}")
            lines.append("")
        
        # Add analysis if available
        if result.analysis and result.analysis.suggested_fix:
            lines.append(self._format_header("Suggestion"))
            lines.append(f"  {result.analysis.suggested_fix}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def format_parsed_command(self, parsed: ParsedCommand) -> str:
        """
        Format parsed command for display.
        
        Args:
            parsed: ParsedCommand to format
            
        Returns:
            Formatted string
        """
        lines = []
        lines.append(self._format_header("Parsed Command"))
        lines.append(f"  Intent: {parsed.intent.value}")
        lines.append(f"  Action: {parsed.action}")
        lines.append(f"  Confidence: {parsed.confidence:.1%}")
        
        if parsed.parameters:
            lines.append("  Parameters:")
            for key, value in parsed.parameters.items():
                lines.append(f"    - {key}: {value}")
        
        if parsed.executable_command:
            lines.append(f"  Executable: {parsed.executable_command}")
        
        return '\n'.join(lines)
    
    def format_error(self, error: str, details: Optional[str] = None) -> str:
        """
        Format error message.
        
        Args:
            error: Error message
            details: Optional error details
            
        Returns:
            Formatted error string
        """
        lines = []
        lines.append(self._colorize("✗ Error:", "red"))
        lines.append(f"  {error}")
        
        if details:
            lines.append("")
            lines.append("Details:")
            for line in details.split('\n'):
                lines.append(f"  {line}")
        
        return '\n'.join(lines)
    
    def format_success(self, message: str) -> str:
        """
        Format success message.
        
        Args:
            message: Success message
            
        Returns:
            Formatted success string
        """
        return self._colorize(f"✓ {message}", "green")
    
    def format_info(self, message: str) -> str:
        """
        Format info message.
        
        Args:
            message: Info message
            
        Returns:
            Formatted info string
        """
        return self._colorize(f"ℹ {message}", "blue")
    
    def format_warning(self, message: str) -> str:
        """
        Format warning message.
        
        Args:
            message: Warning message
            
        Returns:
            Formatted warning string
        """
        return self._colorize(f"⚠ {message}", "yellow")
    
    def _format_header(self, text: str) -> str:
        """Format section header."""
        return self._colorize(f"[{text}]", "cyan")
    
    def _colorize(self, text: str, color: str) -> str:
        """
        Add color to text if supported.
        
        Args:
            text: Text to colorize
            color: Color name
            
        Returns:
            Colorized text or plain text
        """
        if not self.use_colors:
            return text
        
        colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'reset': '\033[0m'
        }
        
        color_code = colors.get(color, '')
        reset_code = colors['reset']
        
        return f"{color_code}{text}{reset_code}"



class TerminalContextManager:
    """Manages terminal session context and history."""
    
    def __init__(self, working_directory: Optional[Path] = None):
        """
        Initialize context manager.
        
        Args:
            working_directory: Initial working directory
        """
        self.context = CommandContext(
            working_directory=working_directory or Path.cwd(),
            environment_variables=dict(os.environ),
            shell_type=self._detect_shell(),
            session_id=f"session_{datetime.now().timestamp()}"
        )
        self.command_history: List[Tuple[str, CommandResult]] = []
        self.context_data: Dict[str, Any] = {}
    
    def _detect_shell(self) -> str:
        """Detect current shell type."""
        shell = os.getenv('SHELL', '')
        if 'bash' in shell:
            return 'bash'
        elif 'zsh' in shell:
            return 'zsh'
        elif 'fish' in shell:
            return 'fish'
        else:
            return 'sh'
    
    def add_to_history(self, command: str, result: CommandResult) -> None:
        """
        Add command and result to history.
        
        Args:
            command: Executed command
            result: Command result
        """
        self.context.history.append(command)
        self.command_history.append((command, result))
        
        # Update working directory if cd command
        if command.strip().startswith('cd '):
            if result.success:
                new_dir = command.strip()[3:].strip()
                if new_dir:
                    try:
                        self.context.working_directory = Path(new_dir).resolve()
                    except Exception:
                        pass
    
    def get_context(self) -> CommandContext:
        """
        Get current context.
        
        Returns:
            Current CommandContext
        """
        return self.context
    
    def get_history(self, limit: Optional[int] = None) -> List[str]:
        """
        Get command history.
        
        Args:
            limit: Maximum number of commands to return
            
        Returns:
            List of command strings
        """
        if limit:
            return self.context.history[-limit:]
        return self.context.history.copy()
    
    def get_last_result(self) -> Optional[CommandResult]:
        """
        Get result of last command.
        
        Returns:
            Last CommandResult or None
        """
        if self.command_history:
            return self.command_history[-1][1]
        return None
    
    def set_context_data(self, key: str, value: Any) -> None:
        """
        Store context data.
        
        Args:
            key: Data key
            value: Data value
        """
        self.context_data[key] = value
    
    def get_context_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve context data.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        return self.context_data.get(key, default)
    
    def clear_history(self) -> None:
        """Clear command history."""
        self.context.history.clear()
        self.command_history.clear()
    
    def update_working_directory(self, path: Path) -> None:
        """
        Update working directory.
        
        Args:
            path: New working directory
        """
        self.context.working_directory = path.resolve()
    
    def get_environment_variable(self, name: str) -> Optional[str]:
        """
        Get environment variable.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value or None
        """
        return self.context.environment_variables.get(name)
    
    def set_environment_variable(self, name: str, value: str) -> None:
        """
        Set environment variable.
        
        Args:
            name: Variable name
            value: Variable value
        """
        self.context.environment_variables[name] = value
        os.environ[name] = value



class TerminalInterface:
    """
    Main terminal interface for natural language command processing.
    
    Provides a native terminal interface where developers can interact with
    CodeGenie using natural language commands.
    """
    
    def __init__(
        self,
        tool_executor: Optional[ToolExecutor] = None,
        working_directory: Optional[Path] = None
    ):
        """
        Initialize terminal interface.
        
        Args:
            tool_executor: ToolExecutor instance for command execution
            working_directory: Initial working directory
        """
        self.tool_executor = tool_executor or ToolExecutor()
        self.parser = NaturalLanguageCommandParser()
        self.formatter = TerminalOutputFormatter()
        self.context_manager = TerminalContextManager(working_directory)
        self.running = False
    
    async def process_natural_language_command(
        self,
        command: str,
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """
        Process a natural language command.
        
        Args:
            command: Natural language command
            auto_execute: Whether to execute without confirmation
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Parse command
            parsed = await self.parser.parse_command(command)
            
            # Check if executable command was generated
            if not parsed.executable_command:
                return {
                    'success': False,
                    'error': 'Could not convert command to executable form',
                    'parsed': parsed,
                    'suggestion': 'Try rephrasing the command or use a direct shell command'
                }
            
            # Check if confirmation is needed
            if parsed.requires_confirmation and not auto_execute:
                return {
                    'success': False,
                    'requires_confirmation': True,
                    'parsed': parsed,
                    'message': f"This command requires confirmation: {parsed.executable_command}"
                }
            
            # Execute command
            result = await self.execute_in_terminal(parsed.executable_command)
            
            # Add to history
            self.context_manager.add_to_history(command, result)
            
            return {
                'success': result.success,
                'parsed': parsed,
                'result': result,
                'formatted_output': self.formatter.format_command_result(result)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'formatted_output': self.formatter.format_error(str(e))
            }
    
    async def execute_in_terminal(
        self,
        command: str,
        stream_output: bool = False
    ) -> CommandResult:
        """
        Execute a command in the terminal.
        
        Args:
            command: Command to execute
            stream_output: Whether to stream output in real-time
            
        Returns:
            CommandResult with execution details
        """
        context = self.context_manager.get_context()
        
        if stream_output:
            # Stream output in real-time
            output_lines = []
            
            def output_callback(line: str):
                output_lines.append(line)
                print(line)
            
            result = await self.tool_executor.terminal.stream_output(
                command,
                callback=output_callback,
                cwd=context.working_directory,
                env=context.environment_variables
            )
        else:
            # Execute normally
            result = await self.tool_executor.execute_command(
                command,
                cwd=context.working_directory,
                env=context.environment_variables
            )
        
        return result
    
    async def start_interactive_session(self) -> None:
        """
        Start an interactive terminal session.
        
        Runs a REPL-like interface for continuous command processing.
        """
        self.running = True
        
        print(self.formatter.format_info("CodeGenie Terminal Interface"))
        print(self.formatter.format_info(f"Working directory: {self.context_manager.get_context().working_directory}"))
        print(self.formatter.format_info("Type 'exit' or 'quit' to exit, 'help' for commands\n"))
        
        while self.running:
            try:
                # Get user input
                prompt = f"{self.context_manager.get_context().working_directory} $ "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit']:
                    print(self.formatter.format_info("Goodbye!"))
                    break
                
                if user_input.lower() == 'help':
                    await self._show_help()
                    continue
                
                if user_input.lower() == 'history':
                    await self._show_history()
                    continue
                
                if user_input.lower() == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                    continue
                
                # Process command
                result = await self.process_natural_language_command(user_input)
                
                # Display result
                if result.get('requires_confirmation'):
                    print(self.formatter.format_warning(result['message']))
                    confirm = input("Execute? (y/n): ").strip().lower()
                    if confirm == 'y':
                        # Execute with confirmation
                        result = await self.process_natural_language_command(user_input, auto_execute=True)
                        print(result.get('formatted_output', ''))
                else:
                    print(result.get('formatted_output', ''))
                
            except KeyboardInterrupt:
                print("\n" + self.formatter.format_info("Use 'exit' to quit"))
            except EOFError:
                break
            except Exception as e:
                print(self.formatter.format_error(f"Error: {e}"))
    
    async def _show_help(self) -> None:
        """Show help information."""
        help_text = """
CodeGenie Terminal Interface - Help

You can use natural language commands like:
  - "create a file called test.py"
  - "list all files in the current directory"
  - "show git status"
  - "run tests"
  - "find all Python files"

Or use direct shell commands:
  - ls -la
  - git status
  - python script.py

Special commands:
  - help     : Show this help
  - history  : Show command history
  - clear    : Clear screen
  - exit/quit: Exit terminal
"""
        print(help_text)
    
    async def _show_history(self) -> None:
        """Show command history."""
        history = self.context_manager.get_history(limit=20)
        
        if not history:
            print(self.formatter.format_info("No command history"))
            return
        
        print(self.formatter.format_info("Command History (last 20):"))
        for i, cmd in enumerate(history, 1):
            print(f"  {i}. {cmd}")
    
    def get_context_manager(self) -> TerminalContextManager:
        """
        Get context manager.
        
        Returns:
            TerminalContextManager instance
        """
        return self.context_manager
    
    def get_formatter(self) -> TerminalOutputFormatter:
        """
        Get output formatter.
        
        Returns:
            TerminalOutputFormatter instance
        """
        return self.formatter
    
    def stop(self) -> None:
        """Stop the terminal interface."""
        self.running = False
