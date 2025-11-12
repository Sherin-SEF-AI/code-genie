# Error Recovery System Guide

## Overview

The Error Recovery System is an intelligent component that automatically analyzes errors, suggests fixes, and can apply fixes automatically with learning capabilities.

## Quick Start

```python
from codegenie.core.error_recovery_system import (
    ErrorRecoverySystem,
    FixPatternLearner,
    InteractiveRecoveryAssistant
)

# Create recovery system
recovery = ErrorRecoverySystem()

# Analyze an error
context = recovery.analyze_error(
    error_message="ModuleNotFoundError: No module named 'requests'",
    file_path=Path("app.py")
)

# Get fix suggestions
suggestions = recovery.generate_fix_suggestions(context)

# Apply automatic fix (if high confidence)
result = recovery.apply_automatic_fix(context)
```

## Core Features

### 1. Error Analysis

Automatically detects and categorizes errors:

```python
context = recovery.analyze_error(
    error_message="SyntaxError: invalid syntax at line 42",
    file_path=Path("script.py"),
    code_context="if x == 5\n    print('hello')"
)

print(f"Type: {context.error_type}")
print(f"Language: {context.language}")
print(f"Line: {context.line_number}")
```

**Supported Error Types:**
- Syntax errors
- Import/module errors
- Name errors (undefined variables)
- Type errors
- Attribute errors
- File not found
- Permission errors
- Command errors
- Dependency errors
- Indentation errors
- Runtime errors

### 2. Fix Suggestions

Generate multiple fix options with confidence levels:

```python
suggestions = recovery.generate_fix_suggestions(context, max_suggestions=5)

for suggestion in suggestions:
    print(f"{suggestion.description}")
    print(f"  Confidence: {suggestion.confidence.value}")
    print(f"  Type: {suggestion.fix_type}")
    if suggestion.commands:
        print(f"  Commands: {', '.join(suggestion.commands)}")
    if suggestion.explanation:
        print(f"  Explanation: {suggestion.explanation}")
```

**Confidence Levels:**
- **HIGH**: 90%+ confidence, eligible for auto-apply
- **MEDIUM**: 60-90% confidence, suggest to user
- **LOW**: <60% confidence, show as option

**Fix Types:**
- `code_change`: Modify source files
- `command`: Execute shell commands
- `install`: Install packages
- `config`: Update configuration files

### 3. Automatic Fixes

Apply fixes automatically for high-confidence suggestions:

```python
# Auto-select best fix
result = recovery.apply_automatic_fix(context)

# Or apply specific suggestion
result = recovery.apply_automatic_fix(context, suggestion)

if result.success:
    print(f"Fixed in {result.duration:.2f}s")
    print(f"Output: {result.output}")
else:
    print(f"Failed: {result.error_message}")
```

**Safety Features:**
- Backup creation before code changes
- Command timeout protection (120s)
- Approval requirements for risky operations
- Only auto-applies HIGH confidence fixes

### 4. Learning Capabilities

Learn from successful fixes to improve over time:

```python
# Create learner
learner = FixPatternLearner(recovery)

# Track fix success
learner.track_fix_success(error_context, fix_result)

# Get recommendations based on learned patterns
suggestions = recovery.generate_fix_suggestions(context)
recommended = learner.recommend_fixes(context, suggestions)

# Get insights
insights = learner.get_pattern_insights()
print(f"Learned {insights['total_error_patterns']} patterns")
print(f"Top successful patterns: {insights['top_successful_patterns']}")
```

**Learning Features:**
- Tracks success rates per error-fix pattern
- Uses exponential moving average for learning
- Stores patterns persistently to disk
- Boosts confidence based on usage count
- Identifies problematic patterns

### 5. Interactive Recovery

Guide users through error recovery:

```python
# Create assistant
assistant = InteractiveRecoveryAssistant(recovery)

# Set interaction callback
def user_input(prompt: str) -> str:
    return input(prompt)

assistant.set_interaction_callback(user_input)

# Guide user through recovery
result = assistant.guided_recovery(error_context)
```

**Interactive Features:**
- Presents fix options with explanations
- Shows confidence levels and estimated times
- Allows user selection
- Confirms before applying
- Fallback to manual mode

## Configuration

```python
config = {
    "auto_fix_enabled": True,      # Enable automatic fixes
    "max_auto_fix_attempts": 3,    # Max attempts per error
}

recovery = ErrorRecoverySystem(config)
```

## Statistics and Monitoring

### Get Fix Statistics

```python
stats = recovery.get_fix_statistics()

print(f"Total attempts: {stats['total_attempts']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average duration: {stats['average_duration']:.2f}s")
print(f"Learned patterns: {stats['learned_patterns']}")

# By fix type
for fix_type, type_stats in stats['by_fix_type'].items():
    print(f"{fix_type}: {type_stats['successful']}/{type_stats['total']}")
```

### Clear History

```python
# Clear fix history
recovery.clear_history()

# Reset learned patterns
recovery.reset_learned_patterns()
```

## Common Use Cases

### 1. Missing Package Installation

```python
# Error: ModuleNotFoundError
context = recovery.analyze_error(
    "ModuleNotFoundError: No module named 'pandas'"
)

# Generates: pip install pandas
suggestions = recovery.generate_fix_suggestions(context)
result = recovery.apply_automatic_fix(context)
```

### 2. Indentation Errors

```python
# Error: IndentationError
context = recovery.analyze_error(
    "IndentationError: unexpected indent at line 15",
    file_path=Path("script.py")
)

# Generates: black script.py or autopep8 --in-place script.py
suggestions = recovery.generate_fix_suggestions(context)
```

### 3. Undefined Variables

```python
# Error: NameError
context = recovery.analyze_error(
    "NameError: name 'requests' is not defined",
    file_path=Path("app.py")
)

# Suggests: Add import statement
suggestions = recovery.generate_fix_suggestions(context)
```

### 4. Syntax Errors

```python
# Error: SyntaxError
context = recovery.analyze_error(
    "SyntaxError: invalid syntax",
    file_path=Path("test.py"),
    code_context="if x == 5\n    print('hello')"
)

# Suggests: Add missing colon
suggestions = recovery.generate_fix_suggestions(context)
```

## Persistent Storage

### Learned Patterns
- **Location**: `~/.codegenie/learned_patterns.json`
- **Content**: Error signatures and successful fix patterns
- **Format**: JSON

### Pattern Statistics
- **Location**: `~/.codegenie/pattern_statistics.json`
- **Content**: Success rates and usage counts
- **Format**: JSON

## Best Practices

1. **Always analyze errors first** before generating suggestions
2. **Review suggestions** before applying, especially for code changes
3. **Track fix success** to improve learning
4. **Use interactive mode** for complex or unfamiliar errors
5. **Monitor statistics** to identify patterns and improvements
6. **Clear history periodically** to manage memory usage
7. **Backup important files** before applying automatic fixes

## Error Handling

The system handles errors gracefully:

```python
try:
    result = recovery.apply_automatic_fix(context)
    if not result.success:
        print(f"Fix failed: {result.error_message}")
        # Fallback to manual mode or try another suggestion
except Exception as e:
    print(f"Error during recovery: {e}")
    # Handle exception
```

## Integration with Other Components

### With CommandExecutor
```python
from codegenie.core.command_executor import CommandExecutor

executor = CommandExecutor()
# Use executor for safe command execution in fixes
```

### With FileCreator
```python
from codegenie.core.file_creator import FileCreator

creator = FileCreator()
# Use creator for file modifications in fixes
```

### With ApprovalSystem
```python
from codegenie.core.approval_system import ApprovalSystem

approval = ApprovalSystem()
# Use approval system for user confirmations
```

## Advanced Usage

### Custom Fix Suggestions

```python
from codegenie.core.error_recovery_system import FixSuggestion, FixConfidence

custom_fix = FixSuggestion(
    description="Custom fix for specific error",
    fix_type="code_change",
    confidence=FixConfidence.MEDIUM,
    code_changes={
        "app.py": "# Fixed code content"
    },
    explanation="This fix addresses the specific issue",
    estimated_time=10,
    requires_approval=True
)

result = recovery.apply_automatic_fix(context, custom_fix)
```

### Pattern Matching

```python
# Get error signature for pattern matching
signature = recovery._get_error_signature(context)

# Check if pattern is learned
if signature in recovery.learned_patterns:
    learned_fixes = recovery.learned_patterns[signature]
    print(f"Found {len(learned_fixes)} learned fixes")
```

## Troubleshooting

### Fix Not Applied
- Check if auto_fix_enabled is True
- Verify fix confidence is HIGH for auto-apply
- Check error logs for detailed information

### Command Timeout
- Default timeout is 120 seconds
- Long-running commands may timeout
- Consider running manually for very long operations

### Pattern Not Learning
- Ensure fixes are being tracked with track_fix_success()
- Check if pattern statistics file is writable
- Verify at least 3 successful fixes for pattern recognition

## API Reference

### ErrorRecoverySystem

**Methods:**
- `analyze_error(error_message, file_path, code_context, **kwargs)` → ErrorContext
- `generate_fix_suggestions(error_context, max_suggestions)` → List[FixSuggestion]
- `apply_automatic_fix(error_context, suggestion)` → FixResult
- `get_fix_statistics()` → Dict[str, Any]
- `clear_history()` → None
- `reset_learned_patterns()` → None

### FixPatternLearner

**Methods:**
- `track_fix_success(error_context, fix_result)` → None
- `recommend_fixes(error_context, candidate_fixes)` → List[FixSuggestion]
- `get_pattern_insights()` → Dict[str, Any]

### InteractiveRecoveryAssistant

**Methods:**
- `set_interaction_callback(callback)` → None
- `guided_recovery(error_context, suggestions)` → FixResult

## Examples

See the following files for complete examples:
- `demo_error_recovery_system.py` - Comprehensive demonstration
- `test_error_recovery_system_simple.py` - Unit tests and examples

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the examples
3. Check the API reference
4. Consult the main documentation

## Version History

- **v1.0.0** - Initial implementation
  - Error analysis and type detection
  - Fix suggestion generation
  - Automatic fix application
  - Learning capabilities
  - Interactive recovery
  - Statistics and monitoring
