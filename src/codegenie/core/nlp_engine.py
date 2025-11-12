"""
Natural Language Processing Engine for CodeGenie

This module provides natural language understanding capabilities for converting
user requirements into technical specifications and code implementations.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path

from ..models.model_manager import ModelManager


class IntentType(Enum):
    """Types of development intents that can be extracted from natural language."""
    CREATE_FUNCTION = "create_function"
    CREATE_CLASS = "create_class"
    CREATE_MODULE = "create_module"
    IMPLEMENT_FEATURE = "implement_feature"
    FIX_BUG = "fix_bug"
    REFACTOR_CODE = "refactor_code"
    ADD_TESTS = "add_tests"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    ADD_DOCUMENTATION = "add_documentation"
    SETUP_PROJECT = "setup_project"


class EntityType(Enum):
    """Types of entities that can be extracted from requirements."""
    FUNCTION_NAME = "function_name"
    CLASS_NAME = "class_name"
    MODULE_NAME = "module_name"
    PARAMETER = "parameter"
    RETURN_TYPE = "return_type"
    TECHNOLOGY = "technology"
    FRAMEWORK = "framework"
    DATABASE = "database"
    API_ENDPOINT = "api_endpoint"
    FILE_PATH = "file_path"


@dataclass
class Entity:
    """Represents an extracted entity from natural language."""
    type: EntityType
    value: str
    confidence: float
    context: str = ""


@dataclass
class Intent:
    """Represents an extracted intent from natural language."""
    type: IntentType
    confidence: float
    description: str
    entities: List[Entity] = field(default_factory=list)


@dataclass
class Ambiguity:
    """Represents an ambiguous part of the requirement that needs clarification."""
    text: str
    possible_interpretations: List[str]
    clarification_question: str
    context: str = ""


@dataclass
class RequirementAnalysis:
    """Result of analyzing a natural language requirement."""
    original_text: str
    intents: List[Intent]
    entities: List[Entity]
    ambiguities: List[Ambiguity]
    confidence_score: float
    technical_specification: Optional[str] = None
    clarification_needed: bool = False


class NLPEngine:
    """
    Natural Language Processing Engine for requirement analysis and code generation.
    
    This engine processes natural language descriptions and converts them into
    structured technical specifications that can be used for code generation.
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager
        self._intent_patterns = self._load_intent_patterns()
        self._entity_patterns = self._load_entity_patterns()
        self._ambiguity_patterns = self._load_ambiguity_patterns()
    
    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Load regex patterns for intent recognition."""
        return {
            IntentType.CREATE_FUNCTION: [
                r"create\s+(?:a\s+)?function",
                r"write\s+(?:a\s+)?function",
                r"implement\s+(?:a\s+)?function",
                r"build\s+(?:a\s+)?function",
                r"make\s+(?:a\s+)?function"
            ],
            IntentType.CREATE_CLASS: [
                r"create\s+(?:a\s+)?class",
                r"write\s+(?:a\s+)?class",
                r"implement\s+(?:a\s+)?class",
                r"build\s+(?:a\s+)?class",
                r"make\s+(?:a\s+)?class"
            ],
            IntentType.CREATE_MODULE: [
                r"create\s+(?:a\s+)?module",
                r"write\s+(?:a\s+)?module",
                r"implement\s+(?:a\s+)?module",
                r"build\s+(?:a\s+)?module",
                r"make\s+(?:a\s+)?module"
            ],
            IntentType.IMPLEMENT_FEATURE: [
                r"implement\s+(?:a\s+)?feature",
                r"add\s+(?:a\s+)?feature",
                r"build\s+(?:a\s+)?feature",
                r"create\s+(?:a\s+)?feature"
            ],
            IntentType.FIX_BUG: [
                r"fix\s+(?:the\s+)?bug",
                r"resolve\s+(?:the\s+)?issue",
                r"debug",
                r"troubleshoot"
            ],
            IntentType.REFACTOR_CODE: [
                r"refactor",
                r"improve\s+(?:the\s+)?code",
                r"optimize\s+(?:the\s+)?structure",
                r"clean\s+up"
            ],
            IntentType.ADD_TESTS: [
                r"add\s+tests",
                r"write\s+tests",
                r"create\s+tests",
                r"test\s+(?:the\s+)?code"
            ],
            IntentType.OPTIMIZE_PERFORMANCE: [
                r"optimize\s+performance",
                r"improve\s+speed",
                r"make\s+faster",
                r"reduce\s+latency"
            ],
            IntentType.ADD_DOCUMENTATION: [
                r"add\s+documentation",
                r"write\s+docs",
                r"document\s+(?:the\s+)?code",
                r"create\s+documentation"
            ],
            IntentType.SETUP_PROJECT: [
                r"setup\s+project",
                r"initialize\s+project",
                r"create\s+project\s+structure",
                r"scaffold\s+project"
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[EntityType, List[str]]:
        """Load regex patterns for entity extraction."""
        return {
            EntityType.FUNCTION_NAME: [
                r"function\s+(?:called\s+|named\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
                r"([a-zA-Z_][a-zA-Z0-9_]*)\s+function",
                r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)"
            ],
            EntityType.CLASS_NAME: [
                r"class\s+(?:called\s+|named\s+)?([A-Z][a-zA-Z0-9_]*)",
                r"([A-Z][a-zA-Z0-9_]*)\s+class",
                r"class\s+([A-Z][a-zA-Z0-9_]*)"
            ],
            EntityType.MODULE_NAME: [
                r"module\s+(?:called\s+|named\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
                r"([a-zA-Z_][a-zA-Z0-9_]*)\s+module"
            ],
            EntityType.PARAMETER: [
                r"parameter\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                r"argument\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                r"takes?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as"
            ],
            EntityType.RETURN_TYPE: [
                r"returns?\s+(?:a\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
                r"return\s+type\s+([a-zA-Z_][a-zA-Z0-9_]*)"
            ],
            EntityType.TECHNOLOGY: [
                r"using\s+([A-Z][a-zA-Z0-9]*)",
                r"with\s+([A-Z][a-zA-Z0-9]*)",
                r"in\s+(Python|JavaScript|TypeScript|Java|C\+\+|C#|Go|Rust)"
            ],
            EntityType.FRAMEWORK: [
                r"(Flask|Django|FastAPI|Express|React|Vue|Angular|Spring)",
                r"framework\s+([A-Z][a-zA-Z0-9]*)"
            ],
            EntityType.DATABASE: [
                r"(PostgreSQL|MySQL|MongoDB|SQLite|Redis|Elasticsearch)",
                r"database\s+([A-Z][a-zA-Z0-9]*)"
            ],
            EntityType.API_ENDPOINT: [
                r"endpoint\s+([/a-zA-Z0-9_-]+)",
                r"API\s+([/a-zA-Z0-9_-]+)",
                r"route\s+([/a-zA-Z0-9_-]+)"
            ],
            EntityType.FILE_PATH: [
                r"file\s+([a-zA-Z0-9_/.-]+)",
                r"path\s+([a-zA-Z0-9_/.-]+)"
            ]
        }
    
    def _load_ambiguity_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns that indicate potential ambiguity."""
        return [
            {
                "pattern": r"(?:some|any|several|multiple|various)",
                "question": "Can you be more specific about the quantity or type?",
                "context": "vague_quantity"
            },
            {
                "pattern": r"(?:good|bad|better|best|optimal|efficient)",
                "question": "What specific criteria define 'good' or 'optimal' in this context?",
                "context": "subjective_quality"
            },
            {
                "pattern": r"(?:handle|process|manage|deal with)",
                "question": "What specific actions should be taken when handling this?",
                "context": "vague_action"
            },
            {
                "pattern": r"(?:user|client|customer|person)",
                "question": "What type of user are you referring to? (admin, end-user, developer, etc.)",
                "context": "user_type"
            },
            {
                "pattern": r"(?:data|information|content)",
                "question": "What specific type and format of data are you working with?",
                "context": "data_type"
            }
        ]
    
    async def analyze_requirement(self, text: str) -> RequirementAnalysis:
        """
        Analyze a natural language requirement and extract structured information.
        
        Args:
            text: The natural language requirement text
            
        Returns:
            RequirementAnalysis containing intents, entities, and ambiguities
        """
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Extract intents
        intents = await self._extract_intents(normalized_text)
        
        # Extract entities
        entities = await self._extract_entities(text)
        
        # Detect ambiguities
        ambiguities = await self._detect_ambiguities(text)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(intents, entities, ambiguities)
        
        # Generate technical specification if confidence is high enough
        technical_spec = None
        if confidence_score > 0.7 and not ambiguities:
            technical_spec = await self._generate_technical_specification(
                text, intents, entities
            )
        
        return RequirementAnalysis(
            original_text=text,
            intents=intents,
            entities=entities,
            ambiguities=ambiguities,
            confidence_score=confidence_score,
            technical_specification=technical_spec,
            clarification_needed=len(ambiguities) > 0 or confidence_score < 0.6
        )
    
    async def _extract_intents(self, text: str) -> List[Intent]:
        """Extract development intents from text."""
        intents = []
        
        for intent_type, patterns in self._intent_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    confidence = self._calculate_pattern_confidence(match, text)
                    intents.append(Intent(
                        type=intent_type,
                        confidence=confidence,
                        description=match.group(0),
                        entities=[]
                    ))
        
        # Remove duplicates and sort by confidence
        unique_intents = {}
        for intent in intents:
            if intent.type not in unique_intents or intent.confidence > unique_intents[intent.type].confidence:
                unique_intents[intent.type] = intent
        
        return sorted(unique_intents.values(), key=lambda x: x.confidence, reverse=True)
    
    async def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text."""
        entities = []
        
        for entity_type, patterns in self._entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) > 0:
                        value = match.group(1)
                        confidence = self._calculate_pattern_confidence(match, text)
                        entities.append(Entity(
                            type=entity_type,
                            value=value,
                            confidence=confidence,
                            context=match.group(0)
                        ))
        
        # Remove duplicates
        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity.type, entity.value.lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return sorted(unique_entities, key=lambda x: x.confidence, reverse=True)
    
    async def _detect_ambiguities(self, text: str) -> List[Ambiguity]:
        """Detect ambiguous parts of the requirement."""
        ambiguities = []
        
        for pattern_info in self._ambiguity_patterns:
            pattern = pattern_info["pattern"]
            question = pattern_info["question"]
            context = pattern_info["context"]
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Create possible interpretations based on context
                interpretations = self._generate_interpretations(match.group(0), context)
                
                ambiguities.append(Ambiguity(
                    text=match.group(0),
                    possible_interpretations=interpretations,
                    clarification_question=question,
                    context=context
                ))
        
        return ambiguities
    
    def _generate_interpretations(self, ambiguous_text: str, context: str) -> List[str]:
        """Generate possible interpretations for ambiguous text."""
        interpretations = {
            "vague_quantity": [
                "Exactly one item",
                "A small number (2-5 items)",
                "A moderate number (5-20 items)",
                "A large number (20+ items)"
            ],
            "subjective_quality": [
                "High performance (speed/efficiency)",
                "Good maintainability (readable/modular)",
                "Robust error handling",
                "User-friendly interface"
            ],
            "vague_action": [
                "Validate and process",
                "Transform and store",
                "Filter and forward",
                "Log and respond"
            ],
            "user_type": [
                "End user (application user)",
                "Administrator (system admin)",
                "Developer (API consumer)",
                "Anonymous user (public access)"
            ],
            "data_type": [
                "Structured data (JSON/XML)",
                "Text data (strings/documents)",
                "Binary data (files/images)",
                "Numeric data (integers/floats)"
            ]
        }
        
        return interpretations.get(context, ["Please specify more details"])
    
    def _calculate_pattern_confidence(self, match, text: str) -> float:
        """Calculate confidence score for a pattern match."""
        # Base confidence
        confidence = 0.7
        
        # Adjust based on match position (beginning of sentence gets higher score)
        if match.start() < len(text) * 0.2:
            confidence += 0.1
        
        # Adjust based on surrounding context
        context_window = 20
        start = max(0, match.start() - context_window)
        end = min(len(text), match.end() + context_window)
        context = text[start:end].lower()
        
        # Boost confidence for technical keywords
        technical_keywords = ["function", "class", "module", "api", "database", "framework"]
        for keyword in technical_keywords:
            if keyword in context:
                confidence += 0.05
        
        return min(1.0, confidence)
    
    def _calculate_confidence(self, intents: List[Intent], entities: List[Entity], 
                           ambiguities: List[Ambiguity]) -> float:
        """Calculate overall confidence score for the analysis."""
        if not intents:
            return 0.0
        
        # Base confidence from intents
        intent_confidence = sum(intent.confidence for intent in intents) / len(intents)
        
        # Boost for entities
        entity_boost = min(0.2, len(entities) * 0.05)
        
        # Penalty for ambiguities
        ambiguity_penalty = len(ambiguities) * 0.1
        
        confidence = intent_confidence + entity_boost - ambiguity_penalty
        return max(0.0, min(1.0, confidence))
    
    async def _generate_technical_specification(self, text: str, intents: List[Intent], 
                                              entities: List[Entity]) -> str:
        """Generate a technical specification from the analyzed requirement."""
        if not self.model_manager:
            return self._generate_basic_specification(intents, entities)
        
        # Use AI model to generate detailed specification
        prompt = self._create_specification_prompt(text, intents, entities)
        
        try:
            response = await self.model_manager.generate_response(
                prompt=prompt,
                model_type="code_generation",
                max_tokens=1000
            )
            return response.strip()
        except Exception:
            # Fallback to basic specification
            return self._generate_basic_specification(intents, entities)
    
    def _generate_basic_specification(self, intents: List[Intent], 
                                    entities: List[Entity]) -> str:
        """Generate a basic technical specification without AI model."""
        spec_parts = []
        
        if intents:
            primary_intent = intents[0]
            spec_parts.append(f"Primary Task: {primary_intent.type.value}")
        
        # Group entities by type
        entity_groups = {}
        for entity in entities:
            if entity.type not in entity_groups:
                entity_groups[entity.type] = []
            entity_groups[entity.type].append(entity.value)
        
        for entity_type, values in entity_groups.items():
            spec_parts.append(f"{entity_type.value}: {', '.join(values)}")
        
        return "\n".join(spec_parts)
    
    def _create_specification_prompt(self, text: str, intents: List[Intent], 
                                   entities: List[Entity]) -> str:
        """Create a prompt for AI-generated technical specification."""
        intent_list = [f"- {intent.type.value} (confidence: {intent.confidence:.2f})" 
                      for intent in intents]
        entity_list = [f"- {entity.type.value}: {entity.value}" for entity in entities]
        
        return f"""
Convert this natural language requirement into a detailed technical specification:

Original Requirement: "{text}"

Detected Intents:
{chr(10).join(intent_list)}

Extracted Entities:
{chr(10).join(entity_list)}

Please provide a clear, technical specification that includes:
1. Functional requirements
2. Input/output specifications
3. Technical constraints
4. Implementation approach

Technical Specification:
"""

    async def generate_clarification_questions(self, analysis: RequirementAnalysis) -> List[str]:
        """Generate clarification questions for ambiguous requirements."""
        questions = []
        
        # Questions from detected ambiguities
        for ambiguity in analysis.ambiguities:
            questions.append(ambiguity.clarification_question)
        
        # Additional questions based on missing information
        if not analysis.entities:
            questions.append("What specific components or names should be used?")
        
        if analysis.confidence_score < 0.5:
            questions.append("Could you provide more specific details about what you want to implement?")
        
        # Intent-specific questions
        if analysis.intents:
            primary_intent = analysis.intents[0]
            intent_questions = self._get_intent_specific_questions(primary_intent, analysis.entities)
            questions.extend(intent_questions)
        
        return questions[:5]  # Limit to 5 questions to avoid overwhelming user
    
    def _get_intent_specific_questions(self, intent: Intent, entities: List[Entity]) -> List[str]:
        """Get questions specific to the detected intent."""
        questions = []
        entity_types = {entity.type for entity in entities}
        
        if intent.type == IntentType.CREATE_FUNCTION:
            if EntityType.FUNCTION_NAME not in entity_types:
                questions.append("What should the function be named?")
            if EntityType.PARAMETER not in entity_types:
                questions.append("What parameters should the function accept?")
            if EntityType.RETURN_TYPE not in entity_types:
                questions.append("What should the function return?")
        
        elif intent.type == IntentType.CREATE_CLASS:
            if EntityType.CLASS_NAME not in entity_types:
                questions.append("What should the class be named?")
            questions.append("What methods should the class have?")
            questions.append("What attributes should the class have?")
        
        elif intent.type == IntentType.IMPLEMENT_FEATURE:
            questions.append("What specific functionality should this feature provide?")
            questions.append("How should users interact with this feature?")
        
        elif intent.type == IntentType.SETUP_PROJECT:
            if EntityType.TECHNOLOGY not in entity_types:
                questions.append("What programming language or technology stack should be used?")
            questions.append("What type of project is this? (web app, CLI tool, library, etc.)")
        
        return questions

    async def validate_requirement(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validate if a requirement is clear and implementable.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check minimum length
        if len(text.strip()) < 10:
            issues.append("Requirement is too short. Please provide more details.")
        
        # Check for vague language
        vague_words = ["something", "somehow", "maybe", "probably", "might", "could"]
        for word in vague_words:
            if word in text.lower():
                issues.append(f"Avoid vague language like '{word}'. Be more specific.")
        
        # Analyze the requirement
        analysis = await self.analyze_requirement(text)
        
        # Check for intents
        if not analysis.intents:
            issues.append("No clear development intent detected. Please specify what you want to create or implement.")
        
        # Check confidence
        if analysis.confidence_score < 0.3:
            issues.append("Requirement is unclear. Please provide more specific details.")
        
        # Check for ambiguities
        if len(analysis.ambiguities) > 3:
            issues.append("Too many ambiguous terms. Please be more specific.")
        
        return len(issues) == 0, issues