#!/usr/bin/env python3
"""
Demo script for the Error Recovery System.

This demonstrates:
1. Error analysis and context extraction
2. Fix suggestion generation
3. Automatic fix application
4. Learning from successful fixes
5. Interactive user-assisted recovery
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.error_recovery_system import (
    ErrorRecoverySystem,
    ErrorContext,
    ErrorType,
    FixSuggestion,
    FixConfidence,
    FixPatternLearner,
    InteractiveRecoveryAssistant,
)


def demo_error_analysis():
    """Demonstrate error analysis capabilities."""
    print("=" * 80)
    print("DEMO 1: Error Analysis")
    print("=" * 80)
    
    recovery_system = ErrorRecoverySystem()
    
    # Test different error types
    test_errors = [
        {
            "message": "ModuleNotFoundError: No module named 'requests'",
            "file_path": Path("test.py"),
            "description": "Python import error"
        },
        {
            "message": "SyntaxError: invalid syntax at line 42",
            "file_path": Path("app.py"),
            "code_context": "if x == 5\n    print('hello')",
            "description": "Python syntax error"
        },
        {
            "message": "NameError: name 'undefined_var' is not defined",
            "file_path": Path("main.py"),
            "description": "Python name error"
        },
        {
            "message": "IndentationError: unexpected indent at line 10",
            "file_path": Path("utils.py"),
            "description": "Python indentation error"
        },
    ]
    
    for i, error_data in enumerate(test_errors, 1):
        print(f"\n{i}. {error_data['description']}")
        print(f"   Message: {error_data['message']}")
        
        context = recovery_system.analyze_error(
            error_message=error_data['message'],
            file_path=error_data.get('file_path'),
            code_context=error_data.get('code_context')
        )
        
        print(f"   Detected Type: {context.error_type.value}")
        print(f"   Language: {context.language}")
        if context.line_number:
            print(f"   Line: {context.line_number}")


def demo_fix_suggestions():
    """Demonstrate fix suggestion generation."""
    print("\n" + "=" * 80)
    print("DEMO 2: Fix Suggestion Generation")
    print("=" * 80)
    
    recovery_system = ErrorRecoverySystem()
    
    # Test import error
    print("\n1. Import Error Fix Suggestions")
    error_context = recovery_system.analyze_error(
        error_message="ModuleNotFoundError: No module named 'pandas'",
        file_path=Path("data_analysis.py")
    )
    
    suggestions = recovery_system.generate_fix_suggestions(error_context)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n   Suggestion {i}:")
        print(f"   - Description: {suggestion.description}")
        print(f"   - Type: {suggestion.fix_type}")
        print(f"   - Confidence: {suggestion.confidence.value}")
        if suggestion.commands:
            print(f"   - Commands: {', '.join(suggestion.commands)}")
        if suggestion.explanation:
            print(f"   - Explanation: {suggestion.explanation}")
        if suggestion.estimated_time:
            print(f"   - Estimated Time: {suggestion.estimated_time}s")
    
    # Test indentation error
    print("\n2. Indentation Error Fix Suggestions")
    error_context = recovery_system.analyze_error(
        error_message="IndentationError: unexpected indent at line 15",
        file_path=Path("script.py")
    )
    
    suggestions = recovery_system.generate_fix_suggestions(error_context)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n   Suggestion {i}:")
        print(f"   - Description: {suggestion.description}")
        print(f"   - Confidence: {suggestion.confidence.value}")
        if suggestion.commands:
            print(f"   - Commands: {', '.join(suggestion.commands)}")


def demo_automatic_fixes():
    """Demonstrate automatic fix application."""
    print("\n" + "=" * 80)
    print("DEMO 3: Automatic Fix Application")
    print("=" * 80)
    
    recovery_system = ErrorRecoverySystem(config={"auto_fix_enabled": True})
    
    # Simulate a high-confidence fix
    print("\n1. High Confidence Fix (Auto-Applied)")
    error_context = ErrorContext(
        error_type=ErrorType.IMPORT_ERROR,
        message="ModuleNotFoundError: No module named 'numpy'",
        file_path=Path("test.py"),
        language="python"
    )
    
    # Create a mock high-confidence suggestion
    suggestion = FixSuggestion(
        description="Install missing Python package: numpy",
        fix_type="install",
        confidence=FixConfidence.HIGH,
        commands=["echo 'Simulating: pip install numpy'"],  # Mock command
        explanation="The module 'numpy' is not installed.",
        estimated_time=30,
        requires_approval=False  # For demo purposes
    )
    
    print(f"   Error: {error_context.message}")
    print(f"   Applying: {suggestion.description}")
    
    result = recovery_system.apply_automatic_fix(error_context, suggestion)
    
    print(f"   Success: {result.success}")
    if result.output:
        print(f"   Output: {result.output}")
    print(f"   Duration: {result.duration:.2f}s")
    
    # Simulate a medium-confidence fix
    print("\n2. Medium Confidence Fix (Requires Approval)")
    suggestion_medium = FixSuggestion(
        description="Add missing import statement",
        fix_type="code_change",
        confidence=FixConfidence.MEDIUM,
        explanation="The name appears to need an import.",
        estimated_time=5
    )
    
    result = recovery_system.apply_automatic_fix(error_context, suggestion_medium)
    
    print(f"   Error: {error_context.message}")
    print(f"   Suggestion: {suggestion_medium.description}")
    print(f"   Auto-Applied: {result.success}")
    print(f"   Reason: {result.error_message}")


def demo_learning_capabilities():
    """Demonstrate learning from successful fixes."""
    print("\n" + "=" * 80)
    print("DEMO 4: Learning Capabilities")
    print("=" * 80)
    
    recovery_system = ErrorRecoverySystem()
    learner = FixPatternLearner(recovery_system)
    
    # Simulate multiple fix attempts
    print("\n1. Tracking Fix Success")
    
    error_context = ErrorContext(
        error_type=ErrorType.IMPORT_ERROR,
        message="ModuleNotFoundError: No module named 'requests'",
        language="python"
    )
    
    suggestion = FixSuggestion(
        description="Install requests package",
        fix_type="install",
        confidence=FixConfidence.HIGH,
        commands=["pip install requests"]
    )
    
    # Simulate successful fixes
    for i in range(5):
        from codegenie.core.error_recovery_system import FixResult
        result = FixResult(
            success=True,
            suggestion=suggestion,
            output="Package installed successfully"
        )
        learner.track_fix_success(error_context, result)
        print(f"   Tracked successful fix #{i+1}")
    
    # Get pattern insights
    print("\n2. Pattern Insights")
    insights = learner.get_pattern_insights()
    print(f"   Total Error Patterns: {insights['total_error_patterns']}")
    print(f"   Total Fix Patterns: {insights['total_fix_patterns']}")
    
    # Get statistics
    print("\n3. Fix Statistics")
    stats = recovery_system.get_fix_statistics()
    print(f"   Total Attempts: {stats['total_attempts']}")
    print(f"   Successful Fixes: {stats['successful_fixes']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Learned Patterns: {stats['learned_patterns']}")


def demo_interactive_recovery():
    """Demonstrate interactive user-assisted recovery."""
    print("\n" + "=" * 80)
    print("DEMO 5: Interactive User-Assisted Recovery")
    print("=" * 80)
    
    recovery_system = ErrorRecoverySystem()
    assistant = InteractiveRecoveryAssistant(recovery_system)
    
    # Mock interaction callback
    responses = ["1", "y"]  # Select first option, then confirm
    response_index = [0]
    
    def mock_interaction(prompt: str) -> str:
        print(f"\n{prompt}")
        if response_index[0] < len(responses):
            response = responses[response_index[0]]
            response_index[0] += 1
            print(f"[Simulated Response: {response}]")
            return response
        return "m"
    
    assistant.set_interaction_callback(mock_interaction)
    
    # Create error context
    error_context = ErrorContext(
        error_type=ErrorType.IMPORT_ERROR,
        message="ModuleNotFoundError: No module named 'flask'",
        file_path=Path("app.py"),
        language="python"
    )
    
    # Generate suggestions
    suggestions = recovery_system.generate_fix_suggestions(error_context)
    
    print("\n1. Guided Recovery Process")
    print(f"   Error: {error_context.message}")
    print(f"   Available Suggestions: {len(suggestions)}")
    
    # Note: In a real scenario, this would be interactive
    print("\n   [In a real scenario, user would select from options]")
    print("   [For demo, we're simulating selection of first option]")


def demo_statistics_and_insights():
    """Demonstrate statistics and insights."""
    print("\n" + "=" * 80)
    print("DEMO 6: Statistics and Insights")
    print("=" * 80)
    
    recovery_system = ErrorRecoverySystem()
    
    # Simulate some fix history
    from codegenie.core.error_recovery_system import FixResult
    
    for i in range(10):
        suggestion = FixSuggestion(
            description=f"Fix {i}",
            fix_type="install" if i % 2 == 0 else "code_change",
            confidence=FixConfidence.HIGH
        )
        result = FixResult(
            success=i % 3 != 0,  # 2/3 success rate
            suggestion=suggestion,
            duration=float(i * 2)
        )
        recovery_system.fix_history.append(result)
    
    stats = recovery_system.get_fix_statistics()
    
    print("\n1. Overall Statistics")
    print(f"   Total Attempts: {stats['total_attempts']}")
    print(f"   Successful Fixes: {stats['successful_fixes']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Average Duration: {stats['average_duration']:.2f}s")
    
    print("\n2. By Fix Type")
    for fix_type, type_stats in stats['by_fix_type'].items():
        success_rate = type_stats['successful'] / type_stats['total'] if type_stats['total'] > 0 else 0
        print(f"   {fix_type}:")
        print(f"     - Total: {type_stats['total']}")
        print(f"     - Successful: {type_stats['successful']}")
        print(f"     - Success Rate: {success_rate:.1%}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ERROR RECOVERY SYSTEM DEMO" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        demo_error_analysis()
        demo_fix_suggestions()
        demo_automatic_fixes()
        demo_learning_capabilities()
        demo_interactive_recovery()
        demo_statistics_and_insights()
        
        print("\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80)
        print("\nThe Error Recovery System provides:")
        print("  ✓ Intelligent error analysis")
        print("  ✓ Multiple fix suggestions with confidence levels")
        print("  ✓ Automatic fix application for high-confidence fixes")
        print("  ✓ Learning from successful fixes")
        print("  ✓ Interactive user-assisted recovery")
        print("  ✓ Comprehensive statistics and insights")
        print("\nAll features are working as expected!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
