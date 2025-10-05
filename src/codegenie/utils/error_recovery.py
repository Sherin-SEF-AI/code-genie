"""
Automatic error recovery and self-healing system.
"""

import asyncio
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from .error_detector import DetectedError, ErrorDetector

logger = logging.getLogger(__name__)


class RecoveryAction(BaseModel):
    """A recovery action to fix an error."""
    
    action_type: str  # "command", "file_edit", "install", "config", "rollback"
    description: str
    command: Optional[str] = None
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    success_criteria: List[str] = []
    rollback_command: Optional[str] = None
    confidence: float = 0.8


class RecoveryResult(BaseModel):
    """Result of a recovery action."""
    
    success: bool
    action: RecoveryAction
    output: str
    error_message: Optional[str] = None
    rollback_performed: bool = False
    duration: float = 0.0


class ErrorRecovery:
    """Automatic error recovery and self-healing system."""
    
    def __init__(self, config):
        self.config = config
        self.error_detector = ErrorDetector()
        self.recovery_history: List[RecoveryResult] = []
        self.backup_dir = Path(tempfile.mkdtemp(prefix="claude-code-recovery-"))
        self.recovery_strategies = self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self) -> Dict[str, List[RecoveryAction]]:
        """Initialize recovery strategies for different error types."""
        
        strategies = {
            "python_import_error": [
                RecoveryAction(
                    action_type="install",
                    description="Install missing Python package",
                    command="pip install {package_name}",
                    success_criteria=["package installed successfully"],
                    confidence=0.9,
                ),
                RecoveryAction(
                    action_type="command",
                    description="Check if package is available",
                    command="pip search {package_name}",
                    success_criteria=["package found"],
                    confidence=0.7,
                ),
            ],
            "python_syntax_error": [
                RecoveryAction(
                    action_type="command",
                    description="Run syntax check with Python",
                    command="python -m py_compile {file_path}",
                    success_criteria=["no syntax errors"],
                    confidence=0.8,
                ),
                RecoveryAction(
                    action_type="file_edit",
                    description="Attempt to fix common syntax issues",
                    file_path="{file_path}",
                    success_criteria=["syntax error resolved"],
                    confidence=0.6,
                ),
            ],
            "python_indentation_error": [
                RecoveryAction(
                    action_type="command",
                    description="Fix indentation with autopep8",
                    command="autopep8 --in-place --aggressive {file_path}",
                    success_criteria=["indentation fixed"],
                    confidence=0.9,
                ),
                RecoveryAction(
                    action_type="command",
                    description="Fix indentation with black",
                    command="black {file_path}",
                    success_criteria=["indentation fixed"],
                    confidence=0.8,
                ),
            ],
            "python_name_error": [
                RecoveryAction(
                    action_type="file_edit",
                    description="Add missing import statement",
                    file_path="{file_path}",
                    success_criteria=["import added"],
                    confidence=0.7,
                ),
                RecoveryAction(
                    action_type="file_edit",
                    description="Define missing variable",
                    file_path="{file_path}",
                    success_criteria=["variable defined"],
                    confidence=0.6,
                ),
            ],
            "python_type_error": [
                RecoveryAction(
                    action_type="file_edit",
                    description="Add type conversion",
                    file_path="{file_path}",
                    success_criteria=["type error resolved"],
                    confidence=0.7,
                ),
                RecoveryAction(
                    action_type="file_edit",
                    description="Add type hints",
                    file_path="{file_path}",
                    success_criteria=["type hints added"],
                    confidence=0.6,
                ),
            ],
            "python_file_not_found": [
                RecoveryAction(
                    action_type="command",
                    description="Create missing file",
                    command="touch {file_path}",
                    success_criteria=["file created"],
                    confidence=0.9,
                ),
                RecoveryAction(
                    action_type="command",
                    description="Check file path",
                    command="find . -name '{file_name}' -type f",
                    success_criteria=["file found"],
                    confidence=0.8,
                ),
            ],
            "python_permission_error": [
                RecoveryAction(
                    action_type="command",
                    description="Fix file permissions",
                    command="chmod 644 {file_path}",
                    success_criteria=["permissions fixed"],
                    confidence=0.9,
                ),
                RecoveryAction(
                    action_type="command",
                    description="Change file ownership",
                    command="chown $USER:$USER {file_path}",
                    success_criteria=["ownership changed"],
                    confidence=0.8,
                ),
            ],
            "command_not_found": [
                RecoveryAction(
                    action_type="install",
                    description="Install missing command",
                    command="sudo apt-get install {command_name}",
                    success_criteria=["command installed"],
                    confidence=0.9,
                ),
                RecoveryAction(
                    action_type="command",
                    description="Check if command is in PATH",
                    command="which {command_name}",
                    success_criteria=["command found"],
                    confidence=0.7,
                ),
            ],
            "js_module_not_found": [
                RecoveryAction(
                    action_type="install",
                    description="Install missing npm package",
                    command="npm install {package_name}",
                    success_criteria=["package installed"],
                    confidence=0.9,
                ),
                RecoveryAction(
                    action_type="command",
                    description="Check package.json",
                    command="npm list {package_name}",
                    success_criteria=["package listed"],
                    confidence=0.8,
                ),
            ],
            "go_undefined_error": [
                RecoveryAction(
                    action_type="command",
                    description="Run go mod tidy",
                    command="go mod tidy",
                    success_criteria=["dependencies resolved"],
                    confidence=0.8,
                ),
                RecoveryAction(
                    action_type="file_edit",
                    description="Add missing import",
                    file_path="{file_path}",
                    success_criteria=["import added"],
                    confidence=0.7,
                ),
            ],
        }
        
        return strategies
    
    async def recover_from_error(
        self,
        error: DetectedError,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[RecoveryResult]:
        """Attempt to recover from a detected error."""
        
        logger.info(f"Attempting to recover from error: {error.error_type}")
        
        # Get recovery strategies for this error type
        strategies = self.recovery_strategies.get(error.error_type, [])
        
        if not strategies:
            logger.warning(f"No recovery strategies found for error type: {error.error_type}")
            return []
        
        recovery_results = []
        
        for strategy in strategies:
            try:
                # Create backup before attempting recovery
                await self._create_backup(error, context)
                
                # Attempt recovery
                result = await self._execute_recovery_action(strategy, error, context)
                recovery_results.append(result)
                
                # If successful, stop trying other strategies
                if result.success:
                    logger.info(f"Successfully recovered from error using: {strategy.description}")
                    break
                
            except Exception as e:
                logger.error(f"Recovery action failed: {e}")
                recovery_results.append(RecoveryResult(
                    success=False,
                    action=strategy,
                    output="",
                    error_message=str(e),
                ))
        
        # Add to history
        self.recovery_history.extend(recovery_results)
        
        return recovery_results
    
    async def _create_backup(self, error: DetectedError, context: Optional[Dict[str, Any]]) -> None:
        """Create backup before attempting recovery."""
        
        if error.file_path and Path(error.file_path).exists():
            backup_path = self.backup_dir / f"{Path(error.file_path).name}.backup"
            shutil.copy2(error.file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
    
    async def _execute_recovery_action(
        self,
        action: RecoveryAction,
        error: DetectedError,
        context: Optional[Dict[str, Any]],
    ) -> RecoveryResult:
        """Execute a recovery action."""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            if action.action_type == "command":
                result = await self._execute_command_recovery(action, error, context)
            elif action.action_type == "file_edit":
                result = await self._execute_file_edit_recovery(action, error, context)
            elif action.action_type == "install":
                result = await self._execute_install_recovery(action, error, context)
            elif action.action_type == "config":
                result = await self._execute_config_recovery(action, error, context)
            else:
                result = RecoveryResult(
                    success=False,
                    action=action,
                    output="",
                    error_message=f"Unknown action type: {action.action_type}",
                )
            
            end_time = asyncio.get_event_loop().time()
            result.duration = end_time - start_time
            
            return result
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message=str(e),
                duration=end_time - start_time,
            )
    
    async def _execute_command_recovery(
        self,
        action: RecoveryAction,
        error: DetectedError,
        context: Optional[Dict[str, Any]],
    ) -> RecoveryResult:
        """Execute a command-based recovery action."""
        
        if not action.command:
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message="No command specified",
            )
        
        # Replace placeholders in command
        command = self._replace_placeholders(action.command, error, context)
        
        # Check if command is allowed
        if not self._is_command_allowed(command):
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message="Command not allowed by security policy",
            )
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            output = stdout.decode('utf-8') + stderr.decode('utf-8')
            success = process.returncode == 0
            
            # Check success criteria
            if success and action.success_criteria:
                success = all(criteria.lower() in output.lower() for criteria in action.success_criteria)
            
            return RecoveryResult(
                success=success,
                action=action,
                output=output,
                error_message=None if success else f"Command failed with exit code {process.returncode}",
            )
            
        except asyncio.TimeoutError:
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message="Command timed out",
            )
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message=str(e),
            )
    
    async def _execute_file_edit_recovery(
        self,
        action: RecoveryAction,
        error: DetectedError,
        context: Optional[Dict[str, Any]],
    ) -> RecoveryResult:
        """Execute a file edit recovery action."""
        
        if not action.file_path:
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message="No file path specified",
            )
        
        file_path = self._replace_placeholders(action.file_path, error, context)
        
        if not Path(file_path).exists():
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message=f"File does not exist: {file_path}",
            )
        
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply recovery based on error type
            new_content = self._apply_file_recovery(original_content, error, action)
            
            if new_content != original_content:
                # Write modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                return RecoveryResult(
                    success=True,
                    action=action,
                    output=f"File modified: {file_path}",
                )
            else:
                return RecoveryResult(
                    success=False,
                    action=action,
                    output="",
                    error_message="No changes made to file",
                )
                
        except Exception as e:
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message=str(e),
            )
    
    async def _execute_install_recovery(
        self,
        action: RecoveryAction,
        error: DetectedError,
        context: Optional[Dict[str, Any]],
    ) -> RecoveryResult:
        """Execute an installation recovery action."""
        
        # Extract package name from error message
        package_name = self._extract_package_name(error)
        
        if not package_name:
            return RecoveryResult(
                success=False,
                action=action,
                output="",
                error_message="Could not extract package name from error",
            )
        
        # Replace package name in command
        command = action.command.replace("{package_name}", package_name)
        
        return await self._execute_command_recovery(
            RecoveryAction(
                action_type="command",
                description=action.description,
                command=command,
                success_criteria=action.success_criteria,
            ),
            error,
            context,
        )
    
    async def _execute_config_recovery(
        self,
        action: RecoveryAction,
        error: DetectedError,
        context: Optional[Dict[str, Any]],
    ) -> RecoveryResult:
        """Execute a configuration recovery action."""
        
        # This would handle configuration file modifications
        # For now, treat it as a command recovery
        return await self._execute_command_recovery(action, error, context)
    
    def _replace_placeholders(
        self,
        text: str,
        error: DetectedError,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Replace placeholders in text with actual values."""
        
        replacements = {
            "{file_path}": error.file_path or "",
            "{file_name}": Path(error.file_path).name if error.file_path else "",
            "{line_number}": str(error.line_number) if error.line_number else "",
            "{package_name}": self._extract_package_name(error),
            "{command_name}": self._extract_command_name(error),
        }
        
        result = text
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result
    
    def _extract_package_name(self, error: DetectedError) -> str:
        """Extract package name from error message."""
        
        message = error.message.lower()
        
        # Python import errors
        if "import" in message and "error" in message:
            import re
            match = re.search(r"no module named ['\"]([^'\"]+)['\"]", message)
            if match:
                return match.group(1)
        
        # JavaScript module errors
        if "cannot resolve module" in message:
            import re
            match = re.search(r"cannot resolve module ['\"]([^'\"]+)['\"]", message)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_command_name(self, error: DetectedError) -> str:
        """Extract command name from error message."""
        
        message = error.message.lower()
        
        if "command not found" in message:
            import re
            match = re.search(r"command not found: ([^\s]+)", message)
            if match:
                return match.group(1)
        
        return ""
    
    def _apply_file_recovery(self, content: str, error: DetectedError, action: RecoveryAction) -> str:
        """Apply file-based recovery based on error type."""
        
        lines = content.split('\n')
        
        if error.error_type == "python_name_error":
            # Try to add missing import
            variable_name = self._extract_variable_name(error)
            if variable_name:
                import_line = f"import {variable_name}\n"
                if not any(import_line.strip() in line for line in lines):
                    lines.insert(0, import_line)
        
        elif error.error_type == "python_indentation_error":
            # Fix indentation
            if error.line_number and error.line_number <= len(lines):
                line_index = error.line_number - 1
                line = lines[line_index]
                # Remove leading whitespace and add proper indentation
                lines[line_index] = "    " + line.lstrip()
        
        elif error.error_type == "python_syntax_error":
            # Try to fix common syntax errors
            if error.line_number and error.line_number <= len(lines):
                line_index = error.line_number - 1
                line = lines[line_index]
                
                # Fix missing colon
                if line.strip().endswith(')'):
                    lines[line_index] = line + ':'
                # Fix missing quote
                elif line.count('"') % 2 == 1:
                    lines[line_index] = line + '"'
                elif line.count("'") % 2 == 1:
                    lines[line_index] = line + "'"
        
        return '\n'.join(lines)
    
    def _extract_variable_name(self, error: DetectedError) -> str:
        """Extract variable name from name error."""
        
        message = error.message
        import re
        match = re.search(r"name '([^']+)' is not defined", message)
        return match.group(1) if match else ""
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed by security policy."""
        
        cmd_parts = command.split()
        if not cmd_parts:
            return False
        
        cmd_name = cmd_parts[0]
        
        # Check blocked commands
        blocked_commands = ["rm", "del", "format", "fdisk", "mkfs", "dd", "shutdown", "reboot"]
        if any(cmd_name.startswith(blocked) for blocked in blocked_commands):
            return False
        
        # Check allowed commands
        allowed_commands = ["pip", "npm", "go", "python", "python3", "chmod", "chown", "touch", "find", "which"]
        if any(cmd_name.startswith(allowed) for allowed in allowed_commands):
            return True
        
        return False
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        
        if not self.recovery_history:
            return {"message": "No recovery attempts yet"}
        
        total_attempts = len(self.recovery_history)
        successful_recoveries = sum(1 for result in self.recovery_history if result.success)
        success_rate = successful_recoveries / total_attempts if total_attempts > 0 else 0.0
        
        # Count by action type
        action_type_counts = {}
        for result in self.recovery_history:
            action_type = result.action.action_type
            action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
        
        return {
            "total_attempts": total_attempts,
            "successful_recoveries": successful_recoveries,
            "success_rate": success_rate,
            "action_type_distribution": action_type_counts,
            "average_duration": sum(r.duration for r in self.recovery_history) / total_attempts,
        }
    
    def rollback_recovery(self, result: RecoveryResult) -> bool:
        """Rollback a recovery action."""
        
        try:
            if result.action.rollback_command:
                # Execute rollback command
                subprocess.run(result.action.rollback_command, shell=True, check=True)
            
            # Restore from backup if available
            if result.action.file_path:
                backup_path = self.backup_dir / f"{Path(result.action.file_path).name}.backup"
                if backup_path.exists():
                    shutil.copy2(backup_path, result.action.file_path)
            
            result.rollback_performed = True
            logger.info(f"Rolled back recovery action: {result.action.description}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback recovery: {e}")
            return False
    
    def clear_history(self) -> None:
        """Clear recovery history."""
        self.recovery_history.clear()
        logger.info("Cleared recovery history")
    
    def cleanup(self) -> None:
        """Clean up temporary resources."""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup backup directory: {e}")
