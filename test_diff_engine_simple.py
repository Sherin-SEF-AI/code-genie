#!/usr/bin/env python3
"""
Simple test for DiffEngine without external dependencies.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.diff_engine import (
    DiffEngine,
    DiffFormat,
    ChangeType,
)


def test_unified_diff():
    """Test unified diff generation."""
    print("Test 1: Unified Diff Generation")
    print("-" * 40)
    
    engine = DiffEngine(colored_output=False)
    
    original = """def hello():
    print("Hello")
    return True
"""
    
    modified = """def hello(name="World"):
    print(f"Hello, {name}")
    return True
"""
    
    diff = engine.generate_diff(original, modified, "test.py")
    
    assert diff.additions > 0, "Should have additions"
    assert diff.deletions > 0, "Should have deletions"
    assert len(diff.hunks) > 0, "Should have hunks"
    
    unified = engine.show_unified_diff(diff)
    assert "def hello" in unified, "Should contain function name"
    assert "+" in unified, "Should have addition markers"
    assert "-" in unified, "Should have deletion markers"
    
    print(f"✓ Additions: {diff.additions}")
    print(f"✓ Deletions: {diff.deletions}")
    print(f"✓ Hunks: {len(diff.hunks)}")
    print()


def test_side_by_side_diff():
    """Test side-by-side diff."""
    print("Test 2: Side-by-Side Diff")
    print("-" * 40)
    
    engine = DiffEngine(colored_output=False)
    
    original = "line 1\nline 2\nline 3\n"
    modified = "line 1\nline 2 modified\nline 3\nline 4\n"
    
    diff = engine.generate_diff(original, modified, "test.txt")
    side_by_side = engine.show_side_by_side_diff(diff, width=80)
    
    assert "Original" in side_by_side, "Should have Original header"
    assert "Modified" in side_by_side, "Should have Modified header"
    assert "|" in side_by_side, "Should have separator"
    
    print("✓ Side-by-side diff generated")
    print(f"✓ Output length: {len(side_by_side)} chars")
    print()


def test_patch_application():
    """Test patch application."""
    print("Test 3: Patch Application")
    print("-" * 40)
    
    engine = DiffEngine()
    
    # Create test file
    test_file = Path("test_patch_temp.txt")
    original = "line 1\nline 2\nline 3\n"
    modified = "line 1\nline 2 modified\nline 3\n"
    
    test_file.write_text(original)
    
    # Generate and apply diff
    diff = engine.generate_diff(original, modified, str(test_file))
    
    # Dry run
    result = engine.apply_diff(test_file, diff, dry_run=True)
    assert result['success'], "Dry run should succeed"
    assert result['dry_run'], "Should be marked as dry run"
    
    # Real application
    result = engine.apply_diff(test_file, diff, dry_run=False)
    assert result['success'], "Application should succeed"
    
    # Verify content
    new_content = test_file.read_text()
    assert "modified" in new_content, "Should contain modified text"
    
    # Cleanup
    test_file.unlink()
    
    print("✓ Dry run successful")
    print("✓ Patch applied successfully")
    print("✓ Content verified")
    print()


def test_change_validation():
    """Test change validation."""
    print("Test 4: Change Validation")
    print("-" * 40)
    
    engine = DiffEngine()
    
    # Valid Python
    original = "def test():\n    pass\n"
    modified_valid = "def test():\n    return True\n"
    modified_invalid = "def test(\n    return True\n"
    
    result_valid = engine.validate_changes(original, modified_valid, 'python')
    assert result_valid['valid'], "Valid Python should pass"
    
    result_invalid = engine.validate_changes(original, modified_invalid, 'python')
    assert not result_invalid['valid'], "Invalid Python should fail"
    assert len(result_invalid['errors']) > 0, "Should have errors"
    
    print("✓ Valid Python detected correctly")
    print("✓ Invalid Python detected correctly")
    print()


def test_multi_file_diff():
    """Test multi-file diff."""
    print("Test 5: Multi-File Diff")
    print("-" * 40)
    
    engine = DiffEngine()
    
    file_changes = {
        Path("file1.py"): ("old1\n", "new1\n"),
        Path("file2.py"): ("old2\n", "new2\n"),
        Path("file3.py"): ("", "new3\n"),  # Added file
    }
    
    file_diffs = engine.generate_batch_diff(file_changes)
    
    assert len(file_diffs) == 3, "Should have 3 file diffs"
    
    # Check file statuses
    statuses = [fd.file_status for fd in file_diffs]
    assert 'modified' in statuses, "Should have modified files"
    assert 'added' in statuses, "Should have added file"
    
    # Test summary
    summary = engine.show_diff_summary(file_diffs)
    assert "3 files changed" in summary, "Should show file count"
    
    # Test navigation
    navigation = engine.navigate_file_diffs(file_diffs)
    assert "File 1/3" in navigation, "Should have navigation markers"
    
    print("✓ Batch diff generated")
    print("✓ File statuses correct")
    print("✓ Summary generated")
    print("✓ Navigation generated")
    print()


def test_selective_changes():
    """Test selective change application."""
    print("Test 6: Selective Changes")
    print("-" * 40)
    
    engine = DiffEngine()
    
    original = """line 1
line 2
line 3
line 4
"""
    
    modified = """line 1 modified
line 2
line 3 modified
line 4
"""
    
    diff = engine.generate_diff(original, modified, "test.txt")
    
    # Should have multiple hunks
    assert len(diff.hunks) >= 1, "Should have hunks"
    
    # Create test file
    test_file = Path("test_selective_temp.txt")
    test_file.write_text(original)
    
    # Apply only first hunk
    result = engine.apply_selective_changes(test_file, diff, [0], dry_run=False)
    assert result['success'], "Selective application should succeed"
    
    # Cleanup
    test_file.unlink()
    
    print("✓ Selective changes applied")
    print()


def test_patch_creation():
    """Test patch creation."""
    print("Test 7: Patch Creation")
    print("-" * 40)
    
    engine = DiffEngine()
    
    file_changes = {
        Path("file1.txt"): ("old1\n", "new1\n"),
        Path("file2.txt"): ("old2\n", "new2\n"),
    }
    
    file_diffs = engine.generate_batch_diff(file_changes)
    patch = engine.create_patch(file_diffs, "Test patch")
    
    assert patch.description == "Test patch", "Should have description"
    assert len(patch.file_diffs) == 2, "Should have 2 file diffs"
    
    # Test serialization
    patch_dict = patch.to_dict()
    assert 'description' in patch_dict, "Should serialize description"
    assert 'file_diffs' in patch_dict, "Should serialize file diffs"
    
    print("✓ Patch created")
    print("✓ Patch serialized")
    print()


def main():
    """Run all tests."""
    print()
    print("=" * 50)
    print("DiffEngine Simple Tests")
    print("=" * 50)
    print()
    
    tests = [
        test_unified_diff,
        test_side_by_side_diff,
        test_patch_application,
        test_change_validation,
        test_multi_file_diff,
        test_selective_changes,
        test_patch_creation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
