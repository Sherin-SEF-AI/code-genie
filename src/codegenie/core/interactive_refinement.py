"""
Interactive Clarification and Refinement System

This module provides interactive workflows for clarifying requirements,
refining code generation, and iteratively improving explanations.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from .nlp_engine import RequirementAnalysis
from .requirement_processor import ClarificationSession, RequirementProcessor
from .code_generator import CodeGenerator, CodeGenerationRequest, GeneratedCode
from .explanation_engine import ExplanationEngine, ExplanationRequest, CodeExplanation
from ..models.model_manager import ModelManager


class InteractionType(Enum):
    """Types of user interactions."""
    CLARIFICATION_QUESTION = "clarification_question"
    CODE_FEEDBACK = "code_feedback"
    EXPLANATION_REQUEST = "explanation_request"
    REFINEMENT_REQUEST = "refinement_request"
    ALTERNATIVE_REQUEST = "alternative_request"


class RefinementType(Enum):
    """Types of refinements."""
    REQUIREMENT_REFINEMENT = "requirement_refinement"
    CODE_REFINEMENT = "code_refinement"
    EXPLANATION_REFINEMENT = "explanation_refinement"
    DOCUMENTATION_REFINEMENT = "documentation_refinement"


@dataclass
class UserFeedback:
    """Represents user feedback on generated content."""
    feedback_type: str  # "positive", "negative", "suggestion"
    content: str
    target: str  # What the feedback is about
    specific_issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    rating: Optional[int] = None  # 1-5 scale


@dataclass
class RefinementRequest:
    """Request for refining generated content."""
    refinement_type: RefinementType
    original_content: str
    feedback: UserFeedback
    additional_context: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractiveSession:
    """Manages an interactive session with the user."""
    session_id: str
    current_requirement: str
    clarification_session: Optional[ClarificationSession] = None
    generated_code: Optional[GeneratedCode] = None
    explanations: List[CodeExplanation] = field(default_factory=list)
    feedback_history: List[UserFeedback] = field(default_factory=list)
    refinement_iterations: int = 0
    max_iterations: int = 5
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionResponse:
    """Response to user interaction."""
    success: bool
    response_type: InteractionType
    content: str
    options: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class InteractiveRefinementEngine:
    """
    Manages interactive clarification and refinement workflows.
    
    This engine provides conversational interfaces for iteratively
    improving requirements, code generation, and explanations based
    on user feedback and preferences.
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self.requirement_processor = RequirementProcessor(model_manager)
        self.code_generator = CodeGenerator(model_manager)
        self.explanation_engine = ExplanationEngine(model_manager)
        self.active_sessions: Dict[str, InteractiveSession] = {}
        self._interaction_handlers = self._setup_interaction_handlers()
    
    def _setup_interaction_handlers(self) -> Dict[InteractionType, Callable]:
        """Setup handlers for different interaction types."""
        return {
            InteractionType.CLARIFICATION_QUESTION: self._handle_clarification_question,
            InteractionType.CODE_FEEDBACK: self._handle_code_feedback,
            InteractionType.EXPLANATION_REQUEST: self._handle_explanation_request,
            InteractionType.REFINEMENT_REQUEST: self._handle_refinement_request,
            InteractionType.ALTERNATIVE_REQUEST: self._handle_alternative_request
        }
    
    async def start_interactive_session(self, requirement: str, 
                                      session_id: Optional[str] = None,
                                      user_preferences: Optional[Dict[str, Any]] = None) -> InteractiveSession:
        """
        Start a new interactive session for requirement processing.
        
        Args:
            requirement: Initial requirement text
            session_id: Optional session ID
            user_preferences: Optional user preferences
            
        Returns:
            InteractiveSession object
        """
        session_id = session_id or f"interactive_{len(self.active_sessions) + 1}"
        
        # Process initial requirement
        clarification_session = await self.requirement_processor.process_requirement(
            requirement, session_id
        )
        
        session = InteractiveSession(
            session_id=session_id,
            current_requirement=requirement,
            clarification_session=clarification_session,
            user_preferences=user_preferences or {}
        )
        
        self.active_sessions[session_id] = session
        return session
    
    async def handle_user_interaction(self, session_id: str, 
                                    interaction_type: InteractionType,
                                    user_input: str,
                                    context: Optional[Dict[str, Any]] = None) -> InteractionResponse:
        """
        Handle user interaction in an active session.
        
        Args:
            session_id: The session ID
            interaction_type: Type of interaction
            user_input: User's input/response
            context: Optional additional context
            
        Returns:
            InteractionResponse with appropriate response
        """
        if session_id not in self.active_sessions:
            return InteractionResponse(
                success=False,
                response_type=interaction_type,
                content="Session not found. Please start a new session."
            )
        
        session = self.active_sessions[session_id]
        
        # Route to appropriate handler
        handler = self._interaction_handlers.get(interaction_type)
        if not handler:
            return InteractionResponse(
                success=False,
                response_type=interaction_type,
                content="Unsupported interaction type."
            )
        
        return await handler(session, user_input, context or {})
    
    async def _handle_clarification_question(self, session: InteractiveSession,
                                           user_input: str,
                                           context: Dict[str, Any]) -> InteractionResponse:
        """Handle clarification question responses."""
        
        if not session.clarification_session:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.CLARIFICATION_QUESTION,
                content="No active clarification session."
            )
        
        # Find the question being answered
        question_id = context.get("question_id")
        if not question_id:
            # Try to match the question based on context
            question_id = self._find_matching_question(session.clarification_session, user_input)
        
        if not question_id:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.CLARIFICATION_QUESTION,
                content="Could not identify which question you're answering. Please specify."
            )
        
        # Answer the question
        updated_session = await self.requirement_processor.answer_clarification_question(
            session.clarification_session.session_id,
            question_id,
            user_input
        )
        
        session.clarification_session = updated_session
        
        # Check if more questions remain
        unanswered_questions = [
            q for q in updated_session.questions 
            if not q.answered and q.required
        ]
        
        if unanswered_questions:
            next_question = unanswered_questions[0]
            return InteractionResponse(
                success=True,
                response_type=InteractionType.CLARIFICATION_QUESTION,
                content=f"Thank you! Next question: {next_question.question}",
                options=next_question.possible_answers,
                metadata={"question_id": next_question.id}
            )
        else:
            # All questions answered, proceed to code generation
            return await self._proceed_to_code_generation(session)
    
    async def _handle_code_feedback(self, session: InteractiveSession,
                                  user_input: str,
                                  context: Dict[str, Any]) -> InteractionResponse:
        """Handle feedback on generated code."""
        
        if not session.generated_code:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.CODE_FEEDBACK,
                content="No code has been generated yet."
            )
        
        # Parse feedback
        feedback = await self._parse_user_feedback(user_input, "code")
        session.feedback_history.append(feedback)
        
        if feedback.feedback_type == "positive":
            return InteractionResponse(
                success=True,
                response_type=InteractionType.CODE_FEEDBACK,
                content="Great! I'm glad the code meets your needs. Would you like me to explain any part of it or generate documentation?",
                options=["Explain the code", "Generate documentation", "I'm done"]
            )
        
        elif feedback.feedback_type == "negative" or feedback.feedback_type == "suggestion":
            # Offer refinement options
            return InteractionResponse(
                success=True,
                response_type=InteractionType.CODE_FEEDBACK,
                content="I understand you'd like some changes. What would you like me to do?",
                options=[
                    "Refine the existing code",
                    "Generate a completely different approach",
                    "Explain the current approach first",
                    "Ask me more specific questions"
                ],
                suggestions=self._generate_improvement_suggestions(feedback)
            )
    
    async def _handle_explanation_request(self, session: InteractiveSession,
                                        user_input: str,
                                        context: Dict[str, Any]) -> InteractionResponse:
        """Handle requests for code explanation."""
        
        if not session.generated_code:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.EXPLANATION_REQUEST,
                content="No code available to explain."
            )
        
        # Parse what kind of explanation is requested
        explanation_type = await self._parse_explanation_request(user_input)
        
        # Generate explanation
        explanation_request = ExplanationRequest(
            code=session.generated_code.code,
            language=session.generated_code.language,
            explanation_types=[explanation_type],
            target_audience=session.user_preferences.get("experience_level", "developer"),
            include_examples=True,
            context=session.current_requirement
        )
        
        explanations = await self.explanation_engine.explain_code(explanation_request)
        
        if explanations:
            explanation = explanations[0]
            session.explanations.append(explanation)
            
            return InteractionResponse(
                success=True,
                response_type=InteractionType.EXPLANATION_REQUEST,
                content=explanation.content,
                follow_up_questions=[
                    "Would you like a more detailed explanation of any part?",
                    "Should I explain the trade-offs in this approach?",
                    "Do you want to see alternative implementations?"
                ]
            )
        else:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.EXPLANATION_REQUEST,
                content="I couldn't generate an explanation. Could you be more specific about what you'd like explained?"
            )
    
    async def _handle_refinement_request(self, session: InteractiveSession,
                                       user_input: str,
                                       context: Dict[str, Any]) -> InteractionResponse:
        """Handle requests for refining generated content."""
        
        refinement_type = context.get("refinement_type", RefinementType.CODE_REFINEMENT)
        
        if refinement_type == RefinementType.CODE_REFINEMENT and not session.generated_code:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.REFINEMENT_REQUEST,
                content="No code available to refine."
            )
        
        # Check iteration limit
        if session.refinement_iterations >= session.max_iterations:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.REFINEMENT_REQUEST,
                content="Maximum refinement iterations reached. Please start a new session for major changes."
            )
        
        # Parse refinement request
        feedback = await self._parse_user_feedback(user_input, "refinement")
        
        # Perform refinement
        if refinement_type == RefinementType.CODE_REFINEMENT:
            refined_code = await self._refine_code(session, feedback)
            if refined_code:
                session.generated_code = refined_code
                session.refinement_iterations += 1
                
                return InteractionResponse(
                    success=True,
                    response_type=InteractionType.REFINEMENT_REQUEST,
                    content="I've refined the code based on your feedback. Here's the updated version:",
                    metadata={"refined_code": refined_code.code},
                    follow_up_questions=[
                        "Does this look better?",
                        "Would you like me to explain the changes?",
                        "Any other improvements needed?"
                    ]
                )
        
        return InteractionResponse(
            success=False,
            response_type=InteractionType.REFINEMENT_REQUEST,
            content="I couldn't refine the content as requested. Could you provide more specific guidance?"
        )
    
    async def _handle_alternative_request(self, session: InteractiveSession,
                                        user_input: str,
                                        context: Dict[str, Any]) -> InteractionResponse:
        """Handle requests for alternative implementations."""
        
        if not session.clarification_session or not session.clarification_session.final_specification:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.ALTERNATIVE_REQUEST,
                content="Need a clear specification to generate alternatives."
            )
        
        # Generate alternative implementation
        alternative_request = CodeGenerationRequest(
            requirement=session.clarification_session.final_specification,
            language=session.generated_code.language if session.generated_code else session.user_preferences.get("language", "python"),
            strategy="ai_driven",  # Use different strategy for alternatives
            include_tests=session.user_preferences.get("include_tests", True)
        )
        
        result = await self.code_generator.generate_code(
            alternative_request,
            session.clarification_session.analysis
        )
        
        if result.success and result.generated_code:
            return InteractionResponse(
                success=True,
                response_type=InteractionType.ALTERNATIVE_REQUEST,
                content="Here's an alternative implementation approach:",
                metadata={"alternative_code": result.generated_code.code},
                options=[
                    "Use this alternative",
                    "Compare with previous version",
                    "Generate another alternative",
                    "Stick with original"
                ]
            )
        else:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.ALTERNATIVE_REQUEST,
                content="I couldn't generate an alternative implementation. The current approach might be optimal."
            )
    
    async def _proceed_to_code_generation(self, session: InteractiveSession) -> InteractionResponse:
        """Proceed to code generation after clarification is complete."""
        
        if not session.clarification_session or not session.clarification_session.final_specification:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.CLARIFICATION_QUESTION,
                content="Specification is not ready for code generation."
            )
        
        # Generate code
        generation_request = CodeGenerationRequest(
            requirement=session.clarification_session.final_specification,
            language=session.user_preferences.get("language", "python"),
            include_tests=session.user_preferences.get("include_tests", True),
            include_documentation=session.user_preferences.get("include_documentation", True)
        )
        
        result = await self.code_generator.generate_code(
            generation_request,
            session.clarification_session.analysis,
            session.clarification_session
        )
        
        if result.success and result.generated_code:
            session.generated_code = result.generated_code
            
            return InteractionResponse(
                success=True,
                response_type=InteractionType.CLARIFICATION_QUESTION,
                content="Perfect! I've generated the code based on your requirements. Here it is:",
                metadata={"generated_code": result.generated_code.code},
                follow_up_questions=[
                    "Does this look correct?",
                    "Would you like me to explain how it works?",
                    "Any changes needed?"
                ]
            )
        else:
            return InteractionResponse(
                success=False,
                response_type=InteractionType.CLARIFICATION_QUESTION,
                content="I encountered an issue generating the code. Let me ask a few more questions to clarify.",
                suggestions=["Could you provide more specific details about the implementation?"]
            )
    
    def _find_matching_question(self, clarification_session: ClarificationSession, 
                              user_input: str) -> Optional[str]:
        """Find which question the user is answering based on context."""
        
        # Simple matching - in practice, would use more sophisticated NLP
        for question in clarification_session.questions:
            if not question.answered and question.required:
                return question.id
        
        return None
    
    async def _parse_user_feedback(self, user_input: str, target: str) -> UserFeedback:
        """Parse user feedback to extract sentiment and specific issues."""
        
        # Simple sentiment analysis - in practice, would use more sophisticated NLP
        positive_words = ["good", "great", "perfect", "excellent", "correct", "right"]
        negative_words = ["bad", "wrong", "incorrect", "issue", "problem", "error"]
        
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in positive_words):
            feedback_type = "positive"
        elif any(word in user_input_lower for word in negative_words):
            feedback_type = "negative"
        else:
            feedback_type = "suggestion"
        
        # Extract specific issues (simplified)
        issues = []
        if "too complex" in user_input_lower:
            issues.append("complexity")
        if "too simple" in user_input_lower:
            issues.append("simplicity")
        if "performance" in user_input_lower:
            issues.append("performance")
        if "error" in user_input_lower:
            issues.append("errors")
        
        return UserFeedback(
            feedback_type=feedback_type,
            content=user_input,
            target=target,
            specific_issues=issues
        )
    
    async def _parse_explanation_request(self, user_input: str):
        """Parse what type of explanation is being requested."""
        from .explanation_engine import ExplanationType
        
        user_input_lower = user_input.lower()
        
        if "line by line" in user_input_lower or "step by step" in user_input_lower:
            return ExplanationType.LINE_BY_LINE
        elif "algorithm" in user_input_lower:
            return ExplanationType.ALGORITHM
        elif "pattern" in user_input_lower:
            return ExplanationType.DESIGN_PATTERNS
        elif "performance" in user_input_lower:
            return ExplanationType.PERFORMANCE
        elif "security" in user_input_lower:
            return ExplanationType.SECURITY
        elif "best practice" in user_input_lower:
            return ExplanationType.BEST_PRACTICES
        elif "trade" in user_input_lower or "tradeoff" in user_input_lower:
            return ExplanationType.TRADE_OFFS
        else:
            return ExplanationType.OVERVIEW
    
    def _generate_improvement_suggestions(self, feedback: UserFeedback) -> List[str]:
        """Generate suggestions for improvement based on feedback."""
        
        suggestions = []
        
        for issue in feedback.specific_issues:
            if issue == "complexity":
                suggestions.append("Break down into smaller functions")
                suggestions.append("Add more comments for clarity")
            elif issue == "performance":
                suggestions.append("Optimize algorithms for better performance")
                suggestions.append("Consider caching or memoization")
            elif issue == "errors":
                suggestions.append("Add more comprehensive error handling")
                suggestions.append("Include input validation")
        
        if not suggestions:
            suggestions = [
                "Provide more specific feedback about what to improve",
                "Tell me which part needs changes",
                "Describe your preferred approach"
            ]
        
        return suggestions
    
    async def _refine_code(self, session: InteractiveSession, 
                         feedback: UserFeedback) -> Optional[GeneratedCode]:
        """Refine code based on user feedback."""
        
        if not session.generated_code:
            return None
        
        # Create refinement prompt
        refinement_prompt = f"""
Refine this code based on the user feedback:

Original Code:
```{session.generated_code.language.value}
{session.generated_code.code}
```

User Feedback: {feedback.content}

Specific Issues: {', '.join(feedback.specific_issues)}

Please provide improved code that addresses the feedback while maintaining the original functionality.

Refined Code:
"""
        
        try:
            response = await self.model_manager.generate_response(
                prompt=refinement_prompt,
                model_type="code_generation",
                max_tokens=1500
            )
            
            # Extract refined code
            import re
            code_pattern = rf"```{session.generated_code.language.value}\n(.*?)\n```"
            code_match = re.search(code_pattern, response, re.DOTALL | re.IGNORECASE)
            
            if code_match:
                refined_code_text = code_match.group(1).strip()
                
                # Create new GeneratedCode object with refined code
                refined_code = GeneratedCode(
                    code=refined_code_text,
                    language=session.generated_code.language,
                    file_path=session.generated_code.file_path,
                    dependencies=session.generated_code.dependencies,
                    imports=session.generated_code.imports,
                    tests=session.generated_code.tests,
                    documentation=session.generated_code.documentation
                )
                
                return refined_code
            
        except Exception:
            pass
        
        return None
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an interactive session."""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session.session_id,
            "current_requirement": session.current_requirement,
            "clarification_complete": (
                session.clarification_session and 
                session.clarification_session.status.value == "completed"
            ),
            "code_generated": session.generated_code is not None,
            "explanations_count": len(session.explanations),
            "feedback_count": len(session.feedback_history),
            "refinement_iterations": session.refinement_iterations,
            "max_iterations": session.max_iterations
        }
    
    def end_session(self, session_id: str) -> bool:
        """End an interactive session and clean up resources."""
        
        if session_id in self.active_sessions:
            # Clean up clarification session
            if self.active_sessions[session_id].clarification_session:
                self.requirement_processor.cleanup_session(
                    self.active_sessions[session_id].clarification_session.session_id
                )
            
            del self.active_sessions[session_id]
            return True
        
        return False
    
    async def generate_session_summary(self, session_id: str) -> Optional[str]:
        """Generate a summary of the interactive session."""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        summary_parts = [
            f"Interactive Session Summary for {session_id}",
            f"Original Requirement: {session.current_requirement}",
            ""
        ]
        
        if session.clarification_session:
            summary_parts.extend([
                "Clarification Process:",
                f"- Questions asked: {len(session.clarification_session.questions)}",
                f"- Questions answered: {len([q for q in session.clarification_session.questions if q.answered])}",
                f"- Final specification: {session.clarification_session.final_specification or 'Not completed'}",
                ""
            ])
        
        if session.generated_code:
            summary_parts.extend([
                "Code Generation:",
                f"- Language: {session.generated_code.language.value}",
                f"- Lines of code: {len(session.generated_code.code.split(chr(10)))}",
                f"- Tests included: {'Yes' if session.generated_code.tests else 'No'}",
                ""
            ])
        
        if session.feedback_history:
            summary_parts.extend([
                "User Feedback:",
                f"- Total feedback items: {len(session.feedback_history)}",
                f"- Positive feedback: {len([f for f in session.feedback_history if f.feedback_type == 'positive'])}",
                f"- Refinement requests: {session.refinement_iterations}",
                ""
            ])
        
        if session.explanations:
            summary_parts.extend([
                "Explanations Provided:",
                f"- Total explanations: {len(session.explanations)}",
                f"- Explanation types: {', '.join(set(e.explanation_type.value for e in session.explanations))}",
                ""
            ])
        
        return "\n".join(summary_parts)