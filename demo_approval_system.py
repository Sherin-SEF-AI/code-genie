#!/usr/bin/env python3
"""
Demo script for the Approval System.

This demonstrates:
- Approval request mechanism
- Batch approval support
- Preference storage
- Undo functionality
- Conflict detection
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.approval_system import (
    ApprovalSystem,
    Operation,
    OperationType,
    ApprovalDecision,
    ConflictDetector,
    ConflictResolutionUI,
    FileUndoManager,
)


def demo_basic_approval():
    """Demonstrate basic approval workflow."""
    print("=" * 60)
    print("Demo 1: Basic Approval Workflow")
    print("=" * 60)
    print()
    
    # Create approval system
    approval_system = ApprovalSystem(auto_approve_safe=True)
    
    # Create some operations
    op1 = Operation(
        id="op1",
        operation_type=OperationType.FILE_CREATE,
        description="Create new Python file",
        target="example.py",
        risk_level="low"
    )
    
    op2 = Operation(
        id="op2",
        operation_type=OperationType.FILE_DELETE,
        description="Delete configuration file",
        target="config.json",
        risk_level="high"
    )
    
    op3 = Operation(
        id="op3",
        operation_type=OperationType.COMMAND_EXECUTE,
        description="Install dependencies",
        target="pip install requests",
        risk_level="medium"
    )
    
    # Request approval for each
    print("Requesting approval for operations...")
    print()
    
    decision1 = approval_system.request_approval(op1)
    print(f"Operation 1: {op1.description}")
    print(f"  Decision: {decision1.value}")
    print()
    
    decision2 = approval_system.request_approval(op2)
    print(f"Operation 2: {op2.description}")
    print(f"  Decision: {decision2.value}")
    print()
    
    decision3 = approval_system.request_approval(op3)
    print(f"Operation 3: {op3.description}")
    print(f"  Decision: {decision3.value}")
    print()
    
    # Show statistics
    stats = approval_system.get_statistics()
    print("Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()


def demo_batch_approval():
    """Demonstrate batch approval."""
    print("=" * 60)
    print("Demo 2: Batch Approval")
    print("=" * 60)
    print()
    
    approval_system = ApprovalSystem(auto_approve_safe=False)
    
    # Create multiple operations
    operations = [
        Operation(
            id=f"batch_op{i}",
            operation_type=OperationType.FILE_MODIFY,
            description=f"Modify file {i}",
            target=f"file{i}.py",
            risk_level="medium"
        )
        for i in range(5)
    ]
    
    # Define a batch approval callback
    def batch_callback(ops):
        print(f"Batch approval requested for {len(ops)} operations:")
        for op in ops:
            print(f"  - {op.description}")
        print()
        
        # Auto-approve all for demo
        return {op.id: True for op in ops}
    
    # Request batch approval
    decisions = approval_system.batch_approval(operations, callback=batch_callback)
    
    print("Batch approval results:")
    for op_id, decision in decisions.items():
        print(f"  {op_id}: {decision.value}")
    print()


def demo_preferences():
    """Demonstrate preference storage."""
    print("=" * 60)
    print("Demo 3: Preference Storage")
    print("=" * 60)
    print()
    
    approval_system = ApprovalSystem()
    
    # Remember some preferences
    print("Storing preferences...")
    approval_system.remember_preference(
        OperationType.FILE_CREATE,
        "*.py",
        True
    )
    approval_system.remember_preference(
        OperationType.FILE_DELETE,
        "*.log",
        True
    )
    approval_system.remember_preference(
        OperationType.COMMAND_EXECUTE,
        "rm *",
        False
    )
    print()
    
    # Check preferences
    print("Checking preferences:")
    pref1 = approval_system.get_preference(OperationType.FILE_CREATE, "*.py")
    print(f"  FILE_CREATE *.py: {pref1}")
    
    pref2 = approval_system.get_preference(OperationType.FILE_DELETE, "*.log")
    print(f"  FILE_DELETE *.log: {pref2}")
    
    pref3 = approval_system.get_preference(OperationType.COMMAND_EXECUTE, "rm *")
    print(f"  COMMAND_EXECUTE rm *: {pref3}")
    print()


def demo_undo_functionality():
    """Demonstrate undo functionality."""
    print("=" * 60)
    print("Demo 4: Undo Functionality")
    print("=" * 60)
    print()
    
    approval_system = ApprovalSystem(enable_undo=True)
    
    # Create some operations
    operations = [
        Operation(
            id=f"undo_op{i}",
            operation_type=OperationType.FILE_MODIFY,
            description=f"Modify file {i}",
            target=f"file{i}.py",
            risk_level="medium"
        )
        for i in range(3)
    ]
    
    # Create undo point
    print("Creating undo point...")
    undo_point = approval_system.create_undo_point(
        operations=operations,
        state_snapshot={'files': ['file0.py', 'file1.py', 'file2.py']},
        description="Before batch modifications"
    )
    print(f"  Undo point created: {undo_point.id}")
    print(f"  Description: {undo_point.description}")
    print()
    
    # Show undo history
    history = approval_system.get_undo_history()
    print(f"Undo history: {len(history)} points")
    for up in history:
        print(f"  - {up.description} ({up.timestamp})")
    print()
    
    # Demonstrate rollback (with mock callback)
    def rollback_callback(undo_point):
        print(f"Rolling back to: {undo_point.description}")
        print(f"  Restoring {len(undo_point.operations)} operations")
        return True
    
    print("Performing rollback...")
    success = approval_system.rollback(rollback_callback=rollback_callback)
    print(f"  Rollback successful: {success}")
    print()


def demo_conflict_detection():
    """Demonstrate conflict detection."""
    print("=" * 60)
    print("Demo 5: Conflict Detection")
    print("=" * 60)
    print()
    
    approval_system = ApprovalSystem()
    detector = ConflictDetector()
    
    # Create conflicting operations
    operations = [
        Operation(
            id="conflict_op1",
            operation_type=OperationType.FILE_MODIFY,
            description="Modify config.json",
            target="config.json",
            risk_level="medium"
        ),
        Operation(
            id="conflict_op2",
            operation_type=OperationType.FILE_MODIFY,
            description="Another modification to config.json",
            target="config.json",
            risk_level="medium"
        ),
        Operation(
            id="conflict_op3",
            operation_type=OperationType.FILE_DELETE,
            description="Delete config.json",
            target="config.json",
            risk_level="high"
        ),
    ]
    
    # Detect conflicts
    print("Detecting conflicts...")
    conflicts = detector.detect_file_conflicts(operations)
    
    print(f"Found {len(conflicts)} conflicts:")
    for conflict in conflicts:
        print(f"\n  Conflict: {conflict.description}")
        print(f"  Type: {conflict.conflict_type.value}")
        print(f"  Affected operations: {len(conflict.affected_operations)}")
        print(f"  Suggestions:")
        for suggestion in conflict.resolution_suggestions:
            print(f"    - {suggestion}")
    print()
    
    # Add conflicts to approval system
    approval_system.conflicts.extend(conflicts)
    
    # Show conflict statistics
    stats = approval_system.get_statistics()
    print(f"Total conflicts: {stats['conflicts']}")
    print(f"Unresolved conflicts: {stats['unresolved_conflicts']}")
    print()


def demo_file_undo_manager():
    """Demonstrate file undo manager."""
    print("=" * 60)
    print("Demo 6: File Undo Manager")
    print("=" * 60)
    print()
    
    undo_manager = FileUndoManager()
    
    # Create a test file
    test_file = Path("test_undo_file.txt")
    test_file.write_text("Original content")
    print(f"Created test file: {test_file}")
    print()
    
    # Create backup
    print("Creating backup...")
    backup_path = undo_manager.create_backup(test_file)
    if backup_path:
        print(f"  Backup created: {backup_path}")
    print()
    
    # Modify the file
    test_file.write_text("Modified content")
    print("Modified test file")
    print()
    
    # List backups
    backups = undo_manager.list_backups("test_undo_file.txt")
    print(f"Available backups: {len(backups)}")
    for backup in backups:
        print(f"  - {backup.name}")
    print()
    
    # Restore backup
    if backup_path:
        print("Restoring from backup...")
        success = undo_manager.restore_backup(backup_path, test_file)
        print(f"  Restore successful: {success}")
        
        # Verify content
        content = test_file.read_text()
        print(f"  Restored content: {content}")
        print()
    
    # Cleanup
    test_file.unlink()
    if backup_path and backup_path.exists():
        undo_manager.delete_backup(backup_path)
    print("Cleanup complete")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "APPROVAL SYSTEM DEMO" + " " * 23 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    try:
        demo_basic_approval()
        demo_batch_approval()
        demo_preferences()
        demo_undo_functionality()
        demo_conflict_detection()
        demo_file_undo_manager()
        
        print("=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
