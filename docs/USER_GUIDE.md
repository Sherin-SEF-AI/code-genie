# CodeGenie User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Multi-Agent System](#multi-agent-system)
5. [Autonomous Workflows](#autonomous-workflows)
6. [Natural Language Programming](#natural-language-programming)
7. [Configuration](#configuration)
8. [Best Practices](#best-practices)

## Getting Started

### First Steps

After installation, start CodeGenie in your project directory:

```bash
codegenie
```

Or specify a project path:

```bash
codegenie /path/to/your/project
```

### Your First Task

Try a simple task to get familiar with CodeGenie:

```
You: Create a Python function to calculate fibonacci numbers

CodeGenie: I'll create a fibonacci function for you. Let me analyze your project structure first...

✅ Created: src/utils/math_utils.py
✅ Added: fibonacci function with memoization
✅ Generated: Unit tests in tests/test_math_utils.py

Would you like me to run the tests?
```

## Basic Usage

### Simple Commands

**Code Generation:**
```
You: Create a REST API endpoint for user registration
You: Add error handling to the login function
You: Write a function to validate email addresses
```

**Code Analysis:**
```
You: Analyze the performance of this function
You: Find security vulnerabilities in the authentication module
You: Suggest improvements for the database queries
```

**Debugging:**
```
You: Fix the error in test_user.py
You: Debug why the API is returning 500 errors
You: Explain what's wrong with this code
```

### Interactive Refinement

CodeGenie supports iterative refinement:

```
You: Create a user dashboard component

CodeGenie: I'll create a user dashboard. Should it include:
1. User profile information
2. Activity timeline
3. Statistics widgets
4. Settings panel

You: Include 1, 2, and 3

CodeGenie: Creating dashboard with profile, timeline, and statistics...
```

## Advanced Features

### Code Intelligence

CodeGenie understands your codebase deeply:

**Semantic Analysis:**
```
You: Show me all functions that interact with the database

CodeGenie: Found 12 functions with database interactions:
- UserRepository.create_user() in src/repositories/user.py
- UserRepository.get_user() in src/repositories/user.py
- OrderService.create_order() in src/services/order.py
...

Would you like me to analyze their performance?
```

**Impact Analysis:**
```
You: What will break if I change the User model?

CodeGenie: Analyzing impact of User model changes...

🔍 Direct Dependencies (5):
- UserRepository (src/repositories/user.py)
- AuthService (src/services/auth.py)
- UserController (src/controllers/user.py)

⚠️ Indirect Dependencies (12):
- OrderService depends on UserRepository
- NotificationService depends on UserRepository
...

💡 Recommendation: Create a migration script and update tests
```

### Learning and Adaptation

CodeGenie learns from your coding style:

```
You: Create a new service class

CodeGenie: I notice you prefer:
- Type hints for all parameters
- Docstrings in Google style
- Dependency injection via constructor
- Async methods for I/O operations

I'll follow these patterns for the new service.
```

### Context Awareness

CodeGenie maintains context across sessions:

```
You: Continue working on the authentication system

CodeGenie: Resuming authentication system work...

📋 Previous Session Summary:
- Created User model with password hashing
- Implemented JWT token generation
- Added login endpoint

🎯 Suggested Next Steps:
1. Add token refresh mechanism
2. Implement password reset flow
3. Add rate limiting to login endpoint

Which would you like to tackle first?
```

## Multi-Agent System

### Specialized Agents

CodeGenie uses specialized agents for different tasks:

**Architect Agent:**
```
You: Design a microservices architecture for this application

Architect Agent: Analyzing requirements and designing architecture...

🏗️ Proposed Architecture:
1. API Gateway (Kong/Nginx)
2. User Service (Authentication & Profiles)
3. Order Service (Order Management)
4. Payment Service (Payment Processing)
5. Notification Service (Email/SMS)

📊 Communication: Event-driven with RabbitMQ
💾 Data: PostgreSQL per service
🔒 Security: OAuth2 + JWT

Would you like me to create the service scaffolding?
```

**Security Agent:**
```
You: Check this code for security issues

Security Agent: Scanning for vulnerabilities...

🔴 Critical Issues (2):
1. SQL Injection risk in user_query() - Line 45
   Fix: Use parameterized queries
   
2. Hardcoded API key in config.py - Line 12
   Fix: Move to environment variables

🟡 Warnings (3):
1. Weak password hashing (MD5) - Use bcrypt
2. Missing CSRF protection on forms
3. Sensitive data in logs

Would you like me to fix these automatically?
```

**Performance Agent:**
```
You: Optimize the database queries in this module

Performance Agent: Analyzing performance...

⚡ Bottlenecks Found:
1. N+1 query problem in get_users_with_orders()
   Current: 1 + N queries
   Optimized: 1 query with JOIN
   Expected improvement: 95% faster

2. Missing index on user_id column
   Expected improvement: 80% faster lookups

3. Inefficient pagination (OFFSET)
   Recommendation: Use cursor-based pagination

Shall I implement these optimizations?
```

### Agent Coordination

Multiple agents work together on complex tasks:

```
You: Build a complete user authentication system

CodeGenie: This requires multiple agents. Coordinating...

👥 Agent Assignment:
- Architect: Design authentication flow
- Developer: Implement core logic
- Security: Add security measures
- Tester: Create test suite
- Documentation: Generate docs

🔄 Execution Plan:
1. Architect designs system [2 min]
2. Developer implements [10 min]
3. Security hardens [5 min]
4. Tester validates [5 min]
5. Documentation generates [3 min]

Starting autonomous execution...
```

## Autonomous Workflows

### Autonomous Mode

Enable autonomous execution for complex tasks:

```
You: /autonomous on

You: Create a complete REST API with authentication, CRUD operations, and tests

CodeGenie: Entering autonomous mode...

📋 Execution Plan (15 steps):
1. Analyze project structure
2. Design API architecture
3. Create database models
4. Implement authentication
5. Create CRUD endpoints
6. Add input validation
7. Implement error handling
8. Add logging and monitoring
9. Create unit tests
10. Create integration tests
11. Generate API documentation
12. Add rate limiting
13. Implement caching
14. Security hardening
15. Final validation

⏱️ Estimated time: 25 minutes

Starting execution... (Press Ctrl+C to intervene)
```

### Progress Monitoring

Track autonomous execution in real-time:

```
🔄 Step 3/15: Creating database models
├─ ✅ User model created
├─ ✅ Post model created
├─ ⏳ Comment model in progress...
└─ ⏸️ Waiting: Tag model

💡 Decision: Using SQLAlchemy ORM based on existing patterns
⚠️ Note: Added cascade delete for user relationships

[Intervention Point] Continue? (y/n/modify):
```

### Rollback and Recovery

If something goes wrong:

```
❌ Error in Step 8: Database migration failed

🔄 Rollback Options:
1. Rollback to Step 7 (before migration)
2. Rollback to Step 5 (before database changes)
3. Rollback completely (start over)
4. Fix manually and continue

Your choice: 1

✅ Rolled back to Step 7
💾 All changes preserved in backup/

Would you like me to retry Step 8 with a different approach?
```

## Natural Language Programming

### Describe What You Want

Use natural language to describe features:

```
You: I need a system where users can create posts, other users can comment on posts, and users can like both posts and comments. Posts should support markdown formatting and image uploads. Add moderation features for admins.

CodeGenie: Let me clarify the requirements...

📝 Understanding:
- Users create posts (markdown + images)
- Users comment on posts
- Users like posts and comments
- Admin moderation features

❓ Clarifications needed:
1. Should comments support nested replies?
2. Should there be a limit on image uploads?
3. What moderation actions? (delete, hide, ban user)
4. Should users be notified of likes/comments?

Please answer these questions...
```

### Iterative Refinement

Refine the implementation through conversation:

```
You: The post creation is too slow

CodeGenie: Analyzing post creation performance...

Found: Image upload is blocking (takes 2-5 seconds)

💡 Solutions:
1. Async image processing (recommended)
2. Client-side image compression
3. CDN integration for uploads

Implementing async image processing...

✅ Post creation now returns immediately
✅ Images processed in background
✅ User notified when processing complete

Performance improvement: 95% faster
```

### Explain and Learn

Ask CodeGenie to explain its decisions:

```
You: Why did you use Redis for caching instead of Memcached?

CodeGenie: I chose Redis over Memcached because:

1. **Data Structures**: Your code uses lists and sets, which Redis supports natively
2. **Persistence**: Redis can persist cache to disk, useful for your session data
3. **Pub/Sub**: You have real-time notifications, Redis pub/sub is perfect for this
4. **Existing Stack**: Your project already uses Redis for task queues

Trade-offs:
- Redis uses slightly more memory
- Memcached might be faster for simple key-value

Would you like me to switch to Memcached if you prefer?
```

## Configuration

### User Preferences

Configure CodeGenie to match your style:

```yaml
# ~/.config/codegenie/config.yaml

# Model preferences
models:
  default: "llama3.1:8b"
  code_generation: "codellama:7b"
  reasoning: "llama3.1:70b"
  
# Coding style
coding_style:
  language: "python"
  style_guide: "pep8"
  type_hints: true
  docstring_style: "google"
  max_line_length: 88
  
# Autonomous mode
autonomous:
  enabled: true
  auto_approve_safe: true
  intervention_points: true
  max_steps: 50
  
# Learning
learning:
  adapt_to_style: true
  remember_preferences: true
  learn_from_corrections: true
```

### Project Configuration

Project-specific settings:

```yaml
# .codegenie.yaml

project:
  name: "MyApp"
  type: "web_api"
  framework: "fastapi"
  
# Agent preferences
agents:
  architect:
    style: "microservices"
  security:
    level: "strict"
  performance:
    target: "high"
    
# Testing
testing:
  framework: "pytest"
  coverage_threshold: 80
  auto_generate: true
```

## Best Practices

### Effective Prompts

**Good Prompts:**
```
✅ "Create a user registration endpoint with email validation and password hashing"
✅ "Refactor the authentication module to use dependency injection"
✅ "Add comprehensive error handling to the payment processing service"
```

**Less Effective Prompts:**
```
❌ "Make it better"
❌ "Fix the code"
❌ "Add some tests"
```

### Iterative Development

Work in small, testable increments:

```
1. You: Create the User model
2. CodeGenie: [Creates model]
3. You: Add validation to the User model
4. CodeGenie: [Adds validation]
5. You: Create tests for the User model
6. CodeGenie: [Creates tests]
7. You: Now create the UserRepository
```

### Review and Feedback

Always review generated code:

```
You: Create a password hashing function

CodeGenie: [Creates function using bcrypt]

You: Use argon2 instead of bcrypt

CodeGenie: Good catch! Argon2 is more secure. Updating...
[Updates to use argon2]

💡 Learning: You prefer argon2 for password hashing
```

### Use Context

Provide context for better results:

```
You: This is a high-traffic API that handles 10,000 requests per second. Create a caching layer.

CodeGenie: Given the high traffic, I'll implement:
- Redis cluster for distributed caching
- Cache warming on startup
- Intelligent cache invalidation
- Circuit breaker for cache failures
- Monitoring and metrics
```

### Leverage Agents

Use the right agent for the task:

```
You: @architect Design the system architecture
You: @security Review this authentication code
You: @performance Optimize these database queries
You: @documentation Generate API docs
```

## Tips and Tricks

### Keyboard Shortcuts

- `Ctrl+C`: Interrupt autonomous execution
- `Ctrl+D`: Exit CodeGenie
- `/help`: Show available commands
- `/clear`: Clear conversation history
- `/undo`: Undo last operation

### Commands

```
/autonomous on|off    - Toggle autonomous mode
/agents list          - Show available agents
/context show         - Display current context
/history              - Show conversation history
/rollback [step]      - Rollback to previous state
/explain [topic]      - Explain a concept or decision
/learn [preference]   - Teach CodeGenie a preference
```

### Debugging

Enable debug mode for troubleshooting:

```bash
codegenie --debug
```

View logs:

```bash
tail -f ~/.codegenie/logs/codegenie.log
```

## Getting Help

- Use `/help` command in CodeGenie
- Check the [API Documentation](API_REFERENCE.md)
- Visit [Troubleshooting Guide](TROUBLESHOOTING.md)
- Join our [Community Forum](https://community.codegenie.dev)

## Next Steps

- Explore [Advanced Tutorials](TUTORIALS.md)
- Watch [Video Tutorials](VIDEO_TUTORIALS.md)
- Read [API Reference](API_REFERENCE.md)
- Learn about [ToolExecutor](TOOL_EXECUTOR_GUIDE.md)
- Master [Terminal Interface](TERMINAL_INTERFACE_GUIDE.md)
- Check out [Example Projects](../examples/)
- Join the [Community](https://community.codegenie.dev)
