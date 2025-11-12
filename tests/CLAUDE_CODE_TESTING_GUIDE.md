# Claude Code Features Testing Guide

## Overview

This document describes the comprehensive test suite for Claude Code features, including unit tests, integration tests, safety tests, and security audits.

## Test Structure

```
tests/
├── unit/                                    # Unit tests for individual components
│   ├── test_planning_agent.py             # Planning Agent tests
│   ├── test_file_creator.py               # File Creator tests
│   ├── test_command_executor.py           # Command Executor tests
│   └── test_approval_system.py            # Approval System tests
│
├── integration/                             # Integration tests
│   ├── test_claude_code_workflows.py      # End-to-end workflow tests
│   └── test_safety_mechanisms.py          # Safety mechanism tests
│
└── security/                                # Security audit tests
    └── test_security_audit.py             # Security tests
```

## Test Categories

### 1. Unit Tests

Unit tests verify individual components in isolation.

#### Planning Agent Tests (`test_planning_agent.py`)
- Plan creation for different task types
- Task decomposition
- Complexity estimation
- Plan validation
- Circular dependency detection
- Plan execution with approval callbacks
- Progress tracking

**Run:**
```bash
pytest tests/unit/test_planning_agent.py -v
```

#### File Creator Tests (`test_file_creator.py`)
- File creation, modification, deletion
- Diff generation and preview
- Directory structure creation
- Operation approval workflow
- Batch operations
- File type detection

**Run:**
```bash
pytest tests/unit/test_file_creator.py -v
```

#### Command Executor Tests (`test_command_executor.py`)
- Command classification (safe/risky/dangerous)
- Command execution with approval
- Error recovery and suggestions
- Streaming output
- Retry mechanisms
- Command history tracking

**Run:**
```bash
pytest tests/unit/test_command_executor.py -v
```

#### Approval System Tests (`test_approval_system.py`)
- Approval workflows
- Batch approval
- Preference storage
- Undo point creation
- Rollback mechanisms
- Conflict detection
- File backup and restore

**Run:**
```bash
pytest tests/unit/test_approval_system.py -v
```

### 2. Integration Tests

Integration tests verify component interactions and end-to-end workflows.

#### Workflow Tests (`test_claude_code_workflows.py`)
- Project creation workflow
- Refactoring workflow
- Error recovery workflow
- Component interaction
- Batch operations
- Complex multi-step workflows

**Run:**
```bash
pytest tests/integration/test_claude_code_workflows.py -v
```

#### Safety Mechanism Tests (`test_safety_mechanisms.py`)
- Command blocking for dangerous operations
- File backup and restore
- Rollback mechanisms
- Permission handling
- Atomic operations
- Safety auditing

**Run:**
```bash
pytest tests/integration/test_safety_mechanisms.py -v
```

### 3. Security Tests

Security tests audit the system for security vulnerabilities.

#### Security Audit Tests (`test_security_audit.py`)
- Command execution security
- Path traversal prevention
- Input validation
- Permission handling
- Audit logging
- Security best practices

**Run:**
```bash
pytest tests/security/test_security_audit.py -v
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Category
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Security tests only
pytest tests/security/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_planning_agent.py -v
```

### Run Specific Test
```bash
pytest tests/unit/test_planning_agent.py::TestPlanningAgent::test_create_plan_project_creation -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src/codegenie/core --cov-report=html
```

### Run with Markers
```bash
# Run only async tests
pytest tests/ -m asyncio -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

## Test Coverage

### Core Components Coverage

| Component | Unit Tests | Integration Tests | Security Tests |
|-----------|------------|-------------------|----------------|
| Planning Agent | ✓ | ✓ | - |
| File Creator | ✓ | ✓ | ✓ |
| Command Executor | ✓ | ✓ | ✓ |
| Approval System | ✓ | ✓ | ✓ |

### Coverage Goals

- **Overall Coverage**: > 80%
- **Core Components**: > 90%
- **Critical Paths**: 100%

## Test Requirements

### Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Environment Setup
```bash
# Install project dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt  # if exists
```

## Writing New Tests

### Test Structure
```python
import pytest

class TestFeatureName:
    """Test suite for feature name."""
    
    @pytest.fixture
    def setup_fixture(self):
        """Set up test fixture."""
        # Setup code
        yield fixture_data
        # Teardown code
    
    def test_specific_behavior(self, setup_fixture):
        """Test specific behavior with clear description."""
        # Arrange
        input_data = setup_fixture
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result.success
        assert result.value == expected_value
```

### Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Test names should describe what is being tested
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Use Fixtures**: Leverage pytest fixtures for setup/teardown
5. **Mock External Dependencies**: Isolate the code under test
6. **Test Edge Cases**: Include boundary conditions
7. **Document Complex Tests**: Add comments for complex test logic

## Test Scenarios

### Unit Test Scenarios

#### Planning Agent
- ✓ Create plans for different task types
- ✓ Break down complex tasks
- ✓ Estimate complexity accurately
- ✓ Validate plans for errors
- ✓ Detect circular dependencies
- ✓ Execute plans with approval
- ✓ Track execution progress

#### File Creator
- ✓ Create new files
- ✓ Modify existing files
- ✓ Delete files safely
- ✓ Generate diffs
- ✓ Create directory structures
- ✓ Handle approval workflows
- ✓ Batch operations

#### Command Executor
- ✓ Classify command risk levels
- ✓ Execute safe commands
- ✓ Block dangerous commands
- ✓ Handle command failures
- ✓ Provide error recovery
- ✓ Stream command output
- ✓ Retry failed commands

#### Approval System
- ✓ Request approval
- ✓ Batch approval
- ✓ Store preferences
- ✓ Create undo points
- ✓ Rollback changes
- ✓ Detect conflicts
- ✓ Backup files

### Integration Test Scenarios

#### Workflows
- ✓ Project creation workflow
- ✓ Refactoring workflow
- ✓ Error recovery workflow
- ✓ Component interaction
- ✓ Batch operations
- ✓ Complex multi-step workflows

#### Safety
- ✓ Command blocking
- ✓ File backup/restore
- ✓ Rollback mechanisms
- ✓ Permission handling
- ✓ Atomic operations
- ✓ Safety auditing

### Security Test Scenarios

#### Command Security
- ✓ Dangerous command detection
- ✓ Command injection prevention
- ✓ Timeout enforcement
- ✓ Environment isolation
- ✓ Sudo command detection

#### File Security
- ✓ Path traversal prevention
- ✓ Symlink handling
- ✓ Permission preservation
- ✓ Overwrite prevention
- ✓ Backup before destruction

#### Access Control
- ✓ Approval for high-risk operations
- ✓ Preference storage security
- ✓ Undo history access control

#### Input Validation
- ✓ File path validation
- ✓ Content validation
- ✓ Command string validation
- ✓ Null byte injection prevention

## Continuous Integration

### GitHub Actions Example
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest tests/ -v --cov=src/codegenie/core
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure project is installed in development mode
pip install -e .
```

**Async Test Failures**
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**Permission Errors**
```bash
# Run tests with appropriate permissions
# Or use temporary directories for file operations
```

**Timeout Errors**
```bash
# Increase timeout for slow tests
pytest tests/ --timeout=300
```

## Test Metrics

### Current Status
- **Total Tests**: 150+
- **Unit Tests**: 80+
- **Integration Tests**: 50+
- **Security Tests**: 20+
- **Pass Rate**: > 95%

### Performance Benchmarks
- **Unit Test Execution**: < 30 seconds
- **Integration Test Execution**: < 2 minutes
- **Full Test Suite**: < 5 minutes

## Contributing

### Adding New Tests

1. Identify the component or feature to test
2. Choose appropriate test category (unit/integration/security)
3. Create test file following naming convention
4. Write tests following best practices
5. Run tests locally
6. Submit pull request with tests

### Test Review Checklist

- [ ] Tests are independent and isolated
- [ ] Test names are descriptive
- [ ] Edge cases are covered
- [ ] Fixtures are used appropriately
- [ ] Tests pass locally
- [ ] Coverage is maintained or improved
- [ ] Documentation is updated

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

## Summary

This comprehensive test suite ensures the reliability, safety, and security of Claude Code features. The tests cover:

- **Core Functionality**: All major components are thoroughly tested
- **Integration**: Component interactions are verified
- **Safety**: Safety mechanisms are validated
- **Security**: Security vulnerabilities are audited

Regular execution of these tests helps maintain code quality and prevents regressions.
