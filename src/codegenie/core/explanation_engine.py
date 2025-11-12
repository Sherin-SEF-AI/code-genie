"""
Code Explanation and Documentation Engine

This module provides comprehensive code explanation, trade-off analysis,
and automated documentation generation capabilities.
"""

import re
import ast
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..models.model_manager import ModelManager
from .code_generator import CodeLanguage, GeneratedCode
from ..utils.code_analyzer import CodeAnalyzer


class ExplanationLevel(Enum):
    """Level of detail for code explanations."""
    BRIEF = "brief"  # High-level overview
    STANDARD = "standard"  # Moderate detail
    DETAILED = "detailed"  # Comprehensive explanation
    EXPERT = "expert"  # Technical deep-dive


class DocumentationType(Enum):
    """Types of documentation that can be generated."""
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    INLINE_COMMENTS = "inline_comments"
    README = "readme"
    CHANGELOG = "changelog"


class ExplanationType(Enum):
    """Types of code explanations."""
    OVERVIEW = "overview"
    DETAILED = "detailed"
    STEP_BY_STEP = "step_by_step"
    CONCEPTUAL = "conceptual"


class TradeOffCategory(Enum):
    """Categories of trade-offs."""
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
    SECURITY = "security"
    COMPLEXITY = "complexity"


@dataclass
class CodeExplanation:
    """Represents an explanation of code."""
    code_snippet: str
    explanation: str
    level: ExplanationLevel
    key_concepts: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_analysis: Optional[str] = None
    performance_notes: Optional[str] = None
    security_notes: Optional[str] = None


@dataclass
class TradeOffAnalysis:
    """Analysis of implementation trade-offs."""
    approach: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    recommendation: Optional[str] = None
    use_cases: List[str] = field(default_factory=list)


@dataclass
class Documentation:
    """Generated documentation for code."""
    title: str
    content: str
    doc_type: DocumentationType
    sections: Dict[str, str] = field(default_factory=dict)
    code_examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractiveRefinement:
    """Represents an interactive refinement session."""
    session_id: str
    original_code: str
    current_code: str
    refinement_history: List[Dict[str, str]] = field(default_factory=list)
    user_feedback: List[str] = field(default_factory=list)
    iterations: int = 0


@dataclass
class ExplanationRequest:
    """Request for code explanation."""
    code: str
    language: CodeLanguage = CodeLanguage.PYTHON
    explanation_type: ExplanationType = ExplanationType.OVERVIEW
    level: ExplanationLevel = ExplanationLevel.STANDARD
    include_analysis: bool = True
    focus_areas: List[str] = field(default_factory=list)


@dataclass
class DocumentationRequest:
    """Request for documentation generation."""
    code: str
    doc_type: DocumentationType = DocumentationType.API_REFERENCE
    language: CodeLanguage = CodeLanguage.PYTHON
    include_examples: bool = True
    target_audience: str = "developers"
    sections: List[str] = field(default_factory=list)


class ExplanationEngine:
    """
    Engine for generating code explanations and documentation.
    
    This class provides comprehensive code explanation capabilities including
    trade-off analysis, documentation generation, and interactive refinement.
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager
        self.code_analyzer = CodeAnalyzer()
        self._explanation_templates = self._load_explanation_templates()
    
    def _load_explanation_templates(self) -> Dict[ExplanationLevel, str]:
        """Load templates for different explanation levels."""
        return {
            ExplanationLevel.BRIEF: """
Provide a brief, high-level explanation of this code in 2-3 sentences:

Code:
```
{code}
```

Brief Explanation:
""",
            ExplanationLevel.STANDARD: """
Explain this code with moderate detail:

Code:
```
{code}
```

Please include:
1. What the code does
2. Key components and their roles
3. Main logic flow

Explanation:
""",
            ExplanationLevel.DETAILED: """
Provide a comprehensive explanation of this code:

Code:
```
{code}
```

Please include:
1. Detailed description of functionality
2. Step-by-step logic breakdown
3. Data structures and algorithms used
4. Error handling approach
5. Performance considerations
6. Potential edge cases

Detailed Explanation:
""",
            ExplanationLevel.EXPERT: """
Provide an expert-level technical analysis of this code:

Code:
```
{code}
```

Please include:
1. Architectural patterns and design decisions
2. Algorithm complexity analysis (time and space)
3. Performance optimization opportunities
4. Security considerations
5. Scalability implications
6. Best practices adherence
7. Potential refactoring opportunities

Expert Analysis:
"""
        }
    
    async def explain_code(
        self,
        code: str,
        language: CodeLanguage = CodeLanguage.PYTHON,
        level: ExplanationLevel = ExplanationLevel.STANDARD,
        include_analysis: bool = True
    ) -> CodeExplanation:
        """
        Generate an explanation for the given code.
        
        Args:
            code: The code to explain
            language: Programming language of the code
            level: Level of detail for the explanation
            include_analysis: Whether to include complexity/performance analysis
            
        Returns:
            CodeExplanation with detailed explanation
        """
        # Get base explanation
        prompt = self._explanation_templates[level].format(code=code)
        
        try:
            explanation_text = await self.model_manager.generate_response(
                prompt=prompt,
                model_type="text_generation",
                max_tokens=1000 if level == ExplanationLevel.DETAILED else 500
            )
        except Exception:
            explanation_text = self._generate_basic_explanation(code, language)
        
        # Extract key concepts
        key_concepts = await self._extract_key_concepts(code, language)
        
        # Analyze dependencies
        dependencies = self._extract_dependencies(code, language)
        
        # Additional analysis if requested
        complexity_analysis = None
        performance_notes = None
        security_notes = None
        
        if include_analysis:
            complexity_analysis = await self._analyze_complexity(code, language)
            performance_notes = await self._analyze_performance(code, language)
            security_notes = await self._analyze_security(code, language)
        
        return CodeExplanation(
            code_snippet=code,
            explanation=explanation_text.strip(),
            level=level,
            key_concepts=key_concepts,
            dependencies=dependencies,
            complexity_analysis=complexity_analysis,
            performance_notes=performance_notes,
            security_notes=security_notes
        )
    
    def _generate_basic_explanation(self, code: str, language: CodeLanguage) -> str:
        """Generate a basic explanation without AI model."""
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        explanation_parts = [
            f"This {language.value} code consists of {len(non_empty_lines)} lines.",
        ]
        
        # Detect common patterns
        if 'def ' in code or 'function ' in code:
            explanation_parts.append("It defines one or more functions.")
        if 'class ' in code:
            explanation_parts.append("It defines one or more classes.")
        if 'import ' in code or 'require(' in code:
            explanation_parts.append("It imports external dependencies.")
        if 'try:' in code or 'try {' in code:
            explanation_parts.append("It includes error handling.")
        
        return " ".join(explanation_parts)
    
    async def _extract_key_concepts(self, code: str, language: CodeLanguage) -> List[str]:
        """Extract key programming concepts used in the code."""
        concepts = []
        
        # Pattern-based concept detection
        concept_patterns = {
            "Object-Oriented Programming": [r"class\s+\w+", r"self\.", r"this\."],
            "Functional Programming": [r"lambda\s+", r"map\(", r"filter\(", r"reduce\("],
            "Asynchronous Programming": [r"async\s+def", r"await\s+", r"Promise"],
            "Error Handling": [r"try:", r"except", r"catch", r"throw"],
            "Type Hints": [r"->\s*\w+", r":\s*\w+\s*="],
            "Decorators": [r"@\w+"],
            "List Comprehension": [r"\[.*for.*in.*\]"],
            "Context Managers": [r"with\s+\w+"],
            "Generators": [r"yield\s+"],
            "Regular Expressions": [r"re\.", r"regex", r"pattern"]
        }
        
        for concept, patterns in concept_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code):
                    concepts.append(concept)
                    break
        
        return concepts
    
    def _extract_dependencies(self, code: str, language: CodeLanguage) -> List[str]:
        """Extract dependencies from code."""
        dependencies = []
        
        if language == CodeLanguage.PYTHON:
            # Extract Python imports
            import_patterns = [
                r"^import\s+([^\s]+)",
                r"^from\s+([^\s]+)\s+import"
            ]
            for pattern in import_patterns:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    dependencies.append(match.group(1))
        
        elif language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
            # Extract JS/TS imports
            import_patterns = [
                r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
                r"require\(['\"]([^'\"]+)['\"]\)"
            ]
            for pattern in import_patterns:
                matches = re.finditer(pattern, code)
                for match in matches:
                    dependencies.append(match.group(1))
        
        return list(set(dependencies))
    
    async def _analyze_complexity(self, code: str, language: CodeLanguage) -> str:
        """Analyze code complexity."""
        if language != CodeLanguage.PYTHON:
            return "Complexity analysis only available for Python"
        
        try:
            tree = ast.parse(code)
            
            # Count various complexity metrics
            num_functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
            num_classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            num_loops = len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))])
            num_conditionals = len([n for n in ast.walk(tree) if isinstance(n, ast.If)])
            
            complexity_notes = []
            complexity_notes.append(f"Functions: {num_functions}")
            complexity_notes.append(f"Classes: {num_classes}")
            complexity_notes.append(f"Loops: {num_loops}")
            complexity_notes.append(f"Conditionals: {num_conditionals}")
            
            # Estimate cyclomatic complexity
            cyclomatic = 1 + num_loops + num_conditionals
            complexity_notes.append(f"Estimated Cyclomatic Complexity: {cyclomatic}")
            
            if cyclomatic > 10:
                complexity_notes.append("⚠️ High complexity - consider refactoring")
            
            return "\n".join(complexity_notes)
            
        except Exception:
            return "Unable to analyze complexity"
    
    async def _analyze_performance(self, code: str, language: CodeLanguage) -> str:
        """Analyze performance characteristics."""
        performance_notes = []
        
        # Check for common performance patterns
        if "for" in code and "for" in code:
            nested_loops = len(re.findall(r'for.*:\s*\n\s+.*for', code))
            if nested_loops > 0:
                performance_notes.append(f"⚠️ {nested_loops} nested loop(s) detected - O(n²) or higher complexity")
        
        if ".append(" in code and "for" in code:
            performance_notes.append("Consider list comprehension for better performance")
        
        if "+" in code and "str" in code.lower():
            performance_notes.append("String concatenation in loops - consider using join()")
        
        if not performance_notes:
            performance_notes.append("No obvious performance issues detected")
        
        return "\n".join(performance_notes)
    
    async def _analyze_security(self, code: str, language: CodeLanguage) -> str:
        """Analyze security considerations."""
        security_notes = []
        
        # Check for common security patterns
        if "eval(" in code:
            security_notes.append("⚠️ CRITICAL: eval() usage detected - major security risk")
        
        if "exec(" in code:
            security_notes.append("⚠️ CRITICAL: exec() usage detected - major security risk")
        
        if "pickle" in code:
            security_notes.append("⚠️ WARNING: pickle usage - ensure trusted data only")
        
        if "sql" in code.lower() and "+" in code:
            security_notes.append("⚠️ WARNING: Possible SQL injection risk - use parameterized queries")
        
        if "password" in code.lower() and "=" in code:
            security_notes.append("⚠️ WARNING: Hardcoded credentials detected")
        
        if not security_notes:
            security_notes.append("No obvious security issues detected")
        
        return "\n".join(security_notes)
    
    async def analyze_tradeoffs(
        self,
        code: str,
        requirement: str,
        language: CodeLanguage = CodeLanguage.PYTHON
    ) -> TradeOffAnalysis:
        """
        Analyze implementation trade-offs and alternatives.
        
        Args:
            code: The implemented code
            requirement: Original requirement
            language: Programming language
            
        Returns:
            TradeOffAnalysis with pros, cons, and alternatives
        """
        prompt = f"""
Analyze the trade-offs of this implementation:

Requirement: {requirement}

Implementation:
```{language.value}
{code}
```

Please provide:
1. Pros of this approach
2. Cons of this approach
3. Alternative approaches
4. Recommendation for when to use this approach
5. Specific use cases where this excels

Trade-off Analysis:
"""
        
        try:
            response = await self.model_manager.generate_response(
                prompt=prompt,
                model_type="text_generation",
                max_tokens=800
            )
            
            # Parse response into structured format
            analysis = self._parse_tradeoff_response(response)
            analysis.approach = "Current Implementation"
            
            return analysis
            
        except Exception:
            return self._generate_basic_tradeoff_analysis(code, language)
    
    def _parse_tradeoff_response(self, response: str) -> TradeOffAnalysis:
        """Parse AI response into TradeOffAnalysis structure."""
        analysis = TradeOffAnalysis(approach="Current Implementation")
        
        # Simple parsing - look for sections
        sections = {
            "pros": r"(?:Pros|Advantages):\s*(.*?)(?=\n\n|\n[A-Z]|$)",
            "cons": r"(?:Cons|Disadvantages):\s*(.*?)(?=\n\n|\n[A-Z]|$)",
            "alternatives": r"(?:Alternatives|Alternative Approaches):\s*(.*?)(?=\n\n|\n[A-Z]|$)",
            "recommendation": r"(?:Recommendation|When to Use):\s*(.*?)(?=\n\n|\n[A-Z]|$)",
            "use_cases": r"(?:Use Cases|Best For):\s*(.*?)(?=\n\n|\n[A-Z]|$)"
        }
        
        for field, pattern in sections.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Split by bullet points or newlines
                items = [item.strip() for item in re.split(r'[-•\n]+', content) if item.strip()]
                
                if field == "recommendation":
                    analysis.recommendation = items[0] if items else None
                else:
                    setattr(analysis, field, items)
        
        return analysis
    
    def _generate_basic_tradeoff_analysis(
        self,
        code: str,
        language: CodeLanguage
    ) -> TradeOffAnalysis:
        """Generate basic trade-off analysis without AI."""
        analysis = TradeOffAnalysis(approach="Current Implementation")
        
        # Generic pros
        analysis.pros = [
            "Implements the required functionality",
            f"Uses {language.value} standard practices"
        ]
        
        # Check for specific patterns
        if "class" in code:
            analysis.pros.append("Object-oriented design for maintainability")
        if "try:" in code or "try {" in code:
            analysis.pros.append("Includes error handling")
        
        # Generic cons
        analysis.cons = [
            "May need optimization for large-scale use",
            "Consider adding more comprehensive tests"
        ]
        
        # Generic alternatives
        analysis.alternatives = [
            "Consider alternative algorithms for better performance",
            "Evaluate different design patterns"
        ]
        
        analysis.recommendation = "Suitable for general use cases"
        
        return analysis
    
    async def generate_documentation(
        self,
        code: str,
        doc_type: DocumentationType = DocumentationType.API_REFERENCE,
        language: CodeLanguage = CodeLanguage.PYTHON,
        include_examples: bool = True
    ) -> Documentation:
        """
        Generate documentation for code.
        
        Args:
            code: Code to document
            doc_type: Type of documentation to generate
            language: Programming language
            include_examples: Whether to include usage examples
            
        Returns:
            Documentation object with generated content
        """
        prompt = self._create_documentation_prompt(code, doc_type, language, include_examples)
        
        try:
            content = await self.model_manager.generate_response(
                prompt=prompt,
                model_type="text_generation",
                max_tokens=1500
            )
            
            # Parse into sections
            sections = self._parse_documentation_sections(content)
            
            # Extract code examples
            code_examples = self._extract_code_examples(content)
            
            return Documentation(
                title=self._generate_doc_title(code, doc_type),
                content=content.strip(),
                doc_type=doc_type,
                sections=sections,
                code_examples=code_examples,
                metadata={
                    "language": language.value,
                    "generated_at": "now",
                    "includes_examples": include_examples
                }
            )
            
        except Exception:
            return self._generate_basic_documentation(code, doc_type, language)
    
    def _create_documentation_prompt(
        self,
        code: str,
        doc_type: DocumentationType,
        language: CodeLanguage,
        include_examples: bool
    ) -> str:
        """Create prompt for documentation generation."""
        base_prompt = f"""
Generate {doc_type.value.replace('_', ' ')} documentation for this {language.value} code:

```{language.value}
{code}
```
"""
        
        if doc_type == DocumentationType.API_REFERENCE:
            base_prompt += """
Include:
1. Overview
2. Functions/Methods with parameters and return values
3. Classes with attributes and methods
4. Usage examples
5. Error handling information
"""
        elif doc_type == DocumentationType.USER_GUIDE:
            base_prompt += """
Include:
1. Introduction
2. Getting Started
3. Basic Usage
4. Common Use Cases
5. Troubleshooting
"""
        elif doc_type == DocumentationType.DEVELOPER_GUIDE:
            base_prompt += """
Include:
1. Architecture Overview
2. Code Structure
3. Key Components
4. Extension Points
5. Development Workflow
"""
        elif doc_type == DocumentationType.README:
            base_prompt += """
Include:
1. Project Description
2. Installation
3. Quick Start
4. Features
5. Usage Examples
6. Contributing
"""
        
        if include_examples:
            base_prompt += "\nInclude practical code examples for each major feature.\n"
        
        base_prompt += "\nDocumentation:\n"
        
        return base_prompt
    
    def _parse_documentation_sections(self, content: str) -> Dict[str, str]:
        """Parse documentation content into sections."""
        sections = {}
        
        # Look for markdown headers
        section_pattern = r'^#+\s+(.+?)$\n(.*?)(?=^#+\s+|\Z)'
        matches = re.finditer(section_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            section_title = match.group(1).strip()
            section_content = match.group(2).strip()
            sections[section_title] = section_content
        
        return sections
    
    def _extract_code_examples(self, content: str) -> List[str]:
        """Extract code examples from documentation."""
        examples = []
        
        # Look for code blocks
        code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.finditer(code_block_pattern, content, re.DOTALL)
        
        for match in matches:
            examples.append(match.group(1).strip())
        
        return examples
    
    def _generate_doc_title(self, code: str, doc_type: DocumentationType) -> str:
        """Generate a title for the documentation."""
        # Try to extract main function/class name
        name_match = re.search(r'(?:def|class)\s+(\w+)', code)
        if name_match:
            name = name_match.group(1)
            return f"{name} - {doc_type.value.replace('_', ' ').title()}"
        
        return f"Code Documentation - {doc_type.value.replace('_', ' ').title()}"
    
    def _generate_basic_documentation(
        self,
        code: str,
        doc_type: DocumentationType,
        language: CodeLanguage
    ) -> Documentation:
        """Generate basic documentation without AI."""
        title = self._generate_doc_title(code, doc_type)
        
        content_parts = [
            f"# {title}\n",
            f"## Overview\n",
            f"This {language.value} code provides the following functionality:\n",
            f"```{language.value}\n{code}\n```\n",
            f"## Usage\n",
            f"See the code above for implementation details.\n"
        ]
        
        content = "\n".join(content_parts)
        
        return Documentation(
            title=title,
            content=content,
            doc_type=doc_type,
            sections={"Overview": "See code", "Usage": "See code"},
            metadata={"language": language.value}
        )
    
    async def interactive_refinement(
        self,
        code: str,
        feedback: str,
        session: Optional[InteractiveRefinement] = None
    ) -> InteractiveRefinement:
        """
        Refine code based on user feedback interactively.
        
        Args:
            code: Current code
            feedback: User feedback for refinement
            session: Existing refinement session to continue
            
        Returns:
            Updated InteractiveRefinement session
        """
        if session is None:
            session = InteractiveRefinement(
                session_id=f"refine_{id(code)}",
                original_code=code,
                current_code=code
            )
        
        # Generate refined code based on feedback
        refinement_prompt = f"""
Refine this code based on user feedback:

Current Code:
```
{session.current_code}
```

User Feedback: {feedback}

Please provide the refined code that addresses the feedback while maintaining functionality:

Refined Code:
"""
        
        try:
            response = await self.model_manager.generate_response(
                prompt=refinement_prompt,
                model_type="code_generation",
                max_tokens=1500
            )
            
            # Extract refined code
            code_match = re.search(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                refined_code = code_match.group(1).strip()
                
                # Update session
                session.refinement_history.append({
                    "iteration": session.iterations + 1,
                    "feedback": feedback,
                    "previous_code": session.current_code,
                    "refined_code": refined_code
                })
                session.current_code = refined_code
                session.user_feedback.append(feedback)
                session.iterations += 1
            
        except Exception:
            # If refinement fails, keep current code
            pass
        
        return session
    
    def get_refinement_summary(self, session: InteractiveRefinement) -> str:
        """Get a summary of the refinement session."""
        lines = [
            f"=== Refinement Session Summary ===",
            f"Session ID: {session.session_id}",
            f"Total Iterations: {session.iterations}",
            f"Feedback Items: {len(session.user_feedback)}",
            ""
        ]
        
        if session.refinement_history:
            lines.append("Refinement History:")
            for item in session.refinement_history:
                lines.append(f"  Iteration {item['iteration']}: {item['feedback']}")
        
        return "\n".join(lines)
