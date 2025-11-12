#!/usr/bin/env python3
"""
Demo script for Documentation Generator.

This script demonstrates the documentation generation capabilities including:
- Docstring generation
- README generation
- API documentation
- Code explanation
- Documentation maintenance
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


def demo_docstring_generation():
    """Demonstrate docstring generation."""
    print("=" * 60)
    print("DEMO: Docstring Generation")
    print("=" * 60)
    
    generator = DocumentationGenerator(docstring_style=DocstringStyle.GOOGLE)
    
    # Sample function code
    sample_code = '''
def calculate_average(numbers, weights=None):
    if weights:
        return sum(n * w for n, w in zip(numbers, weights)) / sum(weights)
    return sum(numbers) / len(numbers)
'''
    
    print("\nOriginal Code:")
    print(sample_code)
    
    print("\nGenerated Docstring (Google Style):")
    docstring = generator.generate_docstring(sample_code, "calculate_average", "function")
    print(docstring)
    
    # Try NumPy style
    generator_numpy = DocumentationGenerator(docstring_style=DocstringStyle.NUMPY)
    print("\nGenerated Docstring (NumPy Style):")
    docstring_numpy = generator_numpy.generate_docstring(sample_code, "calculate_average", "function")
    print(docstring_numpy)


def demo_class_docstring():
    """Demonstrate class docstring generation."""
    print("\n" + "=" * 60)
    print("DEMO: Class Docstring Generation")
    print("=" * 60)
    
    generator = DocumentationGenerator(docstring_style=DocstringStyle.GOOGLE)
    
    sample_class = '''
class DataProcessor:
    def __init__(self, data, config=None):
        self.data = data
        self.config = config or {}
    
    def process(self):
        return [self.transform(item) for item in self.data]
    
    def transform(self, item):
        return item * 2
'''
    
    print("\nOriginal Class:")
    print(sample_class)
    
    print("\nGenerated Class Docstring:")
    docstring = generator.generate_docstring(sample_class, "DataProcessor", "class")
    print(docstring)


def demo_readme_generation():
    """Demonstrate README generation."""
    print("\n" + "=" * 60)
    print("DEMO: README Generation")
    print("=" * 60)
    
    generator = DocumentationGenerator()
    
    # Use current project as example
    project_path = Path(__file__).parent
    
    print(f"\nGenerating README for project: {project_path.name}")
    
    readme = generator.generate_readme(
        project_path,
        project_name="CodeGenie",
        description="An AI-powered coding assistant with advanced features"
    )
    
    print("\nGenerated README (first 1000 characters):")
    print(readme[:1000])
    print("...")


def demo_api_documentation():
    """Demonstrate API documentation generation."""
    print("\n" + "=" * 60)
    print("DEMO: API Documentation Generation")
    print("=" * 60)
    
    generator = DocumentationGenerator()
    
    # Create a sample module for documentation
    sample_module_path = Path(__file__).parent / "src" / "codegenie" / "core" / "file_creator.py"
    
    if sample_module_path.exists():
        print(f"\nGenerating API docs for: {sample_module_path.name}")
        
        api_doc = generator.generate_api_documentation(
            sample_module_path.parent,
            output_format=DocumentationFormat.MARKDOWN
        )
        
        print(f"\nAPI Documentation Title: {api_doc.title}")
        print(f"Number of modules documented: {len(api_doc.modules)}")
        
        if api_doc.modules:
            first_module = api_doc.modules[0]
            print(f"\nFirst Module: {first_module.name}")
            print(f"  Functions: {len(first_module.functions)}")
            print(f"  Classes: {len(first_module.classes)}")
            
            # Show formatted output (first 500 chars)
            formatted = generator.format_api_documentation(api_doc)
            print("\nFormatted API Documentation (excerpt):")
            print(formatted[:500])
            print("...")
    else:
        print(f"\nSample module not found: {sample_module_path}")


def demo_code_explanation():
    """Demonstrate code explanation."""
    print("\n" + "=" * 60)
    print("DEMO: Code Explanation")
    print("=" * 60)
    
    generator = DocumentationGenerator()
    
    sample_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
'''
    
    print("\nCode to Explain:")
    print(sample_code)
    
    print("\n--- Brief Explanation ---")
    explanation_brief = generator.explain_code(sample_code, detail_level="brief")
    print(explanation_brief)
    
    print("\n--- Standard Explanation ---")
    explanation_standard = generator.explain_code(sample_code, detail_level="standard")
    print(explanation_standard)
    
    print("\n--- Detailed Explanation ---")
    explanation_detailed = generator.explain_code(sample_code, detail_level="detailed")
    print(explanation_detailed)


def demo_example_generation():
    """Demonstrate example generation."""
    print("\n" + "=" * 60)
    print("DEMO: Example Generation")
    print("=" * 60)
    
    generator = DocumentationGenerator()
    
    sample_code = '''
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b

def format_result(value, precision=2):
    return f"{value:.{precision}f}"
'''
    
    print("\nCode:")
    print(sample_code)
    
    print("\nGenerated Examples:")
    examples = generator.generate_examples(sample_code, num_examples=3)
    
    for i, example in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(example)


def demo_code_explainer():
    """Demonstrate advanced code explainer."""
    print("\n" + "=" * 60)
    print("DEMO: Advanced Code Explainer")
    print("=" * 60)
    
    explainer = CodeExplainer(style=ExplanationStyle.INTERMEDIATE)
    
    sample_code = '''
def process_data(items):
    """Process a list of items."""
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result

data = [1, -2, 3, -4, 5]
processed = process_data(data)
'''
    
    print("\nCode to Analyze:")
    print(sample_code)
    
    print("\n--- Code Analysis ---")
    analysis = explainer.analyze_code(sample_code)
    
    print(f"\nOverview: {analysis.overview}")
    print(f"Complexity Score: {analysis.complexity_score}")
    print(f"Key Concepts: {', '.join(analysis.key_concepts)}")
    
    if analysis.blocks:
        print(f"\nCode Blocks Found: {len(analysis.blocks)}")
        for block in analysis.blocks:
            print(f"  - {block.block_type} (lines {block.line_start}-{block.line_end})")
    
    if analysis.recommendations:
        print("\nRecommendations:")
        for rec in analysis.recommendations:
            print(f"  - {rec}")


def demo_tutorial_generation():
    """Demonstrate tutorial generation."""
    print("\n" + "=" * 60)
    print("DEMO: Tutorial Generation")
    print("=" * 60)
    
    explainer = CodeExplainer(style=ExplanationStyle.TUTORIAL)
    
    sample_code = '''
import math

def calculate_circle_area(radius):
    return math.pi * radius ** 2

radius = 5
area = calculate_circle_area(radius)
print(f"Area: {area}")
'''
    
    print("\nCode:")
    print(sample_code)
    
    print("\n--- Generated Tutorial ---")
    tutorial = explainer.generate_tutorial(sample_code)
    print(tutorial)


def demo_doc_sync_check():
    """Demonstrate documentation sync checking."""
    print("\n" + "=" * 60)
    print("DEMO: Documentation Sync Check")
    print("=" * 60)
    
    generator = DocumentationGenerator()
    
    project_path = Path(__file__).parent / "src" / "codegenie" / "core"
    
    if project_path.exists():
        print(f"\nChecking documentation sync for: {project_path}")
        
        issues = generator.check_doc_sync(
            project_path,
            check_docstrings=True,
            check_readme=False
        )
        
        print(f"\nFound {len(issues)} documentation issue(s)")
        
        # Show first 5 issues
        for issue in issues[:5]:
            print(f"\n[{issue.severity.upper()}] {issue.issue_type}")
            print(f"  File: {issue.file_path.name}")
            print(f"  Description: {issue.description}")
            if issue.suggestion:
                print(f"  Suggestion: {issue.suggestion}")
    else:
        print(f"\nPath not found: {project_path}")


def demo_doc_validation():
    """Demonstrate documentation validation."""
    print("\n" + "=" * 60)
    print("DEMO: Documentation Validation")
    print("=" * 60)
    
    generator = DocumentationGenerator()
    
    project_path = Path(__file__).parent / "src" / "codegenie" / "core"
    
    if project_path.exists():
        print(f"\nValidating documentation for: {project_path}")
        
        report = generator.validate_documentation(project_path)
        
        print("\n--- Validation Report ---")
        print(f"Total Files: {report['total_files']}")
        print(f"Documented Functions: {report['documented_functions']}")
        print(f"Undocumented Functions: {report['undocumented_functions']}")
        print(f"Documented Classes: {report['documented_classes']}")
        print(f"Undocumented Classes: {report['undocumented_classes']}")
        print(f"Documentation Score: {report['score']:.1f}%")
        
        if report['issues']:
            print(f"\nTotal Issues: {len(report['issues'])}")
            print("(Use doc_sync_check demo to see details)")
    else:
        print(f"\nPath not found: {project_path}")


def demo_concept_explanation():
    """Demonstrate concept explanation."""
    print("\n" + "=" * 60)
    print("DEMO: Concept Explanation")
    print("=" * 60)
    
    explainer = CodeExplainer()
    
    concepts = ["function", "class", "decorator", "generator", "list_comprehension"]
    
    print("\nExplaining Programming Concepts:")
    
    for concept in concepts:
        concept_exp = explainer.explain_concept(concept)
        if concept_exp:
            print(f"\n--- {concept_exp.concept} ---")
            print(f"Definition: {concept_exp.definition}")
            print(f"Difficulty: {concept_exp.difficulty}")
            print(f"Examples: {', '.join(concept_exp.examples)}")
            if concept_exp.related_concepts:
                print(f"Related: {', '.join(concept_exp.related_concepts)}")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("DOCUMENTATION GENERATOR DEMO")
    print("=" * 60)
    
    demos = [
        ("Docstring Generation", demo_docstring_generation),
        ("Class Docstring", demo_class_docstring),
        ("README Generation", demo_readme_generation),
        ("API Documentation", demo_api_documentation),
        ("Code Explanation", demo_code_explanation),
        ("Example Generation", demo_example_generation),
        ("Advanced Code Explainer", demo_code_explainer),
        ("Tutorial Generation", demo_tutorial_generation),
        ("Doc Sync Check", demo_doc_sync_check),
        ("Doc Validation", demo_doc_validation),
        ("Concept Explanation", demo_concept_explanation),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
