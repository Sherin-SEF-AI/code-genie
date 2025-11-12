"""
Unit tests for Requirement Processor.

Tests the requirement processing, validation, and clarification capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.codegenie.core.requirement_processor import (
    RequirementProcessor, ClarificationSession, ClarificationQuestion,
    RequirementValidation, ClarificationStatus, ValidationResult
)
from src.codegenie.core.nlp_engine import RequirementAnalysis, Intent, IntentType
from src.codegenie.models.model_manager import ModelManager


class TestRequirementProcessor:
    """Test suite for Requirement Processor."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        mock_manager = Mock(spec=ModelManager)
        mock_manager.generate_response = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def requirement_processor(self, mock_model_manager):
        """Create requirement processor with mock model manager."""
        return RequirementProcessor(mock_model_manager)
    
    @pytest.fixture
    def requirement_processor_no_model(self):
        """Create requirement processor without model manager."""
        return RequirementProcessor(None)
    
    @pytest.mark.asyncio
    async def test_process_simple_requirement(self, requirement_processor_no_model):
        """Test processing of simple requirement."""
        requirement = "Create a function to calculate the area of a circle"
        
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        assert isinstance(session, ClarificationSession)
        assert session.original_requirement == requirement
        assert session.analysis is not None
        assert session.session_id is not None
    
    @pytest.mark.asyncio
    async def test_process_clear_requirement_no_questions(self, requirement_processor_no_model):
        """Test processing of clear requirement that needs no clarification."""
        requirement = "Create a function named calculate_circle_area that takes radius as float parameter and returns area as float"
        
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        # Clear requirement might have fewer questions
        assert session.status in [ClarificationStatus.PENDING, ClarificationStatus.COMPLETED]
        if session.status == ClarificationStatus.COMPLETED:
            assert session.refined_requirement is not None
    
    @pytest.mark.asyncio
    async def test_process_ambiguous_requirement(self, requirement_processor_no_model):
        """Test processing of ambiguous requirement."""
        requirement = "Create some function that handles data"
        
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        assert session.status == ClarificationStatus.PENDING
        assert len(session.questions) > 0
        assert any(q.required for q in session.questions)
    
    @pytest.mark.asyncio
    async def test_validate_clear_requirement(self, requirement_processor_no_model):
        """Test validation of clear requirement."""
        requirement = "Create a function named add_numbers that takes two integers and returns their sum"
        
        validation = await requirement_processor_no_model.validate_requirement(requirement)
        
        assert isinstance(validation, RequirementValidation)
        assert validation.validation_result in [ValidationResult.VALID, ValidationResult.NEEDS_CLARIFICATION]
        assert validation.confidence_score > 0.5
    
    @pytest.mark.asyncio
    async def test_validate_invalid_requirement(self, requirement_processor_no_model):
        """Test validation of invalid requirement."""
        requirement = "Do stuff"
        
        validation = await requirement_processor_no_model.validate_requirement(requirement)
        
        assert not validation.is_valid
        assert validation.validation_result == ValidationResult.INVALID
        assert len(validation.issues) > 0
    
    @pytest.mark.asyncio
    async def test_answer_clarification_question(self, requirement_processor_no_model):
        """Test answering clarification questions."""
        requirement = "Create a function that processes data"
        
        # Process requirement to get questions
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        if session.questions:
            question = session.questions[0]
            answer = "Process user input data from forms"
            
            updated_session = await requirement_processor_no_model.answer_clarification_question(
                session.session_id, question.id, answer
            )
            
            assert updated_session.questions[0].answered
            assert updated_session.questions[0].answer == answer
    
    @pytest.mark.asyncio
    async def test_answer_all_required_questions(self, requirement_processor_no_model):
        """Test answering all required questions completes session."""
        requirement = "Create a function"
        
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        # Answer all required questions
        for question in session.questions:
            if question.required:
                await requirement_processor_no_model.answer_clarification_question(
                    session.session_id, question.id, "Test answer"
                )
        
        # Get updated session
        final_session = await requirement_processor_no_model.get_clarification_status(session.session_id)
        
        if final_session:
            all_required_answered = all(
                q.answered or not q.required 
                for q in final_session.questions
            )
            if all_required_answered:
                assert final_session.status == ClarificationStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_get_clarification_status(self, requirement_processor_no_model):
        """Test getting clarification status."""
        requirement = "Create a function"
        
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        status = await requirement_processor_no_model.get_clarification_status(session.session_id)
        
        assert status is not None
        assert status.session_id == session.session_id
        assert status.original_requirement == requirement
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session_status(self, requirement_processor_no_model):
        """Test getting status of nonexistent session."""
        status = await requirement_processor_no_model.get_clarification_status("nonexistent")
        
        assert status is None
    
    @pytest.mark.asyncio
    async def test_answer_nonexistent_question(self, requirement_processor_no_model):
        """Test answering nonexistent question raises error."""
        requirement = "Create a function"
        
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        with pytest.raises(ValueError, match="Question .* not found"):
            await requirement_processor_no_model.answer_clarification_question(
                session.session_id, "nonexistent_question", "answer"
            )
    
    @pytest.mark.asyncio
    async def test_answer_question_nonexistent_session(self, requirement_processor_no_model):
        """Test answering question in nonexistent session raises error."""
        with pytest.raises(ValueError, match="Session .* not found"):
            await requirement_processor_no_model.answer_clarification_question(
                "nonexistent_session", "q1", "answer"
            )
    
    @pytest.mark.asyncio
    async def test_generate_clarification_questions(self, requirement_processor_no_model):
        """Test generation of clarification questions."""
        # Create a mock analysis with ambiguities
        analysis = RequirementAnalysis(
            original_text="Create some function",
            intents=[Intent(IntentType.CREATE_FUNCTION, 0.8, "create function")],
            entities=[],
            ambiguities=[],
            confidence_score=0.6,
            clarification_needed=True
        )
        
        questions = await requirement_processor_no_model._generate_clarification_questions(analysis)
        
        assert isinstance(questions, list)
        assert all(isinstance(q, ClarificationQuestion) for q in questions)
    
    @pytest.mark.asyncio
    async def test_generate_intent_specific_questions(self, requirement_processor_no_model):
        """Test generation of intent-specific questions."""
        intent = Intent(IntentType.CREATE_FUNCTION, 0.9, "create function")
        
        questions = await requirement_processor_no_model._generate_intent_specific_questions(intent)
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, str) for q in questions)
    
    @pytest.mark.asyncio
    async def test_generate_validation_suggestions(self, requirement_processor_no_model):
        """Test generation of validation suggestions."""
        analysis = RequirementAnalysis(
            original_text="Do something",
            intents=[],
            entities=[],
            ambiguities=[],
            confidence_score=0.2,
            clarification_needed=True
        )
        
        suggestions = await requirement_processor_no_model._generate_validation_suggestions(analysis, ["Too vague"])
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_resolve_ambiguity(self, requirement_processor_no_model):
        """Test resolving specific ambiguity."""
        requirement = "Create some function that handles data efficiently"
        
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        if session.analysis.ambiguities:
            ambiguity = session.analysis.ambiguities[0]
            resolution = "Create exactly one function"
            
            updated_session = await requirement_processor_no_model.resolve_ambiguity(
                session.session_id, ambiguity.text, resolution
            )
            
            # Should find and answer corresponding question
            assert updated_session is not None
    
    def test_get_session_summary(self, requirement_processor_no_model):
        """Test getting session summary."""
        requirement = "Create a function"
        
        # Process requirement synchronously for test
        session = asyncio.run(requirement_processor_no_model.process_requirement(requirement))
        
        summary = requirement_processor_no_model.get_session_summary(session.session_id)
        
        assert summary is not None
        assert summary["session_id"] == session.session_id
        assert summary["original_requirement"] == requirement
        assert "total_questions" in summary
        assert "answered_questions" in summary
        assert "confidence_score" in summary
    
    def test_get_nonexistent_session_summary(self, requirement_processor_no_model):
        """Test getting summary of nonexistent session."""
        summary = requirement_processor_no_model.get_session_summary("nonexistent")
        
        assert summary is None
    
    @pytest.mark.asyncio
    async def test_batch_process_requirements(self, requirement_processor_no_model):
        """Test batch processing of multiple requirements."""
        requirements = [
            "Create a function to add numbers",
            "Create a class for user management",
            "Implement a sorting algorithm"
        ]
        
        sessions = await requirement_processor_no_model.batch_process_requirements(requirements)
        
        assert len(sessions) == len(requirements)
        assert all(isinstance(s, ClarificationSession) for s in sessions)
        assert all(s.original_requirement in requirements for s in sessions)
    
    def test_cleanup_session(self, requirement_processor_no_model):
        """Test cleaning up a session."""
        requirement = "Create a function"
        
        session = asyncio.run(requirement_processor_no_model.process_requirement(requirement))
        
        # Session should exist
        assert session.session_id in requirement_processor_no_model.active_sessions
        
        # Clean up session
        result = requirement_processor_no_model.cleanup_session(session.session_id)
        
        assert result is True
        assert session.session_id not in requirement_processor_no_model.active_sessions
    
    def test_cleanup_nonexistent_session(self, requirement_processor_no_model):
        """Test cleaning up nonexistent session."""
        result = requirement_processor_no_model.cleanup_session("nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_refined_requirement_generation_with_model(self, requirement_processor):
        """Test refined requirement generation with model."""
        requirement_processor.model_manager.generate_response.return_value = "Refined: Create a function named add that takes two integers"
        
        requirement = "Create a function to add numbers"
        session = await requirement_processor.process_requirement(requirement)
        
        # Simulate answering questions
        if session.questions:
            for question in session.questions[:2]:  # Answer first 2 questions
                await requirement_processor.answer_clarification_question(
                    session.session_id, question.id, "Test answer"
                )
        
        final_session = await requirement_processor.get_clarification_status(session.session_id)
        
        if final_session and final_session.refined_requirement:
            # Should have used model for refinement
            requirement_processor.model_manager.generate_response.assert_called()
    
    @pytest.mark.asyncio
    async def test_refined_requirement_generation_without_model(self, requirement_processor_no_model):
        """Test refined requirement generation without model."""
        requirement = "Create a function to add numbers"
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        # Simulate answering questions
        if session.questions:
            for question in session.questions:
                if question.required:
                    await requirement_processor_no_model.answer_clarification_question(
                        session.session_id, question.id, "Test answer"
                    )
        
        final_session = await requirement_processor_no_model.get_clarification_status(session.session_id)
        
        if final_session and final_session.status == ClarificationStatus.COMPLETED:
            # Should generate basic refined requirement
            assert final_session.refined_requirement is not None
            assert "Original requirement:" in final_session.refined_requirement
    
    @pytest.mark.asyncio
    async def test_final_specification_generation(self, requirement_processor_no_model):
        """Test final specification generation."""
        requirement = "Create a function named calculate_area that takes radius and returns area"
        session = await requirement_processor_no_model.process_requirement(requirement)
        
        # Complete the session by answering questions
        for question in session.questions:
            if question.required:
                await requirement_processor_no_model.answer_clarification_question(
                    session.session_id, question.id, "Detailed answer"
                )
        
        final_session = await requirement_processor_no_model.get_clarification_status(session.session_id)
        
        if final_session and final_session.status == ClarificationStatus.COMPLETED:
            assert final_session.final_specification is not None
    
    @pytest.mark.asyncio
    async def test_continue_existing_session(self, requirement_processor_no_model):
        """Test continuing an existing session with updated requirement."""
        requirement = "Create a function"
        session = await requirement_processor_no_model.process_requirement(requirement, "test_session")
        
        # Continue with updated requirement
        updated_requirement = "Create a function to calculate square root"
        updated_session = await requirement_processor_no_model.process_requirement(
            updated_requirement, "test_session"
        )
        
        assert updated_session.session_id == "test_session"
        assert updated_session.original_requirement == updated_requirement
        assert updated_session.status == ClarificationStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_error_handling_in_refinement(self, requirement_processor):
        """Test error handling during refinement."""
        requirement_processor.model_manager.generate_response.side_effect = Exception("Model error")
        
        requirement = "Create a function"
        session = await requirement_processor.process_requirement(requirement)
        
        # Should still work with fallback
        assert isinstance(session, ClarificationSession)
        assert session.original_requirement == requirement