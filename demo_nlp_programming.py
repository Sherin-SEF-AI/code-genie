"""
Demo: Natural Language Programming Interface

This demo showcases the natural language programming capabilities including:
- NLP-driven code generation from natural language requirements
- Automatic requirement clarification
- Code explanation and documentation generation
- Interactive refinement workflows
"""

import asyncio
from pathlib import Path

from src.codegenie.core.nlp_code_generator import NLPCodeGenerator
from src.codegenie.core.code_generator import CodeLanguage, GenerationStrategy
from src.codegenie.core.explanation_engine import (
    ExplanationEngine, ExplanationLevel, DocumentationType
)


async def demo_simple_code_generation():
    """Demo: Generate code from simple natural language requirement."""
    print("=" * 80)
    print("DEMO 1: Simple Code Generation from Natural Language")
    print("=" * 80)
    
    generator = NLPCodeGenerator(model_manager=None)
    
    requirement = "Create a function named calculate_area that takes radius as a float parameter and returns the area of a circle"
    
    print(f"\nRequirement: {requirement}\n")
    
    result = await generator.generate_from_natural_language(
        requirement=requirement,
        language=CodeLanguage.PYTHON,
        auto_clarify=True,
        execute_validation=True,
        include_tests=True
    )
    
    print(f"Success: {result.success}")
    print(f"Confidence Score: {result.requirement_analysis.confidence_score:.2f}")
    
    if result.generated_code:
        print(f"\nGenerated Code:\n{'-' * 40}")
        print(result.generated_code.code)
        print("-" * 40)
        
        if result.generated_code.tests:
            print(f"\nGenerated Tests:\n{'-' * 40}")
            print(result.generated_code.tests)
            print("-" * 40)
    
    if result.execution_test:
        print(f"\nExecution Test: {'PASSED' if result.execution_test.success else 'FAILED'}")
    
    print()


async def demo_clarification_workflow():
    """Demo: Code generation with clarification workflow."""
    print("=" * 80)
    print("DEMO 2: Code Generation with Clarification")
    print("=" * 80)
    
    generator = NLPCodeGenerator(model_manager=None)
    
    # Ambiguous requirement that needs clarification
    requirement = "Create a function that processes data efficiently"
    
    print(f"\nRequirement: {requirement}\n")
    
    result = await generator.generate_from_natural_language(
        requirement=requirement,
        language=CodeLanguage.PYTHON,
        auto_clarify=False,  # Don't auto-answer
        execute_validation=False
    )
    
    if result.clarification_session and result.clarification_session.questions:
        print(f"Clarification Questions ({len(result.clarification_session.questions)}):")
        for i, question in enumerate(result.clarification_session.questions[:3], 1):
            print(f"  {i}. {question.question}")
            if question.possible_answers:
                print(f"     Options: {', '.join(question.possible_answers[:3])}")
        print()
    
    # Now generate with auto-clarification
    print("Generating with automatic clarification...\n")
    
    result = await generator.generate_from_natural_language(
        requirement=requirement,
        language=CodeLanguage.PYTHON,
        auto_clarify=True,
        execute_validation=False
    )
    
    if result.generated_code:
        print(f"Generated Code:\n{'-' * 40}")
        print(result.generated_code.code[:300] + "..." if len(result.generated_code.code) > 300 else result.generated_code.code)
        print("-" * 40)
    
    print()


async def demo_code_explanation():
    """Demo: Code explanation at different levels."""
    print("=" * 80)
    print("DEMO 3: Code Explanation")
    print("=" * 80)
    
    explainer = ExplanationEngine(model_manager=None)
    
    code = """
def fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number using recursion.\"\"\"
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    print(f"Code to Explain:\n{'-' * 40}")
    print(code)
    print("-" * 40)
    
    # Brief explanation
    print("\n1. BRIEF Explanation:")
    explanation = await explainer.explain_code(
        code=code,
        language=CodeLanguage.PYTHON,
        level=ExplanationLevel.BRIEF,
        include_analysis=False
    )
    print(f"   {explanation.explanation}")
    
    # Standard explanation with analysis
    print("\n2. STANDARD Explanation with Analysis:")
    explanation = await explainer.explain_code(
        code=code,
        language=CodeLanguage.PYTHON,
        level=ExplanationLevel.STANDARD,
        include_analysis=True
    )
    print(f"   {explanation.explanation}")
    
    if explanation.key_concepts:
        print(f"\n   Key Concepts: {', '.join(explanation.key_concepts)}")
    
    if explanation.complexity_analysis:
        print(f"\n   Complexity Analysis:")
        for line in explanation.complexity_analysis.split('\n'):
            print(f"   {line}")
    
    if explanation.performance_notes:
        print(f"\n   Performance Notes:")
        for line in explanation.performance_notes.split('\n'):
            print(f"   {line}")
    
    print()


async def demo_tradeoff_analysis():
    """Demo: Trade-off analysis of implementation."""
    print("=" * 80)
    print("DEMO 4: Trade-off Analysis")
    print("=" * 80)
    
    explainer = ExplanationEngine(model_manager=None)
    
    code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"""
    
    print(f"Code:\n{'-' * 40}")
    print(code)
    print("-" * 40)
    
    analysis = await explainer.analyze_tradeoffs(
        code=code,
        requirement="Sort an array of numbers",
        language=CodeLanguage.PYTHON
    )
    
    print(f"\nApproach: {analysis.approach}")
    
    if analysis.pros:
        print(f"\nPros:")
        for pro in analysis.pros:
            print(f"  ✓ {pro}")
    
    if analysis.cons:
        print(f"\nCons:")
        for con in analysis.cons:
            print(f"  ✗ {con}")
    
    if analysis.alternatives:
        print(f"\nAlternatives:")
        for alt in analysis.alternatives:
            print(f"  → {alt}")
    
    if analysis.recommendation:
        print(f"\nRecommendation: {analysis.recommendation}")
    
    print()


async def demo_documentation_generation():
    """Demo: Automatic documentation generation."""
    print("=" * 80)
    print("DEMO 5: Documentation Generation")
    print("=" * 80)
    
    explainer = ExplanationEngine(model_manager=None)
    
    code = """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def get_history(self):
        return self.history
"""
    
    print(f"Code:\n{'-' * 40}")
    print(code)
    print("-" * 40)
    
    # Generate API Reference
    doc = await explainer.generate_documentation(
        code=code,
        doc_type=DocumentationType.API_REFERENCE,
        language=CodeLanguage.PYTHON,
        include_examples=True
    )
    
    print(f"\nGenerated Documentation ({doc.doc_type.value}):")
    print("-" * 40)
    print(doc.content[:500] + "..." if len(doc.content) > 500 else doc.content)
    print("-" * 40)
    
    if doc.sections:
        print(f"\nSections: {', '.join(doc.sections.keys())}")
    
    print()


async def demo_interactive_refinement():
    """Demo: Interactive code refinement."""
    print("=" * 80)
    print("DEMO 6: Interactive Code Refinement")
    print("=" * 80)
    
    explainer = ExplanationEngine(model_manager=None)
    
    initial_code = """
def divide(a, b):
    return a / b
"""
    
    print(f"Initial Code:\n{'-' * 40}")
    print(initial_code)
    print("-" * 40)
    
    # First refinement
    print("\nUser Feedback 1: Add error handling for division by zero")
    session = await explainer.interactive_refinement(
        code=initial_code,
        feedback="Add error handling for division by zero"
    )
    
    print(f"Iterations: {session.iterations}")
    print(f"Current Code:\n{'-' * 40}")
    print(session.current_code[:200] + "..." if len(session.current_code) > 200 else session.current_code)
    print("-" * 40)
    
    # Second refinement
    print("\nUser Feedback 2: Add type hints")
    session = await explainer.interactive_refinement(
        code=session.current_code,
        feedback="Add type hints",
        session=session
    )
    
    print(f"Iterations: {session.iterations}")
    
    # Get summary
    summary = explainer.get_refinement_summary(session)
    print(f"\n{summary}")
    
    print()


async def demo_batch_generation():
    """Demo: Batch code generation."""
    print("=" * 80)
    print("DEMO 7: Batch Code Generation")
    print("=" * 80)
    
    generator = NLPCodeGenerator(model_manager=None)
    
    requirements = [
        "Create a function to check if a number is prime",
        "Create a function to reverse a string",
        "Create a function to find the maximum value in a list"
    ]
    
    print("Requirements:")
    for i, req in enumerate(requirements, 1):
        print(f"  {i}. {req}")
    
    print("\nGenerating code for all requirements...\n")
    
    results = await generator.batch_generate(
        requirements=requirements,
        language=CodeLanguage.PYTHON
    )
    
    print(f"Generated {len(results)} code implementations:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Requirement: {requirements[i-1]}")
        print(f"   Success: {result.success}")
        print(f"   Confidence: {result.requirement_analysis.confidence_score:.2f}")
        if result.generated_code:
            code_preview = result.generated_code.code[:100].replace('\n', ' ')
            print(f"   Code Preview: {code_preview}...")
    
    print()


async def demo_generation_summary():
    """Demo: Generation summary and reporting."""
    print("=" * 80)
    print("DEMO 8: Generation Summary")
    print("=" * 80)
    
    generator = NLPCodeGenerator(model_manager=None)
    
    requirement = "Create a class named User with name and email attributes, and a method to validate email"
    
    print(f"Requirement: {requirement}\n")
    
    result = await generator.generate_from_natural_language(
        requirement=requirement,
        language=CodeLanguage.PYTHON,
        auto_clarify=True,
        execute_validation=True
    )
    
    # Get comprehensive summary
    summary = generator.get_generation_summary(result)
    
    print(summary)
    print()


async def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "NATURAL LANGUAGE PROGRAMMING DEMO" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    demos = [
        ("Simple Code Generation", demo_simple_code_generation),
        ("Clarification Workflow", demo_clarification_workflow),
        ("Code Explanation", demo_code_explanation),
        ("Trade-off Analysis", demo_tradeoff_analysis),
        ("Documentation Generation", demo_documentation_generation),
        ("Interactive Refinement", demo_interactive_refinement),
        ("Batch Generation", demo_batch_generation),
        ("Generation Summary", demo_generation_summary),
    ]
    
    for name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            print(f"Error in {name}: {e}")
            import traceback
            traceback.print_exc()
        
        input("Press Enter to continue to next demo...")
        print("\n")
    
    print("=" * 80)
    print("All demos completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
