#!/usr/bin/env python3
"""
Simple test for IDE Integration features
Tests the core functionality without external dependencies
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.integrations.ide_features import (
    InlineDiffProvider,
    QuickActionProvider,
    CodeLensProvider,
    IDEFeatureManager,
    QuickActionType,
    Range
)


def test_inline_diff_provider():
    """Test inline diff provider"""
    print("Testing InlineDiffProvider...")
    
    provider = InlineDiffProvider()
    test_file = Path("test.py")
    
    # Create a diff
    diff = provider.create_diff(
        file_path=test_file,
        start_line=5,
        start_column=0,
        end_line=5,
        end_column=20,
        original_text="def old_function():",
        modified_text="def new_function():",
        description="Rename function"
    )
    
    assert diff.file_path == test_file
    assert diff.original_text == "def old_function():"
    assert diff.modified_text == "def new_function():"
    
    # Get diffs for file
    diffs = provider.get_diffs_for_file(test_file)
    assert len(diffs) == 1
    
    # Apply diff
    content = "line1\nline2\nline3\nline4\nline5\ndef old_function():\n    pass\n"
    diff_id = f"{test_file}:5:0"
    result = provider.apply_diff(diff_id, content)
    assert "def new_function():" in result
    
    print("  ✓ Inline diff provider works correctly")


def test_quick_action_provider():
    """Test quick action provider"""
    print("Testing QuickActionProvider...")
    
    provider = QuickActionProvider()
    test_file = Path("test.py")
    
    # Create a fix error action
    action = provider.create_fix_error_action(
        file_path=test_file,
        line=10,
        column=0,
        error_message="Missing import",
        fix_text="from typing import List"
    )
    
    assert action.action_type == QuickActionType.FIX_ERROR
    assert "Fix:" in action.title
    assert action.is_preferred
    
    # Create a refactor action
    refactor_action = provider.create_refactor_action(
        file_path=test_file,
        start_line=15,
        start_column=0,
        end_line=20,
        end_column=0,
        refactor_type="extract_method",
        title="Extract method"
    )
    
    assert refactor_action.action_type == QuickActionType.REFACTOR
    
    # Get actions for range
    actions = provider.get_actions_for_range(
        file_path=test_file,
        start_line=10,
        start_column=0,
        end_line=25,
        end_column=0
    )
    
    assert len(actions) == 2
    
    print("  ✓ Quick action provider works correctly")


def test_code_lens_provider():
    """Test code lens provider"""
    print("Testing CodeLensProvider...")
    
    provider = CodeLensProvider()
    test_file = Path("test.py")
    
    # Add run test lens
    lens = provider.add_run_test_lens(
        file_path=test_file,
        line=10,
        test_name="test_example"
    )
    
    assert lens.command == "codegenie.runTest"
    assert "Run" in lens.title
    
    # Add references lens
    ref_lens = provider.add_references_lens(
        file_path=test_file,
        line=20,
        symbol="MyClass",
        reference_count=5
    )
    
    assert "5 references" in ref_lens.title
    
    # Add complexity lens
    complexity_lens = provider.add_complexity_lens(
        file_path=test_file,
        line=30,
        function_name="complex_function",
        complexity=12
    )
    
    assert "Complexity" in complexity_lens.title
    assert "High" in complexity_lens.title
    
    # Get lenses for file
    lenses = provider.get_lenses_for_file(test_file)
    assert len(lenses) == 3
    
    # Clear lenses
    provider.clear_lenses_for_file(test_file)
    lenses = provider.get_lenses_for_file(test_file)
    assert len(lenses) == 0
    
    print("  ✓ Code lens provider works correctly")


async def test_feature_manager():
    """Test IDE feature manager"""
    print("Testing IDEFeatureManager...")
    
    manager = IDEFeatureManager()
    test_file = Path("test_example.py")
    
    # Test code with test functions
    test_code = """
def test_example():
    assert True

def test_another():
    assert False
"""
    
    # Analyze and suggest
    suggestions = await manager.suggest_improvements(
        file_path=test_file,
        content=test_code,
        language="python"
    )
    
    assert 'diffs' in suggestions
    assert 'actions' in suggestions
    assert 'lenses' in suggestions
    
    # Should have detected test functions and added lenses
    lenses = manager.lens_provider.get_lenses_for_file(test_file)
    assert len(lenses) == 2  # Two test functions
    
    # Clear all features
    manager.clear_all_features_for_file(test_file)
    lenses = manager.lens_provider.get_lenses_for_file(test_file)
    assert len(lenses) == 0
    
    print("  ✓ Feature manager works correctly")


def test_range():
    """Test Range class"""
    print("Testing Range...")
    
    range_obj = Range(
        start_line=10,
        start_column=5,
        end_line=15,
        end_column=20
    )
    
    range_dict = range_obj.to_dict()
    assert range_dict['start']['line'] == 10
    assert range_dict['start']['character'] == 5
    assert range_dict['end']['line'] == 15
    assert range_dict['end']['character'] == 20
    
    print("  ✓ Range class works correctly")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("IDE Integration Features - Simple Tests")
    print("=" * 60)
    print()
    
    try:
        test_range()
        test_inline_diff_provider()
        test_quick_action_provider()
        test_code_lens_provider()
        await test_feature_manager()
        
        print()
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
