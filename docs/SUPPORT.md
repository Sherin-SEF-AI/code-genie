# CodeGenie Support

## Getting Help

We're here to help you get the most out of CodeGenie. Here are the various ways you can get support:

## Documentation

Start with our comprehensive documentation:

- **[User Guide](USER_GUIDE.md)** - Complete feature documentation
- **[Tutorials](TUTORIALS.md)** - Step-by-step tutorials
- **[API Reference](API_REFERENCE.md)** - API documentation
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[FAQ](FAQ.md)** - Frequently asked questions
- **[Deployment Guide](DEPLOYMENT.md)** - Deployment instructions

## Community Support

### Discord Server

Join our Discord community for real-time help:
- **Server**: https://discord.gg/codegenie
- **Channels**:
  - `#general` - General discussion
  - `#help` - Get help from community
  - `#showcase` - Share your projects
  - `#feature-requests` - Suggest new features
  - `#bugs` - Report bugs

### Community Forum

Visit our community forum for in-depth discussions:
- **Forum**: https://community.codegenie.dev
- **Categories**:
  - General Discussion
  - Help & Support
  - Feature Requests
  - Show & Tell
  - Development

### GitHub Discussions

Participate in GitHub Discussions:
- **URL**: https://github.com/your-org/codegenie/discussions
- **Topics**:
  - Q&A
  - Ideas
  - Show and tell
  - General

## Bug Reports

### Reporting Bugs

Found a bug? Please report it on GitHub Issues:

1. **Check existing issues**: https://github.com/your-org/codegenie/issues
2. **Create new issue**: Use the bug report template
3. **Include**:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Error messages and logs
   - Screenshots if applicable

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots.

**System Information**
- OS: [e.g. Ubuntu 22.04]
- Python version: [e.g. 3.10.5]
- CodeGenie version: [e.g. 0.3.0]
- Ollama version: [e.g. 0.1.20]

**Error Messages**
```
Paste error messages here
```

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other context about the problem.
```

### Generating Diagnostic Information

Use the built-in diagnostic tool:

```bash
# Run diagnostics
codegenie diagnostics

# Export diagnostics to file
codegenie diagnostics --export diagnostics.json
```

Include the diagnostic information in your bug report.

## Feature Requests

### Requesting Features

Have an idea for a new feature?

1. **Check existing requests**: https://github.com/your-org/codegenie/issues?q=is%3Aissue+label%3Aenhancement
2. **Create new request**: Use the feature request template
3. **Include**:
   - Clear description
   - Use case
   - Expected behavior
   - Mockups/examples if applicable

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Use case**
Describe how you would use this feature.

**Additional context**
Any other context, screenshots, or mockups.
```

## Email Support

For private inquiries or sensitive issues:

- **Email**: support@codegenie.dev
- **Response time**: Within 48 hours
- **Include**:
  - Subject line with clear description
  - Detailed description of issue
  - System information
  - Error messages/logs if applicable

## Priority Support

### Enterprise Support

For enterprise customers, we offer priority support:

- **Dedicated support channel**
- **24/7 availability**
- **SLA guarantees**
- **Direct access to engineering team**
- **Custom training and onboarding**

Contact: enterprise@codegenie.dev

## Self-Service Tools

### Diagnostic Tool

Run diagnostics to identify issues:

```bash
codegenie diagnostics
```

This checks:
- System information
- Ollama status
- Installed models
- Configuration validity
- Disk space
- Recent errors

### Error Reporting

When an error occurs, CodeGenie automatically generates an error report:

```bash
# View recent errors
codegenie errors list

# View specific error
codegenie errors show <error-id>

# Export error report
codegenie errors export <error-id> error-report.json
```

### Log Files

Check log files for detailed information:

```bash
# View main log
tail -f ~/.codegenie/logs/codegenie.log

# View agent logs
tail -f ~/.codegenie/logs/agents.log

# View error logs
tail -f ~/.codegenie/logs/errors.log
```

## Common Issues

### Installation Issues

**Problem**: Ollama not found
```bash
# Solution: Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

**Problem**: Python version too old
```bash
# Solution: Install Python 3.9+
# Ubuntu/Debian
sudo apt install python3.9

# macOS
brew install python@3.9
```

### Runtime Issues

**Problem**: Out of memory
```bash
# Solution: Use smaller model
codegenie --model llama3.1:8b
```

**Problem**: Model not found
```bash
# Solution: Install model
ollama pull llama3.1:8b
```

### Performance Issues

**Problem**: Slow responses
```bash
# Solution: Enable caching
# Edit ~/.config/codegenie/config.yaml
cache:
  enabled: true
```

See [Troubleshooting Guide](TROUBLESHOOTING.md) for more solutions.

## Contributing

Want to contribute? We welcome contributions!

1. **Read**: [Contributing Guide](../CONTRIBUTING.md)
2. **Fork**: Fork the repository
3. **Branch**: Create a feature branch
4. **Code**: Make your changes
5. **Test**: Run tests
6. **Submit**: Create a pull request

## Security Issues

Found a security vulnerability?

**DO NOT** create a public issue. Instead:

1. **Email**: security@codegenie.dev
2. **Include**:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We take security seriously and will respond promptly.

## Feedback

We value your feedback!

### In-App Feedback

Provide feedback directly in CodeGenie:

```bash
codegenie feedback
```

This will prompt you for:
- Feedback type (bug, feature, general)
- Rating (1-5)
- Comments

### Surveys

Participate in our periodic surveys:
- User satisfaction surveys
- Feature prioritization surveys
- Usability studies

We'll notify you via email or in-app.

## Social Media

Follow us for updates:

- **Twitter**: [@codegenie_dev](https://twitter.com/codegenie_dev)
- **LinkedIn**: [CodeGenie](https://linkedin.com/company/codegenie)
- **Blog**: https://blog.codegenie.dev
- **YouTube**: [CodeGenie Channel](https://youtube.com/@codegenie)

## Office Hours

Join our weekly office hours:

- **When**: Every Friday, 2-3 PM PST
- **Where**: Discord voice channel
- **What**: Ask questions, get help, discuss features

## Resources

### Video Tutorials

- [Getting Started](https://youtube.com/watch?v=xxx)
- [Advanced Features](https://youtube.com/watch?v=xxx)
- [Autonomous Workflows](https://youtube.com/watch?v=xxx)
- [Multi-Agent System](https://youtube.com/watch?v=xxx)

### Blog Posts

- [Introduction to CodeGenie](https://blog.codegenie.dev/intro)
- [Best Practices](https://blog.codegenie.dev/best-practices)
- [Case Studies](https://blog.codegenie.dev/case-studies)

### Example Projects

- [REST API Example](../examples/rest-api)
- [Web App Example](../examples/web-app)
- [CLI Tool Example](../examples/cli-tool)

## Response Times

Expected response times:

| Channel | Response Time |
|---------|---------------|
| Discord | Minutes to hours |
| Forum | Hours to 1 day |
| GitHub Issues | 1-3 days |
| Email | 1-2 days |
| Enterprise Support | Hours (24/7) |

## Support Hours

Community support is available 24/7 through Discord and forums.

Email support hours:
- **Monday-Friday**: 9 AM - 6 PM PST
- **Weekends**: Limited availability

## Language Support

Primary language: English

Community translations available for:
- Spanish
- French
- German
- Chinese
- Japanese

## Accessibility

We're committed to accessibility. If you encounter accessibility issues:

- **Email**: accessibility@codegenie.dev
- **Include**: Description of issue and your accessibility needs

## Thank You

Thank you for using CodeGenie! We're here to help you succeed.

If you have any questions or need assistance, don't hesitate to reach out through any of the channels above.

Happy coding! 🧞‍♂️
