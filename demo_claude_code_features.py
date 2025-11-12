#!/usr/bin/env python3
"""
Demo of Claude Code-like Features in CodeGenie
Showcases context awareness, multi-file editing, and intelligent completions
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.claude_code_features import ClaudeCodeFeatures
from codegenie.core.multi_file_editor import EditType
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


async def demo_context_awareness():
    """Demo 1: Context Awareness"""
    console = Console()
    
    console.print("\n" + "="*60, style="blue")
    console.print("Demo 1: Context Awareness (Like Claude Code)", style="bold blue")
    console.print("="*60 + "\n", style="blue")
    
    # Initialize features
    features = ClaudeCodeFeatures(Path.cwd())
    
    # Add files to context
    console.print("📁 Adding files to context...", style="cyan")
    test_files = [
        Path("src/codegenie/core/agent.py"),
        Path("src/codegenie/core/config.py"),
    ]
    
    for file_path in test_files:
        if file_path.exists():
            features.add_file_to_context(file_path)
            console.print(f"  ✓ Added: {file_path}", style="green")
    
    # Get context summary
    console.print("\n📊 Context Summary:", style="cyan")
    summary = features.get_context_summary()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Files in Context", str(len(summary['current_files'])))
    table.add_row("Symbols Indexed", str(summary['total_symbols_indexed']))
    table.add_row("Recent Edits", str(summary['recent_edits_count']))
    
    console.print(table)
    
    # Process a context-aware request
    console.print("\n💬 Processing context-aware request...", style="cyan")
    request = "Explain how the agent initialization works"
    console.print(f"  Request: '{request}'", style="yellow")
    
    result = await features.process_request(request)
    console.print(f"  Intent: {result['intent']}", style="green")
    console.print(f"  Action: {result['action']}", style="green")


async def demo_multi_file_editing():
    """Demo 2: Multi-File Editing"""
    console = Console()
    
    console.print("\n" + "="*60, style="blue")
    console.print("Demo 2: Multi-File Editing (Like Claude Code)", style="bold blue")
    console.print("="*60 + "\n", style="blue")
    
    features = ClaudeCodeFeatures(Path.cwd())
    
    # Create a test file
    test_file = Path("demo_test_file.py")
    console.print(f"📝 Creating test file: {test_file}", style="cyan")
    
    initial_content = '''def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
'''
    
    # Create file edit
    create_edit = features.multi_file_editor.create_file(
        test_file,
        initial_content,
        "Create demo file"
    )
    
    # Apply edit
    result = await features.apply_multi_file_edit(
        "Create demo file",
        [create_edit],
        preview=False
    )
    
    if result['success']:
        console.print("  ✓ File created successfully", style="green")
    
    # Show file content
    console.print("\n📄 Initial Content:", style="cyan")
    syntax = Syntax(initial_content, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    # Modify the file
    console.print("\n✏️  Modifying file...", style="cyan")
    
    modify_edit = features.multi_file_editor.replace_lines(
        test_file,
        2,
        2,
        '    print("Hello from CodeGenie!")\n',
        "Update hello message"
    )
    
    # Preview the edit
    console.print("\n🔍 Edit Preview:", style="cyan")
    preview = features.multi_file_editor.preview_edit(modify_edit)
    console.print(preview)
    
    # Apply the edit
    result = await features.apply_multi_file_edit(
        "Update hello message",
        [modify_edit],
        preview=False
    )
    
    if result['success']:
        console.print("\n  ✓ Edit applied successfully", style="green")
        
        # Show updated content
        with open(test_file) as f:
            updated_content = f.read()
        
        console.print("\n📄 Updated Content:", style="cyan")
        syntax = Syntax(updated_content, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
        console.print("\n🧹 Cleaned up test file", style="yellow")


async def demo_intelligent_completions():
    """Demo 3: Intelligent Completions"""
    console = Console()
    
    console.print("\n" + "="*60, style="blue")
    console.print("Demo 3: Intelligent Completions (Like Claude Code)", style="bold blue")
    console.print("="*60 + "\n", style="blue")
    
    features = ClaudeCodeFeatures(Path.cwd())
    
    # Create a test file for completions
    test_file = Path("demo_completion_test.py")
    test_content = '''import os
import sys

def calculate_sum(a, b):
    """Calculate sum of two numbers"""
    return a + b

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self):
        for 
'''
    
    test_file.write_text(test_content)
    
    console.print("📝 Test file created with incomplete code", style="cyan")
    console.print("\n📄 File Content:", style="cyan")
    syntax = Syntax(test_content, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    # Get completions at the incomplete line
    console.print("\n💡 Getting completions for line 13 (incomplete for loop)...", style="cyan")
    
    completions = await features.get_completions(test_file, 13, 12)
    
    if completions:
        console.print(f"\n  Found {len(completions)} completions:", style="green")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Suggestion", style="green")
        table.add_column("Confidence", style="yellow")
        
        for completion in completions[:5]:
            table.add_row(
                completion.completion_type.value,
                completion.text[:50] + "..." if len(completion.text) > 50 else completion.text,
                f"{completion.confidence:.0%}"
            )
        
        console.print(table)
    
    # Suggest next line
    console.print("\n🔮 Suggesting next line...", style="cyan")
    next_line = await features.suggest_next_line(test_file)
    
    if next_line:
        console.print(f"  Suggestion: {next_line}", style="green")
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
        console.print("\n🧹 Cleaned up test file", style="yellow")


async def demo_symbol_operations():
    """Demo 4: Symbol Operations"""
    console = Console()
    
    console.print("\n" + "="*60, style="blue")
    console.print("Demo 4: Symbol Operations (Like Claude Code)", style="bold blue")
    console.print("="*60 + "\n", style="blue")
    
    features = ClaudeCodeFeatures(Path.cwd())
    
    # Add files to context
    console.print("📁 Indexing project files...", style="cyan")
    
    # Index a few Python files
    python_files = list(Path("src/codegenie/core").glob("*.py"))[:3]
    for file_path in python_files:
        features.add_file_to_context(file_path)
        console.print(f"  ✓ Indexed: {file_path.name}", style="green")
    
    # Find references to a symbol
    console.print("\n🔍 Finding references to 'Config'...", style="cyan")
    references = await features.find_references("Config")
    
    if references:
        console.print(f"\n  Found {len(references)} references:", style="green")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        table.add_column("Line", style="yellow")
        table.add_column("Type", style="green")
        
        for ref in references[:5]:
            table.add_row(
                Path(ref['file']).name,
                str(ref['line']),
                ref['type']
            )
        
        console.print(table)


async def demo_code_review():
    """Demo 5: Code Review Suggestions"""
    console = Console()
    
    console.print("\n" + "="*60, style="blue")
    console.print("Demo 5: Code Review (Like Claude Code)", style="bold blue")
    console.print("="*60 + "\n", style="blue")
    
    features = ClaudeCodeFeatures(Path.cwd())
    
    # Create a file with some issues
    test_file = Path("demo_review_test.py")
    test_content = '''def long_function():
    # This function is too long and has issues
    x = 1
    y = 2
    z = 3
    # ... imagine 50 more lines here ...
    try:
        result = x + y + z
    except:
        pass
    return result

class MyClass:
    def method(self):
        pass
'''
    
    test_file.write_text(test_content)
    features.add_file_to_context(test_file)
    
    console.print("📝 Analyzing code for issues...", style="cyan")
    
    # Get code review
    result = await features.process_request("Review the code in demo_review_test.py")
    
    if 'suggestions' in result and result['suggestions']:
        console.print(f"\n  Found {len(result['suggestions'])} suggestions:", style="yellow")
        
        for i, suggestion in enumerate(result['suggestions'], 1):
            console.print(f"\n  {i}. {suggestion['type'].upper()} (Line {suggestion['line']})", style="cyan")
            console.print(f"     {suggestion['message']}", style="yellow")
            console.print(f"     💡 {suggestion['suggestion']}", style="green")
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
        console.print("\n🧹 Cleaned up test file", style="yellow")


async def demo_statistics():
    """Demo 6: Usage Statistics"""
    console = Console()
    
    console.print("\n" + "="*60, style="blue")
    console.print("Demo 6: Usage Statistics", style="bold blue")
    console.print("="*60 + "\n", style="blue")
    
    features = ClaudeCodeFeatures(Path.cwd())
    
    # Add some files to context
    python_files = list(Path("src/codegenie/core").glob("*.py"))[:5]
    for file_path in python_files:
        features.add_file_to_context(file_path)
    
    # Get statistics
    stats = features.get_statistics()
    
    console.print("📊 CodeGenie Statistics:", style="cyan")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Files in Context", str(stats['files_in_context']))
    table.add_row("Symbols Indexed", str(stats['symbols_indexed']))
    table.add_row("Recent Edits", str(stats['recent_edits']))
    table.add_row("Edit History", str(stats['edit_history']))
    table.add_row("IDE Connected", "Yes" if stats['ide_connected'] else "No")
    
    console.print(table)


async def main():
    """Run all demos"""
    console = Console()
    
    console.print("\n" + "="*60, style="bold blue")
    console.print("🧞 CodeGenie - Claude Code Features Demo", style="bold blue")
    console.print("="*60 + "\n", style="bold blue")
    
    console.print("This demo showcases Claude Code-like features:", style="cyan")
    console.print("  • Context-aware code understanding", style="green")
    console.print("  • Multi-file editing capabilities", style="green")
    console.print("  • Intelligent code completions", style="green")
    console.print("  • Symbol operations (find references, refactor)", style="green")
    console.print("  • Code review and suggestions", style="green")
    console.print("  • Usage statistics and insights", style="green")
    
    try:
        await demo_context_awareness()
        await demo_multi_file_editing()
        await demo_intelligent_completions()
        await demo_symbol_operations()
        await demo_code_review()
        await demo_statistics()
        
        console.print("\n" + "="*60, style="bold green")
        console.print("✅ All demos completed successfully!", style="bold green")
        console.print("="*60 + "\n", style="bold green")
        
        console.print("🎯 Key Features Demonstrated:", style="bold blue")
        console.print("  ✓ Context awareness across multiple files", style="green")
        console.print("  ✓ Coordinated multi-file editing", style="green")
        console.print("  ✓ Intelligent code completions", style="green")
        console.print("  ✓ Symbol indexing and search", style="green")
        console.print("  ✓ Automated code review", style="green")
        console.print("  ✓ Real-time statistics", style="green")
        
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}", style="red")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
