#!/usr/bin/env python3
"""
Simple standalone test for Error Recovery System.
Tests core functionality without external dependencies.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import only the error recovery system
from codegenie.core.error_recovery_system import (
    ErrorRecoverySystem,
    ErrorContext,
    ErrorType,
    FixSuggestion,
    FixConfidence,
    FixPatternLearner,
    InteractiveRecoveryAssistant,
    FixResult,
)


def test_error_analysis():
    """Test error analysis capabilities."""
    print("Test 1: Error Analysis")
    print("-" * 60)
    
    recovery_system = ErrorRecoverySystem()
    
    # Test import error
    context = recovery_system.analyze_error(
        error_message="ModuleNotFoundError: No module named 'requests'",
        file_path=Path("test.py")
    )
    
    assert context.error_type == ErrorType.IMPORT_ERROR
    assert context.language == "python"
    print("✓ Import error detected correctly")
    
    # Test syntax error
    context = recovery_system.analyze_error(
        error_message="SyntaxError: invalid syntax at line 42",
        file_path=Path("app.py")
    )
    
    assert context.error_type == ErrorType.SYNTAX_ERROR
    assert context.line_number == 42
    print("✓ Syntax error detected correctly")
    
    # Test name error
    context = recovery_system.analyze_error(
        error_message="NameError: name 'undefined_var' is not defined",
        file_path=Path("main.py")
    )
    
    assert context.error_type == ErrorType.NAME_ERROR
    print("✓ Name error detected correctly")
    
    print("✓ All error analysis tests passed\n")


def test_fix_suggestions():
    """Test fix suggestion generation."""
    print("Test 2: Fix Suggestion Generation")
    print("-" * 60)
    
    recovery_system = ErrorRecoverySystem()
    
    # Test import error suggestions
    error_context = recovery_system.analyze_error(
        error_message="ModuleNotFoundError: No module named 'pandas'",
        file_path=Path("data_analysis.py")
    )
    
    suggestions = recovery_system.generate_fix_suggestions(error_context)
    
    assert len(suggestions) > 0
    assert any(s.fix_type == "install" for s in suggestions)
    print(f"✓ Generated {len(suggestions)} suggestions for import error")
    
    # Test indentation error suggestions
    error_context = recovery_system.analyze_error(
        error_message="IndentationError: unexpected indent at line 15",
        file_path=Path("script.py")
    )
    
    suggestions = recovery_system.generate_fix_suggestions(error_context)
    
    assert len(suggestions) > 0
    print(f"✓ Generated {len(suggestions)} suggestions for indentation error")
    
    print("✓ All fix suggestion tests passed\n")


def test_learning_capabilities():
    """Test learning from successful fixes."""
    print("Test 3: Learning Capabilities")
    print("-" * 60)
    
    recovery_system = ErrorRecoverySystem()
    learner = FixPatternLearner(recovery_system)
    
    # Create error context
    error_context = ErrorContext(
        error_type=ErrorType.IMPORT_ERROR,
        message="ModuleNotFoundError: No module named 'requests'",
        language="python"
    )
    
    # Create fix suggestion
    suggestion = FixSuggestion(
        description="Install requests package",
        fix_type="install",
        confidence=FixConfidence.HIGH,
        commands=["pip install requests"]
    )
    
    # Track successful fixes
    for i in range(5):
        result = FixResult(
            success=True,
            suggestion=suggestion,
            output="Package installed successfully"
        )
        learner.track_fix_success(error_context, result)
    
    print("✓ Tracked 5 successful fixes")
    
    # Get insights
    insights = learner.get_pattern_insights()
    assert insights['total_error_patterns'] > 0
    print(f"✓ Learned {insights['total_error_patterns']} error patterns")
    
    print("✓ All learning capability tests passed\n")


def test_statistics():
    """Test statistics tracking."""
    print("Test 4: Statistics Tracking")
    print("-" * 60)
    
    recovery_system = ErrorRecoverySystem()
    
    # Add some fix history
    for i in range(10):
        suggestion = FixSuggestion(
            description=f"Fix {i}",
            fix_type="install" if i % 2 == 0 else "code_change",
            confidence=FixConfidence.HIGH
        )
        result = FixResult(
            success=i % 3 != 0,
            suggestion=suggestion,
            duration=float(i * 2)
        )
        recovery_system.fix_history.append(result)
    
    stats = recovery_system.get_fix_statistics()
    
    assert stats['total_attempts'] == 10
    assert stats['successful_fixes'] > 0
    assert 0 <= stats['success_rate'] <= 1.0
    print(f"✓ Statistics: {stats['successful_fixes']}/10 successful ({stats['success_rate']:.1%})")
    
    assert 'by_fix_type' in stats
    print(f"✓ Tracked statistics by fix type")
    
    print("✓ All statistics tests passed\n")


def test_interactive_assistant():
    """Test interactive recovery assistant."""
    print("Test 5: Interactive Recovery Assistant")
    print("-" * 60)
    
    recovery_system = ErrorRecoverySystem()
    assistant = InteractiveRecoveryAssistant(recovery_system)
    
    # Test callback setting
    def mock_callback(prompt: str) -> str:
        return "1"
    
    assistant.set_interaction_callback(mock_callback)
    assert assistant.interaction_callback is not None
    print("✓ Interaction callback set successfully")
    
    # Test format fix options
    suggestions = [
        FixSuggestion(
            description="Test fix 1",
            fix_type="install",
            confidence=FixConfidence.HIGH,
            explanation="Test explanation"
        ),
        FixSuggestion(
            description="Test fix 2",
            fix_type="code_change",
            confidence=FixConfidence.MEDIUM
        )
    ]
    
    formatted = assistant._format_fix_options(suggestions)
    assert "Test fix 1" in formatted
    assert "Test fix 2" in formatted
    print("✓ Fix options formatted correctly")
    
    print("✓ All interactive assistant tests passed\n")


def test_error_type_detection():
    """Test comprehensive error type detection."""
    print("Test 6: Error Type Detection")
    print("-" * 60)
    
    recovery_system = ErrorRecoverySystem()
    
    test_cases = [
        ("SyntaxError: invalid syntax", ErrorType.SYNTAX_ERROR),
        ("ImportError: cannot import name", ErrorType.IMPORT_ERROR),
        ("NameError: name 'x' is not defined", ErrorType.NAME_ERROR),
        ("TypeError: unsupported operand type", ErrorType.TYPE_ERROR),
        ("AttributeError: object has no attribute", ErrorType.ATTRIBUTE_ERROR),
        ("FileNotFoundError: No such file", ErrorType.FILE_NOT_FOUND),
        ("PermissionError: Permission denied", ErrorType.PERMISSION_ERROR),
        ("IndentationError: unexpected indent", ErrorType.INDENTATION_ERROR),
    ]
    
    for message, expected_type in test_cases:
        detected_type = recovery_system._detect_error_type(message)
        assert detected_type == expected_type, f"Failed for: {message}"
        print(f"✓ Detected {expected_type.value} correctly")
    
    print("✓ All error type detection tests passed\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ERROR RECOVERY SYSTEM - SIMPLE TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_error_analysis()
        test_fix_suggestions()
        test_learning_capabilities()
        test_statistics()
        test_interactive_assistant()
        test_error_type_detection()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nError Recovery System is working correctly!")
        print("\nKey Features Verified:")
        print("  ✓ Error analysis and type detection")
        print("  ✓ Fix suggestion generation")
        print("  ✓ Learning from successful fixes")
        print("  ✓ Statistics tracking")
        print("  ✓ Interactive recovery assistance")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
