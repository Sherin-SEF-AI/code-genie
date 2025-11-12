# Context Analyzer Guide

## Overview

The Context Analyzer is a powerful component that understands your project's structure, conventions, and patterns. It provides intelligent analysis to help CodeGenie generate code that matches your project's style and architecture.

## Features

### 1. Language Detection
Automatically detects the primary programming language(s) in your project:
- Python, JavaScript, TypeScript, Go, Rust, Java, C++
- Confidence scoring
- Multi-language project support

### 2. Framework Detection
Identifies frameworks and libraries used:
- **Python**: Django, Flask, FastAPI, pytest, numpy, pandas, tensorflow, pytorch
- **JavaScript/TypeScript**: React, Vue, Angular, Express, Next.js, Jest, NestJS
- Categorization (web, testing, data, cli)

### 3. Coding Convention Extraction
Learns your coding style automatically:
- Indentation (spaces vs tabs, size)
- Quote style (single vs double)
- Line length preferences
- Naming conventions (snake_case, camelCase, PascalCase)
- Import patterns

### 4. Architecture Pattern Detection
Recognizes common architecture patterns:
- MVC (Model-View-Controller)
- Layered Architecture
- Microservices
- Clean Architecture
- Monorepo
- Hexagonal Architecture

### 5. Dependency Analysis
- Parses dependency files (requirements.txt, package.json, go.mod, Cargo.toml)
- Builds dependency graphs
- Tracks versions and sources

### 6. Code Similarity Search
- Finds similar code patterns
- Token-based similarity matching
- Configurable thresholds

## Usage

### Basic Project Analysis

```python
from codegenie.core.context_analyzer import ContextAnalyzer
from pathlib import Path

# Initialize analyzer
analyzer = ContextAnalyzer()

# Analyze your project
context = analyzer.analyze_project(Path("/path/to/project"))

# Access results
print(f"Language: {context.language.name}")
print(f"Frameworks: {[f.name for f in context.frameworks]}")
print(f"Dependencies: {len(context.dependencies)}")
print(f"Architecture: {context.architecture_patterns}")
```

### Language Detection

```python
# Detect language for a project
language = analyzer.detect_language(Path("/path/to/project"))
print(f"Language: {language.name}")
print(f"Confidence: {language.confidence:.2%}")

# Detect language for a single file
file_language = analyzer.detect_language(Path("script.py"))
```

### Framework Detection

```python
# Detect frameworks
frameworks = analyzer.detect_framework(Path("/path/to/project"), "python")

for framework in frameworks:
    print(f"{framework.name} ({framework.category})")
    print(f"  Confidence: {framework.confidence:.2%}")
```

### Coding Conventions

```python
# Extract coding conventions
conventions = analyzer.extract_conventions(Path("/path/to/project"))

print(f"Indentation: {repr(conventions.indentation)}")
print(f"Quote style: {conventions.quote_style}")
print(f"Line length: {conventions.line_length}")

# Get naming conventions
naming = analyzer.detect_naming_conventions(Path("/path/to/project"))
print(f"Function naming: {naming['function']}")
print(f"Class naming: {naming['class']}")
```

### Import Pattern Analysis

```python
# Analyze import patterns
patterns = analyzer.analyze_import_patterns(Path("/path/to/project"))

print(f"Import styles: {patterns['import_styles']}")
print(f"Relative imports: {patterns['relative_imports']}")
print(f"Absolute imports: {patterns['absolute_imports']}")
print(f"Common imports: {patterns['common_imports'].most_common(5)}")
```

### Architecture Pattern Detection

```python
# Detect architecture patterns
patterns = analyzer.detect_architecture_patterns(Path("/path/to/project"))

for pattern in patterns:
    print(f"{pattern['name']}")
    print(f"  Confidence: {pattern['confidence']:.2%}")
    print(f"  Description: {pattern['description']}")
```

### Dependency Graph

```python
# Build dependency graph
graph = analyzer.build_dependency_graph(Path("/path/to/project"))

for module, dependencies in graph.items():
    print(f"{module}:")
    for dep in dependencies:
        print(f"  → {dep}")
```

### Code Similarity Search

```python
# Find similar code
code_snippet = """
def calculate_total(items):
    return sum(item.price for item in items)
"""

matches = analyzer.find_similar_code(
    code_snippet,
    Path("/path/to/project"),
    threshold=0.7
)

for match in matches:
    print(f"{match.file_path}:{match.line_number}")
    print(f"  Similarity: {match.similarity_score:.2%}")
```

### Project Statistics

```python
# Get comprehensive statistics
stats = analyzer.get_project_statistics(Path("/path/to/project"))

print(f"Total files: {stats['total_files']}")
print(f"Total lines: {stats['total_lines']:,}")
print(f"Total size: {stats['total_size'] / 1024 / 1024:.2f} MB")

print("\nLanguages:")
for lang, info in stats['languages'].items():
    print(f"  {lang}: {info['files']} files, {info['lines']:,} lines")

print("\nLargest files:")
for file_info in stats['largest_files'][:5]:
    print(f"  {file_info['path']}: {file_info['size'] / 1024:.2f} KB")
```

### Complete Coding Style Analysis

```python
# Comprehensive style analysis
style = analyzer.analyze_coding_style(Path("/path/to/project"))

print(f"Indentation: {repr(style['indentation'])}")
print(f"Quote style: {style['quote_style']}")
print(f"Line length: {style['line_length']}")

print("\nNaming conventions:")
for entity, convention in style['naming_conventions'].items():
    print(f"  {entity}: {convention}")

print("\nFormatting tools:")
for tool, enabled in style['formatting_rules'].items():
    if enabled:
        print(f"  ✓ {tool}")
```

## Data Models

### ProjectContext
Complete project information:
- `project_path`: Project root path
- `language`: Primary language
- `frameworks`: List of detected frameworks
- `conventions`: Coding conventions
- `dependencies`: Project dependencies
- `file_structure`: Directory tree
- `git_info`: Git repository info
- `architecture_patterns`: Detected patterns
- `entry_points`: Application entry points

### Language
Language information:
- `name`: Language name
- `version`: Version (if detected)
- `file_extensions`: Associated extensions
- `confidence`: Detection confidence (0.0-1.0)

### Framework
Framework information:
- `name`: Framework name
- `version`: Version (if detected)
- `category`: Category (web, testing, data, cli)
- `confidence`: Detection confidence (0.0-1.0)

### CodingConventions
Coding style information:
- `indentation`: Indentation string
- `quote_style`: "single" or "double"
- `line_length`: Preferred line length
- `naming_conventions`: Dict of naming styles
- `import_style`: Import organization style
- `docstring_style`: Docstring format
- `formatting_rules`: Formatter configurations

## Integration with Other Components

### File Creator
The Context Analyzer provides conventions to the File Creator:
```python
context = analyzer.analyze_project(project_path)
file_creator.set_conventions(context.conventions)
```

### Multi-File Editor
Ensures consistent edits across files:
```python
context = analyzer.analyze_project(project_path)
editor.apply_conventions(context.conventions)
```

### Project Scaffolder
Informs project structure decisions:
```python
context = analyzer.analyze_project(similar_project_path)
scaffolder.use_template_from_context(context)
```

## Performance Tips

1. **Sampling**: The analyzer samples files for convention detection (default: 20-30 files)
2. **Caching**: Results can be cached for repeated analysis
3. **Selective Analysis**: Use specific methods instead of full project analysis when possible
4. **Ignore Patterns**: Common directories are automatically skipped

## Best Practices

1. **Run Once**: Analyze the project once and reuse the context
2. **Update on Changes**: Re-analyze when project structure changes significantly
3. **Use Confidence Scores**: Check confidence before applying detected patterns
4. **Combine Results**: Use multiple detection methods for better accuracy

## Troubleshooting

### No Language Detected
- Ensure the project has source files
- Check that file extensions are recognized
- Verify the project path is correct

### Low Confidence Scores
- Small projects may have less data for analysis
- Mixed coding styles reduce confidence
- Consider manual configuration for edge cases

### Missing Frameworks
- Framework detection requires dependency files or imports
- Add framework indicators to improve detection
- Check that dependency files are in standard locations

## Examples

See the following files for complete examples:
- `demo_context_analyzer.py` - Comprehensive demonstration
- `test_context_analyzer_simple.py` - Unit tests and examples

## API Reference

### Main Methods

- `analyze_project(project_path)` - Complete project analysis
- `detect_language(path)` - Language detection
- `detect_framework(project_path, language)` - Framework detection
- `extract_conventions(project_path)` - Convention extraction
- `analyze_import_patterns(project_path)` - Import analysis
- `detect_naming_conventions(project_path)` - Naming detection
- `detect_architecture_patterns(project_path)` - Architecture detection
- `build_dependency_graph(project_path)` - Dependency graph
- `find_similar_code(snippet, project_path, threshold)` - Similarity search
- `analyze_module_complexity(project_path)` - Complexity analysis
- `get_project_statistics(project_path)` - Statistics
- `analyze_coding_style(project_path)` - Style analysis

## Future Enhancements

Planned improvements:
- Machine learning for pattern detection
- More language support
- Real-time analysis
- Incremental updates
- Custom analyzer plugins
