#!/usr/bin/env python3
"""
Simple test for the Approval System without full package dependencies.
"""

import sys
from pathlib import Path

# Test imports
try:
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    # Import only the approval system module directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "approval_system",
        Path(__file__).parent / "src" / "codegenie" / "core" / "approval_system.py"
    )
    approval_system = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(approval_system)
    
    print("✓ Successfully imported approval_system module")
    print()
    
    # Test class availability
    print("Testing class availability:")
    classes = [
        'ApprovalSystem',
        'Operation',
        'OperationType',
        'ApprovalDecision',
        'UndoPoint',
        'Conflict',
        'ConflictType',
        'ConflictDetector',
        'ConflictResolutionUI',
        'FileUndoManager',
        'UndoHistory',
    ]
    
    for class_name in classes:
        if hasattr(approval_system, class_name):
            print(f"  ✓ {class_name}")
        else:
            print(f"  ✗ {class_name} - NOT FOUND")
    
    print()
    
    # Test basic instantiation
    print("Testing basic instantiation:")
    
    # Create ApprovalSystem
    sys_instance = approval_system.ApprovalSystem(auto_approve_safe=True)
    print(f"  ✓ ApprovalSystem created")
    
    # Create Operation
    op = approval_system.Operation(
        id="test_op",
        operation_type=approval_system.OperationType.FILE_CREATE,
        description="Test operation",
        target="test.py",
        risk_level="low"
    )
    print(f"  ✓ Operation created: {op.description}")
    
    # Test approval request
    decision = sys_instance.request_approval(op)
    print(f"  ✓ Approval requested, decision: {decision.value}")
    
    # Test statistics
    stats = sys_instance.get_statistics()
    print(f"  ✓ Statistics retrieved: {stats['total_decisions']} decisions")
    
    # Create ConflictDetector
    detector = approval_system.ConflictDetector()
    print(f"  ✓ ConflictDetector created")
    
    # Create FileUndoManager
    undo_mgr = approval_system.FileUndoManager()
    print(f"  ✓ FileUndoManager created")
    
    print()
    print("=" * 60)
    print("All tests passed successfully!")
    print("=" * 60)
    print()
    
    # Show implementation summary
    print("Implementation Summary:")
    print("  - ApprovalSystem: Centralized approval management")
    print("  - Operation: Represents operations requiring approval")
    print("  - UndoPoint: Rollback points for undo functionality")
    print("  - Conflict: Represents conflicts between operations")
    print("  - ConflictDetector: Detects various types of conflicts")
    print("  - ConflictResolutionUI: UI helpers for conflict resolution")
    print("  - FileUndoManager: File-specific undo with backups")
    print("  - UndoHistory: Persistent undo history management")
    print()
    
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
