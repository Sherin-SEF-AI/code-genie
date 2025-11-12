#!/usr/bin/env python3
"""
Demo of the Planning Agent functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.tree import Tree

from codegenie.core.planning_agent import PlanningAgent, RiskLevel, StepStatus


console = Console()


def print_plan_summary(plan):
    """Print a summary of the execution plan."""
    
    console.print()
    console.print(Panel(
        f"[bold cyan]{plan.description}[/bold cyan]\n\n"
        f"Plan ID: {plan.id}\n"
        f"Total Steps: {len(plan.steps)}\n"
        f"Estimated Duration: {plan.estimated_duration.total_seconds():.0f}s\n"
        f"Risk Level: {plan.risk_level.value}\n"
        f"Complexity: {plan.complexity.complexity_level if plan.complexity else 'Unknown'}",
        title="📋 Execution Plan",
        border_style="cyan"
    ))


def print_steps_tree(plan):
    """Print steps as a tree structure."""
    
    tree = Tree("📝 [bold]Execution Steps[/bold]")
    
    for i, step in enumerate(plan.steps, 1):
        # Determine icon based on risk level
        if step.risk_level == RiskLevel.SAFE:
            icon = "✅"
        elif step.risk_level == RiskLevel.LOW:
            icon = "🟢"
        elif step.risk_level == RiskLevel.MEDIUM:
            icon = "🟡"
        elif step.risk_level == RiskLevel.HIGH:
            icon = "🟠"
        else:
            icon = "🔴"
        
        # Create step node
        step_text = f"{icon} Step {i}: {step.description}"
        step_node = tree.add(step_text)
        
        # Add details
        step_node.add(f"Action: {step.action_type.value}")
        step_node.add(f"Duration: ~{step.estimated_duration.total_seconds():.0f}s")
        step_node.add(f"Risk: {step.risk_level.value}")
        
        if step.dependencies:
            step_node.add(f"Depends on: {', '.join(step.dependencies)}")
    
    console.print(tree)


def print_complexity_analysis(complexity):
    """Print complexity analysis."""
    
    if not complexity:
        return
    
    console.print()
    console.print(Panel(
        f"Total Steps: {complexity.total_steps}\n"
        f"Estimated Duration: {complexity.estimated_duration.total_seconds():.0f}s\n"
        f"Risk Score: {complexity.risk_score:.2f}/1.0\n"
        f"Complexity Level: [bold]{complexity.complexity_level}[/bold]\n"
        f"Confidence: {complexity.confidence:.0%}",
        title="📊 Complexity Analysis",
        border_style="yellow"
    ))


def print_validation_results(validation):
    """Print validation results."""
    
    if not validation:
        return
    
    console.print()
    
    if validation.is_valid:
        console.print("✅ [bold green]Plan is valid[/bold green]")
    else:
        console.print("❌ [bold red]Plan has errors[/bold red]")
    
    if validation.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in validation.errors:
            console.print(f"  • {error}")
    
    if validation.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in validation.warnings:
            console.print(f"  • {warning}")
    
    if validation.suggestions:
        console.print("\n[bold cyan]Suggestions:[/bold cyan]")
        for suggestion in validation.suggestions:
            console.print(f"  • {suggestion}")


def demo_project_creation():
    """Demo creating a new project."""
    
    console.print("\n" + "="*80)
    console.print("[bold magenta]Demo 1: Create a New FastAPI Project[/bold magenta]")
    console.print("="*80)
    
    agent = PlanningAgent()
    
    # Create a plan
    plan = agent.create_plan(
        "Create a new FastAPI project with authentication",
        context={'language': 'python', 'framework': 'fastapi'}
    )
    
    # Display the plan
    print_plan_summary(plan)
    print_steps_tree(plan)
    print_complexity_analysis(plan.complexity)
    print_validation_results(plan.validation)


def demo_refactoring():
    """Demo refactoring code."""
    
    console.print("\n" + "="*80)
    console.print("[bold magenta]Demo 2: Refactor Code to Use Async/Await[/bold magenta]")
    console.print("="*80)
    
    agent = PlanningAgent()
    
    # Create a plan
    plan = agent.create_plan(
        "Refactor the database module to use async/await patterns",
        context={'files': ['src/database.py'], 'language': 'python'}
    )
    
    # Display the plan
    print_plan_summary(plan)
    print_steps_tree(plan)
    print_complexity_analysis(plan.complexity)
    print_validation_results(plan.validation)


def demo_bug_fix():
    """Demo fixing a bug."""
    
    console.print("\n" + "="*80)
    console.print("[bold magenta]Demo 3: Fix Memory Leak Bug[/bold magenta]")
    console.print("="*80)
    
    agent = PlanningAgent()
    
    # Create a plan
    plan = agent.create_plan(
        "Fix the memory leak in the cache manager",
        context={'issue': 'memory_leak', 'component': 'cache_manager'}
    )
    
    # Display the plan
    print_plan_summary(plan)
    print_steps_tree(plan)
    print_complexity_analysis(plan.complexity)
    print_validation_results(plan.validation)


def demo_execution():
    """Demo executing a plan."""
    
    console.print("\n" + "="*80)
    console.print("[bold magenta]Demo 4: Execute a Plan[/bold magenta]")
    console.print("="*80)
    
    agent = PlanningAgent()
    
    # Create a simple plan
    plan = agent.create_plan(
        "Add a new feature to the API",
        context={'feature': 'user_profile'}
    )
    
    print_plan_summary(plan)
    
    # Approval callback
    def approve_step(step):
        if step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            console.print(f"\n⚠️  [yellow]Step requires approval:[/yellow] {step.description}")
            console.print(f"   Risk Level: {step.risk_level.value}")
            return console.input("   Approve? (y/n): ").lower() == 'y'
        return True
    
    # Execute with progress
    console.print("\n[bold]Executing plan...[/bold]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("Executing steps...", total=len(plan.steps))
        
        def progress_callback(step, current, total):
            progress.update(task, completed=current, description=f"Step {current}/{total}: {step.description}")
        
        result = agent.execute_plan(plan, approve_step, progress_callback)
    
    # Display results
    console.print()
    console.print(Panel(
        f"Success: {'✅ Yes' if result.success else '❌ No'}\n"
        f"Completed: {result.completed_steps}\n"
        f"Failed: {result.failed_steps}\n"
        f"Skipped: {result.skipped_steps}\n"
        f"Duration: {result.total_duration.total_seconds():.1f}s",
        title="📊 Execution Results",
        border_style="green" if result.success else "red"
    ))


def main():
    """Run all demos."""
    
    console.print(Panel(
        "[bold cyan]Planning Agent Demo[/bold cyan]\n\n"
        "Demonstrating intelligent task decomposition and execution planning",
        title="🤖 CodeGenie Planning Agent",
        border_style="cyan"
    ))
    
    try:
        # Run demos
        demo_project_creation()
        demo_refactoring()
        demo_bug_fix()
        demo_execution()
        
        console.print("\n" + "="*80)
        console.print("[bold green]✅ All demos completed successfully![/bold green]")
        console.print("="*80 + "\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
