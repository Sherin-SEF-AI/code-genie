"""
Integration tests for Natural Language Programming workflow.

Tests the complete workflow from natural language requirement
to generated code with validation and explanation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.codegenie.core.nlp_engine import NLPEngine
from src.codegenie.core.requirement_processor import RequirementProcessor, ClarificationStatus
from src.codegenie.core.code_generator import CodeGenerator, CodeGenerationRequest, CodeLanguage
from src.codegenie.core.explanation_engine import ExplanationEngine, ExplanationRequest, ExplanationType
from src.codegenie.core.interactive_refinement import InteractiveRefinementEngine, InteractionType
from src.codegenie.models.model_manager import ModelManager


class TestNLPWorkflowIntegration:
    """Integration test suite for NLP workflow."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager for testing."""
        mock_manager = Mock(spec=ModelManager)
        mock_manager.generate_response = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def nlp_components(self, mock_model_manager):
        """Create all NLP components with mock model manager."""
        return {
            'nlp_engine': NLPEngine(mock_model_manager),
            'requirement_processor': RequirementProcessor(mock_model_manager),
            'code_generator': CodeGenerator(mock_model_manager),
            'explanation_engine': ExplanationEngine(mock_model_manager),
            'interactive_engine': InteractiveRefinementEngine(mock_model_manager)
        }
    
    @pytest.fixture
    def nlp_components_no_model(self):
        """Create all NLP components without model manager."""
        return {
            'nlp_engine': NLPEngine(None),
            'requirement_processor': RequirementProcessor(None),
            'code_generator': CodeGenerator(None),
            'explanation_engine': ExplanationEngine(None),
            'interactive_engine': InteractiveRefinementEngine(None)
        }
    
    @pytest.mark.asyncio
    async def test_complete_workflow_simple_function(self, nlp_components_no_model):
        """Test complete workflow for simple function creation."""
        components = nlp_components_no_model
        requirement = "Create a function named calculate_area that takes radius as parameter and returns the area of a circle"
        
        # Step 1: Analyze requirement
        analysis = await components['nlp_engine'].analyze_requirement(requirement)
        assert analysis.confidence_score > 0.6
        assert len(analysis.intents) > 0
        
        # Step 2: Process requirement (may need clarification)
        session = await components['requirement_processor'].process_requirement(requirement)
        assert session.original_requirement == requirement
        
        # Step 3: If clarification needed, simulate answering questions
        if session.status == ClarificationStatus.PENDING and session.questions:
            for question in session.questions:
                if question.required:
                    await components['requirement_processor'].answer_clarification_question(
                        session.session_id, question.id, "Use math.pi for pi value"
                    )
        
        # Get final session status
        final_session = await components['requirement_processor'].get_clarification_status(session.session_id)
        
        # Step 4: Generate code
        if final_session and final_session.status == ClarificationStatus.COMPLETED:
            generation_request = CodeGenerationRequest(
                requirement=final_session.final_specification or requirement,
                language=CodeLanguage.PYTHON,
                include_tests=True
            )
            
            result = await components['code_generator'].generate_code(
                generation_request, analysis, final_session
            )
            
            assert result.success
            assert result.generated_code is not None
            assert "calculate_area" in result.generated_code.code
            assert "radius" in result.generated_code.code
    
    @pytest.mark.asyncio
    async def test_workflow_with_ambiguous_requirement(self, nlp_components_no_model):
        """Test workflow with ambiguous requirement requiring clarification."""
        components = nlp_components_no_model
        requirement = "Create a function that processes data efficiently"
        
        # Step 1: Analyze requirement
        analysis = await components['nlp_engine'].analyze_requirement(requirement)
        assert analysis.clarification_needed
        assert len(analysis.ambiguities) > 0
        
        # Step 2: Process requirement
        session = await components['requirement_processor'].process_requirement(requirement)
        assert session.status == ClarificationStatus.PENDING
        assert len(session.questions) > 0
        
        # Step 3: Answer clarification questions
        answers = {
            "function name": "process_user_data",
            "data type": "user input from web forms",
            "processing": "validate and sanitize input data",
            "return": "cleaned data dictionary"
        }
        
        for question in session.questions:
            if question.required:
                # Provide relevant answer based on question content
                answer = "process user input data and return cleaned dictionary"
                await components['requirement_processor'].answer_clarification_question(
                    session.session_id, question.id, answer
                )
        
        # Step 4: Verify session completion
        final_session = await components['requirement_processor'].get_clarification_status(session.session_id)
        
        if final_session and final_session.status == ClarificationStatus.COMPLETED:
            assert final_session.refined_requirement is not None
            assert final_session.final_specification is not None
    
    @pytest.mark.asyncio
    async def test_code_generation_and_explanation_workflow(self, nlp_components_no_model):
        """Test code generation followed by explanation."""
        components = nlp_components_no_model
        requirement = "Create a function named fibonacci that calculates the nth Fibonacci number"
        
        # Generate code
        analysis = await components['nlp_engine'].analyze_requirement(requirement)
        
        generation_request = CodeGenerationRequest(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            include_tests=True
        )
        
        result = await components['code_generator'].generate_code(generation_request, analysis)
        
        if result.success and result.generated_code:
            # Generate explanation
            explanation_request = ExplanationRequest(
                code=result.generated_code.code,
                language=result.generated_code.language,
                explanation_types=[ExplanationType.OVERVIEW, ExplanationType.ALGORITHM],
                context=requirement
            )
            
            explanations = await components['explanation_engine'].explain_code(explanation_request)
            
            assert len(explanations) > 0
            assert any(exp.explanation_type == ExplanationType.OVERVIEW for exp in explanations)
    
    @pytest.mark.asyncio
    async def test_interactive_refinement_workflow(self, nlp_components_no_model):
        """Test interactive refinement workflow."""
        components = nlp_components_no_model
        requirement = "Create a function to sort a list of numbers"
        
        # Start interactive session
        session = await components['interactive_engine'].start_interactive_session(requirement)
        
        assert session.session_id is not None
        assert session.current_requirement == requirement
        
        # Simulate user interaction for clarification
        if session.clarification_session and session.clarification_session.questions:
            question = session.clarification_session.questions[0]
            
            response = await components['interactive_engine'].handle_user_interaction(
                session.session_id,
                InteractionType.CLARIFICATION_QUESTION,
                "Sort in ascending order using quicksort algorithm",
                {"question_id": question.id}
            )
            
            assert response.success
    
    @pytest.mark.asyncio
    async def test_validation_workflow(self, nlp_components_no_model):
        """Test requirement validation workflow."""
        components = nlp_components_no_model
        
        # Test valid requirement
        valid_requirement = "Create a function named add_two_numbers that takes two integer parameters and returns their sum"
        validation = await components['requirement_processor'].validate_requirement(valid_requirement)
        
        assert validation.confidence_score > 0.5
        
        # Test invalid requirement
        invalid_requirement = "Do something maybe"
        validation = await components['requirement_processor'].validate_requirement(invalid_requirement)
        
        assert not validation.is_valid
        assert len(validation.issues) > 0
    
    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self, nlp_components_no_model):
        """Test batch processing of multiple requirements."""
        components = nlp_components_no_model
        
        requirements = [
            "Create a function to calculate factorial",
            "Create a class for managing user accounts",
            "Implement a binary search algorithm"
        ]
        
        # Batch process requirements
        sessions = await components['requirement_processor'].batch_process_requirements(requirements)
        
        assert len(sessions) == len(requirements)
        assert all(session.original_requirement in requirements for session in sessions)
        
        # Analyze each requirement
        for i, session in enumerate(sessions):
            analysis = session.analysis
            assert analysis.original_text == requirements[i]
            assert len(analysis.intents) > 0
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, nlp_components_no_model):
        """Test error recovery in workflow."""
        components = nlp_components_no_model
        
        # Test with empty requirement
        empty_requirement = ""
        
        try:
            analysis = await components['nlp_engine'].analyze_requirement(empty_requirement)
            # Should handle gracefully
            assert isinstance(analysis.original_text, str)
        except Exception:
            # Should not raise unhandled exceptions
            pytest.fail("Should handle empty requirement gracefully")
        
        # Test validation of empty requirement
        is_valid, issues = await components['nlp_engine'].validate_requirement(empty_requirement)
        assert not is_valid
        assert len(issues) > 0
    
    @pytest.mark.asyncio
    async def test_multi_language_workflow(self, nlp_components_no_model):
        """Test workflow with different programming languages."""
        components = nlp_components_no_model
        requirement = "Create a function to reverse a string"
        
        languages = [CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT]
        
        for language in languages:
            analysis = await components['nlp_engine'].analyze_requirement(requirement)
            
            generation_request = CodeGenerationRequest(
                requirement=requirement,
                language=language,
                include_tests=True
            )
            
            result = await components['code_generator'].generate_code(generation_request, analysis)
            
            if result.success and result.generated_code:
                assert result.generated_code.language == language
                # Should contain language-appropriate syntax
                if language == CodeLanguage.PYTHON:
                    assert "def " in result.generated_code.code
                elif language == CodeLanguage.JAVASCRIPT:
                    assert "function" in result.generated_code.code
    
    @pytest.mark.asyncio
    async def test_complex_requirement_workflow(self, nlp_components_no_model):
        """Test workflow with complex requirement."""
        components = nlp_components_no_model
        requirement = """
        Create a class called DataProcessor that:
        1. Has a method to load data from CSV files
        2. Has a method to clean and validate the data
        3. Has a method to export processed data to JSON
        4. Includes proper error handling for file operations
        """
        
        # Analyze complex requirement
        analysis = await components['nlp_engine'].analyze_requirement(requirement)
        
        # Should detect class creation intent
        assert any(intent.type.value == "create_class" for intent in analysis.intents)
        
        # Should extract class name
        class_entities = [e for e in analysis.entities if e.type.value == "class_name"]
        assert len(class_entities) > 0
        assert any("DataProcessor" in e.value for e in class_entities)
        
        # Process requirement
        session = await components['requirement_processor'].process_requirement(requirement)
        
        # Should generate questions for clarification of complex requirements
        if session.questions:
            assert len(session.questions) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_session_management(self, nlp_components_no_model):
        """Test session management throughout workflow."""
        components = nlp_components_no_model
        requirement = "Create a function to calculate prime numbers"
        
        # Create session
        session = await components['requirement_processor'].process_requirement(requirement, "test_session")
        
        # Verify session exists
        status = await components['requirement_processor'].get_clarification_status("test_session")
        assert status is not None
        assert status.session_id == "test_session"
        
        # Get session summary
        summary = components['requirement_processor'].get_session_summary("test_session")
        assert summary is not None
        assert summary["original_requirement"] == requirement
        
        # Clean up session
        cleanup_result = components['requirement_processor'].cleanup_session("test_session")
        assert cleanup_result is True
        
        # Verify session is gone
        status_after_cleanup = await components['requirement_processor'].get_clarification_status("test_session")
        assert status_after_cleanup is None
    
    @pytest.mark.asyncio
    async def test_workflow_with_model_integration(self, nlp_components):
        """Test workflow with model manager integration."""
        components = nlp_components
        requirement = "Create a function to calculate compound interest"
        
        # Mock model responses
        components['nlp_engine'].model_manager.generate_response.return_value = "Technical specification: Calculate compound interest using formula A = P(1 + r/n)^(nt)"
        components['code_generator'].model_manager.generate_response.return_value = '''
```python
def calculate_compound_interest(principal, rate, time, compound_frequency=1):
    """Calculate compound interest."""
    return principal * (1 + rate / compound_frequency) ** (compound_frequency * time)
```
'''
        
        # Run workflow
        analysis = await components['nlp_engine'].analyze_requirement(requirement)
        
        if analysis.confidence_score > 0.7:
            # Should use model for technical specification
            assert analysis.technical_specification is not None
            components['nlp_engine'].model_manager.generate_response.assert_called()
        
        # Generate code with model
        generation_request = CodeGenerationRequest(
            requirement=requirement,
            language=CodeLanguage.PYTHON,
            strategy="ai_driven"
        )
        
        result = await components['code_generator'].generate_code(generation_request, analysis)
        
        if result.success:
            components['code_generator'].model_manager.generate_response.assert_called()
    
    @pytest.mark.asyncio
    async def test_end_to_end_user_experience(self, nlp_components_no_model):
        """Test end-to-end user experience simulation."""
        components = nlp_components_no_model
        
        # User provides initial requirement
        user_requirement = "I need a function to check if a number is prime"
        
        # System analyzes and processes requirement
        analysis = await components['nlp_engine'].analyze_requirement(user_requirement)
        session = await components['requirement_processor'].process_requirement(user_requirement)
        
        # If clarification needed, simulate user responses
        if session.questions:
            for question in session.questions[:2]:  # Answer first 2 questions
                if question.required:
                    await components['requirement_processor'].answer_clarification_question(
                        session.session_id, question.id, "Return True for prime, False for non-prime"
                    )
        
        # Generate code
        final_session = await components['requirement_processor'].get_clarification_status(session.session_id)
        
        if final_session and final_session.status == ClarificationStatus.COMPLETED:
            generation_request = CodeGenerationRequest(
                requirement=final_session.final_specification or user_requirement,
                language=CodeLanguage.PYTHON,
                include_tests=True,
                include_documentation=True
            )
            
            result = await components['code_generator'].generate_code(generation_request, analysis)
            
            if result.success and result.generated_code:
                # User requests explanation
                explanation_request = ExplanationRequest(
                    code=result.generated_code.code,
                    language=result.generated_code.language,
                    explanation_types=[ExplanationType.OVERVIEW],
                    target_audience="developer"
                )
                
                explanations = await components['explanation_engine'].explain_code(explanation_request)
                
                # Verify complete workflow
                assert len(explanations) > 0
                assert result.generated_code.tests is not None
                assert result.generated_code.documentation is not None
                assert "prime" in result.generated_code.code.lower()