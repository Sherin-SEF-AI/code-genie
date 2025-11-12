# Contributing to CodeGenie

First off, thank you for considering contributing to CodeGenie! It's people like you that make CodeGenie such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Describe the behavior you observed and what you expected**
- **Include screenshots if relevant**
- **Include your environment details** (OS, Python version, Ollama version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any similar features in other tools**

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:

- `good first issue` - Simple issues perfect for beginners
- `help wanted` - Issues where we need community help
- `documentation` - Documentation improvements

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows our coding standards
6. Issue the pull request!

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Ollama installed and running
- Git
- Virtual environment tool (venv or conda)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/codegenie.git
cd codegenie

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Run tests to verify setup
pytest tests/
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agent.py

# Run with coverage
pytest --cov=src/codegenie tests/

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/
```

## Pull Request Process

1. **Update Documentation**: Update the README.md and relevant docs with details of changes
2. **Update Tests**: Add or update tests for your changes
3. **Follow Coding Standards**: Ensure your code follows our style guide
4. **Update Changelog**: Add your changes to CHANGELOG.md
5. **One Feature Per PR**: Keep pull requests focused on a single feature or fix
6. **Descriptive Commits**: Write clear, descriptive commit messages
7. **Link Issues**: Reference any related issues in your PR description

### Commit Message Format

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(agents): add refactoring agent

Implement a new specialized agent for code refactoring tasks.
The agent can identify code smells and suggest improvements.

Closes #123
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: 100 characters (not 79)
- **Imports**: Group imports (standard library, third-party, local)
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings

### Code Quality Tools

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all checks
./scripts/check-code-quality.sh
```

### Example Code

```python
from typing import List, Optional

def process_code(
    code: str,
    language: str,
    options: Optional[dict] = None
) -> List[str]:
    """Process code and return suggestions.
    
    Args:
        code: The source code to process
        language: Programming language (e.g., 'python', 'javascript')
        options: Optional processing options
        
    Returns:
        List of suggestions for code improvement
        
    Raises:
        ValueError: If language is not supported
    """
    if options is None:
        options = {}
    
    # Implementation here
    return []
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interaction
├── e2e/           # End-to-end tests for complete workflows
└── fixtures/      # Test fixtures and data
```

### Writing Tests

```python
import pytest
from codegenie.core.agent import CodeGenieAgent

def test_agent_initialization():
    """Test that agent initializes correctly."""
    agent = CodeGenieAgent()
    assert agent is not None
    assert agent.status == "ready"

@pytest.mark.asyncio
async def test_agent_execute_task():
    """Test task execution."""
    agent = CodeGenieAgent()
    result = await agent.execute_task("create a function")
    assert result.success is True
    assert len(result.files_created) > 0
```

### Test Coverage

- Aim for 80%+ code coverage
- All new features must include tests
- Bug fixes should include regression tests

## Documentation

### Documentation Standards

- **Clear and Concise**: Write for developers of all skill levels
- **Examples**: Include code examples for all features
- **Up-to-Date**: Update docs when changing functionality
- **Screenshots**: Add screenshots for UI features
- **Links**: Link to related documentation

### Documentation Structure

```
docs/
├── USER_GUIDE.md           # User-facing documentation
├── API_REFERENCE.md        # API documentation
├── TUTORIALS.md            # Step-by-step tutorials
├── CONTRIBUTING.md         # This file
└── ARCHITECTURE.md         # System architecture
```

### Writing Documentation

- Use Markdown format
- Include table of contents for long documents
- Use code blocks with syntax highlighting
- Add links to related sections
- Include troubleshooting tips

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Discord**: Real-time chat and community support
- **Twitter**: [@codegenie_dev](https://twitter.com/codegenie_dev)

### Getting Help

- Check the [FAQ](docs/FAQ.md)
- Search existing [GitHub Issues](https://github.com/Sherin-SEF-AI/codegenie/issues)
- Ask in [GitHub Discussions](https://github.com/Sherin-SEF-AI/codegenie/discussions)
- Join our [Discord server](https://discord.gg/codegenie)

### Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project website (coming soon)

## License

By contributing to CodeGenie, you agree that your contributions will be licensed under the MIT License.

## Questions?

Don't hesitate to ask questions! We're here to help:

- Open an issue with the `question` label
- Ask in GitHub Discussions
- Reach out on Discord
- Email: support@codegenie.dev

## Thank You!

Your contributions make CodeGenie better for everyone. We appreciate your time and effort!

---

**Author**: Sherin Joseph Roy  
**Website**: [sherinjosephroy.link](https://sherinjosephroy.link)  
**GitHub**: [@Sherin-SEF-AI](https://github.com/Sherin-SEF-AI)
