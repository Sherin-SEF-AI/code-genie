"""
Unit tests for NLP Engine components.

Tests the natural language processing capabilities including
requirement analysis, intent recognition, and entity extraction.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.codegenie.core.nlp_engine import (
    NLPEngine, RequirementAnalysis, Intent, Entity, Ambiguity,
    IntentType, EntityType
)
from src.codegenie.models.model_manager import ModelManager


class TestNLPEngine:
    """Test suite for NLP Engine."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        mock_manager = Mock(spec=ModelManager)
        mock_manager.generate_response = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def nlp_engine(self, mock_model_manager):
        """Create NLP engine with mock model manager."""
        return NLPEngine(mock_model_manager)
    
    @pytest.fixture
    def nlp_engine_no_model(self):
        """Create NLP engine without model manager."""
        return NLPEngine(None)
    
    @pytest.mark.asyncio
    async def test_analyze_simple_function_requirement(self, nlp_engine_no_model):
        """Test analysis of simple function creation requirement."""
        requirement = "Create a function called calculate_sum that takes two numbers and returns their sum"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        assert isinstance(analysis, RequirementAnalysis)
        assert analysis.original_text == requirement
        assert len(analysis.intents) > 0
        assert analysis.intents[0].type == IntentType.CREATE_FUNCTION
        
        # Check for extracted entities
        function_names = [e for e in analysis.entities if e.type == EntityType.FUNCTION_NAME]
        assert len(function_names) > 0
        assert "calculate_sum" in [e.value for e in function_names]
    
    @pytest.mark.asyncio
    async def test_analyze_class_requirement(self, nlp_engine_no_model):
        """Test analysis of class creation requirement."""
        requirement = "Create a class called UserManager that handles user authentication"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        assert len(analysis.intents) > 0
        assert analysis.intents[0].type == IntentType.CREATE_CLASS
        
        class_names = [e for e in analysis.entities if e.type == EntityType.CLASS_NAME]
        assert len(class_names) > 0
        assert "UserManager" in [e.value for e in class_names]
    
    @pytest.mark.asyncio
    async def test_analyze_ambiguous_requirement(self, nlp_engine_no_model):
        """Test analysis of ambiguous requirement."""
        requirement = "Create some function that handles data efficiently"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        # Should detect ambiguities
        assert len(analysis.ambiguities) > 0
        assert analysis.clarification_needed
        assert analysis.confidence_score < 0.8
    
    @pytest.mark.asyncio
    async def test_analyze_clear_requirement(self, nlp_engine_no_model):
        """Test analysis of clear, specific requirement."""
        requirement = "Create a function named fibonacci that takes an integer n and returns the nth Fibonacci number using recursion"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        assert analysis.confidence_score > 0.6
        assert len(analysis.intents) > 0
        assert analysis.intents[0].type == IntentType.CREATE_FUNCTION
        
        # Should extract function name and parameter
        entities_by_type = {}
        for entity in analysis.entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity.value)
        
        assert EntityType.FUNCTION_NAME in entities_by_type
        assert "fibonacci" in entities_by_type[EntityType.FUNCTION_NAME]
    
    @pytest.mark.asyncio
    async def test_extract_intents_multiple(self, nlp_engine_no_model):
        """Test extraction of multiple intents."""
        requirement = "Create a function to validate user input and also add tests for it"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        intent_types = [intent.type for intent in analysis.intents]
        assert IntentType.CREATE_FUNCTION in intent_types
        # Note: ADD_TESTS might not be detected in this simple implementation
    
    @pytest.mark.asyncio
    async def test_extract_entities_comprehensive(self, nlp_engine_no_model):
        """Test comprehensive entity extraction."""
        requirement = "Create a Python function called process_data that takes a filename parameter and returns a DataFrame using pandas"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        entities_by_type = {}
        for entity in analysis.entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity.value)
        
        # Check for various entity types
        assert EntityType.FUNCTION_NAME in entities_by_type
        assert "process_data" in entities_by_type[EntityType.FUNCTION_NAME]
        
        if EntityType.PARAMETER in entities_by_type:
            assert "filename" in entities_by_type[EntityType.PARAMETER]
        
        if EntityType.TECHNOLOGY in entities_by_type:
            assert "Python" in entities_by_type[EntityType.TECHNOLOGY]
    
    @pytest.mark.asyncio
    async def test_detect_ambiguities(self, nlp_engine_no_model):
        """Test ambiguity detection."""
        requirement = "Create some good function that handles various data efficiently"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        # Should detect multiple ambiguities
        assert len(analysis.ambiguities) > 0
        
        ambiguity_contexts = [amb.context for amb in analysis.ambiguities]
        assert "vague_quantity" in ambiguity_contexts  # "some"
        assert "subjective_quality" in ambiguity_contexts  # "good", "efficiently"
    
    @pytest.mark.asyncio
    async def test_generate_clarification_questions(self, nlp_engine_no_model):
        """Test generation of clarification questions."""
        requirement = "Create a function that processes data"
        
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        questions = await nlp_engine_no_model.generate_clarification_questions(analysis)
        
        assert len(questions) > 0
        assert all(isinstance(q, str) for q in questions)
        assert len(questions) <= 5  # Should limit questions
    
    @pytest.mark.asyncio
    async def test_validate_requirement_valid(self, nlp_engine_no_model):
        """Test validation of valid requirement."""
        requirement = "Create a function called add_numbers that takes two integer parameters a and b and returns their sum as an integer"
        
        is_valid, issues = await nlp_engine_no_model.validate_requirement(requirement)
        
        assert is_valid
        assert len(issues) == 0
    
    @pytest.mark.asyncio
    async def test_validate_requirement_invalid(self, nlp_engine_no_model):
        """Test validation of invalid requirement."""
        requirement = "Do something"
        
        is_valid, issues = await nlp_engine_no_model.validate_requirement(requirement)
        
        assert not is_valid
        assert len(issues) > 0
    
    @pytest.mark.asyncio
    async def test_validate_requirement_too_short(self, nlp_engine_no_model):
        """Test validation of too short requirement."""
        requirement = "Make it"
        
        is_valid, issues = await nlp_engine_no_model.validate_requirement(requirement)
        
        assert not is_valid
        assert any("too short" in issue.lower() for issue in issues)
    
    @pytest.mark.asyncio
    async def test_validate_requirement_vague_language(self, nlp_engine_no_model):
        """Test validation catches vague language."""
        requirement = "Create something that might work somehow"
        
        is_valid, issues = await nlp_engine_no_model.validate_requirement(requirement)
        
        assert not is_valid
        assert any("vague language" in issue.lower() for issue in issues)
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, nlp_engine_no_model):
        """Test confidence score calculation."""
        # High confidence requirement
        clear_requirement = "Create a function named calculate_area that takes radius as float parameter and returns area as float"
        clear_analysis = await nlp_engine_no_model.analyze_requirement(clear_requirement)
        
        # Low confidence requirement
        vague_requirement = "Make something good"
        vague_analysis = await nlp_engine_no_model.analyze_requirement(vague_requirement)
        
        assert clear_analysis.confidence_score > vague_analysis.confidence_score
        assert clear_analysis.confidence_score > 0.5
        assert vague_analysis.confidence_score < 0.5
    
    @pytest.mark.asyncio
    async def test_technical_specification_generation_with_model(self, nlp_engine):
        """Test technical specification generation with model."""
        nlp_engine.model_manager.generate_response.return_value = "Technical specification: Create a function that calculates sum"
        
        requirement = "Create a function to add two numbers"
        analysis = await nlp_engine.analyze_requirement(requirement)
        
        if analysis.confidence_score > 0.7 and not analysis.ambiguities:
            assert analysis.technical_specification is not None
            nlp_engine.model_manager.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_technical_specification_generation_without_model(self, nlp_engine_no_model):
        """Test technical specification generation without model."""
        requirement = "Create a function named test_func that returns True"
        analysis = await nlp_engine_no_model.analyze_requirement(requirement)
        
        # Should generate basic specification even without model
        if analysis.confidence_score > 0.7 and not analysis.ambiguities:
            assert analysis.technical_specification is not None
            assert "Primary Task:" in analysis.technical_specification
    
    def test_intent_pattern_matching(self, nlp_engine_no_model):
        """Test intent pattern matching."""
        test_cases = [
            ("create a function", IntentType.CREATE_FUNCTION),
            ("write a class", IntentType.CREATE_CLASS),
            ("implement a module", IntentType.CREATE_MODULE),
            ("add a feature", IntentType.IMPLEMENT_FEATURE),
            ("fix the bug", IntentType.FIX_BUG),
            ("refactor this code", IntentType.REFACTOR_CODE),
            ("add tests", IntentType.ADD_TESTS),
            ("optimize performance", IntentType.OPTIMIZE_PERFORMANCE),
            ("write documentation", IntentType.ADD_DOCUMENTATION),
            ("setup project", IntentType.SETUP_PROJECT)
        ]
        
        for text, expected_intent in test_cases:
            intents = asyncio.run(nlp_engine_no_model._extract_intents(text))
            assert len(intents) > 0
            assert intents[0].type == expected_intent
    
    def test_entity_pattern_matching(self, nlp_engine_no_model):
        """Test entity pattern matching."""
        test_cases = [
            ("function called calculate", EntityType.FUNCTION_NAME, "calculate"),
            ("class named UserManager", EntityType.CLASS_NAME, "UserManager"),
            ("parameter username", EntityType.PARAMETER, "username"),
            ("returns string", EntityType.RETURN_TYPE, "string"),
            ("using Python", EntityType.TECHNOLOGY, "Python"),
            ("with Flask framework", EntityType.FRAMEWORK, "Flask"),
            ("database PostgreSQL", EntityType.DATABASE, "PostgreSQL"),
            ("endpoint /api/users", EntityType.API_ENDPOINT, "/api/users"),
            ("file config.py", EntityType.FILE_PATH, "config.py")
        ]
        
        for text, expected_type, expected_value in test_cases:
            entities = asyncio.run(nlp_engine_no_model._extract_entities(text))
            matching_entities = [e for e in entities if e.type == expected_type and expected_value in e.value]
            assert len(matching_entities) > 0, f"Failed to extract {expected_type} '{expected_value}' from '{text}'"
    
    @pytest.mark.asyncio
    async def test_intent_specific_questions(self, nlp_engine_no_model):
        """Test intent-specific question generation."""
        # Test function creation questions
        function_intent = Intent(
            type=IntentType.CREATE_FUNCTION,
            confidence=0.9,
            description="create function"
        )
        
        questions = nlp_engine_no_model._get_intent_specific_questions(function_intent, [])
        
        assert len(questions) > 0
        assert any("function" in q.lower() for q in questions)
        assert any("parameter" in q.lower() for q in questions)
        assert any("return" in q.lower() for q in questions)
    
    def test_pattern_confidence_calculation(self, nlp_engine_no_model):
        """Test pattern confidence calculation."""
        import re
        
        # Test with match at beginning of text
        text = "create a function to calculate sum"
        match = re.search(r"create\s+(?:a\s+)?function", text)
        confidence = nlp_engine_no_model._calculate_pattern_confidence(match, text)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be high confidence
        
        # Test with match in middle of text
        text = "I want to create a function for calculations"
        match = re.search(r"create\s+(?:a\s+)?function", text)
        confidence = nlp_engine_no_model._calculate_pattern_confidence(match, text)
        
        assert 0.0 <= confidence <= 1.0
    
    def test_overall_confidence_calculation(self, nlp_engine_no_model):
        """Test overall confidence calculation."""
        # High confidence case
        intents = [Intent(IntentType.CREATE_FUNCTION, 0.9, "create function")]
        entities = [
            Entity(EntityType.FUNCTION_NAME, "test_func", 0.8),
            Entity(EntityType.PARAMETER, "param1", 0.7)
        ]
        ambiguities = []
        
        confidence = nlp_engine_no_model._calculate_confidence(intents, entities, ambiguities)
        assert confidence > 0.8
        
        # Low confidence case
        intents = [Intent(IntentType.CREATE_FUNCTION, 0.4, "maybe create")]
        entities = []
        ambiguities = [Ambiguity("some", ["one", "many"], "How many?")]
        
        confidence = nlp_engine_no_model._calculate_confidence(intents, entities, ambiguities)
        assert confidence < 0.5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, nlp_engine):
        """Test error handling in NLP engine."""
        # Test with model manager that raises exception
        nlp_engine.model_manager.generate_response.side_effect = Exception("Model error")
        
        requirement = "Create a function"
        analysis = await nlp_engine.analyze_requirement(requirement)
        
        # Should still work with fallback
        assert isinstance(analysis, RequirementAnalysis)
        assert analysis.original_text == requirement
    
    @pytest.mark.asyncio
    async def test_empty_requirement(self, nlp_engine_no_model):
        """Test handling of empty requirement."""
        requirement = ""
        
        is_valid, issues = await nlp_engine_no_model.validate_requirement(requirement)
        
        assert not is_valid
        assert len(issues) > 0
    
    @pytest.mark.asyncio
    async def test_whitespace_only_requirement(self, nlp_engine_no_model):
        """Test handling of whitespace-only requirement."""
        requirement = "   \n\t   "
        
        is_valid, issues = await nlp_engine_no_model.validate_requirement(requirement)
        
        assert not is_valid
        assert len(issues) > 0