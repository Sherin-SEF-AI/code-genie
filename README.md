# CodeGenie - Local AI Coding Agent

A powerful local AI coding agent that rivals Claude Code, built with Ollama for complete privacy and offline operation. This agent can autonomously plan, write, debug, and execute code while maintaining natural conversation with users.

## 🚀 Features

### Core Capabilities
- **Intelligent Planning**: Breaks down complex tasks into manageable steps with milestone tracking
- **Multi-Step Reasoning**: Chain-of-thought reasoning with transparent decision processes
- **Automatic Error Recovery**: Self-healing capabilities with intelligent debugging
- **Code Generation**: Context-aware code writing that matches project style
- **Real-time Execution**: Safe terminal integration with automatic command validation

### Advanced Features
- **Project Understanding**: Automatic detection of frameworks, patterns, and architecture
- **Learning System**: Adapts to your coding style and learns from corrections
- **Rich Terminal UI**: Beautiful interface with syntax highlighting and progress tracking
- **Multi-Model Support**: Intelligent model selection based on task complexity
- **Collaboration Ready**: Team support with knowledge sharing and conflict resolution

## 🛠 Installation

### Prerequisites
- Python 3.9 or higher
- [Ollama](https://ollama.ai/) installed and running

### Quick Install
```bash
# Clone the repository
git clone https://github.com/Sherin-SEF-AI/code-genie.git
cd codegenie

# Install dependencies
pip install -e .

# Install recommended Ollama models
ollama pull llama3.1:8b
ollama pull codellama:7b
ollama pull deepseek-coder:6.7b
```

### Development Install
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 🎯 Quick Start

### Basic Usage
```bash
# Start the agent in your project directory
codegenie

# Or specify a project path
codegenie /path/to/your/project
```

### Example Session
```
🧞 CodeGenie v0.1.0
📁 Working in: /home/user/my-project
🧠 Using model: llama3.1:8b

You: Create a REST API with user authentication

🤖 I'll help you create a REST API with user authentication. Let me break this down into steps:

📋 Plan:
1. Analyze project structure and choose framework
2. Set up authentication system (JWT tokens)
3. Create user model and database schema
4. Implement authentication endpoints
5. Add protected routes middleware
6. Create user management endpoints
7. Add input validation and error handling
8. Write tests for all endpoints

Let me start by examining your project structure...

🔍 Analyzing project...
✅ Detected: Python project with FastAPI framework
✅ Found: Existing database configuration
✅ Identified: SQLAlchemy ORM setup

📝 Step 1: Creating user authentication system...
```

## 🏗 Architecture

### Core Components
- **Agent System**: Central reasoning and planning engine
- **Model Manager**: Ollama integration with intelligent model selection
- **Code Analyzer**: Static analysis and project understanding
- **Execution Engine**: Safe terminal and file operations
- **Memory System**: Context and learning persistence
- **UI Layer**: Rich terminal interface with real-time updates

### Model Strategy
- **Small Models** (7B): Simple tasks, code completion, quick fixes
- **Medium Models** (13B): Complex reasoning, architecture decisions
- **Large Models** (70B): Advanced problem solving, code generation
- **Specialized Models**: Code-specific models for different languages

## 📚 Usage Examples

### Web Development
```bash
# Create a React component
claude-code "Create a responsive user dashboard with charts"

# Add authentication
claude-code "Add JWT authentication to the existing API"

# Optimize performance
claude-code "Optimize the database queries and add caching"
```

### Data Science
```bash
# Analyze data
claude-code "Create a machine learning pipeline for customer segmentation"

# Visualize results
claude-code "Generate interactive visualizations for the analysis results"
```

### DevOps
```bash
# Set up CI/CD
claude-code "Create GitHub Actions workflow for automated testing and deployment"

# Infrastructure
claude-code "Set up Docker containers and Kubernetes deployment"
```

## ⚙️ Configuration

### Global Configuration (`~/.config/claude-code/config.yaml`)
```yaml
# Model preferences
models:
  default: "llama3.1:8b"
  code_generation: "codellama:7b"
  reasoning: "llama3.1:70b"
  
# UI preferences
ui:
  theme: "dark"
  show_reasoning: true
  auto_approve_safe: true
  
# Execution settings
execution:
  sandbox_mode: true
  auto_backup: true
  max_file_size: "10MB"
  
# Learning preferences
learning:
  save_corrections: true
  adapt_style: true
  remember_patterns: true
```

### Project Configuration (`.claude-code.yaml`)
```yaml
# Project-specific settings
project:
  type: "web_app"
  framework: "fastapi"
  language: "python"
  
# Custom prompts
prompts:
  code_style: "Follow PEP 8 and use type hints"
  testing: "Write comprehensive tests with pytest"
  
# Ignore patterns
ignore:
  - "node_modules/"
  - "*.pyc"
  - ".git/"
```

## 🔧 Advanced Features

### Custom Models
```bash
# Use a custom fine-tuned model
codegenie --model my-custom-model:latest

# Switch models during conversation
codegenie "Switch to the code generation model for this task"
```

### Team Collaboration
```bash
# Share knowledge with team
codegenie --share-knowledge

# Import team patterns
codegenie --import-patterns team-patterns.json
```

### Integration
```bash
# Git integration
codegenie "Create a commit with descriptive message for recent changes"

# CI/CD integration
codegenie "Update the deployment pipeline for the new features"
```

## 🛡 Safety Features

- **Sandboxed Execution**: All commands run in isolated environments
- **Automatic Backups**: Changes are backed up before execution
- **Rollback Capability**: Easy undo for any operation
- **Dangerous Operation Detection**: Warnings for potentially harmful commands
- **Secret Detection**: Automatic masking of sensitive information

## 📊 Performance

- **Fast Response**: Optimized for sub-second response times
- **Memory Efficient**: Intelligent caching and resource management
- **Parallel Processing**: Multiple operations run concurrently
- **Incremental Analysis**: Only re-analyze changed files

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/Sherin-SEF-AI/code-genie.git
cd codegenie

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black src/ tests/
flake8 src/ tests/
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Created by [Sherin Joseph Roy](https://github.com/Sherin-SEF-AI)**, Co-Founder of [DeepMost AI](https://github.com/Sherin-SEF-AI) and creator of intelligent systems that bridge research and real-world safety
- [Ollama](https://ollama.ai/) for providing the local LLM infrastructure
- [Rich](https://rich.readthedocs.io/) for beautiful terminal interfaces
- [Textual](https://textual.textualize.io/) for advanced terminal UI components
- The open-source community for inspiration and tools

## 📞 Support

- 📖 [Documentation](https://github.com/Sherin-SEF-AI/code-genie)
- 🐛 [Issue Tracker](https://github.com/Sherin-SEF-AI/code-genie/issues)
- 💬 [Discussions](https://github.com/Sherin-SEF-AI/code-genie/discussions)
- 📧 [Email Support](mailto:sherin.joseph2217@gmail.com)

---

**Made with ❤️ for developers who want AI assistance without compromising privacy**
