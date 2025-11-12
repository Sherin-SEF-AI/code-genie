#!/usr/bin/env python3
"""
Demo script for Context Analyzer functionality.

This script demonstrates the Context Analyzer's capabilities:
- Language and framework detection
- Project structure analysis
- Coding convention extraction
- Import pattern analysis
- Architecture pattern detection
- Dependency graph construction
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.context_analyzer import ContextAnalyzer


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_basic_analysis():
    """Demonstrate basic project analysis."""
    print_section("Basic Project Analysis")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    print(f"\nAnalyzing project at: {project_path}")
    
    # Analyze the project
    context = analyzer.analyze_project(project_path)
    
    print(f"\n✓ Language: {context.language.name if context.language else 'Unknown'}")
    if context.language:
        print(f"  Confidence: {context.language.confidence:.2%}")
        print(f"  Extensions: {', '.join(context.language.file_extensions)}")
    
    print(f"\n✓ Frameworks detected: {len(context.frameworks)}")
    for framework in context.frameworks[:5]:
        print(f"  - {framework.name} ({framework.category}) - {framework.confidence:.2%}")
    
    print(f"\n✓ Dependencies: {len(context.dependencies)}")
    for dep in context.dependencies[:10]:
        print(f"  - {dep.name} {dep.version or ''} ({dep.source})")
    
    print(f"\n✓ Architecture patterns: {len(context.architecture_patterns)}")
    for pattern in context.architecture_patterns:
        print(f"  - {pattern}")
    
    if context.file_structure:
        print(f"\n✓ File structure:")
        print(f"  Total files: {context.file_structure.total_files}")
        print(f"  Total size: {context.file_structure.total_size / 1024:.2f} KB")
        print(f"  Directories: {len(context.file_structure.directories)}")
    
    if context.git_info and context.git_info.is_repo:
        print(f"\n✓ Git repository:")
        print(f"  Branch: {context.git_info.branch or 'Unknown'}")


def demo_language_detection():
    """Demonstrate language detection."""
    print_section("Language Detection")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    language = analyzer.detect_language(project_path)
    
    if language:
        print(f"\n✓ Detected language: {language.name}")
        print(f"  Confidence: {language.confidence:.2%}")
        print(f"  File extensions: {', '.join(language.file_extensions)}")
    else:
        print("\n✗ Could not detect language")


def demo_framework_detection():
    """Demonstrate framework detection."""
    print_section("Framework Detection")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    frameworks = analyzer.detect_framework(project_path, 'python')
    
    print(f"\n✓ Found {len(frameworks)} frameworks:")
    for framework in frameworks:
        print(f"\n  {framework.name}")
        print(f"    Category: {framework.category}")
        print(f"    Confidence: {framework.confidence:.2%}")


def demo_coding_conventions():
    """Demonstrate coding convention extraction."""
    print_section("Coding Conventions")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    conventions = analyzer.extract_conventions(project_path)
    
    print(f"\n✓ Indentation: {repr(conventions.indentation)}")
    print(f"✓ Quote style: {conventions.quote_style}")
    print(f"✓ Line length: {conventions.line_length}")
    
    print(f"\n✓ Naming conventions:")
    for entity_type, convention in conventions.naming_conventions.items():
        print(f"  {entity_type}: {convention}")


def demo_import_patterns():
    """Demonstrate import pattern analysis."""
    print_section("Import Pattern Analysis")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    patterns = analyzer.analyze_import_patterns(project_path)
    
    print(f"\n✓ Import styles:")
    for style, count in patterns['import_styles'].items():
        print(f"  {style}: {count}")
    
    print(f"\n✓ Relative imports: {patterns['relative_imports']}")
    print(f"✓ Absolute imports: {patterns['absolute_imports']}")
    
    print(f"\n✓ Most common imports:")
    for module, count in patterns['common_imports'].most_common(10):
        print(f"  {module}: {count}")


def demo_naming_conventions():
    """Demonstrate naming convention detection."""
    print_section("Naming Convention Detection")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    conventions = analyzer.detect_naming_conventions(project_path)
    
    print(f"\n✓ Detected naming conventions:")
    for entity_type, convention in conventions.items():
        print(f"  {entity_type}: {convention}")


def demo_architecture_patterns():
    """Demonstrate architecture pattern detection."""
    print_section("Architecture Pattern Detection")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    patterns = analyzer.detect_architecture_patterns(project_path)
    
    if patterns:
        print(f"\n✓ Detected {len(patterns)} architecture patterns:")
        for pattern in patterns:
            print(f"\n  {pattern['name']}")
            print(f"    Confidence: {pattern['confidence']:.2%}")
            print(f"    Description: {pattern['description']}")
    else:
        print("\n✓ No specific architecture patterns detected")


def demo_dependency_graph():
    """Demonstrate dependency graph construction."""
    print_section("Dependency Graph")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent / "src" / "codegenie"
    
    graph = analyzer.build_dependency_graph(project_path)
    
    print(f"\n✓ Built dependency graph with {len(graph)} modules")
    
    # Show a few examples
    print(f"\n✓ Sample dependencies:")
    for module, deps in list(graph.items())[:5]:
        print(f"\n  {module}:")
        for dep in deps[:5]:
            print(f"    → {dep}")


def demo_code_similarity():
    """Demonstrate code similarity search."""
    print_section("Code Similarity Search")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    # Search for a common pattern
    code_snippet = """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    """
    
    print(f"\n✓ Searching for similar code...")
    matches = analyzer.find_similar_code(code_snippet, project_path, threshold=0.5)
    
    print(f"\n✓ Found {len(matches)} similar code snippets:")
    for match in matches[:3]:
        print(f"\n  {match.file_path.name}:{match.line_number}")
        print(f"    Similarity: {match.similarity_score:.2%}")


def demo_project_statistics():
    """Demonstrate project statistics."""
    print_section("Project Statistics")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    stats = analyzer.get_project_statistics(project_path)
    
    print(f"\n✓ Total files: {stats['total_files']}")
    print(f"✓ Total lines: {stats['total_lines']:,}")
    print(f"✓ Total size: {stats['total_size'] / 1024 / 1024:.2f} MB")
    
    print(f"\n✓ Languages:")
    for lang, info in stats['languages'].items():
        print(f"  {lang}: {info['files']} files, {info['lines']:,} lines")
    
    print(f"\n✓ File types:")
    for ext, count in stats['file_types'].most_common(10):
        print(f"  {ext or 'no extension'}: {count}")
    
    print(f"\n✓ Largest files:")
    for file_info in stats['largest_files'][:5]:
        print(f"  {Path(file_info['path']).name}: {file_info['size'] / 1024:.2f} KB")
    
    print(f"\n✓ Most complex modules:")
    for module_info in stats['most_complex_modules'][:5]:
        print(f"  {module_info['module']}: complexity {module_info['complexity']}")


def demo_coding_style():
    """Demonstrate comprehensive coding style analysis."""
    print_section("Coding Style Analysis")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    style = analyzer.analyze_coding_style(project_path)
    
    print(f"\n✓ Indentation: {repr(style['indentation'])}")
    print(f"✓ Quote style: {style['quote_style']}")
    print(f"✓ Line length: {style['line_length']}")
    
    print(f"\n✓ Naming conventions:")
    for entity, convention in style['naming_conventions'].items():
        print(f"  {entity}: {convention}")
    
    print(f"\n✓ Formatting tools detected:")
    for tool, enabled in style['formatting_rules'].items():
        if enabled:
            print(f"  ✓ {tool}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  Context Analyzer Demo")
    print("=" * 60)
    
    demos = [
        ("Basic Analysis", demo_basic_analysis),
        ("Language Detection", demo_language_detection),
        ("Framework Detection", demo_framework_detection),
        ("Coding Conventions", demo_coding_conventions),
        ("Import Patterns", demo_import_patterns),
        ("Naming Conventions", demo_naming_conventions),
        ("Architecture Patterns", demo_architecture_patterns),
        ("Dependency Graph", demo_dependency_graph),
        ("Code Similarity", demo_code_similarity),
        ("Project Statistics", demo_project_statistics),
        ("Coding Style", demo_coding_style),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
