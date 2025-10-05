#!/usr/bin/env python3
"""
Demo script showcasing Claude Code Agent with Ollama integration.
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


async def demo_ollama_integration():
    """Demonstrate Ollama integration with the CodeGenie Agent."""
    
    console = Console()
    
    # Display welcome message
    welcome_text = """
🧞 CodeGenie v0.1.0 - Ollama Integration Demo
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
        
        # Test basic functionality
        console.print("\n🧪 Testing Basic Functionality:", style="bold blue")
        
        # Test 1: Simple code generation
        console.print("\n1️⃣  Testing Code Generation:", style="bold yellow")
        test_prompt = "Write a simple Python function that calculates the factorial of a number"
        
        try:
            response = await agent.generate_code(test_prompt)
            console.print("✅ Code generation successful", style="green")
            console.print(f"Generated code:\n{response[:200]}...", style="cyan")
        except Exception as e:
            console.print(f"❌ Code generation failed: {e}", style="red")
        
        # Test 2: Project analysis
        console.print("\n2️⃣  Testing Project Analysis:", style="bold yellow")
        try:
            analysis = await agent.analyze_project()
            console.print("✅ Project analysis successful", style="green")
            console.print(f"Project type: {analysis.get('project_type', 'Unknown')}", style="cyan")
            console.print(f"Languages: {', '.join(analysis.get('languages', []))}", style="cyan")
        except Exception as e:
            console.print(f"❌ Project analysis failed: {e}", style="red")
        
        # Test 3: Error detection
        console.print("\n3️⃣  Testing Error Detection:", style="bold yellow")
        test_code = """
def broken_function(
    print("This has a syntax error")
    return 42
"""
        
        try:
            errors = await agent.detect_errors(test_code)
            console.print("✅ Error detection successful", style="green")
            console.print(f"Detected {len(errors)} errors", style="cyan")
            for error in errors:
                console.print(f"   • {error.error_type}: {error.message[:50]}...", style="yellow")
        except Exception as e:
            console.print(f"❌ Error detection failed: {e}", style="red")
        
        # Test 4: Safe execution
        console.print("\n4️⃣  Testing Safe Execution:", style="bold yellow")
        safe_code = """
import sys
print("Hello from Claude Code Agent!")
print(f"Python version: {sys.version}")
"""
        
        try:
            result = await agent.execute_code_safely(safe_code)
            console.print("✅ Safe execution successful", style="green")
            console.print(f"Output: {result.stdout[:100]}...", style="cyan")
        except Exception as e:
            console.print(f"❌ Safe execution failed: {e}", style="red")
        
        # Show statistics
        console.print("\n📊 Agent Statistics:", style="bold blue")
        stats = agent.get_statistics()
        console.print(f"   • Total operations: {stats.get('total_operations', 0)}", style="cyan")
        console.print(f"   • Successful operations: {stats.get('successful_operations', 0)}", style="cyan")
        console.print(f"   • Success rate: {stats.get('success_rate', 0):.2%}", style="cyan")
        
        console.print("\n🎉 Ollama Integration Demo Completed Successfully!", style="bold green")
        
        return 0
        
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}", style="red")
        logger.exception("Demo failed")
        return 1


async def main():
    """Main demo function."""
    
    console = Console()
    
    console.print("🚀 CodeGenie - Ollama Integration Demo", style="bold blue")
    console.print("=" * 60, style="blue")
    
    try:
        # Run the demo
        exit_code = await demo_ollama_integration()
        
        if exit_code == 0:
            console.print("\n✅ Demo completed successfully!", style="bold green")
            console.print("\n🎯 Key Features Demonstrated:", style="bold blue")
            console.print("   • Ollama model integration and selection", style="cyan")
            console.print("   • Code generation with local AI models", style="cyan")
            console.print("   • Project analysis and understanding", style="cyan")
            console.print("   • Error detection and analysis", style="cyan")
            console.print("   • Safe code execution", style="cyan")
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
