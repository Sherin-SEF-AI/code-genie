"""
Agent isolation and sandboxing system for secure multi-agent execution.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import psutil
from concurrent.futures import ThreadPoolExecutor

# Docker is optional
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

logger = logging.getLogger(__name__)


class IsolationLevel(Enum):
    """Isolation levels for agent execution."""
    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"
    VM = "vm"


class ResourceLimit(Enum):
    """Resource limit types."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    TIME = "time"


@dataclass
class AgentSandbox:
    """Agent sandbox configuration and state."""
    agent_id: str
    sandbox_id: str
    isolation_level: IsolationLevel
    working_directory: Path
    resource_limits: Dict[ResourceLimit, Any] = field(default_factory=dict)
    allowed_operations: Set[str] = field(default_factory=set)
    blocked_operations: Set[str] = field(default_factory=set)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    network_access: bool = False
    file_system_access: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    container_id: Optional[str] = None
    process_id: Optional[int] = None


@dataclass
class ResourceUsage:
    """Resource usage tracking."""
    cpu_percent: float = 0.0
    memory_bytes: int = 0
    disk_bytes: int = 0
    network_bytes: int = 0
    execution_time: float = 0.0
    file_operations: int = 0
    network_operations: int = 0


class AgentIsolationManager:
    """Manages agent isolation and sandboxing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sandboxes: Dict[str, AgentSandbox] = {}
        self.resource_monitor = ResourceMonitor()
        self.docker_client = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize Docker client if available
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized for container isolation")
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
        else:
            logger.warning("Docker module not installed, container isolation unavailable")
        
        # Create base sandbox directory
        self.base_sandbox_dir = Path(tempfile.mkdtemp(prefix="agent-sandbox-"))
        self.base_sandbox_dir.mkdir(exist_ok=True)
        
        # Start monitoring
        asyncio.create_task(self._monitor_sandboxes())
    
    async def create_sandbox(
        self,
        agent_id: str,
        isolation_level: IsolationLevel = IsolationLevel.PROCESS,
        resource_limits: Optional[Dict[ResourceLimit, Any]] = None,
        allowed_operations: Optional[Set[str]] = None,
        network_access: bool = False
    ) -> AgentSandbox:
        """Create a new agent sandbox."""
        
        sandbox_id = f"sandbox_{agent_id}_{int(time.time())}"
        sandbox_dir = self.base_sandbox_dir / sandbox_id
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default resource limits
        default_limits = {
            ResourceLimit.CPU: 50.0,  # 50% CPU
            ResourceLimit.MEMORY: 512 * 1024 * 1024,  # 512MB
            ResourceLimit.DISK: 1024 * 1024 * 1024,  # 1GB
            ResourceLimit.TIME: 300,  # 5 minutes
            ResourceLimit.NETWORK: 10 * 1024 * 1024  # 10MB
        }
        
        if resource_limits:
            default_limits.update(resource_limits)
        
        # Set default allowed operations
        default_operations = {
            'read_file', 'write_file', 'execute_code', 'analyze_code'
        }
        if allowed_operations:
            default_operations.update(allowed_operations)
        
        sandbox = AgentSandbox(
            agent_id=agent_id,
            sandbox_id=sandbox_id,
            isolation_level=isolation_level,
            working_directory=sandbox_dir,
            resource_limits=default_limits,
            allowed_operations=default_operations,
            network_access=network_access,
            file_system_access={str(sandbox_dir)}
        )
        
        # Initialize sandbox based on isolation level
        if isolation_level == IsolationLevel.CONTAINER:
            await self._setup_container_sandbox(sandbox)
        elif isolation_level == IsolationLevel.PROCESS:
            await self._setup_process_sandbox(sandbox)
        
        self.sandboxes[sandbox_id] = sandbox
        
        logger.info(f"Created sandbox {sandbox_id} for agent {agent_id} with isolation level {isolation_level.value}")
        return sandbox
    
    async def _setup_container_sandbox(self, sandbox: AgentSandbox) -> None:
        """Set up container-based sandbox."""
        
        if not self.docker_client:
            raise RuntimeError("Docker not available for container isolation")
        
        try:
            # Create container with resource limits
            container = self.docker_client.containers.run(
                image="python:3.9-slim",
                command="sleep infinity",
                detach=True,
                name=f"agent-{sandbox.sandbox_id}",
                working_dir="/workspace",
                volumes={
                    str(sandbox.working_directory): {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                },
                mem_limit=f"{sandbox.resource_limits[ResourceLimit.MEMORY]}b",
                cpu_quota=int(sandbox.resource_limits[ResourceLimit.CPU] * 1000),
                cpu_period=100000,
                network_mode="none" if not sandbox.network_access else "bridge",
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],
                cap_add=["CHOWN", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID"],
                read_only=False,
                tmpfs={"/tmp": "noexec,nosuid,size=100m"}
            )
            
            sandbox.container_id = container.id
            logger.info(f"Container {container.id} created for sandbox {sandbox.sandbox_id}")
            
        except Exception as e:
            logger.error(f"Failed to create container sandbox: {e}")
            raise
    
    async def _setup_process_sandbox(self, sandbox: AgentSandbox) -> None:
        """Set up process-based sandbox."""
        
        # Create isolated environment
        (sandbox.working_directory / "bin").mkdir(exist_ok=True)
        (sandbox.working_directory / "lib").mkdir(exist_ok=True)
        (sandbox.working_directory / "tmp").mkdir(exist_ok=True)
        
        # Set up environment variables
        sandbox.environment_variables.update({
            "HOME": str(sandbox.working_directory),
            "TMPDIR": str(sandbox.working_directory / "tmp"),
            "PATH": str(sandbox.working_directory / "bin"),
            "PYTHONPATH": str(sandbox.working_directory / "lib"),
        })
        
        logger.info(f"Process sandbox set up for {sandbox.sandbox_id}")
    
    async def execute_in_sandbox(
        self,
        sandbox_id: str,
        operation: str,
        code: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute code in a sandbox."""
        
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f"Sandbox {sandbox_id} not found")
        
        if not sandbox.is_active:
            raise RuntimeError(f"Sandbox {sandbox_id} is not active")
        
        if operation not in sandbox.allowed_operations:
            raise PermissionError(f"Operation {operation} not allowed in sandbox {sandbox_id}")
        
        # Update last activity
        sandbox.last_activity = time.time()
        
        # Check resource limits before execution
        current_usage = await self.resource_monitor.get_usage(sandbox_id)
        if not self._check_resource_limits(sandbox, current_usage):
            raise RuntimeError("Resource limits exceeded")
        
        # Execute based on isolation level
        if sandbox.isolation_level == IsolationLevel.CONTAINER:
            return await self._execute_in_container(sandbox, operation, code, timeout)
        elif sandbox.isolation_level == IsolationLevel.PROCESS:
            return await self._execute_in_process(sandbox, operation, code, timeout)
        else:
            return await self._execute_direct(sandbox, operation, code, timeout)
    
    async def _execute_in_container(
        self,
        sandbox: AgentSandbox,
        operation: str,
        code: str,
        timeout: Optional[int]
    ) -> Dict[str, Any]:
        """Execute code in container sandbox."""
        
        if not sandbox.container_id:
            raise RuntimeError("Container not available")
        
        try:
            container = self.docker_client.containers.get(sandbox.container_id)
            
            # Write code to file in container
            code_file = "/workspace/execution.py"
            container.exec_run(f"bash -c 'cat > {code_file}'", stdin=True, socket=True)
            
            # Execute code
            exec_result = container.exec_run(
                f"python {code_file}",
                workdir="/workspace",
                environment=sandbox.environment_variables,
                user="nobody"
            )
            
            return {
                'success': exec_result.exit_code == 0,
                'exit_code': exec_result.exit_code,
                'stdout': exec_result.output.decode('utf-8', errors='replace'),
                'stderr': '',
                'execution_time': 0.0  # TODO: Measure actual time
            }
            
        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            return {
                'success': False,
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0.0
            }
    
    async def _execute_in_process(
        self,
        sandbox: AgentSandbox,
        operation: str,
        code: str,
        timeout: Optional[int]
    ) -> Dict[str, Any]:
        """Execute code in process sandbox."""
        
        # Create temporary file for execution
        code_file = sandbox.working_directory / "execution.py"
        
        try:
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Execute with resource limits
            process = await asyncio.create_subprocess_exec(
                "python", str(code_file),
                cwd=sandbox.working_directory,
                env=sandbox.environment_variables,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=self._set_process_limits(sandbox)
            )
            
            # Store process ID for monitoring
            sandbox.process_id = process.pid
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout or sandbox.resource_limits[ResourceLimit.TIME]
                )
                
                return {
                    'success': process.returncode == 0,
                    'exit_code': process.returncode,
                    'stdout': stdout.decode('utf-8', errors='replace'),
                    'stderr': stderr.decode('utf-8', errors='replace'),
                    'execution_time': 0.0  # TODO: Measure actual time
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                
                return {
                    'success': False,
                    'exit_code': 124,
                    'stdout': '',
                    'stderr': 'Execution timed out',
                    'execution_time': timeout or sandbox.resource_limits[ResourceLimit.TIME]
                }
            
        except Exception as e:
            logger.error(f"Process execution failed: {e}")
            return {
                'success': False,
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0.0
            }
        finally:
            # Clean up
            if code_file.exists():
                code_file.unlink()
            sandbox.process_id = None
    
    async def _execute_direct(
        self,
        sandbox: AgentSandbox,
        operation: str,
        code: str,
        timeout: Optional[int]
    ) -> Dict[str, Any]:
        """Execute code directly (no isolation)."""
        
        # This is for testing/development only - not secure
        logger.warning(f"Executing code without isolation in sandbox {sandbox.sandbox_id}")
        
        try:
            # Change to sandbox directory
            original_cwd = os.getcwd()
            os.chdir(sandbox.working_directory)
            
            # Execute code
            exec_globals = {}
            exec(code, exec_globals)
            
            return {
                'success': True,
                'exit_code': 0,
                'stdout': 'Execution completed',
                'stderr': '',
                'execution_time': 0.0
            }
            
        except Exception as e:
            return {
                'success': False,
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0.0
            }
        finally:
            os.chdir(original_cwd)
    
    def _set_process_limits(self, sandbox: AgentSandbox):
        """Create preexec function to set process resource limits."""
        
        def set_limits():
            try:
                import resource
                
                # Set memory limit
                memory_limit = sandbox.resource_limits[ResourceLimit.MEMORY]
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
                
                # Set CPU time limit
                cpu_limit = int(sandbox.resource_limits[ResourceLimit.TIME])
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
                
                # Set file size limit
                disk_limit = sandbox.resource_limits[ResourceLimit.DISK]
                resource.setrlimit(resource.RLIMIT_FSIZE, (disk_limit, disk_limit))
                
            except Exception as e:
                logger.warning(f"Failed to set resource limits: {e}")
        
        return set_limits
    
    def _check_resource_limits(self, sandbox: AgentSandbox, usage: ResourceUsage) -> bool:
        """Check if current usage is within limits."""
        
        limits = sandbox.resource_limits
        
        if usage.memory_bytes > limits.get(ResourceLimit.MEMORY, float('inf')):
            logger.warning(f"Memory limit exceeded in sandbox {sandbox.sandbox_id}")
            return False
        
        if usage.cpu_percent > limits.get(ResourceLimit.CPU, 100.0):
            logger.warning(f"CPU limit exceeded in sandbox {sandbox.sandbox_id}")
            return False
        
        if usage.execution_time > limits.get(ResourceLimit.TIME, float('inf')):
            logger.warning(f"Time limit exceeded in sandbox {sandbox.sandbox_id}")
            return False
        
        return True
    
    async def destroy_sandbox(self, sandbox_id: str) -> None:
        """Destroy a sandbox and clean up resources."""
        
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return
        
        logger.info(f"Destroying sandbox {sandbox_id}")
        
        try:
            # Stop container if exists
            if sandbox.container_id and self.docker_client:
                try:
                    container = self.docker_client.containers.get(sandbox.container_id)
                    container.stop(timeout=10)
                    container.remove()
                    logger.info(f"Container {sandbox.container_id} stopped and removed")
                except Exception as e:
                    logger.warning(f"Failed to stop container: {e}")
            
            # Kill process if exists
            if sandbox.process_id:
                try:
                    process = psutil.Process(sandbox.process_id)
                    process.terminate()
                    process.wait(timeout=10)
                except Exception as e:
                    logger.warning(f"Failed to terminate process: {e}")
            
            # Clean up filesystem
            if sandbox.working_directory.exists():
                shutil.rmtree(sandbox.working_directory, ignore_errors=True)
            
            # Mark as inactive
            sandbox.is_active = False
            
        except Exception as e:
            logger.error(f"Error destroying sandbox {sandbox_id}: {e}")
        
        # Remove from tracking
        del self.sandboxes[sandbox_id]
    
    async def _monitor_sandboxes(self) -> None:
        """Monitor sandbox health and resource usage."""
        
        while True:
            try:
                current_time = time.time()
                
                # Check for inactive sandboxes
                inactive_sandboxes = []
                for sandbox_id, sandbox in self.sandboxes.items():
                    # Check if sandbox has been inactive for too long
                    if current_time - sandbox.last_activity > 3600:  # 1 hour
                        inactive_sandboxes.append(sandbox_id)
                        continue
                    
                    # Monitor resource usage
                    usage = await self.resource_monitor.get_usage(sandbox_id)
                    if not self._check_resource_limits(sandbox, usage):
                        logger.warning(f"Resource limits exceeded in sandbox {sandbox_id}")
                        # Could implement automatic cleanup here
                
                # Clean up inactive sandboxes
                for sandbox_id in inactive_sandboxes:
                    await self.destroy_sandbox(sandbox_id)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in sandbox monitoring: {e}")
                await asyncio.sleep(60)
    
    def get_sandbox_status(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Get sandbox status information."""
        
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return None
        
        return {
            'sandbox_id': sandbox.sandbox_id,
            'agent_id': sandbox.agent_id,
            'isolation_level': sandbox.isolation_level.value,
            'is_active': sandbox.is_active,
            'created_at': sandbox.created_at,
            'last_activity': sandbox.last_activity,
            'resource_limits': {k.value: v for k, v in sandbox.resource_limits.items()},
            'allowed_operations': list(sandbox.allowed_operations),
            'network_access': sandbox.network_access,
            'container_id': sandbox.container_id,
            'process_id': sandbox.process_id
        }
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all active sandboxes."""
        
        return [
            self.get_sandbox_status(sandbox_id)
            for sandbox_id in self.sandboxes.keys()
        ]
    
    def cleanup_all(self) -> None:
        """Clean up all sandboxes."""
        
        logger.info("Cleaning up all sandboxes")
        
        for sandbox_id in list(self.sandboxes.keys()):
            asyncio.create_task(self.destroy_sandbox(sandbox_id))
        
        # Clean up base directory
        if self.base_sandbox_dir.exists():
            shutil.rmtree(self.base_sandbox_dir, ignore_errors=True)


class ResourceMonitor:
    """Monitors resource usage of sandboxes."""
    
    def __init__(self):
        self.usage_history: Dict[str, List[ResourceUsage]] = {}
    
    async def get_usage(self, sandbox_id: str) -> ResourceUsage:
        """Get current resource usage for a sandbox."""
        
        # This is a simplified implementation
        # In practice, you'd monitor actual process/container metrics
        
        usage = ResourceUsage(
            cpu_percent=0.0,
            memory_bytes=0,
            disk_bytes=0,
            network_bytes=0,
            execution_time=0.0,
            file_operations=0,
            network_operations=0
        )
        
        # Store in history
        if sandbox_id not in self.usage_history:
            self.usage_history[sandbox_id] = []
        
        self.usage_history[sandbox_id].append(usage)
        
        # Keep only recent history
        if len(self.usage_history[sandbox_id]) > 100:
            self.usage_history[sandbox_id] = self.usage_history[sandbox_id][-100:]
        
        return usage
    
    def get_usage_history(self, sandbox_id: str) -> List[ResourceUsage]:
        """Get usage history for a sandbox."""
        return self.usage_history.get(sandbox_id, [])