# Documentation Generator Integration Guide

## Overview
This guide explains how to integrate the Documentation Generator into the CodeGenie system.

## Components

### 1. DocumentationGenerator
**Location**: `src/codegenie/core/documentation_generator.py`

**Purpose**: Main documentation generation system

**Key Methods**:
- `generate_docstring(code, name, entity_type)` - Generate docstrings
- `generate_readme(project_path, project_name, description)` - Generate README
- `generate_api_documentation(project_path, output_format)` - Generate API docs
- `explain_code(code, context, detail_level)` - Explain code
- `generate_examples(code, num_examples)` - Generate usage examples
- `check_doc_sync(project_path, check_docstrings, check_readme)` - Check sync
- `validate_documentation(project_path)` - Validate documentation
- `update_documentation(project_path, update_docstrings, update_readme)` - Update docs

### 2. CodeExplainer
**Location**: `src/codegenie/core/code_explainer.py`

**Purpose**: Advanced code analysis and explanation

**Key Methods**:
- `analyze_code(code, language)` - Comprehensive code analysis
- `explain_concept(concept)` - Explain programming concepts
- `generate_tutorial(code)` - Generate step-by-step tutorials

## Integration with Existing Components

### With Planning Agent
```python
from codegenie.core.planning_agent import PlanningAgent
from codegenie.core.documentation_generator import DocumentationGenerator

# In planning phase, suggest documentation tasks
planner = PlanningAgent()
doc_gen = DocumentationGenerator()

# Add documentation step to plan
plan.add_step({
    "action": "generate_documentation",
    "description": "Generate API documentation",
    "tool": doc_gen
})
```

### With File Creator
```python
from codegenie.core.file_creator import FileCreator
from codegenie.core.documentation_generator import DocumentationGenerator

file_creator = FileCreator()
doc_gen = DocumentationGenerator()

# Generate and create README
readme_content = doc_gen.generate_readme(project_path)
file_creator.create_file("README.md", readme_content)
```

### With Multi-File Editor
```python
from codegenie.core.multi_file_editor import MultiFileEditor
from codegenie.core.documentation_generator import DocumentationGenerator

editor = MultiFileEditor()
doc_gen = DocumentationGenerator()

# Update docstrings across multiple files
issues = doc_gen.check_doc_sync(project_path)
for issue in issues:
    if issue.issue_type == "missing_docstring":
        # Generate and add docstring
        docstring = doc_gen.generate_docstring(...)
        editor.add_change(issue.file_path, docstring)
```

### With Context Analyzer
```python
from codegenie.core.context_analyzer import ContextAnalyzer
from codegenie.core.documentation_generator import DocumentationGenerator

analyzer = ContextAnalyzer()
doc_gen = DocumentationGenerator()

# Use project context for better documentation
context = analyzer.analyze_project(project_path)
readme = doc_gen.generate_readme(
    project_path,
    project_name=context.project_path.name,
    description=f"A {context.language.name} project"
)
```

## CLI Integration

### Add Documentation Commands

```python
# In src/codegenie/cli.py

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--style', default='google', help='Docstring style')
def generate_docs(path, style):
    """Generate documentation for a project."""
    from codegenie.core.documentation_generator import (
        DocumentationGenerator,
        DocstringStyle
    )
    
    doc_gen = DocumentationGenerator(
        docstring_style=DocstringStyle[style.upper()]
    )
    
    # Generate API documentation
    api_doc = doc_gen.generate_api_documentation(Path(path))
    
    # Save to file
    output_path = Path(path) / "docs" / "api.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(doc_gen.format_api_documentation(api_doc))
    
    click.echo(f"Documentation generated: {output_path}")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def check_docs(path):
    """Check documentation sync."""
    from codegenie.core.documentation_generator import DocumentationGenerator
    
    doc_gen = DocumentationGenerator()
    issues = doc_gen.check_doc_sync(Path(path))
    
    if not issues:
        click.echo("✓ All documentation is in sync!")
    else:
        click.echo(f"Found {len(issues)} issue(s):")
        for issue in issues:
            click.echo(f"  [{issue.severity}] {issue.description}")

@cli.command()
@click.argument('code_file', type=click.Path(exists=True))
@click.option('--level', default='standard', help='Detail level')
def explain(code_file, level):
    """Explain code in natural language."""
    from codegenie.core.documentation_generator import DocumentationGenerator
    
    doc_gen = DocumentationGenerator()
    code = Path(code_file).read_text()
    
    explanation = doc_gen.explain_code(code, detail_level=level)
    click.echo(explanation)
```

## Web Interface Integration

### Add Documentation Endpoints

```python
# In src/codegenie/ui/web_interface.py

from flask import Flask, request, jsonify
from codegenie.core.documentation_generator import DocumentationGenerator

app = Flask(__name__)
doc_gen = DocumentationGenerator()

@app.route('/api/generate-docstring', methods=['POST'])
def generate_docstring():
    """Generate docstring for code."""
    data = request.json
    code = data.get('code')
    name = data.get('name')
    entity_type = data.get('type', 'function')
    
    docstring = doc_gen.generate_docstring(code, name, entity_type)
    return jsonify({'docstring': docstring})

@app.route('/api/explain-code', methods=['POST'])
def explain_code():
    """Explain code."""
    data = request.json
    code = data.get('code')
    level = data.get('level', 'standard')
    
    explanation = doc_gen.explain_code(code, detail_level=level)
    return jsonify({'explanation': explanation})

@app.route('/api/check-docs/<path:project_path>', methods=['GET'])
def check_docs(project_path):
    """Check documentation sync."""
    issues = doc_gen.check_doc_sync(Path(project_path))
    
    return jsonify({
        'total_issues': len(issues),
        'issues': [
            {
                'type': issue.issue_type,
                'severity': issue.severity,
                'description': issue.description,
                'file': str(issue.file_path),
                'line': issue.line_number,
                'suggestion': issue.suggestion
            }
            for issue in issues
        ]
    })
```

## Automated Workflows

### Pre-commit Hook
```python
# .git/hooks/pre-commit

#!/usr/bin/env python3
from pathlib import Path
from codegenie.core.documentation_generator import DocumentationGenerator

doc_gen = DocumentationGenerator()
project_path = Path.cwd()

# Check documentation
issues = doc_gen.check_doc_sync(project_path)
critical_issues = [i for i in issues if i.severity == "error"]

if critical_issues:
    print(f"❌ Found {len(critical_issues)} critical documentation issues:")
    for issue in critical_issues:
        print(f"  - {issue.description}")
    exit(1)

print("✓ Documentation check passed")
```

### CI/CD Integration
```yaml
# .github/workflows/docs.yml

name: Documentation Check

on: [push, pull_request]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Check documentation
        run: |
          python -c "
          from pathlib import Path
          from codegenie.core.documentation_generator import DocumentationGenerator
          
          doc_gen = DocumentationGenerator()
          report = doc_gen.validate_documentation(Path('.'))
          
          print(f'Documentation Score: {report[\"score\"]:.1f}%')
          
          if report['score'] < 80:
              print('❌ Documentation score below threshold')
              exit(1)
          "
```

## Best Practices

### 1. Use Appropriate Docstring Style
Choose a docstring style that matches your project:
- **Google**: Clean, readable (recommended for most projects)
- **NumPy**: Scientific Python projects
- **Sphinx**: Projects using Sphinx documentation
- **Plain**: Simple projects

### 2. Regular Documentation Checks
Run documentation checks regularly:
```python
# Weekly documentation audit
doc_gen = DocumentationGenerator()
report = doc_gen.validate_documentation(project_path)

if report['score'] < 90:
    # Send notification
    # Update documentation
    pass
```

### 3. Automated Documentation Updates
Set up automated documentation updates:
```python
# After code changes
doc_gen.update_documentation(
    project_path,
    update_docstrings=True,
    update_readme=False  # Manual review recommended
)
```

### 4. Context-Aware Documentation
Use project context for better documentation:
```python
from codegenie.core.context_analyzer import ContextAnalyzer

analyzer = ContextAnalyzer()
context = analyzer.analyze_project(project_path)

# Use context for documentation
doc_gen = DocumentationGenerator()
# Documentation will be aware of project conventions
```

## Testing

### Unit Tests
```python
def test_documentation_generator():
    doc_gen = DocumentationGenerator()
    
    code = "def add(a, b): return a + b"
    docstring = doc_gen.generate_docstring(code, "add", "function")
    
    assert '"""' in docstring
    assert "add" in docstring.lower()
```

### Integration Tests
```python
def test_full_documentation_workflow():
    doc_gen = DocumentationGenerator()
    
    # Generate README
    readme = doc_gen.generate_readme(project_path)
    assert len(readme) > 0
    
    # Generate API docs
    api_doc = doc_gen.generate_api_documentation(project_path)
    assert len(api_doc.modules) > 0
    
    # Check sync
    issues = doc_gen.check_doc_sync(project_path)
    assert isinstance(issues, list)
```

## Troubleshooting

### Issue: Docstring generation fails
**Solution**: Check if code is valid Python. Use try-except:
```python
try:
    docstring = doc_gen.generate_docstring(code, name, entity_type)
except Exception as e:
    logger.error(f"Failed to generate docstring: {e}")
    docstring = f'"""{name}."""'  # Fallback
```

### Issue: README generation is generic
**Solution**: Provide more context:
```python
readme = doc_gen.generate_readme(
    project_path,
    project_name="MyProject",
    description="Detailed description here"
)
```

### Issue: Too many sync issues reported
**Solution**: Filter by severity:
```python
issues = doc_gen.check_doc_sync(project_path)
critical = [i for i in issues if i.severity in ["error", "warning"]]
```

## Performance Considerations

1. **Cache Results**: Cache documentation analysis results
2. **Incremental Updates**: Only update changed files
3. **Parallel Processing**: Process multiple files in parallel
4. **Lazy Loading**: Load documentation on demand

## Future Enhancements

1. AI-powered documentation with LLMs
2. Multi-language support (JS, TS, Go, Rust)
3. Automatic diagram generation
4. Interactive documentation
5. Version-aware documentation
6. Custom template support

## Conclusion

The Documentation Generator is now fully integrated and ready to use. Follow this guide to incorporate it into your workflows and enjoy automated, high-quality documentation!
