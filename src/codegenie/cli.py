"""
Command-line interface for CodeGenie.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .core.agent import CodeGenieAgent
from .core.config import Config
from .core.session import SessionManager
from .ui.terminal import TerminalUI

app = typer.Typer(
    name="codegenie",
    help="CodeGenie - Local AI coding agent powered by Ollama",
    add_completion=False,
)

console = Console()


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
    """Start the CodeGenie Agent."""
    
    # Set up project path
    if project_path is None:
        project_path = Path.cwd()
    
    # Display welcome message
    welcome_text = Text()
    welcome_text.append("🧞 CodeGenie v0.1.0\n", style="bold blue")
    welcome_text.append(f"📁 Working in: {project_path}\n", style="green")
    if model:
        welcome_text.append(f"🧠 Using model: {model}\n", style="yellow")
    else:
        welcome_text.append("🧠 Using default model\n", style="yellow")
    
    console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    # Initialize and run the agent
    try:
        asyncio.run(run_agent(project_path, model, config_file, verbose, debug))
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")
        if debug:
            console.print_exception()
        sys.exit(1)


async def run_agent(
    project_path: Path,
    model: Optional[str],
    config_file: Optional[Path],
    verbose: bool,
    debug: bool,
) -> None:
    """Run the Claude Code Agent."""
    
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
    
    # Initialize session manager
    session_manager = SessionManager(project_path, config)
    
    # Initialize agent
    agent = CodeGenieAgent(session_manager)
    
    # Initialize UI
    ui = TerminalUI(agent, console)
    
    # Start the agent
    await ui.run()


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
