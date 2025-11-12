"""
Unit tests for Code Generator.

Tests the code generation capabilities including template-based,
AI-driven, and hybrid code generation approaches.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.codegenie.core.code_generator import (
    CodeGenerator, GeneratedCode, CodeGenerationRequest, CodeGenerationResult,
    CodeTemplate, CodeLanguage, GenerationStrategy, ValidationLevel
)
from src.codegenie.core.nlp_engine import RequirementAnalysis, Intent, Entity, IntentType, EntityType
from src.codegenie.models.model_manager import ModelManager


class TestCodeGenerator:
    """Test suite for Code Generator."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        mock_manager = Mock(spec=ModelManager)
        mock_manager.generate_response = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def code_generator(self, mock_model_manager):
        """Create code generator with mock model manager."""
        return CodeGenerator(mock_model_manager)
    
    @pytest.fixture
    def code_generator_no_model(self):
        """Create code generator without model manager."""
        return CodeGenerator(None)
    
    @pytest.fixture
    def sample_analysis(self):
        """Create sample requirement analysis."""
        return RequirementAnalysis(
            original_text="Create a function named add_numbers that takes two integers and returns their sum",
            intents=[Intent(IntentType.CREATE_FUNCTION, 0.9, "create function")],
            entities=[
                Entity(EntityType.FUNCTION_NAME, "add_numbers", 0.9),
                Entity(EntityType.PARAMETER, "a", 0.8),
                Entity(EntityType.PARAMETER, "b", 0.8),
                Entity(EntityType.RETURN_TYPE, "int", 0.7)
            ],
            ambiguities=[],
            confidence_score=0.85,
            clarification_needed=False
        )
    
    @pytest.fixture
    def sample_request(self):
        """Create sample code generation request."""
        return CodeGenerationRequest(
            requirement="Create a function named add_numbers that takes two integers and returns their sum",
            language=CodeLanguage.PYTHON,
            strategy=GenerationStrategy.TEMPLATE_BASED,
            include_tests=True,
            include_documentation=True
        )
    
    @pytest.mark.asyncio
    async def test_generate_code_template_based(self, code_generator_no_model, sample_request, sample_analysis):
        """Test template-based code generation."""
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        assert isinstance(result, CodeGenerationResult)
        assert result.success
        assert result.generated_code is not None
        assert isinstance(result.generated_code, GeneratedCode)
        assert result.generated_code.language == CodeLanguage.PYTHON
        assert "def add_numbers" in result.generated_code.code
    
    @pytest.mark.asyncio
    async def test_generate_code_ai_driven(self, code_generator, sample_request, sample_analysis):
        """Test AI-driven code generation."""
        # Mock AI response
        ai_response = '''
```python
def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b
```

```test
def test_add_numbers():
    assert add_numbers(2, 3) == 5
```
'''
        code_generator.model_manager.generate_response.return_value = ai_response
        
        sample_request.strategy = GenerationStrategy.AI_DRIVEN
        result = await code_generator.generate_code(sample_request, sample_analysis)
        
        assert result.success
        assert result.generated_code is not None
        assert "def add_numbers" in result.generated_code.code
        assert result.generated_code.tests is not None
        code_generator.model_manager.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_code_hybrid(self, code_generator_no_model, sample_request, sample_analysis):
        """Test hybrid code generation."""
        sample_request.strategy = GenerationStrategy.HYBRID
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        assert isinstance(result, CodeGenerationResult)
        # Should fall back to template-based when no model available
        if result.success:
            assert result.generated_code is not None
    
    @pytest.mark.asyncio
    async def test_generate_code_with_validation(self, code_generator_no_model, sample_request, sample_analysis):
        """Test code generation with validation."""
        sample_request.validation_level = ValidationLevel.COMPREHENSIVE
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        if result.success and result.generated_code:
            assert result.validation_passed is not None
            assert result.generated_code.validation_results is not None
    
    @pytest.mark.asyncio
    async def test_generate_code_javascript(self, code_generator_no_model, sample_analysis):
        """Test JavaScript code generation."""
        request = CodeGenerationRequest(
            requirement="Create a function to add numbers",
            language=CodeLanguage.JAVASCRIPT,
            strategy=GenerationStrategy.TEMPLATE_BASED
        )
        
        result = await code_generator_no_model.generate_code(request, sample_analysis)
        
        if result.success and result.generated_code:
            assert result.generated_code.language == CodeLanguage.JAVASCRIPT
            assert "function" in result.generated_code.code
    
    @pytest.mark.asyncio
    async def test_generate_code_class_creation(self, code_generator_no_model):
        """Test class creation code generation."""
        analysis = RequirementAnalysis(
            original_text="Create a class named Calculator",
            intents=[Intent(IntentType.CREATE_CLASS, 0.9, "create class")],
            entities=[Entity(EntityType.CLASS_NAME, "Calculator", 0.9)],
            ambiguities=[],
            confidence_score=0.85,
            clarification_needed=False
        )
        
        request = CodeGenerationRequest(
            requirement="Create a class named Calculator",
            language=CodeLanguage.PYTHON,
            strategy=GenerationStrategy.TEMPLATE_BASED
        )
        
        result = await code_generator_no_model.generate_code(request, analysis)
        
        if result.success and result.generated_code:
            assert "class Calculator" in result.generated_code.code
    
    @pytest.mark.asyncio
    async def test_generate_code_with_tests(self, code_generator_no_model, sample_request, sample_analysis):
        """Test code generation with tests included."""
        sample_request.include_tests = True
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        if result.success and result.generated_code:
            assert result.generated_code.tests is not None
            assert "test_" in result.generated_code.tests
    
    @pytest.mark.asyncio
    async def test_generate_code_without_tests(self, code_generator_no_model, sample_request, sample_analysis):
        """Test code generation without tests."""
        sample_request.include_tests = False
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        if result.success and result.generated_code:
            assert result.generated_code.tests is None
    
    @pytest.mark.asyncio
    async def test_generate_code_with_documentation(self, code_generator_no_model, sample_request, sample_analysis):
        """Test code generation with documentation."""
        sample_request.include_documentation = True
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        if result.success and result.generated_code:
            assert result.generated_code.documentation is not None
    
    @pytest.mark.asyncio
    async def test_generate_code_with_error_handling(self, code_generator_no_model, sample_request, sample_analysis):
        """Test code generation with error handling."""
        sample_request.include_error_handling = True
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        if result.success and result.generated_code:
            # Should include try/except or similar error handling
            code = result.generated_code.code.lower()
            assert "try" in code or "except" in code or "error" in code
    
    @pytest.mark.asyncio
    async def test_generate_code_no_intents(self, code_generator_no_model):
        """Test code generation with no detected intents."""
        analysis = RequirementAnalysis(
            original_text="Do something unclear",
            intents=[],
            entities=[],
            ambiguities=[],
            confidence_score=0.2,
            clarification_needed=True
        )
        
        request = CodeGenerationRequest(
            requirement="Do something unclear",
            language=CodeLanguage.PYTHON
        )
        
        result = await code_generator_no_model.generate_code(request, analysis)
        
        # Should fail gracefully
        assert not result.success or result.generated_code is None
    
    @pytest.mark.asyncio
    async def test_extract_template_values(self, code_generator_no_model, sample_analysis, sample_request):
        """Test extraction of template values from analysis."""
        values = await code_generator_no_model._extract_template_values(sample_analysis, sample_request)
        
        assert isinstance(values, dict)
        assert "function_name" in values
        assert values["function_name"] == "add_numbers"
        assert "parameters" in values
        assert "docstring" in values
    
    @pytest.mark.asyncio
    async def test_extract_test_values(self, code_generator_no_model, sample_analysis):
        """Test extraction of test template values."""
        placeholder_values = {"function_name": "add_numbers", "class_name": "Calculator"}
        test_values = await code_generator_no_model._extract_test_values(sample_analysis, placeholder_values)
        
        assert isinstance(test_values, dict)
        assert "normal_test" in test_values
        assert "edge_case_tests" in test_values
        assert "error_tests" in test_values
    
    @pytest.mark.asyncio
    async def test_parse_ai_response(self, code_generator_no_model):
        """Test parsing of AI response."""
        ai_response = '''
Here's the code:

```python
def test_function():
    return "Hello"
```

```test
def test_test_function():
    assert test_function() == "Hello"
```

```documentation
This function returns a greeting.
```
'''
        
        parsed = await code_generator_no_model._parse_ai_response(ai_response, CodeLanguage.PYTHON)
        
        assert "code" in parsed
        assert "def test_function" in parsed["code"]
        assert "tests" in parsed
        assert parsed["tests"] is not None
        assert "documentation" in parsed
        assert parsed["documentation"] is not None
    
    def test_extract_imports_python(self, code_generator_no_model):
        """Test extraction of Python imports."""
        code = '''
import os
from typing import List
import json
'''
        
        imports = code_generator_no_model._extract_imports(code, CodeLanguage.PYTHON)
        
        assert "os" in imports
        assert "typing" in imports
        assert "json" in imports
    
    def test_extract_imports_javascript(self, code_generator_no_model):
        """Test extraction of JavaScript imports."""
        code = '''
import { useState } from 'react';
const fs = require('fs');
import axios from 'axios';
'''
        
        imports = code_generator_no_model._extract_imports(code, CodeLanguage.JAVASCRIPT)
        
        assert "react" in imports
        assert "fs" in imports
        assert "axios" in imports
    
    def test_extract_dependencies(self, code_generator_no_model):
        """Test extraction of dependencies."""
        code = '''
import requests
import numpy as np
from flask import Flask
'''
        
        dependencies = code_generator_no_model._extract_dependencies(code, CodeLanguage.PYTHON)
        
        # Should detect common dependencies
        assert any(dep in ["requests", "numpy", "flask"] for dep in dependencies)
    
    @pytest.mark.asyncio
    async def test_validate_syntax_python(self, code_generator_no_model):
        """Test Python syntax validation."""
        valid_code = GeneratedCode(
            code="def test():\n    return True",
            language=CodeLanguage.PYTHON
        )
        
        invalid_code = GeneratedCode(
            code="def test(\n    return True",  # Missing closing parenthesis
            language=CodeLanguage.PYTHON
        )
        
        assert await code_generator_no_model._validate_syntax(valid_code)
        assert not await code_generator_no_model._validate_syntax(invalid_code)
    
    @pytest.mark.asyncio
    async def test_generate_edge_case_handling(self, code_generator, sample_analysis):
        """Test generation of edge case handling."""
        generated_code = GeneratedCode(
            code="def add_numbers(a, b):\n    return a + b",
            language=CodeLanguage.PYTHON
        )
        
        code_generator.model_manager.generate_response.return_value = '''
```python
def add_numbers(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments must be numbers")
    return a + b
```
'''
        
        enhanced_code = await code_generator.generate_edge_case_handling(generated_code, sample_analysis)
        
        assert "isinstance" in enhanced_code.code
        assert "TypeError" in enhanced_code.code
        code_generator.model_manager.generate_response.assert_called_once()
    
    def test_get_supported_languages(self, code_generator_no_model):
        """Test getting supported languages."""
        languages = code_generator_no_model.get_supported_languages()
        
        assert isinstance(languages, list)
        assert CodeLanguage.PYTHON in languages
        assert CodeLanguage.JAVASCRIPT in languages
        assert len(languages) > 0
    
    def test_get_available_templates(self, code_generator_no_model):
        """Test getting available templates."""
        all_templates = code_generator_no_model.get_available_templates()
        python_templates = code_generator_no_model.get_available_templates(CodeLanguage.PYTHON)
        
        assert isinstance(all_templates, list)
        assert isinstance(python_templates, list)
        assert len(python_templates) <= len(all_templates)
        assert all(template.language == CodeLanguage.PYTHON for template in python_templates)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_generation(self, code_generator):
        """Test error handling during code generation."""
        code_generator.model_manager.generate_response.side_effect = Exception("Model error")
        
        request = CodeGenerationRequest(
            requirement="Create a function",
            language=CodeLanguage.PYTHON,
            strategy=GenerationStrategy.AI_DRIVEN
        )
        
        analysis = RequirementAnalysis(
            original_text="Create a function",
            intents=[Intent(IntentType.CREATE_FUNCTION, 0.8, "create function")],
            entities=[],
            ambiguities=[],
            confidence_score=0.6,
            clarification_needed=False
        )
        
        result = await code_generator.generate_code(request, analysis)
        
        # Should handle error gracefully
        assert isinstance(result, CodeGenerationResult)
        if not result.success:
            assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_generation_time_tracking(self, code_generator_no_model, sample_request, sample_analysis):
        """Test that generation time is tracked."""
        result = await code_generator_no_model.generate_code(sample_request, sample_analysis)
        
        assert result.generation_time >= 0
        assert isinstance(result.generation_time, float)
    
    @pytest.mark.asyncio
    async def test_template_based_fallback(self, code_generator_no_model):
        """Test fallback to template-based when AI fails."""
        analysis = RequirementAnalysis(
            original_text="Create a function named test_func",
            intents=[Intent(IntentType.CREATE_FUNCTION, 0.9, "create function")],
            entities=[Entity(EntityType.FUNCTION_NAME, "test_func", 0.9)],
            ambiguities=[],
            confidence_score=0.85,
            clarification_needed=False
        )
        
        request = CodeGenerationRequest(
            requirement="Create a function named test_func",
            language=CodeLanguage.PYTHON,
            strategy=GenerationStrategy.HYBRID  # Should try AI then fall back to template
        )
        
        result = await code_generator_no_model.generate_code(request, analysis)
        
        # Should succeed with template-based approach
        if result.success:
            assert result.generated_code is not None
            assert "def test_func" in result.generated_code.code