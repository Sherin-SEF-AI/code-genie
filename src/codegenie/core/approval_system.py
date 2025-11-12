"""
Approval System for managing user approval workflows.

This module provides a centralized approval system for file operations,
command execution, and other actions that require user confirmation.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations that require approval."""
    FILE_CREATE = "file_create"
    FILE_MODIFY = "file_modify"
    FILE_DELETE = "file_delete"
    FILE_MOVE = "file_move"
    COMMAND_EXECUTE = "command_execute"
    BATCH_OPERATION = "batch_operation"
    CUSTOM = "custom"


class ApprovalDecision(Enum):
    """Approval decision types."""
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    AUTO_APPROVED = "auto_approved"


class ConflictType(Enum):
    """Types of conflicts that can occur."""
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    CONCURRENT_EDIT = "concurrent_edit"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    MERGE_CONFLICT = "merge_conflict"


@dataclass
class Operation:
    """Represents an operation that requires approval."""
    id: str
    operation_type: OperationType
    description: str
    target: str  # File path, command, etc.
    risk_level: str = "medium"  # low, medium, high
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    decision: Optional[ApprovalDecision] = None
    decision_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['operation_type'] = self.operation_type.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.decision:
            data['decision'] = self.decision.value
        if self.decision_timestamp:
            data['decision_timestamp'] = self.decision_timestamp.isoformat()
        return data


@dataclass
class UndoPoint:
    """Represents a point in time that can be rolled back to."""
    id: str
    timestamp: datetime
    operations: List[Operation]
    state_snapshot: Dict[str, Any]
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'operations': [op.to_dict() for op in self.operations],
            'state_snapshot': self.state_snapshot,
            'description': self.description,
        }


@dataclass
class Conflict:
    """Represents a conflict between operations."""
    id: str
    conflict_type: ConflictType
    description: str
    affected_operations: List[str]  # Operation IDs
    affected_resources: List[str]  # File paths, etc.
    resolution_suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'conflict_type': self.conflict_type.value,
            'description': self.description,
            'affected_operations': self.affected_operations,
            'affected_resources': self.affected_resources,
            'resolution_suggestions': self.resolution_suggestions,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution': self.resolution,
        }


class ApprovalSystem:
    """
    Centralized approval system for managing user confirmations.
    
    Features:
    - Approval request mechanism for various operation types
    - Batch approval support
    - Preference storage and learning
    - Undo functionality with rollback
    - Conflict detection and resolution
    """
    
    def __init__(
        self,
        preferences_file: Optional[Path] = None,
        auto_approve_safe: bool = True,
        enable_undo: bool = True,
        max_undo_history: int = 50
    ):
        """
        Initialize the approval system.
        
        Args:
            preferences_file: Path to store user preferences
            auto_approve_safe: Whether to auto-approve safe operations
            enable_undo: Whether to enable undo functionality
            max_undo_history: Maximum number of undo points to keep
        """
        self.preferences_file = preferences_file or Path.home() / ".codegenie" / "approval_preferences.json"
        self.auto_approve_safe = auto_approve_safe
        self.enable_undo = enable_undo
        self.max_undo_history = max_undo_history
        
        # Storage
        self.pending_operations: List[Operation] = []
        self.approved_operations: List[Operation] = []
        self.rejected_operations: List[Operation] = []
        self.preferences: Dict[str, Any] = {}
        self.undo_history: List[UndoPoint] = []
        self.conflicts: List[Conflict] = []
        
        # Callbacks
        self.approval_callback: Optional[Callable[[Operation], bool]] = None
        
        # Load preferences
        self._load_preferences()
        
        logger.info("ApprovalSystem initialized")
    
    def request_approval(
        self,
        operation: Operation,
        callback: Optional[Callable[[Operation], bool]] = None
    ) -> ApprovalDecision:
        """
        Request approval for a single operation.
        
        Args:
            operation: Operation to approve
            callback: Optional callback for custom approval logic
            
        Returns:
            ApprovalDecision indicating the result
        """
        logger.info(f"Requesting approval for: {operation.description}")
        
        # Check if auto-approval applies
        if self._should_auto_approve(operation):
            operation.decision = ApprovalDecision.AUTO_APPROVED
            operation.decision_timestamp = datetime.now()
            self.approved_operations.append(operation)
            logger.info(f"Auto-approved: {operation.description}")
            return ApprovalDecision.AUTO_APPROVED
        
        # Check stored preferences
        preference = self._get_preference(operation)
        if preference is not None:
            if preference:
                operation.decision = ApprovalDecision.APPROVED
                operation.decision_timestamp = datetime.now()
                self.approved_operations.append(operation)
                logger.info(f"Approved by preference: {operation.description}")
                return ApprovalDecision.APPROVED
            else:
                operation.decision = ApprovalDecision.REJECTED
                operation.decision_timestamp = datetime.now()
                self.rejected_operations.append(operation)
                logger.info(f"Rejected by preference: {operation.description}")
                return ApprovalDecision.REJECTED
        
        # Use callback if provided
        use_callback = callback or self.approval_callback
        if use_callback:
            try:
                approved = use_callback(operation)
                decision = ApprovalDecision.APPROVED if approved else ApprovalDecision.REJECTED
                operation.decision = decision
                operation.decision_timestamp = datetime.now()
                
                if approved:
                    self.approved_operations.append(operation)
                else:
                    self.rejected_operations.append(operation)
                
                logger.info(f"Decision from callback: {decision.value}")
                return decision
            except Exception as e:
                logger.error(f"Error in approval callback: {e}")
        
        # Add to pending if no decision made
        self.pending_operations.append(operation)
        logger.info(f"Operation pending approval: {operation.description}")
        return ApprovalDecision.DEFERRED
    
    def batch_approval(
        self,
        operations: List[Operation],
        callback: Optional[Callable[[List[Operation]], Dict[str, bool]]] = None
    ) -> Dict[str, ApprovalDecision]:
        """
        Request approval for multiple operations at once.
        
        Args:
            operations: List of operations to approve
            callback: Optional callback that returns dict of operation_id -> approved
            
        Returns:
            Dictionary mapping operation IDs to approval decisions
        """
        logger.info(f"Requesting batch approval for {len(operations)} operations")
        
        decisions = {}
        
        # Use callback if provided
        if callback:
            try:
                approvals = callback(operations)
                for operation in operations:
                    approved = approvals.get(operation.id, False)
                    decision = ApprovalDecision.APPROVED if approved else ApprovalDecision.REJECTED
                    operation.decision = decision
                    operation.decision_timestamp = datetime.now()
                    decisions[operation.id] = decision
                    
                    if approved:
                        self.approved_operations.append(operation)
                    else:
                        self.rejected_operations.append(operation)
                
                return decisions
            except Exception as e:
                logger.error(f"Error in batch approval callback: {e}")
        
        # Process each operation individually
        for operation in operations:
            decision = self.request_approval(operation)
            decisions[operation.id] = decision
        
        return decisions
    
    def approve(self, operation_id: str) -> bool:
        """
        Approve a pending operation.
        
        Args:
            operation_id: ID of the operation to approve
            
        Returns:
            True if successful, False otherwise
        """
        operation = self._find_pending_operation(operation_id)
        if not operation:
            logger.error(f"Operation not found: {operation_id}")
            return False
        
        operation.decision = ApprovalDecision.APPROVED
        operation.decision_timestamp = datetime.now()
        self.pending_operations.remove(operation)
        self.approved_operations.append(operation)
        
        logger.info(f"Approved operation: {operation.description}")
        return True
    
    def reject(self, operation_id: str) -> bool:
        """
        Reject a pending operation.
        
        Args:
            operation_id: ID of the operation to reject
            
        Returns:
            True if successful, False otherwise
        """
        operation = self._find_pending_operation(operation_id)
        if not operation:
            logger.error(f"Operation not found: {operation_id}")
            return False
        
        operation.decision = ApprovalDecision.REJECTED
        operation.decision_timestamp = datetime.now()
        self.pending_operations.remove(operation)
        self.rejected_operations.append(operation)
        
        logger.info(f"Rejected operation: {operation.description}")
        return True
    
    def approve_all_pending(self) -> int:
        """
        Approve all pending operations.
        
        Returns:
            Number of operations approved
        """
        count = len(self.pending_operations)
        
        for operation in self.pending_operations[:]:
            operation.decision = ApprovalDecision.APPROVED
            operation.decision_timestamp = datetime.now()
            self.approved_operations.append(operation)
        
        self.pending_operations.clear()
        
        logger.info(f"Approved {count} pending operations")
        return count
    
    def reject_all_pending(self) -> int:
        """
        Reject all pending operations.
        
        Returns:
            Number of operations rejected
        """
        count = len(self.pending_operations)
        
        for operation in self.pending_operations[:]:
            operation.decision = ApprovalDecision.REJECTED
            operation.decision_timestamp = datetime.now()
            self.rejected_operations.append(operation)
        
        self.pending_operations.clear()
        
        logger.info(f"Rejected {count} pending operations")
        return count
    
    def remember_preference(
        self,
        operation_type: OperationType,
        pattern: str,
        approved: bool
    ) -> None:
        """
        Remember approval preference for future operations.
        
        Args:
            operation_type: Type of operation
            pattern: Pattern to match (e.g., file extension, command prefix)
            approved: Whether to approve or reject
        """
        key = f"{operation_type.value}:{pattern}"
        self.preferences[key] = approved
        self._save_preferences()
        
        logger.info(f"Saved preference: {key} = {approved}")
    
    def get_preference(
        self,
        operation_type: OperationType,
        pattern: str
    ) -> Optional[bool]:
        """
        Get stored preference for an operation pattern.
        
        Args:
            operation_type: Type of operation
            pattern: Pattern to match
            
        Returns:
            True if should approve, False if should reject, None if no preference
        """
        key = f"{operation_type.value}:{pattern}"
        return self.preferences.get(key)
    
    def clear_preferences(self) -> None:
        """Clear all stored preferences."""
        self.preferences.clear()
        self._save_preferences()
        logger.info("Cleared all preferences")
    
    def create_undo_point(
        self,
        operations: List[Operation],
        state_snapshot: Dict[str, Any],
        description: str
    ) -> UndoPoint:
        """
        Create an undo point for rollback.
        
        Args:
            operations: Operations included in this undo point
            state_snapshot: Snapshot of current state
            description: Description of the undo point
            
        Returns:
            Created UndoPoint
        """
        if not self.enable_undo:
            logger.warning("Undo is disabled")
            return None
        
        undo_point = UndoPoint(
            id=f"undo_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            operations=operations,
            state_snapshot=state_snapshot,
            description=description
        )
        
        self.undo_history.append(undo_point)
        
        # Trim history if needed
        if len(self.undo_history) > self.max_undo_history:
            removed = self.undo_history.pop(0)
            logger.debug(f"Removed old undo point: {removed.id}")
        
        logger.info(f"Created undo point: {description}")
        return undo_point
    
    def rollback(
        self,
        undo_point_id: Optional[str] = None,
        rollback_callback: Optional[Callable[[UndoPoint], bool]] = None
    ) -> bool:
        """
        Rollback to an undo point.
        
        Args:
            undo_point_id: ID of undo point (None for most recent)
            rollback_callback: Callback to perform actual rollback
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enable_undo:
            logger.error("Undo is disabled")
            return False
        
        if not self.undo_history:
            logger.error("No undo history available")
            return False
        
        # Find undo point
        if undo_point_id:
            undo_point = next(
                (up for up in self.undo_history if up.id == undo_point_id),
                None
            )
            if not undo_point:
                logger.error(f"Undo point not found: {undo_point_id}")
                return False
        else:
            undo_point = self.undo_history[-1]
        
        logger.info(f"Rolling back to: {undo_point.description}")
        
        # Perform rollback
        if rollback_callback:
            try:
                success = rollback_callback(undo_point)
                if success:
                    # Remove this and all later undo points
                    index = self.undo_history.index(undo_point)
                    self.undo_history = self.undo_history[:index]
                    logger.info("Rollback successful")
                    return True
                else:
                    logger.error("Rollback callback failed")
                    return False
            except Exception as e:
                logger.error(f"Error during rollback: {e}")
                return False
        else:
            logger.warning("No rollback callback provided")
            return False
    
    def get_undo_history(self) -> List[UndoPoint]:
        """Get list of available undo points."""
        return self.undo_history.copy()
    
    def clear_undo_history(self) -> None:
        """Clear undo history."""
        self.undo_history.clear()
        logger.info("Cleared undo history")
    
    def detect_conflicts(
        self,
        operations: List[Operation]
    ) -> List[Conflict]:
        """
        Detect conflicts between operations.
        
        Args:
            operations: Operations to check for conflicts
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Group operations by target
        target_operations: Dict[str, List[Operation]] = {}
        for op in operations:
            target = op.target
            if target not in target_operations:
                target_operations[target] = []
            target_operations[target].append(op)
        
        # Check for conflicts on same target
        for target, ops in target_operations.items():
            if len(ops) > 1:
                # Multiple operations on same target
                conflict = Conflict(
                    id=f"conflict_{datetime.now().timestamp()}",
                    conflict_type=ConflictType.CONCURRENT_EDIT,
                    description=f"Multiple operations on {target}",
                    affected_operations=[op.id for op in ops],
                    affected_resources=[target],
                    resolution_suggestions=[
                        "Review operations and decide which to keep",
                        "Merge operations if possible",
                        "Execute operations sequentially"
                    ]
                )
                conflicts.append(conflict)
        
        # Store conflicts
        self.conflicts.extend(conflicts)
        
        if conflicts:
            logger.warning(f"Detected {len(conflicts)} conflicts")
        
        return conflicts
    
    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str
    ) -> bool:
        """
        Mark a conflict as resolved.
        
        Args:
            conflict_id: ID of the conflict
            resolution: Description of how it was resolved
            
        Returns:
            True if successful, False otherwise
        """
        conflict = next(
            (c for c in self.conflicts if c.id == conflict_id),
            None
        )
        
        if not conflict:
            logger.error(f"Conflict not found: {conflict_id}")
            return False
        
        conflict.resolved = True
        conflict.resolution = resolution
        
        logger.info(f"Resolved conflict: {conflict.description}")
        return True
    
    def get_conflicts(self, resolved: Optional[bool] = None) -> List[Conflict]:
        """
        Get list of conflicts.
        
        Args:
            resolved: Filter by resolved status (None for all)
            
        Returns:
            List of conflicts
        """
        if resolved is None:
            return self.conflicts.copy()
        return [c for c in self.conflicts if c.resolved == resolved]
    
    def get_pending_operations(self) -> List[Operation]:
        """Get list of pending operations."""
        return self.pending_operations.copy()
    
    def get_approved_operations(self) -> List[Operation]:
        """Get list of approved operations."""
        return self.approved_operations.copy()
    
    def get_rejected_operations(self) -> List[Operation]:
        """Get list of rejected operations."""
        return self.rejected_operations.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get approval statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.approved_operations) + len(self.rejected_operations)
        
        return {
            'total_decisions': total,
            'approved': len(self.approved_operations),
            'rejected': len(self.rejected_operations),
            'pending': len(self.pending_operations),
            'approval_rate': len(self.approved_operations) / total if total > 0 else 0.0,
            'preferences_stored': len(self.preferences),
            'undo_points': len(self.undo_history),
            'conflicts': len(self.conflicts),
            'unresolved_conflicts': len([c for c in self.conflicts if not c.resolved]),
        }
    
    def set_approval_callback(
        self,
        callback: Callable[[Operation], bool]
    ) -> None:
        """
        Set the default approval callback.
        
        Args:
            callback: Callback function that takes an Operation and returns bool
        """
        self.approval_callback = callback
        logger.info("Set approval callback")
    
    def _should_auto_approve(self, operation: Operation) -> bool:
        """Check if operation should be auto-approved."""
        if not self.auto_approve_safe:
            return False
        
        # Auto-approve low-risk operations
        if operation.risk_level == "low":
            return True
        
        return False
    
    def _get_preference(self, operation: Operation) -> Optional[bool]:
        """Get stored preference for an operation."""
        # Try exact match first
        key = f"{operation.operation_type.value}:{operation.target}"
        if key in self.preferences:
            return self.preferences[key]
        
        # Try pattern matching
        if operation.operation_type in [OperationType.FILE_CREATE, OperationType.FILE_MODIFY, OperationType.FILE_DELETE]:
            # Match by file extension
            target_path = Path(operation.target)
            ext = target_path.suffix
            if ext:
                key = f"{operation.operation_type.value}:*{ext}"
                if key in self.preferences:
                    return self.preferences[key]
        
        return None
    
    def _find_pending_operation(self, operation_id: str) -> Optional[Operation]:
        """Find a pending operation by ID."""
        return next(
            (op for op in self.pending_operations if op.id == operation_id),
            None
        )
    
    def _load_preferences(self) -> None:
        """Load preferences from file."""
        if not self.preferences_file.exists():
            logger.debug("No preferences file found")
            return
        
        try:
            with open(self.preferences_file, 'r') as f:
                self.preferences = json.load(f)
            logger.info(f"Loaded {len(self.preferences)} preferences")
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
    
    def _save_preferences(self) -> None:
        """Save preferences to file."""
        try:
            self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            logger.debug("Saved preferences")
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")



class FileUndoManager:
    """
    Manages undo operations specifically for file changes.
    
    Provides file-level undo with backup and restore capabilities.
    """
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize file undo manager.
        
        Args:
            backup_dir: Directory to store file backups
        """
        self.backup_dir = backup_dir or Path.home() / ".codegenie" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileUndoManager initialized with backup dir: {self.backup_dir}")
    
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a backup of a file before modification.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file, or None if failed
        """
        if not file_path.exists():
            logger.warning(f"File does not exist, cannot backup: {file_path}")
            return None
        
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}.{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            
            # Copy file to backup
            import shutil
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_path: Path to backup file
            target_path: Path to restore to
            
        Returns:
            True if successful, False otherwise
        """
        if not backup_path.exists():
            logger.error(f"Backup file does not exist: {backup_path}")
            return False
        
        try:
            import shutil
            shutil.copy2(backup_path, target_path)
            logger.info(f"Restored backup to: {target_path}")
            return True
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def delete_backup(self, backup_path: Path) -> bool:
        """
        Delete a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        if not backup_path.exists():
            logger.warning(f"Backup file does not exist: {backup_path}")
            return False
        
        try:
            backup_path.unlink()
            logger.info(f"Deleted backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False
    
    def list_backups(self, file_pattern: Optional[str] = None) -> List[Path]:
        """
        List available backup files.
        
        Args:
            file_pattern: Optional pattern to filter backups
            
        Returns:
            List of backup file paths
        """
        try:
            if file_pattern:
                backups = list(self.backup_dir.glob(f"{file_pattern}*.backup"))
            else:
                backups = list(self.backup_dir.glob("*.backup"))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            return backups
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self, days: int = 30) -> int:
        """
        Clean up backups older than specified days.
        
        Args:
            days: Number of days to keep backups
            
        Returns:
            Number of backups deleted
        """
        import time
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted = 0
        
        try:
            for backup in self.backup_dir.glob("*.backup"):
                if backup.stat().st_mtime < cutoff_time:
                    backup.unlink()
                    deleted += 1
            
            logger.info(f"Cleaned up {deleted} old backups")
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            return deleted


class UndoHistory:
    """
    Manages a history of undo points with persistence.
    """
    
    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize undo history.
        
        Args:
            history_file: Path to store undo history
        """
        self.history_file = history_file or Path.home() / ".codegenie" / "undo_history.json"
        self.history: List[UndoPoint] = []
        self._load_history()
        
        logger.info("UndoHistory initialized")
    
    def add(self, undo_point: UndoPoint) -> None:
        """Add an undo point to history."""
        self.history.append(undo_point)
        self._save_history()
    
    def get_latest(self) -> Optional[UndoPoint]:
        """Get the most recent undo point."""
        return self.history[-1] if self.history else None
    
    def get_by_id(self, undo_id: str) -> Optional[UndoPoint]:
        """Get an undo point by ID."""
        return next((up for up in self.history if up.id == undo_id), None)
    
    def remove(self, undo_id: str) -> bool:
        """Remove an undo point from history."""
        undo_point = self.get_by_id(undo_id)
        if undo_point:
            self.history.remove(undo_point)
            self._save_history()
            return True
        return False
    
    def clear(self) -> None:
        """Clear all undo history."""
        self.history.clear()
        self._save_history()
    
    def get_all(self) -> List[UndoPoint]:
        """Get all undo points."""
        return self.history.copy()
    
    def _load_history(self) -> None:
        """Load history from file."""
        if not self.history_file.exists():
            return
        
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct undo points
            for item in data:
                operations = [
                    Operation(
                        id=op['id'],
                        operation_type=OperationType(op['operation_type']),
                        description=op['description'],
                        target=op['target'],
                        risk_level=op.get('risk_level', 'medium'),
                        metadata=op.get('metadata', {}),
                        timestamp=datetime.fromisoformat(op['timestamp']),
                        decision=ApprovalDecision(op['decision']) if op.get('decision') else None,
                        decision_timestamp=datetime.fromisoformat(op['decision_timestamp']) if op.get('decision_timestamp') else None
                    )
                    for op in item['operations']
                ]
                
                undo_point = UndoPoint(
                    id=item['id'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    operations=operations,
                    state_snapshot=item['state_snapshot'],
                    description=item['description']
                )
                self.history.append(undo_point)
            
            logger.info(f"Loaded {len(self.history)} undo points")
        except Exception as e:
            logger.error(f"Error loading undo history: {e}")
    
    def _save_history(self) -> None:
        """Save history to file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = [up.to_dict() for up in self.history]
            
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved undo history")
        except Exception as e:
            logger.error(f"Error saving undo history: {e}")



class ConflictDetector:
    """
    Advanced conflict detection for operations.
    
    Detects various types of conflicts including:
    - Concurrent edits to the same file
    - File deletions while modifications are pending
    - Dependency conflicts
    - Merge conflicts
    """
    
    def __init__(self):
        """Initialize conflict detector."""
        logger.info("ConflictDetector initialized")
    
    def detect_file_conflicts(
        self,
        operations: List[Operation]
    ) -> List[Conflict]:
        """
        Detect conflicts in file operations.
        
        Args:
            operations: List of file operations
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Group operations by file
        file_ops: Dict[str, List[Operation]] = {}
        for op in operations:
            if op.operation_type in [
                OperationType.FILE_CREATE,
                OperationType.FILE_MODIFY,
                OperationType.FILE_DELETE,
                OperationType.FILE_MOVE
            ]:
                target = op.target
                if target not in file_ops:
                    file_ops[target] = []
                file_ops[target].append(op)
        
        # Check for conflicts
        for file_path, ops in file_ops.items():
            if len(ops) <= 1:
                continue
            
            # Check for delete + modify conflict
            has_delete = any(op.operation_type == OperationType.FILE_DELETE for op in ops)
            has_modify = any(op.operation_type == OperationType.FILE_MODIFY for op in ops)
            
            if has_delete and has_modify:
                conflict = Conflict(
                    id=f"conflict_{datetime.now().timestamp()}",
                    conflict_type=ConflictType.FILE_DELETED,
                    description=f"File {file_path} is being deleted while modifications are pending",
                    affected_operations=[op.id for op in ops],
                    affected_resources=[file_path],
                    resolution_suggestions=[
                        "Cancel the delete operation",
                        "Apply modifications before deleting",
                        "Cancel all modifications"
                    ]
                )
                conflicts.append(conflict)
            
            # Check for multiple modifications
            modify_ops = [op for op in ops if op.operation_type == OperationType.FILE_MODIFY]
            if len(modify_ops) > 1:
                conflict = Conflict(
                    id=f"conflict_{datetime.now().timestamp()}",
                    conflict_type=ConflictType.CONCURRENT_EDIT,
                    description=f"Multiple concurrent modifications to {file_path}",
                    affected_operations=[op.id for op in modify_ops],
                    affected_resources=[file_path],
                    resolution_suggestions=[
                        "Merge the modifications",
                        "Apply modifications sequentially",
                        "Keep only one modification"
                    ]
                )
                conflicts.append(conflict)
            
            # Check for create + create conflict
            create_ops = [op for op in ops if op.operation_type == OperationType.FILE_CREATE]
            if len(create_ops) > 1:
                conflict = Conflict(
                    id=f"conflict_{datetime.now().timestamp()}",
                    conflict_type=ConflictType.FILE_MODIFIED,
                    description=f"Multiple attempts to create {file_path}",
                    affected_operations=[op.id for op in create_ops],
                    affected_resources=[file_path],
                    resolution_suggestions=[
                        "Keep only one create operation",
                        "Merge the content from both operations"
                    ]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def detect_dependency_conflicts(
        self,
        operations: List[Operation]
    ) -> List[Conflict]:
        """
        Detect dependency conflicts between operations.
        
        Args:
            operations: List of operations
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check for operations that depend on each other
        for i, op1 in enumerate(operations):
            for op2 in operations[i+1:]:
                # Check if op2 depends on op1's output
                if self._has_dependency(op1, op2):
                    # Check if they're in wrong order
                    if op1.timestamp > op2.timestamp:
                        conflict = Conflict(
                            id=f"conflict_{datetime.now().timestamp()}",
                            conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                            description=f"Operation depends on another that hasn't executed yet",
                            affected_operations=[op1.id, op2.id],
                            affected_resources=[op1.target, op2.target],
                            resolution_suggestions=[
                                "Reorder operations to respect dependencies",
                                "Execute operations sequentially"
                            ]
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def detect_merge_conflicts(
        self,
        file_path: Path,
        local_content: str,
        remote_content: str
    ) -> Optional[Conflict]:
        """
        Detect merge conflicts in file content.
        
        Args:
            file_path: Path to file
            local_content: Local version of content
            remote_content: Remote version of content
            
        Returns:
            Conflict if detected, None otherwise
        """
        # Simple conflict detection - check if contents differ
        if local_content != remote_content:
            conflict = Conflict(
                id=f"conflict_{datetime.now().timestamp()}",
                conflict_type=ConflictType.MERGE_CONFLICT,
                description=f"Merge conflict in {file_path}",
                affected_operations=[],
                affected_resources=[str(file_path)],
                resolution_suggestions=[
                    "Manually merge the changes",
                    "Keep local version",
                    "Keep remote version",
                    "Use a merge tool"
                ]
            )
            return conflict
        
        return None
    
    def _has_dependency(self, op1: Operation, op2: Operation) -> bool:
        """Check if op2 depends on op1."""
        # Simple heuristic: if op2's target is in op1's metadata
        if 'dependencies' in op2.metadata:
            return op1.target in op2.metadata['dependencies']
        return False


class ConflictResolutionUI:
    """
    Provides UI helpers for conflict resolution.
    """
    
    def __init__(self, colored_output: bool = True):
        """
        Initialize conflict resolution UI.
        
        Args:
            colored_output: Whether to use colored output
        """
        self.colored_output = colored_output
        logger.info("ConflictResolutionUI initialized")
    
    def display_conflict(self, conflict: Conflict) -> None:
        """
        Display a conflict to the user.
        
        Args:
            conflict: Conflict to display
        """
        print(self._format_header("CONFLICT DETECTED"))
        print()
        print(f"Type: {conflict.conflict_type.value}")
        print(f"Description: {conflict.description}")
        print()
        
        if conflict.affected_resources:
            print("Affected Resources:")
            for resource in conflict.affected_resources:
                print(f"  - {resource}")
            print()
        
        if conflict.resolution_suggestions:
            print("Suggested Resolutions:")
            for i, suggestion in enumerate(conflict.resolution_suggestions, 1):
                print(f"  {i}. {suggestion}")
            print()
        
        print(self._format_footer())
    
    def prompt_resolution(
        self,
        conflict: Conflict
    ) -> Optional[str]:
        """
        Prompt user to select a resolution.
        
        Args:
            conflict: Conflict to resolve
            
        Returns:
            Selected resolution or None if cancelled
        """
        self.display_conflict(conflict)
        
        if not conflict.resolution_suggestions:
            return None
        
        while True:
            try:
                choice = input(f"\nSelect resolution (1-{len(conflict.resolution_suggestions)}) or 'c' to cancel: ").strip().lower()
                
                if choice == 'c':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(conflict.resolution_suggestions):
                    return conflict.resolution_suggestions[index]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'c'.")
    
    def display_conflicts_summary(
        self,
        conflicts: List[Conflict]
    ) -> None:
        """
        Display a summary of multiple conflicts.
        
        Args:
            conflicts: List of conflicts
        """
        print(self._format_header(f"CONFLICTS SUMMARY ({len(conflicts)} conflicts)"))
        print()
        
        # Group by type
        by_type: Dict[ConflictType, List[Conflict]] = {}
        for conflict in conflicts:
            if conflict.conflict_type not in by_type:
                by_type[conflict.conflict_type] = []
            by_type[conflict.conflict_type].append(conflict)
        
        for conflict_type, type_conflicts in by_type.items():
            print(f"{conflict_type.value}: {len(type_conflicts)}")
            for conflict in type_conflicts:
                status = "✓ Resolved" if conflict.resolved else "✗ Unresolved"
                print(f"  - {conflict.description} [{status}]")
            print()
        
        print(self._format_footer())
    
    def prompt_merge_resolution(
        self,
        file_path: Path,
        local_content: str,
        remote_content: str
    ) -> Optional[str]:
        """
        Prompt user to resolve a merge conflict.
        
        Args:
            file_path: Path to conflicted file
            local_content: Local version
            remote_content: Remote version
            
        Returns:
            Resolved content or None if cancelled
        """
        print(self._format_header(f"MERGE CONFLICT: {file_path}"))
        print()
        print("Options:")
        print("  1. Keep local version")
        print("  2. Keep remote version")
        print("  3. View diff")
        print("  4. Manual merge")
        print("  c. Cancel")
        print()
        
        while True:
            choice = input("Select option: ").strip().lower()
            
            if choice == '1':
                return local_content
            elif choice == '2':
                return remote_content
            elif choice == '3':
                self._show_diff(local_content, remote_content)
            elif choice == '4':
                return self._manual_merge(local_content, remote_content)
            elif choice == 'c':
                return None
            else:
                print("Invalid choice. Please try again.")
    
    def _show_diff(self, local: str, remote: str) -> None:
        """Show diff between local and remote versions."""
        import difflib
        
        diff = difflib.unified_diff(
            local.splitlines(keepends=True),
            remote.splitlines(keepends=True),
            fromfile='local',
            tofile='remote'
        )
        
        print("\n--- Diff ---")
        for line in diff:
            if self.colored_output:
                if line.startswith('+'):
                    print(f"\033[32m{line}\033[0m", end='')
                elif line.startswith('-'):
                    print(f"\033[31m{line}\033[0m", end='')
                else:
                    print(line, end='')
            else:
                print(line, end='')
        print("\n--- End Diff ---\n")
    
    def _manual_merge(self, local: str, remote: str) -> Optional[str]:
        """Prompt for manual merge."""
        print("\nManual merge mode:")
        print("Enter the merged content (end with Ctrl+D on Unix or Ctrl+Z on Windows):")
        print()
        
        try:
            lines = []
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    break
            
            return '\n'.join(lines)
        except KeyboardInterrupt:
            print("\nMerge cancelled")
            return None
    
    def _format_header(self, text: str) -> str:
        """Format header text."""
        if self.colored_output:
            return f"\033[1;31m{'=' * 60}\033[0m\n\033[1;31m{text}\033[0m\n\033[1;31m{'=' * 60}\033[0m"
        return f"{'=' * 60}\n{text}\n{'=' * 60}"
    
    def _format_footer(self) -> str:
        """Format footer."""
        if self.colored_output:
            return f"\033[1;31m{'=' * 60}\033[0m"
        return '=' * 60
