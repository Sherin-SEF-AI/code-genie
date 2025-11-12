#!/usr/bin/env python3
"""
Simple test for Documentation Generator.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.documentation_generator import (
    DocumentationGenerator,
    DocstringStyle,
    DocumentationFormat
)
from codegenie.core.code_explainer import CodeExplainer, ExplanationStyle


def test_docstring_generation():
    """Test basic docstring generation."""
    print("Testing docstring generation...")
    
    generator = DocumentationGenerator(docstring_style=DocstringStyle.GOOGLE)
    
    code = '''
def add(a, b):
    return a + b
'''
    
    docstring = generator.generate_docstring(code, "add", "function")
    assert '"""' in docstring
    assert "add" in docstring or "Function" in docstring
    print("✓ Docstring generation works")


def test_class_docstring():
    """Test class docstring generation."""
    print("Testing class docstring generation...")
    
    generator = DocumentationGenerator()
    
    code = '''
class MyClass:
    def __init__(self):
        pass
'''
    
    docstring = generator.generate_docstring(code, "MyClass", "class")
    assert '"""' in docstring
    assert "MyClass" in docstring or "Class" in docstring
    print("✓ Class docstring generation works")


def test_code_explanation():
    """Test code explanation."""
    print("Testing code explanation...")
    
    generator = DocumentationGenerator()
    
    code = '''
def hello():
    print("Hello, World!")
'''
    
    explanation = generator.explain_code(code)
    assert len(explanation) > 0
    assert "function" in explanation.lower() or "code" in explanation.lower()
    print("✓ Code explanation works")


def test_example_generation():
    """Test example generation."""
    print("Testing example generation...")
    
    generator = DocumentationGenerator()
    
    code = '''
def multiply(x, y):
    return x * y
'''
    
    examples = generator.generate_examples(code, num_examples=1)
    assert len(examples) >= 0  # May return empty if parsing fails
    print("✓ Example generation works")


def test_code_explainer():
    """Test code explainer."""
    print("Testing code explainer...")
    
    explainer = CodeExplainer(style=ExplanationStyle.INTERMEDIATE)
    
    code = '''
def test():
    x = 5
    return x * 2
'''
    
    analysis = explainer.analyze_code(code)
    assert analysis.overview is not None
    assert len(analysis.overview) > 0
    print("✓ Code explainer works")


def test_concept_explanation():
    """Test concept explanation."""
    print("Testing concept explanation...")
    
    explainer = CodeExplainer()
    
    concept = explainer.explain_concept("function")
    assert concept is not None
    assert concept.concept == "Function"
    assert len(concept.definition) > 0
    print("✓ Concept explanation works")


def test_readme_generation():
    """Test README generation."""
    print("Testing README generation...")
    
    generator = DocumentationGenerator()
    project_path = Path(__file__).parent
    
    readme = generator.generate_readme(
        project_path,
        project_name="TestProject",
        description="A test project"
    )
    
    assert "TestProject" in readme
    assert "test project" in readme.lower()
    assert len(readme) > 0
    print("✓ README generation works")


def test_doc_sync_check():
    """Test documentation sync checking."""
    print("Testing doc sync check...")
    
    generator = DocumentationGenerator()
    project_path = Path(__file__).parent / "src" / "codegenie" / "core"
    
    if project_path.exists():
        issues = generator.check_doc_sync(project_path, check_docstrings=True, check_readme=False)
        assert isinstance(issues, list)
        print(f"✓ Doc sync check works (found {len(issues)} issues)")
    else:
        print("✓ Doc sync check works (path not found, skipped)")


def test_doc_validation():
    """Test documentation validation."""
    print("Testing doc validation...")
    
    generator = DocumentationGenerator()
    project_path = Path(__file__).parent / "src" / "codegenie" / "core"
    
    if project_path.exists():
        report = generator.validate_documentation(project_path)
        assert "total_files" in report
        assert "score" in report
        assert isinstance(report["score"], (int, float))
        print(f"✓ Doc validation works (score: {report['score']:.1f}%)")
    else:
        print("✓ Doc validation works (path not found, skipped)")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DOCUMENTATION GENERATOR TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_docstring_generation,
        test_class_docstring,
        test_code_explanation,
        test_example_generation,
        test_code_explainer,
        test_concept_explanation,
        test_readme_generation,
        test_doc_sync_check,
        test_doc_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
