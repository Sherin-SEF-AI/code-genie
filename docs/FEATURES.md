# CodeGenie Features Guide

Complete reference for all CodeGenie features and capabilities.

## Table of Contents
1. [Planning Agent](#planning-agent)
2. [File Operations](#file-operations)
3. [Command Execution](#command-execution)
4. [Project Scaffolding](#project-scaffolding)
5. [Diff Engine](#diff-engine)
6. [Approval System](#approval-system)
7. [Context Analysis](#context-analysis)
8. [Multi-File Editing](#multi-file-editing)
9. [Error Recovery](#error-recovery)
10. [Template System](#template-system)
11. [Dependency Management](#dependency-management)
12. [Documentation Generation](#documentation-generation)
13. [Multi-Agent System](#multi-agent-system)
14. [Autonomous Mode](#autonomous-mode)
15. [Natural Language Programming](#natural-language-programming)

## Planning Agent

The Planning Agent creates detailed execution plans before taking actions.

### Features

- **Task Decomposition**: Breaks complex tasks into manageable steps
- **Dependency Analysis**: Identifies dependencies between steps
- **Risk Assessment**: Evaluates risk level of each operation
- **Progress Tracking**: Monitors execution progress in real-time
- **Complexity Estimation**: Estimates time and effort required

### Usage

```
You: Create a complete REST API with authentication

CodeGenie: Let me create a plan...

📋 Execution Plan (12 steps):
1. Set up project structure
2. Configure database
3. Create User model
4. Implement authentication
5. Create API endpoints
6. Add validation
7. Implement error handling
8. Create tests
9. Add documentation
10. Security hardening
11. Performance optimization
12. Final validation

⏱️ Estimated time: 20 minutes
🎯 Risk level: Medium

Proceed? (y/n):
```

### Configuration

```yaml
# ~/.config/codegenie/config.yaml
planning:
  enabled: true
  show_estimates: true
  require_approval: true
  max_steps: 50
```


## File Operations

Automatic file creation, modification, and deletion with safety features.

### Create Files

```
You: Create a User model with email and password

CodeGenie: Creating User model...

✅ Created: src/models/user.py
✅ Created: tests/test_user.py

Files created with:
- Type hints
- Docstrings
- Input validation
- Unit tests
```

### Modify Files

```
You: Add a 'role' field to the User model

CodeGenie: Modifying User model...

📝 Changes to src/models/user.py:
+ Added role field (Enum: admin, user, guest)
+ Updated __init__ method
+ Added role validation
+ Updated tests

Preview diff? (y/n):
```

### Delete Files

```
You: Delete the old migration files

CodeGenie: ⚠️ This will delete 3 files:
- migrations/0001_old.py
- migrations/0002_old.py
- migrations/0003_old.py

Backups will be created.
Proceed? (y/n):
```

### Safety Features

- **Backup Creation**: Automatic backups before modifications
- **Diff Preview**: See changes before applying
- **Undo Support**: Rollback recent changes
- **Conflict Detection**: Warns about conflicting changes


## Command Execution

Safe execution of system commands with approval workflows.

### Command Classification

Commands are classified by risk level:

**Safe Commands** (auto-approved):
- `ls`, `cat`, `grep`, `find`
- `git status`, `git log`, `git diff`
- `python --version`, `pip list`

**Risky Commands** (require approval):
- `pip install`, `npm install`
- `git commit`, `git push`
- `python script.py`

**Dangerous Commands** (require explicit confirmation):
- `rm -rf`, `sudo`, `format`
- `git reset --hard`
- System-level operations

### Usage

```
You: Install pytest and run tests

CodeGenie: I'll install pytest and run tests.

Command 1: pip install pytest
Risk: Risky (installs package)
Approve? (y/n): y

✅ pytest installed

Command 2: pytest tests/
Risk: Safe (read-only)
Executing...

✅ 15 tests passed
```

### Streaming Output

```
You: Run the development server

CodeGenie: Starting server...

🚀 Server output:
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000

Press Ctrl+C to stop
```

### Error Handling

```
You: Run tests

CodeGenie: Running tests...

❌ Command failed with exit code 1

Error: ModuleNotFoundError: No module named 'pytest'

💡 Suggested fix:
Install pytest: pip install pytest

Shall I install pytest and retry? (y/n):
```


## Project Scaffolding

Quickly create new projects with proper structure and configuration.

### Supported Project Types

- **Python**: FastAPI, Django, Flask, CLI tools
- **JavaScript/TypeScript**: React, Next.js, Express, Vue
- **Go**: Web services, CLI tools, gRPC
- **Rust**: CLI tools, web services, libraries

### Usage

```
You: Create a new FastAPI project

CodeGenie: Creating FastAPI project...

Project type: Web API
Framework: FastAPI
Database: PostgreSQL
Testing: pytest

✅ Project structure created
✅ Dependencies configured
✅ Database setup
✅ Git initialized
✅ Tests created

Project ready at: ./my-api/
```

### Features

- **Smart Detection**: Detects project type from description
- **Best Practices**: Follows framework conventions
- **Complete Setup**: Includes tests, docs, and configuration
- **Version Control**: Initializes git with .gitignore
- **Dependency Installation**: Installs required packages

### Custom Templates

```
You: Create a project using my custom template

CodeGenie: Loading custom template...

Template: my-company-api-template
Variables needed:
- project_name: my-new-api
- database: postgresql
- auth_method: jwt

Creating project...
✅ Project created from custom template
```

