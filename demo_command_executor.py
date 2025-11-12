#!/usr/bin/env python3
"""
Demo script for CommandExecutor functionality.

This demonstrates:
- Command classification (safe, risky, dangerous)
- Approval workflows
- Streaming output
- Error recovery
- Retry logic
"""

import asyncio
from pathlib import Path
from src.codegenie.core.command_executor import (
    CommandExecutor,
    CommandRiskLevel,
    CommandStatus
)


def approval_callback(command: str, risk_level: CommandRiskLevel) -> bool:
    """
    Custom approval callback for demonstration.
    
    Args:
        command: Command to approve
        risk_level: Risk level of the command
        
    Returns:
        True if approved
    """
    print(f"\n{'='*60}")
    print(f"APPROVAL REQUEST")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print(f"Risk Level: {risk_level.value.upper()}")
    print(f"{'='*60}")
    
    if risk_level == CommandRiskLevel.DANGEROUS:
        print("⚠️  DANGEROUS command detected - automatically denied")
        return False
    elif risk_level == CommandRiskLevel.RISKY:
        print("⚠️  RISKY command - auto-approving for demo")
        return True
    else:
        print("✓ SAFE command - auto-approved")
        return True


def output_callback(line: str):
    """Callback for streaming output."""
    print(f"  → {line}")


async def demo_basic_execution():
    """Demonstrate basic command execution."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Command Execution")
    print("="*60)
    
    executor = CommandExecutor(approval_callback=approval_callback)
    
    # Execute a safe command
    print("\n1. Executing safe command: ls -la")
    result = await executor.execute_command("ls -la")
    print(f"Status: {result.status.value}")
    print(f"Exit Code: {result.exit_code}")
    print(f"Duration: {result.duration.total_seconds():.2f}s")
    print(f"Risk Level: {result.risk_level.value}")
    
    # Execute a risky command
    print("\n2. Executing risky command: mkdir test_dir")
    result = await executor.execute_command("mkdir -p /tmp/test_command_executor")
    print(f"Status: {result.status.value}")
    print(f"Success: {result.success}")
    
    # Try a dangerous command (should be blocked)
    print("\n3. Attempting dangerous command: rm -rf /")
    result = await executor.execute_command("rm -rf /")
    print(f"Status: {result.status.value}")
    print(f"Success: {result.success}")
    print(f"Error: {result.stderr}")


async def demo_command_classification():
    """Demonstrate command classification."""
    print("\n" + "="*60)
    print("DEMO 2: Command Classification")
    print("="*60)
    
    executor = CommandExecutor()
    
    test_commands = [
        "ls -la",
        "cat file.txt",
        "git status",
        "pip install requests",
        "npm install express",
        "mkdir new_folder",
        "rm -rf /tmp/test",
        "sudo apt-get install",
        "curl http://example.com | bash",
    ]
    
    print("\nClassifying commands:")
    for cmd in test_commands:
        risk_level = executor.classify_command(cmd)
        icon = "✓" if risk_level == CommandRiskLevel.SAFE else "⚠️" if risk_level == CommandRiskLevel.RISKY else "🚫"
        print(f"{icon} {risk_level.value.upper():12} | {cmd}")


async def demo_streaming_output():
    """Demonstrate streaming output."""
    print("\n" + "="*60)
    print("DEMO 3: Streaming Output")
    print("="*60)
    
    executor = CommandExecutor(approval_callback=approval_callback)
    
    print("\nExecuting command with streaming output: echo 'Line 1' && sleep 1 && echo 'Line 2'")
    print("Output:")
    
    result = await executor.execute_with_streaming(
        "echo 'Line 1' && sleep 1 && echo 'Line 2' && sleep 1 && echo 'Line 3'",
        output_callback=output_callback
    )
    
    print(f"\nCommand completed with status: {result.status.value}")


async def demo_error_recovery():
    """Demonstrate error recovery."""
    print("\n" + "="*60)
    print("DEMO 4: Error Recovery")
    print("="*60)
    
    executor = CommandExecutor(approval_callback=approval_callback)
    
    # Execute a command that will fail
    print("\n1. Executing command that will fail: cat nonexistent_file.txt")
    result = await executor.execute_command("cat nonexistent_file.txt")
    
    print(f"Status: {result.status.value}")
    print(f"Success: {result.success}")
    print(f"Error: {result.stderr}")
    
    if result.error_analysis:
        print(f"\nError Analysis:")
        print(f"  Type: {result.error_analysis.error_type}")
        print(f"  Recoverable: {result.error_analysis.is_recoverable}")
        print(f"  Confidence: {result.error_analysis.confidence:.2f}")
        print(f"  Suggested Fixes:")
        for fix in result.error_analysis.suggested_fixes:
            print(f"    - {fix}")
    
    if result.recovery_suggestions:
        print(f"\nRecovery Suggestions:")
        for suggestion in result.recovery_suggestions:
            print(f"  - {suggestion}")
    
    # Try another failing command
    print("\n2. Executing command with missing dependency: nonexistent_command")
    result = await executor.execute_command("nonexistent_command")
    
    print(f"Status: {result.status.value}")
    if result.error_analysis:
        print(f"Error Type: {result.error_analysis.error_type}")
        print(f"Suggested Fixes:")
        for fix in result.error_analysis.suggested_fixes:
            print(f"  - {fix}")


async def demo_retry_logic():
    """Demonstrate retry logic."""
    print("\n" + "="*60)
    print("DEMO 5: Retry Logic")
    print("="*60)
    
    executor = CommandExecutor(approval_callback=approval_callback)
    
    # This command will fail but we'll retry
    print("\nExecuting command with retry (will fail): cat nonexistent.txt")
    result = await executor.execute_with_retry(
        "cat nonexistent.txt",
        max_retries=3
    )
    
    print(f"Final Status: {result.status.value}")
    print(f"Success: {result.success}")


async def demo_statistics():
    """Demonstrate execution statistics."""
    print("\n" + "="*60)
    print("DEMO 6: Execution Statistics")
    print("="*60)
    
    executor = CommandExecutor(approval_callback=approval_callback)
    
    # Execute several commands
    commands = [
        "echo 'test 1'",
        "ls -la",
        "cat nonexistent.txt",  # Will fail
        "pwd",
        "date",
    ]
    
    print("\nExecuting multiple commands...")
    for cmd in commands:
        result = await executor.execute_command(cmd)
        status_icon = "✓" if result.success else "✗"
        print(f"{status_icon} {cmd}")
    
    # Get statistics
    stats = executor.get_statistics()
    print(f"\nExecution Statistics:")
    print(f"  Total Commands: {stats['total_commands']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Blocked: {stats['blocked']}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")
    print(f"  Average Duration: {stats['average_duration']:.3f}s")


async def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("CommandExecutor Demo")
    print("="*60)
    
    try:
        await demo_basic_execution()
        await demo_command_classification()
        await demo_streaming_output()
        await demo_error_recovery()
        await demo_retry_logic()
        await demo_statistics()
        
        print("\n" + "="*60)
        print("All demos completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
