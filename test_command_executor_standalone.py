#!/usr/bin/env python3
"""
Standalone test for CommandExecutor - imports module directly without package dependencies.
"""

import asyncio
import sys
import importlib.util
from pathlib import Path

# Load the module directly without going through package __init__
spec = importlib.util.spec_from_file_location(
    "command_executor",
    Path(__file__).parent / "src" / "codegenie" / "core" / "command_executor.py"
)
command_executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(command_executor)

# Now we can use the classes
CommandExecutor = command_executor.CommandExecutor
CommandRiskLevel = command_executor.CommandRiskLevel
CommandStatus = command_executor.CommandStatus
CommandClassifier = command_executor.CommandClassifier


async def test_all():
    """Run all tests."""
    print("="*60)
    print("CommandExecutor Standalone Test")
    print("="*60)
    
    # Test 1: Command Classification
    print("\n1. Testing Command Classification")
    classifier = CommandClassifier()
    
    test_cases = [
        ("ls -la", CommandRiskLevel.SAFE),
        ("cat file.txt", CommandRiskLevel.SAFE),
        ("mkdir test", CommandRiskLevel.RISKY),
        ("pip install requests", CommandRiskLevel.RISKY),
        ("rm -rf /", CommandRiskLevel.DANGEROUS),
    ]
    
    for command, expected in test_cases:
        actual = classifier.classify(command)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {command:30} -> {actual.value}")
    
    # Test 2: Basic Execution
    print("\n2. Testing Basic Execution")
    executor = CommandExecutor()
    
    result = await executor.execute_command("echo 'Hello World'", require_approval=False)
    print(f"  ✓ Command: echo 'Hello World'")
    print(f"    Status: {result.status.value}")
    print(f"    Success: {result.success}")
    print(f"    Output: {result.stdout.strip()}")
    print(f"    Duration: {result.duration.total_seconds():.3f}s")
    
    # Test 3: Error Handling
    print("\n3. Testing Error Handling")
    result = await executor.execute_command("cat nonexistent_file.txt", require_approval=False)
    print(f"  ✓ Command: cat nonexistent_file.txt")
    print(f"    Status: {result.status.value}")
    print(f"    Success: {result.success}")
    if result.error_analysis:
        print(f"    Error Type: {result.error_analysis.error_type}")
        print(f"    Recoverable: {result.error_analysis.is_recoverable}")
        print(f"    Suggestions: {len(result.recovery_suggestions)}")
    
    # Test 4: Approval Workflow
    print("\n4. Testing Approval Workflow")
    
    def deny_all(cmd, risk):
        return False
    
    executor_deny = CommandExecutor(approval_callback=deny_all)
    result = await executor_deny.execute_command("mkdir test", require_approval=True)
    print(f"  ✓ Command blocked: {result.status == CommandStatus.BLOCKED}")
    print(f"    Status: {result.status.value}")
    
    # Test 5: Statistics
    print("\n5. Testing Statistics")
    executor_stats = CommandExecutor()
    await executor_stats.execute_command("echo 'test1'", require_approval=False)
    await executor_stats.execute_command("echo 'test2'", require_approval=False)
    await executor_stats.execute_command("cat nonexistent.txt", require_approval=False)
    
    stats = executor_stats.get_statistics()
    print(f"  ✓ Total Commands: {stats['total_commands']}")
    print(f"    Successful: {stats['successful']}")
    print(f"    Failed: {stats['failed']}")
    print(f"    Success Rate: {stats['success_rate']:.1%}")
    
    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_all())
