"""
Learning engine for user preference modeling and adaptive behavior.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of user feedback."""
    
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"
    PREFERENCE = "preference"
    SUGGESTION = "suggestion"


class LearningDomain(Enum):
    """Domains for learning and adaptation."""
    
    CODING_STYLE = "coding_style"
    ARCHITECTURE_PREFERENCE = "architecture_preference"
    TOOL_PREFERENCE = "tool_preference"
    COMMUNICATION_STYLE = "communication_style"
    WORKFLOW_PREFERENCE = "workflow_preference"
    ERROR_HANDLING = "error_handling"


@dataclass
class UserFeedback:
    """Represents user feedback for learning."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    feedback_type: FeedbackType = FeedbackType.POSITIVE
    domain: LearningDomain = LearningDomain.CODING_STYLE
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    # Associated data
    user_input: str = ""
    agent_response: str = ""
    suggested_improvement: str = ""
    
    # Learning metadata
    processed: bool = False
    confidence: float = 1.0
    impact_score: float = 0.0


@dataclass
class CodingStylePattern:
    """Represents a learned coding style pattern."""
    
    pattern_type: str  # "naming", "formatting", "structure", etc.
    pattern_value: Any
    confidence: float = 0.0
    evidence_count: int = 0
    last_updated: float = field(default_factory=time.time)
    examples: List[str] = field(default_factory=list)


@dataclass
class UserPreference:
    """Represents a learned user preference."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    domain: LearningDomain = LearningDomain.CODING_STYLE
    preference_key: str = ""
    preference_value: Any = None
    confidence: float = 0.0
    evidence_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    
    # Supporting evidence
    supporting_feedback: List[str] = field(default_factory=list)
    contradicting_feedback: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """Represents a personalized recommendation."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    recommendation_type: str = ""
    content: str = ""
    reasoning: str = ""
    confidence: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    # Tracking
    presented_to_user: bool = False
    user_response: Optional[str] = None
    effectiveness_score: Optional[float] = None


class UserPreferenceModeler:
    """Models user preferences based on interactions and feedback."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.preferences_file = self.storage_path / "user_preferences.json"
        self.coding_patterns_file = self.storage_path / "coding_patterns.json"
        
        # In-memory data
        self.preferences: Dict[str, UserPreference] = {}
        self.coding_patterns: Dict[str, CodingStylePattern] = {}
        
        # Load existing data
        self._load_data()
        
        logger.info("Initialized UserPreferenceModeler")
    
    def _load_data(self) -> None:
        """Load preferences and patterns from storage."""
        try:
            # Load preferences
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pref_data in data:
                        pref = self._deserialize_preference(pref_data)
                        self.preferences[pref.id] = pref
            
            # Load coding patterns
            if self.coding_patterns_file.exists():
                with open(self.coding_patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pattern_data in data:
                        pattern = self._deserialize_coding_pattern(pattern_data)
                        self.coding_patterns[pattern.pattern_type] = pattern
            
            logger.info(f"Loaded {len(self.preferences)} preferences and {len(self.coding_patterns)} coding patterns")
            
        except Exception as e:
            logger.error(f"Error loading preference data: {e}")
    
    def _save_data(self) -> None:
        """Save preferences and patterns to storage."""
        try:
            # Save preferences
            pref_data = [self._serialize_preference(pref) for pref in self.preferences.values()]
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(pref_data, f, indent=2)
            
            # Save coding patterns
            pattern_data = [self._serialize_coding_pattern(pattern) for pattern in self.coding_patterns.values()]
            with open(self.coding_patterns_file, 'w', encoding='utf-8') as f:
                json.dump(pattern_data, f, indent=2)
            
            logger.debug("Saved preference and pattern data")
            
        except Exception as e:
            logger.error(f"Error saving preference data: {e}")
    
    def learn_from_code(self, code: str, language: str = "python") -> None:
        """Learn coding style patterns from user code."""
        patterns = self._analyze_code_patterns(code, language)
        
        for pattern_type, pattern_value in patterns.items():
            if pattern_type in self.coding_patterns:
                # Update existing pattern
                pattern = self.coding_patterns[pattern_type]
                pattern.evidence_count += 1
                pattern.last_updated = time.time()
                
                # Update confidence based on consistency
                if pattern.pattern_value == pattern_value:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)
                else:
                    pattern.confidence = max(pattern.confidence - 0.05, 0.0)
                    # If confidence drops too low, update the pattern
                    if pattern.confidence < 0.3:
                        pattern.pattern_value = pattern_value
                        pattern.confidence = 0.5
                
                # Add example
                if len(pattern.examples) < 10:
                    pattern.examples.append(code[:100] + "..." if len(code) > 100 else code)
            
            else:
                # Create new pattern
                self.coding_patterns[pattern_type] = CodingStylePattern(
                    pattern_type=pattern_type,
                    pattern_value=pattern_value,
                    confidence=0.5,
                    evidence_count=1,
                    examples=[code[:100] + "..." if len(code) > 100 else code]
                )
        
        self._save_data()
    
    def learn_from_feedback(self, feedback: UserFeedback) -> None:
        """Learn preferences from user feedback."""
        # Extract preference from feedback
        preference_key = self._extract_preference_key(feedback)
        preference_value = self._extract_preference_value(feedback)
        
        if not preference_key:
            return
        
        # Find or create preference
        existing_pref = self._find_preference(feedback.domain, preference_key)
        
        if existing_pref:
            # Update existing preference
            self._update_preference(existing_pref, feedback, preference_value)
        else:
            # Create new preference
            new_pref = UserPreference(
                domain=feedback.domain,
                preference_key=preference_key,
                preference_value=preference_value,
                confidence=0.5,
                evidence_count=1,
                supporting_feedback=[feedback.id]
            )
            self.preferences[new_pref.id] = new_pref
        
        self._save_data()
    
    def get_coding_style_preferences(self) -> Dict[str, Any]:
        """Get learned coding style preferences."""
        style_prefs = {}
        
        for pattern in self.coding_patterns.values():
            if pattern.confidence > 0.3:  # Only include confident patterns
                style_prefs[pattern.pattern_type] = {
                    "value": pattern.pattern_value,
                    "confidence": pattern.confidence,
                    "evidence_count": pattern.evidence_count
                }
        
        return style_prefs
    
    def get_preferences_by_domain(self, domain: LearningDomain) -> Dict[str, Any]:
        """Get preferences for a specific domain."""
        domain_prefs = {}
        
        for pref in self.preferences.values():
            if pref.domain == domain and pref.confidence > 0.3:
                domain_prefs[pref.preference_key] = {
                    "value": pref.preference_value,
                    "confidence": pref.confidence,
                    "evidence_count": pref.evidence_count
                }
        
        return domain_prefs
    
    def _analyze_code_patterns(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code to extract style patterns."""
        patterns = {}
        
        if language == "python":
            patterns.update(self._analyze_python_patterns(code))
        elif language in ["javascript", "typescript"]:
            patterns.update(self._analyze_js_patterns(code))
        
        # General patterns
        patterns.update(self._analyze_general_patterns(code))
        
        return patterns
    
    def _analyze_python_patterns(self, code: str) -> Dict[str, Any]:
        """Analyze Python-specific patterns."""
        patterns = {}
        
        # Naming conventions
        import re
        
        # Function naming
        func_names = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        if func_names:
            snake_case_count = sum(1 for name in func_names if '_' in name and name.islower())
            camel_case_count = sum(1 for name in func_names if any(c.isupper() for c in name[1:]))
            
            if snake_case_count > camel_case_count:
                patterns["function_naming"] = "snake_case"
            elif camel_case_count > snake_case_count:
                patterns["function_naming"] = "camelCase"
        
        # Class naming
        class_names = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        if class_names:
            if all(name[0].isupper() for name in class_names):
                patterns["class_naming"] = "PascalCase"
        
        # Import style
        if 'from ' in code and ' import ' in code:
            patterns["import_style"] = "from_import"
        elif 'import ' in code:
            patterns["import_style"] = "direct_import"
        
        # Docstring style
        if '"""' in code:
            patterns["docstring_style"] = "triple_quotes"
        elif "'''" in code:
            patterns["docstring_style"] = "triple_single_quotes"
        
        return patterns
    
    def _analyze_js_patterns(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript patterns."""
        patterns = {}
        
        # Function declaration style
        if 'function ' in code:
            patterns["function_style"] = "function_declaration"
        elif '=>' in code:
            patterns["function_style"] = "arrow_function"
        
        # Variable declaration
        if 'const ' in code:
            patterns["variable_declaration"] = "const"
        elif 'let ' in code:
            patterns["variable_declaration"] = "let"
        elif 'var ' in code:
            patterns["variable_declaration"] = "var"
        
        return patterns
    
    def _analyze_general_patterns(self, code: str) -> Dict[str, Any]:
        """Analyze general code patterns."""
        patterns = {}
        
        # Indentation
        lines = code.split('\n')
        indented_lines = [line for line in lines if line.startswith(' ') or line.startswith('\t')]
        
        if indented_lines:
            space_indents = sum(1 for line in indented_lines if line.startswith(' '))
            tab_indents = sum(1 for line in indented_lines if line.startswith('\t'))
            
            if space_indents > tab_indents:
                # Detect space count
                space_counts = []
                for line in indented_lines:
                    if line.startswith(' '):
                        count = len(line) - len(line.lstrip(' '))
                        space_counts.append(count)
                
                if space_counts:
                    common_indent = max(set(space_counts), key=space_counts.count)
                    patterns["indentation"] = f"{common_indent}_spaces"
            else:
                patterns["indentation"] = "tabs"
        
        # Line length preference
        line_lengths = [len(line) for line in lines if line.strip()]
        if line_lengths:
            avg_length = sum(line_lengths) / len(line_lengths)
            max_length = max(line_lengths)
            
            if max_length > 120:
                patterns["line_length_preference"] = "long_lines"
            elif avg_length < 60:
                patterns["line_length_preference"] = "short_lines"
            else:
                patterns["line_length_preference"] = "medium_lines"
        
        return patterns
    
    def _extract_preference_key(self, feedback: UserFeedback) -> Optional[str]:
        """Extract preference key from feedback."""
        content_lower = feedback.content.lower()
        
        # Map feedback content to preference keys
        preference_mappings = {
            "verbose": "verbosity_level",
            "concise": "verbosity_level",
            "detailed": "detail_level",
            "simple": "complexity_preference",
            "complex": "complexity_preference",
            "explain": "explanation_preference",
            "comment": "comment_preference",
            "test": "testing_preference",
            "documentation": "documentation_preference"
        }
        
        for keyword, pref_key in preference_mappings.items():
            if keyword in content_lower:
                return pref_key
        
        return None
    
    def _extract_preference_value(self, feedback: UserFeedback) -> Any:
        """Extract preference value from feedback."""
        content_lower = feedback.content.lower()
        
        if feedback.feedback_type == FeedbackType.POSITIVE:
            # Positive feedback reinforces current behavior
            return "preferred"
        elif feedback.feedback_type == FeedbackType.NEGATIVE:
            # Negative feedback suggests opposite preference
            return "not_preferred"
        elif feedback.feedback_type == FeedbackType.PREFERENCE:
            # Extract specific preference value
            if "more" in content_lower:
                return "increase"
            elif "less" in content_lower:
                return "decrease"
            elif "verbose" in content_lower:
                return "verbose"
            elif "concise" in content_lower:
                return "concise"
        
        return feedback.content
    
    def _find_preference(self, domain: LearningDomain, preference_key: str) -> Optional[UserPreference]:
        """Find existing preference by domain and key."""
        for pref in self.preferences.values():
            if pref.domain == domain and pref.preference_key == preference_key:
                return pref
        return None
    
    def _update_preference(self, preference: UserPreference, feedback: UserFeedback, new_value: Any) -> None:
        """Update existing preference with new feedback."""
        preference.evidence_count += 1
        preference.last_updated = time.time()
        
        if feedback.feedback_type == FeedbackType.POSITIVE:
            preference.supporting_feedback.append(feedback.id)
            preference.confidence = min(preference.confidence + 0.1, 1.0)
        elif feedback.feedback_type == FeedbackType.NEGATIVE:
            preference.contradicting_feedback.append(feedback.id)
            preference.confidence = max(preference.confidence - 0.1, 0.0)
        else:
            # Update value if it's a direct preference statement
            if new_value != preference.preference_value:
                preference.preference_value = new_value
                preference.confidence = 0.5  # Reset confidence for new value
            else:
                preference.confidence = min(preference.confidence + 0.05, 1.0)
    
    def _serialize_preference(self, pref: UserPreference) -> Dict[str, Any]:
        """Serialize preference for storage."""
        return {
            "id": pref.id,
            "domain": pref.domain.value,
            "preference_key": pref.preference_key,
            "preference_value": pref.preference_value,
            "confidence": pref.confidence,
            "evidence_count": pref.evidence_count,
            "created_at": pref.created_at,
            "last_updated": pref.last_updated,
            "supporting_feedback": pref.supporting_feedback,
            "contradicting_feedback": pref.contradicting_feedback
        }
    
    def _deserialize_preference(self, data: Dict[str, Any]) -> UserPreference:
        """Deserialize preference from storage."""
        return UserPreference(
            id=data["id"],
            domain=LearningDomain(data["domain"]),
            preference_key=data["preference_key"],
            preference_value=data["preference_value"],
            confidence=data["confidence"],
            evidence_count=data["evidence_count"],
            created_at=data["created_at"],
            last_updated=data["last_updated"],
            supporting_feedback=data["supporting_feedback"],
            contradicting_feedback=data["contradicting_feedback"]
        )
    
    def _serialize_coding_pattern(self, pattern: CodingStylePattern) -> Dict[str, Any]:
        """Serialize coding pattern for storage."""
        return {
            "pattern_type": pattern.pattern_type,
            "pattern_value": pattern.pattern_value,
            "confidence": pattern.confidence,
            "evidence_count": pattern.evidence_count,
            "last_updated": pattern.last_updated,
            "examples": pattern.examples
        }
    
    def _deserialize_coding_pattern(self, data: Dict[str, Any]) -> CodingStylePattern:
        """Deserialize coding pattern from storage."""
        return CodingStylePattern(
            pattern_type=data["pattern_type"],
            pattern_value=data["pattern_value"],
            confidence=data["confidence"],
            evidence_count=data["evidence_count"],
            last_updated=data["last_updated"],
            examples=data["examples"]
        )


class FeedbackProcessor:
    """Processes user feedback for learning."""
    
    def __init__(self):
        self.feedback_history: List[UserFeedback] = []
        self.processing_rules: Dict[str, callable] = {
            "positive": self._process_positive_feedback,
            "negative": self._process_negative_feedback,
            "correction": self._process_correction_feedback,
            "preference": self._process_preference_feedback,
            "suggestion": self._process_suggestion_feedback
        }
        
        logger.info("Initialized FeedbackProcessor")
    
    def process_feedback(
        self,
        feedback_type: FeedbackType,
        content: str,
        context: Dict[str, Any] = None,
        user_input: str = "",
        agent_response: str = ""
    ) -> UserFeedback:
        """Process user feedback and extract learning insights."""
        
        feedback = UserFeedback(
            feedback_type=feedback_type,
            content=content,
            context=context or {},
            user_input=user_input,
            agent_response=agent_response
        )
        
        # Determine domain
        feedback.domain = self._classify_domain(feedback)
        
        # Process based on type
        processor = self.processing_rules.get(feedback_type.value)
        if processor:
            processor(feedback)
        
        # Calculate impact score
        feedback.impact_score = self._calculate_impact_score(feedback)
        
        # Mark as processed
        feedback.processed = True
        
        # Store in history
        self.feedback_history.append(feedback)
        
        logger.info(f"Processed {feedback_type.value} feedback with impact score {feedback.impact_score:.2f}")
        return feedback
    
    def _classify_domain(self, feedback: UserFeedback) -> LearningDomain:
        """Classify feedback into learning domain."""
        content_lower = feedback.content.lower()
        context = feedback.context
        
        # Check context for domain hints
        if context.get("code_related", False):
            return LearningDomain.CODING_STYLE
        
        # Analyze content for domain keywords
        domain_keywords = {
            LearningDomain.CODING_STYLE: ["code", "style", "format", "naming", "indent"],
            LearningDomain.ARCHITECTURE_PREFERENCE: ["architecture", "design", "pattern", "structure"],
            LearningDomain.TOOL_PREFERENCE: ["tool", "library", "framework", "package"],
            LearningDomain.COMMUNICATION_STYLE: ["explain", "verbose", "concise", "detail"],
            LearningDomain.WORKFLOW_PREFERENCE: ["workflow", "process", "step", "order"],
            LearningDomain.ERROR_HANDLING: ["error", "exception", "bug", "fix", "debug"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return domain
        
        return LearningDomain.CODING_STYLE  # Default
    
    def _process_positive_feedback(self, feedback: UserFeedback) -> None:
        """Process positive feedback."""
        # Positive feedback reinforces current behavior
        feedback.confidence = 0.8
        
        # Extract what was liked
        if "good" in feedback.content.lower():
            feedback.suggested_improvement = "Continue current approach"
        elif "helpful" in feedback.content.lower():
            feedback.suggested_improvement = "Maintain helpfulness level"
    
    def _process_negative_feedback(self, feedback: UserFeedback) -> None:
        """Process negative feedback."""
        # Negative feedback suggests changes needed
        feedback.confidence = 0.9  # High confidence that change is needed
        
        # Extract what needs improvement
        content_lower = feedback.content.lower()
        if "too verbose" in content_lower:
            feedback.suggested_improvement = "Be more concise"
        elif "too simple" in content_lower:
            feedback.suggested_improvement = "Provide more detail"
        elif "wrong" in content_lower:
            feedback.suggested_improvement = "Correct the approach"
    
    def _process_correction_feedback(self, feedback: UserFeedback) -> None:
        """Process correction feedback."""
        # Corrections are high-value learning opportunities
        feedback.confidence = 1.0
        feedback.suggested_improvement = feedback.content
    
    def _process_preference_feedback(self, feedback: UserFeedback) -> None:
        """Process preference feedback."""
        # Preferences help personalize behavior
        feedback.confidence = 0.7
        
        # Extract preference direction
        content_lower = feedback.content.lower()
        if "prefer" in content_lower:
            feedback.suggested_improvement = f"Adapt to preference: {feedback.content}"
    
    def _process_suggestion_feedback(self, feedback: UserFeedback) -> None:
        """Process suggestion feedback."""
        # Suggestions are improvement opportunities
        feedback.confidence = 0.6
        feedback.suggested_improvement = feedback.content
    
    def _calculate_impact_score(self, feedback: UserFeedback) -> float:
        """Calculate the potential impact of feedback on learning."""
        score = 0.0
        
        # Base score from feedback type
        type_scores = {
            FeedbackType.CORRECTION: 1.0,
            FeedbackType.NEGATIVE: 0.8,
            FeedbackType.PREFERENCE: 0.6,
            FeedbackType.POSITIVE: 0.4,
            FeedbackType.SUGGESTION: 0.5
        }
        
        score += type_scores.get(feedback.feedback_type, 0.3)
        
        # Boost for specific, actionable feedback
        if len(feedback.content.split()) > 5:  # Detailed feedback
            score += 0.2
        
        # Boost for feedback with context
        if feedback.context:
            score += 0.1
        
        # Boost for feedback that includes examples
        if "example" in feedback.content.lower() or "like this" in feedback.content.lower():
            score += 0.2
        
        return min(score, 1.0)
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of processed feedback."""
        if not self.feedback_history:
            return {"total": 0}
        
        # Count by type
        type_counts = {}
        for feedback in self.feedback_history:
            type_name = feedback.feedback_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Count by domain
        domain_counts = {}
        for feedback in self.feedback_history:
            domain_name = feedback.domain.value
            domain_counts[domain_name] = domain_counts.get(domain_name, 0) + 1
        
        # Calculate average impact
        avg_impact = sum(f.impact_score for f in self.feedback_history) / len(self.feedback_history)
        
        return {
            "total": len(self.feedback_history),
            "by_type": type_counts,
            "by_domain": domain_counts,
            "average_impact": avg_impact,
            "high_impact_count": sum(1 for f in self.feedback_history if f.impact_score > 0.7)
        }


class PersonalizedRecommendationEngine:
    """Generates personalized recommendations based on learned preferences."""
    
    def __init__(self, preference_modeler: UserPreferenceModeler):
        self.preference_modeler = preference_modeler
        self.recommendation_history: List[Recommendation] = []
        
        logger.info("Initialized PersonalizedRecommendationEngine")
    
    def generate_recommendations(
        self,
        context: Dict[str, Any],
        domain: Optional[LearningDomain] = None,
        limit: int = 5
    ) -> List[Recommendation]:
        """Generate personalized recommendations based on context."""
        
        recommendations = []
        
        # Get relevant preferences
        if domain:
            preferences = self.preference_modeler.get_preferences_by_domain(domain)
        else:
            # Get preferences from all domains
            preferences = {}
            for d in LearningDomain:
                preferences.update(self.preference_modeler.get_preferences_by_domain(d))
        
        # Generate recommendations based on preferences
        for pref_key, pref_data in preferences.items():
            if pref_data["confidence"] > 0.5:  # Only confident preferences
                rec = self._create_recommendation_from_preference(
                    pref_key, pref_data, context
                )
                if rec:
                    recommendations.append(rec)
        
        # Generate coding style recommendations
        coding_style = self.preference_modeler.get_coding_style_preferences()
        for style_key, style_data in coding_style.items():
            if style_data["confidence"] > 0.5:
                rec = self._create_coding_style_recommendation(
                    style_key, style_data, context
                )
                if rec:
                    recommendations.append(rec)
        
        # Sort by confidence and limit
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        recommendations = recommendations[:limit]
        
        # Store in history
        self.recommendation_history.extend(recommendations)
        
        return recommendations
    
    def _create_recommendation_from_preference(
        self,
        pref_key: str,
        pref_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Recommendation]:
        """Create recommendation from user preference."""
        
        pref_value = pref_data["value"]
        confidence = pref_data["confidence"]
        
        # Generate recommendation based on preference key
        if pref_key == "verbosity_level":
            if pref_value == "verbose":
                return Recommendation(
                    recommendation_type="communication",
                    content="Provide detailed explanations and step-by-step guidance",
                    reasoning=f"User prefers verbose communication (confidence: {confidence:.2f})",
                    confidence=confidence,
                    context=context
                )
            elif pref_value == "concise":
                return Recommendation(
                    recommendation_type="communication",
                    content="Keep responses concise and to the point",
                    reasoning=f"User prefers concise communication (confidence: {confidence:.2f})",
                    confidence=confidence,
                    context=context
                )
        
        elif pref_key == "explanation_preference":
            if pref_value == "preferred":
                return Recommendation(
                    recommendation_type="explanation",
                    content="Include explanations for code and decisions",
                    reasoning=f"User appreciates explanations (confidence: {confidence:.2f})",
                    confidence=confidence,
                    context=context
                )
        
        elif pref_key == "testing_preference":
            if pref_value == "preferred":
                return Recommendation(
                    recommendation_type="testing",
                    content="Include test cases and testing suggestions",
                    reasoning=f"User values testing (confidence: {confidence:.2f})",
                    confidence=confidence,
                    context=context
                )
        
        return None
    
    def _create_coding_style_recommendation(
        self,
        style_key: str,
        style_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Recommendation]:
        """Create recommendation from coding style preference."""
        
        style_value = style_data["value"]
        confidence = style_data["confidence"]
        
        if style_key == "function_naming":
            return Recommendation(
                recommendation_type="coding_style",
                content=f"Use {style_value} for function names",
                reasoning=f"User consistently uses {style_value} naming (confidence: {confidence:.2f})",
                confidence=confidence,
                context=context
            )
        
        elif style_key == "indentation":
            return Recommendation(
                recommendation_type="coding_style",
                content=f"Use {style_value} for indentation",
                reasoning=f"User prefers {style_value} indentation (confidence: {confidence:.2f})",
                confidence=confidence,
                context=context
            )
        
        elif style_key == "import_style":
            return Recommendation(
                recommendation_type="coding_style",
                content=f"Use {style_value} for imports",
                reasoning=f"User typically uses {style_value} (confidence: {confidence:.2f})",
                confidence=confidence,
                context=context
            )
        
        return None
    
    def track_recommendation_effectiveness(
        self,
        recommendation_id: str,
        user_response: str,
        effectiveness_score: float
    ) -> None:
        """Track how effective a recommendation was."""
        
        for rec in self.recommendation_history:
            if rec.id == recommendation_id:
                rec.user_response = user_response
                rec.effectiveness_score = effectiveness_score
                break
    
    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get statistics about recommendation effectiveness."""
        
        if not self.recommendation_history:
            return {"total": 0}
        
        # Count by type
        type_counts = {}
        for rec in self.recommendation_history:
            rec_type = rec.recommendation_type
            type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
        
        # Calculate effectiveness
        effective_recs = [r for r in self.recommendation_history if r.effectiveness_score is not None]
        avg_effectiveness = 0.0
        if effective_recs:
            avg_effectiveness = sum(r.effectiveness_score for r in effective_recs) / len(effective_recs)
        
        return {
            "total": len(self.recommendation_history),
            "by_type": type_counts,
            "evaluated": len(effective_recs),
            "average_effectiveness": avg_effectiveness,
            "highly_effective": sum(1 for r in effective_recs if r.effectiveness_score > 0.7)
        }


class LearningEngine:
    """Main learning engine that coordinates all learning components."""
    
    def __init__(self, storage_path: Path):
        self.preference_modeler = UserPreferenceModeler(storage_path / "preferences")
        self.feedback_processor = FeedbackProcessor()
        self.recommendation_engine = PersonalizedRecommendationEngine(self.preference_modeler)
        
        logger.info("Initialized LearningEngine")
    
    def learn_from_interaction(
        self,
        user_input: str,
        agent_response: str,
        feedback: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        context: Dict[str, Any] = None
    ) -> None:
        """Learn from a user interaction."""
        
        # Learn from code if present
        if context and context.get("code"):
            language = context.get("language", "python")
            self.preference_modeler.learn_from_code(context["code"], language)
        
        # Process feedback if provided
        if feedback and feedback_type:
            processed_feedback = self.feedback_processor.process_feedback(
                feedback_type=feedback_type,
                content=feedback,
                context=context,
                user_input=user_input,
                agent_response=agent_response
            )
            
            # Learn preferences from feedback
            self.preference_modeler.learn_from_feedback(processed_feedback)
    
    def get_personalized_recommendations(
        self,
        context: Dict[str, Any],
        domain: Optional[LearningDomain] = None
    ) -> List[Recommendation]:
        """Get personalized recommendations for the current context."""
        return self.recommendation_engine.generate_recommendations(context, domain)
    
    def adapt_agent_behavior(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get behavior adaptations based on learned preferences."""
        
        adaptations = {}
        
        # Get communication preferences
        comm_prefs = self.preference_modeler.get_preferences_by_domain(LearningDomain.COMMUNICATION_STYLE)
        for pref_key, pref_data in comm_prefs.items():
            if pref_data["confidence"] > 0.5:
                adaptations[pref_key] = pref_data["value"]
        
        # Get coding style preferences
        coding_style = self.preference_modeler.get_coding_style_preferences()
        adaptations["coding_style"] = coding_style
        
        # Get workflow preferences
        workflow_prefs = self.preference_modeler.get_preferences_by_domain(LearningDomain.WORKFLOW_PREFERENCE)
        adaptations["workflow"] = workflow_prefs
        
        return adaptations
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        
        feedback_stats = self.feedback_processor.get_feedback_summary()
        recommendation_stats = self.recommendation_engine.get_recommendation_stats()
        
        # Get preference counts
        total_preferences = len(self.preference_modeler.preferences)
        confident_preferences = sum(
            1 for pref in self.preference_modeler.preferences.values()
            if pref.confidence > 0.5
        )
        
        coding_patterns = len(self.preference_modeler.coding_patterns)
        confident_patterns = sum(
            1 for pattern in self.preference_modeler.coding_patterns.values()
            if pattern.confidence > 0.5
        )
        
        return {
            "preferences": {
                "total": total_preferences,
                "confident": confident_preferences,
                "confidence_rate": confident_preferences / max(total_preferences, 1)
            },
            "coding_patterns": {
                "total": coding_patterns,
                "confident": confident_patterns,
                "confidence_rate": confident_patterns / max(coding_patterns, 1)
            },
            "feedback": feedback_stats,
            "recommendations": recommendation_stats
        }