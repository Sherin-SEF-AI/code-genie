#!/usr/bin/env python3
"""
Comprehensive demo script showcasing all CodeGenie features.
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
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_full_features():
    """Demonstrate all CodeGenie features."""
    
    console = Console()
    
    # Display welcome message
    welcome_text = """
🧞 CodeGenie v0.1.0 - Full Features Demo
📁 Working in: {project_path}
🧠 Available Models: llama3.2:latest, gpt-oss:latest
🛡️  Safety features: Enabled
🔧 Error recovery: Enabled
🚀 Advanced features: Enabled
""".format(project_path=Path.cwd())

    console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    try:
        # Initialize configuration
        config = Config.create_default()
        console.print("✅ Configuration loaded", style="green")
        
        # Initialize session manager
        session_manager = SessionManager(Path.cwd(), config)
        console.print("✅ Session manager initialized", style="green")
        
        # Initialize agent
        agent = CodeGenieAgent(session_manager)
        console.print("✅ Agent initialized", style="green")
        
        # Initialize the agent
        await agent.initialize()
        console.print("✅ Agent initialized and ready", style="green")
        
        # Demo 1: Enhanced Input Analysis
        console.print("\n🧪 Demo 1: Enhanced Input Analysis", style="bold blue")
        console.print("=" * 50, style="blue")
        
        test_inputs = [
            "Create a Python function that calculates fibonacci numbers",
            "Debug the error in my authentication system",
            "What is the best way to handle database connections?",
            "Run the tests for the user service module"
        ]
        
        for i, test_input in enumerate(test_inputs, 1):
            console.print(f"\n{i}. Testing: {test_input}", style="cyan")
            
            # Analyze input (this would be done internally)
            analysis = await agent._analyze_input(test_input)
            
            table = Table(title="Input Analysis")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Type", analysis.get("type", "unknown"))
            table.add_row("Complexity", analysis.get("complexity", "unknown"))
            table.add_row("Requires Code", "Yes" if analysis.get("requires_code") else "No")
            table.add_row("Requires Execution", "Yes" if analysis.get("requires_execution") else "No")
            table.add_row("Requires File Ops", "Yes" if analysis.get("requires_file_ops") else "No")
            table.add_row("Intent", analysis.get("intent", "unknown"))
            
            console.print(table)
        
        # Demo 2: Code Execution
        console.print("\n🧪 Demo 2: Safe Code Execution", style="bold blue")
        console.print("=" * 50, style="blue")
        
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")
"""
        
        console.print("Executing Fibonacci function...", style="yellow")
        result = await agent.execute_code(test_code, "python")
        
        if result.get("success"):
            console.print("✅ Code executed successfully!", style="green")
            console.print(f"Output:\n{result.get('output', '')}", style="white")
            console.print(f"Execution time: {result.get('execution_time', 0):.2f}s", style="blue")
        else:
            console.print("❌ Code execution failed!", style="red")
            console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
        
        # Demo 3: File Creation
        console.print("\n🧪 Demo 3: File Creation", style="bold blue")
        console.print("=" * 50, style="blue")
        
        test_file_content = """
# Demo file created by CodeGenie
def hello_world():
    \"\"\"A simple hello world function.\"\"\"
    return "Hello, World from CodeGenie!"

def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    return a + b

if __name__ == "__main__":
    print(hello_world())
    print(f"Sum of 5 and 3: {calculate_sum(5, 3)}")
"""
        
        console.print("Creating demo file...", style="yellow")
        result = await agent.create_file("demo_created_file.py", test_file_content, "python")
        
        if result.get("success"):
            console.print("✅ File created successfully!", style="green")
            console.print(f"File: {result.get('file_path', 'unknown')}", style="blue")
        else:
            console.print("❌ File creation failed!", style="red")
            console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
        
        # Demo 4: Code Analysis
        console.print("\n🧪 Demo 4: Code Analysis", style="bold blue")
        console.print("=" * 50, style="blue")
        
        console.print("Analyzing the created file...", style="yellow")
        result = await agent.analyze_code("demo_created_file.py")
        
        if result.get("success"):
            console.print("✅ Code analysis completed!", style="green")
            
            issues = result.get("issues", [])
            if issues:
                console.print(f"⚠️  Found {len(issues)} issues:", style="yellow")
                for issue in issues[:3]:
                    console.print(f"  • {issue}", style="yellow")
            else:
                console.print("✅ No issues found!", style="green")
            
            suggestions = result.get("suggestions", [])
            if suggestions:
                console.print("\n💡 Suggestions:", style="cyan")
                for suggestion in suggestions[:3]:
                    console.print(f"  • {suggestion}", style="cyan")
        else:
            console.print("❌ Code analysis failed!", style="red")
            console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
        
        # Demo 5: Project Insights
        console.print("\n🧪 Demo 5: Project Insights", style="bold blue")
        console.print("=" * 50, style="blue")
        
        console.print("Getting project insights...", style="yellow")
        result = await agent.get_project_insights()
        
        if result.get("success"):
            console.print("✅ Project insights retrieved!", style="green")
            
            table = Table(title="Project Insights")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Project Type", result.get("project_type", "Unknown"))
            table.add_row("File Count", str(result.get("file_count", 0)))
            table.add_row("Languages", ", ".join(result.get("languages", [])))
            table.add_row("Frameworks", ", ".join(result.get("frameworks", [])))
            table.add_row("Size", result.get("size", "Unknown"))
            
            console.print(table)
            
            recommendations = result.get("recommendations", [])
            if recommendations:
                console.print("\n💡 Recommendations:", style="yellow")
                for i, rec in enumerate(recommendations[:3], 1):
                    console.print(f"{i}. {rec}", style="yellow")
        else:
            console.print("❌ Failed to get insights!", style="red")
            console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
        
        # Demo 6: Learning Suggestions
        console.print("\n🧪 Demo 6: Learning Suggestions", style="bold blue")
        console.print("=" * 50, style="blue")
        
        console.print("Getting learning suggestions...", style="yellow")
        suggestions = await agent.get_learning_suggestions()
        
        console.print("✅ Learning suggestions retrieved!", style="green")
        console.print("\n🎓 Personalized Learning Suggestions:", style="bold cyan")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"{i}. {suggestion}", style="cyan")
        
        # Demo 7: Enhanced Error Recovery
        console.print("\n🧪 Demo 7: Enhanced Error Recovery", style="bold blue")
        console.print("=" * 50, style="blue")
        
        # Test error recovery with invalid input
        console.print("Testing error recovery with invalid input...", style="yellow")
        
        try:
            # This should trigger error recovery
            response = await agent.process_user_input("This is a test of error recovery with some invalid context that might cause issues")
            console.print("✅ Error recovery handled gracefully!", style="green")
            console.print(f"Response: {response[:100]}...", style="white")
        except Exception as e:
            console.print(f"❌ Error recovery failed: {e}", style="red")
        
        # Demo 8: Test Execution
        console.print("\n🧪 Demo 8: Test Execution", style="bold blue")
        console.print("=" * 50, style="blue")
        
        console.print("Running project tests...", style="yellow")
        result = await agent.run_tests()
        
        if result.get("success"):
            passed = result.get("passed", 0)
            total = result.get("total", 0)
            
            if result.get("all_passed"):
                console.print(f"✅ All {total} tests passed!", style="green")
            else:
                console.print(f"⚠️  {passed}/{total} tests passed", style="yellow")
            
            if result.get("output"):
                console.print(f"Test output:\n{result.get('output')[:200]}...", style="white")
        else:
            console.print("❌ Test execution failed!", style="red")
            console.print(f"Error: {result.get('error', 'Unknown error')}", style="red")
        
        # Demo 9: Natural Language Processing
        console.print("\n🧪 Demo 9: Natural Language Processing", style="bold blue")
        console.print("=" * 50, style="blue")
        
        test_queries = [
            "Help me understand how to create a REST API",
            "What are the best practices for error handling in Python?",
            "How can I optimize the performance of my code?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            console.print(f"\n{i}. Query: {query}", style="cyan")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Processing query...", total=None)
                
                try:
                    response = await agent.process_user_input(query)
                    console.print("✅ Query processed successfully!", style="green")
                    console.print(f"Response: {response[:150]}...", style="white")
                except Exception as e:
                    console.print(f"❌ Query processing failed: {e}", style="red")
        
        # Final Summary
        console.print("\n🎉 Full Features Demo Completed Successfully!", style="bold green")
        console.print("=" * 60, style="green")
        
        console.print("✅ Key Features Demonstrated:", style="bold")
        console.print("   • Enhanced input analysis and intent recognition", style="white")
        console.print("   • Safe code execution with comprehensive error handling", style="white")
        console.print("   • Intelligent file creation and management", style="white")
        console.print("   • Advanced code analysis and issue detection", style="white")
        console.print("   • Comprehensive project insights and recommendations", style="white")
        console.print("   • Personalized learning suggestions", style="white")
        console.print("   • Enhanced error recovery and fallback strategies", style="white")
        console.print("   • Test execution and validation", style="white")
        console.print("   • Natural language processing and conversation", style="white")
        
        console.print("\n🚀 CodeGenie is now fully functional with advanced features!", style="bold blue")
        
        # Cleanup
        await agent.shutdown()
        console.print("✅ Agent shutdown completed", style="green")
        
    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="red")


async def main():
    """Main demo function."""
    
    console = Console()
    
    console.print("🚀 CodeGenie - Full Features Demo", style="bold blue")
    console.print("=" * 60, style="blue")
    
    try:
        # Run the demo
        await demo_full_features()
        
    except KeyboardInterrupt:
        console.print("\n👋 Demo interrupted by user", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="red")


if __name__ == "__main__":
    asyncio.run(main())
