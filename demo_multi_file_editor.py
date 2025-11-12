#!/usr/bin/env python3
"""
Demo script for Multi-File Editor functionality.

This demonstrates:
- Change planning and coordination
- Cross-file refactoring
- Atomic operations
- Import management
- Symbol refactoring
- Change validation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from codegenie.core.multi_file_editor import (
    MultiFileEditor,
    ChangeSet,
    FileEdit,
    EditType
)


def demo_change_planning():
    """Demonstrate change planning."""
    print("\n" + "="*60)
    print("DEMO: Change Planning")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Plan changes
    change_set = editor.plan_changes(
        intent="Refactor authentication module",
        files=[Path("src/codegenie/core/agent.py")]
    )
    
    print(f"\nChange Set: {change_set.intent}")
    print(f"Affected Files: {len(change_set.affected_files)}")
    print(f"Estimated Impact: {change_set.estimated_impact}")
    print(f"Dependencies: {len(change_set.dependencies)}")


def demo_import_management():
    """Demonstrate import management."""
    print("\n" + "="*60)
    print("DEMO: Import Management")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create a test file
    test_file = Path("test_imports.py")
    test_content = """import os
import sys
from pathlib import Path
from typing import Dict, List

def example():
    # Only using Path, not Dict or List
    p = Path('.')
    return p
"""
    
    test_file.write_text(test_content)
    print(f"\nCreated test file: {test_file}")
    
    # Remove unused imports
    print("\nRemoving unused imports...")
    edit = editor.remove_unused_imports(test_file, dry_run=True)
    
    if edit:
        print(f"Would remove unused imports from {test_file}")
        print(f"Description: {edit.description}")
    else:
        print("No unused imports found")
    
    # Organize imports
    print("\nOrganizing imports...")
    edit = editor.organize_imports(test_file, dry_run=True)
    
    if edit:
        print(f"Would organize imports in {test_file}")
        print(f"Description: {edit.description}")
    
    # Clean up
    test_file.unlink()
    print(f"\nCleaned up test file")


def demo_symbol_refactoring():
    """Demonstrate symbol refactoring."""
    print("\n" + "="*60)
    print("DEMO: Symbol Refactoring")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test files
    test_file1 = Path("test_refactor1.py")
    test_file2 = Path("test_refactor2.py")
    
    test_file1.write_text("""
class OldClassName:
    def method(self):
        return "old"

def use_old_class():
    obj = OldClassName()
    return obj.method()
""")
    
    test_file2.write_text("""
from test_refactor1 import OldClassName

def another_use():
    obj = OldClassName()
    return obj
""")
    
    print(f"\nCreated test files: {test_file1}, {test_file2}")
    
    # Refactor symbol
    print("\nRefactoring symbol: OldClassName -> NewClassName")
    edits = editor.refactor_symbol(
        "OldClassName",
        "NewClassName",
        scope="project",
        files=[test_file1, test_file2]
    )
    
    print(f"Would refactor symbol in {len(edits)} files:")
    for edit in edits:
        print(f"  - {edit.file_path}: {edit.description}")
    
    # Clean up
    test_file1.unlink()
    test_file2.unlink()
    print(f"\nCleaned up test files")


def demo_file_move():
    """Demonstrate file move with reference updates."""
    print("\n" + "="*60)
    print("DEMO: File Move with Reference Updates")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test files
    old_path = Path("old_module.py")
    new_path = Path("new_module.py")
    
    old_path.write_text("""
def important_function():
    return "important"
""")
    
    print(f"\nCreated test file: {old_path}")
    
    # Plan file move
    print(f"\nPlanning move: {old_path} -> {new_path}")
    change_set = editor.move_rename_file(old_path, new_path, update_references=True)
    
    print(f"Change Set: {change_set.intent}")
    print(f"Total Edits: {len(change_set.file_edits)}")
    print(f"Affected Files: {len(change_set.affected_files)}")
    
    for edit in change_set.file_edits[:5]:  # Show first 5
        print(f"  - {edit.edit_type.value}: {edit.file_path}")
    
    # Clean up
    if old_path.exists():
        old_path.unlink()
    print(f"\nCleaned up test file")


def demo_change_validation():
    """Demonstrate change validation."""
    print("\n" + "="*60)
    print("DEMO: Change Validation")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test file with valid Python
    test_file = Path("test_validation.py")
    valid_content = """
def valid_function():
    x = 10
    y = 20
    return x + y
"""
    
    test_file.write_text(valid_content)
    print(f"\nCreated test file: {test_file}")
    
    # Validate syntax
    print("\nValidating syntax of valid code...")
    result = editor.validate_syntax(test_file)
    print(f"Valid: {result['valid']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
    
    # Test with invalid syntax
    invalid_content = """
def invalid_function()
    x = 10
    return x
"""
    
    print("\nValidating syntax of invalid code...")
    result = editor.validate_syntax(test_file, invalid_content)
    print(f"Valid: {result['valid']}")
    print(f"Errors: {result['errors']}")
    
    # Validate semantics
    print("\nValidating semantics...")
    result = editor.validate_semantics(test_file)
    print(f"Valid: {result['valid']}")
    print(f"Warnings: {result['warnings']}")
    
    # Clean up
    test_file.unlink()
    print(f"\nCleaned up test file")


def demo_atomic_operations():
    """Demonstrate atomic operations."""
    print("\n" + "="*60)
    print("DEMO: Atomic Operations")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test files
    test_files = []
    for i in range(3):
        test_file = Path(f"test_atomic_{i}.py")
        test_file.write_text(f"# Test file {i}\n")
        test_files.append(test_file)
    
    print(f"\nCreated {len(test_files)} test files")
    
    # Create a change set
    change_set = ChangeSet(intent="Atomic test changes")
    
    for test_file in test_files:
        edit = FileEdit(
            file_path=test_file,
            edit_type=EditType.REPLACE,
            old_content=test_file.read_text(),
            new_content=f"# Modified file {test_file.name}\n",
            description=f"Modify {test_file.name}"
        )
        change_set.file_edits.append(edit)
        change_set.affected_files.add(test_file)
    
    print(f"\nChange set created with {len(change_set.file_edits)} edits")
    print(f"Atomic: {change_set.is_atomic}")
    
    # Validate change set
    print("\nValidating change set...")
    validation = editor.validate_changes(change_set)
    print(f"Valid: {validation['valid']}")
    print(f"Errors: {validation['errors']}")
    
    # Clean up
    for test_file in test_files:
        if test_file.exists():
            test_file.unlink()
    print(f"\nCleaned up test files")


def demo_cross_file_refactoring():
    """Demonstrate cross-file refactoring."""
    print("\n" + "="*60)
    print("DEMO: Cross-File Refactoring")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test files
    file1 = Path("test_cross1.py")
    file2 = Path("test_cross2.py")
    file3 = Path("test_cross3.py")
    
    file1.write_text("""
OLD_CONSTANT = 42

def use_constant():
    return OLD_CONSTANT
""")
    
    file2.write_text("""
from test_cross1 import OLD_CONSTANT

def another_use():
    return OLD_CONSTANT * 2
""")
    
    file3.write_text("""
from test_cross1 import OLD_CONSTANT

class MyClass:
    value = OLD_CONSTANT
""")
    
    print(f"\nCreated test files: {file1}, {file2}, {file3}")
    
    # Perform cross-file refactoring
    print("\nPerforming cross-file refactoring: OLD_CONSTANT -> NEW_CONSTANT")
    change_set = editor.refactor_across_files(
        refactoring_type="rename_symbol",
        target="OLD_CONSTANT",
        replacement="NEW_CONSTANT",
        files=[file1, file2, file3]
    )
    
    print(f"\nChange Set: {change_set.intent}")
    print(f"File Edits: {len(change_set.file_edits)}")
    print(f"Affected Files: {len(change_set.affected_files)}")
    
    for edit in change_set.file_edits:
        print(f"  - {edit.file_path.name}: {edit.description}")
    
    # Clean up
    for f in [file1, file2, file3]:
        if f.exists():
            f.unlink()
    print(f"\nCleaned up test files")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("MULTI-FILE EDITOR DEMO")
    print("="*60)
    
    try:
        demo_change_planning()
        demo_import_management()
        demo_symbol_refactoring()
        demo_file_move()
        demo_change_validation()
        demo_atomic_operations()
        demo_cross_file_refactoring()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
