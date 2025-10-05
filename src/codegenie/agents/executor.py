"""
Task execution engine for running tests and other operations.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExecutionResult(BaseModel):
    """Result of a task execution."""
    
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    command: str
    working_directory: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class TaskExecutor:
    """Executes tasks and operations safely."""
    
    def __init__(self, config):
        self.config = config
        self.execution_history: List[ExecutionResult] = []
        self.sandbox_dir = Path(tempfile.mkdtemp(prefix="claude-code-"))
    
    async def execute_command(
        self,
        command: str,
        working_directory: Optional[Path] = None,
        timeout: int = 300,
        capture_output: bool = True,
    ) -> ExecutionResult:
        """Execute a command safely."""
        
        if working_directory is None:
            working_directory = Path.cwd()
        
        # Validate command
        if not self._is_command_allowed(command):
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Command not allowed: {command}",
                duration=0.0,
                command=command,
                working_directory=str(working_directory),
                error_message="Command blocked by security policy",
            )
        
        logger.info(f"Executing command: {command} in {working_directory}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=working_directory,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Decode output
            stdout_str = stdout.decode('utf-8') if stdout else ""
            stderr_str = stderr.decode('utf-8') if stderr else ""
            
            result = ExecutionResult(
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                duration=duration,
                command=command,
                working_directory=str(working_directory),
            )
            
            # Add to history
            self.execution_history.append(result)
            
            logger.info(f"Command completed with exit code {process.returncode}")
            return result
            
        except asyncio.TimeoutError:
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            result = ExecutionResult(
                success=False,
                exit_code=124,  # Timeout exit code
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration=duration,
                command=command,
                working_directory=str(working_directory),
                error_message="Command execution timed out",
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            result = ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration=duration,
                command=command,
                working_directory=str(working_directory),
                error_message=str(e),
            )
            
            self.execution_history.append(result)
            logger.error(f"Command execution failed: {e}")
            return result
    
    async def run_tests(
        self,
        project_path: Path,
        test_path: Optional[Path] = None,
        framework: Optional[str] = None,
    ) -> ExecutionResult:
        """Run tests for the project."""
        
        # Detect testing framework if not specified
        if framework is None:
            framework = self._detect_testing_framework(project_path)
        
        # Build test command
        command = self._build_test_command(framework, test_path)
        
        if not command:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="No testing framework detected",
                duration=0.0,
                command="",
                working_directory=str(project_path),
                error_message="Testing framework not found",
            )
        
        # Execute tests
        result = await self.execute_command(command, project_path)
        
        # Parse test results
        result.metadata = self._parse_test_results(result, framework)
        
        return result
    
    async def run_linter(
        self,
        project_path: Path,
        file_path: Optional[Path] = None,
    ) -> ExecutionResult:
        """Run linter on the project or specific file."""
        
        # Detect linter
        linter = self._detect_linter(project_path)
        
        if not linter:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="No linter detected",
                duration=0.0,
                command="",
                working_directory=str(project_path),
                error_message="Linter not found",
            )
        
        # Build linter command
        command = self._build_linter_command(linter, file_path)
        
        # Execute linter
        result = await self.execute_command(command, project_path)
        
        # Parse linter results
        result.metadata = self._parse_linter_results(result, linter)
        
        return result
    
    async def run_formatter(
        self,
        project_path: Path,
        file_path: Optional[Path] = None,
        check_only: bool = False,
    ) -> ExecutionResult:
        """Run code formatter on the project or specific file."""
        
        # Detect formatter
        formatter = self._detect_formatter(project_path)
        
        if not formatter:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="No formatter detected",
                duration=0.0,
                command="",
                working_directory=str(project_path),
                error_message="Formatter not found",
            )
        
        # Build formatter command
        command = self._build_formatter_command(formatter, file_path, check_only)
        
        # Execute formatter
        result = await self.execute_command(command, project_path)
        
        # Parse formatter results
        result.metadata = self._parse_formatter_results(result, formatter)
        
        return result
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to execute."""
        
        cmd_parts = command.split()
        if not cmd_parts:
            return False
        
        cmd_name = cmd_parts[0]
        
        # Check blocked commands
        if any(cmd_name.startswith(blocked) for blocked in self.config.execution.blocked_commands):
            return False
        
        # Check allowed commands
        if any(cmd_name.startswith(allowed) for allowed in self.config.execution.allowed_commands):
            return True
        
        # Default to blocked for safety
        return False
    
    def _detect_testing_framework(self, project_path: Path) -> Optional[str]:
        """Detect the testing framework used in the project."""
        
        # Check for Python frameworks
        if (project_path / "requirements.txt").exists():
            try:
                with open(project_path / "requirements.txt", 'r') as f:
                    content = f.read()
                    if "pytest" in content:
                        return "pytest"
                    elif "unittest" in content:
                        return "unittest"
            except Exception:
                pass
        
        # Check for Node.js frameworks
        if (project_path / "package.json").exists():
            try:
                with open(project_path / "package.json", 'r') as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})
                    if "test" in scripts:
                        test_script = scripts["test"]
                        if "jest" in test_script:
                            return "jest"
                        elif "mocha" in test_script:
                            return "mocha"
            except Exception:
                pass
        
        # Check for Go testing
        if any(f.suffix == '.go' for f in project_path.rglob("*")):
            return "go_test"
        
        # Check for Rust testing
        if (project_path / "Cargo.toml").exists():
            return "cargo_test"
        
        return None
    
    def _build_test_command(self, framework: str, test_path: Optional[Path] = None) -> Optional[str]:
        """Build the test command for the given framework."""
        
        if framework == "pytest":
            if test_path:
                return f"pytest {test_path} -v"
            return "pytest -v"
        
        elif framework == "unittest":
            if test_path:
                return f"python -m unittest {test_path}"
            return "python -m unittest discover"
        
        elif framework == "jest":
            return "npm test"
        
        elif framework == "mocha":
            return "npm test"
        
        elif framework == "go_test":
            if test_path:
                return f"go test {test_path}"
            return "go test ./..."
        
        elif framework == "cargo_test":
            return "cargo test"
        
        return None
    
    def _detect_linter(self, project_path: Path) -> Optional[str]:
        """Detect the linter used in the project."""
        
        # Check for Python linters
        if any(f.suffix == '.py' for f in project_path.rglob("*")):
            if (project_path / ".pylintrc").exists():
                return "pylint"
            elif (project_path / "setup.cfg").exists():
                try:
                    with open(project_path / "setup.cfg", 'r') as f:
                        content = f.read()
                        if "flake8" in content:
                            return "flake8"
                except Exception:
                    pass
        
        # Check for JavaScript linters
        if (project_path / ".eslintrc").exists() or (project_path / ".eslintrc.js").exists():
            return "eslint"
        
        return None
    
    def _build_linter_command(self, linter: str, file_path: Optional[Path] = None) -> str:
        """Build the linter command."""
        
        if linter == "pylint":
            if file_path:
                return f"pylint {file_path}"
            return "pylint ."
        
        elif linter == "flake8":
            if file_path:
                return f"flake8 {file_path}"
            return "flake8 ."
        
        elif linter == "eslint":
            if file_path:
                return f"eslint {file_path}"
            return "eslint ."
        
        return ""
    
    def _detect_formatter(self, project_path: Path) -> Optional[str]:
        """Detect the formatter used in the project."""
        
        # Check for Python formatters
        if any(f.suffix == '.py' for f in project_path.rglob("*")):
            if (project_path / "pyproject.toml").exists():
                try:
                    with open(project_path / "pyproject.toml", 'r') as f:
                        content = f.read()
                        if "black" in content:
                            return "black"
                except Exception:
                    pass
        
        # Check for JavaScript formatters
        if (project_path / ".prettierrc").exists() or (project_path / "prettier.config.js").exists():
            return "prettier"
        
        return None
    
    def _build_formatter_command(self, formatter: str, file_path: Optional[Path] = None, check_only: bool = False) -> str:
        """Build the formatter command."""
        
        if formatter == "black":
            if check_only:
                if file_path:
                    return f"black --check {file_path}"
                return "black --check ."
            else:
                if file_path:
                    return f"black {file_path}"
                return "black ."
        
        elif formatter == "prettier":
            if check_only:
                if file_path:
                    return f"prettier --check {file_path}"
                return "prettier --check ."
            else:
                if file_path:
                    return f"prettier --write {file_path}"
                return "prettier --write ."
        
        return ""
    
    def _parse_test_results(self, result: ExecutionResult, framework: str) -> Dict[str, Any]:
        """Parse test execution results."""
        
        metadata = {
            "framework": framework,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "coverage": None,
            "errors": [],
        }
        
        if framework == "pytest":
            # Parse pytest output
            lines = result.stdout.split('\n')
            for line in lines:
                if "failed" in line and "passed" in line:
                    # Extract test counts
                    import re
                    match = re.search(r'(\d+) failed', line)
                    if match:
                        metadata["tests_failed"] = int(match.group(1))
                    
                    match = re.search(r'(\d+) passed', line)
                    if match:
                        metadata["tests_passed"] = int(match.group(1))
                    
                    metadata["tests_run"] = metadata["tests_passed"] + metadata["tests_failed"]
        
        elif framework == "jest":
            # Parse Jest output
            if "Tests:" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Tests:" in line:
                        import re
                        match = re.search(r'(\d+) passed', line)
                        if match:
                            metadata["tests_passed"] = int(match.group(1))
                        
                        match = re.search(r'(\d+) failed', line)
                        if match:
                            metadata["tests_failed"] = int(match.group(1))
                        
                        metadata["tests_run"] = metadata["tests_passed"] + metadata["tests_failed"]
        
        return metadata
    
    def _parse_linter_results(self, result: ExecutionResult, linter: str) -> Dict[str, Any]:
        """Parse linter execution results."""
        
        metadata = {
            "linter": linter,
            "issues": [],
            "error_count": 0,
            "warning_count": 0,
        }
        
        # Parse linter output for issues
        lines = result.stdout.split('\n') + result.stderr.split('\n')
        
        for line in lines:
            if line.strip():
                # Simple parsing - in a real implementation, you'd parse more specifically
                if "error" in line.lower():
                    metadata["error_count"] += 1
                    metadata["issues"].append({"type": "error", "message": line})
                elif "warning" in line.lower():
                    metadata["warning_count"] += 1
                    metadata["issues"].append({"type": "warning", "message": line})
        
        return metadata
    
    def _parse_formatter_results(self, result: ExecutionResult, formatter: str) -> Dict[str, Any]:
        """Parse formatter execution results."""
        
        metadata = {
            "formatter": formatter,
            "files_changed": 0,
            "files_checked": 0,
        }
        
        # Parse formatter output
        lines = result.stdout.split('\n')
        
        for line in lines:
            if "reformatted" in line.lower() or "changed" in line.lower():
                metadata["files_changed"] += 1
            elif "unchanged" in line.lower() or "would reformat" in line.lower():
                metadata["files_checked"] += 1
        
        return metadata
    
    def get_execution_history(self) -> List[ExecutionResult]:
        """Get the execution history."""
        return self.execution_history.copy()
    
    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self.execution_history.clear()
    
    def cleanup(self) -> None:
        """Clean up temporary resources."""
        try:
            import shutil
            if self.sandbox_dir.exists():
                shutil.rmtree(self.sandbox_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup sandbox directory: {e}")
