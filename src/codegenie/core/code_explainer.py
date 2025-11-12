"""
Code Explainer - Advanced code analysis and natural language explanation.

This module provides detailed code analysis and explanation capabilities:
- Step-by-step code analysis
- Natural language explanations
- Example generation with context
- Conceptual explanations
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class ExplanationStyle(Enum):
    """Style of code explanation."""
    BEGINNER = "beginner"  # Simple, educational
    INTERMEDIATE = "intermediate"  # Balanced detail
    EXPERT = "expert"  # Technical, concise
    TUTORIAL = "tutorial"  # Step-by-step guide


@dataclass
class CodeBlock:
    """Represents a block of code with metadata."""
    code: str
    line_start: int
    line_end: int
    block_type: str  # function, class, loop, conditional, etc.
    complexity: int = 0


@dataclass
class StepExplanation:
    """Explanation for a single step in code execution."""
    step_number: int
    code_line: str
    explanation: str
    variables_affected: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)


@dataclass
class CodeAnalysis:
    """Complete analysis of code."""
    overview: str
    blocks: List[CodeBlock] = field(default_factory=list)
    steps: List[StepExplanation] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_score: int = 0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ConceptExplanation:
    """Explanation of a programming concept."""
    concept: str
    definition: str
    examples: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"  # beginner, intermediate, advanced


class CodeExplainer:
    """
    Provides advanced code explanation and analysis.
    
    This class analyzes code and generates natural language explanations
    suitable for different audiences and purposes.
    """
    
    # Common programming concepts
    CONCEPTS = {
        "variable": ConceptExplanation(
            concept="Variable",
            definition="A named storage location that holds a value",
            examples=["x = 5", "name = 'John'"],
            related_concepts=["assignment", "data types"],
            difficulty="beginner"
        ),
        "function": ConceptExplanation(
            concept="Function",
            definition="A reusable block of code that performs a specific task",
            examples=["def greet(name):", "return value"],
            related_concepts=["parameters", "return values", "scope"],
            difficulty="beginner"
        ),
        "class": ConceptExplanation(
            concept="Class",
            definition="A blueprint for creating objects with attributes and methods",
            examples=["class Person:", "self.name = name"],
            related_concepts=["object", "inheritance", "encapsulation"],
            difficulty="intermediate"
        ),
        "loop": ConceptExplanation(
            concept="Loop",
            definition="A control structure that repeats a block of code",
            examples=["for i in range(10):", "while condition:"],
            related_concepts=["iteration", "break", "continue"],
            difficulty="beginner"
        ),
        "conditional": ConceptExplanation(
            concept="Conditional",
            definition="A control structure that executes code based on a condition",
            examples=["if x > 0:", "elif x == 0:", "else:"],
            related_concepts=["boolean logic", "comparison operators"],
            difficulty="beginner"
        ),
        "list_comprehension": ConceptExplanation(
            concept="List Comprehension",
            definition="A concise way to create lists based on existing lists",
            examples=["[x*2 for x in range(10)]", "[x for x in items if x > 0]"],
            related_concepts=["loops", "filtering", "mapping"],
            difficulty="intermediate"
        ),
        "decorator": ConceptExplanation(
            concept="Decorator",
            definition="A function that modifies the behavior of another function",
            examples=["@property", "@staticmethod", "@custom_decorator"],
            related_concepts=["higher-order functions", "closures"],
            difficulty="advanced"
        ),
        "context_manager": ConceptExplanation(
            concept="Context Manager",
            definition="An object that manages resources using 'with' statement",
            examples=["with open('file.txt') as f:", "with lock:"],
            related_concepts=["resource management", "exceptions"],
            difficulty="intermediate"
        ),
        "generator": ConceptExplanation(
            concept="Generator",
            definition="A function that yields values one at a time",
            examples=["yield value", "for item in generator():"],
            related_concepts=["iterators", "lazy evaluation"],
            difficulty="advanced"
        ),
        "exception": ConceptExplanation(
            concept="Exception Handling",
            definition="Mechanism to handle errors gracefully",
            examples=["try:", "except ValueError:", "finally:"],
            related_concepts=["error handling", "raise"],
            difficulty="intermediate"
        )
    }
    
    def __init__(self, style: ExplanationStyle = ExplanationStyle.INTERMEDIATE):
        """
        Initialize the Code Explainer.
        
        Args:
            style: Style of explanations to generate
        """
        self.style = style
    
    def analyze_code(self, code: str, language: str = "python") -> CodeAnalysis:
        """
        Perform comprehensive code analysis.
        
        Args:
            code: Source code to analyze
            language: Programming language
            
        Returns:
            CodeAnalysis with detailed analysis
        """
        analysis = CodeAnalysis(overview="")
        
        if language == "python":
            analysis = self._analyze_python_code(code)
        else:
            analysis.overview = f"Analysis for {language} is not yet implemented"
        
        return analysis
    
    def _analyze_python_code(self, code: str) -> CodeAnalysis:
        """Analyze Python code."""
        analysis = CodeAnalysis(overview="")
        
        try:
            tree = ast.parse(code)
            
            # Extract code blocks
            analysis.blocks = self._extract_code_blocks(tree, code)
            
            # Generate overview
            analysis.overview = self._generate_overview(tree, code)
            
            # Extract key concepts
            analysis.key_concepts = self._extract_concepts(tree, code)
            
            # Extract dependencies
            analysis.dependencies = self._extract_dependencies(tree)
            
            # Calculate complexity
            analysis.complexity_score = self._calculate_complexity(tree)
            
            # Generate recommendations
            analysis.recommendations = self._generate_recommendations(tree, code)
            
            # Generate step-by-step explanation
            analysis.steps = self._generate_step_by_step(tree, code)
            
        except SyntaxError as e:
            analysis.overview = f"Syntax error in code: {e}"
            logger.warning(f"Syntax error analyzing code: {e}")
        except Exception as e:
            analysis.overview = f"Error analyzing code: {e}"
            logger.error(f"Error analyzing code: {e}")
        
        return analysis
    
    def _extract_code_blocks(self, tree: ast.AST, code: str) -> List[CodeBlock]:
        """Extract logical code blocks."""
        blocks = []
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                blocks.append(CodeBlock(
                    code=self._get_node_code(node, lines),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    block_type="function",
                    complexity=self._calculate_node_complexity(node)
                ))
            elif isinstance(node, ast.ClassDef):
                blocks.append(CodeBlock(
                    code=self._get_node_code(node, lines),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    block_type="class",
                    complexity=self._calculate_node_complexity(node)
                ))
            elif isinstance(node, (ast.For, ast.While)):
                blocks.append(CodeBlock(
                    code=self._get_node_code(node, lines),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    block_type="loop",
                    complexity=self._calculate_node_complexity(node)
                ))
        
        return blocks
    
    def _get_node_code(self, node: ast.AST, lines: List[str]) -> str:
        """Get source code for an AST node."""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            start = node.lineno - 1
            end = node.end_lineno if node.end_lineno else node.lineno
            return '\n'.join(lines[start:end])
        return ""
    
    def _generate_overview(self, tree: ast.AST, code: str) -> str:
        """Generate high-level overview."""
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        
        lines = code.split('\n')
        non_empty = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        overview_parts = []
        
        if self.style == ExplanationStyle.BEGINNER:
            overview_parts.append("This code is a Python program.")
            overview_parts.append(f"It has {len(non_empty)} lines of code.")
            
            if functions:
                overview_parts.append(f"It defines {len(functions)} function(s) that perform specific tasks.")
            if classes:
                overview_parts.append(f"It defines {len(classes)} class(es) that represent objects.")
            if imports:
                overview_parts.append(f"It uses {len(imports)} external library/libraries.")
        
        elif self.style == ExplanationStyle.EXPERT:
            overview_parts.append(f"Python module with {len(functions)} functions, {len(classes)} classes.")
            if imports:
                overview_parts.append(f"Dependencies: {len(imports)} imports.")
        
        else:  # INTERMEDIATE or TUTORIAL
            overview_parts.append(f"This Python code contains {len(functions)} function(s) and {len(classes)} class(es).")
            
            if functions:
                func_names = [f.name for f in functions if isinstance(f, ast.FunctionDef)]
                overview_parts.append(f"Functions: {', '.join(func_names[:5])}")
            
            if classes:
                class_names = [c.name for c in classes if isinstance(c, ast.ClassDef)]
                overview_parts.append(f"Classes: {', '.join(class_names[:5])}")
        
        return " ".join(overview_parts)
    
    def _extract_concepts(self, tree: ast.AST, code: str) -> List[str]:
        """Extract programming concepts used."""
        concepts = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                concepts.add("function")
            elif isinstance(node, ast.ClassDef):
                concepts.add("class")
            elif isinstance(node, (ast.For, ast.While)):
                concepts.add("loop")
            elif isinstance(node, ast.If):
                concepts.add("conditional")
            elif isinstance(node, ast.ListComp):
                concepts.add("list_comprehension")
            elif isinstance(node, ast.With):
                concepts.add("context_manager")
            elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                concepts.add("generator")
            elif isinstance(node, ast.Try):
                concepts.add("exception")
            elif isinstance(node, ast.FunctionDef) and node.decorator_list:
                concepts.add("decorator")
        
        return list(concepts)
    
    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        """Extract imported dependencies."""
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)
        
        return dependencies
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate overall complexity score."""
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_node_complexity(self, node: ast.AST) -> int:
        """Calculate complexity for a specific node."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While)):
                complexity += 1
        
        return complexity
    
    def _generate_recommendations(self, tree: ast.AST, code: str) -> List[str]:
        """Generate code improvement recommendations."""
        recommendations = []
        
        # Check for long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        recommendations.append(
                            f"Function '{node.name}' is {length} lines long. "
                            "Consider breaking it into smaller functions."
                        )
        
        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    recommendations.append(
                        f"Add a docstring to {node.__class__.__name__.lower()} '{node.name}'"
                    )
        
        # Check for complex conditionals
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                complexity = self._calculate_node_complexity(node)
                if complexity > 5:
                    recommendations.append(
                        "Simplify complex conditional logic or extract to separate functions"
                    )
        
        return recommendations[:5]  # Limit to top 5
    
    def _generate_step_by_step(self, tree: ast.AST, code: str) -> List[StepExplanation]:
        """Generate step-by-step explanation."""
        steps = []
        lines = code.split('\n')
        step_num = 1
        
        # Only generate for tutorial style
        if self.style != ExplanationStyle.TUTORIAL:
            return steps
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            explanation = self._explain_line(stripped, i, tree)
            if explanation:
                steps.append(StepExplanation(
                    step_number=step_num,
                    code_line=stripped,
                    explanation=explanation
                ))
                step_num += 1
            
            if step_num > 20:  # Limit steps
                break
        
        return steps
    
    def _explain_line(self, line: str, line_num: int, tree: ast.AST) -> str:
        """Explain a single line of code."""
        # Import statement
        if line.startswith('import ') or line.startswith('from '):
            module = line.split()[1]
            return f"Import the '{module}' module to use its functionality"
        
        # Function definition
        if line.startswith('def '):
            match = re.match(r'def\s+(\w+)\s*\((.*?)\)', line)
            if match:
                func_name = match.group(1)
                params = match.group(2)
                if params:
                    return f"Define a function named '{func_name}' that takes parameters: {params}"
                else:
                    return f"Define a function named '{func_name}' with no parameters"
        
        # Class definition
        if line.startswith('class '):
            match = re.match(r'class\s+(\w+)', line)
            if match:
                class_name = match.group(1)
                return f"Define a class named '{class_name}'"
        
        # Assignment
        if '=' in line and not line.startswith('if') and not line.startswith('while'):
            parts = line.split('=', 1)
            var_name = parts[0].strip()
            value = parts[1].strip()
            return f"Assign the value {value} to variable '{var_name}'"
        
        # Return statement
        if line.startswith('return '):
            value = line[7:].strip()
            return f"Return the value: {value}"
        
        # If statement
        if line.startswith('if '):
            condition = line[3:].rstrip(':')
            return f"Check if the condition '{condition}' is true"
        
        # For loop
        if line.startswith('for '):
            return f"Start a loop: {line}"
        
        # While loop
        if line.startswith('while '):
            condition = line[6:].rstrip(':')
            return f"Loop while the condition '{condition}' is true"
        
        # Generic explanation
        return f"Execute: {line}"
    
    def explain_concept(self, concept: str) -> Optional[ConceptExplanation]:
        """
        Get explanation for a programming concept.
        
        Args:
            concept: Name of the concept
            
        Returns:
            ConceptExplanation if found, None otherwise
        """
        return self.CONCEPTS.get(concept.lower())
    
    def generate_tutorial(self, code: str) -> str:
        """
        Generate a tutorial-style explanation.
        
        Args:
            code: Code to explain
            
        Returns:
            Tutorial text
        """
        analysis = self.analyze_code(code)
        
        tutorial_lines = [
            "# Code Tutorial",
            "",
            "## Overview",
            analysis.overview,
            ""
        ]
        
        if analysis.key_concepts:
            tutorial_lines.append("## Key Concepts")
            tutorial_lines.append("")
            for concept in analysis.key_concepts:
                concept_exp = self.explain_concept(concept)
                if concept_exp:
                    tutorial_lines.append(f"### {concept_exp.concept}")
                    tutorial_lines.append(concept_exp.definition)
                    tutorial_lines.append("")
        
        if analysis.steps:
            tutorial_lines.append("## Step-by-Step Walkthrough")
            tutorial_lines.append("")
            for step in analysis.steps:
                tutorial_lines.append(f"**Step {step.step_number}:**")
                tutorial_lines.append(f"```python")
                tutorial_lines.append(step.code_line)
                tutorial_lines.append(f"```")
                tutorial_lines.append(step.explanation)
                tutorial_lines.append("")
        
        if analysis.recommendations:
            tutorial_lines.append("## Recommendations")
            tutorial_lines.append("")
            for rec in analysis.recommendations:
                tutorial_lines.append(f"- {rec}")
            tutorial_lines.append("")
        
        return "\n".join(tutorial_lines)
