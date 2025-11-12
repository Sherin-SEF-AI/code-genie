"""
Core components of CodeGenie.
"""

from .agent import CodeGenieAgent
from .config import Config
from .session import Session
from .memory import Memory
from .reasoning import ReasoningEngine
from .workflow_engine import WorkflowEngine, TaskPlanner, ExecutionEngine, RiskAssessor
from .context_engine import ContextEngine, PersistentMemoryManager, SemanticIndexer, ProjectEvolutionTracker
from .learning_engine import LearningEngine, UserPreferenceModeler, FeedbackProcessor, PersonalizedRecommendationEngine
from .code_intelligence import (
    SemanticAnalyzer, ASTAnalyzer, PatternRecognizer, ComplexityAnalyzer,
    CodeEntity, DesignPattern, CodeSmell, SemanticAnalysis,
    EntityType, ComplexityMetrics, CodeLocation, PatternMatch, CodeSmellDetection
)
from .knowledge_graph import (
    CodeKnowledgeGraph, GraphNode, CodeRelationship, RelationshipType,
    GraphQueryResult, DependencyChain
)
from .impact_analysis import (
    ChangeImpactAnalyzer, CodeChange, ImpactedEntity,
    ImpactAnalysis, ChangeType, RiskLevel, ImpactScope, MultiFileChange, ChangeValidation
)
from .nlp_engine import (
    NLPEngine, RequirementAnalysis, Intent, Entity, Ambiguity,
    IntentType, EntityType
)
from .requirement_processor import (
    RequirementProcessor, ClarificationSession, ClarificationQuestion,
    RequirementValidation, ClarificationStatus, ValidationResult
)
from .code_generator import (
    CodeGenerator, GeneratedCode, CodeGenerationRequest, CodeGenerationResult,
    CodeTemplate, CodeLanguage, GenerationStrategy, ValidationLevel
)
from .code_validator import (
    CodeValidator, ValidationResult as CodeValidationResult, TestResult,
    QualityScore, ValidationIssue, TestFramework, QualityMetric
)
from .explanation_engine import (
    ExplanationEngine, CodeExplanation, TradeOffAnalysis, Documentation,
    ExplanationRequest, DocumentationRequest, ExplanationType, DocumentationType, TradeOffCategory
)
from .interactive_refinement import (
    InteractiveRefinementEngine, InteractiveSession, InteractionResponse,
    UserFeedback, RefinementRequest, InteractionType, RefinementType
)
from .predictive_engine import (
    DevelopmentPatternAnalyzer, ProactiveSuggestionEngine, PredictiveDevelopmentAssistant,
    DevelopmentPattern, VelocityMetrics, CollaborationPattern, ProjectTrend,
    PredictiveSuggestion, PatternType, PredictionType, ConfidenceLevel
)
from .proactive_assistant import (
    ContextAwareSuggestionEngine, PreventiveIssueDetector,
    ContextualSuggestion, PreventiveAlert, OptimizationOpportunity,
    SuggestionCategory, IssueType, CodeContextAnalyzer, ProjectContextAnalyzer,
    TeamContextAnalyzer, WorkflowContextAnalyzer
)
from .proactive_monitoring import (
    ProactiveAssistant, CodebaseMonitor, IssueDetector, SuggestionEngine,
    WorkflowPredictor, ProactiveSuggestion, DetectedIssue, WorkflowPrediction,
    MonitoringResult, ChangeEvent, SuggestionType, Severity
)
from .related_code_finder import (
    RelatedCodeFinder, DependencyAnalyzer, TestSuggestionEngine,
    DocumentationDetector, RelatedCode, DependencyInfo, TestSuggestion,
    DocumentationUpdate
)
from .convention_enforcer import (
    ConventionEnforcer, PatternAnalyzer, ViolationDetector, AutoFixer,
    Convention, Violation, TeamStandard, ConventionType, ViolationSeverity
)
from .security_performance_scanner import (
    SecurityPerformanceScanner, SecurityScanner, PerformanceScanner,
    ProactiveAlertSystem, AutoFixGenerator, SecurityIssue, PerformanceIssue,
    ProactiveAlert as SecurityPerformanceAlert, SecurityIssueType,
    PerformanceIssueType, IssueSeverity
)
from .tool_executor import (
    ToolExecutor, TerminalExecutor, ResultAnalyzer, REPLManager, FileEditor, GitIntegration,
    CommandResult, OutputAnalysis, FileEdit, REPLResult, GitOperation,
    CommandStatus, EditType
)
from .agentic_search import (
    AgenticSearchEngine, CodebaseScanner, RelevanceScorer, SearchStrategySelector,
    Symbol, FileIndex, SearchResult, SearchIntent
)
from .parallel_executor import (
    ParallelExecutor, ParallelTask, ExecutionBatch, ParallelExecutionResult,
    ResourceManager, DependencyResolver, ProgressTracker, TaskState
)
from .result_verifier import (
    ResultVerifier, VerificationResult, VerificationCriteria, IterationPlan,
    OutputVerifier, StateValidator, TestExecutor,
    VerificationStatus, VerificationMethod
)
from .agent_communication import (
    AgentCommunicationBus, AgentCoordinatorEnhanced, Message, AgentRegistration,
    MessageType, MessagePriority
)

__all__ = [
    "CodeGenieAgent",
    "Config",
    "Session",
    "Memory",
    "ReasoningEngine",
    "WorkflowEngine",
    "TaskPlanner",
    "ExecutionEngine",
    "RiskAssessor",
    "ContextEngine",
    "PersistentMemoryManager",
    "SemanticIndexer",
    "ProjectEvolutionTracker",
    "LearningEngine",
    "UserPreferenceModeler",
    "FeedbackProcessor",
    "PersonalizedRecommendationEngine",
    "SemanticAnalyzer",
    "ASTAnalyzer", 
    "PatternRecognizer",
    "ComplexityAnalyzer",
    "CodeEntity",
    "DesignPattern",
    "CodeSmell",
    "SemanticAnalysis",
    "EntityType",
    "ComplexityMetrics",
    "CodeLocation",
    "PatternMatch",
    "CodeSmellDetection",
    "CodeKnowledgeGraph",
    "GraphNode",
    "CodeRelationship",
    "RelationshipType",
    "GraphQueryResult",
    "DependencyChain",
    "ChangeImpactAnalyzer",
    "CodeChange",
    "ImpactedEntity",
    "ImpactAnalysis",
    "ChangeType",
    "RiskLevel",
    "ImpactScope",
    "MultiFileChange",
    "ChangeValidation",
    "NLPEngine",
    "RequirementAnalysis",
    "Intent",
    "Entity",
    "Ambiguity",
    "IntentType",
    "EntityType",
    "RequirementProcessor",
    "ClarificationSession",
    "ClarificationQuestion",
    "RequirementValidation",
    "ClarificationStatus",
    "ValidationResult",
    "CodeGenerator",
    "GeneratedCode",
    "CodeGenerationRequest",
    "CodeGenerationResult",
    "CodeTemplate",
    "CodeLanguage",
    "GenerationStrategy",
    "ValidationLevel",
    "CodeValidator",
    "CodeValidationResult",
    "TestResult",
    "QualityScore",
    "ValidationIssue",
    "TestFramework",
    "QualityMetric",
    "ExplanationEngine",
    "CodeExplanation",
    "TradeOffAnalysis",
    "Documentation",
    "ExplanationRequest",
    "DocumentationRequest",
    "ExplanationType",
    "DocumentationType",
    "TradeOffCategory",
    "InteractiveRefinementEngine",
    "InteractiveSession",
    "InteractionResponse",
    "UserFeedback",
    "RefinementRequest",
    "InteractionType",
    "RefinementType",
    "DevelopmentPatternAnalyzer",
    "ProactiveSuggestionEngine",
    "PredictiveDevelopmentAssistant",
    "DevelopmentPattern",
    "VelocityMetrics",
    "CollaborationPattern",
    "ProjectTrend",
    "PredictiveSuggestion",
    "PatternType",
    "PredictionType",
    "ConfidenceLevel",
    "ContextAwareSuggestionEngine",
    "PreventiveIssueDetector",
    "ContextualSuggestion",
    "PreventiveAlert",
    "OptimizationOpportunity",
    "SuggestionCategory",
    "IssueType",
    "CodeContextAnalyzer",
    "ProjectContextAnalyzer",
    "TeamContextAnalyzer",
    "WorkflowContextAnalyzer",
    "ProactiveAssistant",
    "CodebaseMonitor",
    "IssueDetector",
    "SuggestionEngine",
    "WorkflowPredictor",
    "ProactiveSuggestion",
    "DetectedIssue",
    "WorkflowPrediction",
    "MonitoringResult",
    "ChangeEvent",
    "SuggestionType",
    "Severity",
    "RelatedCodeFinder",
    "DependencyAnalyzer",
    "TestSuggestionEngine",
    "DocumentationDetector",
    "RelatedCode",
    "DependencyInfo",
    "TestSuggestion",
    "DocumentationUpdate",
    "ConventionEnforcer",
    "PatternAnalyzer",
    "ViolationDetector",
    "AutoFixer",
    "Convention",
    "Violation",
    "TeamStandard",
    "ConventionType",
    "ViolationSeverity",
    "SecurityPerformanceScanner",
    "SecurityScanner",
    "PerformanceScanner",
    "ProactiveAlertSystem",
    "AutoFixGenerator",
    "SecurityIssue",
    "PerformanceIssue",
    "SecurityPerformanceAlert",
    "SecurityIssueType",
    "PerformanceIssueType",
    "IssueSeverity",
    "ToolExecutor",
    "TerminalExecutor",
    "ResultAnalyzer",
    "REPLManager",
    "FileEditor",
    "GitIntegration",
    "CommandResult",
    "OutputAnalysis",
    "FileEdit",
    "REPLResult",
    "GitOperation",
    "CommandStatus",
    "EditType",
    "AgenticSearchEngine",
    "CodebaseScanner",
    "RelevanceScorer",
    "SearchStrategySelector",
    "Symbol",
    "FileIndex",
    "SearchResult",
    "SearchIntent",
    "ParallelExecutor",
    "ParallelTask",
    "ExecutionBatch",
    "ParallelExecutionResult",
    "ResourceManager",
    "DependencyResolver",
    "ProgressTracker",
    "TaskState",
    "ResultVerifier",
    "VerificationResult",
    "VerificationCriteria",
    "IterationPlan",
    "OutputVerifier",
    "StateValidator",
    "TestExecutor",
    "VerificationStatus",
    "VerificationMethod",
    "AgentCommunicationBus",
    "AgentCoordinatorEnhanced",
    "Message",
    "AgentRegistration",
    "MessageType",
    "MessagePriority",
]
