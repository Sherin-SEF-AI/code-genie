"""
Requirement Processing and Clarification System

This module handles the processing, validation, and clarification of user requirements
for natural language programming.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from .nlp_engine import NLPEngine, RequirementAnalysis, Ambiguity
from ..models.model_manager import ModelManager


class ClarificationStatus(Enum):
    """Status of requirement clarification process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationResult(Enum):
    """Result of requirement validation."""
    VALID = "valid"
    NEEDS_CLARIFICATION = "needs_clarification"
    INVALID = "invalid"


@dataclass
class ClarificationQuestion:
    """Represents a clarification question for the user."""
    id: str
    question: str
    context: str
    possible_answers: List[str] = field(default_factory=list)
    required: bool = True
    answered: bool = False
    answer: Optional[str] = None


@dataclass
class ClarificationSession:
    """Manages a clarification session for a requirement."""
    session_id: str
    original_requirement: str
    analysis: RequirementAnalysis
    questions: List[ClarificationQuestion] = field(default_factory=list)
    status: ClarificationStatus = ClarificationStatus.PENDING
    refined_requirement: Optional[str] = None
    final_specification: Optional[str] = None


@dataclass
class RequirementValidation:
    """Result of requirement validation."""
    is_valid: bool
    validation_result: ValidationResult
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


class RequirementProcessor:
    """
    Processes and validates user requirements for natural language programming.
    
    This class handles the complete workflow from initial requirement analysis
    to final validated specification ready for code generation.
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.nlp_engine = NLPEngine(model_manager)
        self.model_manager = model_manager
        self.active_sessions: Dict[str, ClarificationSession] = {}
    
    async def process_requirement(self, requirement: str, session_id: Optional[str] = None) -> ClarificationSession:
        """
        Process a natural language requirement and create a clarification session.
        
        Args:
            requirement: The natural language requirement text
            session_id: Optional existing session ID to continue
            
        Returns:
            ClarificationSession with analysis and questions
        """
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            # Update the requirement if it's different
            if session.original_requirement != requirement:
                session.original_requirement = requirement
                session.analysis = await self.nlp_engine.analyze_requirement(requirement)
                session.questions = await self._generate_clarification_questions(session.analysis)
                session.status = ClarificationStatus.PENDING
        else:
            # Create new session
            analysis = await self.nlp_engine.analyze_requirement(requirement)
            questions = await self._generate_clarification_questions(analysis)
            
            session_id = session_id or f"session_{len(self.active_sessions) + 1}"
            session = ClarificationSession(
                session_id=session_id,
                original_requirement=requirement,
                analysis=analysis,
                questions=questions,
                status=ClarificationStatus.PENDING if questions else ClarificationStatus.COMPLETED
            )
            
            self.active_sessions[session_id] = session
        
        return session
    
    async def validate_requirement(self, requirement: str) -> RequirementValidation:
        """
        Validate a requirement for completeness and clarity.
        
        Args:
            requirement: The requirement text to validate
            
        Returns:
            RequirementValidation with validation results
        """
        # Basic validation using NLP engine
        is_valid, issues = await self.nlp_engine.validate_requirement(requirement)
        
        # Analyze the requirement
        analysis = await self.nlp_engine.analyze_requirement(requirement)
        
        # Determine validation result
        if is_valid and analysis.confidence_score > 0.8 and not analysis.ambiguities:
            validation_result = ValidationResult.VALID
        elif analysis.clarification_needed or analysis.ambiguities:
            validation_result = ValidationResult.NEEDS_CLARIFICATION
        else:
            validation_result = ValidationResult.INVALID
        
        # Generate suggestions
        suggestions = await self._generate_validation_suggestions(analysis, issues)
        
        return RequirementValidation(
            is_valid=is_valid,
            validation_result=validation_result,
            issues=issues,
            suggestions=suggestions,
            confidence_score=analysis.confidence_score
        )
    
    async def answer_clarification_question(self, session_id: str, question_id: str, 
                                          answer: str) -> ClarificationSession:
        """
        Answer a clarification question and update the session.
        
        Args:
            session_id: The clarification session ID
            question_id: The question ID to answer
            answer: The user's answer
            
        Returns:
            Updated ClarificationSession
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Find and update the question
        for question in session.questions:
            if question.id == question_id:
                question.answer = answer
                question.answered = True
                break
        else:
            raise ValueError(f"Question {question_id} not found in session {session_id}")
        
        # Check if all required questions are answered
        all_answered = all(
            q.answered or not q.required 
            for q in session.questions
        )
        
        if all_answered:
            session.status = ClarificationStatus.COMPLETED
            # Generate refined requirement and specification
            session.refined_requirement = await self._generate_refined_requirement(session)
            session.final_specification = await self._generate_final_specification(session)
        else:
            session.status = ClarificationStatus.IN_PROGRESS
        
        return session
    
    async def get_clarification_status(self, session_id: str) -> Optional[ClarificationSession]:
        """Get the current status of a clarification session."""
        return self.active_sessions.get(session_id)
    
    async def _generate_clarification_questions(self, analysis: RequirementAnalysis) -> List[ClarificationQuestion]:
        """Generate clarification questions based on requirement analysis."""
        questions = []
        question_counter = 1
        
        # Questions from ambiguities
        for ambiguity in analysis.ambiguities:
            questions.append(ClarificationQuestion(
                id=f"q{question_counter}",
                question=ambiguity.clarification_question,
                context=ambiguity.context,
                possible_answers=ambiguity.possible_interpretations,
                required=True
            ))
            question_counter += 1
        
        # Generate additional questions using NLP engine
        additional_questions = await self.nlp_engine.generate_clarification_questions(analysis)
        
        for question_text in additional_questions:
            if not any(q.question == question_text for q in questions):
                questions.append(ClarificationQuestion(
                    id=f"q{question_counter}",
                    question=question_text,
                    context="general",
                    required=True
                ))
                question_counter += 1
        
        # Add intent-specific questions
        if analysis.intents:
            intent_questions = await self._generate_intent_specific_questions(analysis.intents[0])
            for question_text in intent_questions:
                if not any(q.question == question_text for q in questions):
                    questions.append(ClarificationQuestion(
                        id=f"q{question_counter}",
                        question=question_text,
                        context="intent_specific",
                        required=False
                    ))
                    question_counter += 1
        
        return questions
    
    async def _generate_intent_specific_questions(self, intent) -> List[str]:
        """Generate questions specific to the detected intent."""
        from .nlp_engine import IntentType
        
        questions = []
        
        if intent.type == IntentType.CREATE_FUNCTION:
            questions.extend([
                "What should the function do step by step?",
                "What error conditions should be handled?",
                "Are there any performance requirements?"
            ])
        elif intent.type == IntentType.CREATE_CLASS:
            questions.extend([
                "What is the main responsibility of this class?",
                "What other classes should it interact with?",
                "Should it inherit from any base class?"
            ])
        elif intent.type == IntentType.IMPLEMENT_FEATURE:
            questions.extend([
                "What are the acceptance criteria for this feature?",
                "How should the feature integrate with existing code?",
                "What user interface elements are needed?"
            ])
        elif intent.type == IntentType.SETUP_PROJECT:
            questions.extend([
                "What dependencies or libraries should be included?",
                "What project structure do you prefer?",
                "Do you need any specific configuration files?"
            ])
        
        return questions
    
    async def _generate_validation_suggestions(self, analysis: RequirementAnalysis, 
                                             issues: List[str]) -> List[str]:
        """Generate suggestions to improve the requirement."""
        suggestions = []
        
        if analysis.confidence_score < 0.5:
            suggestions.append("Try to be more specific about what you want to implement")
        
        if not analysis.intents:
            suggestions.append("Clearly state what action you want to perform (create, implement, fix, etc.)")
        
        if not analysis.entities:
            suggestions.append("Include specific names, types, or technologies you want to use")
        
        if analysis.ambiguities:
            suggestions.append("Replace vague terms with specific requirements")
        
        # Add suggestions based on detected intents
        if analysis.intents:
            intent = analysis.intents[0]
            intent_suggestions = self._get_intent_suggestions(intent)
            suggestions.extend(intent_suggestions)
        
        return suggestions
    
    def _get_intent_suggestions(self, intent) -> List[str]:
        """Get suggestions specific to the detected intent."""
        from .nlp_engine import IntentType
        
        suggestions = []
        
        if intent.type == IntentType.CREATE_FUNCTION:
            suggestions.extend([
                "Specify the function name, parameters, and return type",
                "Describe what the function should do in detail"
            ])
        elif intent.type == IntentType.CREATE_CLASS:
            suggestions.extend([
                "Specify the class name and its main purpose",
                "List the methods and attributes it should have"
            ])
        elif intent.type == IntentType.IMPLEMENT_FEATURE:
            suggestions.extend([
                "Break down the feature into specific requirements",
                "Describe the expected user interaction"
            ])
        
        return suggestions
    
    async def _generate_refined_requirement(self, session: ClarificationSession) -> str:
        """Generate a refined requirement based on answered questions."""
        original = session.original_requirement
        answers = {q.id: q.answer for q in session.questions if q.answered and q.answer}
        
        if not self.model_manager:
            return self._generate_basic_refined_requirement(original, answers)
        
        # Use AI model to generate refined requirement
        prompt = self._create_refinement_prompt(original, session.questions, answers)
        
        try:
            response = await self.model_manager.generate_response(
                prompt=prompt,
                model_type="text_generation",
                max_tokens=500
            )
            return response.strip()
        except Exception:
            return self._generate_basic_refined_requirement(original, answers)
    
    def _generate_basic_refined_requirement(self, original: str, answers: Dict[str, str]) -> str:
        """Generate a basic refined requirement without AI model."""
        refined_parts = [f"Original requirement: {original}"]
        
        if answers:
            refined_parts.append("\nAdditional details:")
            for answer in answers.values():
                if answer:
                    refined_parts.append(f"- {answer}")
        
        return "\n".join(refined_parts)
    
    def _create_refinement_prompt(self, original: str, questions: List[ClarificationQuestion], 
                                 answers: Dict[str, str]) -> str:
        """Create a prompt for AI-generated requirement refinement."""
        qa_pairs = []
        for question in questions:
            if question.id in answers and answers[question.id]:
                qa_pairs.append(f"Q: {question.question}\nA: {answers[question.id]}")
        
        return f"""
Refine this software requirement based on the clarification questions and answers:

Original Requirement: "{original}"

Clarification Q&A:
{chr(10).join(qa_pairs)}

Please provide a refined, detailed requirement that incorporates all the clarification answers and is ready for implementation:

Refined Requirement:
"""
    
    async def _generate_final_specification(self, session: ClarificationSession) -> str:
        """Generate the final technical specification."""
        if not session.refined_requirement:
            return ""
        
        # Re-analyze the refined requirement
        refined_analysis = await self.nlp_engine.analyze_requirement(session.refined_requirement)
        
        if refined_analysis.technical_specification:
            return refined_analysis.technical_specification
        
        # Generate specification manually if AI analysis didn't produce one
        return await self._generate_manual_specification(session)
    
    async def _generate_manual_specification(self, session: ClarificationSession) -> str:
        """Generate a manual technical specification."""
        spec_parts = []
        
        # Add requirement summary
        spec_parts.append(f"Requirement: {session.refined_requirement}")
        spec_parts.append("")
        
        # Add detected intents
        if session.analysis.intents:
            spec_parts.append("Implementation Tasks:")
            for intent in session.analysis.intents:
                spec_parts.append(f"- {intent.type.value}: {intent.description}")
            spec_parts.append("")
        
        # Add entities
        if session.analysis.entities:
            spec_parts.append("Components:")
            for entity in session.analysis.entities:
                spec_parts.append(f"- {entity.type.value}: {entity.value}")
            spec_parts.append("")
        
        # Add answered questions as requirements
        answered_questions = [q for q in session.questions if q.answered and q.answer]
        if answered_questions:
            spec_parts.append("Detailed Requirements:")
            for question in answered_questions:
                spec_parts.append(f"- {question.question}: {question.answer}")
        
        return "\n".join(spec_parts)

    async def resolve_ambiguity(self, session_id: str, ambiguity_text: str, 
                               resolution: str) -> ClarificationSession:
        """
        Resolve a specific ambiguity in the requirement.
        
        Args:
            session_id: The clarification session ID
            ambiguity_text: The ambiguous text to resolve
            resolution: The chosen resolution
            
        Returns:
            Updated ClarificationSession
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Find the corresponding question for this ambiguity
        for question in session.questions:
            if ambiguity_text.lower() in question.context.lower():
                question.answer = resolution
                question.answered = True
                break
        
        # Re-evaluate the session status
        all_answered = all(
            q.answered or not q.required 
            for q in session.questions
        )
        
        if all_answered:
            session.status = ClarificationStatus.COMPLETED
            session.refined_requirement = await self._generate_refined_requirement(session)
            session.final_specification = await self._generate_final_specification(session)
        
        return session

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the clarification session."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "original_requirement": session.original_requirement,
            "confidence_score": session.analysis.confidence_score,
            "total_questions": len(session.questions),
            "answered_questions": len([q for q in session.questions if q.answered]),
            "required_questions": len([q for q in session.questions if q.required]),
            "ambiguities_count": len(session.analysis.ambiguities),
            "intents_detected": [intent.type.value for intent in session.analysis.intents],
            "entities_detected": len(session.analysis.entities),
            "refined_requirement": session.refined_requirement,
            "has_final_specification": session.final_specification is not None
        }

    async def batch_process_requirements(self, requirements: List[str]) -> List[ClarificationSession]:
        """Process multiple requirements in batch."""
        sessions = []
        
        for i, requirement in enumerate(requirements):
            session_id = f"batch_session_{i + 1}"
            session = await self.process_requirement(requirement, session_id)
            sessions.append(session)
        
        return sessions

    def cleanup_session(self, session_id: str) -> bool:
        """Remove a completed or failed session from active sessions."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False