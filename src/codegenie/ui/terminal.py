"""
Rich terminal interface for Claude Code Agent.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.align import Align

from ..core.agent import CodeGenieAgent

logger = logging.getLogger(__name__)


class TerminalUI:
    """Rich terminal interface for CodeGenie."""
    
    def __init__(self, agent: CodeGenieAgent, console: Console):
        self.agent = agent
        self.console = console
        self.running = False
        self.current_plan = None
        self.current_progress = None
    
    async def run(self) -> None:
        """Run the main terminal interface."""
        
        self.running = True
        
        # Display welcome message
        await self._display_welcome()
        
        # Main interaction loop
        while self.running:
            try:
                # Get user input
                user_input = await self._get_user_input()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                    continue
                
                # Process with agent
                await self._process_with_agent(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n👋 Goodbye!", style="yellow")
                break
            except Exception as e:
                self.console.print(f"\n❌ Error: {e}", style="red")
                logger.error(f"UI error: {e}")
    
    async def _display_welcome(self) -> None:
        """Display welcome message and status."""
        
        # Get agent status
        status = await self.agent.get_status()
        
        # Create welcome panel
        welcome_text = Text()
        welcome_text.append("🧞 CodeGenie v0.1.0\n", style="bold blue")
        welcome_text.append("Local AI coding assistant powered by Ollama\n\n", style="green")
        
        # Add project info
        if status.get("session_stats"):
            session_stats = status["session_stats"]
            project_info = session_stats.get("project_info", {})
            
            welcome_text.append("📁 Project Information:\n", style="bold")
            welcome_text.append(f"  Type: {project_info.get('type', 'Unknown')}\n", style="cyan")
            welcome_text.append(f"  Languages: {', '.join(project_info.get('languages', []))}\n", style="cyan")
            welcome_text.append(f"  Files: {project_info.get('file_count', 0)}\n", style="cyan")
            welcome_text.append(f"  Size: {project_info.get('size', 'Unknown')}\n\n", style="cyan")
        
        # Add model info
        if status.get("model_stats"):
            model_stats = status["model_stats"]
            welcome_text.append("🧠 Available Models:\n", style="bold")
            for model_name in model_stats.get("models", {}).keys():
                welcome_text.append(f"  • {model_name}\n", style="yellow")
            welcome_text.append("\n")
        
        welcome_text.append("💡 Tips:\n", style="bold")
        welcome_text.append("  • Type your coding requests in natural language\n", style="white")
        welcome_text.append("  • Use /help for available commands\n", style="white")
        welcome_text.append("  • Use /status to see current state\n", style="white")
        welcome_text.append("  • Use Ctrl+C to exit\n\n", style="white")
        
        welcome_text.append("Ready to help! What would you like to work on?", style="bold green")
        
        self.console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    async def _get_user_input(self) -> str:
        """Get user input with rich prompt."""
        
        try:
            user_input = Prompt.ask(
                "\n[bold blue]You[/bold blue]",
                console=self.console
            ).strip()
            return user_input
        except KeyboardInterrupt:
            return ""
    
    async def _handle_command(self, command: str) -> None:
        """Handle special commands."""
        
        cmd = command[1:].lower()
        
        if cmd == "help":
            await self._show_help()
        elif cmd == "status":
            await self._show_status()
        elif cmd == "models":
            await self._show_models()
        elif cmd == "memory":
            await self._show_memory()
        elif cmd == "suggestions":
            await self._show_suggestions()
        elif cmd == "clear":
            self.console.clear()
        elif cmd == "exit" or cmd == "quit":
            self.running = False
        else:
            self.console.print(f"Unknown command: {command}", style="red")
            self.console.print("Type /help for available commands", style="yellow")
    
    async def _show_help(self) -> None:
        """Show help information."""
        
        help_text = """
[bold]Available Commands:[/bold]

[cyan]/help[/cyan]          - Show this help message
[cyan]/status[/cyan]        - Show current agent status
[cyan]/models[/cyan]        - List available Ollama models
[cyan]/memory[/cyan]        - Show memory statistics
[cyan]/suggestions[/cyan]   - Get project suggestions
[cyan]/clear[/cyan]         - Clear the screen
[cyan]/exit[/cyan]          - Exit the agent

[bold]Usage Examples:[/bold]

[green]Create a REST API with authentication[/green]
[green]Debug the login function in auth.py[/green]
[green]Add unit tests for the user service[/green]
[green]Refactor the database models[/green]
[green]Optimize the performance of the search function[/green]
[green]Explain how the authentication system works[/green]
"""
        
        self.console.print(Panel(help_text, title="Help", border_style="green"))
    
    async def _show_status(self) -> None:
        """Show current agent status."""
        
        status = await self.agent.get_status()
        
        # Create status table
        table = Table(title="Agent Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        # Basic status
        table.add_row("Initialized", "✅ Yes" if status.get("initialized") else "❌ No")
        table.add_row("Thinking", "🤔 Yes" if status.get("thinking") else "😴 No")
        
        if status.get("current_task"):
            table.add_row("Current Task", status["current_task"][:50] + "...")
        
        # Session stats
        if status.get("session_stats"):
            session_stats = status["session_stats"]
            table.add_row("Session Duration", f"{session_stats.get('duration', 0):.1f}s")
            table.add_row("Conversation Turns", str(session_stats.get('conversation_turns', 0)))
            table.add_row("Successful Turns", str(session_stats.get('successful_turns', 0)))
            table.add_row("Failed Turns", str(session_stats.get('failed_turns', 0)))
        
        # Memory stats
        if status.get("memory_stats"):
            memory_stats = status["memory_stats"]
            table.add_row("Memory Entries", str(memory_stats.get('total_entries', 0)))
            table.add_row("Memory Size", f"{memory_stats.get('memory_size', 0) / 1024:.1f} KB")
        
        self.console.print(table)
    
    async def _show_models(self) -> None:
        """Show available models."""
        
        status = await self.agent.get_status()
        
        if not status.get("model_stats"):
            self.console.print("No model information available", style="red")
            return
        
        model_stats = status["model_stats"]
        models = model_stats.get("models", {})
        
        if not models:
            self.console.print("No models available", style="red")
            return
        
        # Create models table
        table = Table(title="Available Models")
        table.add_column("Model Name", style="cyan")
        table.add_column("Size", style="yellow")
        table.add_column("Capabilities", style="green")
        
        for model_name, model_info in models.items():
            capabilities = ", ".join(model_info.get("capabilities", []))
            size = model_info.get("size", "Unknown")
            table.add_row(model_name, str(size), capabilities)
        
        self.console.print(table)
    
    async def _show_memory(self) -> None:
        """Show memory statistics."""
        
        status = await self.agent.get_status()
        
        if not status.get("memory_stats"):
            self.console.print("No memory information available", style="red")
            return
        
        memory_stats = status["memory_stats"]
        
        # Create memory table
        table = Table(title="Memory Statistics")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="yellow")
        
        table.add_row("Total Entries", str(memory_stats.get("total_entries", 0)))
        table.add_row("Memory Size", f"{memory_stats.get('memory_size', 0) / 1024:.1f} KB")
        table.add_row("Max Memory Size", f"{memory_stats.get('max_memory_size', 0) / 1024:.1f} KB")
        
        # Add type breakdown
        types = memory_stats.get("types", {})
        for mem_type, count in types.items():
            table.add_row(f"  {mem_type.title()}", str(count))
        
        self.console.print(table)
    
    async def _show_suggestions(self) -> None:
        """Show project suggestions."""
        
        try:
            suggestions = await self.agent.get_suggestions()
            
            if not suggestions:
                self.console.print("No suggestions available", style="yellow")
                return
            
            suggestion_text = "\n".join(f"• {suggestion}" for suggestion in suggestions)
            
            self.console.print(Panel(
                suggestion_text,
                title="Project Suggestions",
                border_style="yellow"
            ))
            
        except Exception as e:
            self.console.print(f"Error getting suggestions: {e}", style="red")
    
    async def _process_with_agent(self, user_input: str) -> None:
        """Process user input with the agent."""
        
        # Show thinking indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("🤔 Thinking...", total=None)
            
            try:
                # Process with agent
                response = await self.agent.process_user_input(user_input)
                
                # Display response
                await self._display_response(response)
                
            except Exception as e:
                self.console.print(f"\n❌ Error: {e}", style="red")
                logger.error(f"Agent processing error: {e}")
    
    async def _display_response(self, response: str) -> None:
        """Display agent response with rich formatting."""
        
        # Check if response contains code
        if "```" in response:
            # Parse and display with syntax highlighting
            await self._display_response_with_code(response)
        else:
            # Display as markdown
            try:
                markdown = Markdown(response)
                self.console.print(markdown)
            except Exception:
                # Fallback to plain text
                self.console.print(response)
    
    async def _display_response_with_code(self, response: str) -> None:
        """Display response with code syntax highlighting."""
        
        parts = response.split("```")
        
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Regular text - display as markdown
                if part.strip():
                    try:
                        markdown = Markdown(part)
                        self.console.print(markdown)
                    except Exception:
                        self.console.print(part)
            else:
                # Code block
                lines = part.split('\n')
                if lines:
                    language = lines[0].strip()
                    code = '\n'.join(lines[1:])
                    
                    if language and code.strip():
                        # Display with syntax highlighting
                        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
                        self.console.print(Panel(syntax, title=f"Code ({language})", border_style="green"))
                    else:
                        # Plain code block
                        self.console.print(Panel(code, title="Code", border_style="green"))
    
    async def display_plan(self, plan: Any) -> None:
        """Display a plan with rich formatting."""
        
        # Create plan table
        table = Table(title=f"Plan: {plan.goal}")
        table.add_column("Step", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Duration", style="green")
        table.add_column("Status", style="magenta")
        
        for step in plan.steps:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(step.status, "❓")
            
            table.add_row(
                step.id,
                step.description[:50] + "..." if len(step.description) > 50 else step.description,
                step.action_type,
                f"{step.estimated_duration}s",
                f"{status_icon} {step.status}"
            )
        
        self.console.print(table)
        
        # Show success criteria
        if plan.success_criteria:
            criteria_text = "\n".join(f"• {criteria}" for criteria in plan.success_criteria)
            self.console.print(Panel(
                criteria_text,
                title="Success Criteria",
                border_style="green"
            ))
    
    async def display_progress(self, current_step: str, progress: float, total_steps: int) -> None:
        """Display progress for plan execution."""
        
        progress_text = f"Executing: {current_step} ({progress:.1%})"
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        ) as progress_bar:
            task = progress_bar.add_task(progress_text, total=100, completed=progress * 100)
            
            # Keep the progress bar visible for a moment
            await asyncio.sleep(0.1)
    
    async def confirm_action(self, message: str) -> bool:
        """Ask for user confirmation."""
        
        return Confirm.ask(message, console=self.console)
    
    async def display_error(self, error: str, details: Optional[str] = None) -> None:
        """Display an error message."""
        
        error_text = Text()
        error_text.append("❌ Error: ", style="bold red")
        error_text.append(error, style="red")
        
        if details:
            error_text.append(f"\n\nDetails: {details}", style="dim")
        
        self.console.print(Panel(error_text, title="Error", border_style="red"))
    
    async def display_success(self, message: str) -> None:
        """Display a success message."""
        
        success_text = Text()
        success_text.append("✅ ", style="bold green")
        success_text.append(message, style="green")
        
        self.console.print(Panel(success_text, title="Success", border_style="green"))
    
    async def display_info(self, message: str) -> None:
        """Display an info message."""
        
        info_text = Text()
        info_text.append("ℹ️ ", style="bold blue")
        info_text.append(message, style="blue")
        
        self.console.print(Panel(info_text, title="Info", border_style="blue"))
