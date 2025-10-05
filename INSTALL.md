# Installation Guide for Claude Code Agent

## Prerequisites

### 1. Python 3.9 or Higher
Make sure you have Python 3.9 or higher installed:

```bash
python --version
# or
python3 --version
```

### 2. Ollama Installation
Claude Code Agent requires Ollama to be installed and running. Follow these steps:

#### Install Ollama
Visit [https://ollama.ai/](https://ollama.ai/) and download Ollama for your operating system.

#### Start Ollama Service
```bash
ollama serve
```

#### Install Recommended Models
```bash
# Install a general-purpose model (recommended)
ollama pull llama3.1:8b

# Install a code-specific model (recommended)
ollama pull codellama:7b

# Install a larger model for complex reasoning (optional)
ollama pull llama3.1:70b
```

## Installation Methods

### Method 1: Development Installation (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/claude-code.git
cd claude-code
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode:**
```bash
pip install -e .
```

### Method 2: Direct Installation

```bash
pip install claude-code
```

### Method 3: From Source

```bash
git clone https://github.com/your-org/claude-code.git
cd claude-code
pip install -r requirements.txt
pip install -e .
```

## Verification

### 1. Check Ollama is Running
```bash
ollama list
```
You should see your installed models listed.

### 2. Test Claude Code Agent
```bash
claude-code --version
```

### 3. Initialize in a Project
```bash
cd /path/to/your/project
claude-code init
```

### 4. Start the Agent
```bash
claude-code
```

## Configuration

### Global Configuration
The agent will create a global configuration file at `~/.config/claude-code/config.yaml` on first run.

### Project Configuration
You can create a project-specific configuration file `.claude-code.yaml` in your project root:

```yaml
# .claude-code.yaml
project:
  type: "python"
  framework: "fastapi"
  language: "python"

models:
  default: "llama3.1:8b"
  code_generation: "codellama:7b"

ui:
  theme: "dark"
  show_reasoning: true

execution:
  sandbox_mode: true
  auto_backup: true
```

## Troubleshooting

### Common Issues

#### 1. "Ollama service is not running"
**Solution:** Start Ollama service:
```bash
ollama serve
```

#### 2. "No models found"
**Solution:** Install at least one model:
```bash
ollama pull llama3.1:8b
```

#### 3. "Permission denied" errors
**Solution:** Make sure you have write permissions to the project directory and cache directory.

#### 4. Import errors
**Solution:** Make sure you're in the correct virtual environment and all dependencies are installed:
```bash
pip install -r requirements.txt
```

#### 5. Model download fails
**Solution:** Check your internet connection and try again:
```bash
ollama pull llama3.1:8b
```

### Performance Issues

#### 1. Slow responses
- Use smaller models for simple tasks
- Ensure you have enough RAM (8GB+ recommended)
- Close other resource-intensive applications

#### 2. High memory usage
- Use models with fewer parameters
- Restart the agent periodically
- Clear cache: `rm -rf ~/.cache/claude-code`

### Getting Help

1. **Check the logs:** The agent logs important information to help debug issues
2. **Run with debug mode:** `claude-code --debug`
3. **Check Ollama status:** `ollama list` and `ollama ps`
4. **Report issues:** Create an issue on GitHub with:
   - Your operating system
   - Python version
   - Ollama version
   - Error messages
   - Steps to reproduce

## Next Steps

1. **Read the README:** Check out the main README.md for usage examples
2. **Try examples:** Start with simple tasks like "Create a hello world function"
3. **Explore features:** Use `/help` in the agent to see available commands
4. **Customize:** Modify the configuration to suit your needs

## Uninstallation

To uninstall Claude Code Agent:

```bash
pip uninstall claude-code
```

To remove all data:
```bash
rm -rf ~/.config/claude-code
rm -rf ~/.cache/claude-code
```

Note: This will not remove your Ollama models. To remove those:
```bash
ollama rm llama3.1:8b
ollama rm codellama:7b
# etc.
```
