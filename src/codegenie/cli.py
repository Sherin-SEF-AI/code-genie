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
def main(
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
def version() -> None:
    """Show version information."""
    from . import __version__
    
    version_text = Text()
    version_text.append(f"CodeGenie v{__version__}\n", style="bold blue")
    version_text.append("Powered by Ollama for local AI coding assistance", style="green")
    
    console.print(Panel(version_text, title="Version Info", border_style="blue"))


if __name__ == "__main__":
    app()
