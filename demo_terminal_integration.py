#!/usr/bin/env python3
"""
Demo script for Terminal Integration features.

This demonstrates:
- Natural language command processing
- Interactive terminal session
- Shell integration
- Command history and context awareness
"""

import asyncio
from pathlib import Path

from src.codegenie.integrations.terminal_integration import TerminalInterface
from src.codegenie.integrations.interactive_terminal import InteractiveTerminalSession
from src.codegenie.integrations.shell_integration import ShellIntegrationManager


async def demo_natural_language_commands():
    """Demonstrate natural language command processing."""
    print("=" * 60)
    print("Demo: Natural Language Command Processing")
    print("=" * 60)
    print()
    
    terminal = TerminalInterface()
    
    # Example commands
    commands = [
        "list files in current directory",
        "show git status",
        "create a file called demo.txt",
    ]
    
    for cmd in commands:
        print(f"\n📝 Command: {cmd}")
        print("-" * 60)
        
        result = await terminal.process_natural_language_command(cmd, auto_execute=True)
        
        if result.get('success'):
            print("✅ Success!")
            if result.get('parsed'):
                parsed = result['parsed']
                print(f"   Intent: {parsed.intent.value}")
                print(f"   Executable: {parsed.executable_command}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        print()


async def demo_command_parsing():
    """Demonstrate command parsing capabilities."""
    print("=" * 60)
    print("Demo: Command Parsing")
    print("=" * 60)
    print()
    
    from src.codegenie.integrations.terminal_integration import NaturalLanguageCommandParser
    
    parser = NaturalLanguageCommandParser()
    
    test_commands = [
        "create a file called test.py",
        "show git status",
        "run all tests",
        "find files containing 'TODO'",
        "delete old logs",
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Command: {cmd}")
        parsed = await parser.parse_command(cmd)
        
        print(f"   Intent: {parsed.intent.value}")
        print(f"   Action: {parsed.action}")
        print(f"   Confidence: {parsed.confidence:.1%}")
        if parsed.parameters:
            print(f"   Parameters: {parsed.parameters}")
        if parsed.executable_command:
            print(f"   Executable: {parsed.executable_command}")
        if parsed.requires_confirmation:
            print(f"   ⚠️  Requires confirmation")


def demo_shell_integration():
    """Demonstrate shell integration features."""
    print("\n" + "=" * 60)
    print("Demo: Shell Integration")
    print("=" * 60)
    print()
    
    shell_manager = ShellIntegrationManager()
    
    # Get shell info
    info = shell_manager.get_shell_info()
    print("🐚 Shell Information:")
    print(f"   Type: {info['shell_type']}")
    print(f"   Path: {info['shell_path']}")
    print(f"   Working Directory: {info['working_directory']}")
    print(f"   Config File: {info['config_file']}")
    print(f"   Aliases: {info['num_aliases']}")
    print(f"   PATH Directories: {info['path_dirs']}")
    
    # Get environment
    print("\n🌍 Environment:")
    env = shell_manager.get_environment()
    print(f"   Shell Type: {env.shell_type.value}")
    print(f"   Working Directory: {env.working_directory}")
    print(f"   Environment Variables: {len(env.environment_variables)}")
    print(f"   PATH Directories: {len(env.path_dirs)}")
    
    # Demonstrate alias syntax
    print("\n📝 Alias Syntax Examples:")
    print(f"   Bash: {shell_manager.integration.get_alias_syntax('ll', 'ls -la')}")
    print(f"   Function: {shell_manager.integration.get_function_syntax('greet', 'echo Hello')}")


def demo_output_formatting():
    """Demonstrate output formatting."""
    print("\n" + "=" * 60)
    print("Demo: Output Formatting")
    print("=" * 60)
    print()
    
    from src.codegenie.integrations.terminal_integration import TerminalOutputFormatter
    from src.codegenie.core.tool_executor import CommandResult, CommandStatus
    
    formatter = TerminalOutputFormatter()
    
    # Success example
    print("✅ Success Example:")
    success_result = CommandResult(
        command='ls -la',
        exit_code=0,
        stdout='total 8\ndrwxr-xr-x  2 user user 4096 Jan 1 12:00 .\ndrwxr-xr-x 10 user user 4096 Jan 1 12:00 ..',
        stderr='',
        duration=0.05,
        success=True,
        status=CommandStatus.SUCCESS
    )
    print(formatter.format_command_result(success_result))
    
    # Error example
    print("\n❌ Error Example:")
    error_result = CommandResult(
        command='invalid_command',
        exit_code=127,
        stdout='',
        stderr='bash: invalid_command: command not found',
        duration=0.01,
        success=False,
        status=CommandStatus.FAILURE
    )
    print(formatter.format_command_result(error_result))


def demo_context_management():
    """Demonstrate context management."""
    print("\n" + "=" * 60)
    print("Demo: Context Management")
    print("=" * 60)
    print()
    
    from src.codegenie.integrations.terminal_integration import TerminalContextManager
    from src.codegenie.core.tool_executor import CommandResult, CommandStatus
    
    context_mgr = TerminalContextManager()
    
    # Add some commands to history
    commands = [
        ('ls -la', True),
        ('git status', True),
        ('python test.py', False),
    ]
    
    for cmd, success in commands:
        result = CommandResult(
            command=cmd,
            exit_code=0 if success else 1,
            stdout='output',
            stderr='' if success else 'error',
            duration=0.1,
            success=success,
            status=CommandStatus.SUCCESS if success else CommandStatus.FAILURE
        )
        context_mgr.add_to_history(cmd, result)
    
    # Show history
    print("📜 Command History:")
    history = context_mgr.get_history()
    for i, cmd in enumerate(history, 1):
        print(f"   {i}. {cmd}")
    
    # Show context
    print("\n📊 Context Information:")
    context = context_mgr.get_context()
    print(f"   Working Directory: {context.working_directory}")
    print(f"   Shell Type: {context.shell_type}")
    print(f"   Session ID: {context.session_id}")
    print(f"   Commands in History: {len(context.history)}")
    
    # Show last result
    last_result = context_mgr.get_last_result()
    if last_result:
        print(f"\n📋 Last Command Result:")
        print(f"   Command: {last_result.command}")
        print(f"   Success: {last_result.success}")
        print(f"   Duration: {last_result.duration:.3f}s")


async def main():
    """Run all demos."""
    print("\n" + "🧞 " * 20)
    print("CodeGenie Terminal Integration Demo")
    print("🧞 " * 20 + "\n")
    
    # Run demos
    await demo_natural_language_commands()
    await demo_command_parsing()
    demo_shell_integration()
    demo_output_formatting()
    demo_context_management()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("To try the interactive terminal, run:")
    print("  python -c 'from src.codegenie.integrations.interactive_terminal import InteractiveTerminalSession; import asyncio; asyncio.run(InteractiveTerminalSession().start())'")
    print()


if __name__ == '__main__':
    asyncio.run(main())
