# CodeGenie Web Interface Guide

## Overview

The CodeGenie Web Interface provides a modern, real-time web-based UI for interacting with the AI coding agent. It features plan visualization, diff viewing, approval workflows, progress tracking, and live updates via WebSocket.

## Features

### 1. Plan Visualization
View execution plans with step-by-step progress tracking.

**Features:**
- Visual step indicators
- Progress bars for each step
- Dependency tracking
- Status color coding
- Timeline display
- Error messages

**Usage:**
```python
from codegenie.ui.web_components import ExecutionPlan, PlanStep

plan = ExecutionPlan(
    id="plan_1",
    name="Build REST API",
    description="Create a complete REST API",
    steps=[...],
    status="in_progress",
    created_at=datetime.now().isoformat()
)
```

### 2. Diff Viewer
Compare file changes before applying them.

**Features:**
- Side-by-side line numbers
- Syntax highlighting
- Addition/deletion colors
- File statistics
- Scrollable content

**Usage:**
```python
from codegenie.ui.web_components import FileDiff

diff = FileDiff(
    file_path="src/api.py",
    old_content="...",
    new_content="...",
    diff_lines=[...],
    additions=10,
    deletions=5
)
```

### 3. Approval Interface
Interactive approval workflow for operations.

**Features:**
- Risk level indicators
- Operation type icons
- Detailed information
- One-click approve/reject
- Real-time updates

**Usage:**
```python
from codegenie.ui.web_components import ApprovalRequest

request = ApprovalRequest(
    id="approval_1",
    title="Create new file",
    description="Create authentication module",
    operation_type="file_create",
    risk_level="safe",
    details={...},
    status="pending",
    timestamp=datetime.now().isoformat()
)
```

### 4. Progress Dashboard
Real-time progress monitoring.

**Features:**
- Metric cards
- Overall progress bar
- Time tracking
- Activity feed
- Auto-refresh

**Usage:**
```python
from codegenie.ui.web_components import ProgressMetrics

metrics = ProgressMetrics(
    total_tasks=10,
    completed_tasks=5,
    failed_tasks=1,
    in_progress_tasks=2,
    estimated_time_remaining=300,
    elapsed_time=450
)
```

### 5. Real-time Updates
WebSocket-based live updates.

**Features:**
- Channel subscriptions
- Progress streaming
- Command output streaming
- Plan updates
- Notifications

**Usage:**
```python
from codegenie.ui.realtime_updates import RealtimeUpdateManager

manager = RealtimeUpdateManager()
await manager.start()

# Send updates
await manager.send_progress_update(update)
await manager.send_command_output(output)
await manager.send_plan_update(plan_update)
```

## API Endpoints

### Plans
- `GET /api/plans/{plan_id}` - Get plan visualization

### Diffs
- `GET /api/diffs/{diff_id}` - Get diff viewer

### Approvals
- `GET /api/approvals` - Get pending approvals
- `POST /api/approvals/{request_id}/approve` - Approve request
- `POST /api/approvals/{request_id}/reject` - Reject request

### Progress
- `GET /api/progress` - Get progress dashboard

### WebSocket
- `GET /ws?channels=global,progress,commands,plans,approvals` - WebSocket connection

## WebSocket Messages

### Client → Server

**Subscribe to channels:**
```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['progress', 'commands']
}));
```

**Send chat message:**
```javascript
ws.send(JSON.stringify({
    type: 'chat',
    message: 'Create a REST API'
}));
```

### Server → Client

**Progress update:**
```json
{
    "type": "progress_update",
    "channel": "progress",
    "data": {
        "type": "task_progress",
        "task_id": "task_1",
        "task_name": "Build API",
        "progress": 50,
        "message": "Implementing authentication",
        "timestamp": "2024-11-12T18:00:00"
    }
}
```

**Command output:**
```json
{
    "type": "command_output",
    "channel": "commands",
    "data": {
        "command_id": "cmd_1",
        "command": "npm install",
        "output_type": "stdout",
        "content": "added 50 packages",
        "timestamp": "2024-11-12T18:00:00"
    }
}
```

**Plan update:**
```json
{
    "type": "plan_update",
    "channel": "plans",
    "data": {
        "plan_id": "plan_1",
        "step_id": "step_2",
        "status": "completed",
        "progress": 100,
        "message": "Step completed",
        "timestamp": "2024-11-12T18:00:00"
    }
}
```

**Notification:**
```json
{
    "type": "notification",
    "channel": "global",
    "data": {
        "message": "Task completed successfully",
        "level": "success",
        "timestamp": "2024-11-12T18:00:00"
    }
}
```

## Starting the Server

### Basic Usage

```python
from codegenie.core.agent import CodeGenieAgent
from codegenie.core.config import Config
from codegenie.ui.web_interface import WebInterface

# Create agent
config = Config()
agent = CodeGenieAgent(config)

# Create web interface
web_interface = WebInterface(agent, config)

# Start server
await web_interface.start_server(host="localhost", port=8080)
```

### With Real-time Features

```python
# Access real-time components
progress_tracker = web_interface.progress_tracker
command_streamer = web_interface.command_streamer
plan_tracker = web_interface.plan_tracker

# Track task progress
await progress_tracker.start_task("task_1", "Build API", total_steps=5)
await progress_tracker.update_progress("task_1", 3, "Implementing auth")
await progress_tracker.complete_task("task_1", "API built successfully")

# Stream command output
await command_streamer.start_command("cmd_1", "npm install")
await command_streamer.stream_output("cmd_1", "Installing...", "stdout")
await command_streamer.complete_command("cmd_1", 0)

# Track plan execution
await plan_tracker.start_plan("plan_1", "Deploy", ["step1", "step2"])
await plan_tracker.update_step("plan_1", "step1", "completed", 100)
await plan_tracker.complete_plan("plan_1")
```

## UI Tabs

### Chat Tab
Interactive chat interface with the AI agent.

### Workflows Tab
Create and manage execution workflows.

### Plans Tab
View execution plans with live updates.

### Approvals Tab
Review and approve/reject operations.

### Progress Tab
Monitor real-time progress dashboard.

### Agents Tab
Coordinate multiple specialized agents.

### Learning Tab
View learning profile and provide feedback.

### Config Tab
Manage configuration settings.

## Styling

All components come with built-in CSS. The styles are automatically included when using the `WebComponentsManager`:

```python
from codegenie.ui.web_components import WebComponentsManager

manager = WebComponentsManager()
css = manager.get_all_css()  # Get all component CSS
```

### Custom Styling

You can override styles by adding custom CSS:

```css
.plan-visualization {
    /* Your custom styles */
}

.diff-viewer {
    /* Your custom styles */
}
```

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Opera: ✅ Full support

## Security Considerations

1. **WebSocket Authentication**: Implement authentication for production
2. **CORS Configuration**: Configure CORS properly for your domain
3. **Session Management**: Use secure session storage
4. **Input Validation**: Validate all user inputs
5. **Rate Limiting**: Implement rate limiting for API endpoints

## Performance Tips

1. **Channel Subscriptions**: Subscribe only to needed channels
2. **Update Batching**: Batch multiple updates when possible
3. **Connection Pooling**: Reuse WebSocket connections
4. **Lazy Loading**: Load components on demand
5. **Caching**: Cache static resources

## Troubleshooting

### WebSocket Connection Issues

**Problem**: WebSocket disconnects frequently
**Solution**: Check network stability, implement reconnection logic

**Problem**: Messages not received
**Solution**: Verify channel subscriptions, check server logs

### UI Not Updating

**Problem**: Real-time updates not showing
**Solution**: Check WebSocket connection, verify message handling

**Problem**: Components not rendering
**Solution**: Check browser console for errors, verify data format

### Performance Issues

**Problem**: Slow page load
**Solution**: Enable caching, optimize CSS, lazy load components

**Problem**: High memory usage
**Solution**: Limit activity feed size, clean up old data

## Examples

See `demo_web_interface.py` for a complete working example with:
- Server setup
- Real-time updates
- Progress tracking
- Command streaming
- Plan execution

## Contributing

To add new components:

1. Create component class in `web_components.py`
2. Implement `generate_html()` and `generate_css()` methods
3. Add to `WebComponentsManager`
4. Update API endpoints in `web_interface.py`
5. Add JavaScript handlers
6. Update documentation

## License

Part of the CodeGenie project. See main LICENSE file.
