"""
Tool Executor for environment interaction and command execution.

This module provides comprehensive tool use capabilities including:
- Terminal command execution with output capture
- Iterative command execution with automatic error correction
- REPL interaction for testing code snippets
- File editing with precise modifications
- Git operations for version control
- Security-integrated command execution with sandboxing
"""

import asyncio
import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Status of command execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class EditType(Enum):
    """Type of file edit operation."""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    CREATE = "create"
    MOVE = "move"


@dataclass
class CommandResult:
    """Result of command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    success: bool
    status: CommandStatus
    analysis: Optional['OutputAnalysis'] = None
    suggested_fixes: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OutputAnalysis:
    """Analysis of command output."""
    has_errors: bool
    error_messages: List[str]
    warnings: List[str]
    error_type: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: float = 0.0


@dataclass
class FileEdit:
    """Represents a file edit operation."""
    file_path: Path
    edit_type: EditType
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    content: str = ""
    reason: str = ""


@dataclass
class REPLResult:
    """Result of REPL execution."""
    code: str
    output: str
    error: Optional[str]
    success: bool
    execution_time: float


@dataclass
class GitOperation:
    """Git operation details."""
    operation: str  # commit, branch, merge, etc.
    parameters: Dict[str, Any]
    result: Optional[str] = None
    success: bool = False


class TerminalExecutor:
    """Executes shell commands with output capture and analysis."""
    
    def __init__(self, default_timeout: int = 30):
        """
        Initialize terminal executor.
        
        Args:
            default_timeout: Default timeout for command execution in seconds
        """
        self.default_timeout = default_timeout
        self.command_history: List[CommandResult] = []
    
    async def run_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> CommandResult:
        """
        Run a shell command and capture output.
        
        Args:
            command: Command to execute
            cwd: Working directory for command execution
            env: Environment variables
            timeout: Command timeout in seconds
            
        Returns:
            CommandResult with execution details
        """
        start_time = datetime.now()
        timeout = timeout or self.default_timeout
        
        try:
            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=exec_env
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration = (datetime.now() - start_time).total_seconds()
                
                result = CommandResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    duration=duration,
                    success=False,
                    status=CommandStatus.TIMEOUT
                )
                self.command_history.append(result)
                return result
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            duration = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = CommandResult(
                command=command,
                exit_code=process.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                duration=duration,
                success=process.returncode == 0,
                status=CommandStatus.SUCCESS if process.returncode == 0 else CommandStatus.FAILURE
            )
            
            self.command_history.append(result)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                success=False,
                status=CommandStatus.FAILURE
            )
            self.command_history.append(result)
            return result
    
    async def stream_output(
        self,
        command: str,
        callback: Callable[[str], None],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Run command and stream output in real-time.
        
        Args:
            command: Command to execute
            callback: Function to call with each line of output
            cwd: Working directory
            env: Environment variables
            
        Returns:
            CommandResult with execution details
        """
        start_time = datetime.now()
        
        try:
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=exec_env
            )
            
            stdout_lines = []
            stderr_lines = []
            
            # Stream stdout
            async def read_stream(stream, lines_list, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line_str = line.decode('utf-8', errors='replace').rstrip()
                    lines_list.append(line_str)
                    callback(line_str)
            
            # Read both streams concurrently
            await asyncio.gather(
                read_stream(process.stdout, stdout_lines),
                read_stream(process.stderr, stderr_lines, True)
            )
            
            await process.wait()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = CommandResult(
                command=command,
                exit_code=process.returncode or 0,
                stdout='\n'.join(stdout_lines),
                stderr='\n'.join(stderr_lines),
                duration=duration,
                success=process.returncode == 0,
                status=CommandStatus.SUCCESS if process.returncode == 0 else CommandStatus.FAILURE
            )
            
            self.command_history.append(result)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                success=False,
                status=CommandStatus.FAILURE
            )
            self.command_history.append(result)
            return result


class ResultAnalyzer:
    """Analyzes command output and errors to provide insights and fixes."""
    
    def __init__(self):
        """Initialize result analyzer."""
        self.error_patterns = self._load_error_patterns()
    
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common error patterns and their fixes."""
        return {
            'permission_denied': {
                'pattern': r'permission denied|access denied',
                'fix': 'Try running with sudo or check file permissions',
                'type': 'permission'
            },
            'command_not_found': {
                'pattern': r'command not found|not recognized',
                'fix': 'Install the required package or check PATH',
                'type': 'missing_command'
            },
            'syntax_error': {
                'pattern': r'syntax error|syntaxerror',
                'fix': 'Check code syntax and fix errors',
                'type': 'syntax'
            },
            'import_error': {
                'pattern': r'importerror|modulenotfounderror|no module named',
                'fix': 'Install missing dependencies or check import paths',
                'type': 'import'
            },
            'file_not_found': {
                'pattern': r'no such file or directory|file not found',
                'fix': 'Check file path and ensure file exists',
                'type': 'file_missing'
            },
        }
    
    def analyze_output(self, result: CommandResult) -> OutputAnalysis:
        """
        Analyze command output for errors and warnings.
        
        Args:
            result: Command execution result
            
        Returns:
            OutputAnalysis with detected issues and suggestions
        """
        combined_output = f"{result.stdout}\n{result.stderr}".lower()
        
        error_messages = []
        warnings = []
        error_type = None
        suggested_fix = None
        
        # Check for errors
        has_errors = result.exit_code != 0 or 'error' in combined_output
        
        # Extract error messages
        for line in result.stderr.split('\n'):
            if 'error' in line.lower():
                error_messages.append(line.strip())
            elif 'warning' in line.lower():
                warnings.append(line.strip())
        
        # Match error patterns
        for pattern_name, pattern_info in self.error_patterns.items():
            if re.search(pattern_info['pattern'], combined_output, re.IGNORECASE):
                error_type = pattern_info['type']
                suggested_fix = pattern_info['fix']
                break
        
        confidence = 0.8 if error_type else 0.3
        
        return OutputAnalysis(
            has_errors=has_errors,
            error_messages=error_messages,
            warnings=warnings,
            error_type=error_type,
            suggested_fix=suggested_fix,
            confidence=confidence
        )


class REPLManager:
    """Manages REPL sessions for interactive code testing."""
    
    def __init__(self):
        """Initialize REPL manager."""
        self.active_sessions: Dict[str, Any] = {}
    
    async def start_repl(self, language: str) -> str:
        """
        Start a REPL session for the specified language.
        
        Args:
            language: Programming language (python, node, ruby, etc.)
            
        Returns:
            Session ID
        """
        session_id = f"{language}_{datetime.now().timestamp()}"
        
        # Language-specific REPL commands
        repl_commands = {
            'python': 'python3 -i',
            'node': 'node',
            'ruby': 'irb',
            'javascript': 'node'
        }
        
        command = repl_commands.get(language.lower(), 'python3 -i')
        
        # Create REPL process
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.active_sessions[session_id] = {
            'language': language,
            'process': process,
            'history': []
        }
        
        return session_id
    
    async def execute_in_repl(
        self,
        session_id: str,
        code: str,
        timeout: int = 10
    ) -> REPLResult:
        """
        Execute code in an active REPL session.
        
        Args:
            session_id: REPL session ID
            code: Code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            REPLResult with execution output
        """
        if session_id not in self.active_sessions:
            return REPLResult(
                code=code,
                output="",
                error="Session not found",
                success=False,
                execution_time=0.0
            )
        
        session = self.active_sessions[session_id]
        process = session['process']
        start_time = datetime.now()
        
        try:
            # Send code to REPL
            process.stdin.write(f"{code}\n".encode())
            await process.stdin.drain()
            
            # Read output with timeout
            output_lines = []
            try:
                while True:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=0.1
                    )
                    if not line:
                        break
                    output_lines.append(line.decode('utf-8', errors='replace'))
            except asyncio.TimeoutError:
                pass
            
            duration = (datetime.now() - start_time).total_seconds()
            output = ''.join(output_lines)
            
            result = REPLResult(
                code=code,
                output=output,
                error=None,
                success=True,
                execution_time=duration
            )
            
            session['history'].append(result)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return REPLResult(
                code=code,
                output="",
                error=str(e),
                success=False,
                execution_time=duration
            )
    
    async def close_repl(self, session_id: str) -> None:
        """
        Close a REPL session.
        
        Args:
            session_id: Session ID to close
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            process = session['process']
            process.kill()
            await process.wait()
            del self.active_sessions[session_id]


class FileEditor:
    """Handles precise file modifications."""
    
    def __init__(self):
        """Initialize file editor."""
        self.edit_history: List[FileEdit] = []
    
    async def edit_file(self, edit: FileEdit) -> bool:
        """
        Apply a file edit operation.
        
        Args:
            edit: FileEdit operation to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = edit.file_path
            
            if edit.edit_type == EditType.CREATE:
                # Create new file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(edit.content)
                self.edit_history.append(edit)
                return True
            
            elif edit.edit_type == EditType.MOVE:
                # Move/rename file
                target_path = Path(edit.content)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.rename(target_path)
                self.edit_history.append(edit)
                return True
            
            # For other operations, read existing content
            if not file_path.exists():
                return False
            
            lines = file_path.read_text().splitlines(keepends=True)
            
            if edit.edit_type == EditType.INSERT:
                # Insert content at specified line
                insert_line = edit.line_start or len(lines)
                lines.insert(insert_line, edit.content + '\n')
            
            elif edit.edit_type == EditType.DELETE:
                # Delete lines
                start = edit.line_start or 0
                end = edit.line_end or len(lines)
                del lines[start:end]
            
            elif edit.edit_type == EditType.REPLACE:
                # Replace lines
                start = edit.line_start or 0
                end = edit.line_end or start + 1
                lines[start:end] = [edit.content + '\n']
            
            # Write modified content
            file_path.write_text(''.join(lines))
            self.edit_history.append(edit)
            return True
            
        except Exception as e:
            print(f"Error editing file: {e}")
            return False
    
    async def edit_multiple_files(self, edits: List[FileEdit]) -> Dict[Path, bool]:
        """
        Apply multiple file edits.
        
        Args:
            edits: List of FileEdit operations
            
        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        for edit in edits:
            results[edit.file_path] = await self.edit_file(edit)
        return results


class GitIntegration:
    """Handles Git version control operations."""
    
    def __init__(self, terminal_executor: TerminalExecutor):
        """
        Initialize Git integration.
        
        Args:
            terminal_executor: Terminal executor for running git commands
        """
        self.terminal = terminal_executor
        self.operation_history: List[GitOperation] = []
    
    async def create_commit(
        self,
        message: str,
        files: Optional[List[Path]] = None,
        cwd: Optional[Path] = None
    ) -> GitOperation:
        """
        Create a git commit.
        
        Args:
            message: Commit message
            files: Specific files to commit (None for all staged)
            cwd: Repository directory
            
        Returns:
            GitOperation with result
        """
        operation = GitOperation(
            operation='commit',
            parameters={'message': message, 'files': files}
        )
        
        try:
            # Stage files if specified
            if files:
                for file in files:
                    result = await self.terminal.run_command(
                        f"git add {file}",
                        cwd=cwd
                    )
                    if not result.success:
                        operation.result = f"Failed to stage {file}"
                        operation.success = False
                        self.operation_history.append(operation)
                        return operation
            
            # Create commit
            result = await self.terminal.run_command(
                f'git commit -m "{message}"',
                cwd=cwd
            )
            
            operation.result = result.stdout
            operation.success = result.success
            self.operation_history.append(operation)
            return operation
            
        except Exception as e:
            operation.result = str(e)
            operation.success = False
            self.operation_history.append(operation)
            return operation
    
    async def create_branch(
        self,
        branch_name: str,
        cwd: Optional[Path] = None
    ) -> GitOperation:
        """
        Create a new git branch.
        
        Args:
            branch_name: Name of the branch
            cwd: Repository directory
            
        Returns:
            GitOperation with result
        """
        operation = GitOperation(
            operation='branch',
            parameters={'branch_name': branch_name}
        )
        
        try:
            result = await self.terminal.run_command(
                f"git checkout -b {branch_name}",
                cwd=cwd
            )
            
            operation.result = result.stdout
            operation.success = result.success
            self.operation_history.append(operation)
            return operation
            
        except Exception as e:
            operation.result = str(e)
            operation.success = False
            self.operation_history.append(operation)
            return operation
    
    async def get_status(self, cwd: Optional[Path] = None) -> CommandResult:
        """
        Get git status.
        
        Args:
            cwd: Repository directory
            
        Returns:
            CommandResult with status output
        """
        return await self.terminal.run_command("git status", cwd=cwd)
    
    async def get_diff(
        self,
        file_path: Optional[Path] = None,
        cwd: Optional[Path] = None
    ) -> CommandResult:
        """
        Get git diff.
        
        Args:
            file_path: Specific file to diff (None for all)
            cwd: Repository directory
            
        Returns:
            CommandResult with diff output
        """
        command = f"git diff {file_path}" if file_path else "git diff"
        return await self.terminal.run_command(command, cwd=cwd)


class ToolExecutor:
    """
    Main tool executor that coordinates all environment interaction capabilities.
    """
    
    def __init__(self):
        """Initialize tool executor with all components."""
        self.terminal = TerminalExecutor()
        self.result_analyzer = ResultAnalyzer()
        self.repl_manager = REPLManager()
        self.file_editor = FileEditor()
        self.git = GitIntegration(self.terminal)
    
    async def execute_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> CommandResult:
        """
        Execute a command and analyze results.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Command timeout
            
        Returns:
            CommandResult with analysis
        """
        result = await self.terminal.run_command(command, cwd, env, timeout)
        result.analysis = self.result_analyzer.analyze_output(result)
        
        # Generate suggested fixes if there are errors
        if result.analysis.suggested_fix:
            result.suggested_fixes.append(result.analysis.suggested_fix)
        
        return result
    
    async def execute_with_retry(
        self,
        command: str,
        max_retries: int = 3,
        cwd: Optional[Path] = None
    ) -> CommandResult:
        """
        Execute command with automatic retry on failure.
        
        Args:
            command: Command to execute
            max_retries: Maximum number of retry attempts
            cwd: Working directory
            
        Returns:
            CommandResult from successful execution or final attempt
        """
        for attempt in range(max_retries):
            result = await self.execute_command(command, cwd=cwd)
            
            if result.success:
                return result
            
            # Try to fix and retry
            if result.analysis and result.analysis.suggested_fix:
                # Apply suggested fix (simplified - would need more logic)
                continue
            
            if attempt == max_retries - 1:
                return result
        
        return result
    
    async def interact_with_repl(
        self,
        code: str,
        language: str = 'python'
    ) -> REPLResult:
        """
        Execute code in a REPL environment.
        
        Args:
            code: Code to execute
            language: Programming language
            
        Returns:
            REPLResult with execution output
        """
        session_id = await self.repl_manager.start_repl(language)
        result = await self.repl_manager.execute_in_repl(session_id, code)
        await self.repl_manager.close_repl(session_id)
        return result
    
    async def edit_file(self, edit: FileEdit) -> bool:
        """
        Edit a file.
        
        Args:
            edit: FileEdit operation
            
        Returns:
            True if successful
        """
        return await self.file_editor.edit_file(edit)
    
    async def edit_multiple_files(self, edits: List[FileEdit]) -> Dict[Path, bool]:
        """
        Edit multiple files.
        
        Args:
            edits: List of FileEdit operations
            
        Returns:
            Dictionary of results
        """
        return await self.file_editor.edit_multiple_files(edits)
    
    async def create_commit(
        self,
        message: str,
        files: Optional[List[Path]] = None,
        cwd: Optional[Path] = None
    ) -> GitOperation:
        """
        Create a git commit.
        
        Args:
            message: Commit message
            files: Files to commit
            cwd: Repository directory
            
        Returns:
            GitOperation with result
        """
        return await self.git.create_commit(message, files, cwd)



class SecureToolExecutor(ToolExecutor):
    """
    Security-enhanced tool executor with sandboxing and access control.
    
    Integrates with SecurityFramework and AgentIsolationManager to provide
    secure command execution with proper authorization and audit logging.
    """
    
    def __init__(self, security_framework=None, isolation_manager=None):
        """
        Initialize secure tool executor.
        
        Args:
            security_framework: SecurityFramework instance for access control
            isolation_manager: AgentIsolationManager for sandboxed execution
        """
        super().__init__()
        self.security_framework = security_framework
        self.isolation_manager = isolation_manager
        self.blocked_commands = self._load_blocked_commands()
        self.command_validators = self._load_command_validators()
    
    def _load_blocked_commands(self) -> List[str]:
        """Load list of blocked/dangerous commands."""
        return [
            'rm -rf /',
            'dd if=/dev/zero',
            'mkfs',
            'format',
            ':(){ :|:& };:',  # Fork bomb
            'chmod -R 777 /',
            'chown -R',
            'sudo rm',
        ]
    
    def _load_command_validators(self) -> Dict[str, Callable]:
        """Load command validation functions."""
        return {
            'file_operations': self._validate_file_operation,
            'network_operations': self._validate_network_operation,
            'system_operations': self._validate_system_operation,
        }
    
    def _validate_file_operation(self, command: str, context) -> Tuple[bool, Optional[str]]:
        """Validate file operation commands."""
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'rm\s+-rf\s+\*',
            r'chmod\s+-R\s+777',
            r'chown\s+-R\s+root',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Dangerous file operation detected: {pattern}"
        
        return True, None
    
    def _validate_network_operation(self, command: str, context) -> Tuple[bool, Optional[str]]:
        """Validate network operation commands."""
        # Check if network access is allowed
        if hasattr(context, 'network_access') and not context.network_access:
            network_commands = ['curl', 'wget', 'nc', 'netcat', 'ssh', 'scp', 'ftp']
            for cmd in network_commands:
                if cmd in command.lower():
                    return False, f"Network access not allowed: {cmd}"
        
        return True, None
    
    def _validate_system_operation(self, command: str, context) -> Tuple[bool, Optional[str]]:
        """Validate system-level operations."""
        system_commands = ['reboot', 'shutdown', 'halt', 'poweroff', 'init']
        for cmd in system_commands:
            if cmd in command.lower():
                return False, f"System operation not allowed: {cmd}"
        
        return True, None
    
    async def execute_command_secure(
        self,
        command: str,
        security_context,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        sandbox_id: Optional[str] = None
    ) -> CommandResult:
        """
        Execute command with security checks and audit logging.
        
        Args:
            command: Command to execute
            security_context: SecurityContext for authorization
            cwd: Working directory
            env: Environment variables
            timeout: Command timeout
            sandbox_id: Optional sandbox ID for isolated execution
            
        Returns:
            CommandResult with execution details
            
        Raises:
            PermissionError: If command is not allowed
            ValueError: If command validation fails
        """
        # Validate security context
        if self.security_framework:
            context = self.security_framework.access_control.validate_context(
                security_context.session_id if hasattr(security_context, 'session_id') else security_context
            )
            if not context:
                raise PermissionError("Invalid or expired security context")
            
            # Check execute permission
            if not self.security_framework.access_control.check_permission(
                context, 'execute', 'command'
            ):
                self.security_framework.audit_logger.log_event(
                    'command_execution_denied',
                    context.user_id,
                    'command',
                    command,
                    'permission_denied',
                    self.security_framework.audit_logger.ThreatLevel.MEDIUM,
                    agent_id=context.agent_id
                )
                raise PermissionError("Execute permission denied")
        
        # Validate command safety
        for blocked in self.blocked_commands:
            if blocked in command:
                if self.security_framework:
                    self.security_framework.audit_logger.log_event(
                        'blocked_command_attempt',
                        context.user_id if context else 'unknown',
                        'command',
                        command,
                        'blocked',
                        self.security_framework.audit_logger.ThreatLevel.HIGH,
                        details={'blocked_pattern': blocked}
                    )
                raise ValueError(f"Blocked command detected: {blocked}")
        
        # Run validators
        for validator_name, validator_func in self.command_validators.items():
            is_valid, error_msg = validator_func(command, context if context else None)
            if not is_valid:
                if self.security_framework:
                    self.security_framework.audit_logger.log_event(
                        'command_validation_failed',
                        context.user_id if context else 'unknown',
                        'command',
                        command,
                        'validation_failed',
                        self.security_framework.audit_logger.ThreatLevel.MEDIUM,
                        details={'validator': validator_name, 'error': error_msg}
                    )
                raise ValueError(f"Command validation failed: {error_msg}")
        
        # Log command execution start
        if self.security_framework:
            self.security_framework.audit_logger.log_event(
                'command_execution_start',
                context.user_id if context else 'unknown',
                'command',
                command,
                'started',
                self.security_framework.audit_logger.ThreatLevel.INFO,
                agent_id=context.agent_id if context else None,
                details={'cwd': str(cwd) if cwd else None, 'sandbox_id': sandbox_id}
            )
        
        try:
            # Execute in sandbox if available
            if sandbox_id and self.isolation_manager:
                result = await self._execute_in_sandbox(
                    sandbox_id, command, cwd, env, timeout
                )
            else:
                # Execute normally
                result = await self.execute_command(command, cwd, env, timeout)
            
            # Log successful execution
            if self.security_framework:
                self.security_framework.audit_logger.log_event(
                    'command_execution_complete',
                    context.user_id if context else 'unknown',
                    'command',
                    command,
                    'success' if result.success else 'failed',
                    self.security_framework.audit_logger.ThreatLevel.INFO,
                    agent_id=context.agent_id if context else None,
                    details={
                        'exit_code': result.exit_code,
                        'duration': result.duration,
                        'sandbox_id': sandbox_id
                    }
                )
            
            return result
            
        except Exception as e:
            # Log execution error
            if self.security_framework:
                self.security_framework.audit_logger.log_event(
                    'command_execution_error',
                    context.user_id if context else 'unknown',
                    'command',
                    command,
                    'error',
                    self.security_framework.audit_logger.ThreatLevel.MEDIUM,
                    agent_id=context.agent_id if context else None,
                    details={'error': str(e), 'sandbox_id': sandbox_id}
                )
            raise
    
    async def _execute_in_sandbox(
        self,
        sandbox_id: str,
        command: str,
        cwd: Optional[Path],
        env: Optional[Dict[str, str]],
        timeout: Optional[int]
    ) -> CommandResult:
        """Execute command in isolated sandbox."""
        if not self.isolation_manager:
            raise RuntimeError("Isolation manager not available")
        
        # Create execution code that runs the command
        execution_code = f"""
import subprocess
import sys

try:
    result = subprocess.run(
        {repr(command)},
        shell=True,
        capture_output=True,
        text=True,
        timeout={timeout or 30},
        cwd={repr(str(cwd)) if cwd else None}
    )
    print(f"EXIT_CODE:{{result.returncode}}")
    print(f"STDOUT:{{result.stdout}}")
    print(f"STDERR:{{result.stderr}}")
except Exception as e:
    print(f"ERROR:{{str(e)}}")
    sys.exit(1)
"""
        
        # Execute in sandbox
        sandbox_result = await self.isolation_manager.execute_in_sandbox(
            sandbox_id,
            'execute_code',
            execution_code,
            timeout
        )
        
        # Parse result
        if sandbox_result['success']:
            output = sandbox_result['stdout']
            exit_code = 0
            stdout = ""
            stderr = ""
            
            # Parse output
            for line in output.split('\n'):
                if line.startswith('EXIT_CODE:'):
                    exit_code = int(line.split(':', 1)[1])
                elif line.startswith('STDOUT:'):
                    stdout = line.split(':', 1)[1]
                elif line.startswith('STDERR:'):
                    stderr = line.split(':', 1)[1]
            
            return CommandResult(
                command=command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=sandbox_result['execution_time'],
                success=exit_code == 0,
                status=CommandStatus.SUCCESS if exit_code == 0 else CommandStatus.FAILURE
            )
        else:
            return CommandResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr=sandbox_result['stderr'],
                duration=sandbox_result['execution_time'],
                success=False,
                status=CommandStatus.FAILURE
            )
    
    async def edit_file_secure(
        self,
        edit: FileEdit,
        security_context,
        sandbox_id: Optional[str] = None
    ) -> bool:
        """
        Edit file with security checks.
        
        Args:
            edit: FileEdit operation
            security_context: SecurityContext for authorization
            sandbox_id: Optional sandbox ID
            
        Returns:
            True if successful
        """
        if self.security_framework:
            context = self.security_framework.access_control.validate_context(
                security_context.session_id if hasattr(security_context, 'session_id') else security_context
            )
            if not context:
                raise PermissionError("Invalid or expired security context")
            
            # Check write permission
            if not self.security_framework.access_control.check_permission(
                context, 'write', str(edit.file_path)
            ):
                self.security_framework.audit_logger.log_event(
                    'file_edit_denied',
                    context.user_id,
                    str(edit.file_path),
                    edit.edit_type.value,
                    'permission_denied',
                    self.security_framework.audit_logger.ThreatLevel.MEDIUM,
                    agent_id=context.agent_id
                )
                raise PermissionError(f"Write permission denied for {edit.file_path}")
            
            # Log file edit
            self.security_framework.audit_logger.log_event(
                'file_edit',
                context.user_id,
                str(edit.file_path),
                edit.edit_type.value,
                'started',
                self.security_framework.audit_logger.ThreatLevel.INFO,
                agent_id=context.agent_id,
                details={'reason': edit.reason}
            )
        
        try:
            # Perform edit
            result = await self.edit_file(edit)
            
            # Log success
            if self.security_framework:
                self.security_framework.audit_logger.log_event(
                    'file_edit_complete',
                    context.user_id if context else 'unknown',
                    str(edit.file_path),
                    edit.edit_type.value,
                    'success' if result else 'failed',
                    self.security_framework.audit_logger.ThreatLevel.INFO,
                    agent_id=context.agent_id if context else None
                )
            
            return result
            
        except Exception as e:
            # Log error
            if self.security_framework:
                self.security_framework.audit_logger.log_event(
                    'file_edit_error',
                    context.user_id if context else 'unknown',
                    str(edit.file_path),
                    edit.edit_type.value,
                    'error',
                    self.security_framework.audit_logger.ThreatLevel.MEDIUM,
                    agent_id=context.agent_id if context else None,
                    details={'error': str(e)}
                )
            raise
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security status of tool executor."""
        status = {
            'security_enabled': self.security_framework is not None,
            'isolation_enabled': self.isolation_manager is not None,
            'blocked_commands_count': len(self.blocked_commands),
            'validators_count': len(self.command_validators),
        }
        
        if self.security_framework:
            status['security_framework_status'] = self.security_framework.get_security_status()
        
        if self.isolation_manager:
            status['active_sandboxes'] = len(self.isolation_manager.sandboxes)
            status['sandboxes'] = self.isolation_manager.list_sandboxes()
        
        return status
