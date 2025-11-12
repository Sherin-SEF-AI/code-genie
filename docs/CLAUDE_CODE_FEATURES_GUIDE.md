# Claude Code Features User Guide

## Introduction

CodeGenie now includes comprehensive Claude Code-like features that provide seamless, context-aware coding assistance. This guide shows you how to use these powerful features.

## Quick Start

```python
from codegenie.core.claude_code_features import ClaudeCodeFeatures
from pathlib import Path

# Initialize with your project
features = ClaudeCodeFeatures(Path("/path/to/your/project"))

# Start coding with AI assistance!
```

## Features Overview

### 1. Context-Aware Understanding

CodeGenie understands your entire codebase and maintains context across conversations.

**Add files to context:**
```python
# Add a single file
features.add_file_to_context(Path("src/main.py"))

# Add multiple files
for file in Path("src").glob("**/*.py"):
    features.add_file_to_context(file)
```

**Get context summary:**
```python
summary = features.get_context_summary()
print(f"Files: {len(summary['current_files'])}")
print(f"Symbols: {summary['total_symbols_indexed']}")
```

**Process context-aware requests:**
```python
result = await features.process_request(
    "Explain how the authentication system works"
)
print(result['intent'])  # 'code_explanation'
print(result['action'])  # 'explain_code'
```

### 2. Multi-File Editing

Make coordinated changes across multiple files.

**Create a new file:**
```python
from codegenie.core.multi_file_editor import EditType

edit = features.multi_file_editor.create_file(
    Path("src/new_module.py"),
    '''"""New module for data processing"""

def process_data(data):
    """Process the input data"""
    return data.strip().lower()
''',
    "Create data processing module"
)

result = await features.apply_multi_file_edit(
    "Add new module",
    [edit],
    preview=False
)
```

**Modify existing file:**
```python
# Replace specific lines
edit = features.multi_file_editor.replace_lines(
    Path("src/main.py"),
    line_start=10,
    line_end=15,
    new_content='''    # Updated implementation
    result = process_data(input_data)
    return result
''',
    "Update main function"
)

# Preview before applying
result = await features.apply_multi_file_edit(
    "Update main function",
    [edit],
    preview=True  # Shows diff
)

print(result['preview'])  # See the changes

# Apply if satisfied
result = await features.apply_multi_file_edit(
    "Update main function",
    [edit],
    preview=False  # Actually apply
)
```

**Search and replace:**
```python
edit = features.multi_file_editor.replace_content(
    Path("src/config.py"),
    old_text='DEBUG = True',
    new_text='DEBUG = False',
    "Disable debug mode"
)
```

**Multi-file refactoring:**
```python
# Rename a function across all files
edits = []
for file in Path("src").glob("**/*.py"):
    if file.exists():
        with open(file) as f:
            content = f.read()
        if 'old_function_name' in content:
            edit = features.multi_file_editor.replace_content(
                file,
                'old_function_name',
                'new_function_name',
                f"Rename function in {file.name}"
            )
            edits.append(edit)

result = await features.apply_multi_file_edit(
    "Rename function across codebase",
    edits,
    preview=True
)
```

### 3. Intelligent Code Completions

Get smart code suggestions as you type.

**Get completions at cursor:**
```python
completions = await features.get_completions(
    file_path=Path("src/main.py"),
    line=25,
    column=10
)

for completion in completions:
    print(f"{completion.completion_type.value}: {completion.text}")
    print(f"  Confidence: {completion.confidence:.0%}")
    print(f"  Description: {completion.description}")
```

**Suggest next line:**
```python
next_line = await features.suggest_next_line(
    file_path=Path("src/main.py")
)

if next_line:
    print(f"Suggested: {next_line}")
```

**Get refactoring suggestions:**
```python
result = await features.process_request(
    "Review src/main.py for improvements"
)

for suggestion in result.get('suggestions', []):
    print(f"{suggestion['type']}: {suggestion['message']}")
    print(f"  Line {suggestion['line']}: {suggestion['suggestion']}")
```

### 4. Symbol Operations

Find and refactor symbols across your codebase.

**Find all references:**
```python
references = await features.find_references("UserModel")

for ref in references:
    print(f"{ref['file']}:{ref['line']} - {ref['type']}")
```

**Refactor symbol:**
```python
result = await features.refactor_symbol(
    old_name="process_user",
    new_name="process_user_data"
)

# Preview changes
print(result['preview'])

# Check affected files
print(f"Files affected: {result['summary']['files_affected']}")
```

**Explain code:**
```python
explanation = await features.explain_code(
    file_path=Path("src/auth.py"),
    line_start=10,
    line_end=25
)

print(explanation)
```

### 5. IDE Integration

Connect CodeGenie to your IDE for real-time assistance.

**Enable VS Code integration:**
```python
features.enable_ide_integration("vscode")

# Now CodeGenie will:
# - Track file opens/closes
# - Provide real-time completions
# - Show hover information
# - Apply edits directly in IDE
```

**Enable IntelliJ integration:**
```python
features.enable_ide_integration("intellij")
```

**Check IDE status:**
```python
stats = features.get_statistics()
print(f"IDE Connected: {stats['ide_connected']}")
```

## Common Use Cases

### Use Case 1: Add Feature Across Multiple Files

```python
# 1. Understand the request
result = await features.process_request(
    "Add logging to all API endpoints"
)

# 2. Get relevant files
features.add_file_to_context(Path("src/api"))

# 3. Create edits
edits = []
for file in Path("src/api").glob("*.py"):
    # Add import
    import_edit = features.multi_file_editor.insert_lines(
        file, 1,
        "import logging\n",
        "Add logging import"
    )
    edits.append(import_edit)
    
    # Add logging calls (simplified)
    # ... create more edits ...

# 4. Preview and apply
result = await features.apply_multi_file_edit(
    "Add logging to API endpoints",
    edits,
    preview=True
)
```

### Use Case 2: Refactor Code

```python
# 1. Find all usages
references = await features.find_references("old_function")

# 2. Create refactoring plan
result = await features.refactor_symbol(
    "old_function",
    "new_improved_function"
)

# 3. Review changes
print(result['preview'])

# 4. Apply if satisfied
if input("Apply changes? (y/n): ") == 'y':
    result = await features.apply_multi_file_edit(
        "Refactor function name",
        result['edits'],
        preview=False
    )
```

### Use Case 3: Code Review

```python
# 1. Add files to review
for file in Path("src").glob("**/*.py"):
    features.add_file_to_context(file)

# 2. Request review
result = await features.process_request(
    "Review all code for security issues and best practices"
)

# 3. Show suggestions
for suggestion in result['suggestions']:
    print(f"\n{suggestion['severity'].upper()}: {suggestion['message']}")
    print(f"File: {suggestion['file']}, Line: {suggestion['line']}")
    print(f"Suggestion: {suggestion['suggestion']}")
```

### Use Case 4: Understand Codebase

```python
# 1. Index the codebase
for file in Path("src").glob("**/*.py"):
    features.add_file_to_context(file)

# 2. Ask questions
questions = [
    "What does this project do?",
    "How does authentication work?",
    "Where is the database accessed?",
    "What are the main components?"
]

for question in questions:
    result = await features.process_request(question)
    print(f"\nQ: {question}")
    print(f"A: {result['message']}")
```

## Best Practices

### 1. Context Management

```python
# Add relevant files only
features.add_file_to_context(Path("src/auth.py"))
features.add_file_to_context(Path("src/models/user.py"))

# Don't add too many files at once
# Keep context focused on current task
```

### 2. Preview Before Applying

```python
# Always preview multi-file edits
result = await features.apply_multi_file_edit(
    description,
    edits,
    preview=True  # Review first!
)

# Check the preview
print(result['preview'])

# Then apply
result = await features.apply_multi_file_edit(
    description,
    edits,
    preview=False
)
```

### 3. Use Intent-Based Requests

```python
# Good: Clear intent
await features.process_request(
    "Add error handling to the login function"
)

# Better: Specific and actionable
await features.process_request(
    "Add try-except blocks around database calls in login function"
)
```

### 4. Leverage Symbol Operations

```python
# Find before refactoring
references = await features.find_references("function_name")
print(f"Found {len(references)} references")

# Then refactor
result = await features.refactor_symbol("old_name", "new_name")
```

## Advanced Features

### Custom Completion Handlers

```python
from codegenie.core.intelligent_completion import Completion, CompletionType

# Add custom completions
def custom_completion_handler(prefix, context):
    if 'api_' in prefix:
        return [
            Completion(
                text="api_endpoint",
                completion_type=CompletionType.FUNCTION,
                description="API endpoint function",
                confidence=0.9
            )
        ]
    return []

# Register handler
features.completion_engine.custom_handlers.append(custom_completion_handler)
```

### Custom Intent Recognition

```python
# Extend intent recognition
def custom_intent_recognizer(user_input):
    if 'deploy' in user_input.lower():
        return 'deployment'
    return None

# Use in processing
intent = custom_intent_recognizer(user_input) or \
         features.context_manager.infer_user_intent(user_input)
```

## Troubleshooting

### Issue: Symbols not found

```python
# Solution: Re-index files
features.context_manager.clear_context()
for file in Path("src").glob("**/*.py"):
    features.add_file_to_context(file)
```

### Issue: Edits not applying

```python
# Solution: Check file permissions and paths
result = await features.apply_multi_file_edit(
    description,
    edits,
    preview=True  # Check preview first
)

if not result['success']:
    print(f"Errors: {result['errors']}")
```

### Issue: Slow performance

```python
# Solution: Limit context size
# Only add files you're actively working on
features.context_manager.clear_context()
features.add_file_to_context(Path("current_file.py"))
```

## API Reference

See [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation.

## Examples

See `demo_claude_code_features.py` for comprehensive examples of all features.

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/codegenie/issues
- Documentation: docs/
- Community: https://community.codegenie.dev

## Next Steps

1. Try the demo: `python demo_claude_code_features.py`
2. Integrate with your IDE
3. Explore advanced features
4. Customize for your workflow

Happy coding with CodeGenie! 🧞‍♂️
