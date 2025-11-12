"""
Command Executor for safe command execution with approval workflows.

This module provides intelligent command execution with:
- Command risk classification (safe, risky, dangerous)
- User approval workflows for risky operations
- Streaming output support
- Error recovery with suggestions
- Command history and audit logging
"""

import asyncio
import subprocess
import re
import shlex
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable, AsyncIterator, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CommandRiskLevel(Enum):
    """Risk level classification for commands."""
    SAFE = "safe"
    RISKY = "risky"
    DANGEROUS = "dangerous"


class CommandStatus(Enum):
    """Status of command execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class CommandResult:
    """Result of command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: timedelta
    success: bool
    status: CommandStatus
    risk_level: CommandRiskLevel
    timestamp: datetime = field(default_factory=datetime.now)
    error_analysis: Optional['ErrorAnalysis'] = None
    recovery_suggestions: List[str] = field(default_factory=list)


@dataclass
class ErrorAnalysis:
    """Analysis of command errors."""
    error_type: str
    error_messages: List[str]
    is_recoverable: bool
    suggested_fixes: List[str]
    confidence: float


@dataclass
class RecoveryAction:
    """Suggested recovery action for command failure."""
    action_type: str  # retry, fix_command, install_dependency, etc.
    description: str
    command: Optional[str] = None
    auto_applicable: bool = False


class CommandClassifier:
    """Classifies commands by risk level."""
    
    def __init__(self):
        """Initialize command classifier with patterns."""
        self.safe_commands = {
            # Read-only operations
            'ls', 'cat', 'head', 'tail', 'less', 'more', 'grep', 'find',
            'pwd', 'whoami', 'date', 'echo', 'which', 'whereis',
            # Git read operations
            'git status', 'git log', 'git diff', 'git show', 'git branch',
            # Package info
            'pip list', 'pip show', 'npm list', 'npm view',
            # System info
            'uname', 'hostname', 'df', 'du', 'ps', 'top', 'free',
        }
        
        self.risky_patterns = [
            # Write operations
            r'^(mkdir|touch|cp|mv)\s',
            r'^(echo|cat)\s.*>\s',  # Redirects
            # Package management
            r'^(pip|npm|yarn|cargo)\s+(install|add|update)',
            # Git write operations
            r'^git\s+(commit|push|pull|merge|rebase|checkout)',
            # Build operations
            r'^(make|cmake|cargo build|npm run|yarn)',
        ]
        
        self.dangerous_patterns = [
            # Destructive operations
            r'^rm\s+-rf',
            r'^rm\s+.*\*',
            r'^dd\s+',
            r'^mkfs',
            r'^format',
            # System operations
            r'^(sudo|su)\s',
            r'^(reboot|shutdown|halt|poweroff)',
            r'^(chmod|chown)\s+-R',
            # Network operations that could be dangerous
            r'^curl.*\|\s*(bash|sh)',
            r'^wget.*\|\s*(bash|sh)',
            # Fork bomb and similar
            r':\(\)\{.*\|\:',
        ]
    
    def classify(self, command: str) -> CommandRiskLevel:
        """
        Classify command by risk level.
        
        Args:
            command: Command to classify
            
        Returns:
            CommandRiskLevel indicating safety
        """
        command_lower = command.lower().strip()
        
        # Check dangerous patterns first
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command_lower):
                return CommandRiskLevel.DANGEROUS
        
        # Check risky patterns
        for pattern in self.risky_patterns:
            if re.search(pattern, command_lower):
                return CommandRiskLevel.RISKY
        
        # Check if it's a known safe command
        command_base = command_lower.split()[0] if command_lower else ""
        if command_base in self.safe_commands or command_lower in self.safe_commands:
            return CommandRiskLevel.SAFE
        
        # Default to risky for unknown commands
        return CommandRiskLevel.RISKY
    
    def is_safe(self, command: str) -> bool:
        """Check if command is safe."""
        return self.classify(command) == CommandRiskLevel.SAFE
    
    def is_dangerous(self, command: str) -> bool:
        """Check if command is dangerous."""
        return self.classify(command) == CommandRiskLevel.DANGEROUS


class ErrorRecoverySystem:
    """Analyzes errors and suggests recovery actions."""
    
    def __init__(self):
        """Initialize error recovery system."""
        self.error_patterns = self._load_error_patterns()
        self.recovery_history: List[Dict[str, Any]] = []
    
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common error patterns and recovery strategies."""
        return {
            'command_not_found': {
                'pattern': r'command not found|not recognized as',
                'type': 'missing_command',
                'recoverable': True,
                'fixes': [
                    'Install the required package',
                    'Check if the command is in your PATH',
                    'Verify the command name spelling'
                ]
            },
            'permission_denied': {
                'pattern': r'permission denied|access denied|operation not permitted',
                'type': 'permission',
                'recoverable': True,
                'fixes': [
                    'Run with appropriate permissions',
                    'Check file/directory permissions',
                    'Ensure you have write access to the target'
                ]
            },
            'file_not_found': {
                'pattern': r'no such file or directory|cannot find',
                'type': 'file_missing',
                'recoverable': True,
                'fixes': [
                    'Check the file path is correct',
                    'Ensure the file exists',
                    'Create the required directory structure'
                ]
            },
            'syntax_error': {
                'pattern': r'syntax error|syntaxerror',
                'type': 'syntax',
                'recoverable': True,
                'fixes': [
                    'Check command syntax',
                    'Review command documentation',
                    'Verify all required arguments are provided'
                ]
            },
            'module_not_found': {
                'pattern': r'modulenotfounderror|no module named|cannot import',
                'type': 'import',
                'recoverable': True,
                'fixes': [
                    'Install missing Python package',
                    'Check virtual environment is activated',
                    'Verify package name and version'
                ]
            },
            'network_error': {
                'pattern': r'connection refused|network unreachable|timeout',
                'type': 'network',
                'recoverable': True,
                'fixes': [
                    'Check network connectivity',
                    'Verify the service is running',
                    'Check firewall settings'
                ]
            },
            'disk_full': {
                'pattern': r'no space left|disk full',
                'type': 'disk_space',
                'recoverable': False,
                'fixes': [
                    'Free up disk space',
                    'Remove unnecessary files',
                    'Check disk usage with df -h'
                ]
            },
        }
    
    def analyze_error(self, result: CommandResult) -> ErrorAnalysis:
        """
        Analyze command error and suggest fixes.
        
        Args:
            result: Command execution result
            
        Returns:
            ErrorAnalysis with recovery suggestions
        """
        combined_output = f"{result.stdout}\n{result.stderr}".lower()
        
        error_messages = []
        error_type = "unknown"
        is_recoverable = False
        suggested_fixes = []
        confidence = 0.0
        
        # Extract error messages from stderr
        for line in result.stderr.split('\n'):
            if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
                error_messages.append(line.strip())
        
        # Match error patterns
        for pattern_name, pattern_info in self.error_patterns.items():
            if re.search(pattern_info['pattern'], combined_output, re.IGNORECASE):
                error_type = pattern_info['type']
                is_recoverable = pattern_info['recoverable']
                suggested_fixes = pattern_info['fixes']
                confidence = 0.85
                break
        
        # If no pattern matched but command failed, provide generic suggestions
        if not suggested_fixes and not result.success:
            suggested_fixes = [
                'Review the error message above',
                'Check command syntax and arguments',
                'Verify all prerequisites are met'
            ]
            confidence = 0.3
        
        return ErrorAnalysis(
            error_type=error_type,
            error_messages=error_messages,
            is_recoverable=is_recoverable,
            suggested_fixes=suggested_fixes,
            confidence=confidence
        )
    
    def suggest_recovery(self, result: CommandResult, analysis: ErrorAnalysis) -> List[RecoveryAction]:
        """
        Suggest recovery actions based on error analysis.
        
        Args:
            result: Command execution result
            analysis: Error analysis
            
        Returns:
            List of recovery actions
        """
        actions = []
        
        if analysis.error_type == 'missing_command':
            # Extract command name
            match = re.search(r'(\w+).*command not found', result.stderr, re.IGNORECASE)
            if match:
                cmd_name = match.group(1)
                actions.append(RecoveryAction(
                    action_type='install_dependency',
                    description=f'Install {cmd_name}',
                    command=f'# Install {cmd_name} using your package manager',
                    auto_applicable=False
                ))
        
        elif analysis.error_type == 'import':
            # Extract module name
            match = re.search(r'no module named [\'"]?(\w+)[\'"]?', result.stderr, re.IGNORECASE)
            if match:
                module_name = match.group(1)
                actions.append(RecoveryAction(
                    action_type='install_dependency',
                    description=f'Install Python package {module_name}',
                    command=f'pip install {module_name}',
                    auto_applicable=True
                ))
        
        elif analysis.error_type == 'permission':
            actions.append(RecoveryAction(
                action_type='fix_permissions',
                description='Fix file permissions',
                command=None,
                auto_applicable=False
            ))
        
        elif analysis.error_type == 'file_missing':
            # Extract file path if possible
            match = re.search(r'no such file or directory.*[\'"]([^\'"]+)[\'"]', result.stderr, re.IGNORECASE)
            if match:
                file_path = match.group(1)
                actions.append(RecoveryAction(
                    action_type='create_file',
                    description=f'Create missing file or directory: {file_path}',
                    command=None,
                    auto_applicable=False
                ))
        
        # Always add retry option if recoverable
        if analysis.is_recoverable:
            actions.append(RecoveryAction(
                action_type='retry',
                description='Retry the command after fixing the issue',
                command=result.command,
                auto_applicable=False
            ))
        
        return actions
    
    def learn_from_recovery(self, original_error: str, recovery_action: str, success: bool):
        """
        Learn from recovery attempts to improve future suggestions.
        
        Args:
            original_error: Original error message
            recovery_action: Action taken to recover
            success: Whether recovery was successful
        """
        self.recovery_history.append({
            'error': original_error,
            'action': recovery_action,
            'success': success,
            'timestamp': datetime.now()
        })


class ApprovalManager:
    """Manages user approval for risky commands."""
    
    def __init__(self):
        """Initialize approval manager."""
        self.approval_preferences: Dict[str, bool] = {}
        self.auto_approve_safe = True
    
    async def request_approval(
        self,
        command: str,
        risk_level: CommandRiskLevel,
        callback: Optional[Callable[[str, CommandRiskLevel], bool]] = None
    ) -> bool:
        """
        Request user approval for command execution.
        
        Args:
            command: Command to execute
            risk_level: Risk level of the command
            callback: Optional callback function for approval
            
        Returns:
            True if approved, False otherwise
        """
        # Auto-approve safe commands if enabled
        if risk_level == CommandRiskLevel.SAFE and self.auto_approve_safe:
            return True
        
        # Check if we have a stored preference for this command
        if command in self.approval_preferences:
            return self.approval_preferences[command]
        
        # Use callback if provided
        if callback:
            approved = callback(command, risk_level)
            return approved
        
        # Default: block dangerous, allow others
        if risk_level == CommandRiskLevel.DANGEROUS:
            logger.warning(f"Dangerous command blocked: {command}")
            return False
        
        return True
    
    def remember_preference(self, command: str, approved: bool):
        """
        Remember approval preference for a command.
        
        Args:
            command: Command
            approved: Whether it was approved
        """
        self.approval_preferences[command] = approved
    
    def set_auto_approve_safe(self, enabled: bool):
        """
        Enable or disable auto-approval of safe commands.
        
        Args:
            enabled: Whether to auto-approve safe commands
        """
        self.auto_approve_safe = enabled


class CommandExecutor:
    """
    Main command executor with classification, approval, and error recovery.
    """
    
    def __init__(
        self,
        default_timeout: int = 30,
        approval_callback: Optional[Callable[[str, CommandRiskLevel], bool]] = None
    ):
        """
        Initialize command executor.
        
        Args:
            default_timeout: Default timeout for commands in seconds
            approval_callback: Optional callback for approval requests
        """
        self.default_timeout = default_timeout
        self.approval_callback = approval_callback
        
        self.classifier = CommandClassifier()
        self.error_recovery = ErrorRecoverySystem()
        self.approval_manager = ApprovalManager()
        
        self.command_history: List[CommandResult] = []
    
    def classify_command(self, command: str) -> CommandRiskLevel:
        """
        Classify command by risk level.
        
        Args:
            command: Command to classify
            
        Returns:
            CommandRiskLevel
        """
        return self.classifier.classify(command)
    
    async def execute_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        require_approval: bool = True
    ) -> CommandResult:
        """
        Execute a command with classification and approval.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Command timeout in seconds
            require_approval: Whether to require approval for risky commands
            
        Returns:
            CommandResult with execution details
        """
        start_time = datetime.now()
        timeout = timeout or self.default_timeout
        
        # Classify command
        risk_level = self.classifier.classify(command)
        logger.info(f"Command classified as {risk_level.value}: {command}")
        
        # Request approval if needed
        if require_approval:
            approved = await self.approval_manager.request_approval(
                command,
                risk_level,
                self.approval_callback
            )
            
            if not approved:
                logger.warning(f"Command execution denied: {command}")
                return CommandResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr="Command execution denied by user or policy",
                    duration=datetime.now() - start_time,
                    success=False,
                    status=CommandStatus.BLOCKED,
                    risk_level=risk_level
                )
        
        # Execute command
        try:
            # Prepare environment
            exec_env = os.environ.copy() if env is None else {**os.environ, **env}
            
            # Execute
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=exec_env
            )
            
            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                
                result = CommandResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    duration=datetime.now() - start_time,
                    success=False,
                    status=CommandStatus.TIMEOUT,
                    risk_level=risk_level
                )
                self.command_history.append(result)
                return result
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Create result
            result = CommandResult(
                command=command,
                exit_code=process.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                duration=datetime.now() - start_time,
                success=process.returncode == 0,
                status=CommandStatus.SUCCESS if process.returncode == 0 else CommandStatus.FAILURE,
                risk_level=risk_level
            )
            
            # Analyze errors if command failed
            if not result.success:
                result.error_analysis = self.error_recovery.analyze_error(result)
                recovery_actions = self.error_recovery.suggest_recovery(result, result.error_analysis)
                result.recovery_suggestions = [
                    f"{action.action_type}: {action.description}"
                    for action in recovery_actions
                ]
            
            self.command_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=datetime.now() - start_time,
                success=False,
                status=CommandStatus.FAILURE,
                risk_level=risk_level
            )
            self.command_history.append(result)
            return result
    
    async def execute_with_streaming(
        self,
        command: str,
        output_callback: Callable[[str], None],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        require_approval: bool = True
    ) -> CommandResult:
        """
        Execute command with streaming output.
        
        Args:
            command: Command to execute
            output_callback: Callback for each line of output
            cwd: Working directory
            env: Environment variables
            require_approval: Whether to require approval
            
        Returns:
            CommandResult with execution details
        """
        start_time = datetime.now()
        
        # Classify and get approval
        risk_level = self.classifier.classify(command)
        
        if require_approval:
            approved = await self.approval_manager.request_approval(
                command,
                risk_level,
                self.approval_callback
            )
            
            if not approved:
                return CommandResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr="Command execution denied",
                    duration=datetime.now() - start_time,
                    success=False,
                    status=CommandStatus.BLOCKED,
                    risk_level=risk_level
                )
        
        try:
            exec_env = os.environ.copy() if env is None else {**os.environ, **env}
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=exec_env
            )
            
            stdout_lines = []
            stderr_lines = []
            
            async def read_stream(stream, lines_list):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line_str = line.decode('utf-8', errors='replace').rstrip()
                    lines_list.append(line_str)
                    output_callback(line_str)
            
            # Read both streams
            await asyncio.gather(
                read_stream(process.stdout, stdout_lines),
                read_stream(process.stderr, stderr_lines)
            )
            
            await process.wait()
            
            result = CommandResult(
                command=command,
                exit_code=process.returncode or 0,
                stdout='\n'.join(stdout_lines),
                stderr='\n'.join(stderr_lines),
                duration=datetime.now() - start_time,
                success=process.returncode == 0,
                status=CommandStatus.SUCCESS if process.returncode == 0 else CommandStatus.FAILURE,
                risk_level=risk_level
            )
            
            if not result.success:
                result.error_analysis = self.error_recovery.analyze_error(result)
                recovery_actions = self.error_recovery.suggest_recovery(result, result.error_analysis)
                result.recovery_suggestions = [
                    f"{action.action_type}: {action.description}"
                    for action in recovery_actions
                ]
            
            self.command_history.append(result)
            return result
            
        except Exception as e:
            result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=datetime.now() - start_time,
                success=False,
                status=CommandStatus.FAILURE,
                risk_level=risk_level
            )
            self.command_history.append(result)
            return result
    
    async def execute_with_retry(
        self,
        command: str,
        max_retries: int = 3,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Execute command with automatic retry on failure.
        
        Args:
            command: Command to execute
            max_retries: Maximum number of retry attempts
            cwd: Working directory
            env: Environment variables
            
        Returns:
            CommandResult from successful execution or final attempt
        """
        for attempt in range(max_retries):
            logger.info(f"Attempt {attempt + 1}/{max_retries} for command: {command}")
            
            result = await self.execute_command(
                command,
                cwd=cwd,
                env=env,
                require_approval=(attempt == 0)  # Only require approval on first attempt
            )
            
            if result.success:
                return result
            
            # If this is not the last attempt, wait before retrying
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Command failed, waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        return result
    
    def handle_command_error(self, result: CommandResult) -> List[RecoveryAction]:
        """
        Handle command error and suggest recovery actions.
        
        Args:
            result: Failed command result
            
        Returns:
            List of recovery actions
        """
        if not result.error_analysis:
            result.error_analysis = self.error_recovery.analyze_error(result)
        
        return self.error_recovery.suggest_recovery(result, result.error_analysis)
    
    def get_command_history(self, limit: Optional[int] = None) -> List[CommandResult]:
        """
        Get command execution history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of CommandResult objects
        """
        if limit:
            return self.command_history[-limit:]
        return self.command_history
    
    def clear_history(self):
        """Clear command execution history."""
        self.command_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.command_history)
        if total == 0:
            return {
                'total_commands': 0,
                'successful': 0,
                'failed': 0,
                'blocked': 0,
                'success_rate': 0.0
            }
        
        successful = sum(1 for r in self.command_history if r.success)
        failed = sum(1 for r in self.command_history if r.status == CommandStatus.FAILURE)
        blocked = sum(1 for r in self.command_history if r.status == CommandStatus.BLOCKED)
        
        return {
            'total_commands': total,
            'successful': successful,
            'failed': failed,
            'blocked': blocked,
            'success_rate': successful / total if total > 0 else 0.0,
            'average_duration': sum(r.duration.total_seconds() for r in self.command_history) / total
        }


# Convenience function for simple command execution
async def execute_command(
    command: str,
    cwd: Optional[Path] = None,
    timeout: int = 30
) -> CommandResult:
    """
    Execute a command with default settings.
    
    Args:
        command: Command to execute
        cwd: Working directory
        timeout: Command timeout
        
    Returns:
        CommandResult
    """
    executor = CommandExecutor(default_timeout=timeout)
    return await executor.execute_command(command, cwd=cwd)
