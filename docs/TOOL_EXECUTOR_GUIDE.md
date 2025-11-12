# ToolExecutor Guide

## Overview

The ToolExecutor is CodeGenie's powerful environment interaction system that enables autonomous command execution, file operations, REPL interaction, and version control operations. This guide covers all ToolExecutor capabilities and security features.

## Table of Contents

1. [Command Execution](#command-execution)
2. [File Operations](#file-operations)
3. [REPL Interaction](#repl-interaction)
4. [Git Operations](#git-operations)
5. [Result Verification](#result-verification)
6. [Security Features](#security-features)
7. [Best Practices](#best-practices)

## Command Execution

### Basic Command Execution

The ToolExecutor can run shell commands and capture their output:

```python
from codegenie.core.tool_executor import ToolExecutor

executor = ToolExecutor()

# Execute a simple command
result = await executor.execute_command("ls -la", cwd="/path/to/project")

print(result.stdout)  # Command output
print(result.stderr)  # Error output
print(result.exit_code)  # Exit code
print(result.success)  # True if exit_code == 0
```

### Iterative Command Execution

ToolExecutor can automatically retry commands with corrections:

```python
# Execute with automatic retry on failure
result = await executor.execute_with_retry(
    command="npm test",
    max_retries=3
)

# ToolExecutor will:
# 1. Run the command
# 2. Analyze any errors
# 3. Suggest fixes
# 4. Retry with corrections
```

### Command Output Analysis

```python
# Analyze command output
analysis = await executor.analyze_command_output(
    output=result.stdout,
    errors=result.stderr
)

print(analysis.success)  # Was command successful?
print(analysis.errors)  # List of detected errors
print(analysis.warnings)  # List of warnings
print(analysis.suggestions)  # Suggested fixes
```

### Real-World Examples

**Running Tests:**
```
You: Run the test suite

CodeGenie: Running tests with ToolExecutor...

$ pytest tests/

✅ 45 tests passed
❌ 3 tests failed

Analyzing failures...
- test_user_login: AssertionError on line 23
- test_password_hash: bcrypt import missing
- test_email_validation: regex pattern incorrect

Fixing issues...
✅ Installed bcrypt
✅ Fixed regex pattern
✅ Updated assertion

Re-running tests...
$ pytest tests/

✅ All 48 tests passed!
```

**Installing Dependencies:**
```
You: Install the required packages

CodeGenie: Installing dependencies...

$ pip install -r requirements.txt

❌ Error: Could not find a version that satisfies the requirement numpy==1.24.0

Analyzing error...
Issue: numpy 1.24.0 not available for Python 3.12

Fixing...
✅ Updated requirements.txt to numpy>=1.23.0,<2.0.0

$ pip install -r requirements.txt

✅ Successfully installed all packages
```

## File Operations

### Editing Files

```python
from codegenie.core.tool_executor import FileEditor

editor = FileEditor()

# Edit a single file
await editor.edit_file(
    file_path="src/main.py",
    edits=[
        FileEdit(
            edit_type="replace",
            line_start=10,
            line_end=15,
            content="def new_function():\n    pass"
        )
    ]
)
```

### Multi-File Editing

```python
# Edit multiple files atomically
await editor.edit_multiple_files({
    "src/models/user.py": [
        FileEdit(edit_type="insert", line_start=20, content="role: str")
    ],
    "src/schemas/user.py": [
        FileEdit(edit_type="insert", line_start=15, content="role: str")
    ],
    "tests/test_user.py": [
        FileEdit(edit_type="insert", line_start=30, content="def test_role(): ...")
    ]
})
```

### File Creation

```python
# Create new file
await editor.create_file(
    file_path="src/services/new_service.py",
    content="""
class NewService:
    def __init__(self):
        pass
    """
)
```

### Real-World Examples

**Refactoring Across Files:**
```
You: Rename the User class to Account across all files

CodeGenie: Analyzing codebase...

Found User class in 12 files:
- src/models/user.py (definition)
- src/services/user_service.py (import)
- src/api/users.py (import)
... (9 more files)

Performing atomic refactoring...
✅ Updated src/models/user.py
✅ Updated src/services/user_service.py
✅ Updated src/api/users.py
... (9 more)

✅ Refactoring complete! All references updated.
```

## REPL Interaction

### Starting a REPL Session

```python
from codegenie.core.tool_executor import REPLManager

repl = REPLManager()

# Start Python REPL
session = await repl.start_repl("python")

# Execute code in REPL
result = await repl.execute_in_repl(
    session=session,
    code="import numpy as np\nprint(np.array([1, 2, 3]))"
)

print(result.output)  # [1 2 3]
```

### Testing Code Snippets

```python
# Test code before committing
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""

result = await repl.execute_in_repl(session, code)
print(result.output)  # 55
```

### Real-World Examples

**Testing Database Queries:**
```
You: Test this SQL query before adding it to the code

CodeGenie: Starting PostgreSQL REPL...

psql> SELECT users.name, COUNT(posts.id) as post_count
      FROM users
      LEFT JOIN posts ON users.id = posts.user_id
      GROUP BY users.id
      ORDER BY post_count DESC
      LIMIT 10;

✅ Query executed successfully
📊 Results:
   name          | post_count
   --------------|------------
   Alice         | 45
   Bob           | 32
   ...

Query looks good! Shall I add it to the code?
```

**Testing API Endpoints:**
```
You: Test the new endpoint before deploying

CodeGenie: Starting development server...

$ python -m uvicorn main:app --reload

Server running at http://localhost:8000

Testing endpoint...
$ curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'

✅ Response: 201 Created
{
  "id": 123,
  "name": "Test User",
  "email": "test@example.com"
}

Endpoint working correctly!
```

## Git Operations

### Creating Commits

```python
from codegenie.core.tool_executor import GitIntegration

git = GitIntegration()

# Create commit
await git.create_commit(
    message="Add user authentication feature",
    files=["src/auth.py", "tests/test_auth.py"]
)
```

### Branch Management

```python
# Create and switch to new branch
await git.manage_branch(
    operation="create",
    branch_name="feature/user-auth"
)

# Merge branch
await git.manage_branch(
    operation="merge",
    branch_name="feature/user-auth",
    target="main"
)
```

### Merge Conflict Resolution

```python
# Resolve merge conflicts
conflict = MergeConflict(
    file="src/models/user.py",
    ours="class User:\n    role: str",
    theirs="class User:\n    permissions: List[str]"
)

resolution = await git.resolve_merge_conflict(conflict)
```

### Real-World Examples

**Automatic Commits:**
```
You: Implement user authentication and commit the changes

CodeGenie: Implementing authentication...

✅ Created src/services/auth.py
✅ Created src/models/user.py
✅ Created tests/test_auth.py
✅ Updated src/main.py

Creating commit...
$ git add src/services/auth.py src/models/user.py tests/test_auth.py src/main.py
$ git commit -m "feat: Add user authentication with JWT

- Implement JWT token generation and validation
- Add User model with password hashing
- Create authentication endpoints
- Add comprehensive tests"

✅ Commit created: abc123f
```

**Handling Merge Conflicts:**
```
You: Merge the feature branch

CodeGenie: Merging feature/user-auth into main...

$ git merge feature/user-auth

⚠️ Merge conflict in src/models/user.py

Analyzing conflict...
- Main branch: Added 'role' field
- Feature branch: Added 'permissions' field

Resolution: Keep both fields

Resolving conflict...
✅ Conflict resolved
✅ Merge completed
```

## Result Verification

### Automatic Verification

ToolExecutor automatically verifies command results:

```python
# Execute with verification
result = await executor.execute_and_verify(
    command="npm run build",
    verification_criteria=[
        "Build completed successfully",
        "No errors",
        "dist/ directory created"
    ]
)

if result.verified:
    print("Build successful and verified!")
else:
    print(f"Verification failed: {result.verification_errors}")
```

### Custom Verification

```python
# Define custom verification logic
async def verify_test_results(result):
    if "All tests passed" in result.stdout:
        return True, "Tests passed"
    return False, "Some tests failed"

result = await executor.execute_command(
    "pytest",
    verification_fn=verify_test_results
)
```

### Real-World Examples

**Build Verification:**
```
You: Build the project and verify it works

CodeGenie: Building project...

$ npm run build

✅ Build completed
✅ No errors
✅ Output files created

Verifying build...
✅ dist/main.js exists (245 KB)
✅ dist/styles.css exists (45 KB)
✅ All assets copied
✅ Source maps generated

Running smoke tests...
$ node dist/main.js --version
✅ Version: 1.0.0

Build verified successfully!
```

## Security Features

### Sandboxed Execution

All commands run in a secure sandbox:

```python
# Commands are sandboxed by default
executor = ToolExecutor(sandbox=True)

# Dangerous commands are blocked
result = await executor.execute_command("rm -rf /")
# Raises SecurityError: Dangerous command blocked
```

### Permission System

```python
# Configure permissions
executor = ToolExecutor(
    permissions={
        "file_write": True,
        "network_access": False,
        "system_commands": False
    }
)

# Network commands blocked
result = await executor.execute_command("curl https://example.com")
# Raises PermissionError: Network access not allowed
```

### Command Whitelisting

```python
# Only allow specific commands
executor = ToolExecutor(
    whitelist=["npm", "pytest", "git"]
)

# Allowed
await executor.execute_command("npm test")

# Blocked
await executor.execute_command("sudo rm -rf /")
# Raises SecurityError: Command not in whitelist
```

### Audit Logging

All ToolExecutor operations are logged:

```python
# View audit log
logs = await executor.get_audit_log()

for log in logs:
    print(f"{log.timestamp}: {log.command}")
    print(f"  User: {log.user}")
    print(f"  Result: {log.result}")
    print(f"  Duration: {log.duration}s")
```

### Real-World Examples

**Secure Deployment:**
```
You: Deploy to production

CodeGenie: Deploying with security checks...

🔒 Security Checks:
✅ No hardcoded secrets
✅ All dependencies scanned
✅ No high-severity vulnerabilities
✅ SSL certificates valid
✅ Firewall rules configured

Deploying...
$ kubectl apply -f deployment.yaml

✅ Deployment successful

📝 Audit Log:
- Command: kubectl apply
- User: admin
- Time: 2024-01-15 14:30:00
- Result: Success
- Changes: 3 pods updated
```

## Best Practices

### 1. Always Verify Results

```python
# Good: Verify command succeeded
result = await executor.execute_command("npm test")
if not result.success:
    print(f"Tests failed: {result.stderr}")
    
# Better: Use automatic verification
result = await executor.execute_and_verify(
    "npm test",
    verification_criteria=["All tests passed"]
)
```

### 2. Use Atomic Operations

```python
# Good: Edit multiple files atomically
await editor.edit_multiple_files({
    "file1.py": [edit1],
    "file2.py": [edit2]
})

# Bad: Edit files separately (can leave inconsistent state)
await editor.edit_file("file1.py", [edit1])
await editor.edit_file("file2.py", [edit2])  # If this fails, file1 is modified
```

### 3. Handle Errors Gracefully

```python
try:
    result = await executor.execute_command("npm test")
except CommandExecutionError as e:
    print(f"Command failed: {e}")
    # Attempt recovery
    await executor.execute_command("npm install")
    result = await executor.execute_command("npm test")
```

### 4. Use Appropriate Timeouts

```python
# Set timeout for long-running commands
result = await executor.execute_command(
    "npm run build",
    timeout=300  # 5 minutes
)
```

### 5. Clean Up Resources

```python
# Always close REPL sessions
session = await repl.start_repl("python")
try:
    result = await repl.execute_in_repl(session, code)
finally:
    await repl.close_repl(session)
```

## Configuration

Configure ToolExecutor behavior:

```yaml
# ~/.config/codegenie/config.yaml

tool_executor:
  # Security
  sandbox: true
  permissions:
    file_write: true
    file_delete: false
    network_access: true
    system_commands: false
  
  # Performance
  timeout: 300
  max_retries: 3
  parallel_execution: true
  
  # Logging
  audit_log: true
  log_level: "INFO"
  
  # Verification
  auto_verify: true
  verification_timeout: 60
```

## Troubleshooting

### Command Execution Fails

**Problem**: Commands fail with permission errors

**Solution**:
```yaml
tool_executor:
  permissions:
    file_write: true
    system_commands: true
```

### REPL Session Hangs

**Problem**: REPL session becomes unresponsive

**Solution**:
```python
# Set timeout
result = await repl.execute_in_repl(
    session,
    code,
    timeout=30
)
```

### File Edits Not Applied

**Problem**: File edits don't seem to take effect

**Solution**:
```python
# Verify file was actually modified
result = await editor.edit_file(file_path, edits)
if not result.success:
    print(f"Edit failed: {result.error}")
```

## API Reference

See [API Reference](API_REFERENCE.md#tool-executor-api) for complete API documentation.

## Examples

See [examples/tool_executor/](../examples/tool_executor/) for more examples.

## Support

For ToolExecutor issues:
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Visit [Community Forum](https://community.codegenie.dev)
- Email: support@codegenie.dev
