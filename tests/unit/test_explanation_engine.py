"""
Unit tests for Explanation Engine.

Tests code explanation, trade-off analysis, documentation generation,
and interactive refinement capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.codegenie.core.explanation_engine import (
    ExplanationEngine, CodeExplanation, TradeOffAnalysis, Documentation,
    InteractiveRefinement, ExplanationLevel, DocumentationType
)
from src.codegenie.core.code_generator import CodeLanguage, GeneratedCode
from src.codegenie.models.model_manager import ModelManager


class TestExplanationEngine:
    """Test suite for Explanation Engine."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        mock_manager = Mock(spec=ModelManager)
        mock_manager.generate_response = AsyncMock(return_value="Generated explanation")
        return mock_manager
    
    @pytest.fixture
    def explanation_engine(self, mock_model_manager):
        """Create explanation engine with mock model manager."""
        return ExplanationEngine(mock_model_manager)
    
    @pytest.fixture
    def explanation_engine_no_model(self):
        """Create explanation engine without model manager."""
        return ExplanationEngine(None)
    
    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing."""
        return """
def calculate_fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number.\"\"\"
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""
    
    @pytest.fixture
    def sample_class_code(self):
        """Sample class code for testing."""
        return """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
"""
    
    @pytest.mark.asyncio
    async def test_explain_code_brief(self, explanation_engine, sample_python_code):
        """Test brief code explanation."""
        explanation = await explanation_engine.explain_code(
            code=sample_python_code,
            language=CodeLanguage.PYTHON,
            level=ExplanationLevel.BRIEF,
            include_analysis=False
        )
        
        assert isinstance(explanation, CodeExplanation)
        assert explanation.code_snippet == sample_python_code
        assert explanation.level == ExplanationLevel.BRIEF
        assert len(explanation.explanation) > 0
    
    @pytest.mark.asyncio
    async def test_explain_code_standard(self, explanation_engine, sample_python_code):
        """Test standard code explanation."""
        explanation = await explanation_engine.explain_code(
            code=sample_python_code,
            language=CodeLanguage.PYTHON,
            level=ExplanationLevel.STANDARD,
            include_analysis=True
        )
        
        assert isinstance(explanation, CodeExplanation)
        assert explanation.level == ExplanationLevel.STANDARD
        assert explanation.complexity_analysis is not None
        assert explanation.performance_notes is not None
        assert explanation.security_notes is not None
    
    @pytest.mark.asyncio
    async def test_explain_code_detailed(self, explanation_engine, sample_python_code):
        """Test detailed code explanation."""
        explanation = await explanation_engine.explain_code(
            code=sample_python_code,
            language=CodeLanguage.PYTHON,
            level=ExplanationLevel.DETAILED,
            include_analysis=True
        )
        
        assert isinstance(explanation, CodeExplanation)
        assert explanation.level == ExplanationLevel.DETAILED
        assert len(explanation.key_concepts) > 0
    
    @pytest.mark.asyncio
    async def test_explain_code_expert(self, explanation_engine, sample_python_code):
        """Test expert-level code explanation."""
        explanation = await explanation_engine.explain_code(
            code=sample_python_code,
            language=CodeLanguage.PYTHON,
            level=ExplanationLevel.EXPERT,
            include_analysis=True
        )
        
        assert isinstance(explanation, CodeExplanation)
        assert explanation.level == ExplanationLevel.EXPERT
    
    @pytest.mark.asyncio
    async def test_explain_code_without_model(self, explanation_engine_no_model, sample_python_code):
        """Test code explanation without AI model."""
        explanation = await explanation_engine_no_model.explain_code(
            code=sample_python_code,
            language=CodeLanguage.PYTHON,
            level=ExplanationLevel.STANDARD,
            include_analysis=False
        )
        
        assert isinstance(explanation, CodeExplanation)
        # Should use basic explanation
        assert "python" in explanation.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_extract_key_concepts(self, explanation_engine_no_model, sample_python_code):
        """Test extraction of key programming concepts."""
        concepts = await explanation_engine_no_model._extract_key_concepts(
            sample_python_code,
            CodeLanguage.PYTHON
        )
        
        assert isinstance(concepts, list)
        # Recursive function should be detected
        assert any("recursive" in c.lower() or "function" in c.lower() for c in concepts)
    
    @pytest.mark.asyncio
    async def test_extract_key_concepts_oop(self, explanation_engine_no_model, sample_class_code):
        """Test extraction of OOP concepts."""
        concepts = await explanation_engine_no_model._extract_key_concepts(
            sample_class_code,
            CodeLanguage.PYTHON
        )
        
        assert isinstance(concepts, list)
        assert "Object-Oriented Programming" in concepts
    
    def test_extract_dependencies_python(self, explanation_engine_no_model):
        """Test extraction of Python dependencies."""
        code = """
import os
import sys
from pathlib import Path
from typing import List, Dict
"""
        
        dependencies = explanation_engine_no_model._extract_dependencies(
            code,
            CodeLanguage.PYTHON
        )
        
        assert "os" in dependencies
        assert "sys" in dependencies
        assert "pathlib" in dependencies
        assert "typing" in dependencies
    
    def test_extract_dependencies_javascript(self, explanation_engine_no_model):
        """Test extraction of JavaScript dependencies."""
        code = """
import { useState } from 'react';
import axios from 'axios';
const fs = require('fs');
"""
        
        dependencies = explanation_engine_no_model._extract_dependencies(
            code,
            CodeLanguage.JAVASCRIPT
        )
        
        assert "react" in dependencies
        assert "axios" in dependencies
        assert "fs" in dependencies
    
    @pytest.mark.asyncio
    async def test_analyze_complexity(self, explanation_engine_no_model, sample_python_code):
        """Test complexity analysis."""
        complexity = await explanation_engine_no_model._analyze_complexity(
            sample_python_code,
            CodeLanguage.PYTHON
        )
        
        assert isinstance(complexity, str)
        assert "Functions:" in complexity
        assert "Cyclomatic Complexity" in complexity
    
    @pytest.mark.asyncio
    async def test_analyze_complexity_high(self, explanation_engine_no_model):
        """Test complexity analysis with high complexity code."""
        complex_code = """
def complex_function(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                for j in range(i):
                    if j > 5:
                        while j < 10:
                            if j == 7:
                                pass
                            j += 1
"""
        
        complexity = await explanation_engine_no_model._analyze_complexity(
            complex_code,
            CodeLanguage.PYTHON
        )
        
        assert "⚠️" in complexity or "High complexity" in complexity
    
    @pytest.mark.asyncio
    async def test_analyze_performance(self, explanation_engine_no_model):
        """Test performance analysis."""
        code_with_nested_loops = """
def process_matrix(matrix):
    for row in matrix:
        for col in row:
            result = col * 2
"""
        
        performance = await explanation_engine_no_model._analyze_performance(
            code_with_nested_loops,
            CodeLanguage.PYTHON
        )
        
        assert isinstance(performance, str)
        assert "nested loop" in performance.lower() or "O(n²)" in performance
    
    @pytest.mark.asyncio
    async def test_analyze_security(self, explanation_engine_no_model):
        """Test security analysis."""
        insecure_code = """
def execute_command(user_input):
    eval(user_input)
    exec(user_input)
"""
        
        security = await explanation_engine_no_model._analyze_security(
            insecure_code,
            CodeLanguage.PYTHON
        )
        
        assert isinstance(security, str)
        assert "eval()" in security
        assert "exec()" in security
        assert "CRITICAL" in security or "⚠️" in security
    
    @pytest.mark.asyncio
    async def test_analyze_security_sql_injection(self, explanation_engine_no_model):
        """Test SQL injection detection."""
        sql_code = """
def get_user(username):
    query = "SELECT * FROM users WHERE name = '" + username + "'"
"""
        
        security = await explanation_engine_no_model._analyze_security(
            sql_code,
            CodeLanguage.PYTHON
        )
        
        assert "SQL injection" in security or "sql" in security.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_tradeoffs(self, explanation_engine, sample_python_code):
        """Test trade-off analysis."""
        analysis = await explanation_engine.analyze_tradeoffs(
            code=sample_python_code,
            requirement="Calculate Fibonacci numbers",
            language=CodeLanguage.PYTHON
        )
        
        assert isinstance(analysis, TradeOffAnalysis)
        assert analysis.approach == "Current Implementation"
        explanation_engine.model_manager.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_tradeoffs_without_model(self, explanation_engine_no_model, sample_python_code):
        """Test trade-off analysis without AI model."""
        analysis = await explanation_engine_no_model.analyze_tradeoffs(
            code=sample_python_code,
            requirement="Calculate Fibonacci numbers",
            language=CodeLanguage.PYTHON
        )
        
        assert isinstance(analysis, TradeOffAnalysis)
        assert len(analysis.pros) > 0
        assert len(analysis.cons) > 0
        assert len(analysis.alternatives) > 0
    
    def test_parse_tradeoff_response(self, explanation_engine_no_model):
        """Test parsing of trade-off response."""
        response = """
Pros:
- Fast execution
- Easy to understand
- Well documented

Cons:
- High memory usage
- Not scalable

Alternatives:
- Use iterative approach
- Implement caching

Recommendation:
Use for small datasets only

Use Cases:
- Prototyping
- Small-scale applications
"""
        
        analysis = explanation_engine_no_model._parse_tradeoff_response(response)
        
        assert len(analysis.pros) > 0
        assert len(analysis.cons) > 0
        assert len(analysis.alternatives) > 0
        assert analysis.recommendation is not None
        assert len(analysis.use_cases) > 0
    
    @pytest.mark.asyncio
    async def test_generate_documentation_api_reference(self, explanation_engine, sample_class_code):
        """Test API reference documentation generation."""
        doc = await explanation_engine.generate_documentation(
            code=sample_class_code,
            doc_type=DocumentationType.API_REFERENCE,
            language=CodeLanguage.PYTHON,
            include_examples=True
        )
        
        assert isinstance(doc, Documentation)
        assert doc.doc_type == DocumentationType.API_REFERENCE
        assert len(doc.content) > 0
        explanation_engine.model_manager.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_documentation_user_guide(self, explanation_engine, sample_python_code):
        """Test user guide documentation generation."""
        doc = await explanation_engine.generate_documentation(
            code=sample_python_code,
            doc_type=DocumentationType.USER_GUIDE,
            language=CodeLanguage.PYTHON,
            include_examples=True
        )
        
        assert isinstance(doc, Documentation)
        assert doc.doc_type == DocumentationType.USER_GUIDE
    
    @pytest.mark.asyncio
    async def test_generate_documentation_readme(self, explanation_engine, sample_python_code):
        """Test README documentation generation."""
        doc = await explanation_engine.generate_documentation(
            code=sample_python_code,
            doc_type=DocumentationType.README,
            language=CodeLanguage.PYTHON,
            include_examples=True
        )
        
        assert isinstance(doc, Documentation)
        assert doc.doc_type == DocumentationType.README
    
    @pytest.mark.asyncio
    async def test_generate_documentation_without_model(self, explanation_engine_no_model, sample_python_code):
        """Test documentation generation without AI model."""
        doc = await explanation_engine_no_model.generate_documentation(
            code=sample_python_code,
            doc_type=DocumentationType.API_REFERENCE,
            language=CodeLanguage.PYTHON,
            include_examples=False
        )
        
        assert isinstance(doc, Documentation)
        assert "Overview" in doc.content
        assert sample_python_code in doc.content
    
    def test_parse_documentation_sections(self, explanation_engine_no_model):
        """Test parsing documentation into sections."""
        content = """
# Introduction
This is the introduction.

## Installation
Install using pip.

### Requirements
Python 3.8+

## Usage
Use the function like this.
"""
        
        sections = explanation_engine_no_model._parse_documentation_sections(content)
        
        assert isinstance(sections, dict)
        assert "Introduction" in sections
        assert "Installation" in sections
        assert "Usage" in sections
    
    def test_extract_code_examples(self, explanation_engine_no_model):
        """Test extraction of code examples from documentation."""
        content = """
Here's an example:

```python
def hello():
    print("Hello")
```

And another:

```python
def world():
    print("World")
```
"""
        
        examples = explanation_engine_no_model._extract_code_examples(content)
        
        assert len(examples) == 2
        assert 'def hello():' in examples[0]
        assert 'def world():' in examples[1]
    
    def test_generate_doc_title(self, explanation_engine_no_model):
        """Test documentation title generation."""
        code = "def calculate_sum(a, b):\n    return a + b"
        
        title = explanation_engine_no_model._generate_doc_title(
            code,
            DocumentationType.API_REFERENCE
        )
        
        assert "calculate_sum" in title
        assert "API Reference" in title
    
    @pytest.mark.asyncio
    async def test_interactive_refinement_new_session(self, explanation_engine, sample_python_code):
        """Test starting a new interactive refinement session."""
        feedback = "Add error handling for negative numbers"
        
        explanation_engine.model_manager.generate_response.return_value = """
```python
def calculate_fibonacci(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```
"""
        
        session = await explanation_engine.interactive_refinement(
            code=sample_python_code,
            feedback=feedback
        )
        
        assert isinstance(session, InteractiveRefinement)
        assert session.original_code == sample_python_code
        assert session.iterations == 1
        assert len(session.user_feedback) == 1
        assert feedback in session.user_feedback
    
    @pytest.mark.asyncio
    async def test_interactive_refinement_continue_session(self, explanation_engine, sample_python_code):
        """Test continuing an existing refinement session."""
        # Create initial session
        session = InteractiveRefinement(
            session_id="test_session",
            original_code=sample_python_code,
            current_code=sample_python_code,
            iterations=0
        )
        
        explanation_engine.model_manager.generate_response.return_value = """
```python
def calculate_fibonacci(n):
    # Improved version
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```
"""
        
        feedback = "Add comments"
        updated_session = await explanation_engine.interactive_refinement(
            code=sample_python_code,
            feedback=feedback,
            session=session
        )
        
        assert updated_session.iterations == 1
        assert len(updated_session.refinement_history) == 1
    
    @pytest.mark.asyncio
    async def test_interactive_refinement_multiple_iterations(self, explanation_engine, sample_python_code):
        """Test multiple refinement iterations."""
        session = None
        feedbacks = [
            "Add error handling",
            "Add type hints",
            "Optimize performance"
        ]
        
        for feedback in feedbacks:
            explanation_engine.model_manager.generate_response.return_value = f"""
```python
# Refined code iteration
{sample_python_code}
```
"""
            session = await explanation_engine.interactive_refinement(
                code=sample_python_code if session is None else session.current_code,
                feedback=feedback,
                session=session
            )
        
        assert session.iterations == len(feedbacks)
        assert len(session.user_feedback) == len(feedbacks)
        assert len(session.refinement_history) == len(feedbacks)
    
    def test_get_refinement_summary(self, explanation_engine_no_model):
        """Test getting refinement session summary."""
        session = InteractiveRefinement(
            session_id="test_session",
            original_code="def test(): pass",
            current_code="def test():\n    return 42",
            iterations=2,
            user_feedback=["Add return value", "Make it return 42"],
            refinement_history=[
                {"iteration": 1, "feedback": "Add return value", "previous_code": "...", "refined_code": "..."},
                {"iteration": 2, "feedback": "Make it return 42", "previous_code": "...", "refined_code": "..."}
            ]
        )
        
        summary = explanation_engine_no_model.get_refinement_summary(session)
        
        assert "test_session" in summary
        assert "Total Iterations: 2" in summary
        assert "Feedback Items: 2" in summary
    
    @pytest.mark.asyncio
    async def test_explanation_with_different_languages(self, explanation_engine_no_model):
        """Test explanation for different programming languages."""
        js_code = "function add(a, b) { return a + b; }"
        
        explanation = await explanation_engine_no_model.explain_code(
            code=js_code,
            language=CodeLanguage.JAVASCRIPT,
            level=ExplanationLevel.STANDARD,
            include_analysis=False
        )
        
        assert isinstance(explanation, CodeExplanation)
        assert "javascript" in explanation.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_explanation(self, explanation_engine):
        """Test error handling during explanation generation."""
        explanation_engine.model_manager.generate_response.side_effect = Exception("Model error")
        
        code = "def test(): pass"
        
        explanation = await explanation_engine.explain_code(
            code=code,
            language=CodeLanguage.PYTHON,
            level=ExplanationLevel.STANDARD
        )
        
        # Should fallback to basic explanation
        assert isinstance(explanation, CodeExplanation)
        assert len(explanation.explanation) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_in_documentation(self, explanation_engine):
        """Test error handling during documentation generation."""
        explanation_engine.model_manager.generate_response.side_effect = Exception("Model error")
        
        code = "def test(): pass"
        
        doc = await explanation_engine.generate_documentation(
            code=code,
            doc_type=DocumentationType.README,
            language=CodeLanguage.PYTHON
        )
        
        # Should fallback to basic documentation
        assert isinstance(doc, Documentation)
        assert len(doc.content) > 0
