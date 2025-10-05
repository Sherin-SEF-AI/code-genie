"""
Safe terminal execution system with security and isolation.
"""

import asyncio
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExecutionContext(BaseModel):
    """Context for command execution."""
    
    working_directory: Path
    environment: Dict[str, str] = {}
    timeout: int = 300
    max_output_size: int = 1024 * 1024  # 1MB
    allowed_commands: List[str] = []
    blocked_commands: List[str] = []
    user_id: Optional[int] = None
    group_id: Optional[int] = None


class ExecutionResult(BaseModel):
    """Result of a safe command execution."""
    
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    command: str
    working_directory: str
    environment: Dict[str, str] = {}
    security_violations: List[str] = []
    resource_usage: Dict[str, Any] = {}


class SafeExecutor:
    """Safe terminal execution system with security and isolation."""
    
    def __init__(self, config):
        self.config = config
        self.sandbox_dir = Path(tempfile.mkdtemp(prefix="claude-code-sandbox-"))
        self.execution_history: List[ExecutionResult] = []
        self.resource_limits = {
            "max_memory": 512 * 1024 * 1024,  # 512MB
            "max_cpu_time": 300,  # 5 minutes
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "max_processes": 10,
        }
        
        # Initialize sandbox environment
        self._setup_sandbox()
    
    def _setup_sandbox(self) -> None:
        """Set up sandbox environment for safe execution."""
        
        # Create sandbox directories
        (self.sandbox_dir / "workspace").mkdir(exist_ok=True)
        (self.sandbox_dir / "temp").mkdir(exist_ok=True)
        (self.sandbox_dir / "logs").mkdir(exist_ok=True)
        
        # Set up environment variables
        self.sandbox_env = {
            "HOME": str(self.sandbox_dir / "workspace"),
            "TMPDIR": str(self.sandbox_dir / "temp"),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "PYTHONPATH": "",
            "NODE_PATH": "",
        }
        
        logger.info(f"Set up sandbox environment: {self.sandbox_dir}")
    
    async def execute_safe(
        self,
        command: str,
        context: Optional[ExecutionContext] = None,
    ) -> ExecutionResult:
        """Execute a command safely with security checks and isolation."""
        
        if context is None:
            context = ExecutionContext(working_directory=Path.cwd())
        
        logger.info(f"Executing safe command: {command}")
        
        # Security checks
        security_violations = self._check_security(command, context)
        if security_violations:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Security violations: {', '.join(security_violations)}",
                duration=0.0,
                command=command,
                working_directory=str(context.working_directory),
                security_violations=security_violations,
            )
        
        # Prepare execution environment
        exec_env = self._prepare_environment(context)
        exec_dir = self._prepare_working_directory(context)
        
        start_time = time.time()
        
        try:
            # Execute command with resource limits
            result = await self._execute_with_limits(command, exec_dir, exec_env, context)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Add to history
            self.execution_history.append(result)
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            error_result = ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration=duration,
                command=command,
                working_directory=str(context.working_directory),
                error_message=str(e),
            )
            
            self.execution_history.append(error_result)
            return error_result
    
    def _check_security(self, command: str, context: ExecutionContext) -> List[str]:
        """Check command for security violations."""
        
        violations = []
        
        # Check for blocked commands
        cmd_parts = command.split()
        if cmd_parts:
            cmd_name = cmd_parts[0]
            
            # Check against blocked commands
            blocked_commands = [
                "rm", "del", "format", "fdisk", "mkfs", "dd", "shutdown", "reboot",
                "halt", "poweroff", "init", "killall", "pkill", "kill", "sudo",
                "su", "passwd", "useradd", "userdel", "groupadd", "groupdel",
                "chmod", "chown", "chgrp", "umount", "mount", "fuser", "lsof"
            ]
            
            if any(cmd_name.startswith(blocked) for blocked in blocked_commands):
                violations.append(f"Blocked command: {cmd_name}")
            
            # Check for dangerous patterns
            dangerous_patterns = [
                r"rm\s+-rf", r"del\s+/[sq]", r"format\s+[c-z]:", r"fdisk\s+/dev/",
                r"mkfs\s+/dev/", r"dd\s+if=.*of=/dev/", r">\s*/dev/", r">>\s*/dev/",
                r"curl\s+.*\|\s*sh", r"wget\s+.*\|\s*sh", r"python\s+-c\s+.*exec",
                r"eval\s+", r"exec\s+", r"system\s+", r"shell_exec\s+"
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    violations.append(f"Dangerous pattern detected: {pattern}")
        
        # Check working directory
        if not self._is_safe_directory(context.working_directory):
            violations.append(f"Unsafe working directory: {context.working_directory}")
        
        # Check environment variables
        for key, value in context.environment.items():
            if self._is_dangerous_env_var(key, value):
                violations.append(f"Dangerous environment variable: {key}")
        
        return violations
    
    def _is_safe_directory(self, directory: Path) -> bool:
        """Check if directory is safe for execution."""
        
        try:
            # Resolve to absolute path
            abs_dir = directory.resolve()
            
            # Check if it's within allowed paths
            allowed_paths = [
                Path.cwd(),
                Path.home() / "projects",
                Path.home() / "workspace",
                Path.home() / "code",
            ]
            
            # Allow if it's within any allowed path
            for allowed_path in allowed_paths:
                try:
                    abs_dir.relative_to(allowed_path.resolve())
                    return True
                except ValueError:
                    continue
            
            # Check if it's a temporary directory
            if "tmp" in str(abs_dir) or "temp" in str(abs_dir):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _is_dangerous_env_var(self, key: str, value: str) -> bool:
        """Check if environment variable is dangerous."""
        
        dangerous_vars = [
            "PATH", "LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONPATH", "NODE_PATH",
            "GOPATH", "RUST_PATH", "JAVA_HOME", "ANDROID_HOME"
        ]
        
        if key in dangerous_vars:
            # Check for dangerous paths
            dangerous_paths = ["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/etc", "/root"]
            if any(path in value for path in dangerous_paths):
                return True
        
        # Check for command injection patterns
        if any(char in value for char in [";", "|", "&", "`", "$", "(", ")"]):
            return True
        
        return False
    
    def _prepare_environment(self, context: ExecutionContext) -> Dict[str, str]:
        """Prepare execution environment."""
        
        # Start with sandbox environment
        env = self.sandbox_env.copy()
        
        # Add context environment variables (filtered)
        for key, value in context.environment.items():
            if not self._is_dangerous_env_var(key, value):
                env[key] = value
        
        # Set resource limits
        env["ULIMIT_MEMORY"] = str(self.resource_limits["max_memory"])
        env["ULIMIT_CPU"] = str(self.resource_limits["max_cpu_time"])
        
        return env
    
    def _prepare_working_directory(self, context: ExecutionContext) -> Path:
        """Prepare working directory for execution."""
        
        # Create a safe working directory in sandbox
        safe_dir = self.sandbox_dir / "workspace" / "execution"
        safe_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy necessary files from original directory
        if context.working_directory.exists():
            try:
                # Copy only safe file types
                safe_extensions = {'.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.h', '.txt', '.md', '.json', '.yaml', '.yml'}
                
                for file_path in context.working_directory.rglob("*"):
                    if file_path.is_file() and file_path.suffix in safe_extensions:
                        rel_path = file_path.relative_to(context.working_directory)
                        target_path = safe_dir / rel_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, target_path)
                        
            except Exception as e:
                logger.warning(f"Failed to copy files to sandbox: {e}")
        
        return safe_dir
    
    async def _execute_with_limits(
        self,
        command: str,
        working_directory: Path,
        environment: Dict[str, str],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute command with resource limits."""
        
        try:
            # Create process with resource limits
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=working_directory,
                env=environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=self._set_resource_limits,
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=context.timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                
                return ExecutionResult(
                    success=False,
                    exit_code=124,  # Timeout exit code
                    stdout="",
                    stderr=f"Command timed out after {context.timeout} seconds",
                    duration=context.timeout,
                    command=command,
                    working_directory=str(working_directory),
                    error_message="Command execution timed out",
                )
            
            # Decode output with size limits
            stdout_str = self._limit_output(stdout.decode('utf-8', errors='replace'), context.max_output_size)
            stderr_str = self._limit_output(stderr.decode('utf-8', errors='replace'), context.max_output_size)
            
            # Check for resource violations
            resource_usage = self._get_resource_usage(process)
            violations = self._check_resource_violations(resource_usage)
            
            return ExecutionResult(
                success=process.returncode == 0 and not violations,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                duration=0.0,  # Will be set by caller
                command=command,
                working_directory=str(working_directory),
                environment=environment,
                security_violations=violations,
                resource_usage=resource_usage,
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration=0.0,
                command=command,
                working_directory=str(working_directory),
                error_message=str(e),
            )
    
    def _set_resource_limits(self) -> None:
        """Set resource limits for the process."""
        
        try:
            import resource
            
            # Set memory limit
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.resource_limits["max_memory"], self.resource_limits["max_memory"])
            )
            
            # Set CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.resource_limits["max_cpu_time"], self.resource_limits["max_cpu_time"])
            )
            
            # Set file size limit
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (self.resource_limits["max_file_size"], self.resource_limits["max_file_size"])
            )
            
        except Exception as e:
            logger.warning(f"Failed to set resource limits: {e}")
    
    def _limit_output(self, output: str, max_size: int) -> str:
        """Limit output size to prevent memory issues."""
        
        if len(output) > max_size:
            return output[:max_size] + "\n... (output truncated)"
        return output
    
    def _get_resource_usage(self, process) -> Dict[str, Any]:
        """Get resource usage information."""
        
        try:
            import psutil
            
            proc = psutil.Process(process.pid)
            return {
                "memory_usage": proc.memory_info().rss,
                "cpu_percent": proc.cpu_percent(),
                "num_threads": proc.num_threads(),
                "create_time": proc.create_time(),
            }
        except Exception:
            return {}
    
    def _check_resource_violations(self, resource_usage: Dict[str, Any]) -> List[str]:
        """Check for resource limit violations."""
        
        violations = []
        
        if "memory_usage" in resource_usage:
            if resource_usage["memory_usage"] > self.resource_limits["max_memory"]:
                violations.append(f"Memory limit exceeded: {resource_usage['memory_usage']} > {self.resource_limits['max_memory']}")
        
        if "num_threads" in resource_usage:
            if resource_usage["num_threads"] > self.resource_limits["max_processes"]:
                violations.append(f"Process limit exceeded: {resource_usage['num_threads']} > {self.resource_limits['max_processes']}")
        
        return violations
    
    async def execute_python_code(
        self,
        code: str,
        context: Optional[ExecutionContext] = None,
    ) -> ExecutionResult:
        """Execute Python code safely."""
        
        # Create temporary Python file
        temp_file = self.sandbox_dir / "temp" / "execution.py"
        temp_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Execute the Python file
            return await self.execute_safe(f"python {temp_file}", context)
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration=0.0,
                command=f"python {temp_file}",
                working_directory=str(temp_file.parent),
                error_message=str(e),
            )
    
    async def execute_shell_script(
        self,
        script: str,
        context: Optional[ExecutionContext] = None,
    ) -> ExecutionResult:
        """Execute shell script safely."""
        
        # Create temporary shell script
        temp_file = self.sandbox_dir / "temp" / "script.sh"
        temp_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n")
                f.write(script)
            
            # Make executable
            os.chmod(temp_file, 0o755)
            
            # Execute the script
            return await self.execute_safe(f"bash {temp_file}", context)
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration=0.0,
                command=f"bash {temp_file}",
                working_directory=str(temp_file.parent),
                error_message=str(e),
            )
    
    def get_execution_history(self) -> List[ExecutionResult]:
        """Get execution history."""
        return self.execution_history.copy()
    
    def clear_execution_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()
        logger.info("Cleared execution history")
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        
        if not self.execution_history:
            return {"message": "No executions yet"}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for result in self.execution_history if result.success)
        failed_executions = total_executions - successful_executions
        
        # Count security violations
        security_violations = sum(len(result.security_violations) for result in self.execution_history)
        
        # Calculate average duration
        total_duration = sum(result.duration for result in self.execution_history)
        average_duration = total_duration / total_executions if total_executions > 0 else 0.0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0.0,
            "security_violations": security_violations,
            "average_duration": average_duration,
        }
    
    def cleanup(self) -> None:
        """Clean up sandbox environment."""
        try:
            if self.sandbox_dir.exists():
                shutil.rmtree(self.sandbox_dir)
            logger.info("Cleaned up sandbox environment")
        except Exception as e:
            logger.warning(f"Failed to cleanup sandbox: {e}")
