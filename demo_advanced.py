#!/usr/bin/env python3
"""
Advanced demo script for Claude Code Agent showcasing project understanding and testing capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.config import Config
from codegenie.core.session import SessionManager
from codegenie.core.agent import CodeGenieAgent
from codegenie.utils.project_analyzer import ProjectAnalyzer
from codegenie.utils.testing_framework import TestingFramework
from codegenie.agents.executor import TaskExecutor
from codegenie.agents.monitor import TaskMonitor, TestMonitor
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn


async def demo_advanced_features():
    """Demo advanced project understanding and testing capabilities."""
    
    console = Console()
    
    # Create a more complex demo project
    demo_dir = Path("demo_advanced_project")
    demo_dir.mkdir(exist_ok=True)
    
    # Create project structure
    (demo_dir / "src").mkdir(exist_ok=True)
    (demo_dir / "tests").mkdir(exist_ok=True)
    (demo_dir / "docs").mkdir(exist_ok=True)
    
    # Create Python source files
    (demo_dir / "src" / "__init__.py").write_text("")
    (demo_dir / "src" / "calculator.py").write_text("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, a, b):
        return a ** b
""")
    
    (demo_dir / "src" / "utils.py").write_text("""
def format_number(number, precision=2):
    return f"{number:.{precision}f}"

def validate_input(value, min_val=None, max_val=None):
    if min_val is not None and value < min_val:
        raise ValueError(f"Value {value} is below minimum {min_val}")
    if max_val is not None and value > max_val:
        raise ValueError(f"Value {value} is above maximum {max_val}")
    return True
""")
    
    # Create test files
    (demo_dir / "tests" / "__init__.py").write_text("")
    (demo_dir / "tests" / "test_calculator.py").write_text("""
import pytest
from src.calculator import Calculator

def test_calculator_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_calculator_divide_by_zero():
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.divide(10, 0)
""")
    
    # Create configuration files
    (demo_dir / "requirements.txt").write_text("""
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
""")
    
    (demo_dir / "README.md").write_text("""
# Demo Advanced Project

A simple calculator library with utilities.

## Features
- Basic arithmetic operations
- Input validation
- Error handling

## Testing
Run tests with: `pytest tests/`
""")
    
    (demo_dir / ".gitignore").write_text("""
__pycache__/
*.pyc
.pytest_cache/
.coverage
""")
    
    console.print("🚀 CodeGenie - Advanced Features Demo", style="bold blue")
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
        
        # 1. Project Analysis
        console.print("\n🔍 Project Analysis", style="bold yellow")
        
        project_analyzer = ProjectAnalyzer()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Analyzing project structure...", total=None)
            
            analysis = project_analyzer.analyze_project(demo_dir)
        
        # Display project analysis results
        analysis_table = Table(title="Project Analysis Results")
        analysis_table.add_column("Category", style="cyan")
        analysis_table.add_column("Value", style="white")
        
        analysis_table.add_row("Project Type", analysis["project_type"])
        analysis_table.add_row("Languages", ", ".join(analysis["languages"].keys()))
        analysis_table.add_row("Total Files", str(analysis["statistics"]["total_files"]))
        analysis_table.add_row("Total Lines", str(analysis["statistics"]["total_lines"]))
        analysis_table.add_row("Organization Score", f"{analysis['structure']['organization_score']:.1%}")
        analysis_table.add_row("Quality Score", f"{analysis['quality']['overall_score']:.1%}")
        
        console.print(analysis_table)
        
        # Display quality breakdown
        quality_table = Table(title="Quality Assessment")
        quality_table.add_column("Aspect", style="cyan")
        quality_table.add_column("Score", style="white")
        quality_table.add_column("Status", style="green")
        
        for aspect, details in analysis["quality"].items():
            if isinstance(details, dict) and "score" in details:
                score = details["score"]
                status = "✅ Good" if score > 0.7 else "⚠️ Needs Improvement" if score > 0.3 else "❌ Poor"
                quality_table.add_row(aspect.title(), f"{score:.1%}", status)
        
        console.print(quality_table)
        
        # Display recommendations
        if analysis["recommendations"]:
            recommendations_text = "\n".join(f"• {rec}" for rec in analysis["recommendations"])
            console.print(Panel(
                recommendations_text,
                title="Recommendations",
                border_style="yellow"
            ))
        
        # 2. Testing Framework Analysis
        console.print("\n🧪 Testing Framework Analysis", style="bold yellow")
        
        testing_framework = TestingFramework()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Analyzing testing setup...", total=None)
            
            test_analysis = testing_framework.detect_testing_framework(demo_dir)
        
        # Display testing analysis
        test_table = Table(title="Testing Framework Analysis")
        test_table.add_column("Aspect", style="cyan")
        test_table.add_column("Value", style="white")
        
        frameworks = [f["name"] for f in test_analysis["frameworks"]]
        test_table.add_row("Frameworks", ", ".join(frameworks) if frameworks else "None detected")
        test_table.add_row("Test Files", str(len(test_analysis["test_files"])))
        test_table.add_row("Coverage Setup", "✅ Yes" if test_analysis["coverage_setup"] else "❌ No")
        test_table.add_row("CI Integration", "✅ Yes" if test_analysis["ci_integration"] else "❌ No")
        
        console.print(test_table)
        
        # Display test files
        if test_analysis["test_files"]:
            test_files_table = Table(title="Test Files")
            test_files_table.add_column("File", style="cyan")
            test_files_table.add_column("Language", style="white")
            test_files_table.add_column("Tests", style="green")
            
            for test_file in test_analysis["test_files"]:
                test_files_table.add_row(
                    test_file["name"],
                    test_file["language"],
                    str(test_file["test_count"])
                )
            
            console.print(test_files_table)
        
        # Display testing recommendations
        if test_analysis["recommendations"]:
            test_recs_text = "\n".join(f"• {rec}" for rec in test_analysis["recommendations"])
            console.print(Panel(
                test_recs_text,
                title="Testing Recommendations",
                border_style="yellow"
            ))
        
        # 3. Test Generation Demo
        console.print("\n📝 Test Generation Demo", style="bold yellow")
        
        # Read a source file and generate tests
        calculator_code = (demo_dir / "src" / "calculator.py").read_text()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Generating test code...", total=None)
            
            generated_test = testing_framework.generate_test_for_function(
                calculator_code,
                "python",
                "pytest"
            )
        
        console.print("Generated test code for Calculator class:")
        console.print(Panel(
            generated_test,
            title="Generated Test Code",
            border_style="green"
        ))
        
        # 4. Task Monitoring Demo
        console.print("\n📊 Task Monitoring Demo", style="bold yellow")
        
        task_monitor = TaskMonitor()
        test_monitor = TestMonitor(task_monitor)
        
        # Simulate a test run
        test_id = "demo_test_run"
        test_monitor.start_test_run(
            test_id=test_id,
            test_type="unit",
            description="Demo test run",
            test_files=["test_calculator.py"]
        )
        
        # Simulate test progress
        await asyncio.sleep(0.5)
        test_monitor.update_test_progress(test_id, 1, 1, 0, 0, "test_calculator_add")
        
        await asyncio.sleep(0.5)
        test_monitor.update_test_progress(test_id, 2, 1, 1, 0, "test_calculator_divide_by_zero")
        
        # Add a test error
        test_monitor.add_test_error(
            test_id=test_id,
            test_name="test_calculator_divide_by_zero",
            error_message="Expected ValueError but got None",
            error_type="error"
        )
        
        # Complete the test run
        test_monitor.complete_test_run(test_id, success=False)
        
        # Display monitoring results
        monitor_stats = task_monitor.get_task_statistics()
        test_stats = test_monitor.get_test_statistics()
        
        monitor_table = Table(title="Task Monitoring Statistics")
        monitor_table.add_column("Metric", style="cyan")
        monitor_table.add_column("Value", style="white")
        
        monitor_table.add_row("Total Tasks", str(monitor_stats["total_tasks"]))
        monitor_table.add_row("Active Tasks", str(monitor_stats["active_tasks"]))
        monitor_table.add_row("Completed Tasks", str(monitor_stats["completed_tasks"]))
        monitor_table.add_row("Failed Tasks", str(monitor_stats["failed_tasks"]))
        monitor_table.add_row("Success Rate", f"{monitor_stats['success_rate']:.1%}")
        
        console.print(monitor_table)
        
        test_stats_table = Table(title="Test Statistics")
        test_stats_table.add_column("Metric", style="cyan")
        test_stats_table.add_column("Value", style="white")
        
        test_stats_table.add_row("Total Test Runs", str(test_stats["total_test_runs"]))
        test_stats_table.add_row("Successful Runs", str(test_stats["successful_runs"]))
        test_stats_table.add_row("Failed Runs", str(test_stats["failed_runs"]))
        test_stats_table.add_row("Success Rate", f"{test_stats['success_rate']:.1%}")
        test_stats_table.add_row("Total Tests Run", str(test_stats["total_tests_run"]))
        test_stats_table.add_row("Tests Passed", str(test_stats["total_tests_passed"]))
        test_stats_table.add_row("Tests Failed", str(test_stats["total_tests_failed"]))
        
        console.print(test_stats_table)
        
        # 5. Code Coverage Analysis
        console.print("\n📈 Code Coverage Analysis", style="bold yellow")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Analyzing code coverage...", total=None)
            
            coverage_analysis = testing_framework.analyze_test_coverage(demo_dir)
        
        coverage_table = Table(title="Code Coverage Analysis")
        coverage_table.add_column("Metric", style="cyan")
        coverage_table.add_column("Value", style="white")
        
        coverage_table.add_row("Overall Coverage", f"{coverage_analysis['overall_coverage']:.1%}")
        coverage_table.add_row("Uncovered Functions", str(len(coverage_analysis["uncovered_functions"])))
        
        console.print(coverage_table)
        
        if coverage_analysis["uncovered_functions"]:
            uncovered_table = Table(title="Uncovered Functions")
            uncovered_table.add_column("File", style="cyan")
            uncovered_table.add_column("Function", style="white")
            
            for func in coverage_analysis["uncovered_functions"][:5]:  # Show first 5
                uncovered_table.add_row(func["file"], func["function"])
            
            console.print(uncovered_table)
        
        if coverage_analysis["recommendations"]:
            coverage_recs_text = "\n".join(f"• {rec}" for rec in coverage_analysis["recommendations"])
            console.print(Panel(
                coverage_recs_text,
                title="Coverage Recommendations",
                border_style="yellow"
            ))
        
        console.print("\n🎉 Advanced Features Demo completed successfully!", style="bold green")
        console.print("The Claude Code Agent now includes:", style="yellow")
        console.print("  • Comprehensive project analysis and understanding", style="white")
        console.print("  • Testing framework detection and integration", style="white")
        console.print("  • Automatic test generation capabilities", style="white")
        console.print("  • Task monitoring and progress tracking", style="white")
        console.print("  • Code coverage analysis and recommendations", style="white")
        console.print("  • Quality assessment and improvement suggestions", style="white")
        
    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="red")


if __name__ == "__main__":
    asyncio.run(demo_advanced_features())
