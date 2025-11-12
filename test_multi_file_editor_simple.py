#!/usr/bin/env python3
"""
Simple test for Multi-File Editor functionality.
Tests core features without requiring full dependencies.
"""

import sys
import ast
from pathlib import Path

# Test the multi_file_editor module directly
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from codegenie.core.multi_file_editor import (
    MultiFileEditor,
    ChangeSet,
    FileEdit,
    EditType,
    ChangeResult
)


def test_initialization():
    """Test MultiFileEditor initialization."""
    print("\n" + "="*60)
    print("TEST: Initialization")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    assert editor.project_root == Path.cwd()
    assert isinstance(editor.pending_edits, list)
    assert isinstance(editor.edit_history, list)
    assert isinstance(editor._backups, dict)
    
    print("✓ MultiFileEditor initialized successfully")
    print(f"  Project root: {editor.project_root}")
    print(f"  Pending edits: {len(editor.pending_edits)}")
    print(f"  Edit history: {len(editor.edit_history)}")


def test_change_planning():
    """Test change planning functionality."""
    print("\n" + "="*60)
    print("TEST: Change Planning")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Plan changes
    change_set = editor.plan_changes(
        intent="Test refactoring",
        files=[Path("src/codegenie/core/agent.py")]
    )
    
    assert isinstance(change_set, ChangeSet)
    assert change_set.intent == "Test refactoring"
    assert isinstance(change_set.affected_files, set)
    assert isinstance(change_set.dependencies, dict)
    assert change_set.estimated_impact in ["low", "medium", "high"]
    
    print("✓ Change planning works correctly")
    print(f"  Intent: {change_set.intent}")
    print(f"  Affected files: {len(change_set.affected_files)}")
    print(f"  Estimated impact: {change_set.estimated_impact}")


def test_file_operations():
    """Test basic file operations."""
    print("\n" + "="*60)
    print("TEST: File Operations")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test file
    test_file = Path("test_ops.py")
    test_content = "# Test file\n"
    
    # Test create_file
    edit = editor.create_file(test_file, test_content, "Create test file")
    assert isinstance(edit, FileEdit)
    assert edit.file_path == test_file
    assert edit.edit_type == EditType.CREATE_FILE
    assert edit.new_content == test_content
    
    print("✓ File operations work correctly")
    print(f"  Created edit for: {edit.file_path}")
    print(f"  Edit type: {edit.edit_type.value}")
    
    # Clean up
    if test_file.exists():
        test_file.unlink()


def test_validation():
    """Test validation functionality."""
    print("\n" + "="*60)
    print("TEST: Validation")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Test syntax validation with valid Python
    valid_code = "def test():\n    return 42\n"
    result = editor._validate_python_syntax(valid_code)
    
    assert result['valid'] == True
    assert len(result['errors']) == 0
    
    print("✓ Valid Python code passes validation")
    
    # Test syntax validation with invalid Python
    invalid_code = "def test(\n    return 42\n"
    result = editor._validate_python_syntax(invalid_code)
    
    assert result['valid'] == False
    assert len(result['errors']) > 0
    
    print("✓ Invalid Python code fails validation")
    print(f"  Errors detected: {len(result['errors'])}")


def test_import_management():
    """Test import management."""
    print("\n" + "="*60)
    print("TEST: Import Management")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Test stdlib detection
    assert editor._is_stdlib_module('os') == True
    assert editor._is_stdlib_module('sys') == True
    assert editor._is_stdlib_module('pathlib') == True
    assert editor._is_stdlib_module('numpy') == False
    assert editor._is_stdlib_module('custom_module') == False
    
    print("✓ Stdlib module detection works correctly")
    print("  ✓ os, sys, pathlib detected as stdlib")
    print("  ✓ numpy, custom_module detected as non-stdlib")


def test_symbol_refactoring():
    """Test symbol refactoring."""
    print("\n" + "="*60)
    print("TEST: Symbol Refactoring")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test files
    test_file1 = Path("test_refactor1.py")
    test_file2 = Path("test_refactor2.py")
    
    test_file1.write_text("OLD_NAME = 42\n")
    test_file2.write_text("from test_refactor1 import OLD_NAME\n")
    
    # Refactor symbol
    edits = editor.refactor_symbol(
        "OLD_NAME",
        "NEW_NAME",
        scope="project",
        files=[test_file1, test_file2]
    )
    
    assert isinstance(edits, list)
    assert len(edits) == 2
    
    for edit in edits:
        assert isinstance(edit, FileEdit)
        assert "OLD_NAME" in edit.old_content
        assert "NEW_NAME" in edit.new_content
    
    print("✓ Symbol refactoring works correctly")
    print(f"  Refactored in {len(edits)} files")
    
    # Clean up
    test_file1.unlink()
    test_file2.unlink()


def test_change_set_validation():
    """Test change set validation."""
    print("\n" + "="*60)
    print("TEST: Change Set Validation")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create a valid change set
    change_set = ChangeSet(intent="Test validation")
    
    # Add a file that exists
    test_file = Path("test_validation.py")
    test_file.write_text("# Test\n")
    
    change_set.affected_files.add(test_file)
    
    # Validate
    result = editor.validate_changes(change_set)
    
    assert isinstance(result, dict)
    assert 'valid' in result
    assert 'errors' in result
    assert 'warnings' in result
    
    print("✓ Change set validation works correctly")
    print(f"  Valid: {result['valid']}")
    print(f"  Errors: {len(result['errors'])}")
    print(f"  Warnings: {len(result['warnings'])}")
    
    # Clean up
    test_file.unlink()


def test_atomic_operations():
    """Test atomic operations."""
    print("\n" + "="*60)
    print("TEST: Atomic Operations")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test files
    test_files = []
    for i in range(3):
        test_file = Path(f"test_atomic_{i}.py")
        test_file.write_text(f"# File {i}\n")
        test_files.append(test_file)
    
    # Create backups
    editor._create_backups(set(test_files))
    
    assert len(editor._backups) == 3
    
    for test_file in test_files:
        assert test_file in editor._backups
        assert editor._backups[test_file] == f"# File {test_files.index(test_file)}\n"
    
    print("✓ Backup creation works correctly")
    print(f"  Created {len(editor._backups)} backups")
    
    # Test rollback
    # Modify files
    for i, test_file in enumerate(test_files):
        test_file.write_text(f"# Modified {i}\n")
    
    # Rollback
    editor._rollback_changes()
    
    # Verify rollback
    for i, test_file in enumerate(test_files):
        content = test_file.read_text()
        assert content == f"# File {i}\n"
    
    print("✓ Rollback works correctly")
    print(f"  Rolled back {len(test_files)} files")
    
    # Clean up
    for test_file in test_files:
        test_file.unlink()


def test_dependency_analysis():
    """Test dependency analysis."""
    print("\n" + "="*60)
    print("TEST: Dependency Analysis")
    print("="*60)
    
    editor = MultiFileEditor(Path.cwd())
    
    # Create test files with dependencies
    file1 = Path("test_dep1.py")
    file2 = Path("test_dep2.py")
    file3 = Path("test_dep3.py")
    
    file1.write_text("# Base module\n")
    file2.write_text("from test_dep1 import something\n")
    file3.write_text("from test_dep2 import other\n")
    
    # Analyze dependencies
    deps = editor._analyze_file_dependencies([file1, file2, file3])
    
    assert isinstance(deps, dict)
    assert file1 in deps
    assert file2 in deps
    assert file3 in deps
    
    print("✓ Dependency analysis works correctly")
    print(f"  Analyzed {len(deps)} files")
    
    # Test circular dependency detection
    has_circular = editor._has_circular_dependencies(deps)
    assert isinstance(has_circular, bool)
    
    print(f"  Circular dependencies: {has_circular}")
    
    # Clean up
    file1.unlink()
    file2.unlink()
    file3.unlink()


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("MULTI-FILE EDITOR TEST SUITE")
    print("="*70)
    
    tests = [
        test_initialization,
        test_change_planning,
        test_file_operations,
        test_validation,
        test_import_management,
        test_symbol_refactoring,
        test_change_set_validation,
        test_atomic_operations,
        test_dependency_analysis,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ Test error: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
