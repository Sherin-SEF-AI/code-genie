#!/usr/bin/env python3
"""
Simple test script for CommandExecutor - tests core functionality without full package imports.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import only what we need
from codegenie.core.command_executor import (
    CommandExecutor,
    CommandRiskLevel,
    CommandStatus,
    CommandClassifier
)


async def test_command_classification():
    """Test command classification."""
    print("="*60)
    print("TEST 1: Command Classification")
    print("="*60)
    
    classifier = CommandClassifier()
    
    test_cases = [
        ("ls -la", CommandRiskLevel.SAFE),
        ("cat file.txt", CommandRiskLevel.SAFE),
        ("git status", CommandRiskLevel.SAFE),
        ("mkdir test", CommandRiskLevel.RISKY),
        ("pip install requests", CommandRiskLevel.RISKY),
        ("rm -rf /tmp/test", CommandRiskLevel.DANGEROUS),
        ("sudo apt-get install", CommandRiskLevel.DANGEROUS),
    ]
    
    passed = 0
    failed = 0
    
    for command, expected_level in test_cases:
        actual_level = classifier.classify(command)
        status = "✓" if actual_level == expected_level else "✗"
        if actual_level == expected_level:
            passed += 1
        else:
            failed += 1
        print(f"{status} {command:30} | Expected: {expected_level.value:10} | Got: {actual_level.value}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


async def test_basic_execution():
    """Test basic command execution."""
    print("\n" + "="*60)
    print("TEST 2: Basic Command Execution")
    print("="*60)
    
    executor = CommandExecutor()
    
    # Test safe command
    print("\n1. Testing safe command: echo 'Hello World'")
    result = await executor.execute_command("echo 'Hello World'", require_approval=False)
    
    assert result.status == CommandStatus.SUCCESS, f"Expected SUCCESS, got {result.status}"
    assert result.success, "Command should succeed"
    assert "Hello World" in result.stdout, "Output should contain 'Hello World'"
    assert result.risk_level == CommandRiskLevel.SAFE, "Should be classified as SAFE"
    print(f"✓ Command executed successfully")
    print(f"  Output: {result.stdout.strip()}")
    print(f"  Duration: {result.duration.total_seconds():.3f}s")
    
    # Test command that fails
    print("\n2. Testing failing command: cat nonexistent_file.txt")
    result = await executor.execute_command("cat nonexistent_file.txt", require_approval=False)
    
    assert result.status == CommandStatus.FAILURE, f"Expected FAILURE, got {result.status}"
    assert not result.success, "Command should fail"
    assert result.error_analysis is not None, "Should have error analysis"
    print(f"✓ Command failed as expected")
    print(f"  Error type: {result.error_analysis.error_type}")
    print(f"  Recoverable: {result.error_analysis.is_recoverable}")
    
    return True


async def test_approval_workflow():
    """Test approval workflow."""
    print("\n" + "="*60)
    print("TEST 3: Approval Workflow")
    print("="*60)
    
    # Create executor with approval callback that denies everything
    def deny_all(command: str, risk_level: CommandRiskLevel) -> bool:
        return False
    
    executor = CommandExecutor(approval_callback=deny_all)
    
    print("\n1. Testing command denial")
    result = await executor.execute_command("mkdir test_dir", require_approval=True)
    
    assert result.status == CommandStatus.BLOCKED, f"Expected BLOCKED, got {result.status}"
    assert not result.success, "Command should be blocked"
    print(f"✓ Command blocked as expected")
    
    # Test with approval callback that approves safe commands
    def approve_safe(command: str, risk_level: CommandRiskLevel) -> bool:
        return risk_level == CommandRiskLevel.SAFE
    
    executor2 = CommandExecutor(approval_callback=approve_safe)
    
    print("\n2. Testing safe command approval")
    result = await executor2.execute_command("echo 'test'", require_approval=True)
    
    assert result.status == CommandStatus.SUCCESS, f"Expected SUCCESS, got {result.status}"
    assert result.success, "Safe command should be approved and succeed"
    print(f"✓ Safe command approved and executed")
    
    return True


async def test_streaming_output():
    """Test streaming output."""
    print("\n" + "="*60)
    print("TEST 4: Streaming Output")
    print("="*60)
    
    executor = CommandExecutor()
    
    output_lines = []
    
    def capture_output(line: str):
        output_lines.append(line)
        print(f"  → {line}")
    
    print("\nExecuting command with streaming: echo 'Line 1' && echo 'Line 2'")
    result = await executor.execute_with_streaming(
        "echo 'Line 1' && echo 'Line 2'",
        output_callback=capture_output,
        require_approval=False
    )
    
    assert result.success, "Command should succeed"
    assert len(output_lines) >= 2, "Should capture at least 2 lines"
    print(f"✓ Streaming output captured {len(output_lines)} lines")
    
    return True


async def test_error_recovery():
    """Test error recovery system."""
    print("\n" + "="*60)
    print("TEST 5: Error Recovery")
    print("="*60)
    
    executor = CommandExecutor()
    
    # Test file not found error
    print("\n1. Testing file not found error")
    result = await executor.execute_command("cat missing_file.txt", require_approval=False)
    
    assert not result.success, "Command should fail"
    assert result.error_analysis is not None, "Should have error analysis"
    assert result.error_analysis.error_type == "file_missing", f"Expected file_missing, got {result.error_analysis.error_type}"
    assert len(result.recovery_suggestions) > 0, "Should have recovery suggestions"
    print(f"✓ Error correctly identified as: {result.error_analysis.error_type}")
    print(f"  Recovery suggestions: {len(result.recovery_suggestions)}")
    for suggestion in result.recovery_suggestions:
        print(f"    - {suggestion}")
    
    # Test command not found error
    print("\n2. Testing command not found error")
    result = await executor.execute_command("nonexistent_command_xyz", require_approval=False)
    
    assert not result.success, "Command should fail"
    assert result.error_analysis is not None, "Should have error analysis"
    print(f"✓ Error correctly identified as: {result.error_analysis.error_type}")
    
    return True


async def test_statistics():
    """Test execution statistics."""
    print("\n" + "="*60)
    print("TEST 6: Execution Statistics")
    print("="*60)
    
    executor = CommandExecutor()
    
    # Execute several commands
    await executor.execute_command("echo 'test1'", require_approval=False)
    await executor.execute_command("echo 'test2'", require_approval=False)
    await executor.execute_command("cat nonexistent.txt", require_approval=False)  # Will fail
    
    stats = executor.get_statistics()
    
    assert stats['total_commands'] == 3, f"Expected 3 commands, got {stats['total_commands']}"
    assert stats['successful'] == 2, f"Expected 2 successful, got {stats['successful']}"
    assert stats['failed'] == 1, f"Expected 1 failed, got {stats['failed']}"
    
    print(f"✓ Statistics tracking working correctly")
    print(f"  Total: {stats['total_commands']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CommandExecutor Test Suite")
    print("="*60)
    
    tests = [
        ("Command Classification", test_command_classification),
        ("Basic Execution", test_basic_execution),
        ("Approval Workflow", test_approval_workflow),
        ("Streaming Output", test_streaming_output),
        ("Error Recovery", test_error_recovery),
        ("Statistics", test_statistics),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"\n✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"Test Results: {passed}/{len(tests)} passed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
