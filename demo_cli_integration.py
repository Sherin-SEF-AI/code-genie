#!/usr/bin/env python3
"""
Demo script for CLI Integration (Task 13).

This demonstrates:
- New CLI commands (plan, scaffold, refactor)
- Enhanced CLI UX with interactive prompts
- Progress indicators and colored output
- Command history management
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from codegenie.ui.cli_helpers import (
    CommandHistory,
    InteractivePrompt,
    ProgressIndicator,
    OutputFormatter,
)

console = Console()


def demo_cli_helpers():
    """Demonstrate CLI helper utilities."""
    console.print("\n" + "=" * 70, style="bold blue")
    console.print("CLI Helpers Demo", style="bold blue")
    console.print("=" * 70 + "\n", style="bold blue")
    
    # Initialize helpers
    output_formatter = OutputFormatter(console)
    interactive_prompt = InteractivePrompt(console)
    progress_indicator = ProgressIndicator(console)
    command_history = CommandHistory()
    
    # 1. Output Formatting
    output_formatter.header("Output Formatting Demo", "Various styled outputs")
    
    output_formatter.success("This is a success message")
    output_formatter.error("This is an error message")
    output_formatter.warning("This is a warning message")
    output_formatter.info("This is an info message")
    
    # 2. Tables
    output_formatter.section("Table Display")
    output_formatter.table(
        "Sample Data",
        ["Name", "Status", "Count"],
        [
            ["Task 1", "✅ Complete", "10"],
            ["Task 2", "⏳ In Progress", "5"],
            ["Task 3", "❌ Failed", "0"],
        ],
        column_styles=["cyan", "white", "green"]
    )
    
    # 3. Lists
    output_formatter.section("List Display")
    output_formatter.list_items(
        ["Item 1", "Item 2", "Item 3"],
        title="Sample Items",
        style="cyan"
    )
    
    # 4. Key-Value Pairs
    output_formatter.section("Key-Value Display")
    output_formatter.key_value({
        "Project": "CodeGenie",
        "Version": "2.0.0",
        "Status": "Active",
        "Features": "CLI Integration",
    })
    
    # 5. Tree Structure
    output_formatter.section("Tree Display")
    output_formatter.tree("Project Structure", {
        "src": {
            "codegenie": {
                "core": ["agent.py", "config.py"],
                "ui": ["cli.py", "terminal.py"],
            }
        },
        "tests": ["test_cli.py", "test_agent.py"],
    })
    
    # 6. Code Display
    output_formatter.section("Code Display")
    sample_code = '''def hello_world():
    """A simple function."""
    print("Hello, World!")
    return True'''
    
    output_formatter.code(sample_code, "python")
    
    # 7. Progress Indicators
    output_formatter.section("Progress Indicators")
    
    console.print("\nSpinner Progress:", style="bold")
    with progress_indicator.spinner("Processing...") as progress:
        task = progress.add_task("Loading data...", total=None)
        import time
        time.sleep(1)
        progress.update(task, description="Processing complete!")
        time.sleep(0.5)
    
    console.print("\nProgress Bar:", style="bold")
    with progress_indicator.bar("Processing items...") as progress:
        task = progress.add_task("Processing...", total=100)
        for i in range(100):
            time.sleep(0.01)
            progress.update(task, advance=1)
    
    # 8. Command History
    output_formatter.section("Command History")
    
    # Add some sample commands
    command_history.add_command("plan", {"goal": "Add feature"}, success=True)
    command_history.add_command("scaffold", {"type": "python-fastapi"}, success=True)
    command_history.add_command("refactor", {"target": "main.py"}, success=False, error="File not found")
    
    # Show recent commands
    recent = command_history.get_recent(3)
    rows = []
    for entry in recent:
        status = "✅" if entry['success'] else "❌"
        rows.append([entry['command'], status, entry['timestamp'][:19]])
    
    output_formatter.table(
        "Recent Commands",
        ["Command", "Status", "Timestamp"],
        rows,
        column_styles=["cyan", "green", "dim"]
    )
    
    # Show statistics
    stats = command_history.get_stats()
    output_formatter.key_value({
        "Total Commands": stats['total_commands'],
        "Success Rate": f"{stats['success_rate']:.1%}",
    }, title="Command Statistics")
    
    output_formatter.success("\n✅ CLI Helpers Demo Complete!")


def demo_interactive_prompts():
    """Demonstrate interactive prompts (non-interactive for demo)."""
    console.print("\n" + "=" * 70, style="bold blue")
    console.print("Interactive Prompts Demo", style="bold blue")
    console.print("=" * 70 + "\n", style="bold blue")
    
    output_formatter = OutputFormatter(console)
    
    output_formatter.info("Interactive prompts are available in the CLI:")
    
    features = [
        "Text input with validation",
        "Single choice selection",
        "Multiple choice selection",
        "Yes/No confirmation",
        "Numeric input with range validation",
    ]
    
    output_formatter.list_items(features, title="Available Prompt Types", style="cyan")
    
    output_formatter.section("Example Usage")
    
    console.print("\nText Input:", style="bold")
    console.print('  interactive_prompt.ask_text("Enter project name")', style="dim")
    
    console.print("\nChoice Selection:", style="bold")
    console.print('  interactive_prompt.ask_choice("Select type", ["Python", "JavaScript"])', style="dim")
    
    console.print("\nConfirmation:", style="bold")
    console.print('  interactive_prompt.ask_confirm("Continue?")', style="dim")
    
    output_formatter.success("\n✅ Interactive Prompts Demo Complete!")


def demo_cli_commands():
    """Demonstrate new CLI commands."""
    console.print("\n" + "=" * 70, style="bold blue")
    console.print("New CLI Commands Demo", style="bold blue")
    console.print("=" * 70 + "\n", style="bold blue")
    
    output_formatter = OutputFormatter(console)
    
    output_formatter.header("Available Commands", "New commands added in Task 13")
    
    commands = {
        "codegenie plan": "Create a detailed execution plan for a task",
        "codegenie scaffold": "Scaffold a new project with proper structure",
        "codegenie refactor": "Refactor code across multiple files",
        "codegenie history": "Show command history and statistics",
        "codegenie interactive": "Start interactive mode with guided prompts",
    }
    
    output_formatter.section("Command Reference")
    
    for cmd, description in commands.items():
        console.print(f"\n[bold cyan]{cmd}[/bold cyan]")
        console.print(f"  {description}", style="dim")
    
    output_formatter.section("Example Usage")
    
    examples = [
        ("Plan a task", "codegenie plan 'Add user authentication'"),
        ("Scaffold project", "codegenie scaffold python-fastapi my-api"),
        ("Refactor code", "codegenie refactor main.py rename --name new_main.py"),
        ("View history", "codegenie history --count 10"),
        ("Interactive mode", "codegenie interactive"),
    ]
    
    for title, command in examples:
        console.print(f"\n[bold]{title}:[/bold]")
        console.print(f"  $ {command}", style="green")
    
    output_formatter.section("Command Options")
    
    options_table = [
        ["--path, -p", "Specify project path"],
        ["--save", "Save plan to file"],
        ["--execute, -e", "Execute plan after creation"],
        ["--preview", "Preview changes before applying"],
        ["--debug", "Enable debug mode"],
    ]
    
    output_formatter.table(
        "Common Options",
        ["Option", "Description"],
        options_table,
        column_styles=["cyan", "white"]
    )
    
    output_formatter.success("\n✅ CLI Commands Demo Complete!")


def main():
    """Run all demos."""
    console.print("\n" + "=" * 70, style="bold magenta")
    console.print("🧞 CodeGenie CLI Integration Demo (Task 13)", style="bold magenta")
    console.print("=" * 70 + "\n", style="bold magenta")
    
    try:
        # Run demos
        demo_cli_helpers()
        demo_interactive_prompts()
        demo_cli_commands()
        
        # Summary
        console.print("\n" + "=" * 70, style="bold green")
        console.print("Demo Summary", style="bold green")
        console.print("=" * 70 + "\n", style="bold green")
        
        output_formatter = OutputFormatter(console)
        
        output_formatter.info("Task 13 Implementation Complete!")
        
        completed_features = [
            "✅ Task 13.1: CLI commands (plan, scaffold, refactor)",
            "✅ Task 13.2: Enhanced CLI UX",
            "  • Interactive prompts with validation",
            "  • Progress indicators (spinner, bar, multi-task)",
            "  • Colored and formatted output",
            "  • Command history management",
        ]
        
        output_formatter.list_items(completed_features, title="Completed Features", style="green")
        
        output_formatter.section("Try It Out")
        console.print("\nRun these commands to test the new features:", style="bold")
        console.print("  $ codegenie plan 'Create a REST API'", style="cyan")
        console.print("  $ codegenie scaffold python-fastapi my-api", style="cyan")
        console.print("  $ codegenie history --stats", style="cyan")
        console.print("  $ codegenie interactive", style="cyan")
        
        output_formatter.success("\n🎉 All demos completed successfully!")
        
    except KeyboardInterrupt:
        console.print("\n\n⚠️  Demo interrupted by user", style="yellow")
    except Exception as e:
        console.print(f"\n\n❌ Error: {e}", style="red")
        console.print_exception()


if __name__ == "__main__":
    main()
