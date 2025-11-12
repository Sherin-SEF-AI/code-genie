#!/usr/bin/env python3
"""
Example: Integrating ApprovalSystem with FileCreator and CommandExecutor

This example shows how to use the centralized ApprovalSystem with
existing file operations and command execution.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import only what we need
import importlib.util

def load_module(name, path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load modules
base_path = Path(__file__).parent / "src" / "codegenie" / "core"
approval_system = load_module("approval_system", base_path / "approval_system.py")


def example_approval_workflow():
    """Example of a complete approval workflow."""
    print("=" * 60)
    print("Example: Complete Approval Workflow")
    print("=" * 60)
    print()
    
    # Create approval system
    system = approval_system.ApprovalSystem(
        auto_approve_safe=True,
        enable_undo=True
    )
    
    # Set up a custom approval callback
    def approval_callback(operation):
        print(f"\n📋 Approval Request:")
        print(f"   Type: {operation.operation_type.value}")
        print(f"   Description: {operation.description}")
        print(f"   Target: {operation.target}")
        print(f"   Risk Level: {operation.risk_level}")
        
        # Auto-approve for demo
        if operation.risk_level == "low":
            print(f"   ✓ Auto-approved (low risk)")
            return True
        elif operation.risk_level == "high":
            print(f"   ⚠ Requires manual approval (high risk)")
            return False
        else:
            print(f"   ℹ Approved (medium risk)")
            return True
    
    system.set_approval_callback(approval_callback)
    
    # Create operations
    operations = [
        approval_system.Operation(
            id="op1",
            operation_type=approval_system.OperationType.FILE_CREATE,
            description="Create new Python module",
            target="src/new_module.py",
            risk_level="low",
            metadata={'size': 1024, 'type': 'python'}
        ),
        approval_system.Operation(
            id="op2",
            operation_type=approval_system.OperationType.FILE_MODIFY,
            description="Update configuration file",
            target="config.json",
            risk_level="medium",
            metadata={'backup': True}
        ),
        approval_system.Operation(
            id="op3",
            operation_type=approval_system.OperationType.FILE_DELETE,
            description="Delete temporary files",
            target="temp/*.tmp",
            risk_level="high",
            metadata={'pattern': '*.tmp'}
        ),
        approval_system.Operation(
            id="op4",
            operation_type=approval_system.OperationType.COMMAND_EXECUTE,
            description="Run tests",
            target="pytest tests/",
            risk_level="low",
            metadata={'timeout': 30}
        ),
    ]
    
    # Request approval for each operation
    print("\n🔍 Processing Operations:")
    print("-" * 60)
    
    for op in operations:
        decision = system.request_approval(op)
    
    print()
    
    # Show results
    print("\n📊 Results:")
    print("-" * 60)
    stats = system.get_statistics()
    print(f"Total decisions: {stats['total_decisions']}")
    print(f"Approved: {stats['approved']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Pending: {stats['pending']}")
    print(f"Approval rate: {stats['approval_rate']:.1%}")
    print()
    
    # Create undo point
    print("\n💾 Creating Undo Point:")
    print("-" * 60)
    approved_ops = system.get_approved_operations()
    if approved_ops:
        undo_point = system.create_undo_point(
            operations=approved_ops,
            state_snapshot={'timestamp': 'now', 'files': ['src/new_module.py', 'config.json']},
            description="Before applying approved operations"
        )
        print(f"✓ Undo point created: {undo_point.id}")
        print(f"  Operations: {len(undo_point.operations)}")
        print(f"  Description: {undo_point.description}")
    print()


def example_conflict_detection():
    """Example of conflict detection."""
    print("=" * 60)
    print("Example: Conflict Detection")
    print("=" * 60)
    print()
    
    system = approval_system.ApprovalSystem()
    detector = approval_system.ConflictDetector()
    
    # Create conflicting operations
    operations = [
        approval_system.Operation(
            id="conflict1",
            operation_type=approval_system.OperationType.FILE_MODIFY,
            description="User A modifies database.py",
            target="database.py",
            risk_level="medium"
        ),
        approval_system.Operation(
            id="conflict2",
            operation_type=approval_system.OperationType.FILE_MODIFY,
            description="User B modifies database.py",
            target="database.py",
            risk_level="medium"
        ),
        approval_system.Operation(
            id="conflict3",
            operation_type=approval_system.OperationType.FILE_DELETE,
            description="Delete database.py",
            target="database.py",
            risk_level="high"
        ),
    ]
    
    print("🔍 Detecting conflicts...")
    print()
    
    # Detect conflicts
    conflicts = detector.detect_file_conflicts(operations)
    
    if conflicts:
        print(f"⚠ Found {len(conflicts)} conflicts:")
        print()
        
        for i, conflict in enumerate(conflicts, 1):
            print(f"Conflict {i}:")
            print(f"  Type: {conflict.conflict_type.value}")
            print(f"  Description: {conflict.description}")
            print(f"  Affected operations: {len(conflict.affected_operations)}")
            print(f"  Affected resources: {', '.join(conflict.affected_resources)}")
            print(f"  Suggestions:")
            for suggestion in conflict.resolution_suggestions:
                print(f"    • {suggestion}")
            print()
        
        # Add to system
        system.conflicts.extend(conflicts)
        
        # Show statistics
        stats = system.get_statistics()
        print(f"📊 Conflict Statistics:")
        print(f"  Total conflicts: {stats['conflicts']}")
        print(f"  Unresolved: {stats['unresolved_conflicts']}")
    else:
        print("✓ No conflicts detected")
    
    print()


def example_preference_learning():
    """Example of preference learning."""
    print("=" * 60)
    print("Example: Preference Learning")
    print("=" * 60)
    print()
    
    system = approval_system.ApprovalSystem()
    
    # Store some preferences
    print("📚 Storing preferences:")
    preferences = [
        (approval_system.OperationType.FILE_CREATE, "*.py", True, "Always approve Python file creation"),
        (approval_system.OperationType.FILE_CREATE, "*.js", True, "Always approve JavaScript file creation"),
        (approval_system.OperationType.FILE_DELETE, "*.log", True, "Always approve log file deletion"),
        (approval_system.OperationType.FILE_DELETE, "*.py", False, "Never auto-approve Python file deletion"),
        (approval_system.OperationType.COMMAND_EXECUTE, "rm -rf *", False, "Never approve dangerous rm commands"),
    ]
    
    for op_type, pattern, approved, description in preferences:
        system.remember_preference(op_type, pattern, approved)
        status = "✓ Approve" if approved else "✗ Reject"
        print(f"  {status}: {op_type.value} {pattern} - {description}")
    
    print()
    
    # Test preference retrieval
    print("🔍 Testing preference retrieval:")
    test_cases = [
        (approval_system.OperationType.FILE_CREATE, "*.py"),
        (approval_system.OperationType.FILE_DELETE, "*.py"),
        (approval_system.OperationType.FILE_DELETE, "*.log"),
        (approval_system.OperationType.COMMAND_EXECUTE, "rm -rf *"),
    ]
    
    for op_type, pattern in test_cases:
        pref = system.get_preference(op_type, pattern)
        if pref is not None:
            status = "✓ Approve" if pref else "✗ Reject"
            print(f"  {status}: {op_type.value} {pattern}")
        else:
            print(f"  ? No preference: {op_type.value} {pattern}")
    
    print()


def example_batch_operations():
    """Example of batch operations."""
    print("=" * 60)
    print("Example: Batch Operations")
    print("=" * 60)
    print()
    
    system = approval_system.ApprovalSystem(auto_approve_safe=False)
    
    # Create batch of operations
    operations = [
        approval_system.Operation(
            id=f"batch_{i}",
            operation_type=approval_system.OperationType.FILE_MODIFY,
            description=f"Refactor module {i}",
            target=f"src/module_{i}.py",
            risk_level="medium"
        )
        for i in range(5)
    ]
    
    print(f"📦 Processing batch of {len(operations)} operations:")
    print()
    
    # Define batch callback
    def batch_callback(ops):
        print(f"  Batch approval requested for {len(ops)} operations")
        print(f"  Operations:")
        for op in ops:
            print(f"    • {op.description}")
        print()
        
        # Approve all for demo
        print(f"  ✓ Approving all operations")
        return {op.id: True for op in ops}
    
    # Request batch approval
    decisions = system.batch_approval(operations, callback=batch_callback)
    
    print()
    print(f"📊 Batch Results:")
    approved = sum(1 for d in decisions.values() if d == approval_system.ApprovalDecision.APPROVED)
    print(f"  Approved: {approved}/{len(operations)}")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "APPROVAL SYSTEM INTEGRATION" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    try:
        example_approval_workflow()
        example_conflict_detection()
        example_preference_learning()
        example_batch_operations()
        
        print("=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        print()
        
        print("Key Features Demonstrated:")
        print("  ✓ Approval request mechanism")
        print("  ✓ Batch approval support")
        print("  ✓ Preference storage and learning")
        print("  ✓ Undo point creation")
        print("  ✓ Conflict detection")
        print("  ✓ Risk-based approval")
        print()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
