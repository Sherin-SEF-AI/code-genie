# Example: Automated Testing Workflow

This example demonstrates how to use CodeGenie to automate your testing workflow with safe command execution.

## Scenario

You want to automate:
1. Running tests before commits
2. Checking code coverage
3. Running linters and formatters
4. Generating test reports

## Step-by-Step with CodeGenie

### Step 1: Set Up Testing Workflow

```
You: Set up an automated testing workflow that runs tests, checks coverage, and runs linters before each commit

CodeGenie: I'll set up a comprehensive testing workflow for you.

📋 Plan:
1. Install testing dependencies (pytest, coverage, flake8, black)
2. Create pytest configuration
3. Create coverage configuration
4. Set up pre-commit hooks
5. Create test runner script
6. Add CI/CD configuration

Proceed? (y/n): y
```

### Step 2: Install Dependencies

```
CodeGenie: Installing testing dependencies...

Command: pip install pytest pytest-cov pytest-asyncio flake8 black isort pre-commit
Risk: Risky (installs packages)
Approve? (y/n): y

✅ Installing pytest...
✅ Installing pytest-cov...
✅ Installing pytest-asyncio...
✅ Installing flake8...
✅ Installing black...
✅ Installing isort...
✅ Installing pre-commit...

All dependencies installed successfully!
```

### Step 3: Configure Testing Tools

```
CodeGenie: Creating configuration files...

✅ Created: pytest.ini

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

✅ Created: .coveragerc

[run]
source = src
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

✅ Created: .flake8

[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    venv,
    .venv

✅ Created: pyproject.toml

[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
```

### Step 4: Create Test Runner Script

```
CodeGenie: Creating test runner script...

✅ Created: scripts/run_tests.sh

#!/bin/bash
set -e

echo "🧪 Running automated tests..."

# Format code
echo "📝 Formatting code with black..."
black src/ tests/

# Sort imports
echo "📦 Sorting imports with isort..."
isort src/ tests/

# Lint code
echo "🔍 Linting with flake8..."
flake8 src/ tests/

# Run tests with coverage
echo "🧪 Running tests with coverage..."
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

# Check coverage threshold
echo "📊 Checking coverage threshold..."
coverage report --fail-under=80

echo "✅ All checks passed!"

✅ Made executable: chmod +x scripts/run_tests.sh
```

### Step 5: Set Up Pre-Commit Hooks

```
CodeGenie: Setting up pre-commit hooks...

✅ Created: .pre-commit-config.yaml

repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true

Command: pre-commit install
Risk: Safe (installs git hooks)
Executing...

✅ Pre-commit hooks installed

Now your tests will run automatically before each commit!
```

### Step 6: Run the Test Suite

```
You: Run the test suite

CodeGenie: Running automated test suite...

Command: ./scripts/run_tests.sh
Risk: Safe (runs tests)
Executing...

🧪 Running automated tests...

📝 Formatting code with black...
All done! ✨ 🍰 ✨
12 files reformatted, 3 files left unchanged.

📦 Sorting imports with isort...
Fixing /path/to/src/main.py
Fixing /path/to/src/services/user.py
Skipped 10 files

🔍 Linting with flake8...
✅ No issues found

🧪 Running tests with coverage...

tests/test_auth.py::test_register PASSED                    [ 10%]
tests/test_auth.py::test_login PASSED                       [ 20%]
tests/test_auth.py::test_invalid_credentials PASSED         [ 30%]
tests/test_posts.py::test_create_post PASSED                [ 40%]
tests/test_posts.py::test_get_posts PASSED                  [ 50%]
tests/test_posts.py::test_update_post PASSED                [ 60%]
tests/test_posts.py::test_delete_post PASSED                [ 70%]
tests/test_posts.py::test_unauthorized_delete PASSED        [ 80%]
tests/test_comments.py::test_create_comment PASSED          [ 90%]
tests/test_comments.py::test_get_comments PASSED            [100%]

---------- coverage: platform linux, python 3.9.7 -----------
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/__init__.py                   0      0   100%
src/main.py                      45      2    96%   78-79
src/api/auth.py                  67      5    93%   45, 67, 89, 102, 115
src/api/posts.py                 89      7    92%   34, 56, 78, 90, 112, 134, 156
src/services/auth.py             56      3    95%   23, 45, 67
src/services/post.py             78      6    92%   12, 34, 56, 78, 90, 102
src/models/user.py               34      0   100%
src/models/post.py               45      0   100%
-----------------------------------------------------------
TOTAL                           414     23    94%

📊 Checking coverage threshold...
✅ Coverage is 94% (threshold: 80%)

✅ All checks passed!

Test report generated: htmlcov/index.html
```

### Step 7: View Coverage Report

```
You: Open the coverage report

CodeGenie: Opening coverage report...

Command: open htmlcov/index.html
Risk: Safe (opens file)
Executing...

✅ Coverage report opened in browser

The report shows:
- Overall coverage: 94%
- Files with < 100% coverage highlighted
- Line-by-line coverage visualization
- Missing lines highlighted in red
```

### Step 8: Fix Coverage Gaps

```
You: The auth service has only 95% coverage. Add tests for the missing lines.

CodeGenie: Analyzing coverage gaps in auth service...

Missing coverage:
- Line 23: Error handling for invalid token
- Line 45: Error handling for expired token
- Line 67: Error handling for malformed token

Creating tests...

✅ Updated: tests/test_auth.py

Added tests:
- test_invalid_token_format
- test_expired_token
- test_malformed_token

Running tests...

tests/test_auth.py::test_invalid_token_format PASSED
tests/test_auth.py::test_expired_token PASSED
tests/test_auth.py::test_malformed_token PASSED

New coverage: 100% for auth service ✅
Overall coverage: 96% ✅
```

## Automated Workflow in Action

### Making a Commit

```bash
git add .
git commit -m "Add user profile feature"
```

Pre-commit hooks run automatically:

```
[INFO] Initializing environment for black...
[INFO] Initializing environment for isort...
[INFO] Initializing environment for flake8...
[INFO] Installing environment for black...
[INFO] Installing environment for isort...
[INFO] Installing environment for flake8...

black....................................................................Passed
isort....................................................................Passed
flake8...................................................................Passed
pytest...................................................................Passed

✅ All checks passed! Commit successful.
```

### Continuous Integration

```
You: Add GitHub Actions workflow for CI

CodeGenie: Creating GitHub Actions workflow...

✅ Created: .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black isort
    
    - name: Run tests
      run: ./scripts/run_tests.sh
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml

Now your tests will run automatically on every push!
```

## Key Features Demonstrated

### 1. Safe Command Execution
- Commands classified by risk level
- Approval required for risky commands
- Safe commands auto-executed

### 2. Automated Testing
- Tests run automatically
- Coverage checked
- Linting enforced

### 3. Pre-Commit Hooks
- Code formatted before commit
- Tests run before commit
- Prevents bad code from being committed

### 4. Continuous Integration
- Tests run on every push
- Coverage tracked over time
- Build status visible

## Benefits

- ✅ Consistent code quality
- ✅ Catch bugs early
- ✅ Automated formatting
- ✅ High test coverage
- ✅ Fast feedback loop

## Running the Example

```bash
# Navigate to example
cd examples/03_command_execution/automated_testing/

# Start CodeGenie
codegenie

# Follow the steps in this README

# Try making a commit
git add .
git commit -m "Test commit"
# Watch pre-commit hooks run!
```

## Customization

### Adjust Coverage Threshold

```
You: Change the coverage threshold to 90%

CodeGenie: Updating coverage threshold...

✅ Updated: pytest.ini
✅ Updated: scripts/run_tests.sh

Coverage threshold now: 90%
```

### Add More Linters

```
You: Add mypy for type checking

CodeGenie: Adding mypy...

✅ Installed: mypy
✅ Created: mypy.ini
✅ Updated: .pre-commit-config.yaml
✅ Updated: scripts/run_tests.sh

Type checking now included in test suite!
```

## Troubleshooting

### Tests Failing

```
You: Tests are failing, help me debug

CodeGenie: Analyzing test failures...

Found 3 failing tests:
1. test_create_user - AssertionError on line 45
2. test_update_post - Database connection error
3. test_delete_comment - Permission error

Let me help fix these...
```

### Pre-Commit Hooks Too Slow

```
You: Pre-commit hooks are taking too long

CodeGenie: I can optimize the pre-commit hooks.

Options:
1. Run only fast checks pre-commit (format, lint)
2. Run full tests only in CI
3. Use parallel execution
4. Skip tests for certain file types

Which would you prefer?
```

## Next Steps

- Try [Database Migrations](../database_migrations/) example
- Explore [Deployment Scripts](../deployment/) example
- Learn about [Autonomous Development](../../04_autonomous/)

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pre-commit Documentation](https://pre-commit.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

