"""
Permissions and security system for CodeGenie operations.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Available permissions for operations."""
    
    # File operations
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    FILE_EXECUTE = "file:execute"
    
    # Command execution
    COMMAND_EXECUTE = "command:execute"
    COMMAND_SHELL = "command:shell"
    COMMAND_SUDO = "command:sudo"
    
    # Network operations
    NETWORK_HTTP = "network:http"
    NETWORK_SOCKET = "network:socket"
    
    # System operations
    SYSTEM_ENV = "system:env"
    SYSTEM_PROCESS = "system:process"
    
    # Git operations
    GIT_READ = "git:read"
    GIT_WRITE = "git:write"
    GIT_PUSH = "git:push"
    
    # Agent operations
    AGENT_COORDINATE = "agent:coordinate"
    AGENT_DELEGATE = "agent:delegate"
    
    # Workflow operations
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_MODIFY = "workflow:modify"


@dataclass
class PermissionPolicy:
    """Permission policy configuration."""
    
    allowed_permissions: Set[Permission] = field(default_factory=set)
    denied_permissions: Set[Permission] = field(default_factory=set)
    allowed_paths: List[Path] = field(default_factory=list)
    denied_paths: List[Path] = field(default_factory=list)
    allowed_commands: List[str] = field(default_factory=list)
    denied_commands: List[str] = field(default_factory=list)
    require_approval: Set[Permission] = field(default_factory=set)


class PermissionManager:
    """Manages permissions for CodeGenie operations."""
    
    def __init__(self, policy: Optional[PermissionPolicy] = None):
        self.policy = policy or self._get_default_policy()
        self.approval_callbacks: Dict[Permission, callable] = {}
    
    def _get_default_policy(self) -> PermissionPolicy:
        """Get default permission policy."""
        
        return PermissionPolicy(
            allowed_permissions={
                Permission.FILE_READ,
                Permission.FILE_WRITE,
                Permission.COMMAND_EXECUTE,
                Permission.GIT_READ,
                Permission.GIT_WRITE,
                Permission.AGENT_COORDINATE,
                Permission.WORKFLOW_CREATE,
                Permission.WORKFLOW_EXECUTE
            },
            denied_permissions={
                Permission.COMMAND_SUDO,
                Permission.FILE_DELETE,
                Permission.GIT_PUSH
            },
            require_approval={
                Permission.FILE_DELETE,
                Permission.COMMAND_SHELL,
                Permission.GIT_PUSH,
                Permission.WORKFLOW_MODIFY
            },
            denied_commands=[
                "rm -rf /",
                "sudo",
                "chmod 777",
                "mkfs",
                "dd if="
            ]
        )
    
    def check_permission(
        self,
        permission: Permission,
        context: Optional[Dict] = None
    ) -> bool:
        """Check if a permission is allowed."""
        
        # Check if explicitly denied
        if permission in self.policy.denied_permissions:
            logger.warning(f"Permission denied: {permission.value}")
            return False
        
        # Check if explicitly allowed
        if permission in self.policy.allowed_permissions:
            return True
        
        # Default deny
        logger.warning(f"Permission not in allowed list: {permission.value}")
        return False
    
    async def request_permission(
        self,
        permission: Permission,
        context: Optional[Dict] = None
    ) -> bool:
        """Request permission with optional user approval."""
        
        # Check if permission requires approval
        if permission in self.policy.require_approval:
            if permission in self.approval_callbacks:
                return await self.approval_callbacks[permission](context)
            else:
                logger.warning(f"Permission requires approval but no callback set: {permission.value}")
                return False
        
        return self.check_permission(permission, context)
    
    def check_file_access(self, file_path: Path, permission: Permission) -> bool:
        """Check if file access is allowed."""
        
        # Check denied paths
        for denied_path in self.policy.denied_paths:
            if self._is_subpath(file_path, denied_path):
                logger.warning(f"File access denied: {file_path}")
                return False
        
        # Check allowed paths
        if self.policy.allowed_paths:
            for allowed_path in self.policy.allowed_paths:
                if self._is_subpath(file_path, allowed_path):
                    return self.check_permission(permission)
            
            logger.warning(f"File not in allowed paths: {file_path}")
            return False
        
        return self.check_permission(permission)
    
    def check_command(self, command: str) -> bool:
        """Check if command execution is allowed."""
        
        # Check denied commands
        for denied_cmd in self.policy.denied_commands:
            if denied_cmd in command:
                logger.warning(f"Command denied: {command}")
                return False
        
        # Check allowed commands
        if self.policy.allowed_commands:
            for allowed_cmd in self.policy.allowed_commands:
                if command.startswith(allowed_cmd):
                    return self.check_permission(Permission.COMMAND_EXECUTE)
            
            logger.warning(f"Command not in allowed list: {command}")
            return False
        
        return self.check_permission(Permission.COMMAND_EXECUTE)
    
    def register_approval_callback(
        self,
        permission: Permission,
        callback: callable
    ) -> None:
        """Register a callback for permission approval."""
        self.approval_callbacks[permission] = callback
    
    def _is_subpath(self, path: Path, parent: Path) -> bool:
        """Check if path is a subpath of parent."""
        try:
            path.resolve().relative_to(parent.resolve())
            return True
        except ValueError:
            return False
    
    def grant_permission(self, permission: Permission) -> None:
        """Grant a permission."""
        self.policy.allowed_permissions.add(permission)
        self.policy.denied_permissions.discard(permission)
    
    def revoke_permission(self, permission: Permission) -> None:
        """Revoke a permission."""
        self.policy.allowed_permissions.discard(permission)
        self.policy.denied_permissions.add(permission)
    
    def add_allowed_path(self, path: Path) -> None:
        """Add an allowed path."""
        self.policy.allowed_paths.append(path)
    
    def add_denied_path(self, path: Path) -> None:
        """Add a denied path."""
        self.policy.denied_paths.append(path)
    
    def get_policy_summary(self) -> Dict:
        """Get a summary of the current policy."""
        return {
            "allowed_permissions": [p.value for p in self.policy.allowed_permissions],
            "denied_permissions": [p.value for p in self.policy.denied_permissions],
            "require_approval": [p.value for p in self.policy.require_approval],
            "allowed_paths": [str(p) for p in self.policy.allowed_paths],
            "denied_paths": [str(p) for p in self.policy.denied_paths],
            "allowed_commands": self.policy.allowed_commands,
            "denied_commands": self.policy.denied_commands
        }
