#!/usr/bin/env python3
"""
Demo script for DiffEngine functionality.

Demonstrates unified diff, side-by-side diff, patch application,
and multi-file diff capabilities.
"""

from pathlib import Path
from src.codegenie.core.diff_engine import (
    DiffEngine,
    DiffFormat,
    FileDiff,
)


def demo_unified_diff():
    """Demonstrate unified diff generation."""
    print("=" * 60)
    print("Demo 1: Unified Diff")
    print("=" * 60)
    print()
    
    engine = DiffEngine(context_lines=3, colored_output=True)
    
    original = """def hello():
    print("Hello, World!")
    return True

def goodbye():
    print("Goodbye!")
"""
    
    modified = """def hello(name="World"):
    print(f"Hello, {name}!")
    return True

def goodbye(name="Friend"):
    print(f"Goodbye, {name}!")
    return False
"""
    
    # Generate diff
    diff = engine.generate_diff(original, modified, "example.py")
    
    # Show unified diff
    print(engine.show_unified_diff(diff))
    print()
    print(f"Statistics: +{diff.additions} -{diff.deletions}")
    print()


def demo_side_by_side_diff():
    """Demonstrate side-by-side diff."""
    print("=" * 60)
    print("Demo 2: Side-by-Side Diff")
    print("=" * 60)
    print()
    
    engine = DiffEngine(context_lines=2, colored_output=True)
    
    original = """class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
"""
    
    modified = """class Calculator:
    def add(self, a, b):
        \"\"\"Add two numbers.\"\"\"
        return a + b
    
    def subtract(self, a, b):
        \"\"\"Subtract b from a.\"\"\"
        return a - b
    
    def multiply(self, a, b):
        \"\"\"Multiply two numbers.\"\"\"
        return a * b
"""
    
    # Generate diff
    diff = engine.generate_diff(original, modified, "calculator.py")
    
    # Show side-by-side diff
    print(engine.show_side_by_side_diff(diff, width=100))
    print()


def demo_patch_application():
    """Demonstrate patch application."""
    print("=" * 60)
    print("Demo 3: Patch Application")
    print("=" * 60)
    print()
    
    engine = DiffEngine()
    
    # Create a temporary file
    test_file = Path("test_patch.txt")
    original_content = """Line 1
Line 2
Line 3
Line 4
Line 5
"""
    
    modified_content = """Line 1
Line 2 - Modified
Line 3
New Line 3.5
Line 4
Line 5
"""
    
    # Write original content
    test_file.write_text(original_content)
    print(f"Created test file: {test_file}")
    print()
    
    # Generate diff
    diff = engine.generate_diff(original_content, modified_content, str(test_file))
    
    print("Diff to apply:")
    print(engine.show_unified_diff(diff))
    print()
    
    # Apply diff (dry run first)
    print("Applying diff (dry run)...")
    result = engine.apply_diff(test_file, diff, dry_run=True)
    print(f"Dry run result: {result}")
    print()
    
    # Apply diff for real
    print("Applying diff...")
    result = engine.apply_diff(test_file, diff, dry_run=False)
    print(f"Result: {result}")
    print()
    
    # Show new content
    print("New file content:")
    print(test_file.read_text())
    
    # Cleanup
    test_file.unlink()
    print(f"Cleaned up test file: {test_file}")
    print()


def demo_selective_changes():
    """Demonstrate selective change application."""
    print("=" * 60)
    print("Demo 4: Selective Change Application")
    print("=" * 60)
    print()
    
    engine = DiffEngine()
    
    original = """def function1():
    pass

def function2():
    pass

def function3():
    pass
"""
    
    modified = """def function1():
    \"\"\"Function 1 with docstring.\"\"\"
    pass

def function2():
    \"\"\"Function 2 with docstring.\"\"\"
    pass

def function3():
    \"\"\"Function 3 with docstring.\"\"\"
    pass
"""
    
    # Generate diff
    diff = engine.generate_diff(original, modified, "functions.py")
    
    print("Full diff:")
    print(engine.show_unified_diff(diff))
    print()
    
    print(f"Total hunks: {len(diff.hunks)}")
    print()
    
    # Create test file
    test_file = Path("test_selective.py")
    test_file.write_text(original)
    
    # Apply only first hunk
    print("Applying only hunk 0...")
    result = engine.apply_selective_changes(test_file, diff, [0], dry_run=False)
    print(f"Result: {result}")
    print()
    
    print("New content:")
    print(test_file.read_text())
    
    # Cleanup
    test_file.unlink()
    print()


def demo_change_validation():
    """Demonstrate change validation."""
    print("=" * 60)
    print("Demo 5: Change Validation")
    print("=" * 60)
    print()
    
    engine = DiffEngine()
    
    # Valid Python
    original_py = "def hello():\n    pass\n"
    modified_py_valid = "def hello():\n    print('Hello')\n    return True\n"
    modified_py_invalid = "def hello(\n    print('Hello')\n"
    
    print("Validating valid Python change:")
    result = engine.validate_changes(original_py, modified_py_valid, 'python')
    print(f"Valid: {result['valid']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
    print()
    
    print("Validating invalid Python change:")
    result = engine.validate_changes(original_py, modified_py_invalid, 'python')
    print(f"Valid: {result['valid']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
    print()
    
    # Valid JSON
    original_json = '{"key": "value"}'
    modified_json_valid = '{"key": "new_value", "key2": "value2"}'
    modified_json_invalid = '{"key": "value"'
    
    print("Validating valid JSON change:")
    result = engine.validate_changes(original_json, modified_json_valid, 'json')
    print(f"Valid: {result['valid']}")
    print(f"Errors: {result['errors']}")
    print()
    
    print("Validating invalid JSON change:")
    result = engine.validate_changes(original_json, modified_json_invalid, 'json')
    print(f"Valid: {result['valid']}")
    print(f"Errors: {result['errors']}")
    print()


def demo_multi_file_diff():
    """Demonstrate multi-file diff."""
    print("=" * 60)
    print("Demo 6: Multi-File Diff")
    print("=" * 60)
    print()
    
    engine = DiffEngine()
    
    # Prepare multiple file changes
    file_changes = {
        Path("src/main.py"): (
            "def main():\n    pass\n",
            "def main():\n    print('Hello')\n    return 0\n"
        ),
        Path("src/utils.py"): (
            "",
            "def helper():\n    return True\n"
        ),
        Path("README.md"): (
            "# Project\n\nOld description\n",
            "# Project\n\nNew description with more details\n"
        ),
    }
    
    # Generate batch diff
    file_diffs = engine.generate_batch_diff(file_changes)
    
    # Show summary
    print(engine.show_diff_summary(file_diffs))
    print()
    
    # Show navigable diffs
    print("Detailed diffs:")
    print(engine.navigate_file_diffs(file_diffs, format=DiffFormat.UNIFIED))
    print()


def demo_patch_creation():
    """Demonstrate patch creation."""
    print("=" * 60)
    print("Demo 7: Patch Creation")
    print("=" * 60)
    print()
    
    engine = DiffEngine()
    
    # Create file diffs
    file_changes = {
        Path("file1.txt"): ("old content 1\n", "new content 1\n"),
        Path("file2.txt"): ("old content 2\n", "new content 2\n"),
    }
    
    file_diffs = engine.generate_batch_diff(file_changes)
    
    # Create patch
    patch = engine.create_patch(
        file_diffs,
        description="Update content in file1 and file2"
    )
    
    print(f"Patch created: {patch.description}")
    print(f"Files affected: {len(patch.file_diffs)}")
    print()
    
    # Show patch details
    for fd in patch.file_diffs:
        print(f"File: {fd.file_path}")
        print(f"Status: {fd.file_status}")
        print(f"Changes: +{fd.diff.additions} -{fd.diff.deletions}")
        print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "DiffEngine Demo" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    demos = [
        ("Unified Diff", demo_unified_diff),
        ("Side-by-Side Diff", demo_side_by_side_diff),
        ("Patch Application", demo_patch_application),
        ("Selective Changes", demo_selective_changes),
        ("Change Validation", demo_change_validation),
        ("Multi-File Diff", demo_multi_file_diff),
        ("Patch Creation", demo_patch_creation),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"Error in {name}: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(demos):
            input("\nPress Enter to continue to next demo...")
            print("\n")
    
    print("=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
