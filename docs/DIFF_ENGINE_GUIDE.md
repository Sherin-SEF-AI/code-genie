# DiffEngine User Guide

## Overview

The DiffEngine provides advanced diff generation, visualization, and application capabilities for CodeGenie. It supports multiple output formats, syntax highlighting, patch management, and multi-file operations.

## Quick Start

```python
from src.codegenie.core.diff_engine import DiffEngine

# Create engine instance
engine = DiffEngine(
    context_lines=3,           # Number of context lines
    syntax_highlighting=True,  # Enable syntax highlighting
    colored_output=True        # Enable colored terminal output
)
```

## Basic Usage

### Generate a Diff

```python
original = """def hello():
    print("Hello, World!")
"""

modified = """def hello(name="World"):
    print(f"Hello, {name}!")
"""

diff = engine.generate_diff(original, modified, "example.py")

print(f"Changes: +{diff.additions} -{diff.deletions}")
```

### Display Unified Diff

```python
# Show unified diff (like git diff)
unified = engine.show_unified_diff(diff)
print(unified)
```

Output:
```diff
--- a/example.py
+++ b/example.py
@@ -1,2 +1,2 @@
-def hello():
-    print("Hello, World!")
+def hello(name="World"):
+    print(f"Hello, {name}!")
```

### Display Side-by-Side Diff

```python
# Show side-by-side comparison
side_by_side = engine.show_side_by_side_diff(diff, width=100)
print(side_by_side)
```

## Patch Application

### Apply a Diff to a File

```python
from pathlib import Path

# Apply diff (dry run first)
result = engine.apply_diff(
    Path("example.py"),
    diff,
    dry_run=True  # Test without modifying file
)

if result['success']:
    # Apply for real
    result = engine.apply_diff(
        Path("example.py"),
        diff,
        dry_run=False
    )
    print(f"Applied {result['changes_applied']} changes")
```

### Apply Selective Changes

```python
# Apply only specific hunks (e.g., hunks 0 and 2)
result = engine.apply_selective_changes(
    Path("example.py"),
    diff,
    selected_hunks=[0, 2],
    dry_run=False
)
```

## Change Validation

### Validate Syntax

```python
# Validate Python syntax
result = engine.validate_changes(
    original="def test(): pass",
    modified="def test(): return True",
    file_type="python"
)

if result['valid']:
    print("Changes are valid!")
else:
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
```

Supported file types:
- `python`, `.py`, `text/x-python`
- `javascript`, `.js`, `text/javascript`
- `json`, `.json`, `application/json`

## Multi-File Operations

### Generate Batch Diff

```python
from pathlib import Path

# Prepare file changes
file_changes = {
    Path("src/main.py"): (
        "old content",
        "new content"
    ),
    Path("src/utils.py"): (
        "",  # Empty = new file
        "def helper(): pass"
    ),
    Path("README.md"): (
        "# Old Title",
        "# New Title"
    ),
}

# Generate diffs for all files
file_diffs = engine.generate_batch_diff(file_changes)
```

### Show Diff Summary

```python
# Display summary of all changes
summary = engine.show_diff_summary(file_diffs)
print(summary)
```

Output:
```
============================================================
Diff Summary: 3 files changed
============================================================

Total changes: +5 -2

Files:
  [M] src/main.py (+2 -1)
  [+] src/utils.py (+1 -0)
  [M] README.md (+2 -1)

============================================================
```

### Navigate File Diffs

```python
# Show detailed diffs with navigation
navigation = engine.navigate_file_diffs(
    file_diffs,
    format=DiffFormat.UNIFIED
)
print(navigation)
```

## Patch Management

### Create a Patch

```python
# Create patch from multiple file diffs
patch = engine.create_patch(
    file_diffs,
    description="Update main module and add utilities"
)

print(f"Patch: {patch.description}")
print(f"Files: {len(patch.file_diffs)}")

# Serialize patch
patch_dict = patch.to_dict()
```

### Apply a Patch

```python
# Apply each file diff in the patch
for file_diff in patch.file_diffs:
    result = engine.apply_diff(
        file_diff.file_path,
        file_diff.diff,
        dry_run=False
    )
    print(f"{file_diff.file_path}: {result['success']}")
```

## Advanced Features

### Custom Context Lines

```python
# Show more context around changes
engine = DiffEngine(context_lines=5)
diff = engine.generate_diff(original, modified, "file.py")
```

### Disable Colors

```python
# For logging or non-terminal output
engine = DiffEngine(colored_output=False)
```

### File Status Detection

```python
file_diffs = engine.generate_batch_diff(file_changes)

for fd in file_diffs:
    print(f"{fd.file_path}: {fd.file_status}")
    # file_status can be: 'added', 'modified', 'deleted'
```

## Data Models

### Diff Structure

```python
@dataclass
class Diff:
    original_file: str
    modified_file: str
    hunks: List[DiffHunk]
    additions: int
    deletions: int
    modifications: int
```

### DiffHunk Structure

```python
@dataclass
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine]
    header: str
```

### DiffLine Structure

```python
@dataclass
class DiffLine:
    line_number_old: Optional[int]
    line_number_new: Optional[int]
    content: str
    change_type: ChangeType  # ADDITION, DELETION, UNCHANGED
```

## Integration Examples

### With FileCreator

```python
from src.codegenie.core.file_creator import FileCreator
from src.codegenie.core.diff_engine import DiffEngine

file_creator = FileCreator()
diff_engine = DiffEngine()

# Create file operation
operation = file_creator.modify_file("example.py", new_content)

# Show enhanced diff
if operation.diff:
    # Convert to DiffEngine format for better visualization
    enhanced_diff = diff_engine.generate_diff(
        operation.diff.original,
        operation.diff.modified,
        str(operation.file_path)
    )
    print(diff_engine.show_side_by_side_diff(enhanced_diff))
```

### With ApprovalSystem

```python
from src.codegenie.core.approval_system import ApprovalSystem
from src.codegenie.core.diff_engine import DiffEngine

approval_system = ApprovalSystem()
diff_engine = DiffEngine()

# Generate diff
diff = diff_engine.generate_diff(original, modified, "file.py")

# Show diff for approval
print(diff_engine.show_unified_diff(diff))

# Request approval
if approval_system.request_approval("modify_file", {"file": "file.py"}):
    result = diff_engine.apply_diff("file.py", diff)
```

## Best Practices

1. **Always use dry_run first**: Test patch application before making changes
   ```python
   result = engine.apply_diff(path, diff, dry_run=True)
   if result['success']:
       engine.apply_diff(path, diff, dry_run=False)
   ```

2. **Validate changes**: Check syntax before applying
   ```python
   validation = engine.validate_changes(original, modified, file_type)
   if validation['valid']:
       engine.apply_diff(path, diff)
   ```

3. **Use selective changes**: For large diffs, apply changes incrementally
   ```python
   for i, hunk in enumerate(diff.hunks):
       print(f"Hunk {i}: {hunk.header}")
       # User selects which hunks to apply
   engine.apply_selective_changes(path, diff, selected_hunks)
   ```

4. **Show summaries for multi-file changes**: Help users understand scope
   ```python
   file_diffs = engine.generate_batch_diff(changes)
   print(engine.show_diff_summary(file_diffs))
   # Then show detailed diffs
   ```

## Error Handling

```python
try:
    result = engine.apply_diff(path, diff)
    if not result['success']:
        print(f"Error: {result['error']}")
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Use context_lines wisely**: Fewer context lines = smaller diffs
2. **Disable colors for logging**: Faster processing without ANSI codes
3. **Batch operations**: Use `generate_batch_diff()` for multiple files
4. **Lazy evaluation**: Generate diffs only when needed

## Troubleshooting

### Issue: Colors not showing in terminal
**Solution**: Ensure terminal supports ANSI colors, or disable:
```python
engine = DiffEngine(colored_output=False)
```

### Issue: Patch application fails
**Solution**: Check file exists and content matches:
```python
# Verify file content matches expected original
with open(path) as f:
    current = f.read()
if current != diff.original_file:
    print("File content has changed since diff was generated")
```

### Issue: Validation fails for valid code
**Solution**: Validation is basic; use external tools for comprehensive checks:
```python
# For Python, use pylint or flake8
# For JavaScript, use eslint
# DiffEngine validation is for basic syntax only
```

## API Reference

### DiffEngine Methods

- `generate_diff(original, modified, filename, format)` - Generate diff
- `show_unified_diff(diff)` - Format as unified diff
- `show_side_by_side_diff(diff, width, separator)` - Format side-by-side
- `apply_diff(file_path, diff, dry_run)` - Apply diff to file
- `apply_selective_changes(file_path, diff, selected_hunks, dry_run)` - Apply selected hunks
- `validate_changes(original, modified, file_type)` - Validate syntax
- `create_patch(file_diffs, description)` - Create patch
- `generate_batch_diff(file_changes)` - Generate multi-file diffs
- `show_diff_summary(file_diffs)` - Show summary
- `navigate_file_diffs(file_diffs, format)` - Show navigable diffs

### Enums

- `DiffFormat`: UNIFIED, SIDE_BY_SIDE, CONTEXT, INLINE
- `ChangeType`: ADDITION, DELETION, MODIFICATION, UNCHANGED

## Examples Repository

See `demo_diff_engine.py` for comprehensive examples of all features.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the examples in `demo_diff_engine.py`
3. Consult the API reference
4. Check the test suite in `test_diff_engine_simple.py`
