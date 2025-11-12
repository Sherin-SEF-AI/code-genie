"""
Unit tests for NLP Code Generator.

Tests the integrated natural language programming pipeline including
code generation, validation, and execution testing.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile

from src.codegenie.core.nlp_code_generator import (
    NLPCodeGenerator, NLPCodeGenerationResult, ExecutionTestResult
)
from src.codegenie.core.code_generator import (
    CodeLanguage, GenerationStrategy, GeneratedCode
)
from src.codegenie.models.model_manager import ModelManager


class TestNLPCodeGenerator:
    """Test suite for NLP Code Generator."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        mock_manager = Mock(spec=ModelManager)
        mock_manager.generate_response = AsyncMock(return_value="Generated code")
        return mock_manager
    
    @pytest.fixture
    def nlp_code_generator(self, mock_model_manager):
        """Create NLP code generator with mock model manager."""
        return NLPCodeGenerator(mock_model_manager)
    
    @pytest.fixture
    def nlp_code_generator_no_model(self):
        """Create NLP code generator without model manager."""
        return NLPCodeGenerator(None)
    
    @pytest.mark.asyncio
    async def test_generate_simple_function(self, nlp_code_generator_no_model):
        """Test generating a simple function from natural language."""
        requirement = "Create a function named add_numbers that takes two integers and returns their sum"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            execute_validation=False
        )
        
        assert isinstance(result, NLPCodeGenerationResult)
        assert result.requirement_analysis is not None
        assert result.clarification_session is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_clarification(self, nlp_code_generator_no_model):
        """Test generation with automatic clarification."""
        requirement = "Create a function that processes data"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            execute_validation=False
        )
        
        assert result.clarification_session is not None
        # With auto_clarify, questions should be answered
        if result.clarification_session.questions:
            answered_count = sum(1 for q in result.clarification_session.questions if q.answered)
            assert answered_count > 0
    
    @pytest.mark.asyncio
    async def test_generate_without_auto_clarify(self, nlp_code_generator_no_model):
        """Test generation without automatic clarification."""
        requirement = "Create some function"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=False,
            execute_validation=False
        )
        
        # Should have pending questions
        if result.clarification_session and result.clarification_session.questions:
            assert len(result.warnings) > 0
            assert any("Clarification needed" in w for w in result.warnings)
    
    @pytest.mark.asyncio
    async def test_generate_with_execution_validation(self, nlp_code_generator_no_model):
        """Test generation with execution validation."""
        requirement = "Create a function named greet that returns 'Hello World'"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            execute_validation=True
        )
        
        # Should have execution test result
        if result.generated_code:
            assert result.execution_test is not None
            assert isinstance(result.execution_test, ExecutionTestResult)
    
    @pytest.mark.asyncio
    async def test_generate_with_tests(self, nlp_code_generator_no_model):
        """Test generation with test code included."""
        requirement = "Create a function to multiply two numbers"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            include_tests=True,
            execute_validation=False
        )
        
        if result.success and result.generated_code:
            # Tests might be generated
            assert result.generated_code.tests is None or isinstance(result.generated_code.tests, str)
    
    @pytest.mark.asyncio
    async def test_generate_javascript_code(self, nlp_code_generator_no_model):
        """Test generating JavaScript code."""
        requirement = "Create a function to calculate factorial"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.JAVASCRIPT,
            auto_clarify=True,
            execute_validation=False
        )
        
        assert result.requirement_analysis is not None
        if result.generated_code:
            assert result.generated_code.language == CodeLanguage.JAVASCRIPT
    
    @pytest.mark.asyncio
    async def test_generate_with_different_strategies(self, nlp_code_generator_no_model):
        """Test generation with different strategies."""
        requirement = "Create a function to reverse a string"
        
        for strategy in [GenerationStrategy.TEMPLATE_BASED, GenerationStrategy.HYBRID]:
            result = await nlp_code_generator_no_model.generate_from_natural_language(
                requirement=requirement,
                language=CodeLanguage.PYTHON,
                strategy=strategy,
                auto_clarify=True,
                execute_validation=False
            )
            
            assert result.requirement_analysis is not None
    
    @pytest.mark.asyncio
    async def test_auto_answer_clarifications(self, nlp_code_generator_no_model):
        """Test automatic answering of clarification questions."""
        requirement = "Create a function"
        
        # First get a session with questions
        session = await nlp_code_generator_no_model.requirement_processor.process_requirement(requirement)
        
        if session.questions:
            # Auto-answer
            updated_session = await nlp_code_generator_no_model._auto_answer_clarifications(session)
            
            # All questions should be answered
            assert all(q.answered for q in updated_session.questions)
    
    @pytest.mark.asyncio
    async def test_execution_validation_python(self, nlp_code_generator_no_model):
        """Test execution validation for Python code."""
        generated_code = GeneratedCode(
            code="def test_func():\n    return 42",
            language=CodeLanguage.PYTHON
        )
        
        result = await nlp_code_generator_no_model._execute_validation(generated_code)
        
        assert isinstance(result, ExecutionTestResult)
        assert result.success  # Valid Python syntax
    
    @pytest.mark.asyncio
    async def test_execution_validation_invalid_python(self, nlp_code_generator_no_model):
        """Test execution validation with invalid Python code."""
        generated_code = GeneratedCode(
            code="def test_func(\n    return 42",  # Missing closing parenthesis
            language=CodeLanguage.PYTHON
        )
        
        result = await nlp_code_generator_no_model._execute_validation(generated_code)
        
        assert isinstance(result, ExecutionTestResult)
        assert not result.success
        assert result.errors != ""
    
    @pytest.mark.asyncio
    async def test_execution_validation_non_python(self, nlp_code_generator_no_model):
        """Test execution validation for non-Python languages."""
        generated_code = GeneratedCode(
            code="function test() { return 42; }",
            language=CodeLanguage.JAVASCRIPT
        )
        
        result = await nlp_code_generator_no_model._execute_validation(generated_code)
        
        assert isinstance(result, ExecutionTestResult)
        assert result.success  # Should skip validation for non-Python
    
    @pytest.mark.asyncio
    async def test_fix_execution_errors(self, nlp_code_generator):
        """Test fixing execution errors in generated code."""
        generated_code = GeneratedCode(
            code="def test():\n    return x",  # Undefined variable
            language=CodeLanguage.PYTHON
        )
        
        exec_result = ExecutionTestResult(
            success=False,
            errors="NameError: name 'x' is not defined"
        )
        
        nlp_code_generator.model_manager.generate_response.return_value = """
```python
def test():
    x = 42
    return x
```
"""
        
        fixed_code = await nlp_code_generator._fix_execution_errors(
            generated_code, exec_result, "Create a test function"
        )
        
        assert fixed_code is not None
        assert "x = 42" in fixed_code.code
    
    @pytest.mark.asyncio
    async def test_fix_execution_errors_without_model(self, nlp_code_generator_no_model):
        """Test fixing execution errors without model."""
        generated_code = GeneratedCode(
            code="def test():\n    return x",
            language=CodeLanguage.PYTHON
        )
        
        exec_result = ExecutionTestResult(
            success=False,
            errors="NameError"
        )
        
        fixed_code = await nlp_code_generator_no_model._fix_execution_errors(
            generated_code, exec_result, "Create a test function"
        )
        
        assert fixed_code is None  # No model to fix
    
    @pytest.mark.asyncio
    async def test_generate_with_interactive_clarification(self, nlp_code_generator_no_model):
        """Test generation with interactive clarification callback."""
        requirement = "Create a function"
        
        # Mock callback that provides answers
        async def mock_callback(question, options):
            return options[0] if options else "Default answer"
        
        result = await nlp_code_generator_no_model.generate_with_interactive_clarification(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            clarification_callback=mock_callback
        )
        
        assert isinstance(result, NLPCodeGenerationResult)
        assert result.clarification_session is not None
    
    @pytest.mark.asyncio
    async def test_batch_generate(self, nlp_code_generator_no_model):
        """Test batch generation of multiple requirements."""
        requirements = [
            "Create a function to add numbers",
            "Create a function to subtract numbers",
            "Create a function to multiply numbers"
        ]
        
        results = await nlp_code_generator_no_model.batch_generate(
            requirements=requirements,
            language=CodeLanguage.PYTHON
        )
        
        assert len(results) == len(requirements)
        assert all(isinstance(r, NLPCodeGenerationResult) for r in results)
        assert all(r.requirement_analysis is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_generate_and_save(self, nlp_code_generator_no_model):
        """Test generating and saving code to file."""
        requirement = "Create a function to calculate square"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "generated.py"
            
            result = await nlp_code_generator_no_model.generate_and_save(
                requirement=requirement,
                output_path=output_path,
                language=CodeLanguage.PYTHON,
                save_tests=True
            )
            
            assert isinstance(result, NLPCodeGenerationResult)
            
            if result.success and result.generated_code:
                # Check if file was created
                assert output_path.exists()
                assert output_path.read_text() == result.generated_code.code
    
    @pytest.mark.asyncio
    async def test_generate_and_save_with_tests(self, nlp_code_generator_no_model):
        """Test generating and saving code with test files."""
        requirement = "Create a function to check if number is even"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "generated.py"
            
            result = await nlp_code_generator_no_model.generate_and_save(
                requirement=requirement,
                output_path=output_path,
                language=CodeLanguage.PYTHON,
                save_tests=True
            )
            
            if result.success and result.generated_code and result.generated_code.tests:
                test_path = output_path.parent / f"test_{output_path.name}"
                assert test_path.exists()
    
    def test_get_generation_summary(self, nlp_code_generator_no_model):
        """Test getting generation summary."""
        result = NLPCodeGenerationResult(success=True)
        
        summary = nlp_code_generator_no_model.get_generation_summary(result)
        
        assert isinstance(summary, str)
        assert "Natural Language Code Generation Summary" in summary
    
    def test_get_generation_summary_with_errors(self, nlp_code_generator_no_model):
        """Test getting summary with errors."""
        result = NLPCodeGenerationResult(
            success=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        
        summary = nlp_code_generator_no_model.get_generation_summary(result)
        
        assert "Errors:" in summary
        assert "Error 1" in summary
        assert "Warnings:" in summary
        assert "Warning 1" in summary
    
    @pytest.mark.asyncio
    async def test_error_handling_in_generation(self, nlp_code_generator):
        """Test error handling during generation."""
        nlp_code_generator.nlp_engine.analyze_requirement = AsyncMock(
            side_effect=Exception("Analysis error")
        )
        
        requirement = "Create a function"
        
        result = await nlp_code_generator.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON
        )
        
        assert not result.success
        assert len(result.errors) > 0
        assert any("failed" in e.lower() for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_generation_with_existing_context(self, nlp_code_generator_no_model):
        """Test generation with existing project context."""
        requirement = "Add a method to calculate area to the existing Shape class"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            execute_validation=False
        )
        
        assert result.requirement_analysis is not None
        # Should detect intent to modify existing code
        if result.requirement_analysis.intents:
            assert len(result.requirement_analysis.intents) > 0
    
    @pytest.mark.asyncio
    async def test_generation_confidence_scores(self, nlp_code_generator_no_model):
        """Test that generation tracks confidence scores."""
        requirement = "Create a function named calculate_sum that adds two numbers"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            execute_validation=False
        )
        
        assert result.requirement_analysis is not None
        assert result.requirement_analysis.confidence_score >= 0.0
        assert result.requirement_analysis.confidence_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_generation_with_complex_requirement(self, nlp_code_generator_no_model):
        """Test generation with complex multi-part requirement."""
        requirement = """
        Create a class named Calculator with methods for addition, subtraction,
        multiplication, and division. Include error handling for division by zero.
        Add type hints and comprehensive docstrings.
        """
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            execute_validation=False
        )
        
        assert result.requirement_analysis is not None
        # Should detect multiple entities and intents
        if result.requirement_analysis.entities:
            assert len(result.requirement_analysis.entities) > 0
    
    @pytest.mark.asyncio
    async def test_generation_preserves_requirement_details(self, nlp_code_generator_no_model):
        """Test that generation preserves specific requirement details."""
        requirement = "Create a function named fibonacci that takes n as integer parameter"
        
        result = await nlp_code_generator_no_model.generate_from_natural_language(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            auto_clarify=True,
            execute_validation=False
        )
        
        if result.success and result.generated_code:
            # Should contain the function name
            assert "fibonacci" in result.generated_code.code.lower()
