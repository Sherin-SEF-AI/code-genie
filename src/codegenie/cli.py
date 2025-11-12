"""
Advanced Command-line interface for CodeGenie with unified features.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from .core.agent import CodeGenieAgent
from .core.config import Config
from .core.session import SessionManager
from .core.workflow_engine import WorkflowEngine
from .core.context_engine import ContextEngine
from .core.learning_engine import LearningEngine
from .agents.coordinator import AgentCoordinator
from .ui.terminal import TerminalUI
from .ui.web_interface import WebInterface
from .ui.configuration_manager import ConfigurationManager
from .ui.onboarding import OnboardingSystem, TutorialSystem
from .ui.cli_helpers import (
    CommandHistory,
    InteractivePrompt,
    ProgressIndicator,
    OutputFormatter,
)

app = typer.Typer(
    name="codegenie",
    help="CodeGenie - Advanced AI coding agent with autonomous workflows and multi-agent coordination",
    add_completion=False,
)

# Create subcommands for different feature areas
workflow_app = typer.Typer(name="workflow", help="Autonomous workflow management")
agents_app = typer.Typer(name="agents", help="Multi-agent system management")
learning_app = typer.Typer(name="learning", help="Adaptive learning and personalization")
config_app = typer.Typer(name="config", help="Advanced configuration management")
web_app = typer.Typer(name="web", help="Web interface management")
tutorial_app = typer.Typer(name="tutorial", help="Interactive tutorials")

app.add_typer(workflow_app, name="workflow")
app.add_typer(agents_app, name="agents")
app.add_typer(learning_app, name="learning")
app.add_typer(config_app, name="config")
app.add_typer(web_app, name="web")
app.add_typer(tutorial_app, name="tutorial")

console = Console()

# Initialize CLI helpers
command_history = CommandHistory()
interactive_prompt = InteractivePrompt(console)
progress_indicator = ProgressIndicator(console)
output_formatter = OutputFormatter(console)


@app.command()
def start(
    project_path: Optional[Path] = typer.Argument(
        None,
        help="Path to the project directory. Defaults to current directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use. If not specified, uses default from config.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    interface: str = typer.Option(
        "terminal",
        "--interface",
        "-i",
        help="Interface to use: terminal, web, or hybrid",
    ),
    autonomous: bool = typer.Option(
        False,
        "--autonomous",
        "-a",
        help="Enable autonomous workflow mode.",
    ),
    multi_agent: bool = typer.Option(
        False,
        "--multi-agent",
        help="Enable multi-agent coordination.",
    ),
    learning: bool = typer.Option(
        True,
        "--learning/--no-learning",
        help="Enable adaptive learning engine.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode.",
    ),
) -> None:
    """Start the Advanced CodeGenie Agent with unified interface."""
    
    # Set up project path
    if project_path is None:
        project_path = Path.cwd()
    
    # Display enhanced welcome message
    welcome_text = Text()
    welcome_text.append("🧞 CodeGenie v2.0.0 - Advanced AI Agent\n", style="bold blue")
    welcome_text.append(f"📁 Working in: {project_path}\n", style="green")
    welcome_text.append(f"🖥️  Interface: {interface}\n", style="cyan")
    
    if model:
        welcome_text.append(f"🧠 Using model: {model}\n", style="yellow")
    else:
        welcome_text.append("🧠 Using default model\n", style="yellow")
    
    # Show enabled features
    features = []
    if autonomous:
        features.append("🤖 Autonomous Workflows")
    if multi_agent:
        features.append("👥 Multi-Agent Coordination")
    if learning:
        features.append("🎓 Adaptive Learning")
    
    if features:
        welcome_text.append(f"✨ Features: {', '.join(features)}\n", style="magenta")
    
    console.print(Panel(welcome_text, title="Advanced CodeGenie", border_style="blue"))
    
    # Initialize and run the agent
    try:
        asyncio.run(run_advanced_agent(
            project_path, model, config_file, interface, 
            autonomous, multi_agent, learning, verbose, debug
        ))
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")
        if debug:
            console.print_exception()
        sys.exit(1)


async def run_advanced_agent(
    project_path: Path,
    model: Optional[str],
    config_file: Optional[Path],
    interface: str,
    autonomous: bool,
    multi_agent: bool,
    learning: bool,
    verbose: bool,
    debug: bool,
) -> None:
    """Run the Advanced CodeGenie Agent with unified features."""
    
    # Load configuration
    config = Config.load(config_file)
    
    # Override model if specified
    if model:
        config.models.default = model
    
    # Set debug mode
    if debug:
        config.debug = True
        config.verbose = True
    elif verbose:
        config.verbose = True
    
    # Configure advanced features
    config.autonomous_workflows = autonomous
    config.multi_agent_coordination = multi_agent
    config.adaptive_learning = learning
    
    # Initialize session manager
    session_manager = SessionManager(project_path, config)
    
    # Initialize main agent
    agent = CodeGenieAgent(session_manager)
    
    # Initialize the agent
    await agent.initialize()
    
    # Initialize appropriate UI
    if interface == "web":
        ui = WebInterface(agent, config)
    elif interface == "hybrid":
        # Start both terminal and web interfaces
        web_ui = WebInterface(agent, config)
        terminal_ui = TerminalUI(agent, console)
        
        # Start web interface in background
        web_task = asyncio.create_task(web_ui.start_server())
        
        console.print("🌐 Web interface available at http://localhost:8080", style="green")
        console.print("💻 Terminal interface ready", style="green")
        
        # Run terminal interface
        await terminal_ui.run()
        
        # Cleanup web interface
        web_task.cancel()
        return
    else:
        ui = TerminalUI(agent, console)
    
    # Start the agent
    await ui.run()

async def run_agent(
    project_path: Path,
    model: Optional[str],
    config_file: Optional[Path],
    verbose: bool,
    debug: bool,
) -> None:
    """Legacy run agent function for backward compatibility."""
    await run_advanced_agent(
        project_path, model, config_file, "terminal", 
        False, False, True, verbose, debug
    )


@app.command()
def init(
    project_path: Optional[Path] = typer.Argument(
        None,
        help="Path to initialize. Defaults to current directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration.",
    ),
) -> None:
    """Initialize CodeGenie in a project directory."""
    
    if project_path is None:
        project_path = Path.cwd()
    
    config_path = project_path / ".codegenie.yaml"
    
    if config_path.exists() and not force:
        console.print(f"❌ Configuration already exists at {config_path}", style="red")
        console.print("Use --force to overwrite.", style="yellow")
        return
    
    # Create default configuration
    config = Config.create_default()
    config.save(config_path)
    
    console.print(f"✅ Initialized CodeGenie in {project_path}", style="green")
    console.print(f"📝 Configuration saved to {config_path}", style="blue")


@app.command()
def models() -> None:
    """List available Ollama models."""
    import ollama
    
    try:
        models = ollama.list()
        if not models.get('models'):
            console.print("❌ No models found. Install some models first:", style="red")
            console.print("  ollama pull llama3.1:8b", style="yellow")
            console.print("  ollama pull codellama:7b", style="yellow")
            return
        
        console.print("📋 Available Ollama models:", style="bold blue")
        for model in models['models']:
            name = model['name']
            size = model.get('size', 'Unknown')
            modified = model.get('modified_at', 'Unknown')
            console.print(f"  • {name} ({size}) - Modified: {modified}", style="green")
            
    except Exception as e:
        console.print(f"❌ Error listing models: {e}", style="red")
        console.print("Make sure Ollama is running: ollama serve", style="yellow")


@app.command()
def execute(
    code: str = typer.Argument(..., help="Code to execute"),
    language: str = typer.Option("python", "--lang", "-l", help="Programming language"),
) -> None:
    """Execute code safely."""
    import asyncio
    
    async def run_execute():
        try:
            # Initialize agent
            config = Config.load()
            session_manager = SessionManager(Path.cwd(), config)
            agent = CodeGenieAgent(session_manager)
            await agent.initialize()
            
            # Execute code
            result = await agent.execute_code(code, language)
            
            if result.get("success"):
                console.print("✅ Code executed successfully!", style="green")
                console.print(f"Output:\n{result.get('output', '')}", style="white")
                if result.get("execution_time"):
                    console.print(f"Execution time: {result.get('execution_time'):.2f}s", style="blue")
            else:
                console.print("❌ Code execution failed!", style="red")
                console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_execute())


@app.command()
def analyze(
    file_path: str = typer.Argument(..., help="File to analyze"),
) -> None:
    """Analyze code file for issues and suggestions."""
    import asyncio
    
    async def run_analyze():
        try:
            # Initialize agent
            config = Config.load()
            session_manager = SessionManager(Path.cwd(), config)
            agent = CodeGenieAgent(session_manager)
            await agent.initialize()
            
            # Analyze file
            result = await agent.analyze_code(file_path)
            
            if result.get("success"):
                console.print(f"📊 Analysis of {file_path}", style="bold blue")
                
                issues = result.get("issues", [])
                if issues:
                    console.print(f"⚠️  Found {len(issues)} issues:", style="yellow")
                    for issue in issues[:5]:  # Show first 5 issues
                        console.print(f"  • {issue}", style="yellow")
                else:
                    console.print("✅ No issues found!", style="green")
                
                suggestions = result.get("suggestions", [])
                if suggestions:
                    console.print("\n💡 Suggestions:", style="cyan")
                    for suggestion in suggestions[:3]:  # Show first 3 suggestions
                        console.print(f"  • {suggestion}", style="cyan")
            else:
                console.print("❌ Analysis failed!", style="red")
                console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_analyze())


@app.command()
def create(
    file_path: str = typer.Argument(..., help="File path to create"),
    content: str = typer.Option("", "--content", "-c", help="File content"),
    template: str = typer.Option(None, "--template", "-t", help="Template to use"),
) -> None:
    """Create a new file with content."""
    import asyncio
    
    async def run_create():
        try:
            # Initialize agent
            config = Config.load()
            session_manager = SessionManager(Path.cwd(), config)
            agent = CodeGenieAgent(session_manager)
            await agent.initialize()
            
            # Get content
            if template:
                # Generate content based on template
                response = await agent.process_user_input(f"Create a {template} file for {file_path}")
                content = response
            elif not content:
                content = f"# {file_path}\n\n# Created by CodeGenie\n"
            
            # Create file
            result = await agent.create_file(file_path, content)
            
            if result.get("success"):
                console.print(f"✅ Created file: {file_path}", style="green")
                console.print(f"Size: {len(content)} characters", style="blue")
            else:
                console.print("❌ File creation failed!", style="red")
                console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_create())


@app.command()
def test(
    test_path: str = typer.Option(None, "--path", "-p", help="Test path to run"),
) -> None:
    """Run tests for the project."""
    import asyncio
    
    async def run_test():
        try:
            # Initialize agent
            config = Config.load()
            session_manager = SessionManager(Path.cwd(), config)
            agent = CodeGenieAgent(session_manager)
            await agent.initialize()
            
            # Run tests
            result = await agent.run_tests(test_path)
            
            if result.get("success"):
                passed = result.get("passed", 0)
                total = result.get("total", 0)
                
                if result.get("all_passed"):
                    console.print(f"✅ All {total} tests passed!", style="green")
                else:
                    console.print(f"⚠️  {passed}/{total} tests passed", style="yellow")
                
                if result.get("output"):
                    console.print(f"Test output:\n{result.get('output')}", style="white")
            else:
                console.print("❌ Test execution failed!", style="red")
                console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_test())


@app.command()
def insights() -> None:
    """Get comprehensive project insights and recommendations."""
    import asyncio
    
    async def run_insights():
        try:
            # Initialize agent
            config = Config.load()
            session_manager = SessionManager(Path.cwd(), config)
            agent = CodeGenieAgent(session_manager)
            await agent.initialize()
            
            # Get insights
            result = await agent.get_project_insights()
            
            if result.get("success"):
                console.print("📊 Project Insights", style="bold blue")
                console.print(f"Project Type: {result.get('project_type', 'Unknown')}", style="green")
                console.print(f"File Count: {result.get('file_count', 0)}", style="blue")
                console.print(f"Languages: {', '.join(result.get('languages', []))}", style="cyan")
                
                recommendations = result.get("recommendations", [])
                if recommendations:
                    console.print("\n💡 Recommendations:", style="yellow")
                    for rec in recommendations[:5]:
                        console.print(f"  • {rec}", style="yellow")
            else:
                console.print("❌ Failed to get insights!", style="red")
                console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_insights())


@app.command()
def learn() -> None:
    """Get personalized learning suggestions."""
    import asyncio
    
    async def run_learn():
        try:
            # Initialize agent
            config = Config.load()
            session_manager = SessionManager(Path.cwd(), config)
            agent = CodeGenieAgent(session_manager)
            await agent.initialize()
            
            # Get suggestions
            suggestions = await agent.get_learning_suggestions()
            
            console.print("🎓 Learning Suggestions", style="bold blue")
            for i, suggestion in enumerate(suggestions, 1):
                console.print(f"{i}. {suggestion}", style="cyan")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_learn())


# Workflow Management Commands
@workflow_app.command("create")
def create_workflow(
    goal: str = typer.Argument(..., help="High-level goal for the workflow"),
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
    autonomous: bool = typer.Option(True, help="Enable autonomous execution"),
    save_plan: bool = typer.Option(True, help="Save the execution plan"),
) -> None:
    """Create a new autonomous workflow."""
    
    async def run_create_workflow():
        try:
            config = Config.load()
            config.autonomous_workflows = True
            
            if project_path:
                session_manager = SessionManager(project_path, config)
            else:
                session_manager = SessionManager(Path.cwd(), config)
            
            workflow_engine = WorkflowEngine(config)
            agent = CodeGenieAgent(session_manager, workflow_engine=workflow_engine)
            await agent.initialize()
            
            console.print(f"🎯 Creating workflow for goal: {goal}", style="bold blue")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Planning workflow...", total=None)
                
                # Create workflow plan
                plan = await workflow_engine.create_execution_plan(goal)
                
                progress.update(task, description="Workflow plan created!")
            
            # Display plan
            table = Table(title=f"Workflow Plan: {goal}")
            table.add_column("Step", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Agent", style="yellow")
            table.add_column("Estimated Time", style="green")
            
            for i, step in enumerate(plan.steps, 1):
                table.add_row(
                    str(i),
                    step.description[:60] + "..." if len(step.description) > 60 else step.description,
                    step.assigned_agent or "Main",
                    f"{step.estimated_duration}min"
                )
            
            console.print(table)
            
            # Ask for confirmation
            if autonomous and Confirm.ask("Execute workflow autonomously?", console=console):
                console.print("🚀 Starting autonomous execution...", style="green")
                result = await workflow_engine.execute_autonomous_workflow(goal, {})
                
                if result.success:
                    console.print("✅ Workflow completed successfully!", style="green")
                else:
                    console.print(f"❌ Workflow failed: {result.error}", style="red")
            
            if save_plan:
                plan_file = Path.cwd() / f"workflow_plan_{goal.replace(' ', '_')}.json"
                with open(plan_file, 'w') as f:
                    json.dump(plan.to_dict(), f, indent=2)
                console.print(f"💾 Plan saved to {plan_file}", style="blue")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_create_workflow())


@workflow_app.command("list")
def list_workflows(
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """List existing workflows."""
    
    if project_path is None:
        project_path = Path.cwd()
    
    workflow_files = list(project_path.glob("workflow_plan_*.json"))
    
    if not workflow_files:
        console.print("No workflows found in current directory", style="yellow")
        return
    
    table = Table(title="Available Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Goal", style="white")
    table.add_column("Steps", style="yellow")
    table.add_column("Created", style="green")
    
    for workflow_file in workflow_files:
        try:
            with open(workflow_file) as f:
                plan_data = json.load(f)
            
            name = workflow_file.stem.replace("workflow_plan_", "")
            goal = plan_data.get("goal", "Unknown")
            steps = len(plan_data.get("steps", []))
            created = workflow_file.stat().st_mtime
            
            table.add_row(name, goal[:50], str(steps), f"{created:.0f}")
            
        except Exception as e:
            console.print(f"Error reading {workflow_file}: {e}", style="red")
    
    console.print(table)


@workflow_app.command("execute")
def execute_workflow(
    workflow_name: str = typer.Argument(..., help="Name of workflow to execute"),
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """Execute an existing workflow."""
    
    async def run_execute_workflow():
        try:
            if project_path is None:
                current_path = Path.cwd()
            else:
                current_path = project_path
            
            workflow_file = current_path / f"workflow_plan_{workflow_name}.json"
            
            if not workflow_file.exists():
                console.print(f"Workflow '{workflow_name}' not found", style="red")
                return
            
            config = Config.load()
            config.autonomous_workflows = True
            
            session_manager = SessionManager(current_path, config)
            workflow_engine = WorkflowEngine(config)
            agent = CodeGenieAgent(session_manager, workflow_engine=workflow_engine)
            await agent.initialize()
            
            # Load workflow plan
            with open(workflow_file) as f:
                plan_data = json.load(f)
            
            goal = plan_data.get("goal", "Unknown Goal")
            
            console.print(f"🚀 Executing workflow: {goal}", style="bold blue")
            
            # Execute workflow
            result = await workflow_engine.execute_autonomous_workflow(goal, plan_data)
            
            if result.success:
                console.print("✅ Workflow completed successfully!", style="green")
            else:
                console.print(f"❌ Workflow failed: {result.error}", style="red")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_execute_workflow())


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    
    version_text = Text()
    version_text.append(f"CodeGenie v{__version__}\n", style="bold blue")
    version_text.append("Powered by Ollama for local AI coding assistance", style="green")
    
    console.print(Panel(version_text, title="Version Info", border_style="blue"))


def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()

# Multi-Agent System Commands
@agents_app.command("list")
def list_agents() -> None:
    """List available specialized agents."""
    
    agents_info = {
        "architect": "System design and architecture decisions",
        "developer": "Code implementation and debugging",
        "tester": "Test creation and quality assurance",
        "security": "Security analysis and vulnerability scanning",
        "performance": "Performance optimization and analysis",
        "documentation": "Documentation generation and maintenance",
        "refactoring": "Code quality improvement and restructuring"
    }
    
    table = Table(title="Available Specialized Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Specialization", style="white")
    table.add_column("Status", style="green")
    
    for agent_name, description in agents_info.items():
        table.add_row(agent_name.title(), description, "✅ Available")
    
    console.print(table)


@agents_app.command("coordinate")
def coordinate_agents(
    task: str = typer.Argument(..., help="Task requiring multi-agent coordination"),
    agents: Optional[str] = typer.Option(None, help="Comma-separated list of agents to use"),
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """Coordinate multiple agents for a complex task."""
    
    async def run_coordinate():
        try:
            config = Config.load()
            config.multi_agent_coordination = True
            
            if project_path:
                session_manager = SessionManager(project_path, config)
            else:
                session_manager = SessionManager(Path.cwd(), config)
            
            agent_coordinator = AgentCoordinator(config)
            agent = CodeGenieAgent(session_manager, agent_coordinator=agent_coordinator)
            await agent.initialize()
            
            console.print(f"👥 Coordinating agents for task: {task}", style="bold blue")
            
            # Parse requested agents
            if agents:
                requested_agents = [a.strip() for a in agents.split(",")]
            else:
                requested_agents = None
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                coordination_task = progress.add_task("Analyzing task and selecting agents...", total=None)
                
                # Delegate task to appropriate agents
                assignments = await agent_coordinator.delegate_task({
                    "description": task,
                    "requested_agents": requested_agents
                })
                
                progress.update(coordination_task, description="Executing coordinated workflow...")
                
                # Execute coordinated workflow
                result = await agent_coordinator.coordinate_execution(assignments)
            
            # Display results
            if result.success:
                console.print("✅ Multi-agent coordination completed successfully!", style="green")
                
                # Show agent contributions
                table = Table(title="Agent Contributions")
                table.add_column("Agent", style="cyan")
                table.add_column("Task", style="white")
                table.add_column("Status", style="green")
                
                for assignment in assignments:
                    status = "✅ Completed" if assignment.completed else "⏳ In Progress"
                    table.add_row(assignment.agent_name, assignment.task_description, status)
                
                console.print(table)
            else:
                console.print(f"❌ Coordination failed: {result.error}", style="red")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_coordinate())


@agents_app.command("status")
def agents_status() -> None:
    """Show status of all agents."""
    
    async def run_status():
        try:
            config = Config.load()
            config.multi_agent_coordination = True
            
            session_manager = SessionManager(Path.cwd(), config)
            agent_coordinator = AgentCoordinator(config)
            agent = CodeGenieAgent(session_manager, agent_coordinator=agent_coordinator)
            await agent.initialize()
            
            status = await agent_coordinator.get_agents_status()
            
            table = Table(title="Agent Status")
            table.add_column("Agent", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Current Task", style="yellow")
            table.add_column("Performance", style="green")
            
            for agent_name, agent_status in status.items():
                current_task = agent_status.get("current_task", "Idle")[:30]
                performance = f"{agent_status.get('success_rate', 0):.1%}"
                status_icon = "🟢 Active" if agent_status.get("active") else "🔴 Inactive"
                
                table.add_row(agent_name.title(), status_icon, current_task, performance)
            
            console.print(table)
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_status())


# Learning Engine Commands
@learning_app.command("profile")
def show_learning_profile() -> None:
    """Show current learning profile and preferences."""
    
    async def run_profile():
        try:
            config = Config.load()
            config.adaptive_learning = True
            
            session_manager = SessionManager(Path.cwd(), config)
            learning_engine = LearningEngine(config)
            agent = CodeGenieAgent(session_manager, learning_engine=learning_engine)
            await agent.initialize()
            
            profile = await learning_engine.get_user_profile()
            
            console.print("🎓 Learning Profile", style="bold blue")
            
            # Basic info
            table = Table(title="User Preferences")
            table.add_column("Attribute", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Coding Style", profile.get("coding_style", "Unknown"))
            table.add_row("Skill Level", profile.get("skill_level", "Unknown"))
            table.add_row("Preferred Languages", ", ".join(profile.get("languages", [])))
            table.add_row("Learning Goals", ", ".join(profile.get("learning_goals", [])))
            
            console.print(table)
            
            # Learning statistics
            stats = profile.get("statistics", {})
            if stats:
                stats_table = Table(title="Learning Statistics")
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="white")
                
                stats_table.add_row("Interactions", str(stats.get("total_interactions", 0)))
                stats_table.add_row("Successful Suggestions", str(stats.get("successful_suggestions", 0)))
                stats_table.add_row("Learning Rate", f"{stats.get('learning_rate', 0):.2%}")
                
                console.print(stats_table)
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_profile())


@learning_app.command("adapt")
def adapt_preferences(
    coding_style: Optional[str] = typer.Option(None, help="Preferred coding style"),
    skill_level: Optional[str] = typer.Option(None, help="Skill level (beginner/intermediate/advanced)"),
    languages: Optional[str] = typer.Option(None, help="Comma-separated preferred languages"),
) -> None:
    """Adapt learning preferences."""
    
    async def run_adapt():
        try:
            config = Config.load()
            config.adaptive_learning = True
            
            session_manager = SessionManager(Path.cwd(), config)
            learning_engine = LearningEngine(config)
            agent = CodeGenieAgent(session_manager, learning_engine=learning_engine)
            await agent.initialize()
            
            preferences = {}
            if coding_style:
                preferences["coding_style"] = coding_style
            if skill_level:
                preferences["skill_level"] = skill_level
            if languages:
                preferences["languages"] = [lang.strip() for lang in languages.split(",")]
            
            await learning_engine.update_user_preferences(preferences)
            
            console.print("✅ Learning preferences updated successfully!", style="green")
            
            # Show updated profile
            profile = await learning_engine.get_user_profile()
            
            table = Table(title="Updated Preferences")
            table.add_column("Attribute", style="cyan")
            table.add_column("Value", style="white")
            
            for key, value in preferences.items():
                if isinstance(value, list):
                    value = ", ".join(value)
                table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(table)
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_adapt())


@learning_app.command("feedback")
def provide_feedback(
    suggestion_id: str = typer.Argument(..., help="ID of the suggestion to provide feedback on"),
    rating: int = typer.Option(..., help="Rating from 1-5"),
    comment: Optional[str] = typer.Option(None, help="Optional feedback comment"),
) -> None:
    """Provide feedback on AI suggestions."""
    
    async def run_feedback():
        try:
            config = Config.load()
            config.adaptive_learning = True
            
            session_manager = SessionManager(Path.cwd(), config)
            learning_engine = LearningEngine(config)
            agent = CodeGenieAgent(session_manager, learning_engine=learning_engine)
            await agent.initialize()
            
            feedback = {
                "suggestion_id": suggestion_id,
                "rating": rating,
                "comment": comment,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await learning_engine.process_feedback(feedback)
            
            console.print(f"✅ Feedback recorded for suggestion {suggestion_id}", style="green")
            console.print(f"Rating: {rating}/5", style="blue")
            if comment:
                console.print(f"Comment: {comment}", style="blue")
            
            await agent.shutdown()
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
    
    asyncio.run(run_feedback())


# Configuration Management Commands
@config_app.command("init")
def init_advanced_config(
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
    template: str = typer.Option("default", help="Configuration template to use"),
) -> None:
    """Initialize advanced configuration."""
    
    if project_path is None:
        project_path = Path.cwd()
    
    config_manager = ConfigurationManager()
    
    try:
        config_manager.initialize_project_config(project_path, template)
        console.print(f"✅ Advanced configuration initialized in {project_path}", style="green")
        
        # Show configuration summary
        config_file = project_path / ".codegenie" / "config.yaml"
        if config_file.exists():
            console.print(f"📝 Configuration file: {config_file}", style="blue")
            console.print(f"🎨 Template used: {template}", style="blue")
        
    except Exception as e:
        console.print(f"❌ Error initializing configuration: {e}", style="red")


@config_app.command("show")
def show_config(
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """Show current configuration."""
    
    if project_path is None:
        project_path = Path.cwd()
    
    try:
        config = Config.load_from_project(project_path)
        
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        # Core settings
        table.add_row("Default Model", config.models.default)
        table.add_row("Autonomous Workflows", "✅ Enabled" if config.autonomous_workflows else "❌ Disabled")
        table.add_row("Multi-Agent Coordination", "✅ Enabled" if config.multi_agent_coordination else "❌ Disabled")
        table.add_row("Adaptive Learning", "✅ Enabled" if config.adaptive_learning else "❌ Disabled")
        table.add_row("Debug Mode", "✅ Enabled" if config.debug else "❌ Disabled")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error loading configuration: {e}", style="red")


@config_app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """Set configuration value."""
    
    if project_path is None:
        project_path = Path.cwd()
    
    config_manager = ConfigurationManager()
    
    try:
        config_manager.set_config_value(project_path, key, value)
        console.print(f"✅ Configuration updated: {key} = {value}", style="green")
        
    except Exception as e:
        console.print(f"❌ Error setting configuration: {e}", style="red")


# Web Interface Commands
@web_app.command("start")
def start_web_interface(
    port: int = typer.Option(8080, help="Port to run web interface on"),
    host: str = typer.Option("localhost", help="Host to bind to"),
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """Start the web interface."""
    
    async def run_web():
        try:
            config = Config.load()
            
            if project_path:
                session_manager = SessionManager(project_path, config)
            else:
                session_manager = SessionManager(Path.cwd(), config)
            
            agent = CodeGenieAgent(session_manager)
            web_interface = WebInterface(agent, config)
            
            console.print(f"🌐 Starting web interface on http://{host}:{port}", style="green")
            
            await web_interface.start_server(host=host, port=port)
            
        except Exception as e:
            console.print(f"❌ Error starting web interface: {e}", style="red")
    
    asyncio.run(run_web())


@web_app.command("status")
def web_status() -> None:
    """Check web interface status."""
    
    # This would check if the web interface is running
    console.print("🌐 Web Interface Status", style="bold blue")
    console.print("Status: Not implemented yet", style="yellow")
    console.print("Use 'codegenie web start' to launch the web interface", style="blue")


# Onboarding and Tutorial Commands
@app.command()
def onboard(
    project_path: Optional[Path] = typer.Option(None, help="Project path"),
) -> None:
    """Run interactive onboarding for new users."""
    
    async def run_onboard():
        try:
            if project_path is None:
                current_path = Path.cwd()
            else:
                current_path = project_path
            
            onboarding = OnboardingSystem(console)
            preferences = await onboarding.run_onboarding(current_path)
            
            # Start agent if requested
            if preferences.get("start_now"):
                config = Config.load()
                session_manager = SessionManager(current_path, config)
                
                # Apply preferences
                config.autonomous_workflows = preferences.get("autonomous_workflows", True)
                config.multi_agent_coordination = preferences.get("multi_agent_coordination", True)
                config.adaptive_learning = preferences.get("adaptive_learning", True)
                
                # Initialize engines based on preferences
                workflow_engine = WorkflowEngine(config) if config.autonomous_workflows else None
                context_engine = ContextEngine(config)
                learning_engine = LearningEngine(config) if config.adaptive_learning else None
                agent_coordinator = AgentCoordinator(config) if config.multi_agent_coordination else None
                
                agent = CodeGenieAgent(
                    session_manager,
                    workflow_engine=workflow_engine,
                    context_engine=context_engine,
                    learning_engine=learning_engine,
                    agent_coordinator=agent_coordinator
                )
                
                ui = TerminalUI(agent, console)
                await ui.run()
            
        except KeyboardInterrupt:
            console.print("\n👋 Onboarding cancelled", style="yellow")
        except Exception as e:
            console.print(f"❌ Error during onboarding: {e}", style="red")
    
    asyncio.run(run_onboard())


@tutorial_app.command("list")
def list_tutorials() -> None:
    """List available tutorials."""
    
    tutorial_system = TutorialSystem(console)
    tutorial_system.list_tutorials()


@tutorial_app.command("run")
def run_tutorial(
    tutorial_name: str = typer.Argument(..., help="Name of tutorial to run"),
) -> None:
    """Run an interactive tutorial."""
    
    async def run_tutorial_async():
        try:
            tutorial_system = TutorialSystem(console)
            await tutorial_system.run_tutorial(tutorial_name)
        except KeyboardInterrupt:
            console.print("\n👋 Tutorial cancelled", style="yellow")
        except Exception as e:
            console.print(f"❌ Error running tutorial: {e}", style="red")
    
    asyncio.run(run_tutorial_async())


# Claude Code Feature Commands
@app.command()
def plan(
    goal: str = typer.Argument(..., help="Goal or task to plan"),
    project_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save the plan to file"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute the plan after creation"),
) -> None:
    """Create a detailed execution plan for a task using the Planning Agent."""
    
    async def run_plan():
        success = False
        error_msg = None
        
        try:
            from .core.planning_agent import PlanningAgent
            from .core.context_analyzer import ContextAnalyzer
            
            if project_path is None:
                current_path = Path.cwd()
            else:
                current_path = project_path
            
            output_formatter.header("🎯 Task Planning", f"Goal: {goal}")
            
            with progress_indicator.spinner("Planning...") as progress:
                task = progress.add_task("Analyzing project context...", total=None)
                
                # Initialize context analyzer
                context_analyzer = ContextAnalyzer(current_path)
                project_context = await context_analyzer.analyze_project()
                
                progress.update(task, description="Creating execution plan...")
                
                # Initialize planning agent
                planning_agent = PlanningAgent()
                execution_plan = await planning_agent.create_plan(goal, project_context)
                
                progress.update(task, description="Plan created!")
            
            # Display plan summary
            output_formatter.section("Plan Summary")
            output_formatter.key_value({
                "Description": execution_plan.description,
                "Risk Level": execution_plan.risk_level.name,
                "Estimated Duration": str(execution_plan.estimated_duration),
                "Affected Files": len(execution_plan.affected_files),
                "Total Steps": len(execution_plan.steps),
            })
            
            # Display steps
            output_formatter.section("Execution Steps")
            
            rows = []
            for i, step in enumerate(execution_plan.steps, 1):
                rows.append([
                    str(i),
                    step.description[:47] + "..." if len(step.description) > 50 else step.description,
                    step.action_type.value,
                    step.risk_level.name,
                    str(step.estimated_duration)
                ])
            
            output_formatter.table(
                f"{len(execution_plan.steps)} Steps",
                ["#", "Description", "Action", "Risk", "Duration"],
                rows,
                column_styles=["cyan", "white", "yellow", "red", "green"]
            )
            
            # Show affected files
            if execution_plan.affected_files:
                output_formatter.section("Affected Files")
                files_to_show = [str(f) for f in execution_plan.affected_files[:10]]
                output_formatter.list_items(files_to_show, style="cyan")
                
                if len(execution_plan.affected_files) > 10:
                    console.print(f"  ... and {len(execution_plan.affected_files) - 10} more", style="dim")
            
            # Save plan
            if save:
                plan_file = current_path / f"plan_{goal.replace(' ', '_')[:30]}.json"
                plan_data = {
                    'id': execution_plan.id,
                    'description': execution_plan.description,
                    'goal': goal,
                    'steps': [step.to_dict() for step in execution_plan.steps],
                    'estimated_duration': str(execution_plan.estimated_duration),
                    'risk_level': execution_plan.risk_level.name,
                    'affected_files': [str(f) for f in execution_plan.affected_files],
                }
                
                with open(plan_file, 'w') as f:
                    json.dump(plan_data, f, indent=2)
                
                output_formatter.success(f"Plan saved to: {plan_file}")
            
            # Execute if requested
            if execute or interactive_prompt.ask_confirm("Execute this plan now?"):
                output_formatter.info("Executing plan...")
                
                with progress_indicator.bar("Executing steps...") as progress:
                    exec_task = progress.add_task("Executing...", total=len(execution_plan.steps))
                    
                    def approval_callback(step):
                        return interactive_prompt.ask_confirm(f"Approve: {step.description}?")
                    
                    result = await planning_agent.execute_plan(execution_plan, approval_callback)
                    
                    progress.update(exec_task, completed=result.completed_steps)
                
                if result.success:
                    output_formatter.success("Plan executed successfully!")
                    console.print(f"Completed {result.completed_steps}/{result.total_steps} steps", style="green")
                    success = True
                else:
                    output_formatter.error(f"Plan execution failed: {result.error}")
                    console.print(f"Completed {result.completed_steps}/{result.total_steps} steps", style="yellow")
                    error_msg = result.error
            else:
                success = True
            
        except Exception as e:
            error_msg = str(e)
            output_formatter.error(f"Error: {e}")
            if "--debug" in sys.argv:
                console.print_exception()
        finally:
            # Record command in history
            command_history.add_command(
                "plan",
                {"goal": goal, "save": save, "execute": execute},
                success=success,
                error=error_msg
            )
    
    asyncio.run(run_plan())


@app.command()
def scaffold(
    project_type: str = typer.Argument(..., help="Project type (e.g., python-fastapi, react, nextjs)"),
    name: str = typer.Argument(..., help="Project name"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Path to create project in"),
    git: bool = typer.Option(True, "--git/--no-git", help="Initialize git repository"),
    install: bool = typer.Option(True, "--install/--no-install", help="Install dependencies"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Use specific template"),
) -> None:
    """Scaffold a new project with proper structure using Project Scaffolder."""
    
    async def run_scaffold():
        try:
            from .core.project_scaffolder import ProjectScaffolder, ProjectType
            from .core.template_manager import TemplateManager
            
            if path is None:
                project_path = Path.cwd() / name
            else:
                project_path = path / name
            
            console.print(f"🏗️  Scaffolding {project_type} project: {name}", style="bold blue")
            console.print(f"📁 Location: {project_path}", style="cyan")
            
            # Check if directory exists
            if project_path.exists():
                if not Confirm.ask(f"Directory {project_path} already exists. Continue?", console=console):
                    console.print("❌ Scaffolding cancelled", style="yellow")
                    return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Initializing scaffolder...", total=None)
                
                # Initialize scaffolder
                scaffolder = ProjectScaffolder()
                
                # Detect project type
                progress.update(task, description="Detecting project type...")
                detected_type = await scaffolder.detect_project_type(project_type)
                
                # Generate structure
                progress.update(task, description="Generating project structure...")
                structure = await scaffolder.generate_structure(detected_type)
                
                # Create project
                progress.update(task, description="Creating files and directories...")
                project = await scaffolder.create_project(
                    project_type=detected_type,
                    name=name,
                    options={
                        'path': project_path,
                        'template': template,
                        'git': git,
                        'install': install,
                    }
                )
                
                # Initialize git
                if git:
                    progress.update(task, description="Initializing git repository...")
                    await scaffolder.initialize_git(project_path)
                
                # Install dependencies
                if install:
                    progress.update(task, description="Installing dependencies...")
                    install_result = await scaffolder.install_dependencies(project_path)
                    
                    if not install_result.success:
                        console.print(f"⚠️  Dependency installation had issues: {install_result.error}", style="yellow")
                
                progress.update(task, description="Project scaffolding complete!")
            
            # Display summary
            console.print(f"\n✅ Project '{name}' created successfully!", style="bold green")
            console.print(f"📁 Location: {project_path}", style="blue")
            console.print(f"🎨 Type: {detected_type.value}", style="cyan")
            
            # Show next steps
            console.print("\n📝 Next steps:", style="bold blue")
            console.print(f"  1. cd {project_path}", style="white")
            
            if detected_type.value.startswith("python"):
                console.print("  2. python -m venv venv", style="white")
                console.print("  3. source venv/bin/activate", style="white")
                console.print("  4. pip install -r requirements.txt", style="white")
            elif detected_type.value.startswith("javascript") or detected_type.value.startswith("typescript"):
                console.print("  2. npm install", style="white")
                console.print("  3. npm run dev", style="white")
            elif detected_type.value.startswith("go"):
                console.print("  2. go mod download", style="white")
                console.print("  3. go run main.go", style="white")
            elif detected_type.value.startswith("rust"):
                console.print("  2. cargo build", style="white")
                console.print("  3. cargo run", style="white")
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            if "--debug" in sys.argv:
                console.print_exception()
    
    asyncio.run(run_scaffold())


@app.command()
def refactor(
    target: str = typer.Argument(..., help="File or symbol to refactor"),
    operation: str = typer.Argument(..., help="Refactoring operation (rename, extract, move, etc.)"),
    new_name: Optional[str] = typer.Option(None, "--name", "-n", help="New name for rename operations"),
    preview: bool = typer.Option(True, "--preview/--no-preview", help="Preview changes before applying"),
    project_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path"),
) -> None:
    """Refactor code across multiple files using Multi-File Editor."""
    
    async def run_refactor():
        try:
            from .core.multi_file_editor import MultiFileEditor
            from .core.context_analyzer import ContextAnalyzer
            from .core.diff_engine import DiffEngine
            
            if project_path is None:
                current_path = Path.cwd()
            else:
                current_path = project_path
            
            console.print(f"🔧 Refactoring: {target}", style="bold blue")
            console.print(f"Operation: {operation}", style="cyan")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Analyzing project...", total=None)
                
                # Initialize components
                context_analyzer = ContextAnalyzer(current_path)
                project_context = await context_analyzer.analyze_project()
                
                multi_file_editor = MultiFileEditor(project_context)
                diff_engine = DiffEngine()
                
                # Plan changes
                progress.update(task, description="Planning refactoring changes...")
                
                intent = f"{operation} {target}"
                if new_name:
                    intent += f" to {new_name}"
                
                change_set = await multi_file_editor.plan_changes(intent, project_context)
                
                progress.update(task, description="Changes planned!")
            
            # Display change summary
            console.print(f"\n📊 Refactoring Summary", style="bold green")
            console.print(f"Files affected: {len(change_set.changes)}", style="blue")
            console.print(f"Total changes: {sum(len(c.modifications) for c in change_set.changes)}", style="cyan")
            
            # Show affected files
            table = Table(title="Affected Files")
            table.add_column("File", style="cyan", width=50)
            table.add_column("Changes", style="yellow", width=10)
            table.add_column("Type", style="green", width=15)
            
            for file_change in change_set.changes:
                table.add_row(
                    str(file_change.file_path),
                    str(len(file_change.modifications)),
                    file_change.change_type
                )
            
            console.print(table)
            
            # Preview changes
            if preview:
                console.print("\n📝 Change Preview:", style="bold blue")
                
                for file_change in change_set.changes[:5]:  # Show first 5 files
                    console.print(f"\n📄 {file_change.file_path}", style="bold cyan")
                    
                    # Generate and show diff
                    if file_change.original_content and file_change.new_content:
                        diff = diff_engine.generate_diff(
                            file_change.original_content,
                            file_change.new_content
                        )
                        console.print(diff_engine.show_unified_diff(diff), style="white")
                
                if len(change_set.changes) > 5:
                    console.print(f"\n... and {len(change_set.changes) - 5} more files", style="dim")
            
            # Apply changes
            if Confirm.ask("\n✅ Apply these changes?", console=console):
                console.print("\n⚙️  Applying refactoring...", style="bold blue")
                
                result = await multi_file_editor.apply_changes(change_set)
                
                if result.success:
                    console.print("\n✅ Refactoring completed successfully!", style="bold green")
                    console.print(f"Modified {result.files_modified} files", style="green")
                    
                    if result.validation_errors:
                        console.print("\n⚠️  Validation warnings:", style="yellow")
                        for error in result.validation_errors[:5]:
                            console.print(f"  • {error}", style="yellow")
                else:
                    console.print(f"\n❌ Refactoring failed: {result.error}", style="bold red")
            else:
                console.print("❌ Refactoring cancelled", style="yellow")
            
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            if "--debug" in sys.argv:
                console.print_exception()
    
    asyncio.run(run_refactor())


@app.command()
def history(
    count: int = typer.Option(10, "--count", "-n", help="Number of recent commands to show"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search command history"),
    stats: bool = typer.Option(False, "--stats", help="Show command usage statistics"),
) -> None:
    """Show command history and statistics."""
    
    if stats:
        # Show statistics
        stats_data = command_history.get_stats()
        
        output_formatter.header("Command History Statistics")
        
        output_formatter.key_value({
            "Total Commands": stats_data['total_commands'],
            "Success Rate": f"{stats_data['success_rate']:.1%}",
        })
        
        if stats_data['most_used']:
            output_formatter.section("Most Used Commands")
            rows = []
            for cmd, count in stats_data['most_used']:
                rows.append([cmd, str(count)])
            
            output_formatter.table(
                "Top Commands",
                ["Command", "Count"],
                rows,
                column_styles=["cyan", "green"]
            )
    
    elif search:
        # Search history
        results = command_history.search(search)
        
        if not results:
            output_formatter.warning(f"No commands found matching '{search}'")
            return
        
        output_formatter.header(f"Search Results for '{search}'")
        
        rows = []
        for entry in results[-count:]:
            timestamp = entry['timestamp'][:19]  # Remove microseconds
            status = "✅" if entry['success'] else "❌"
            rows.append([timestamp, entry['command'], status])
        
        output_formatter.table(
            f"Found {len(results)} matching commands",
            ["Timestamp", "Command", "Status"],
            rows,
            column_styles=["dim", "cyan", "green"]
        )
    
    else:
        # Show recent commands
        recent = command_history.get_recent(count)
        
        if not recent:
            output_formatter.info("No command history available")
            return
        
        output_formatter.header("Recent Commands")
        
        rows = []
        for entry in recent:
            timestamp = entry['timestamp'][:19]  # Remove microseconds
            status = "✅" if entry['success'] else "❌"
            rows.append([timestamp, entry['command'], status])
        
        output_formatter.table(
            f"Last {len(recent)} commands",
            ["Timestamp", "Command", "Status"],
            rows,
            column_styles=["dim", "cyan", "green"]
        )


@app.command()
def interactive(
    project_path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project path"),
) -> None:
    """Start interactive mode with enhanced prompts and guidance."""
    
    async def run_interactive():
        try:
            if project_path is None:
                current_path = Path.cwd()
            else:
                current_path = project_path
            
            output_formatter.header(
                "🧞 CodeGenie Interactive Mode",
                "Get guided assistance for common tasks"
            )
            
            # Main menu
            while True:
                console.print()
                action = interactive_prompt.ask_choice(
                    "What would you like to do?",
                    [
                        "Create a new project",
                        "Plan a task",
                        "Refactor code",
                        "Analyze code",
                        "Generate documentation",
                        "Run tests",
                        "Exit",
                    ]
                )
                
                if action == "Exit":
                    output_formatter.info("Goodbye! 👋")
                    break
                
                elif action == "Create a new project":
                    # Interactive project creation
                    project_name = interactive_prompt.ask_text(
                        "Project name",
                        validator=lambda x: len(x) > 0 and x.replace('-', '').replace('_', '').isalnum(),
                        error_message="Project name must be alphanumeric (with - or _)"
                    )
                    
                    project_type = interactive_prompt.ask_choice(
                        "Select project type",
                        [
                            "python-fastapi",
                            "python-django",
                            "python-flask",
                            "react",
                            "nextjs",
                            "express",
                            "go-web",
                            "rust-cli",
                        ]
                    )
                    
                    init_git = interactive_prompt.ask_confirm("Initialize git repository?", default=True)
                    install_deps = interactive_prompt.ask_confirm("Install dependencies?", default=True)
                    
                    output_formatter.info(f"Creating {project_type} project: {project_name}")
                    
                    # Execute scaffold command
                    from .core.project_scaffolder import ProjectScaffolder
                    
                    with progress_indicator.spinner("Creating project...") as progress:
                        task = progress.add_task("Scaffolding project...", total=None)
                        
                        scaffolder = ProjectScaffolder()
                        detected_type = await scaffolder.detect_project_type(project_type)
                        
                        project = await scaffolder.create_project(
                            project_type=detected_type,
                            name=project_name,
                            options={
                                'path': current_path / project_name,
                                'git': init_git,
                                'install': install_deps,
                            }
                        )
                        
                        if init_git:
                            progress.update(task, description="Initializing git...")
                            await scaffolder.initialize_git(current_path / project_name)
                        
                        if install_deps:
                            progress.update(task, description="Installing dependencies...")
                            await scaffolder.install_dependencies(current_path / project_name)
                    
                    output_formatter.success(f"Project '{project_name}' created successfully!")
                    command_history.add_command("scaffold", {"name": project_name, "type": project_type}, success=True)
                
                elif action == "Plan a task":
                    # Interactive task planning
                    goal = interactive_prompt.ask_text("Describe the task or goal")
                    
                    output_formatter.info(f"Creating plan for: {goal}")
                    
                    from .core.planning_agent import PlanningAgent
                    from .core.context_analyzer import ContextAnalyzer
                    
                    with progress_indicator.spinner("Planning...") as progress:
                        task = progress.add_task("Analyzing context...", total=None)
                        
                        context_analyzer = ContextAnalyzer(current_path)
                        project_context = await context_analyzer.analyze_project()
                        
                        progress.update(task, description="Creating execution plan...")
                        
                        planning_agent = PlanningAgent()
                        execution_plan = await planning_agent.create_plan(goal, project_context)
                    
                    output_formatter.success("Plan created!")
                    
                    # Display plan summary
                    rows = []
                    for i, step in enumerate(execution_plan.steps[:10], 1):
                        rows.append([
                            str(i),
                            step.description[:50] + "..." if len(step.description) > 50 else step.description,
                            step.action_type.value,
                        ])
                    
                    output_formatter.table(
                        f"Execution Plan ({len(execution_plan.steps)} steps)",
                        ["#", "Description", "Action"],
                        rows,
                        column_styles=["cyan", "white", "yellow"]
                    )
                    
                    if interactive_prompt.ask_confirm("Execute this plan?"):
                        output_formatter.info("Executing plan...")
                        
                        def approval_callback(step):
                            return interactive_prompt.ask_confirm(f"Approve: {step.description}?")
                        
                        result = await planning_agent.execute_plan(execution_plan, approval_callback)
                        
                        if result.success:
                            output_formatter.success("Plan executed successfully!")
                        else:
                            output_formatter.error(f"Plan execution failed: {result.error}")
                    
                    command_history.add_command("plan", {"goal": goal}, success=True)
                
                elif action == "Analyze code":
                    # Interactive code analysis
                    file_path = interactive_prompt.ask_text("File path to analyze")
                    
                    if not Path(file_path).exists():
                        output_formatter.error(f"File not found: {file_path}")
                        continue
                    
                    output_formatter.info(f"Analyzing {file_path}...")
                    
                    # Initialize agent and analyze
                    config = Config.load()
                    session_manager = SessionManager(current_path, config)
                    agent = CodeGenieAgent(session_manager)
                    await agent.initialize()
                    
                    result = await agent.analyze_code(file_path)
                    
                    if result.get("success"):
                        output_formatter.success("Analysis complete!")
                        
                        issues = result.get("issues", [])
                        if issues:
                            output_formatter.section("Issues Found")
                            output_formatter.list_items(issues[:5], style="yellow")
                        else:
                            output_formatter.success("No issues found!")
                        
                        suggestions = result.get("suggestions", [])
                        if suggestions:
                            output_formatter.section("Suggestions")
                            output_formatter.list_items(suggestions[:3], style="cyan")
                    else:
                        output_formatter.error(f"Analysis failed: {result.get('error')}")
                    
                    await agent.shutdown()
                    command_history.add_command("analyze", {"file": file_path}, success=result.get("success", False))
                
                else:
                    output_formatter.warning(f"'{action}' not yet implemented in interactive mode")
        
        except KeyboardInterrupt:
            output_formatter.info("\nExiting interactive mode...")
        except Exception as e:
            output_formatter.error(f"Error: {e}")
            if "--debug" in sys.argv:
                console.print_exception()
    
    asyncio.run(run_interactive())