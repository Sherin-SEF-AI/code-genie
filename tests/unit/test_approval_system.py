"""
Unit tests for Approval System.

Tests approval workflows, batch approval, preference storage,
undo functionality, and conflict detection.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.codegenie.core.approval_system import (
    ApprovalSystem, Operation, OperationType, ApprovalDecision,
    UndoPoint, Conflict, ConflictType, FileUndoManager
)


class TestApprovalSystem:
    """Test suite for Approval System."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def approval_system(self, temp_dir):
        """Create an approval system instance."""
        prefs_file = temp_dir / "preferences.json"
        return ApprovalSystem(preferences_file=prefs_file)
    
    @pytest.fixture
    def sample_operation(self):
        """Create a sample operation."""
        return Operation(
            id="op_1",
            operation_type=OperationType.FILE_CREATE,
            description="Create test file",
            target="test.txt",
            risk_level="low"
        )
    
    def test_initialization(self, approval_system):
        """Test approval system initialization."""
        assert approval_system is not None
        assert len(approval_system.pending_operations) == 0
        assert len(approval_system.approved_operations) == 0
        assert approval_system.auto_approve_safe is True
    
    def test_request_approval_auto_approve(self, approval_system, sample_operation):
        """Test auto-approval of safe operations."""
        decision = approval_system.request_approval(sample_operation)
        
        assert decision == ApprovalDecision.AUTO_APPROVED
        assert sample_operation in approval_system.approved_operations
    
    def test_request_approval_with_callback(self, approval_system):
        """Test approval with callback."""
        operation = Operation(
            id="op_1",
            operation_type=OperationType.COMMAND_EXECUTE,
            description="Run command",
            target="rm file.txt",
            risk_level="high"
        )
        
        def callback(op):
            return op.risk_level != "high"
        
        decision = approval_system.request_approval(operation, callback=callback)
        
        assert decision == ApprovalDecision.REJECTED
        assert operation in approval_system.rejected_operations
    
    def test_approve_pending_operation(self, approval_system):
        """Test approving a pending operation."""
        operation = Operation(
            id="op_1",
            operation_type=OperationType.FILE_MODIFY,
            description="Modify file",
            target="test.txt",
            risk_level="medium"
        )
        
        # Disable auto-approve to make it pending
        approval_system.auto_approve_safe = False
        approval_system.request_approval(operation)
        
        assert operation in approval_system.pending_operations
        
        success = approval_system.approve(operation.id)
        
        assert success
        assert operation not in approval_system.pending_operations
        assert operation in approval_system.approved_operations
    
    def test_reject_pending_operation(self, approval_system):
        """Test rejecting a pending operation."""
        operation = Operation(
            id="op_1",
            operation_type=OperationType.FILE_DELETE,
            description="Delete file",
            target="test.txt",
            risk_level="medium"
        )
        
        approval_system.auto_approve_safe = False
        approval_system.request_approval(operation)
        
        success = approval_system.reject(operation.id)
        
        assert success
        assert operation not in approval_system.pending_operations
        assert operation in approval_system.rejected_operations
    
    def test_batch_approval(self, approval_system):
        """Test batch approval of operations."""
        operations = [
            Operation(
                id=f"op_{i}",
                operation_type=OperationType.FILE_CREATE,
                description=f"Create file {i}",
                target=f"file{i}.txt",
                risk_level="low"
            )
            for i in range(3)
        ]
        
        def callback(ops):
            return {op.id: True for op in ops}
        
        decisions = approval_system.batch_approval(operations, callback=callback)
        
        assert len(decisions) == 3
        assert all(d == ApprovalDecision.APPROVED for d in decisions.values())
    
    def test_approve_all_pending(self, approval_system):
        """Test approving all pending operations."""
        approval_system.auto_approve_safe = False
        
        for i in range(3):
            op = Operation(
                id=f"op_{i}",
                operation_type=OperationType.FILE_CREATE,
                description=f"Create file {i}",
                target=f"file{i}.txt",
                risk_level="medium"
            )
            approval_system.request_approval(op)
        
        count = approval_system.approve_all_pending()
        
        assert count == 3
        assert len(approval_system.pending_operations) == 0
        assert len(approval_system.approved_operations) == 3
    
    def test_reject_all_pending(self, approval_system):
        """Test rejecting all pending operations."""
        approval_system.auto_approve_safe = False
        
        for i in range(3):
            op = Operation(
                id=f"op_{i}",
                operation_type=OperationType.FILE_CREATE,
                description=f"Create file {i}",
                target=f"file{i}.txt",
                risk_level="medium"
            )
            approval_system.request_approval(op)
        
        count = approval_system.reject_all_pending()
        
        assert count == 3
        assert len(approval_system.pending_operations) == 0
        assert len(approval_system.rejected_operations) == 3
    
    def test_remember_preference(self, approval_system):
        """Test remembering approval preference."""
        approval_system.remember_preference(
            OperationType.FILE_CREATE,
            "*.py",
            True
        )
        
        preference = approval_system.get_preference(
            OperationType.FILE_CREATE,
            "*.py"
        )
        
        assert preference is True
    
    def test_clear_preferences(self, approval_system):
        """Test clearing all preferences."""
        approval_system.remember_preference(
            OperationType.FILE_CREATE,
            "*.py",
            True
        )
        
        approval_system.clear_preferences()
        
        assert len(approval_system.preferences) == 0
    
    def test_create_undo_point(self, approval_system, sample_operation):
        """Test creating an undo point."""
        undo_point = approval_system.create_undo_point(
            operations=[sample_operation],
            state_snapshot={'files': ['test.txt']},
            description="Before file creation"
        )
        
        assert isinstance(undo_point, UndoPoint)
        assert len(approval_system.undo_history) == 1
        assert undo_point.description == "Before file creation"
    
    def test_rollback(self, approval_system, sample_operation):
        """Test rollback to undo point."""
        undo_point = approval_system.create_undo_point(
            operations=[sample_operation],
            state_snapshot={'files': []},
            description="Initial state"
        )
        
        def rollback_callback(up):
            return True
        
        success = approval_system.rollback(
            undo_point_id=undo_point.id,
            rollback_callback=rollback_callback
        )
        
        assert success
        assert len(approval_system.undo_history) == 0
    
    def test_get_undo_history(self, approval_system, sample_operation):
        """Test getting undo history."""
        approval_system.create_undo_point(
            operations=[sample_operation],
            state_snapshot={},
            description="Point 1"
        )
        approval_system.create_undo_point(
            operations=[sample_operation],
            state_snapshot={},
            description="Point 2"
        )
        
        history = approval_system.get_undo_history()
        
        assert len(history) == 2
    
    def test_clear_undo_history(self, approval_system, sample_operation):
        """Test clearing undo history."""
        approval_system.create_undo_point(
            operations=[sample_operation],
            state_snapshot={},
            description="Point 1"
        )
        
        approval_system.clear_undo_history()
        
        assert len(approval_system.undo_history) == 0
    
    def test_detect_conflicts(self, approval_system):
        """Test conflict detection."""
        operations = [
            Operation(
                id="op_1",
                operation_type=OperationType.FILE_MODIFY,
                description="Modify file",
                target="test.txt",
                risk_level="low"
            ),
            Operation(
                id="op_2",
                operation_type=OperationType.FILE_DELETE,
                description="Delete file",
                target="test.txt",
                risk_level="medium"
            )
        ]
        
        conflicts = approval_system.detect_conflicts(operations)
        
        assert len(conflicts) > 0
        assert conflicts[0].conflict_type == ConflictType.CONCURRENT_EDIT
    
    def test_resolve_conflict(self, approval_system):
        """Test resolving a conflict."""
        operations = [
            Operation(
                id="op_1",
                operation_type=OperationType.FILE_MODIFY,
                description="Modify file",
                target="test.txt",
                risk_level="low"
            ),
            Operation(
                id="op_2",
                operation_type=OperationType.FILE_MODIFY,
                description="Modify file again",
                target="test.txt",
                risk_level="low"
            )
        ]
        
        conflicts = approval_system.detect_conflicts(operations)
        conflict = conflicts[0]
        
        success = approval_system.resolve_conflict(
            conflict.id,
            "Merged changes manually"
        )
        
        assert success
        assert conflict.resolved
        assert conflict.resolution == "Merged changes manually"
    
    def test_get_conflicts(self, approval_system):
        """Test getting conflicts."""
        operations = [
            Operation(
                id="op_1",
                operation_type=OperationType.FILE_MODIFY,
                description="Modify file",
                target="test.txt",
                risk_level="low"
            ),
            Operation(
                id="op_2",
                operation_type=OperationType.FILE_MODIFY,
                description="Modify file again",
                target="test.txt",
                risk_level="low"
            )
        ]
        
        approval_system.detect_conflicts(operations)
        
        all_conflicts = approval_system.get_conflicts()
        unresolved = approval_system.get_conflicts(resolved=False)
        
        assert len(all_conflicts) > 0
        assert len(unresolved) > 0
    
    def test_get_statistics(self, approval_system):
        """Test getting approval statistics."""
        approval_system.auto_approve_safe = False
        
        # Create some operations
        for i in range(5):
            op = Operation(
                id=f"op_{i}",
                operation_type=OperationType.FILE_CREATE,
                description=f"Create file {i}",
                target=f"file{i}.txt",
                risk_level="medium"
            )
            approval_system.request_approval(op)
        
        # Approve some
        approval_system.approve("op_0")
        approval_system.approve("op_1")
        
        # Reject some
        approval_system.reject("op_2")
        
        stats = approval_system.get_statistics()
        
        assert stats['total_decisions'] == 3
        assert stats['approved'] == 2
        assert stats['rejected'] == 1
        assert stats['pending'] == 2
    
    def test_operation_to_dict(self, sample_operation):
        """Test Operation serialization."""
        op_dict = sample_operation.to_dict()
        
        assert op_dict['id'] == "op_1"
        assert op_dict['operation_type'] == "file_create"
        assert op_dict['target'] == "test.txt"
    
    def test_undo_point_to_dict(self, sample_operation):
        """Test UndoPoint serialization."""
        undo_point = UndoPoint(
            id="undo_1",
            timestamp=datetime.now(),
            operations=[sample_operation],
            state_snapshot={'files': []},
            description="Test undo point"
        )
        
        up_dict = undo_point.to_dict()
        
        assert up_dict['id'] == "undo_1"
        assert up_dict['description'] == "Test undo point"
        assert len(up_dict['operations']) == 1
    
    def test_conflict_to_dict(self):
        """Test Conflict serialization."""
        conflict = Conflict(
            id="conflict_1",
            conflict_type=ConflictType.CONCURRENT_EDIT,
            description="Multiple edits",
            affected_operations=["op_1", "op_2"],
            affected_resources=["test.txt"]
        )
        
        conflict_dict = conflict.to_dict()
        
        assert conflict_dict['id'] == "conflict_1"
        assert conflict_dict['conflict_type'] == "concurrent_edit"
        assert len(conflict_dict['affected_operations']) == 2


class TestFileUndoManager:
    """Test suite for File Undo Manager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def undo_manager(self, temp_dir):
        """Create a file undo manager."""
        backup_dir = temp_dir / "backups"
        return FileUndoManager(backup_dir=backup_dir)
    
    def test_initialization(self, undo_manager):
        """Test file undo manager initialization."""
        assert undo_manager is not None
        assert undo_manager.backup_dir.exists()
    
    def test_create_backup(self, undo_manager, temp_dir):
        """Test creating a file backup."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Original content")
        
        backup_path = undo_manager.create_backup(test_file)
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "Original content"
    
    def test_create_backup_nonexistent(self, undo_manager, temp_dir):
        """Test creating backup of nonexistent file."""
        test_file = temp_dir / "nonexistent.txt"
        
        backup_path = undo_manager.create_backup(test_file)
        
        assert backup_path is None
    
    def test_restore_backup(self, undo_manager, temp_dir):
        """Test restoring a file from backup."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Original content")
        
        backup_path = undo_manager.create_backup(test_file)
        
        # Modify the file
        test_file.write_text("Modified content")
        
        # Restore from backup
        success = undo_manager.restore_backup(backup_path, test_file)
        
        assert success
        assert test_file.read_text() == "Original content"
    
    def test_delete_backup(self, undo_manager, temp_dir):
        """Test deleting a backup file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Content")
        
        backup_path = undo_manager.create_backup(test_file)
        
        success = undo_manager.delete_backup(backup_path)
        
        assert success
        assert not backup_path.exists()
    
    def test_list_backups(self, undo_manager, temp_dir):
        """Test listing backup files."""
        # Create multiple backups
        for i in range(3):
            test_file = temp_dir / f"test{i}.txt"
            test_file.write_text(f"Content {i}")
            undo_manager.create_backup(test_file)
        
        backups = undo_manager.list_backups()
        
        assert len(backups) == 3
    
    def test_list_backups_with_pattern(self, undo_manager, temp_dir):
        """Test listing backups with pattern filter."""
        # Create backups for different files
        test1 = temp_dir / "test1.txt"
        test1.write_text("Content 1")
        undo_manager.create_backup(test1)
        
        test2 = temp_dir / "other.txt"
        test2.write_text("Content 2")
        undo_manager.create_backup(test2)
        
        backups = undo_manager.list_backups("test1.txt")
        
        assert len(backups) >= 1
        assert all("test1.txt" in str(b) for b in backups)
