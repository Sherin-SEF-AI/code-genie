#!/usr/bin/env python3
"""
Demo script for CodeGenie.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.config import Config
from codegenie.core.session import SessionManager
from codegenie.core.agent import CodeGenieAgent
from codegenie.ui.terminal import TerminalUI
from rich.console import Console


async def demo_basic_functionality():
    """Demo basic functionality without Ollama."""
    
    console = Console()
    
    # Create a demo project directory
    demo_dir = Path("demo_project")
    demo_dir.mkdir(exist_ok=True)
    
    # Create a simple Python file
    (demo_dir / "main.py").write_text("""
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")
    
    console.print("🤖 Claude Code Agent Demo", style="bold blue")
    console.print(f"📁 Demo project: {demo_dir.absolute()}", style="green")
    
    try:
        # Initialize configuration
        config = Config.create_default()
        config.cache_dir = Path("demo_cache")
        
        # Initialize session manager
        session_manager = SessionManager(demo_dir, config)
        
        # Initialize agent
        agent = CodeGenieAgent(session_manager)
        
        # Mock the model manager to avoid Ollama dependency
        from unittest.mock import Mock, AsyncMock
        agent.model_manager = Mock()
        agent.model_manager.initialize = AsyncMock()
        agent.model_manager.get_model_stats.return_value = {"models": {"llama3.1:8b": {}}}
        
        # Initialize agent
        await agent.initialize()
        
        console.print("✅ Agent initialized successfully", style="green")
        
        # Show project analysis
        context = session_manager.get_context()
        console.print(f"📊 Project Type: {context.get('project_type', 'Unknown')}", style="cyan")
        console.print(f"📊 Languages: {', '.join(context.get('languages', []))}", style="cyan")
        console.print(f"📊 Files: {context.get('file_count', 0)}", style="cyan")
        
        # Show agent status
        status = await agent.get_status()
        console.print(f"📊 Session ID: {status.get('session_stats', {}).get('session_id', 'Unknown')}", style="cyan")
        console.print(f"📊 Initialized: {status.get('initialized', False)}", style="cyan")
        
        # Test code analysis
        from claude_code.utils.code_analyzer import CodeAnalyzer
        analyzer = CodeAnalyzer()
        
        main_py = demo_dir / "main.py"
        if main_py.exists():
            analysis = analyzer.analyze_file(main_py)
            console.print(f"📊 Functions found: {len(analysis.get('functions', []))}", style="cyan")
            console.print(f"📊 Classes found: {len(analysis.get('classes', []))}", style="cyan")
        
        # Test file operations
        from codegenie.utils.file_operations import FileOperations
        file_ops = FileOperations()
        
        # Create a new file
        result = file_ops.create_file(
            demo_dir / "test.py",
            'print("Test file created by CodeGenie")'
        )
        
        if result["success"]:
            console.print("✅ Test file created successfully", style="green")
        else:
            console.print(f"❌ Failed to create test file: {result['error']}", style="red")
        
        # Show operation log
        operations = file_ops.get_operation_log()
        console.print(f"📊 Operations performed: {len(operations)}", style="cyan")
        
        console.print("\n🎉 Demo completed successfully!", style="bold green")
        console.print("To run the full agent with Ollama, install Ollama and run:", style="yellow")
        console.print("  ollama serve", style="yellow")
        console.print("  ollama pull llama3.1:8b", style="yellow")
        console.print("  codegenie", style="yellow")
        
    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="red")


if __name__ == "__main__":
    asyncio.run(demo_basic_functionality())
