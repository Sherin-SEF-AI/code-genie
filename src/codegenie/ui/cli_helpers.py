"""
CLI Helper utilities for enhanced user experience.

Provides:
- Interactive prompts with validation
- Progress indicators and spinners
- Colored and formatted output
- Command history management
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

logger = logging.getLogger(__name__)


class CommandHistory:
    """Manages command history for the CLI."""
    
    def __init__(self, history_file: Optional[Path] = None):
        """Initialize command history."""
        if history_file is None:
            history_file = Path.home() / ".codegenie" / "history.json"
        
        self.history_file = history_file
        self.history: List[Dict[str, Any]] = []
        self._load_history()
    
    def _load_history(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load command history: {e}")
                self.history = []
        else:
            self.history = []
    
    def _save_history(self) -> None:
        """Save history to file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save command history: {e}")
    
    def add_command(
        self,
        command: str,
        args: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Add a command to history."""
        entry = {
            'command': command,
            'args': args,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'error': error,
        }
        
        self.history.append(entry)
        
        # Keep only last 1000 commands
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        self._save_history()
    
    def get_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent commands."""
        return self.history[-count:]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search command history."""
        results = []
        query_lower = query.lower()
        
        for entry in self.history:
            if query_lower in entry['command'].lower():
                results.append(entry)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get command usage statistics."""
        if not self.history:
            return {
                'total_commands': 0,
                'success_rate': 0.0,
                'most_used': [],
            }
        
        total = len(self.history)
        successful = sum(1 for e in self.history if e['success'])
        
        # Count command usage
        command_counts: Dict[str, int] = {}
        for entry in self.history:
            cmd = entry['command']
            command_counts[cmd] = command_counts.get(cmd, 0) + 1
        
        # Get most used commands
        most_used = sorted(
            command_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_commands': total,
            'success_rate': successful / total if total > 0 else 0.0,
            'most_used': most_used,
        }


class InteractivePrompt:
    """Enhanced interactive prompts with validation."""
    
    def __init__(self, console: Console):
        """Initialize interactive prompt."""
        self.console = console
    
    def ask_text(
        self,
        question: str,
        default: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input. Please try again.",
    ) -> str:
        """Ask for text input with validation."""
        while True:
            response = Prompt.ask(question, default=default, console=self.console)
            
            if validator is None or validator(response):
                return response
            
            self.console.print(error_message, style="red")
    
    def ask_choice(
        self,
        question: str,
        choices: List[str],
        default: Optional[str] = None,
    ) -> str:
        """Ask user to choose from a list of options."""
        # Display choices
        self.console.print(f"\n{question}", style="bold blue")
        for i, choice in enumerate(choices, 1):
            self.console.print(f"  {i}. {choice}", style="cyan")
        
        # Get selection
        while True:
            response = Prompt.ask(
                "Select option",
                choices=[str(i) for i in range(1, len(choices) + 1)],
                default=str(choices.index(default) + 1) if default in choices else None,
                console=self.console,
            )
            
            try:
                index = int(response) - 1
                if 0 <= index < len(choices):
                    return choices[index]
            except ValueError:
                pass
            
            self.console.print("Invalid selection. Please try again.", style="red")
    
    def ask_multiple_choice(
        self,
        question: str,
        choices: List[str],
        min_selections: int = 1,
        max_selections: Optional[int] = None,
    ) -> List[str]:
        """Ask user to select multiple options."""
        self.console.print(f"\n{question}", style="bold blue")
        self.console.print("(Enter numbers separated by commas, e.g., 1,3,5)", style="dim")
        
        for i, choice in enumerate(choices, 1):
            self.console.print(f"  {i}. {choice}", style="cyan")
        
        while True:
            response = Prompt.ask("Select options", console=self.console)
            
            try:
                indices = [int(x.strip()) - 1 for x in response.split(',')]
                
                # Validate selections
                if not all(0 <= i < len(choices) for i in indices):
                    self.console.print("Invalid selection. Please try again.", style="red")
                    continue
                
                if len(indices) < min_selections:
                    self.console.print(
                        f"Please select at least {min_selections} option(s).",
                        style="red"
                    )
                    continue
                
                if max_selections and len(indices) > max_selections:
                    self.console.print(
                        f"Please select at most {max_selections} option(s).",
                        style="red"
                    )
                    continue
                
                return [choices[i] for i in indices]
                
            except (ValueError, IndexError):
                self.console.print("Invalid input. Please try again.", style="red")
    
    def ask_confirm(
        self,
        question: str,
        default: bool = False,
    ) -> bool:
        """Ask for yes/no confirmation."""
        return Confirm.ask(question, default=default, console=self.console)
    
    def ask_number(
        self,
        question: str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> int:
        """Ask for numeric input with validation."""
        while True:
            value = IntPrompt.ask(question, default=default, console=self.console)
            
            if min_value is not None and value < min_value:
                self.console.print(f"Value must be at least {min_value}", style="red")
                continue
            
            if max_value is not None and value > max_value:
                self.console.print(f"Value must be at most {max_value}", style="red")
                continue
            
            return value


class ProgressIndicator:
    """Enhanced progress indicators for long-running operations."""
    
    def __init__(self, console: Console):
        """Initialize progress indicator."""
        self.console = console
    
    def spinner(self, description: str = "Processing..."):
        """Create a spinner progress indicator."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )
    
    def bar(self, description: str = "Processing..."):
        """Create a progress bar."""
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
    
    def multi_task(self):
        """Create a multi-task progress indicator."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )


class OutputFormatter:
    """Enhanced output formatting utilities."""
    
    def __init__(self, console: Console):
        """Initialize output formatter."""
        self.console = console
    
    def success(self, message: str) -> None:
        """Display success message."""
        self.console.print(f"✅ {message}", style="bold green")
    
    def error(self, message: str) -> None:
        """Display error message."""
        self.console.print(f"❌ {message}", style="bold red")
    
    def warning(self, message: str) -> None:
        """Display warning message."""
        self.console.print(f"⚠️  {message}", style="bold yellow")
    
    def info(self, message: str) -> None:
        """Display info message."""
        self.console.print(f"ℹ️  {message}", style="bold blue")
    
    def header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Display a header."""
        text = Text()
        text.append(title, style="bold blue")
        if subtitle:
            text.append(f"\n{subtitle}", style="dim")
        
        self.console.print(Panel(text, border_style="blue"))
    
    def section(self, title: str) -> None:
        """Display a section header."""
        self.console.print(f"\n{title}", style="bold blue")
        self.console.print("─" * len(title), style="blue")
    
    def code(self, code: str, language: str = "python") -> None:
        """Display syntax-highlighted code."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def table(
        self,
        title: str,
        columns: List[str],
        rows: List[List[str]],
        column_styles: Optional[List[str]] = None,
    ) -> None:
        """Display a formatted table."""
        table = Table(title=title)
        
        for i, column in enumerate(columns):
            style = column_styles[i] if column_styles and i < len(column_styles) else "white"
            table.add_column(column, style=style)
        
        for row in rows:
            table.add_row(*row)
        
        self.console.print(table)
    
    def tree(self, title: str, structure: Dict[str, Any]) -> None:
        """Display a tree structure."""
        tree = Tree(title)
        self._build_tree(tree, structure)
        self.console.print(tree)
    
    def _build_tree(self, parent, structure: Dict[str, Any]) -> None:
        """Recursively build tree structure."""
        for key, value in structure.items():
            if isinstance(value, dict):
                branch = parent.add(f"📁 {key}")
                self._build_tree(branch, value)
            elif isinstance(value, list):
                branch = parent.add(f"📋 {key}")
                for item in value:
                    if isinstance(item, dict):
                        self._build_tree(branch, item)
                    else:
                        branch.add(f"• {item}")
            else:
                parent.add(f"📄 {key}: {value}")
    
    def list_items(
        self,
        items: List[str],
        title: Optional[str] = None,
        style: str = "cyan",
    ) -> None:
        """Display a list of items."""
        if title:
            self.console.print(f"\n{title}", style="bold blue")
        
        for item in items:
            self.console.print(f"  • {item}", style=style)
    
    def key_value(
        self,
        data: Dict[str, Any],
        title: Optional[str] = None,
    ) -> None:
        """Display key-value pairs."""
        if title:
            self.console.print(f"\n{title}", style="bold blue")
        
        max_key_length = max(len(str(k)) for k in data.keys()) if data else 0
        
        for key, value in data.items():
            key_str = str(key).ljust(max_key_length)
            self.console.print(f"  {key_str} : {value}", style="white")
