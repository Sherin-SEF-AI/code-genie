"""
End-to-end tests for Natural Language Programming system.

Tests the complete natural language programming system from
user input to final code generation and explanation.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.codegenie.core.nlp_engine import NLPEngine
from src.codegenie.core.requirement_processor import RequirementProcessor
from src.codegenie.core.code_generator import CodeGenerator, CodeLanguage, GenerationStrategy
from src.codegenie.core.explanation_engine import ExplanationEngine, ExplanationType
from src.codegenie.core.interactive_refinement import InteractiveRefinementEngine, InteractionType
from src.codegenie.core.code_validator import CodeValidator
from src.codegenie.models.model_manager import ModelManager


class TestNLPSystemE2E:
    """End-to-end test suite for NLP system."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def nlp_system(self):
        """Create complete NLP system without external dependencies."""
        return {
            'nlp_engine': NLPEngine(None),
            'requirement_processor': RequirementProcessor(None),
            'code_generator': CodeGenerator(None),
            'explanation_engine': ExplanationEngine(None),
            'interactive_engine': InteractiveRefinementEngine(None),
            'code_validator': CodeValidator()
        }
    
    @pytest.mark.asyncio
    async def test_simple_function_creation_e2e(self, nlp_system, temp_workspace):
        """Test complete flow for simple function creation."""
        system = nlp_system
        
        # User story: Developer wants to create a simple math function
        user_input = "Create a function called add_numbers that takes two parameters a and b and returns their sum"
        
        # Step 1: Natural language analysis
        analysis = await system['nlp_engine'].analyze_requirement(user_input)
        
        assert analysis.confidence_score > 0.6
        assert len(analysis.intents) > 0
        assert analysis.intents[0].type.value == "create_function"
        
        # Step 2: Requirement processing
        session = await system['requirement_processor'].process_requirement(user_input)
        
        # Step 3: Handle any clarification (simulate user responses)
        if session.questions:
            for question in session.questions:
                if question.required:
                    # Provide reasonable answers
                    answer = "Integer parameters, return integer sum"
                    await system['requirement_processor'].answer_clarification_question(
                        session.session_id, question.id, answer
                    )
        
        # Step 4: Code generation
        final_session = await system['requirement_processor'].get_clarification_status(session.session_id)
        
        if final_session:
            from src.codegenie.core.code_generator import CodeGenerationRequest
            
            request = CodeGenerationRequest(
                requirement=final_session.final_specification or user_input,
                language=CodeLanguage.PYTHON,
                strategy=GenerationStrategy.TEMPLATE_BASED,
                include_tests=True,
                include_documentation=True
            )
            
            result = await system['code_generator'].generate_code(request, analysis, final_session)
            
            assert result.success
            assert result.generated_code is not None
            
            # Verify generated code content
            code = result.generated_code.code
            assert "def add_numbers" in code
            assert "a" in code and "b" in code
            assert "return" in code
            
            # Step 5: Code validation
            validation_result = await system['code_validator'].validate_code(
                result.generated_code, run_tests=False
            )
            
            assert validation_result.syntax_valid
            
            # Step 6: Generate explanation
            from src.codegenie.core.explanation_engine import ExplanationRequest
            
            explanation_request = ExplanationRequest(
                code=result.generated_code.code,
                language=result.generated_code.language,
                explanation_types=[ExplanationType.OVERVIEW],
                target_audience="developer"
            )
            
            explanations = await system['explanation_engine'].explain_code(explanation_request)
            
            assert len(explanations) > 0
            assert explanations[0].content is not None
            
            # Step 7: Save generated code to file
            code_file = temp_workspace / "add_numbers.py"
            code_file.write_text(result.generated_code.code)
            
            assert code_file.exists()
            assert code_file.stat().st_size > 0
    
    @pytest.mark.asyncio
    async def test_class_creation_e2e(self, nlp_system, temp_workspace):
        """Test complete flow for class creation."""
        system = nlp_system
        
        user_input = "Create a class called Calculator with methods for basic arithmetic operations"
        
        # Process through complete workflow
        analysis = await system['nlp_engine'].analyze_requirement(user_input)
        session = await system['requirement_processor'].process_requirement(user_input)
        
        # Answer clarification questions
        if session.questions:
            for question in session.questions:
                if question.required:
                    if "method" in question.question.lower():
                        answer = "add, subtract, multiply, divide methods"
                    elif "parameter" in question.question.lower():
                        answer = "two number parameters for each operation"
                    else:
                        answer = "Basic arithmetic calculator class"
                    
                    await system['requirement_processor'].answer_clarification_question(
                        session.session_id, question.id, answer
                    )
        
        # Generate code
        final_session = await system['requirement_processor'].get_clarification_status(session.session_id)
        
        if final_session:
            from src.codegenie.core.code_generator import CodeGenerationRequest
            
            request = CodeGenerationRequest(
                requirement=final_session.final_specification or user_input,
                language=CodeLanguage.PYTHON,
                include_tests=True
            )
            
            result = await system['code_generator'].generate_code(request, analysis, final_session)
            
            if result.success and result.generated_code:
                # Verify class structure
                code = result.generated_code.code
                assert "class Calculator" in code
                assert "def " in code  # Should have methods
                
                # Validate code
                validation_result = await system['code_validator'].validate_code(result.generated_code)
                assert validation_result.syntax_valid
    
    @pytest.mark.asyncio
    async def test_interactive_refinement_e2e(self, nlp_system):
        """Test interactive refinement workflow."""
        system = nlp_system
        
        # Start interactive session
        initial_requirement = "Create a sorting function"
        session = await system['interactive_engine'].start_interactive_session(initial_requirement)
        
        # Simulate user clarification
        if session.clarification_session and session.clarification_session.questions:
            question = session.clarification_session.questions[0]
            
            response = await system['interactive_engine'].handle_user_interaction(
                session.session_id,
                InteractionType.CLARIFICATION_QUESTION,
                "Sort a list of integers in ascending order using bubble sort",
                {"question_id": question.id}
            )
            
            assert response.success
        
        # Check session status
        status = system['interactive_engine'].get_session_status(session.session_id)
        assert status is not None
        assert status["session_id"] == session.session_id
    
    @pytest.mark.asyncio
    async def test_multi_language_generation_e2e(self, nlp_system, temp_workspace):
        """Test code generation in multiple languages."""
        system = nlp_system
        
        requirement = "Create a function to calculate factorial of a number"
        languages = [CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT]
        
        for language in languages:
            # Analyze requirement
            analysis = await system['nlp_engine'].analyze_requirement(requirement)
            
            # Generate code
            from src.codegenie.core.code_generator import CodeGenerationRequest
            
            request = CodeGenerationRequest(
                requirement=requirement,
                language=language,
                include_tests=True
            )
            
            result = await system['code_generator'].generate_code(request, analysis)
            
            if result.success and result.generated_code:
                # Verify language-specific syntax
                code = result.generated_code.code
                
                if language == CodeLanguage.PYTHON:
                    assert "def " in code
                    file_ext = ".py"
                elif language == CodeLanguage.JAVASCRIPT:
                    assert "function" in code
                    file_ext = ".js"
                
                # Save to file
                code_file = temp_workspace / f"factorial{file_ext}"
                code_file.write_text(code)
                
                assert code_file.exists()
    
    @pytest.mark.asyncio
    async def test_error_handling_e2e(self, nlp_system):
        """Test error handling throughout the system."""
        system = nlp_system
        
        # Test with invalid/unclear requirement
        unclear_requirement = "Do something with data"
        
        # Should handle gracefully
        analysis = await system['nlp_engine'].analyze_requirement(unclear_requirement)
        assert analysis.clarification_needed
        assert analysis.confidence_score < 0.6
        
        # Validation should catch issues
        validation = await system['requirement_processor'].validate_requirement(unclear_requirement)
        assert not validation.is_valid
        assert len(validation.issues) > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_workflow_e2e(self, nlp_system, temp_workspace):
        """Test comprehensive workflow with all features."""
        system = nlp_system
        
        # Complex requirement
        requirement = """
        Create a Python class called FileManager that:
        - Has a method to read text files
        - Has a method to write text files  
        - Includes error handling for file operations
        - Has a method to list files in a directory
        """
        
        # Step 1: Analysis
        analysis = await system['nlp_engine'].analyze_requirement(requirement)
        
        # Step 2: Processing and clarification
        session = await system['requirement_processor'].process_requirement(requirement)
        
        # Answer questions if any
        if session.questions:
            for question in session.questions:
                if question.required:
                    await system['requirement_processor'].answer_clarification_question(
                        session.session_id, question.id, "Handle common file operations with proper error handling"
                    )
        
        # Step 3: Code generation
        final_session = await system['requirement_processor'].get_clarification_status(session.session_id)
        
        if final_session:
            from src.codegenie.core.code_generator import CodeGenerationRequest
            
            request = CodeGenerationRequest(
                requirement=final_session.final_specification or requirement,
                language=CodeLanguage.PYTHON,
                include_tests=True,
                include_documentation=True,
                include_error_handling=True
            )
            
            result = await system['code_generator'].generate_code(request, analysis, final_session)
            
            if result.success and result.generated_code:
                code = result.generated_code.code
                
                # Verify class and methods
                assert "class FileManager" in code
                assert "def read" in code or "def write" in code
                
                # Step 4: Validation
                validation_result = await system['code_validator'].validate_code(result.generated_code)
                assert validation_result.syntax_valid
                
                # Step 5: Multiple explanations
                from src.codegenie.core.explanation_engine import ExplanationRequest
                
                explanation_request = ExplanationRequest(
                    code=result.generated_code.code,
                    language=result.generated_code.language,
                    explanation_types=[
                        ExplanationType.OVERVIEW,
                        ExplanationType.BEST_PRACTICES,
                        ExplanationType.SECURITY
                    ],
                    target_audience="developer"
                )
                
                explanations = await system['explanation_engine'].explain_code(explanation_request)
                
                assert len(explanations) > 0
                
                # Step 6: Trade-off analysis
                trade_offs = await system['explanation_engine'].analyze_trade_offs(
                    result.generated_code.code,
                    result.generated_code.language,
                    requirement
                )
                
                # Step 7: Documentation generation
                from src.codegenie.core.explanation_engine import DocumentationRequest, DocumentationType
                
                doc_request = DocumentationRequest(
                    code=result.generated_code.code,
                    language=result.generated_code.language,
                    doc_types=[DocumentationType.API_DOCS, DocumentationType.README],
                    project_name="FileManager",
                    project_description="A utility class for file operations"
                )
                
                documentation = await system['explanation_engine'].generate_documentation(doc_request)
                
                # Step 8: Save all outputs
                outputs_dir = temp_workspace / "file_manager_project"
                outputs_dir.mkdir()
                
                # Save code
                (outputs_dir / "file_manager.py").write_text(result.generated_code.code)
                
                # Save tests if available
                if result.generated_code.tests:
                    (outputs_dir / "test_file_manager.py").write_text(result.generated_code.tests)
                
                # Save documentation
                if documentation:
                    for doc in documentation:
                        doc_file = outputs_dir / f"{doc.doc_type.value}.md"
                        doc_file.write_text(doc.content)
                
                # Verify all files created
                assert (outputs_dir / "file_manager.py").exists()
                assert len(list(outputs_dir.glob("*.py"))) >= 1
                assert len(list(outputs_dir.glob("*.md"))) >= 0
    
    @pytest.mark.asyncio
    async def test_performance_workflow_e2e(self, nlp_system):
        """Test performance aspects of the workflow."""
        system = nlp_system
        
        import time
        
        requirement = "Create a function to find the maximum element in a list"
        
        start_time = time.time()
        
        # Run complete workflow
        analysis = await system['nlp_engine'].analyze_requirement(requirement)
        session = await system['requirement_processor'].process_requirement(requirement)
        
        from src.codegenie.core.code_generator import CodeGenerationRequest
        
        request = CodeGenerationRequest(
            requirement=requirement,
            language=CodeLanguage.PYTHON
        )
        
        result = await system['code_generator'].generate_code(request, analysis)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete reasonably quickly (under 5 seconds for simple case)
        assert total_time < 5.0
        
        if result.success:
            assert result.generation_time >= 0
    
    @pytest.mark.asyncio
    async def test_batch_processing_e2e(self, nlp_system, temp_workspace):
        """Test batch processing of multiple requirements."""
        system = nlp_system
        
        requirements = [
            "Create a function to reverse a string",
            "Create a function to check if a string is palindrome",
            "Create a function to count vowels in a string"
        ]
        
        # Batch process
        sessions = await system['requirement_processor'].batch_process_requirements(requirements)
        
        assert len(sessions) == len(requirements)
        
        # Generate code for each
        results = []
        for i, session in enumerate(sessions):
            from src.codegenie.core.code_generator import CodeGenerationRequest
            
            request = CodeGenerationRequest(
                requirement=requirements[i],
                language=CodeLanguage.PYTHON
            )
            
            result = await system['code_generator'].generate_code(request, session.analysis)
            results.append(result)
        
        # Verify all succeeded
        successful_results = [r for r in results if r.success and r.generated_code]
        assert len(successful_results) > 0
        
        # Save all generated code
        for i, result in enumerate(successful_results):
            if result.generated_code:
                code_file = temp_workspace / f"string_function_{i}.py"
                code_file.write_text(result.generated_code.code)
                assert code_file.exists()
    
    @pytest.mark.asyncio
    async def test_user_experience_simulation_e2e(self, nlp_system):
        """Simulate realistic user experience."""
        system = nlp_system
        
        # Simulate user journey
        user_inputs = [
            "I need a function to calculate compound interest",
            "It should take principal, rate, and time as parameters",
            "Use the standard compound interest formula",
            "Include validation for negative values"
        ]
        
        # Start with first input
        analysis = await system['nlp_engine'].analyze_requirement(user_inputs[0])
        session = await system['requirement_processor'].process_requirement(user_inputs[0])
        
        # Simulate answering clarification questions with subsequent inputs
        question_index = 0
        for question in session.questions:
            if question.required and question_index < len(user_inputs) - 1:
                question_index += 1
                await system['requirement_processor'].answer_clarification_question(
                    session.session_id, question.id, user_inputs[question_index]
                )
        
        # Generate final code
        final_session = await system['requirement_processor'].get_clarification_status(session.session_id)
        
        if final_session:
            from src.codegenie.core.code_generator import CodeGenerationRequest
            
            request = CodeGenerationRequest(
                requirement=final_session.final_specification or user_inputs[0],
                language=CodeLanguage.PYTHON,
                include_tests=True,
                include_error_handling=True
            )
            
            result = await system['code_generator'].generate_code(request, analysis, final_session)
            
            if result.success and result.generated_code:
                # Should include compound interest calculation
                code = result.generated_code.code.lower()
                assert "compound" in code or "interest" in code
                assert "principal" in code
                assert "rate" in code
                assert "time" in code
    
    def test_system_integration_health_check(self, nlp_system):
        """Health check for system integration."""
        system = nlp_system
        
        # Verify all components are properly initialized
        assert system['nlp_engine'] is not None
        assert system['requirement_processor'] is not None
        assert system['code_generator'] is not None
        assert system['explanation_engine'] is not None
        assert system['interactive_engine'] is not None
        assert system['code_validator'] is not None
        
        # Verify components have required methods
        assert hasattr(system['nlp_engine'], 'analyze_requirement')
        assert hasattr(system['requirement_processor'], 'process_requirement')
        assert hasattr(system['code_generator'], 'generate_code')
        assert hasattr(system['explanation_engine'], 'explain_code')
        assert hasattr(system['interactive_engine'], 'start_interactive_session')
        assert hasattr(system['code_validator'], 'validate_code')
        
        # Verify supported languages
        languages = system['code_generator'].get_supported_languages()
        assert len(languages) > 0
        assert CodeLanguage.PYTHON in languages