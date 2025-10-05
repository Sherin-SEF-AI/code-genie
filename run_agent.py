#!/usr/bin/env python3
"""
Simple script to run the Claude Code Agent.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.config import Config
from codegenie.core.session import SessionManager
from codegenie.core.agent import CodeGenieAgent
from codegenie.ui.terminal import TerminalUI
from rich.console import Console

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the agent."""
    
    console = Console()
    
    # Display welcome message
    welcome_text = """
🧞 CodeGenie v0.1.0
📁 Working in: {project_path}
🧠 Using model: Default Ollama model
🛡️  Safety features: Enabled
🔧 Error recovery: Enabled
""".format(project_path=Path.cwd())
    
    console.print(f"[bold blue]{welcome_text}[/bold blue]")
    
    try:
        # Load configuration
        config = Config()
        console.print("✅ Configuration loaded", style="green")
        
        # Initialize session manager
        session_manager = SessionManager(Path.cwd(), config)
        console.print("✅ Session manager initialized", style="green")
        
        # Initialize agent
        agent = CodeGenieAgent(session_manager)
        console.print("✅ Agent initialized", style="green")
        
        # Initialize UI
        ui = TerminalUI(agent, console)
        console.print("✅ UI initialized", style="green")
        
        console.print("\n🚀 Starting CodeGenie...", style="bold green")
        console.print("Type 'help' for available commands or 'quit' to exit.\n", style="yellow")
        
        # Start the agent
        await ui.run()
        
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")
        logger.exception("Agent failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
