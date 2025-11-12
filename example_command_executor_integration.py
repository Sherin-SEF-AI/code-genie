#!/usr/bin/env python3
"""
Example showing CommandExecutor integration with other CodeGenie components.

This demonstrates how CommandExecutor can be used in real-world scenarios:
- Project setup workflows
- Dependency installation
- Build and test automation
- Git operations
"""

import asyncio
import importlib.util
from pathlib import Path

# Load CommandExecutor directly
spec = importlib.util.spec_from_file_location(
    "command_executor",
    Path(__file__).parent / "src" / "codegenie" / "core" / "command_executor.py"
)
command_executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(command_executor)

CommandExecutor = command_executor.CommandExecutor
CommandRiskLevel = command_executor.CommandRiskLevel


class ProjectSetupWorkflow:
    """Example workflow for setting up a new project."""
    
    def __init__(self):
        """Initialize workflow with command executor."""
        self.executor = CommandExecutor(
            approval_callback=self.approval_callback
        )
        self.commands_executed = []
    
    def approval_callback(self, command: str, risk_level: CommandRiskLevel) -> bool:
        """Handle approval requests."""
        print(f"\n{'='*60}")
        print(f"Approval Request: {risk_level.value.upper()}")
        print(f"Command: {command}")
        print(f"{'='*60}")
        
        # Auto-approve for demo
        if risk_level == CommandRiskLevel.DANGEROUS:
            print("❌ DENIED - Dangerous command")
            return False
        else:
            print("✅ APPROVED")
            return True
    
    async def setup_python_project(self, project_name: str, project_dir: Path):
        """
        Set up a new Python project.
        
        Args:
            project_name: Name of the project
            project_dir: Directory to create project in
        """
        print(f"\n{'='*60}")
        print(f"Setting up Python project: {project_name}")
        print(f"{'='*60}")
        
        # Step 1: Create project directory
        print("\n1. Creating project directory...")
        result = await self.executor.execute_command(
            f"mkdir -p {project_dir}",
            require_approval=True
        )
        self._log_result("Create directory", result)
        
        # Step 2: Create virtual environment
        print("\n2. Creating virtual environment...")
        result = await self.executor.execute_command(
            f"python3 -m venv {project_dir}/venv",
            require_approval=True
        )
        self._log_result("Create venv", result)
        
        # Step 3: Create project structure
        print("\n3. Creating project structure...")
        structure_commands = [
            f"mkdir -p {project_dir}/src/{project_name}",
            f"mkdir -p {project_dir}/tests",
            f"mkdir -p {project_dir}/docs",
            f"touch {project_dir}/src/{project_name}/__init__.py",
            f"touch {project_dir}/tests/__init__.py",
            f"touch {project_dir}/README.md",
            f"touch {project_dir}/requirements.txt",
        ]
        
        for cmd in structure_commands:
            result = await self.executor.execute_command(cmd, require_approval=False)
            self._log_result(f"  {cmd.split()[-1]}", result)
        
        # Step 4: Initialize git
        print("\n4. Initializing git repository...")
        result = await self.executor.execute_command(
            f"git init {project_dir}",
            require_approval=True
        )
        self._log_result("Git init", result)
        
        # Step 5: Create .gitignore
        print("\n5. Creating .gitignore...")
        gitignore_content = """
__pycache__/
*.py[cod]
*$py.class
venv/
.env
.pytest_cache/
.coverage
dist/
build/
*.egg-info/
"""
        result = await self.executor.execute_command(
            f"cat > {project_dir}/.gitignore << 'EOF'\n{gitignore_content}\nEOF",
            require_approval=False
        )
        self._log_result("Create .gitignore", result)
        
        print(f"\n{'='*60}")
        print(f"✅ Project setup complete!")
        print(f"{'='*60}")
        
        return self._get_summary()
    
    async def install_dependencies(self, requirements: list, project_dir: Path):
        """
        Install Python dependencies.
        
        Args:
            requirements: List of package names
            project_dir: Project directory
        """
        print(f"\n{'='*60}")
        print(f"Installing dependencies")
        print(f"{'='*60}")
        
        for package in requirements:
            print(f"\nInstalling {package}...")
            
            # Use streaming to show installation progress
            def output_handler(line: str):
                if line.strip():
                    print(f"  {line}")
            
            result = await self.executor.execute_with_streaming(
                f"pip install {package}",
                output_callback=output_handler,
                require_approval=True
            )
            
            self._log_result(f"Install {package}", result)
            
            if not result.success:
                print(f"❌ Failed to install {package}")
                if result.recovery_suggestions:
                    print("Recovery suggestions:")
                    for suggestion in result.recovery_suggestions:
                        print(f"  - {suggestion}")
        
        return self._get_summary()
    
    async def run_tests(self, project_dir: Path):
        """
        Run project tests.
        
        Args:
            project_dir: Project directory
        """
        print(f"\n{'='*60}")
        print(f"Running tests")
        print(f"{'='*60}")
        
        # Try to run pytest
        print("\nExecuting pytest...")
        
        def output_handler(line: str):
            print(f"  {line}")
        
        result = await self.executor.execute_with_streaming(
            "pytest tests/ -v",
            output_callback=output_handler,
            require_approval=False
        )
        
        self._log_result("Run tests", result)
        
        if not result.success:
            print("\n⚠️  Tests failed or pytest not installed")
            if result.error_analysis:
                print(f"Error type: {result.error_analysis.error_type}")
                if result.recovery_suggestions:
                    print("Suggestions:")
                    for suggestion in result.recovery_suggestions:
                        print(f"  - {suggestion}")
        
        return self._get_summary()
    
    def _log_result(self, operation: str, result):
        """Log command result."""
        status = "✅" if result.success else "❌"
        self.commands_executed.append({
            'operation': operation,
            'command': result.command,
            'success': result.success,
            'duration': result.duration.total_seconds()
        })
        print(f"{status} {operation}: {result.status.value} ({result.duration.total_seconds():.2f}s)")
    
    def _get_summary(self):
        """Get workflow summary."""
        total = len(self.commands_executed)
        successful = sum(1 for cmd in self.commands_executed if cmd['success'])
        
        return {
            'total_commands': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total if total > 0 else 0
        }


async def demo_project_setup():
    """Demonstrate project setup workflow."""
    workflow = ProjectSetupWorkflow()
    
    # Setup a test project
    project_dir = Path("/tmp/demo_project_executor")
    
    # Clean up if exists
    import shutil
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    # Run setup
    summary = await workflow.setup_python_project("myapp", project_dir)
    
    print(f"\n{'='*60}")
    print("Workflow Summary")
    print(f"{'='*60}")
    print(f"Total Commands: {summary['total_commands']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    
    # Show statistics
    stats = workflow.executor.get_statistics()
    print(f"\nExecutor Statistics:")
    print(f"  Average Duration: {stats['average_duration']:.3f}s")
    print(f"  Total Duration: {sum(cmd['duration'] for cmd in workflow.commands_executed):.2f}s")


async def demo_error_recovery_workflow():
    """Demonstrate error recovery in a workflow."""
    print(f"\n{'='*60}")
    print("Error Recovery Workflow Demo")
    print(f"{'='*60}")
    
    executor = CommandExecutor()
    
    # Simulate a workflow with errors
    commands = [
        ("Check Python version", "python3 --version"),
        ("Try to use missing tool", "nonexistent_tool --help"),
        ("Check directory", "ls -la"),
        ("Try to read missing file", "cat missing_config.json"),
    ]
    
    for description, command in commands:
        print(f"\n{description}:")
        print(f"  Command: {command}")
        
        result = await executor.execute_command(command, require_approval=False)
        
        if result.success:
            print(f"  ✅ Success")
            if result.stdout.strip():
                print(f"  Output: {result.stdout.strip()[:100]}")
        else:
            print(f"  ❌ Failed")
            if result.error_analysis:
                print(f"  Error Type: {result.error_analysis.error_type}")
                print(f"  Recoverable: {result.error_analysis.is_recoverable}")
                
                if result.recovery_suggestions:
                    print(f"  Recovery Options:")
                    for suggestion in result.recovery_suggestions:
                        print(f"    - {suggestion}")


async def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("CommandExecutor Integration Examples")
    print("="*60)
    
    try:
        # Demo 1: Project setup workflow
        await demo_project_setup()
        
        # Demo 2: Error recovery workflow
        await demo_error_recovery_workflow()
        
        print("\n" + "="*60)
        print("✅ All integration demos completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
