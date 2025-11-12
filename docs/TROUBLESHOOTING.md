# CodeGenie Troubleshooting Guide

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [Performance Problems](#performance-problems)
4. [Agent Issues](#agent-issues)
5. [Integration Problems](#integration-problems)
6. [Common Error Messages](#common-error-messages)

## Installation Issues

### Ollama Not Found

**Symptom:**
```
Error: Ollama service not found or not running
```

**Solutions:**

1. **Check if Ollama is installed:**
```bash
ollama --version
```

2. **Install Ollama if missing:**
- Visit https://ollama.ai/
- Download and install for your OS

3. **Start Ollama service:**
```bash
ollama serve
```

4. **Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

### No Models Available

**Symptom:**
```
Error: No models found. Please install at least one model.
```

**Solutions:**

1. **List installed models:**
```bash
ollama list
```

2. **Install recommended models:**
```bash
ollama pull llama3.1:8b
ollama pull codellama:7b
```

3. **Verify model installation:**
```bash
ollama list
```

### Python Version Incompatibility

**Symptom:**
```
Error: Python 3.9 or higher required
```

**Solutions:**

1. **Check Python version:**
```bash
python --version
```

2. **Install Python 3.9+:**
- Ubuntu/Debian: `sudo apt install python3.9`
- macOS: `brew install python@3.9`
- Windows: Download from python.org

3. **Use virtual environment with correct version:**
```bash
python3.9 -m venv venv
source venv/bin/activate
```

### Dependency Installation Failures

**Symptom:**
```
Error: Failed to install dependencies
```

**Solutions:**

1. **Update pip:**
```bash
pip install --upgrade pip
```

2. **Install with verbose output:**
```bash
pip install -e . -v
```

3. **Install system dependencies (Ubuntu/Debian):**
```bash
sudo apt install python3-dev build-essential
```

4. **Install system dependencies (macOS):**
```bash
brew install python@3.9
xcode-select --install
```

## Runtime Errors

### Model Loading Failures

**Symptom:**
```
Error: Failed to load model 'llama3.1:8b'
```

**Solutions:**

1. **Verify model exists:**
```bash
ollama list
```

2. **Re-pull the model:**
```bash
ollama pull llama3.1:8b
```

3. **Check Ollama logs:**
```bash
journalctl -u ollama -f  # Linux
~/Library/Logs/Ollama/server.log  # macOS
```

4. **Try a different model:**
```bash
codegenie --model codellama:7b
```

### Memory Errors

**Symptom:**
```
Error: Out of memory
MemoryError: Unable to allocate array
```

**Solutions:**

1. **Use smaller models:**
```bash
codegenie --model llama3.1:8b  # Instead of 70b
```

2. **Close other applications:**
- Free up RAM by closing unnecessary programs

3. **Increase swap space (Linux):**
```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

4. **Configure model parameters:**
```yaml
# ~/.config/codegenie/config.yaml
models:
  default: "llama3.1:8b"
  context_length: 2048  # Reduce from default 4096
```

### Permission Errors

**Symptom:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

1. **Check file permissions:**
```bash
ls -la /path/to/project
```

2. **Fix ownership:**
```bash
sudo chown -R $USER:$USER /path/to/project
```

3. **Run with appropriate permissions:**
```bash
# Don't use sudo unless necessary
codegenie
```

4. **Check config directory permissions:**
```bash
chmod 755 ~/.config/codegenie
chmod 644 ~/.config/codegenie/config.yaml
```

### Connection Errors

**Symptom:**
```
ConnectionError: Failed to connect to Ollama service
```

**Solutions:**

1. **Check Ollama is running:**
```bash
ps aux | grep ollama
```

2. **Verify port is accessible:**
```bash
curl http://localhost:11434/api/tags
```

3. **Check firewall settings:**
```bash
# Linux
sudo ufw status
sudo ufw allow 11434

# macOS
# System Preferences > Security & Privacy > Firewall
```

4. **Configure custom Ollama URL:**
```yaml
# ~/.config/codegenie/config.yaml
ollama:
  url: "http://localhost:11434"
```

## Performance Problems

### Slow Response Times

**Symptom:**
- Responses take more than 30 seconds
- Agent appears frozen

**Solutions:**

1. **Use faster models:**
```bash
codegenie --model llama3.1:8b  # Faster than 70b
```

2. **Enable caching:**
```yaml
# ~/.config/codegenie/config.yaml
cache:
  enabled: true
  ttl: 3600
```

3. **Reduce context length:**
```yaml
models:
  context_length: 2048
```

4. **Check system resources:**
```bash
top  # or htop
```

5. **Close resource-intensive applications**

### High Memory Usage

**Symptom:**
- System becomes slow
- Swap usage increases significantly

**Solutions:**

1. **Monitor memory usage:**
```bash
codegenie --debug
# Check logs for memory usage
```

2. **Use smaller models:**
```yaml
models:
  default: "llama3.1:8b"
  code_generation: "codellama:7b"
```

3. **Limit concurrent operations:**
```yaml
execution:
  max_concurrent_tasks: 2
```

4. **Clear cache periodically:**
```bash
rm -rf ~/.cache/codegenie
```

### High CPU Usage

**Symptom:**
- CPU at 100% constantly
- System becomes unresponsive

**Solutions:**

1. **Limit CPU threads:**
```yaml
# ~/.config/codegenie/config.yaml
performance:
  max_threads: 4
```

2. **Use GPU acceleration (if available):**
```bash
# Ensure Ollama uses GPU
ollama run llama3.1:8b --gpu
```

3. **Reduce parallel processing:**
```yaml
execution:
  parallel_execution: false
```

## Agent Issues

### Agent Not Responding

**Symptom:**
- Agent doesn't respond to commands
- Stuck on "Thinking..."

**Solutions:**

1. **Check agent status:**
```bash
codegenie --status
```

2. **Restart agent:**
```bash
# Press Ctrl+C to stop
codegenie
```

3. **Clear session state:**
```bash
rm -rf ~/.codegenie/sessions/current
```

4. **Check logs:**
```bash
tail -f ~/.codegenie/logs/codegenie.log
```

### Incorrect Code Generation

**Symptom:**
- Generated code doesn't work
- Code doesn't match requirements

**Solutions:**

1. **Provide more context:**
```
You: Create a user registration endpoint with email validation, 
password hashing using bcrypt, and PostgreSQL database storage
```

2. **Review and correct:**
```
You: The password hashing is incorrect. Use bcrypt with salt rounds of 12
```

3. **Use specialized agents:**
```
You: @developer Create the endpoint
You: @security Review the security
```

4. **Enable learning mode:**
```yaml
learning:
  learn_from_corrections: true
```

### Agent Conflicts

**Symptom:**
```
Warning: Conflicting recommendations from agents
```

**Solutions:**

1. **Review conflict details:**
```
You: Explain the conflict
```

2. **Choose preferred approach:**
```
You: Use the Security Agent's recommendation
```

3. **Configure agent priorities:**
```yaml
agents:
  priority_order:
    - security
    - performance
    - developer
```

### Autonomous Mode Issues

**Symptom:**
- Autonomous execution fails
- Unexpected behavior in autonomous mode

**Solutions:**

1. **Enable intervention points:**
```yaml
autonomous:
  intervention_points: true
```

2. **Reduce autonomous scope:**
```yaml
autonomous:
  max_steps: 10  # Limit number of steps
```

3. **Review execution plan first:**
```
You: Show me the execution plan before starting
```

4. **Use manual mode for complex tasks:**
```
You: /autonomous off
```

## Integration Problems

### IDE Integration Not Working

**Symptom:**
- VS Code extension not responding
- IntelliJ plugin errors

**Solutions:**

1. **Verify extension installation:**
- VS Code: Check Extensions panel
- IntelliJ: Check Plugins settings

2. **Check CodeGenie service:**
```bash
codegenie --service status
```

3. **Restart IDE:**
- Close and reopen your IDE

4. **Check extension logs:**
- VS Code: Developer Tools > Console
- IntelliJ: Help > Show Log

5. **Reinstall extension:**
```bash
# VS Code
code --uninstall-extension codegenie.vscode
code --install-extension codegenie.vscode
```

### Git Integration Issues

**Symptom:**
- Can't commit changes
- Git operations fail

**Solutions:**

1. **Verify Git installation:**
```bash
git --version
```

2. **Check Git configuration:**
```bash
git config --list
```

3. **Configure Git credentials:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

4. **Check repository status:**
```bash
git status
```

### CI/CD Integration Failures

**Symptom:**
- GitHub Actions failing
- Jenkins builds not triggered

**Solutions:**

1. **Verify webhook configuration:**
```bash
curl -X GET https://api.github.com/repos/owner/repo/hooks \
  -H "Authorization: token YOUR_TOKEN"
```

2. **Check API credentials:**
```yaml
integrations:
  github:
    token: "your_token"
    webhook_secret: "your_secret"
```

3. **Review CI/CD logs:**
- GitHub: Actions tab
- Jenkins: Build console output

4. **Test webhook manually:**
```bash
curl -X POST https://your-codegenie-instance/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "push", "repository": "owner/repo"}'
```

## Common Error Messages

### "Context length exceeded"

**Cause:** Too much context for the model to handle

**Solution:**
```yaml
models:
  context_length: 2048  # Reduce context
  
context:
  max_history: 10  # Limit conversation history
```

### "Rate limit exceeded"

**Cause:** Too many requests to Ollama

**Solution:**
```yaml
rate_limiting:
  enabled: true
  requests_per_minute: 30
```

### "Model not found"

**Cause:** Specified model not installed

**Solution:**
```bash
ollama pull llama3.1:8b
# Or specify different model
codegenie --model codellama:7b
```

### "Invalid configuration"

**Cause:** Syntax error in config file

**Solution:**
```bash
# Validate config
codegenie --validate-config

# Reset to defaults
mv ~/.config/codegenie/config.yaml ~/.config/codegenie/config.yaml.bak
codegenie  # Will create new default config
```

### "Checkpoint not found"

**Cause:** Trying to rollback to non-existent checkpoint

**Solution:**
```bash
# List available checkpoints
codegenie --list-checkpoints

# Rollback to specific checkpoint
codegenie --rollback checkpoint_id
```

### "Agent timeout"

**Cause:** Agent took too long to respond

**Solution:**
```yaml
agents:
  timeout: 300  # Increase timeout to 5 minutes
```

## Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
codegenie --debug
```

Debug output includes:
- Model requests and responses
- Agent communication
- File operations
- Performance metrics
- Error stack traces

## Log Files

Check log files for detailed error information:

```bash
# Main log
tail -f ~/.codegenie/logs/codegenie.log

# Agent logs
tail -f ~/.codegenie/logs/agents.log

# Performance logs
tail -f ~/.codegenie/logs/performance.log

# Error logs
tail -f ~/.codegenie/logs/errors.log
```

## Getting Help

If you can't resolve the issue:

1. **Check documentation:**
   - User Guide: docs/USER_GUIDE.md
   - API Reference: docs/API_REFERENCE.md

2. **Search existing issues:**
   - GitHub Issues: https://github.com/your-org/codegenie/issues

3. **Create a bug report:**
   - Include error messages
   - Attach relevant logs
   - Describe steps to reproduce

4. **Join community:**
   - Discord: https://discord.gg/codegenie
   - Forum: https://community.codegenie.dev

5. **Contact support:**
   - Email: support@codegenie.dev
   - Include debug logs and system info

## System Information

When reporting issues, include:

```bash
# Generate system info
codegenie --system-info

# Output includes:
# - OS and version
# - Python version
# - CodeGenie version
# - Ollama version
# - Installed models
# - Configuration summary
```

## Emergency Recovery

If CodeGenie is completely broken:

```bash
# 1. Stop all processes
pkill -f codegenie

# 2. Backup current state
cp -r ~/.codegenie ~/.codegenie.backup

# 3. Reset to defaults
rm -rf ~/.codegenie
rm -rf ~/.cache/codegenie

# 4. Reinstall
pip uninstall codegenie
pip install codegenie

# 5. Restart
codegenie
```

## Performance Tuning

Optimize CodeGenie performance:

```yaml
# ~/.config/codegenie/config.yaml

# Use faster models for simple tasks
models:
  default: "llama3.1:8b"
  simple_tasks: "codellama:7b"
  
# Enable aggressive caching
cache:
  enabled: true
  aggressive: true
  ttl: 7200
  
# Optimize execution
execution:
  parallel_execution: true
  max_concurrent_tasks: 4
  
# Reduce context
context:
  max_history: 10
  max_file_size: "1MB"
  
# Performance monitoring
monitoring:
  enabled: true
  metrics_interval: 60
```
