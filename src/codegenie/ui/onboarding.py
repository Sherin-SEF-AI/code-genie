"""
User onboarding and tutorial system for CodeGenie.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config


class OnboardingSystem:
    """Interactive onboarding system for new users."""
    
    def __init__(self, console: Console):
        self.console = console
        self.user_preferences = {}
    
    async def run_onboarding(self, project_path: Path) -> Dict[str, Any]:
        """Run the complete onboarding process."""
        
        # Welcome message
        await self._show_welcome()
        
        # Collect user information
        await self._collect_user_info()
        
        # Configure features
        await self._configure_features()
        
        # Setup project
        await self._setup_project(project_path)
        
        # Show quick start guide
        await self._show_quick_start()
        
        return self.user_preferences
    
    async def _show_welcome(self) -> None:
        """Show welcome message."""
        
        welcome_text = Text()
        welcome_text.append("🎉 Welcome to CodeGenie!\n\n", style="bold blue")
        welcome_text.append("CodeGenie is an advanced AI coding agent that helps you:\n", style="white")
        welcome_text.append("  • Write and refactor code autonomously\n", style="green")
        welcome_text.append("  • Coordinate multiple specialized AI agents\n", style="green")
        welcome_text.append("  • Learn from your coding patterns\n", style="green")
        welcome_text.append("  • Execute complex workflows automatically\n", style="green")
        welcome_text.append("  • Integrate with your development tools\n\n", style="green")
        welcome_text.append("Let's get you set up! This will only take a few minutes.\n", style="yellow")
        
        self.console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
        
        if not Confirm.ask("Ready to begin?", console=self.console, default=True):
            self.console.print("You can run onboarding later with: codegenie onboard", style="yellow")
            raise KeyboardInterrupt()
    
    async def _collect_user_info(self) -> None:
        """Collect user information and preferences."""
        
        self.console.print("\n📋 Let's learn about you", style="bold blue")
        
        # Experience level
        experience_levels = ["beginner", "intermediate", "advanced", "expert"]
        self.console.print("\nWhat's your coding experience level?")
        for i, level in enumerate(experience_levels, 1):
            self.console.print(f"  {i}. {level.title()}")
        
        level_choice = Prompt.ask(
            "Choose",
            choices=["1", "2", "3", "4"],
            default="2",
            console=self.console
        )
        self.user_preferences["skill_level"] = experience_levels[int(level_choice) - 1]
        
        # Primary languages
        self.console.print("\nWhat programming languages do you primarily use?")
        self.console.print("(Enter comma-separated list, e.g., python,javascript,go)")
        languages = Prompt.ask(
            "Languages",
            default="python",
            console=self.console
        )
        self.user_preferences["languages"] = [lang.strip() for lang in languages.split(",")]
        
        # Coding style
        coding_styles = ["concise", "verbose", "balanced"]
        self.console.print("\nWhat's your preferred coding style?")
        for i, style in enumerate(coding_styles, 1):
            self.console.print(f"  {i}. {style.title()}")
        
        style_choice = Prompt.ask(
            "Choose",
            choices=["1", "2", "3"],
            default="3",
            console=self.console
        )
        self.user_preferences["coding_style"] = coding_styles[int(style_choice) - 1]
        
        # Learning goals
        self.console.print("\nWhat would you like to improve? (comma-separated)")
        self.console.print("Examples: code quality, testing, performance, security, architecture")
        goals = Prompt.ask(
            "Learning goals",
            default="code quality,testing",
            console=self.console
        )
        self.user_preferences["learning_goals"] = [goal.strip() for goal in goals.split(",")]
    
    async def _configure_features(self) -> None:
        """Configure advanced features."""
        
        self.console.print("\n⚙️  Feature Configuration", style="bold blue")
        
        # Autonomous workflows
        self.console.print("\n🤖 Autonomous Workflows")
        self.console.print("  Allow CodeGenie to execute multi-step tasks automatically")
        self.user_preferences["autonomous_workflows"] = Confirm.ask(
            "Enable autonomous workflows?",
            console=self.console,
            default=True
        )
        
        # Multi-agent coordination
        self.console.print("\n👥 Multi-Agent Coordination")
        self.console.print("  Use specialized agents (architect, security, performance, etc.)")
        self.user_preferences["multi_agent_coordination"] = Confirm.ask(
            "Enable multi-agent coordination?",
            console=self.console,
            default=True
        )
        
        # Adaptive learning
        self.console.print("\n🎓 Adaptive Learning")
        self.console.print("  Learn from your patterns and provide personalized suggestions")
        self.user_preferences["adaptive_learning"] = Confirm.ask(
            "Enable adaptive learning?",
            console=self.console,
            default=True
        )
        
        # Proactive assistance
        self.console.print("\n💡 Proactive Assistance")
        self.console.print("  Automatically detect issues and suggest improvements")
        self.user_preferences["proactive_assistance"] = Confirm.ask(
            "Enable proactive assistance?",
            console=self.console,
            default=True
        )
    
    async def _setup_project(self, project_path: Path) -> None:
        """Setup project configuration."""
        
        self.console.print("\n📁 Project Setup", style="bold blue")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Setting up project configuration...", total=None)
            
            # Create configuration directory
            config_dir = project_path / ".codegenie"
            config_dir.mkdir(exist_ok=True)
            
            # Create configuration file
            config = Config.create_default()
            config.autonomous_workflows = self.user_preferences.get("autonomous_workflows", True)
            config.multi_agent_coordination = self.user_preferences.get("multi_agent_coordination", True)
            config.adaptive_learning = self.user_preferences.get("adaptive_learning", True)
            
            config_file = config_dir / "config.yaml"
            config.save(config_file)
            
            # Create user profile
            profile_file = config_dir / "user_profile.yaml"
            with open(profile_file, 'w') as f:
                import yaml
                yaml.dump(self.user_preferences, f, default_flow_style=False)
            
            progress.update(task, description="✅ Project setup complete!")
            await asyncio.sleep(0.5)
        
        self.console.print(f"✅ Configuration saved to {config_dir}", style="green")
    
    async def _show_quick_start(self) -> None:
        """Show quick start guide."""
        
        self.console.print("\n🚀 Quick Start Guide", style="bold blue")
        
        quick_start_text = """
[bold]Getting Started with CodeGenie:[/bold]

[cyan]1. Start the Agent[/cyan]
   codegenie start

[cyan]2. Try Natural Language Commands[/cyan]
   • "Create a REST API with authentication"
   • "Add unit tests for the user service"
   • "Refactor the database models"
   • "Analyze code for security issues"

[cyan]3. Use Autonomous Workflows[/cyan]
   codegenie workflow create "Build a complete user management system"

[cyan]4. Coordinate Multiple Agents[/cyan]
   codegenie agents coordinate "Review and optimize the entire codebase"

[cyan]5. Access Web Interface[/cyan]
   codegenie web start

[bold]Helpful Commands:[/bold]
   /help          - Show available commands
   /status        - Check agent status
   /insights      - Get project insights
   /learn         - Get learning suggestions

[bold]Need Help?[/bold]
   • Documentation: docs/USER_GUIDE.md
   • Tutorials: codegenie tutorial list
   • Support: docs/SUPPORT.md
"""
        
        self.console.print(Panel(quick_start_text, title="Quick Start", border_style="green"))
        
        # Ask if they want to start now
        if Confirm.ask("\nWould you like to start CodeGenie now?", console=self.console, default=True):
            self.console.print("\n🧞 Starting CodeGenie...", style="green")
            self.user_preferences["start_now"] = True
        else:
            self.console.print("\n👋 You can start CodeGenie anytime with: codegenie start", style="yellow")
            self.user_preferences["start_now"] = False


class TutorialSystem:
    """Interactive tutorial system."""
    
    def __init__(self, console: Console):
        self.console = console
        self.tutorials = {
            "basics": self._tutorial_basics,
            "workflows": self._tutorial_workflows,
            "agents": self._tutorial_agents,
            "learning": self._tutorial_learning,
            "advanced": self._tutorial_advanced
        }
    
    def list_tutorials(self) -> None:
        """List available tutorials."""
        
        table = Table(title="Available Tutorials")
        table.add_column("Tutorial", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Duration", style="yellow")
        table.add_column("Level", style="green")
        
        tutorials_info = [
            ("basics", "Getting started with CodeGenie", "5 min", "Beginner"),
            ("workflows", "Creating autonomous workflows", "10 min", "Intermediate"),
            ("agents", "Multi-agent coordination", "10 min", "Intermediate"),
            ("learning", "Adaptive learning features", "8 min", "Intermediate"),
            ("advanced", "Advanced features and customization", "15 min", "Advanced")
        ]
        
        for name, desc, duration, level in tutorials_info:
            table.add_row(name, desc, duration, level)
        
        self.console.print(table)
        self.console.print("\nRun a tutorial with: codegenie tutorial run <name>", style="blue")
    
    async def run_tutorial(self, tutorial_name: str) -> None:
        """Run a specific tutorial."""
        
        if tutorial_name not in self.tutorials:
            self.console.print(f"❌ Tutorial '{tutorial_name}' not found", style="red")
            self.console.print("Run 'codegenie tutorial list' to see available tutorials", style="yellow")
            return
        
        await self.tutorials[tutorial_name]()
    
    async def _tutorial_basics(self) -> None:
        """Basic tutorial."""
        
        self.console.print("\n📚 Tutorial: Getting Started with CodeGenie", style="bold blue")
        
        steps = [
            {
                "title": "Understanding CodeGenie",
                "content": """
CodeGenie is an AI coding agent that helps you write, refactor, and improve code.
It uses local AI models (via Ollama) to provide intelligent assistance without
sending your code to external servers.

Key Features:
• Natural language interaction
• Autonomous task execution
• Multi-agent coordination
• Adaptive learning
• Proactive assistance
                """
            },
            {
                "title": "Starting the Agent",
                "content": """
To start CodeGenie, simply run:
  codegenie start

This will:
1. Initialize the agent in your current directory
2. Scan and index your codebase
3. Start the interactive terminal interface

You can also specify options:
  codegenie start --autonomous    # Enable autonomous workflows
  codegenie start --multi-agent   # Enable multi-agent coordination
                """
            },
            {
                "title": "Natural Language Commands",
                "content": """
You can interact with CodeGenie using natural language:

Examples:
• "Create a new Python module for user authentication"
• "Add error handling to the login function"
• "Explain how the database connection works"
• "Find all TODO comments in the project"
• "Refactor the UserService class"

CodeGenie will understand your intent and execute the appropriate actions.
                """
            },
            {
                "title": "Special Commands",
                "content": """
CodeGenie also supports special commands starting with /:

/help          - Show available commands
/status        - Check agent status
/models        - List available AI models
/insights      - Get project insights
/test          - Run project tests
/analyze <file> - Analyze a specific file
/execute <code> - Execute code safely

Try them out to explore CodeGenie's capabilities!
                """
            }
        ]
        
        for i, step in enumerate(steps, 1):
            self.console.print(f"\n[bold cyan]Step {i}/{len(steps)}: {step['title']}[/bold cyan]")
            self.console.print(Panel(step['content'].strip(), border_style="blue"))
            
            if i < len(steps):
                if not Confirm.ask("Continue to next step?", console=self.console, default=True):
                    break
        
        self.console.print("\n✅ Tutorial complete!", style="green")
        self.console.print("Try starting CodeGenie with: codegenie start", style="blue")
    
    async def _tutorial_workflows(self) -> None:
        """Workflows tutorial."""
        
        self.console.print("\n📚 Tutorial: Autonomous Workflows", style="bold blue")
        
        workflow_text = """
[bold]What are Autonomous Workflows?[/bold]

Autonomous workflows allow CodeGenie to execute complex, multi-step tasks
automatically with minimal human intervention.

[bold cyan]Creating a Workflow:[/bold cyan]

1. Define your goal:
   codegenie workflow create "Build a REST API with authentication"

2. CodeGenie will:
   • Break down the goal into steps
   • Identify dependencies
   • Create an execution plan
   • Show you the plan for approval

3. Execute the workflow:
   • Approve the plan to start execution
   • CodeGenie will execute each step
   • Verify results after each step
   • Iterate if needed
   • Report progress in real-time

[bold cyan]Workflow Features:[/bold cyan]

• Parallel execution of independent tasks
• Automatic error recovery
• Checkpoint-based rollback
• Real-time progress tracking
• User intervention points

[bold cyan]Example Workflows:[/bold cyan]

• "Create a complete user management system"
• "Add comprehensive testing to the project"
• "Refactor the codebase for better performance"
• "Implement CI/CD pipeline"
• "Add security scanning and fixes"

[bold]Try it yourself:[/bold]
  codegenie workflow create "Your goal here"
        """
        
        self.console.print(Panel(workflow_text, border_style="green"))
    
    async def _tutorial_agents(self) -> None:
        """Multi-agent tutorial."""
        
        self.console.print("\n📚 Tutorial: Multi-Agent Coordination", style="bold blue")
        
        agents_text = """
[bold]Specialized AI Agents:[/bold]

CodeGenie includes specialized agents for different aspects of development:

[cyan]🏗️  Architect Agent[/cyan]
   • System design and architecture
   • Technology selection
   • Design patterns
   • Scalability planning

[cyan]👨‍💻 Developer Agent[/cyan]
   • Code implementation
   • Debugging assistance
   • Code review
   • Feature development

[cyan]🔒 Security Agent[/cyan]
   • Vulnerability scanning
   • Security best practices
   • Threat modeling
   • Automated fixes

[cyan]⚡ Performance Agent[/cyan]
   • Performance analysis
   • Optimization suggestions
   • Bottleneck detection
   • Resource monitoring

[cyan]✅ Tester Agent[/cyan]
   • Test generation
   • Test strategy
   • Quality assurance
   • Coverage analysis

[cyan]📝 Documentation Agent[/cyan]
   • Documentation generation
   • API documentation
   • Code comments
   • User guides

[bold]Using Multi-Agent Coordination:[/bold]

1. List available agents:
   codegenie agents list

2. Coordinate agents for a task:
   codegenie agents coordinate "Review and optimize the codebase"

3. Specify which agents to use:
   codegenie agents coordinate "Secure the API" --agents security,developer

The agents will work together, sharing context and coordinating their efforts
to complete the task efficiently.
        """
        
        self.console.print(Panel(agents_text, border_style="magenta"))
    
    async def _tutorial_learning(self) -> None:
        """Learning features tutorial."""
        
        self.console.print("\n📚 Tutorial: Adaptive Learning", style="bold blue")
        
        learning_text = """
[bold]Adaptive Learning Engine:[/bold]

CodeGenie learns from your coding patterns and preferences to provide
increasingly personalized assistance.

[bold cyan]What CodeGenie Learns:[/bold cyan]

• Your coding style (concise vs. verbose)
• Preferred design patterns
• Common workflows
• Technology preferences
• Error patterns
• Success patterns

[bold cyan]Providing Feedback:[/bold cyan]

Help CodeGenie learn by providing feedback:

1. Rate suggestions:
   codegenie learning feedback <suggestion_id> --rating 5

2. Add comments:
   codegenie learning feedback <suggestion_id> --rating 4 --comment "Good but verbose"

3. View your profile:
   codegenie learning profile

4. Adjust preferences:
   codegenie learning adapt --coding-style concise --skill-level advanced

[bold cyan]Benefits of Learning:[/bold cyan]

• More relevant suggestions
• Better code generation
• Personalized recommendations
• Improved accuracy over time
• Faster development

[bold]Privacy:[/bold]

All learning data is stored locally and encrypted. Your code and patterns
never leave your machine.
        """
        
        self.console.print(Panel(learning_text, border_style="yellow"))
    
    async def _tutorial_advanced(self) -> None:
        """Advanced features tutorial."""
        
        self.console.print("\n📚 Tutorial: Advanced Features", style="bold blue")
        
        advanced_text = """
[bold]Advanced CodeGenie Features:[/bold]

[bold cyan]1. Proactive Assistance[/bold cyan]

CodeGenie continuously monitors your codebase and proactively suggests
improvements:

• Detects code smells
• Identifies security issues
• Suggests performance optimizations
• Notices convention violations
• Recommends related updates

[bold cyan]2. Natural Language Programming[/bold cyan]

Describe what you want in plain English:

"Create a user authentication system with JWT tokens, password hashing,
email verification, and rate limiting"

CodeGenie will generate the complete implementation with tests and documentation.

[bold cyan]3. Terminal Integration[/bold cyan]

Use CodeGenie directly in your terminal:

• Natural language command execution
• Real-time output streaming
• Interactive sessions
• Shell integration

[bold cyan]4. Web Interface[/bold cyan]

Launch the web interface for complex workflows:

  codegenie web start

Features:
• Visual workflow management
• Agent coordination dashboard
• Learning profile management
• Configuration interface

[bold cyan]5. IDE Integration[/bold cyan]

CodeGenie integrates with popular IDEs:

• VS Code extension
• IntelliJ plugin
• Real-time code analysis
• Inline suggestions

[bold cyan]6. CI/CD Integration[/bold cyan]

Integrate with your CI/CD pipeline:

• Automated code review
• Security scanning
• Performance analysis
• Quality gates

[bold]Configuration:[/bold]

Customize CodeGenie with advanced configuration:

  codegenie config init --template full
  codegenie config set autonomous_workflows true
  codegenie config show
        """
        
        self.console.print(Panel(advanced_text, border_style="red"))
