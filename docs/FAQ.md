# CodeGenie Frequently Asked Questions (FAQ)

## General Questions

### What is CodeGenie?

CodeGenie is an advanced AI coding agent that helps developers build software faster and better. It uses local AI models (via Ollama) to provide intelligent code generation, autonomous development workflows, multi-agent collaboration, and comprehensive code intelligence—all while maintaining complete privacy.

### How is CodeGenie different from other AI coding assistants?

CodeGenie stands out with:
- **Complete Privacy**: Runs locally with Ollama, no data sent to cloud
- **Autonomous Workflows**: Can complete complex multi-step tasks independently
- **Multi-Agent System**: Specialized agents for architecture, security, performance, etc.
- **Advanced Code Intelligence**: Deep understanding of your codebase
- **Learning System**: Adapts to your coding style and preferences
- **Open Source**: Free and customizable

### Do I need an internet connection?

No! CodeGenie runs completely offline once you have:
- Ollama installed
- AI models downloaded
- CodeGenie installed

You only need internet to initially download models and install CodeGenie.

### Is my code sent to any external servers?

No. All processing happens locally on your machine. Your code never leaves your computer.

## Installation and Setup

### What are the system requirements?

**Minimum:**
- Python 3.9+
- 8GB RAM
- 10GB free disk space
- Ollama installed

**Recommended:**
- Python 3.10+
- 16GB+ RAM
- 50GB free disk space (for multiple models)
- GPU with 8GB+ VRAM (optional, for faster inference)

### Which AI models should I use?

**For most users:**
- `llama3.1:8b` - General purpose, good balance
- `codellama:7b` - Code-specific tasks

**For better performance (requires more RAM):**
- `llama3.1:70b` - Complex reasoning
- `deepseek-coder:33b` - Advanced code generation

**For limited resources:**
- `llama3.1:7b` - Smaller, faster
- `codellama:7b` - Code-specific, efficient

### How do I update CodeGenie?

```bash
pip install --upgrade codegenie
```

### Can I use CodeGenie with my existing projects?

Yes! CodeGenie works with any project. Just navigate to your project directory and run:

```bash
cd /path/to/your/project
codegenie
```

## Usage Questions

### How do I start CodeGenie?

```bash
# In your project directory
codegenie

# Or specify a path
codegenie /path/to/project

# With specific model
codegenie --model llama3.1:70b
```

### What can I ask CodeGenie to do?

Almost anything related to software development:
- Generate code
- Debug errors
- Refactor code
- Write tests
- Create documentation
- Design architecture
- Review security
- Optimize performance
- Explain code
- And much more!

### How do I use autonomous mode?

```
You: /autonomous on
You: Build a complete REST API with authentication
```

CodeGenie will break down the task and execute it step-by-step with minimal supervision.

### Can I interrupt autonomous execution?

Yes! Press `Ctrl+C` at any time to pause execution. You can then:
- Review what's been done
- Make changes
- Continue execution
- Rollback changes

### How do I use specialized agents?

Prefix your request with the agent name:

```
You: @architect Design the system architecture
You: @security Review this code for vulnerabilities
You: @performance Optimize these database queries
You: @documentation Generate API docs
```

### How do I undo changes?

```
You: /undo
```

Or rollback to a specific checkpoint:

```
You: /rollback checkpoint_id
```

## Features and Capabilities

### Does CodeGenie support my programming language?

CodeGenie supports all major programming languages:
- Python, JavaScript, TypeScript
- Java, C#, C++, C
- Go, Rust, Ruby, PHP
- Swift, Kotlin, Scala
- And many more!

### Can CodeGenie work with my framework?

Yes! CodeGenie understands popular frameworks:
- **Web**: FastAPI, Django, Flask, Express, React, Vue, Angular
- **Mobile**: React Native, Flutter, Swift UI
- **Desktop**: Electron, Qt, Tkinter
- **Data**: Pandas, NumPy, TensorFlow, PyTorch
- And many more!

### Does CodeGenie write tests?

Yes! CodeGenie can:
- Generate unit tests
- Create integration tests
- Write end-to-end tests
- Generate test data
- Create test fixtures
- Run tests and fix failures

### Can CodeGenie help with debugging?

Absolutely! CodeGenie can:
- Analyze error messages
- Find root causes
- Suggest fixes
- Implement fixes
- Verify fixes work
- Explain what went wrong

### Does CodeGenie understand my existing codebase?

Yes! CodeGenie:
- Analyzes your project structure
- Understands your patterns and conventions
- Learns your coding style
- Maintains context across sessions
- Tracks project evolution

### Can CodeGenie help with database design?

Yes! CodeGenie can:
- Design database schemas
- Create migrations
- Optimize queries
- Add indexes
- Design relationships
- Suggest improvements

## Performance and Optimization

### Why is CodeGenie slow?

Common causes:
1. **Large model**: Try a smaller model (8b instead of 70b)
2. **Limited RAM**: Close other applications
3. **No GPU**: CPU inference is slower
4. **Large context**: Reduce context length in config

### How can I make CodeGenie faster?

1. **Use smaller models** for simple tasks
2. **Enable caching** in configuration
3. **Use GPU** if available
4. **Reduce context length**
5. **Close unnecessary applications**

### How much RAM do I need?

- **8GB**: Can run 7b-8b models (basic usage)
- **16GB**: Can run 13b models comfortably
- **32GB+**: Can run 70b models

### Can I use GPU acceleration?

Yes! If you have an NVIDIA GPU:
1. Install CUDA toolkit
2. Ollama will automatically use GPU
3. Much faster inference (5-10x)

### How much disk space do models use?

- 7b models: ~4GB
- 8b models: ~5GB
- 13b models: ~8GB
- 33b models: ~20GB
- 70b models: ~40GB

## Configuration and Customization

### Where is the configuration file?

Global config: `~/.config/codegenie/config.yaml`  
Project config: `.codegenie.yaml` in project root

### How do I change the default model?

Edit `~/.config/codegenie/config.yaml`:

```yaml
models:
  default: "llama3.1:8b"
```

### Can I customize CodeGenie's behavior?

Yes! You can customize:
- Model preferences
- Coding style preferences
- Autonomous mode settings
- Agent behavior
- UI preferences
- And much more!

See the [User Guide](USER_GUIDE.md#configuration) for details.

### How do I teach CodeGenie my coding style?

CodeGenie learns automatically, but you can also:

1. **Provide feedback:**
```
You: Use type hints for all functions
You: Prefer async/await over callbacks
```

2. **Configure preferences:**
```yaml
coding_style:
  type_hints: true
  async_preferred: true
  docstring_style: "google"
```

3. **Correct mistakes:**
```
You: Use argon2 instead of bcrypt for passwords
```

CodeGenie will remember and apply your preferences.

## Troubleshooting

### CodeGenie won't start

1. Check Ollama is running: `ollama list`
2. Check Python version: `python --version` (need 3.9+)
3. Reinstall: `pip uninstall codegenie && pip install codegenie`
4. Check logs: `~/.codegenie/logs/codegenie.log`

### "Model not found" error

```bash
# List installed models
ollama list

# Install missing model
ollama pull llama3.1:8b
```

### "Out of memory" error

1. Use smaller model: `codegenie --model llama3.1:8b`
2. Close other applications
3. Reduce context length in config
4. Restart your computer

### Generated code doesn't work

1. **Provide more context:**
```
You: This is a FastAPI project using PostgreSQL. Create a user endpoint.
```

2. **Review and correct:**
```
You: The validation is incorrect. Email should use regex pattern.
```

3. **Ask for explanation:**
```
You: Explain why you chose this approach
```

### CodeGenie is making wrong decisions

1. **Provide explicit instructions:**
```
You: Use PostgreSQL, not SQLite. Use bcrypt for passwords.
```

2. **Use specialized agents:**
```
You: @security Review this and fix any issues
```

3. **Enable intervention points:**
```yaml
autonomous:
  intervention_points: true
```

## Privacy and Security

### Is my code private?

Yes! CodeGenie:
- Runs completely locally
- Never sends code to external servers
- Stores data only on your machine
- Encrypts sensitive data

### Where is my data stored?

- Configuration: `~/.config/codegenie/`
- Cache: `~/.cache/codegenie/`
- Logs: `~/.codegenie/logs/`
- Session data: `~/.codegenie/sessions/`

### Can I delete my data?

Yes:

```bash
# Delete all CodeGenie data
rm -rf ~/.config/codegenie
rm -rf ~/.cache/codegenie
rm -rf ~/.codegenie
```

### Does CodeGenie collect telemetry?

No. CodeGenie does not collect any usage data or telemetry by default. You can optionally enable anonymous usage statistics to help improve CodeGenie, but this is opt-in.

## Advanced Usage

### Can I create custom agents?

Yes! See the [Advanced Guide](ADVANCED.md#custom-agents) for details.

### Can I integrate CodeGenie with my IDE?

Yes! CodeGenie provides:
- VS Code extension
- IntelliJ plugin
- Vim plugin
- Language Server Protocol support

### Can I use CodeGenie in CI/CD?

Yes! CodeGenie can:
- Review pull requests
- Run automated checks
- Generate reports
- Suggest improvements

See [CI/CD Integration Guide](CICD_INTEGRATION.md).

### Can I use CodeGenie with my team?

Yes! CodeGenie supports:
- Shared knowledge bases
- Team configurations
- Collaborative workflows
- Code review automation

See [Team Collaboration Guide](TEAM_COLLABORATION.md).

### Can I extend CodeGenie with plugins?

Yes! CodeGenie has a plugin system. See [Plugin Development Guide](PLUGIN_DEVELOPMENT.md).

## Licensing and Support

### Is CodeGenie free?

Yes! CodeGenie is open source and free to use under the MIT license.

### Can I use CodeGenie commercially?

Yes! The MIT license allows commercial use.

### How do I get support?

1. **Documentation**: Check docs/ directory
2. **GitHub Issues**: Report bugs or request features
3. **Community Forum**: Ask questions
4. **Discord**: Chat with other users
5. **Email**: support@codegenie.dev

### How can I contribute?

We welcome contributions!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

### Where can I report bugs?

GitHub Issues: https://github.com/your-org/codegenie/issues

Please include:
- Error message
- Steps to reproduce
- System information
- Relevant logs

## Comparison with Other Tools

### CodeGenie vs GitHub Copilot

| Feature | CodeGenie | GitHub Copilot |
|---------|-----------|----------------|
| Privacy | ✅ Local | ❌ Cloud |
| Cost | ✅ Free | ❌ Paid |
| Autonomous Mode | ✅ Yes | ❌ No |
| Multi-Agent | ✅ Yes | ❌ No |
| Code Intelligence | ✅ Advanced | ⚠️ Basic |
| Learning | ✅ Adaptive | ⚠️ Limited |

### CodeGenie vs ChatGPT/Claude

| Feature | CodeGenie | ChatGPT/Claude |
|---------|-----------|----------------|
| Code Execution | ✅ Yes | ❌ No |
| Project Context | ✅ Full | ⚠️ Limited |
| File Operations | ✅ Yes | ❌ No |
| Autonomous Workflows | ✅ Yes | ❌ No |
| Privacy | ✅ Local | ❌ Cloud |
| Specialized Agents | ✅ Yes | ❌ No |

### CodeGenie vs Cursor

| Feature | CodeGenie | Cursor |
|---------|-----------|--------|
| Privacy | ✅ Local | ❌ Cloud |
| Cost | ✅ Free | ❌ Paid |
| Multi-Agent | ✅ Yes | ❌ No |
| Autonomous Mode | ✅ Yes | ⚠️ Limited |
| IDE Integration | ✅ Multiple | ✅ Built-in |

## Tips and Best Practices

### How can I get better results?

1. **Be specific**: Provide clear, detailed requirements
2. **Provide context**: Mention framework, language, constraints
3. **Iterate**: Refine through conversation
4. **Use agents**: Leverage specialized agents
5. **Review**: Always review generated code
6. **Provide feedback**: Help CodeGenie learn

### What makes a good prompt?

**Good:**
```
Create a FastAPI endpoint for user registration with email validation,
password hashing using bcrypt, and PostgreSQL storage. Include input
validation and error handling.
```

**Less effective:**
```
Make a user endpoint
```

### How should I structure my workflow?

1. **Start small**: Begin with simple tasks
2. **Build incrementally**: Add features one at a time
3. **Test frequently**: Verify each change works
4. **Use autonomous mode**: For complex, well-defined tasks
5. **Review regularly**: Check generated code
6. **Provide feedback**: Correct mistakes immediately

### When should I use autonomous mode?

**Good for:**
- Well-defined features
- Repetitive tasks
- Standard implementations
- Complete workflows

**Not ideal for:**
- Exploratory work
- Novel solutions
- Critical systems (without review)
- Learning new concepts

## Still Have Questions?

- Check the [User Guide](USER_GUIDE.md)
- Read the [Tutorials](TUTORIALS.md)
- Visit the [Community Forum](https://community.codegenie.dev)
- Join our [Discord](https://discord.gg/codegenie)
- Email us: support@codegenie.dev
