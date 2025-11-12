#!/usr/bin/env python3
"""
Simple test for Context Analyzer functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import only the context analyzer
from codegenie.core.context_analyzer import (
    ContextAnalyzer,
    Language,
    Framework,
    CodingConventions,
    ProjectContext
)


def test_language_detection():
    """Test language detection."""
    print("\n=== Testing Language Detection ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    language = analyzer.detect_language(project_path)
    
    assert language is not None, "Should detect a language"
    assert language.name == "python", f"Expected python, got {language.name}"
    assert language.confidence > 0, "Confidence should be positive"
    
    print(f"✓ Detected language: {language.name}")
    print(f"✓ Confidence: {language.confidence:.2%}")
    print(f"✓ Extensions: {language.file_extensions}")


def test_framework_detection():
    """Test framework detection."""
    print("\n=== Testing Framework Detection ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    frameworks = analyzer.detect_framework(project_path, 'python')
    
    print(f"✓ Found {len(frameworks)} frameworks")
    for framework in frameworks[:5]:
        print(f"  - {framework.name} ({framework.category})")


def test_conventions():
    """Test coding convention extraction."""
    print("\n=== Testing Coding Conventions ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    conventions = analyzer.extract_conventions(project_path)
    
    assert conventions is not None, "Should extract conventions"
    assert conventions.indentation, "Should detect indentation"
    
    print(f"✓ Indentation: {repr(conventions.indentation)}")
    print(f"✓ Quote style: {conventions.quote_style}")
    print(f"✓ Line length: {conventions.line_length}")


def test_naming_conventions():
    """Test naming convention detection."""
    print("\n=== Testing Naming Conventions ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    conventions = analyzer.detect_naming_conventions(project_path)
    
    assert conventions, "Should detect naming conventions"
    assert 'function' in conventions, "Should detect function naming"
    
    print(f"✓ Detected naming conventions:")
    for entity_type, convention in conventions.items():
        print(f"  {entity_type}: {convention}")


def test_import_patterns():
    """Test import pattern analysis."""
    print("\n=== Testing Import Patterns ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    patterns = analyzer.analyze_import_patterns(project_path)
    
    assert patterns, "Should analyze import patterns"
    assert 'import_styles' in patterns, "Should detect import styles"
    
    print(f"✓ Import styles found: {len(patterns['import_styles'])}")
    print(f"✓ Relative imports: {patterns['relative_imports']}")
    print(f"✓ Absolute imports: {patterns['absolute_imports']}")


def test_architecture_patterns():
    """Test architecture pattern detection."""
    print("\n=== Testing Architecture Patterns ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    patterns = analyzer.detect_architecture_patterns(project_path)
    
    print(f"✓ Detected {len(patterns)} architecture patterns")
    for pattern in patterns:
        print(f"  - {pattern['name']} ({pattern['confidence']:.2%})")


def test_dependency_graph():
    """Test dependency graph construction."""
    print("\n=== Testing Dependency Graph ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent / "src" / "codegenie" / "core"
    
    if project_path.exists():
        graph = analyzer.build_dependency_graph(project_path)
        
        print(f"✓ Built dependency graph with {len(graph)} modules")
        
        # Show a sample
        for module, deps in list(graph.items())[:3]:
            print(f"  {module}: {len(deps)} dependencies")
    else:
        print("✓ Skipping (path not found)")


def test_project_analysis():
    """Test complete project analysis."""
    print("\n=== Testing Complete Project Analysis ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    context = analyzer.analyze_project(project_path)
    
    assert context is not None, "Should analyze project"
    assert context.project_path == project_path, "Should set project path"
    
    print(f"✓ Project path: {context.project_path}")
    print(f"✓ Language: {context.language.name if context.language else 'Unknown'}")
    print(f"✓ Frameworks: {len(context.frameworks)}")
    print(f"✓ Dependencies: {len(context.dependencies)}")
    print(f"✓ Architecture patterns: {len(context.architecture_patterns)}")
    
    if context.file_structure:
        print(f"✓ Total files: {context.file_structure.total_files}")


def test_project_statistics():
    """Test project statistics."""
    print("\n=== Testing Project Statistics ===")
    
    analyzer = ContextAnalyzer()
    project_path = Path(__file__).parent
    
    stats = analyzer.get_project_statistics(project_path)
    
    assert stats, "Should generate statistics"
    assert stats['total_files'] > 0, "Should count files"
    
    print(f"✓ Total files: {stats['total_files']}")
    print(f"✓ Total lines: {stats['total_lines']:,}")
    print(f"✓ Languages: {len(stats['languages'])}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  Context Analyzer Tests")
    print("=" * 60)
    
    tests = [
        test_language_detection,
        test_framework_detection,
        test_conventions,
        test_naming_conventions,
        test_import_patterns,
        test_architecture_patterns,
        test_dependency_graph,
        test_project_analysis,
        test_project_statistics,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
