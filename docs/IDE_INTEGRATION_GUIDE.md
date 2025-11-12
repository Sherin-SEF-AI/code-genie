# IDE Integration Guide

## Overview

CodeGenie provides seamless integration with popular IDEs through a comprehensive bridge system. This guide covers how to use and extend IDE integration features.

## Supported IDEs

### VS Code
- Full Language Server Protocol (LSP) support
- Extension API compatibility
- Webview panels
- Integrated terminal
- Code lens and code actions

### JetBrains IDEs
- IntelliJ IDEA
- PyCharm
- WebStorm
- GoLand
- RubyMine
- And all other JetBrains IDEs

## Quick Start

### VS Code Integration

```python
from pathlib import Path
from codegenie.integrations.ide_bridge import VSCodeBridge

# Initialize bridge
project_root = Path("/path/to/project")
vscode = VSCodeBridge(project_root)

# Initialize extension
init_result = await vscode.initialize()
print(f"Capabilities: {init_result['capabilities']}")

# Open a file
await vscode.open_file(Path("src/main.py"), line=10)

# Show a diff
await vscode.show_diff(
    file_path=Path("src/main.py"),
    original="old content",
    modified="new content"
)
```

### JetBrains Integration

```python
from pathlib import Path
from codegenie.integrations.ide_bridge import JetBrainsBridge

# Initialize bridge
project_root = Path("/path/to/project")
jetbrains = JetBrainsBridge(project_root, ide_type="PyCharm")

# Initialize plugin
init_result = await jetbrains.initialize()

# Show balloon notification
await jetbrains.show_balloon("Analysis complete", "info")

# Create intention action
await jetbrains.create_intention_action(
    file_path=Path("src/main.py"),
    range={'start': {'line': 10, 'character': 0}, 'end': {'line': 10, 'character': 20}},
    text="Add type hint",
    action_id="add_type_hint"
)
```

## Features

### 1. Inline Diff Preview

Show changes before applying them:

```python
from codegenie.integrations.ide_features import InlineDiffProvider

provider = InlineDiffProvider()

# Create a diff
diff = provider.create_diff(
    file_path=Path("example.py"),
    start_line=10,
    start_column=0,
    end_line=10,
    end_column=20,
    original_text="def old_function():",
    modified_text="def new_function():",
    description="Rename function"
)

# Apply the diff
content = file.read_text()
new_content = provider.apply_diff(diff_id, content)
```

### 2. Quick Actions

Provide quick fixes and refactorings:

```python
from codegenie.integrations.ide_features import QuickActionProvider, QuickActionType

provider = QuickActionProvider()

# Create a fix error action
action = provider.create_fix_error_action(
    file_path=Path("example.py"),
    line=10,
    column=0,
    error_message="Missing import",
    fix_text="from typing import List"
)

# Create a refactor action
refactor = provider.create_refactor_action(
    file_path=Path("example.py"),
    start_line=15,
    start_column=0,
    end_line=20,
    end_column=0,
    refactor_type="extract_method",
    title="Extract method"
)

# Get actions for a range
actions = provider.get_actions_for_range(
    file_path=Path("example.py"),
    start_line=10,
    start_column=0,
    end_line=25,
    end_column=0
)
```

### 3. Code Lenses

Add contextual information above code:

```python
from codegenie.integrations.ide_features import CodeLensProvider

provider = CodeLensProvider()

# Add run test lens
lens = provider.add_run_test_lens(
    file_path=Path("test_example.py"),
    line=10,
    test_name="test_example"
)

# Add references lens
ref_lens = provider.add_references_lens(
    file_path=Path("example.py"),
    line=20,
    symbol="MyClass",
    reference_count=5
)

# Add complexity lens
complexity_lens = provider.add_complexity_lens(
    file_path=Path("example.py"),
    line=30,
    function_name="complex_function",
    complexity=12
)
```

### 4. File Synchronization

Keep files in sync between IDE and CodeGenie:

```python
# Sync a single file
status = await vscode.sync_file(Path("example.py"))
if not status.in_sync:
    print(f"File out of sync: {status.conflicts}")

# Sync all active files
results = await vscode.sync_all_files()
for file_path, status in results.items():
    if not status.in_sync:
        print(f"{file_path}: {status.conflicts}")

# Get file state
file_state = vscode.get_file_state(Path("example.py"))
print(f"Version: {file_state.version}")
print(f"Is dirty: {file_state.is_dirty}")

# Mark file as dirty/clean
vscode.mark_file_dirty(Path("example.py"))
vscode.mark_file_clean(Path("example.py"))
```

## Feature Manager

Use the feature manager to coordinate all IDE features:

```python
from codegenie.integrations.ide_features import IDEFeatureManager

manager = IDEFeatureManager()

# Get providers
diff_provider = manager.get_diff_provider()
action_provider = manager.get_action_provider()
lens_provider = manager.get_lens_provider()

# Analyze code and suggest improvements
suggestions = await manager.suggest_improvements(
    file_path=Path("example.py"),
    content=file.read_text(),
    language="python"
)

# Clear all features for a file
manager.clear_all_features_for_file(Path("example.py"))

# Clear all features
manager.clear_all_features()
```

## VS Code Specific Features

### Webview Panels

```python
html = """
<html>
    <body>
        <h1>CodeGenie Analysis</h1>
        <p>Your code looks great!</p>
    </body>
</html>
"""

await vscode.show_webview(
    title="Analysis Results",
    html=html,
    view_column=2
)
```

### Terminal Integration

```python
# Create terminal
terminal_id = await vscode.create_terminal("CodeGenie", project_root)

# Send commands
await vscode.send_terminal_text(terminal_id, "npm test\n")
```

### Quick Pick and Input

```python
# Show quick pick
choice = await vscode.show_quick_pick(
    items=["Option 1", "Option 2", "Option 3"],
    title="Choose an option"
)

# Show input box
value = await vscode.show_input_box(
    prompt="Enter a value",
    default="default value"
)
```

### Workspace Edits

```python
edits = {
    "src/file1.py": [
        {
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 0, 'character': 0}
            },
            'newText': '# Header comment\n'
        }
    ],
    "src/file2.py": [
        {
            'range': {
                'start': {'line': 10, 'character': 0},
                'end': {'line': 10, 'character': 10}
            },
            'newText': 'new_text'
        }
    ]
}

await vscode.apply_workspace_edit(edits)
```

## JetBrains Specific Features

### Inspections

```python
await jetbrains.create_inspection(
    file_path=Path("example.py"),
    range={
        'start': {'line': 10, 'character': 0},
        'end': {'line': 10, 'character': 20}
    },
    message="Unused variable 'temp'",
    severity="WARNING"
)
```

### Refactoring

```python
await jetbrains.run_refactoring(
    refactoring_type="rename",
    file_path=Path("example.py"),
    params={
        'oldName': 'old_variable',
        'newName': 'new_variable',
        'line': 20
    }
)
```

### Tool Windows

```python
await jetbrains.show_tool_window(
    window_id="CodeGenie",
    content="<html><body><h2>Analysis Results</h2></body></html>"
)
```

### Gutter Icons

```python
await jetbrains.create_gutter_icon(
    file_path=Path("example.py"),
    line=25,
    icon="run",
    tooltip="Run this test"
)
```

### Execute Actions

```python
await jetbrains.execute_action(
    action_id="ReformatCode",
    context={'file': str(Path("example.py"))}
)
```

## Event Handling

Handle IDE events:

```python
from codegenie.integrations.ide_bridge import IDEEvent, IDEEventType

# Register event handler
async def on_file_opened(event: IDEEvent):
    print(f"File opened: {event.file_path}")

vscode.register_handler(IDEEventType.FILE_OPENED, on_file_opened)

# Handle event
event = IDEEvent(
    event_type=IDEEventType.FILE_OPENED,
    file_path=Path("example.py")
)
response = await vscode.handle_event(event)
```

## WebSocket Server

For real-time communication:

```python
from codegenie.integrations.ide_bridge import WebSocketIDEServer

server = WebSocketIDEServer(
    bridge=vscode,
    host="localhost",
    port=8765
)

# Start server
await server.start()

# Broadcast message
await server.broadcast({
    'type': 'notification',
    'message': 'Analysis complete'
})
```

## Best Practices

### 1. Always Initialize

```python
# Initialize before using
init_result = await bridge.initialize()
```

### 2. Handle Errors

```python
try:
    await vscode.open_file(Path("example.py"))
except Exception as e:
    print(f"Error: {e}")
```

### 3. Clean Up

```python
# Clear features when done
manager.clear_all_features_for_file(file_path)
```

### 4. Use Feature Manager

```python
# Use feature manager for coordination
manager = bridge.get_feature_manager()
```

### 5. Sync Files

```python
# Sync before making changes
status = await bridge.sync_file(file_path)
if not status.in_sync:
    # Handle conflicts
    pass
```

## Advanced Usage

### Custom Action Handlers

```python
from codegenie.integrations.ide_features import QuickActionType

async def handle_custom_action(action):
    print(f"Handling action: {action.title}")
    # Custom logic here

provider = QuickActionProvider()
provider.register_handler(QuickActionType.REFACTOR, handle_custom_action)
```

### Custom Code Lenses

```python
# Add custom lens
lens = provider.add_lens(
    file_path=Path("example.py"),
    line=10,
    column=0,
    command="custom.command",
    title="Custom Action",
    arguments=["arg1", "arg2"]
)
```

### File Watching

```python
async def on_file_change(file_path: Path, content: str):
    print(f"File changed: {file_path}")
    # Handle change

await bridge.watch_file_changes(on_file_change)
```

## Troubleshooting

### Connection Issues

```python
# Check if IDE is connected
if not bridge.clients:
    print("No IDE connected")
```

### Sync Issues

```python
# Force sync
status = await bridge.sync_file(file_path)
if not status.in_sync:
    print(f"Conflicts: {status.conflicts}")
    # Resolve conflicts
```

### Feature Not Showing

```python
# Verify feature was added
lenses = provider.get_lenses_for_file(file_path)
print(f"Lenses: {len(lenses)}")
```

## Examples

See the following files for complete examples:
- `demo_ide_integration.py`: Comprehensive demo
- `test_ide_integration_simple.py`: Unit tests

## API Reference

### IDEBridge
- `initialize()`: Initialize IDE connection
- `handle_event(event)`: Handle IDE event
- `sync_file(file_path)`: Sync a file
- `sync_all_files()`: Sync all files
- `show_inline_diff(...)`: Show inline diff
- `register_quick_action(...)`: Register quick action
- `add_code_lens(...)`: Add code lens

### VSCodeBridge
- `open_file(file_path, line)`: Open file
- `show_diff(file_path, original, modified)`: Show diff
- `show_webview(title, html)`: Show webview
- `create_terminal(name, cwd)`: Create terminal
- `apply_workspace_edit(edits)`: Apply edits

### JetBrainsBridge
- `create_intention_action(...)`: Create intention
- `create_inspection(...)`: Create inspection
- `run_refactoring(...)`: Run refactoring
- `show_balloon(message, type)`: Show balloon
- `show_tool_window(id, content)`: Show tool window

### InlineDiffProvider
- `create_diff(...)`: Create diff
- `apply_diff(diff_id, content)`: Apply diff
- `get_diffs_for_file(file_path)`: Get diffs

### QuickActionProvider
- `create_action(...)`: Create action
- `create_fix_error_action(...)`: Create fix action
- `create_refactor_action(...)`: Create refactor action
- `get_actions_for_range(...)`: Get actions

### CodeLensProvider
- `add_lens(...)`: Add lens
- `add_run_test_lens(...)`: Add test lens
- `add_references_lens(...)`: Add references lens
- `get_lenses_for_file(file_path)`: Get lenses

## Contributing

To add support for a new IDE:

1. Create a new bridge class inheriting from `IDEBridge`
2. Implement IDE-specific methods
3. Add initialization logic
4. Test with the IDE
5. Document the integration

## Support

For issues or questions:
- Check the troubleshooting section
- Review example files
- Open an issue on GitHub
