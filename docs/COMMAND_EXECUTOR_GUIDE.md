# CommandExecutor Guide

## Overview

The CommandExecutor is a comprehensive system for safe and intelligent command execution in CodeGenie. It provides command classification, approval workflows, streaming output, error recovery, and detailed execution tracking.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Command Classification](#command-classification)
4. [Approval Workflows](#approval-workflows)
5. [Error Recovery](#error-recovery)
6. [Streaming Output](#streaming-output)
7. [Advanced Usage](#advanced-usage)
8. [Integration Examples](#integration-examples)
9. [API Reference](#api-reference)

## Quick Start

### Basic Usage

```python
from codegenie.core.command_executor import CommandExecutor

# Create executor
executor = CommandExecutor()

# Execute a command
result = await executor.execute_command("ls -la")

# Check result
if result.success:
    print(f"Output: {result.stdout}")
else:
    print(f"Error: {result.stderr}")
```

### With Approval Callback

```python
def my_approval_callback(command: str, risk_level: CommandRiskLevel) -> bool:
    """Custom approval logic."""
    if risk_level == CommandRiskLevel.DANGEROUS:
        return False  # Block dangerous commands
    return True  # Approve others

executor = CommandExecutor(approval_callback=my_approval_callback)
result = await executor.execute_command("pip install requests")
```

## Core Concepts

### CommandResult

Every command execution returns a `CommandResult` object containing:

- `command`: The executed command string
- `exit_code`: Process exit code
- `stdout`: Standard output
- `stderr`: Standard error output
- `duration`: Execution time
- `success`: Boolean indicating success
- `status`: CommandStatus enum (SUCCESS, FAILURE, TIMEOUT, BLOCKED)
- `risk_level`: CommandRiskLevel enum (SAFE, RISKY, DANGEROUS)
- `error_analysis`: Optional ErrorAnalysis object
- `recovery_suggestions`: List of recovery suggestions

### Command Lifecycle

```
Command Input
    ↓
Classification (Safe/Risky/Dangerous)
    ↓
Approval Check (if required)
    ↓
Execution
    ↓
Error Analysis (if failed)
    ↓
Result with Recovery Suggestions
```

## Command Classification

Commands are automatically classified into three risk levels:

### Safe Commands

Read-only operations that cannot harm the system:

- File reading: `cat`, `less`, `head`, `tail`
- Directory listing: `ls`, `find`
- Information: `pwd`, `whoami`, `date`, `which`
- Git read: `git status`, `git log`, `git diff`
- Package info: `pip list`, `npm list`

**Example:**
```python
executor = CommandExecutor()
result = await executor.execute_command("ls -la")
# Automatically approved if auto_approve_safe is enabled
```

### Risky Commands

Write operations that modify the system but are generally safe:

- Directory operations: `mkdir`, `touch`
- File operations: `cp`, `mv`
- Package management: `pip install`, `npm install`
- Git operations: `git commit`, `git push`
- Build operations: `make`, `npm run`

**Example:**
```python
result = await executor.execute_command("pip install requests")
# Requires approval (unless callback auto-approves)
```

### Dangerous Commands

Destructive operations that could harm the system:

- Recursive deletion: `rm -rf`
- System operations: `sudo`, `reboot`, `shutdown`
- Disk operations: `dd`, `mkfs`, `format`
- Permission changes: `chmod -R 777`
- Pipe to shell: `curl ... | bash`

**Example:**
```python
result = await executor.execute_command("rm -rf /")
# Automatically blocked unless explicitly approved
```

### Custom Classification

You can check classification before execution:

```python
executor = CommandExecutor()
risk_level = executor.classify_command("sudo apt-get install")
print(f"Risk level: {risk_level.value}")  # "dangerous"
```

## Approval Workflows

### Default Behavior

- **Safe commands**: Auto-approved
- **Risky commands**: Require approval
- **Dangerous commands**: Blocked by default

### Custom Approval Callback

```python
def approval_callback(command: str, risk_level: CommandRiskLevel) -> bool:
    """
    Custom approval logic.
    
    Args:
        command: Command to approve
        risk_level: Risk level classification
        
    Returns:
        True to approve, False to deny
    """
    # Log the request
    logger.info(f"Approval requested for {risk_level.value}: {command}")
    
    # Custom logic
    if risk_level == CommandRiskLevel.DANGEROUS:
        # Could prompt user here
        return user_confirms(command)
    
    # Auto-approve risky commands for trusted operations
    if "pip install" in command or "npm install" in command:
        return True
    
    return False

executor = CommandExecutor(approval_callback=approval_callback)
```

### Bypassing Approval

For automated workflows, you can bypass approval:

```python
result = await executor.execute_command(
    "mkdir test_dir",
    require_approval=False  # Skip approval check
)
```

### Approval Preferences

The ApprovalManager can remember preferences:

```python
executor.approval_manager.remember_preference("pip install requests", True)
# Next time this exact command runs, it will be auto-approved
```

## Error Recovery

### Automatic Error Analysis

When a command fails, the ErrorRecoverySystem automatically analyzes the error:

```python
result = await executor.execute_command("cat missing_file.txt")

if not result.success and result.error_analysis:
    print(f"Error type: {result.error_analysis.error_type}")
    print(f"Recoverable: {result.error_analysis.is_recoverable}")
    print(f"Confidence: {result.error_analysis.confidence}")
    
    for fix in result.error_analysis.suggested_fixes:
        print(f"Suggested fix: {fix}")
```

### Error Types

The system recognizes these error types:

- `missing_command`: Command not found
- `permission`: Permission denied
- `file_missing`: File or directory not found
- `syntax`: Syntax error in command
- `import`: Python module not found
- `network`: Network connectivity issues
- `disk_space`: Disk full

### Recovery Actions

```python
result = await executor.execute_command("python script.py")

if not result.success:
    recovery_actions = executor.handle_command_error(result)
    
    for action in recovery_actions:
        print(f"Action: {action.action_type}")
        print(f"Description: {action.description}")
        
        if action.auto_applicable and action.command:
            # Could automatically apply the fix
            fix_result = await executor.execute_command(action.command)
```

### Retry Logic

Automatic retry with exponential backoff:

```python
result = await executor.execute_with_retry(
    "curl https://api.example.com/data",
    max_retries=3  # Will retry up to 3 times
)

# Retry delays: 1s, 2s, 4s (exponential backoff)
```

## Streaming Output

For long-running commands, stream output in real-time:

```python
def output_handler(line: str):
    """Handle each line of output."""
    print(f"→ {line}")
    # Could also:
    # - Update progress bar
    # - Log to file
    # - Send to UI

result = await executor.execute_with_streaming(
    "npm install",
    output_callback=output_handler
)
```

### Progress Tracking

```python
import sys

def progress_handler(line: str):
    """Show progress with spinner."""
    if "Downloading" in line:
        sys.stdout.write(".")
        sys.stdout.flush()

result = await executor.execute_with_streaming(
    "pip install large-package",
    output_callback=progress_handler
)
print()  # New line after progress dots
```

## Advanced Usage

### Execution Statistics

Track command execution metrics:

```python
# Execute several commands
await executor.execute_command("echo 'test1'")
await executor.execute_command("echo 'test2'")
await executor.execute_command("cat missing.txt")  # Will fail

# Get statistics
stats = executor.get_statistics()
print(f"Total commands: {stats['total_commands']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average duration: {stats['average_duration']:.3f}s")
```

### Command History

Access execution history:

```python
# Get last 10 commands
recent = executor.get_command_history(limit=10)

for result in recent:
    print(f"{result.command}: {result.status.value}")

# Clear history
executor.clear_history()
```

### Timeout Configuration

```python
# Set default timeout
executor = CommandExecutor(default_timeout=60)  # 60 seconds

# Override for specific command
result = await executor.execute_command(
    "long_running_task",
    timeout=300  # 5 minutes for this command
)
```

### Environment Variables

```python
result = await executor.execute_command(
    "python script.py",
    env={
        "API_KEY": "secret",
        "DEBUG": "true"
    }
)
```

### Working Directory

```python
from pathlib import Path

result = await executor.execute_command(
    "npm install",
    cwd=Path("/path/to/project")
)
```

## Integration Examples

### Project Setup Workflow

```python
class ProjectSetup:
    def __init__(self):
        self.executor = CommandExecutor()
    
    async def setup_python_project(self, name: str, path: Path):
        """Set up a new Python project."""
        commands = [
            f"mkdir -p {path}",
            f"python3 -m venv {path}/venv",
            f"mkdir -p {path}/src/{name}",
            f"mkdir -p {path}/tests",
            f"touch {path}/README.md",
            f"git init {path}",
        ]
        
        for cmd in commands:
            result = await self.executor.execute_command(cmd)
            if not result.success:
                print(f"Failed: {cmd}")
                return False
        
        return True
```

### Dependency Installation

```python
async def install_dependencies(packages: list):
    """Install Python packages with progress."""
    executor = CommandExecutor()
    
    for package in packages:
        print(f"Installing {package}...")
        
        def show_progress(line: str):
            if "Downloading" in line or "Installing" in line:
                print(f"  {line}")
        
        result = await executor.execute_with_streaming(
            f"pip install {package}",
            output_callback=show_progress
        )
        
        if result.success:
            print(f"✅ {package} installed")
        else:
            print(f"❌ {package} failed")
            if result.recovery_suggestions:
                print("Try:")
                for suggestion in result.recovery_suggestions:
                    print(f"  - {suggestion}")
```

### Build and Test Pipeline

```python
async def run_ci_pipeline(project_dir: Path):
    """Run CI/CD pipeline."""
    executor = CommandExecutor()
    
    pipeline = [
        ("Lint", "flake8 src/"),
        ("Type Check", "mypy src/"),
        ("Test", "pytest tests/ -v"),
        ("Build", "python setup.py sdist bdist_wheel"),
    ]
    
    for stage_name, command in pipeline:
        print(f"\n{'='*60}")
        print(f"Stage: {stage_name}")
        print(f"{'='*60}")
        
        result = await executor.execute_with_streaming(
            command,
            output_callback=lambda line: print(f"  {line}"),
            cwd=project_dir
        )
        
        if not result.success:
            print(f"❌ Pipeline failed at: {stage_name}")
            return False
    
    print("\n✅ Pipeline completed successfully!")
    return True
```

## API Reference

### CommandExecutor

#### Constructor

```python
CommandExecutor(
    default_timeout: int = 30,
    approval_callback: Optional[Callable[[str, CommandRiskLevel], bool]] = None
)
```

#### Methods

##### execute_command

```python
async def execute_command(
    command: str,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    require_approval: bool = True
) -> CommandResult
```

Execute a command with classification and approval.

##### execute_with_streaming

```python
async def execute_with_streaming(
    command: str,
    output_callback: Callable[[str], None],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    require_approval: bool = True
) -> CommandResult
```

Execute command with real-time output streaming.

##### execute_with_retry

```python
async def execute_with_retry(
    command: str,
    max_retries: int = 3,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None
) -> CommandResult
```

Execute command with automatic retry on failure.

##### classify_command

```python
def classify_command(command: str) -> CommandRiskLevel
```

Classify command by risk level.

##### handle_command_error

```python
def handle_command_error(result: CommandResult) -> List[RecoveryAction]
```

Handle command error and suggest recovery actions.

##### get_statistics

```python
def get_statistics() -> Dict[str, Any]
```

Get execution statistics.

##### get_command_history

```python
def get_command_history(limit: Optional[int] = None) -> List[CommandResult]
```

Get command execution history.

### CommandResult

```python
@dataclass
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: timedelta
    success: bool
    status: CommandStatus
    risk_level: CommandRiskLevel
    timestamp: datetime
    error_analysis: Optional[ErrorAnalysis]
    recovery_suggestions: List[str]
```

### CommandRiskLevel

```python
class CommandRiskLevel(Enum):
    SAFE = "safe"
    RISKY = "risky"
    DANGEROUS = "dangerous"
```

### CommandStatus

```python
class CommandStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
```

## Best Practices

### 1. Always Handle Errors

```python
result = await executor.execute_command("risky_command")
if not result.success:
    logger.error(f"Command failed: {result.stderr}")
    # Handle the error appropriately
```

### 2. Use Streaming for Long Operations

```python
# Good: Shows progress
result = await executor.execute_with_streaming(
    "npm install",
    output_callback=print_progress
)

# Bad: User sees nothing until completion
result = await executor.execute_command("npm install")
```

### 3. Set Appropriate Timeouts

```python
# Short timeout for quick commands
result = await executor.execute_command("ls", timeout=5)

# Longer timeout for builds
result = await executor.execute_command("npm run build", timeout=300)
```

### 4. Leverage Error Recovery

```python
result = await executor.execute_command("python script.py")
if not result.success:
    # Use recovery suggestions
    for action in executor.handle_command_error(result):
        if action.auto_applicable:
            await executor.execute_command(action.command)
```

### 5. Use Retry for Flaky Commands

```python
# Network requests can be flaky
result = await executor.execute_with_retry(
    "curl https://api.example.com",
    max_retries=3
)
```

## Security Considerations

1. **Command Injection**: Always validate user input before constructing commands
2. **Dangerous Commands**: Never auto-approve dangerous commands without user confirmation
3. **Sensitive Data**: Avoid logging sensitive information in command output
4. **Audit Trail**: Use command history for security auditing
5. **Least Privilege**: Run commands with minimum required permissions

## Troubleshooting

### Command Always Blocked

Check the risk classification:
```python
risk = executor.classify_command("your_command")
print(f"Risk level: {risk.value}")
```

### Timeout Issues

Increase timeout for long-running commands:
```python
result = await executor.execute_command(
    "long_command",
    timeout=600  # 10 minutes
)
```

### Missing Error Analysis

Ensure the command actually failed:
```python
if not result.success:
    if result.error_analysis is None:
        result.error_analysis = executor.error_recovery.analyze_error(result)
```

## Performance Tips

1. **Reuse Executor**: Create one executor and reuse it
2. **Batch Operations**: Group related commands
3. **Async Execution**: Use asyncio for concurrent commands
4. **Clear History**: Periodically clear history to free memory

## Conclusion

The CommandExecutor provides a robust, safe, and intelligent way to execute system commands in CodeGenie. By leveraging its classification, approval, and error recovery features, you can build reliable automation workflows while maintaining security and user control.

For more examples, see:
- `demo_command_executor.py` - Comprehensive demos
- `example_command_executor_integration.py` - Integration examples
- `test_command_executor_standalone.py` - Test suite
