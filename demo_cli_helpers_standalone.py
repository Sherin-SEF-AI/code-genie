#!/usr/bin/env python3
"""
Standalone demo for CLI helpers without full dependencies.

This demonstrates the CLI helper utilities in isolation.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

console = Console()


def demo_output_formatting():
    """Demonstrate output formatting."""
    console.print("\n" + "=" * 70, style="bold blue")
    console.print("Output Formatting Demo", style="bold blue")
    console.print("=" * 70 + "\n", style="bold blue")
    
    # Success/Error/Warning/Info messages
    console.print("✅ This is a success message", style="bold green")
    console.print("❌ This is an error message", style="bold red")
    console.print("⚠️  This is a warning message", style="bold yellow")
    console.print("ℹ️  This is an info message", style="bold blue")
    
    # Header
    text = Text()
    text.append("Task Planning", style="bold blue")
    text.append("\nGoal: Add user authentication", style="dim")
    console.print(Panel(text, border_style="blue"))
    
    # Section
    console.print("\n📊 Plan Summary", style="bold blue")
    console.print("─" * 13, style="blue")
    
    # Key-value pairs
    data = {
        "Description": "Add authentication system",
        "Risk Level": "MEDIUM",
        "Estimated Duration": "2 hours",
        "Affected Files": "5",
        "Total Steps": "12",
    }
    
    max_key_length = max(len(str(k)) for k in data.keys())
    for key, value in data.items():
        key_str = str(key).ljust(max_key_length)
        console.print(f"  {key_str} : {value}", style="white")
    
    # Table
    console.print("\n📋 Execution Steps", style="bold blue")
    console.print("─" * 16, style="blue")
    
    table = Table(title="12 Steps")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Description", style="white", width=50)
    table.add_column("Action", style="yellow", width=15)
    table.add_column("Risk", style="red", width=8)
    
    steps = [
        ("1", "Create user model with authentication fields", "CREATE_FILE", "LOW"),
        ("2", "Implement password hashing utilities", "CREATE_FILE", "MEDIUM"),
        ("3", "Add JWT token generation", "MODIFY_FILE", "MEDIUM"),
        ("4", "Create login endpoint", "CREATE_FILE", "LOW"),
        ("5", "Add authentication middleware", "CREATE_FILE", "HIGH"),
    ]
    
    for step in steps:
        table.add_row(*step)
    
    console.print(table)
    
    # List
    console.print("\n📁 Affected Files", style="bold blue")
    console.print("─" * 15, style="blue")
    
    files = [
        "src/models/user.py",
        "src/auth/password.py",
        "src/auth/jwt.py",
        "src/api/auth.py",
        "src/middleware/auth.py",
    ]
    
    for file in files:
        console.print(f"  • {file}", style="cyan")
    
    # Tree
    console.print("\n📂 Project Structure", style="bold blue")
    console.print("─" * 19, style="blue")
    
    tree = Tree("src")
    models = tree.add("📁 models")
    models.add("📄 user.py")
    models.add("📄 __init__.py")
    
    auth = tree.add("📁 auth")
    auth.add("📄 password.py")
    auth.add("📄 jwt.py")
    auth.add("📄 __init__.py")
    
    api = tree.add("📁 api")
    api.add("📄 auth.py")
    api.add("📄 __init__.py")
    
    console.print(tree)


def demo_progress_indicators():
    """Demonstrate progress indicators."""
    console.print("\n" + "=" * 70, style="bold blue")
    console.print("Progress Indicators Demo", style="bold blue")
    console.print("=" * 70 + "\n", style="bold blue")
    
    # Spinner
    console.print("Spinner Progress:", style="bold")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing project context...", total=None)
        time.sleep(1)
        progress.update(task, description="Creating execution plan...")
        time.sleep(1)
        progress.update(task, description="Plan created!")
        time.sleep(0.5)
    
    # Progress bar
    console.print("\nProgress Bar:", style="bold")
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Executing steps...", total=100)
        for i in range(100):
            time.sleep(0.02)
            progress.update(task, advance=1)
    
    console.print("\n✅ Progress complete!", style="bold green")


def demo_command_history():
    """Demonstrate command history."""
    console.print("\n" + "=" * 70, style="bold blue")
    console.print("Command History Demo", style="bold blue")
    console.print("=" * 70 + "\n", style="bold blue")
    
    # Simulate command history
    history = [
        {
            "command": "plan",
            "args": {"goal": "Add user authentication"},
            "timestamp": "2024-01-15T10:30:00",
            "success": True,
            "error": None,
        },
        {
            "command": "scaffold",
            "args": {"type": "python-fastapi", "name": "my-api"},
            "timestamp": "2024-01-15T10:35:00",
            "success": True,
            "error": None,
        },
        {
            "command": "refactor",
            "args": {"target": "main.py", "operation": "rename"},
            "timestamp": "2024-01-15T10:40:00",
            "success": False,
            "error": "File not found",
        },
        {
            "command": "plan",
            "args": {"goal": "Add database migrations"},
            "timestamp": "2024-01-15T10:45:00",
            "success": True,
            "error": None,
        },
    ]
    
    # Recent commands
    console.print("📜 Recent Commands", style="bold blue")
    console.print("─" * 16, style="blue")
    
    table = Table(title="Last 4 commands")
    table.add_column("Timestamp", style="dim", width=20)
    table.add_column("Command", style="cyan", width=15)
    table.add_column("Status", style="green", width=10)
    
    for entry in history:
        status = "✅" if entry['success'] else "❌"
        table.add_row(entry['timestamp'], entry['command'], status)
    
    console.print(table)
    
    # Statistics
    console.print("\n📊 Command Statistics", style="bold blue")
    console.print("─" * 20, style="blue")
    
    total = len(history)
    successful = sum(1 for e in history if e['success'])
    success_rate = successful / total if total > 0 else 0.0
    
    stats_data = {
        "Total Commands": str(total),
        "Success Rate": f"{success_rate:.1%}",
    }
    
    max_key_length = max(len(str(k)) for k in stats_data.keys())
    for key, value in stats_data.items():
        key_str = str(key).ljust(max_key_length)
        console.print(f"  {key_str} : {value}", style="white")
    
    # Most used commands
    console.print("\n🔝 Most Used Commands", style="bold blue")
    console.print("─" * 20, style="blue")
    
    command_counts = {}
    for entry in history:
        cmd = entry['command']
        command_counts[cmd] = command_counts.get(cmd, 0) + 1
    
    most_used = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
    
    table = Table(title="Top Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Count", style="green")
    
    for cmd, count in most_used:
        table.add_row(cmd, str(count))
    
    console.print(table)


def demo_cli_commands():
    """Demonstrate new CLI commands."""
    console.print("\n" + "=" * 70, style="bold blue")
    console.print("New CLI Commands Demo", style="bold blue")
    console.print("=" * 70 + "\n", style="bold blue")
    
    # Header
    text = Text()
    text.append("Available Commands", style="bold blue")
    text.append("\nNew commands added in Task 13", style="dim")
    console.print(Panel(text, border_style="blue"))
    
    # Commands
    console.print("\n📝 Command Reference", style="bold blue")
    console.print("─" * 18, style="blue")
    
    commands = [
        ("codegenie plan", "Create a detailed execution plan for a task"),
        ("codegenie scaffold", "Scaffold a new project with proper structure"),
        ("codegenie refactor", "Refactor code across multiple files"),
        ("codegenie history", "Show command history and statistics"),
        ("codegenie interactive", "Start interactive mode with guided prompts"),
    ]
    
    for cmd, description in commands:
        console.print(f"\n[bold cyan]{cmd}[/bold cyan]")
        console.print(f"  {description}", style="dim")
    
    # Examples
    console.print("\n\n💡 Example Usage", style="bold blue")
    console.print("─" * 15, style="blue")
    
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
    
    # Options
    console.print("\n\n⚙️  Command Options", style="bold blue")
    console.print("─" * 17, style="blue")
    
    table = Table(title="Common Options")
    table.add_column("Option", style="cyan", width=20)
    table.add_column("Description", style="white", width=40)
    
    options = [
        ("--path, -p", "Specify project path"),
        ("--save", "Save plan to file"),
        ("--execute, -e", "Execute plan after creation"),
        ("--preview", "Preview changes before applying"),
        ("--debug", "Enable debug mode"),
    ]
    
    for option, desc in options:
        table.add_row(option, desc)
    
    console.print(table)


def main():
    """Run all demos."""
    console.print("\n" + "=" * 70, style="bold magenta")
    console.print("🧞 CodeGenie CLI Integration Demo (Task 13)", style="bold magenta")
    console.print("=" * 70 + "\n", style="bold magenta")
    
    try:
        # Run demos
        demo_output_formatting()
        demo_progress_indicators()
        demo_command_history()
        demo_cli_commands()
        
        # Summary
        console.print("\n" + "=" * 70, style="bold green")
        console.print("Demo Summary", style="bold green")
        console.print("=" * 70 + "\n", style="bold green")
        
        console.print("ℹ️  Task 13 Implementation Complete!", style="bold blue")
        
        console.print("\n✅ Completed Features", style="bold green")
        console.print("─" * 20, style="green")
        
        features = [
            "✅ Task 13.1: CLI commands (plan, scaffold, refactor)",
            "✅ Task 13.2: Enhanced CLI UX",
            "  • Interactive prompts with validation",
            "  • Progress indicators (spinner, bar, multi-task)",
            "  • Colored and formatted output",
            "  • Command history management",
        ]
        
        for feature in features:
            console.print(f"  {feature}", style="green")
        
        console.print("\n\n🚀 Try It Out", style="bold blue")
        console.print("─" * 11, style="blue")
        console.print("\nRun these commands to test the new features:", style="bold")
        console.print("  $ codegenie plan 'Create a REST API'", style="cyan")
        console.print("  $ codegenie scaffold python-fastapi my-api", style="cyan")
        console.print("  $ codegenie history --stats", style="cyan")
        console.print("  $ codegenie interactive", style="cyan")
        
        console.print("\n\n🎉 All demos completed successfully!", style="bold green")
        
    except KeyboardInterrupt:
        console.print("\n\n⚠️  Demo interrupted by user", style="yellow")
    except Exception as e:
        console.print(f"\n\n❌ Error: {e}", style="red")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
