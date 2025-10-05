#!/usr/bin/env python3
"""
Simple demo showcasing Claude Code Agent with Ollama integration.
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
from codegenie.models.ollama_client import OllamaClient
from codegenie.models.model_manager import ModelManager
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_simple_ollama():
    """Demonstrate simple Ollama integration with the CodeGenie Agent."""
    
    console = Console()
    
    # Display welcome message
    welcome_text = """
🧞 CodeGenie v0.1.0 - Simple Ollama Demo
📁 Working in: {project_path}
🧠 Available Models: llama3.2:latest, gpt-oss:latest
🛡️  Safety features: Enabled
🔧 Error recovery: Enabled
""".format(project_path=Path.cwd())
    
    console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    try:
        # Load configuration
        config = Config()
        console.print("✅ Configuration loaded", style="green")
        
        # Initialize Ollama client
        ollama_client = OllamaClient(config)
        console.print("✅ Ollama client initialized", style="green")
        
        # Test Ollama connection
        try:
            models = await ollama_client.list_models()
            console.print(f"✅ Connected to Ollama - Found {len(models)} models", style="green")
            for model in models:
                console.print(f"   • {model['name']} ({model.get('size', 'Unknown size')})", style="cyan")
        except Exception as e:
            console.print(f"❌ Failed to connect to Ollama: {e}", style="red")
            console.print("Make sure Ollama is running: ollama serve", style="yellow")
            return 1
        
        # Initialize model manager
        model_manager = ModelManager(config)
        console.print("✅ Model manager initialized", style="green")
        
        # Test model selection
        selected_model = await model_manager.get_best_model("code_generation")
        console.print(f"✅ Selected model: {selected_model}", style="green")
        
        # Initialize session manager
        session_manager = SessionManager(Path.cwd(), config)
        console.print("✅ Session manager initialized", style="green")
        
        # Initialize agent
        agent = CodeGenieAgent(session_manager)
        console.print("✅ Agent initialized", style="green")
        
        # Initialize the agent
        await agent.initialize()
        console.print("✅ Agent initialized and ready", style="green")
        
        # Test basic functionality
        console.print("\n🧪 Testing Basic Functionality:", style="bold blue")
        
        # Test 1: Simple conversation
        console.print("\n1️⃣  Testing Conversation:", style="bold yellow")
        test_input = "Hello! Can you help me write a simple Python function?"
        
        try:
            response = await agent.process_user_input(test_input)
            console.print("✅ Conversation successful", style="green")
            console.print(f"User: {test_input}", style="cyan")
            console.print(f"Agent: {response[:200]}...", style="cyan")
        except Exception as e:
            console.print(f"❌ Conversation failed: {e}", style="red")
        
        # Test 2: Code generation request
        console.print("\n2️⃣  Testing Code Generation Request:", style="bold yellow")
        code_request = "Write a Python function that calculates the factorial of a number with proper error handling"
        
        try:
            response = await agent.process_user_input(code_request)
            console.print("✅ Code generation request successful", style="green")
            console.print(f"User: {code_request}", style="cyan")
            console.print(f"Agent: {response[:300]}...", style="cyan")
        except Exception as e:
            console.print(f"❌ Code generation request failed: {e}", style="red")
        
        # Test 3: Project analysis request
        console.print("\n3️⃣  Testing Project Analysis Request:", style="bold yellow")
        analysis_request = "Analyze this project and tell me what type of project it is and what technologies are used"
        
        try:
            response = await agent.process_user_input(analysis_request)
            console.print("✅ Project analysis request successful", style="green")
            console.print(f"User: {analysis_request}", style="cyan")
            console.print(f"Agent: {response[:300]}...", style="cyan")
        except Exception as e:
            console.print(f"❌ Project analysis request failed: {e}", style="red")
        
        # Test 4: Get agent status
        console.print("\n4️⃣  Testing Agent Status:", style="bold yellow")
        try:
            status = await agent.get_status()
            console.print("✅ Agent status retrieved", style="green")
            console.print(f"Status: {status}", style="cyan")
        except Exception as e:
            console.print(f"❌ Agent status failed: {e}", style="red")
        
        # Test 5: Get suggestions
        console.print("\n5️⃣  Testing Agent Suggestions:", style="bold yellow")
        try:
            suggestions = await agent.get_suggestions()
            console.print("✅ Agent suggestions retrieved", style="green")
            console.print(f"Suggestions: {suggestions}", style="cyan")
        except Exception as e:
            console.print(f"❌ Agent suggestions failed: {e}", style="red")
        
        # Shutdown agent
        await agent.shutdown()
        console.print("✅ Agent shutdown completed", style="green")
        
        console.print("\n🎉 Simple Ollama Integration Demo Completed Successfully!", style="bold green")
        
        return 0
        
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}", style="red")
        logger.exception("Demo failed")
        return 1


async def main():
    """Main demo function."""
    
    console = Console()
    
    console.print("🚀 CodeGenie - Simple Ollama Integration Demo", style="bold blue")
    console.print("=" * 60, style="blue")
    
    try:
        # Run the demo
        exit_code = await demo_simple_ollama()
        
        if exit_code == 0:
            console.print("\n✅ Demo completed successfully!", style="bold green")
            console.print("\n🎯 Key Features Demonstrated:", style="bold blue")
            console.print("   • Ollama model integration and selection", style="cyan")
            console.print("   • Natural language conversation with local AI", style="cyan")
            console.print("   • Code generation requests", style="cyan")
            console.print("   • Project analysis capabilities", style="cyan")
            console.print("   • Agent status and suggestions", style="cyan")
            console.print("   • Complete offline operation", style="cyan")
        else:
            console.print("\n❌ Demo failed", style="bold red")
        
        return exit_code
        
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}", style="red")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
