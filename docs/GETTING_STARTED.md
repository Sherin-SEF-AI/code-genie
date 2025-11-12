# Getting Started with CodeGenie

Welcome to CodeGenie! This guide will help you get up and running quickly with your AI-powered coding assistant.

## Table of Contents
1. [Installation](#installation)
2. [First Steps](#first-steps)
3. [Basic Concepts](#basic-concepts)
4. [Your First Project](#your-first-project)
5. [Essential Features](#essential-features)
6. [Next Steps](#next-steps)

## Installation

### Prerequisites

Before installing CodeGenie, ensure you have:

- **Python 3.9 or higher**
  ```bash
  python --version  # Should show 3.9+
  ```

- **Ollama** (for local AI models)
  - Download from [ollama.ai](https://ollama.ai)
  - Or install via package manager:
    ```bash
    # macOS
    brew install ollama
    
    # Linux
    curl -fsSL https://ollama.ai/install.sh | sh
    ```

- **Git** (recommended)
  ```bash
  git --version
  ```

### Install CodeGenie

#### Option 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/codegenie.git
cd codegenie

# Run the quick start script
./quick_start.sh
```

The script will:
- Create a virtual environment
- Install all dependencies
- Verify your setup
- Let you choose a demo to run

#### Option 2: Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install CodeGenie
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

### Install AI Models

CodeGenie uses Ollama for local AI models. Install the recommended models:

```bash
# Start Ollama service
ollama serve

# In another terminal, pull models
ollama pull llama3.1:8b      # General purpose (4.7GB)
ollama pull codellama:7b      # Code generation (3.8GB)
```

**Optional models for advanced features:**
```bash
ollama pull llama3.1:70b      # More powerful, requires 40GB+ RAM
ollama pull mistral:7b        # Alternative general model
```

### Verify Installation

```bash
# Check CodeGenie installation
codegenie --version

# Check Ollama connection
ollama list

# Run system check
codegenie --system-info
```

Expected output:
```
✅ Python 3.9+ detected
✅ Ollama service running
✅ Models available: llama3.1:8b, codellama:7b
✅ All dependencies installed
```

## First Steps

### Start CodeGenie

```bash
# Start in current directory
codegenie

# Or specify a project directory
codegenie /path/to/your/project
```

You'll see the CodeGenie prompt:
```
🧞 CodeGenie v1.0.0
Ready to help with your coding tasks!

Type 'help' for available commands or describe what you'd like to build.

You: 
```

### Try Your First Command

Let's create a simple Python function:

```
You: Create a Python function to calculate the factorial of a number

CodeGenie: I'll create a factorial function for you.

✅ Created: src/math_utils.py

def factorial(n: int) -> int:
    """
    Calculate the factorial of a number.
    
    Args:
        n: A non-negative integer
        
    Returns:
        The factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

Would you like me to create tests for this function?
```

### Interactive Help

```
You: help

Available commands:
  help              - Show this help message
  exit/quit         - Exit CodeGenie
  clear             - Clear conversation history
  /autonomous on    - Enable autonomous mode
  /agents list      - Show available agents
  /context show     - Display current context
  /history          - Show conversation history
  /rollback         - Undo last operation
  
You can also:
  - Describe what you want to build
  - Ask questions about your code
  - Request code reviews
  - Get debugging help
```

## Basic Concepts

### 1. Planning Agent

CodeGenie creates a plan before executing complex tasks:

```
You: Create a REST API for a blog

CodeGenie: Let me create a plan for your blog API...

📋 Execution Plan:
1. Set up FastAPI project structure
2. Create database models (User, Post, Comment)
3. Implement authentication (JWT)
4. Create CRUD endpoints for posts
5. Add comment functionality
6. Create tests
7. Generate API documentation

Estimated time: 15 minutes

Shall I proceed? (y/n):
```

### 2. File Operations

CodeGenie can create, modify, and delete files:

```
You: Create a User model with email and password fields

CodeGenie: Creating User model...

✅ Created: src/models/user.py
✅ Created: tests/test_user.py

Preview of changes:
[Shows diff of new files]

Apply changes? (y/n):
```

### 3. Command Execution

CodeGenie can run commands safely:

```
You: Install pytest

CodeGenie: I'll install pytest for you.

Command: pip install pytest

This is a safe command. Executing...

✅ pytest installed successfully
```

### 4. Approval System

For risky operations, CodeGenie asks for approval:

```
You: Delete all migration files

CodeGenie: ⚠️ This operation will delete 5 files:
- migrations/0001_initial.py
- migrations/0002_add_users.py
- migrations/0003_add_posts.py
- migrations/0004_add_comments.py
- migrations/0005_add_likes.py

This action cannot be undone.

Proceed? (y/n):
```

### 5. Context Awareness

CodeGenie understands your project:

```
You: Add a new endpoint

CodeGenie: I see you're using FastAPI with SQLAlchemy.
I'll follow your existing patterns:
- Type hints for all parameters
- Async endpoints
- Dependency injection for database
- Pydantic schemas for validation

What should the endpoint do?
```

## Your First Project

Let's build a complete project from scratch.

### Step 1: Initialize Project

```
You: Create a new FastAPI project for a todo list application

CodeGenie: I'll create a todo list API project.

📋 Plan:
1. Create project structure
2. Set up FastAPI application
3. Configure database (SQLite for development)
4. Create Todo model
5. Implement CRUD endpoints
6. Add tests
7. Create documentation

Creating project...

✅ Project structure created
✅ FastAPI configured
✅ Database setup complete
✅ Todo model created
✅ CRUD endpoints implemented
✅ Tests created (12 tests, all passing)
✅ API documentation generated

Your project is ready!

Project structure:
todo-api/
├── src/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   └── todo.py
│   ├── api/
│   │   └── todos.py
│   └── schemas/
│       └── todo.py
├── tests/
│   └── test_todos.py
├── requirements.txt
└── README.md

To start the server:
  cd todo-api
  pip install -r requirements.txt
  uvicorn src.main:app --reload
```

### Step 2: Run the Project

```bash
cd todo-api
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Visit http://localhost:8000/docs to see your API documentation!

### Step 3: Add Features

```
You: Add user authentication to the todo API

CodeGenie: I'll add JWT authentication.

📋 Plan:
1. Create User model
2. Add password hashing
3. Implement registration endpoint
4. Implement login endpoint
5. Add authentication middleware
6. Protect todo endpoints
7. Update tests

Executing...

✅ Authentication system added
✅ All endpoints now require authentication
✅ Tests updated (18 tests, all passing)

New endpoints:
- POST /auth/register
- POST /auth/login
- GET /auth/me

Try it:
1. Register: POST /auth/register
   {"email": "user@example.com", "password": "secret"}
   
2. Login: POST /auth/login
   {"email": "user@example.com", "password": "secret"}
   Returns: {"access_token": "..."}
   
3. Use token in headers:
   Authorization: Bearer <token>
```

## Essential Features

### Code Generation

```
You: Create a function to validate email addresses

CodeGenie: [Creates function with regex validation]

You: Add support for international domains

CodeGenie: [Updates function to support IDN]
```

### Code Review

```
You: Review the authentication code for security issues

CodeGenie: Analyzing security...

🔍 Security Analysis:
✅ Passwords are hashed with bcrypt
✅ JWT tokens have expiration
⚠️ Consider adding rate limiting to login endpoint
⚠️ JWT secret should be in environment variable

Shall I implement these improvements?
```

### Debugging

```
You: Why is the login endpoint returning 500 errors?

CodeGenie: Let me analyze the error...

Found the issue in src/api/auth.py:45
The database session is not being committed.

Fix:
db.commit()  # Add this line

Shall I apply this fix?
```

### Refactoring

```
You: Refactor the user service to use dependency injection

CodeGenie: I'll refactor to use dependency injection.

Changes:
- Updated UserService to accept dependencies in constructor
- Modified endpoints to use Depends()
- Updated tests to use dependency overrides

Preview:
[Shows diff of changes]

Apply? (y/n):
```

### Testing

```
You: Create tests for the todo endpoints

CodeGenie: Creating comprehensive tests...

✅ Created: tests/test_todos.py

Tests created:
- test_create_todo
- test_get_todo
- test_list_todos
- test_update_todo
- test_delete_todo
- test_create_todo_unauthorized
- test_update_todo_not_owner
- test_delete_todo_not_owner

Running tests...
✅ All 8 tests passed
```

### Documentation

```
You: Generate API documentation

CodeGenie: Generating documentation...

✅ Created: docs/API.md
✅ Updated: README.md
✅ Created: docs/AUTHENTICATION.md

Documentation includes:
- API endpoint reference
- Authentication guide
- Request/response examples
- Error codes
- Getting started guide
```

## Next Steps

### Learn More

1. **Read the User Guide**
   ```bash
   cat docs/USER_GUIDE.md
   ```
   Comprehensive guide to all features

2. **Try Tutorials**
   ```bash
   cat docs/TUTORIALS.md
   ```
   Step-by-step tutorials for common tasks

3. **Explore Examples**
   ```bash
   ls examples/
   ```
   Example projects to learn from

### Advanced Features

- **Autonomous Mode**: Let CodeGenie work independently
  ```
  You: /autonomous on
  You: Build a complete blog system with comments and likes
  ```

- **Multi-Agent System**: Use specialized agents
  ```
  You: @architect Design the system
  You: @security Review security
  You: @performance Optimize queries
  ```

- **Natural Language Programming**: Describe features in plain English
  ```
  You: I need a feature where users can create wishlists, 
       add products, and get notified when prices drop
  ```

### Configuration

Customize CodeGenie to match your preferences:

```bash
# Create config file
mkdir -p ~/.config/codegenie
cat > ~/.config/codegenie/config.yaml << EOF
models:
  default: "llama3.1:8b"
  code_generation: "codellama:7b"

coding_style:
  language: "python"
  style_guide: "pep8"
  type_hints: true
  docstring_style: "google"

autonomous:
  enabled: true
  auto_approve_safe: true
EOF
```

### Join the Community

- **Discord**: https://discord.gg/codegenie
- **Forum**: https://community.codegenie.dev
- **GitHub**: https://github.com/your-org/codegenie

### Get Help

- **In-app help**: Type `help` in CodeGenie
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **FAQ**: `docs/FAQ.md`
- **API Reference**: `docs/API_REFERENCE.md`

## Tips for Success

### 1. Be Specific

❌ "Make it better"
✅ "Add input validation to the user registration endpoint"

### 2. Provide Context

❌ "Create an API"
✅ "Create a REST API for a blog with authentication, posts, and comments using FastAPI and PostgreSQL"

### 3. Review Changes

Always review generated code before applying:
- Check for security issues
- Verify it matches your requirements
- Ensure it follows your coding standards

### 4. Iterate

Work in small steps:
1. Create basic structure
2. Add core functionality
3. Add validation
4. Add tests
5. Add documentation

### 5. Use the Right Tools

- Use `@architect` for design decisions
- Use `@security` for security reviews
- Use `@performance` for optimization
- Use `/autonomous` for complex features

## Common Tasks

### Create a New Endpoint

```
You: Create a GET endpoint at /api/users/{id} that returns user details
```

### Add Validation

```
You: Add validation to ensure email is unique and password is at least 8 characters
```

### Fix a Bug

```
You: Fix the bug where users can delete other users' posts
```

### Optimize Performance

```
You: Optimize the database queries in the post listing endpoint
```

### Add Tests

```
You: Create unit tests for the authentication service
```

### Generate Documentation

```
You: Generate API documentation for all endpoints
```

## Troubleshooting

### CodeGenie is slow

- Use smaller models: `codegenie --model llama3.1:8b`
- Enable caching in config
- Close other applications

### Model not found

```bash
ollama pull llama3.1:8b
```

### Permission errors

```bash
# Fix file permissions
chmod -R 755 ~/.config/codegenie
```

### Connection errors

```bash
# Start Ollama service
ollama serve
```

For more help, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## What's Next?

You're now ready to use CodeGenie! Here are some suggestions:

1. **Build something**: Start with a simple project
2. **Explore features**: Try autonomous mode and specialized agents
3. **Read tutorials**: Learn advanced techniques
4. **Join community**: Share your experience and learn from others

Happy coding with CodeGenie! 🧞‍♂️

