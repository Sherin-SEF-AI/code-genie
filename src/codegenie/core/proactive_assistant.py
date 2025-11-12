"""
Proactive Development Assistant

This module provides context-aware suggestions, preventive issue detection,
and optimization opportunity identification for enhanced development workflows.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from pathlib import Path
import re

from .predictive_engine import (
    PredictiveSuggestion, PredictionType, ConfidenceLevel,
    DevelopmentPattern, PatternType
)
from .code_intelligence import SemanticAnalysis, CodeEntity, ComplexityMetrics
from .context_engine import ContextEngine


class SuggestionCategory(Enum):
    """Categories of proactive suggestions."""
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    WORKFLOW = "workflow"
    MAINTENANCE = "maintenance"


class IssueType(Enum):
    """Types of potential issues that can be detected."""
    TECHNICAL_DEBT = "technical_debt"
    PERFORMANCE_BOTTLENECK = "performance_bottleneck"
    SECURITY_VULNERABILITY = "security_vulnerability"
    MAINTAINABILITY_RISK = "maintainability_risk"
    SCALABILITY_CONCERN = "scalability_concern"
    DEPENDENCY_RISK = "dependency_risk"
    QUALITY_DEGRADATION = "quality_degradation"


@dataclass
class ContextualSuggestion:
    """A context-aware suggestion with detailed reasoning."""
    id: str
    category: SuggestionCategory
    title: str
    description: str
    context_factors: List[str]
    confidence: ConfidenceLevel
    priority: int
    reasoning: str
    implementation_steps: List[str]
    expected_benefits: List[str]
    potential_risks: List[str]
    estimated_effort_hours: float
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PreventiveAlert:
    """An alert about a potential future issue."""
    id: str
    issue_type: IssueType
    title: str
    description: str
    likelihood: float  # 0.0 to 1.0
    potential_impact: str
    time_to_manifestation: timedelta
    prevention_actions: List[str]
    monitoring_metrics: List[str]
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationOpportunity:
    """An identified opportunity for optimization."""
    id: str
    area: str
    title: str
    description: str
    current_state: Dict[str, Any]
    target_state: Dict[str, Any]
    optimization_steps: List[str]
    expected_improvement: str
    effort_required: str
    roi_estimate: float
    prerequisites: List[str] = field(default_factory=list)


class ContextAwareSuggestionEngine:
    """Generates context-aware suggestions based on current development state."""
    
    def __init__(self, context_engine: ContextEngine):
        self.context_engine = context_engine
        self.suggestion_templates = self._load_suggestion_templates()
        self.context_analyzers = self._initialize_context_analyzers()
        
    def _load_suggestion_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load suggestion templates for different scenarios."""
        return {
            "missing_tests": {
                "category": SuggestionCategory.TESTING,
                "title": "Add Missing Test Coverage",
                "base_priority": 7,
                "effort_multiplier": 1.5
            },
            "complex_function": {
                "category": SuggestionCategory.CODE_QUALITY,
                "title": "Refactor Complex Function",
                "base_priority": 6,
                "effort_multiplier": 2.0
            },
            "outdated_dependency": {
                "category": SuggestionCategory.MAINTENANCE,
                "title": "Update Outdated Dependencies",
                "base_priority": 5,
                "effort_multiplier": 1.0
            },
            "security_pattern": {
                "category": SuggestionCategory.SECURITY,
                "title": "Address Security Pattern",
                "base_priority": 9,
                "effort_multiplier": 1.2
            },
            "performance_opportunity": {
                "category": SuggestionCategory.PERFORMANCE,
                "title": "Performance Optimization Opportunity",
                "base_priority": 6,
                "effort_multiplier": 2.5
            }
        }
    
    def _initialize_context_analyzers(self) -> Dict[str, Any]:
        """Initialize context analysis components."""
        return {
            "code_analyzer": CodeContextAnalyzer(),
            "project_analyzer": ProjectContextAnalyzer(),
            "team_analyzer": TeamContextAnalyzer(),
            "workflow_analyzer": WorkflowContextAnalyzer()
        }
    
    async def generate_contextual_suggestions(self, context: Dict[str, Any]) -> List[ContextualSuggestion]:
        """Generate context-aware suggestions based on current development state."""
        suggestions = []
        
        # Analyze different context dimensions
        code_context = await self.context_analyzers["code_analyzer"].analyze(context)
        project_context = await self.context_analyzers["project_analyzer"].analyze(context)
        team_context = await self.context_analyzers["team_analyzer"].analyze(context)
        workflow_context = await self.context_analyzers["workflow_analyzer"].analyze(context)
        
        # Generate suggestions for each context
        suggestions.extend(await self._generate_code_suggestions(code_context))
        suggestions.extend(await self._generate_project_suggestions(project_context))
        suggestions.extend(await self._generate_team_suggestions(team_context))
        suggestions.extend(await self._generate_workflow_suggestions(workflow_context))
        
        # Filter and prioritize based on context
        filtered_suggestions = await self._filter_and_prioritize(suggestions, context)
        
        return filtered_suggestions
    
    async def _generate_code_suggestions(self, code_context: Dict[str, Any]) -> List[ContextualSuggestion]:
        """Generate suggestions based on code analysis context."""
        suggestions = []
        
        # Check for complex functions
        complex_functions = code_context.get('complex_functions', [])
        for func in complex_functions:
            if func.get('complexity_score', 0) > 10:
                suggestions.append(ContextualSuggestion(
                    id=f"refactor_{func['name']}_{datetime.now().isoformat()}",
                    category=SuggestionCategory.CODE_QUALITY,
                    title=f"Refactor Complex Function: {func['name']}",
                    description=f"Function has complexity score of {func['complexity_score']}, consider breaking it down",
                    context_factors=[
                        f"High cyclomatic complexity: {func['complexity_score']}",
                        f"Function length: {func.get('line_count', 0)} lines",
                        f"Number of parameters: {func.get('param_count', 0)}"
                    ],
                    confidence=ConfidenceLevel.HIGH,
                    priority=7,
                    reasoning="High complexity makes code harder to understand, test, and maintain",
                    implementation_steps=[
                        "Extract smaller functions for distinct responsibilities",
                        "Reduce parameter count using objects or configuration",
                        "Add unit tests for each extracted function",
                        "Update documentation"
                    ],
                    expected_benefits=[
                        "Improved code readability",
                        "Easier testing and debugging",
                        "Better maintainability"
                    ],
                    potential_risks=[
                        "Temporary increase in number of functions",
                        "Need to update existing tests"
                    ],
                    estimated_effort_hours=2.5
                ))
        
        # Check for missing error handling
        functions_without_error_handling = code_context.get('functions_without_error_handling', [])
        if functions_without_error_handling:
            suggestions.append(ContextualSuggestion(
                id=f"error_handling_{datetime.now().isoformat()}",
                category=SuggestionCategory.CODE_QUALITY,
                title="Add Error Handling",
                description=f"{len(functions_without_error_handling)} functions lack proper error handling",
                context_factors=[
                    f"Functions without try-catch: {len(functions_without_error_handling)}",
                    "External API calls detected",
                    "File I/O operations present"
                ],
                confidence=ConfidenceLevel.MEDIUM,
                priority=6,
                reasoning="Proper error handling prevents application crashes and improves user experience",
                implementation_steps=[
                    "Add try-catch blocks for risky operations",
                    "Define custom exception types",
                    "Implement proper error logging",
                    "Add user-friendly error messages"
                ],
                expected_benefits=[
                    "Improved application stability",
                    "Better error diagnostics",
                    "Enhanced user experience"
                ],
                potential_risks=[
                    "Increased code verbosity",
                    "Need to handle various error scenarios"
                ],
                estimated_effort_hours=1.5
            ))
        
        return suggestions
    
    async def _generate_project_suggestions(self, project_context: Dict[str, Any]) -> List[ContextualSuggestion]:
        """Generate suggestions based on project-level context."""
        suggestions = []
        
        # Check test coverage
        test_coverage = project_context.get('test_coverage', 0)
        if test_coverage < 80:
            suggestions.append(ContextualSuggestion(
                id=f"test_coverage_{datetime.now().isoformat()}",
                category=SuggestionCategory.TESTING,
                title="Improve Test Coverage",
                description=f"Current test coverage is {test_coverage}%, target is 80%+",
                context_factors=[
                    f"Current coverage: {test_coverage}%",
                    f"Uncovered lines: {project_context.get('uncovered_lines', 0)}",
                    "Critical business logic identified"
                ],
                confidence=ConfidenceLevel.HIGH,
                priority=8,
                reasoning="Higher test coverage reduces bug risk and enables confident refactoring",
                implementation_steps=[
                    "Identify critical uncovered code paths",
                    "Write unit tests for core business logic",
                    "Add integration tests for key workflows",
                    "Set up coverage reporting in CI/CD"
                ],
                expected_benefits=[
                    "Reduced bug risk",
                    "Safer refactoring",
                    "Better code documentation through tests"
                ],
                potential_risks=[
                    "Initial time investment",
                    "Maintenance overhead for tests"
                ],
                estimated_effort_hours=4.0
            ))
        
        # Check for outdated dependencies
        outdated_deps = project_context.get('outdated_dependencies', [])
        if len(outdated_deps) > 3:
            high_risk_deps = [d for d in outdated_deps if d.get('security_risk', False)]
            suggestions.append(ContextualSuggestion(
                id=f"dependencies_{datetime.now().isoformat()}",
                category=SuggestionCategory.MAINTENANCE,
                title="Update Outdated Dependencies",
                description=f"{len(outdated_deps)} dependencies are outdated, {len(high_risk_deps)} have security risks",
                context_factors=[
                    f"Total outdated: {len(outdated_deps)}",
                    f"Security risks: {len(high_risk_deps)}",
                    f"Major version updates: {len([d for d in outdated_deps if d.get('major_update', False)])}"
                ],
                confidence=ConfidenceLevel.HIGH if high_risk_deps else ConfidenceLevel.MEDIUM,
                priority=9 if high_risk_deps else 5,
                reasoning="Outdated dependencies may contain security vulnerabilities and missing features",
                implementation_steps=[
                    "Review dependency update changelog",
                    "Update dependencies incrementally",
                    "Run comprehensive tests after updates",
                    "Update documentation if APIs changed"
                ],
                expected_benefits=[
                    "Improved security",
                    "Access to new features",
                    "Better performance"
                ],
                potential_risks=[
                    "Breaking changes in major updates",
                    "Compatibility issues",
                    "Need for code modifications"
                ],
                estimated_effort_hours=2.0
            ))
        
        return suggestions
    
    async def _generate_team_suggestions(self, team_context: Dict[str, Any]) -> List[ContextualSuggestion]:
        """Generate suggestions based on team collaboration context."""
        suggestions = []
        
        # Check code review participation
        review_participation = team_context.get('code_review_participation', 100)
        if review_participation < 80:
            suggestions.append(ContextualSuggestion(
                id=f"code_review_{datetime.now().isoformat()}",
                category=SuggestionCategory.WORKFLOW,
                title="Improve Code Review Participation",
                description=f"Code review participation is {review_participation}%, target is 80%+",
                context_factors=[
                    f"Current participation: {review_participation}%",
                    f"Unreviewed PRs: {team_context.get('unreviewed_prs', 0)}",
                    "Team size and availability"
                ],
                confidence=ConfidenceLevel.MEDIUM,
                priority=6,
                reasoning="Code reviews improve code quality and knowledge sharing",
                implementation_steps=[
                    "Set up code review guidelines",
                    "Implement review assignment rotation",
                    "Add review reminders and notifications",
                    "Track and report review metrics"
                ],
                expected_benefits=[
                    "Improved code quality",
                    "Better knowledge sharing",
                    "Reduced bug introduction"
                ],
                potential_risks=[
                    "Slower development velocity initially",
                    "Need for team process changes"
                ],
                estimated_effort_hours=1.0
            ))
        
        return suggestions
    
    async def _generate_workflow_suggestions(self, workflow_context: Dict[str, Any]) -> List[ContextualSuggestion]:
        """Generate suggestions based on development workflow context."""
        suggestions = []
        
        # Check build times
        avg_build_time = workflow_context.get('average_build_time_minutes', 0)
        if avg_build_time > 15:
            suggestions.append(ContextualSuggestion(
                id=f"build_optimization_{datetime.now().isoformat()}",
                category=SuggestionCategory.PERFORMANCE,
                title="Optimize Build Performance",
                description=f"Average build time is {avg_build_time} minutes, consider optimization",
                context_factors=[
                    f"Average build time: {avg_build_time} minutes",
                    f"Build steps: {workflow_context.get('build_steps', 0)}",
                    "Dependency compilation time"
                ],
                confidence=ConfidenceLevel.MEDIUM,
                priority=5,
                reasoning="Long build times slow down development feedback loops",
                implementation_steps=[
                    "Analyze build performance bottlenecks",
                    "Implement build caching strategies",
                    "Parallelize independent build steps",
                    "Optimize dependency management"
                ],
                expected_benefits=[
                    "Faster development feedback",
                    "Improved developer productivity",
                    "Reduced CI/CD costs"
                ],
                potential_risks=[
                    "Initial setup complexity",
                    "Cache invalidation issues"
                ],
                estimated_effort_hours=3.0
            ))
        
        return suggestions
    
    async def _filter_and_prioritize(self, suggestions: List[ContextualSuggestion], context: Dict[str, Any]) -> List[ContextualSuggestion]:
        """Filter and prioritize suggestions based on context."""
        # Remove duplicates
        unique_suggestions = {}
        for suggestion in suggestions:
            key = f"{suggestion.category.value}_{suggestion.title}"
            if key not in unique_suggestions or suggestion.priority > unique_suggestions[key].priority:
                unique_suggestions[key] = suggestion
        
        filtered_suggestions = list(unique_suggestions.values())
        
        # Adjust priorities based on context
        project_phase = context.get('project_phase', 'development')
        team_size = context.get('team_size', 1)
        
        for suggestion in filtered_suggestions:
            # Boost security suggestions in production phase
            if project_phase == 'production' and suggestion.category == SuggestionCategory.SECURITY:
                suggestion.priority = min(10, suggestion.priority + 2)
            
            # Boost workflow suggestions for larger teams
            if team_size > 5 and suggestion.category == SuggestionCategory.WORKFLOW:
                suggestion.priority = min(10, suggestion.priority + 1)
        
        # Sort by priority and confidence
        filtered_suggestions.sort(key=lambda s: (s.priority, s.confidence.value), reverse=True)
        
        return filtered_suggestions[:10]  # Return top 10 suggestions


class PreventiveIssueDetector:
    """Detects potential future issues before they become problems."""
    
    def __init__(self):
        self.issue_patterns = self._load_issue_patterns()
        self.detection_rules = self._initialize_detection_rules()
        
    def _load_issue_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns that indicate potential future issues."""
        return {
            "technical_debt_accumulation": {
                "indicators": ["increasing_complexity", "decreasing_test_coverage", "code_duplication"],
                "threshold": 0.7,
                "time_horizon_days": 30
            },
            "performance_degradation": {
                "indicators": ["increasing_response_time", "memory_usage_growth", "cpu_usage_trend"],
                "threshold": 0.8,
                "time_horizon_days": 14
            },
            "security_vulnerability_risk": {
                "indicators": ["outdated_security_deps", "insecure_patterns", "missing_security_headers"],
                "threshold": 0.6,
                "time_horizon_days": 7
            }
        }
    
    def _initialize_detection_rules(self) -> Dict[str, Any]:
        """Initialize detection rules for different issue types."""
        return {
            "complexity_growth_rate": 0.1,  # Max acceptable complexity growth per week
            "test_coverage_decline_rate": 0.05,  # Max acceptable coverage decline per week
            "dependency_age_threshold_days": 365,  # Dependencies older than this are risky
            "performance_degradation_threshold": 0.2  # 20% performance degradation threshold
        }
    
    async def detect_potential_issues(self, context: Dict[str, Any]) -> List[PreventiveAlert]:
        """Detect potential future issues based on current trends and patterns."""
        alerts = []
        
        # Detect technical debt accumulation
        tech_debt_alert = await self._detect_technical_debt_risk(context)
        if tech_debt_alert:
            alerts.append(tech_debt_alert)
        
        # Detect performance issues
        performance_alert = await self._detect_performance_risks(context)
        if performance_alert:
            alerts.append(performance_alert)
        
        # Detect security risks
        security_alert = await self._detect_security_risks(context)
        if security_alert:
            alerts.append(security_alert)
        
        # Detect maintainability risks
        maintainability_alert = await self._detect_maintainability_risks(context)
        if maintainability_alert:
            alerts.append(maintainability_alert)
        
        # Detect scalability concerns
        scalability_alert = await self._detect_scalability_concerns(context)
        if scalability_alert:
            alerts.append(scalability_alert)
        
        return alerts
    
    async def _detect_technical_debt_risk(self, context: Dict[str, Any]) -> Optional[PreventiveAlert]:
        """Detect risk of technical debt accumulation."""
        complexity_trend = context.get('complexity_trend', 'stable')
        test_coverage_trend = context.get('test_coverage_trend', 'stable')
        code_duplication = context.get('code_duplication_percentage', 0)
        
        risk_factors = []
        likelihood = 0.0
        
        if complexity_trend == 'increasing':
            risk_factors.append("Code complexity is increasing")
            likelihood += 0.3
        
        if test_coverage_trend == 'decreasing':
            risk_factors.append("Test coverage is declining")
            likelihood += 0.3
        
        if code_duplication > 15:
            risk_factors.append(f"High code duplication: {code_duplication}%")
            likelihood += 0.2
        
        refactoring_frequency = context.get('refactoring_frequency', 0)
        if refactoring_frequency < 0.1:  # Less than once per 10 commits
            risk_factors.append("Low refactoring frequency")
            likelihood += 0.2
        
        if likelihood > 0.5:
            return PreventiveAlert(
                id=f"tech_debt_risk_{datetime.now().isoformat()}",
                issue_type=IssueType.TECHNICAL_DEBT,
                title="Technical Debt Accumulation Risk",
                description="Current trends indicate increasing technical debt",
                likelihood=likelihood,
                potential_impact="Decreased development velocity, increased bug rate, higher maintenance costs",
                time_to_manifestation=timedelta(days=30),
                prevention_actions=[
                    "Schedule regular refactoring sessions",
                    "Implement code quality gates in CI/CD",
                    "Increase test coverage for new code",
                    "Reduce code duplication through extraction"
                ],
                monitoring_metrics=[
                    "Code complexity metrics",
                    "Test coverage percentage",
                    "Code duplication ratio",
                    "Refactoring frequency"
                ],
                context={
                    'risk_factors': risk_factors,
                    'complexity_trend': complexity_trend,
                    'test_coverage_trend': test_coverage_trend,
                    'code_duplication': code_duplication
                }
            )
        
        return None
    
    async def _detect_performance_risks(self, context: Dict[str, Any]) -> Optional[PreventiveAlert]:
        """Detect potential performance degradation risks."""
        response_time_trend = context.get('response_time_trend', 'stable')
        memory_usage_trend = context.get('memory_usage_trend', 'stable')
        database_query_count = context.get('database_queries_per_request', 0)
        
        risk_factors = []
        likelihood = 0.0
        
        if response_time_trend == 'increasing':
            risk_factors.append("Response times are increasing")
            likelihood += 0.4
        
        if memory_usage_trend == 'increasing':
            risk_factors.append("Memory usage is growing")
            likelihood += 0.3
        
        if database_query_count > 10:
            risk_factors.append(f"High database query count: {database_query_count} per request")
            likelihood += 0.3
        
        if likelihood > 0.6:
            return PreventiveAlert(
                id=f"performance_risk_{datetime.now().isoformat()}",
                issue_type=IssueType.PERFORMANCE_BOTTLENECK,
                title="Performance Degradation Risk",
                description="Performance metrics indicate potential bottlenecks",
                likelihood=likelihood,
                potential_impact="Slow user experience, increased infrastructure costs, scalability issues",
                time_to_manifestation=timedelta(days=14),
                prevention_actions=[
                    "Profile application performance",
                    "Optimize database queries",
                    "Implement caching strategies",
                    "Add performance monitoring"
                ],
                monitoring_metrics=[
                    "Response time percentiles",
                    "Memory usage patterns",
                    "Database query performance",
                    "CPU utilization"
                ],
                context={
                    'risk_factors': risk_factors,
                    'response_time_trend': response_time_trend,
                    'memory_usage_trend': memory_usage_trend
                }
            )
        
        return None
    
    async def _detect_security_risks(self, context: Dict[str, Any]) -> Optional[PreventiveAlert]:
        """Detect potential security vulnerability risks."""
        outdated_security_deps = context.get('outdated_security_dependencies', 0)
        insecure_patterns = context.get('insecure_code_patterns', [])
        missing_security_headers = context.get('missing_security_headers', [])
        
        risk_factors = []
        likelihood = 0.0
        
        if outdated_security_deps > 0:
            risk_factors.append(f"{outdated_security_deps} outdated security-related dependencies")
            likelihood += 0.4
        
        if len(insecure_patterns) > 0:
            risk_factors.append(f"{len(insecure_patterns)} insecure code patterns detected")
            likelihood += 0.3
        
        if len(missing_security_headers) > 2:
            risk_factors.append(f"{len(missing_security_headers)} missing security headers")
            likelihood += 0.2
        
        authentication_complexity = context.get('authentication_complexity', 'medium')
        if authentication_complexity == 'low':
            risk_factors.append("Simple authentication mechanism")
            likelihood += 0.1
        
        if likelihood > 0.4:
            return PreventiveAlert(
                id=f"security_risk_{datetime.now().isoformat()}",
                issue_type=IssueType.SECURITY_VULNERABILITY,
                title="Security Vulnerability Risk",
                description="Security analysis indicates potential vulnerabilities",
                likelihood=likelihood,
                potential_impact="Data breaches, unauthorized access, compliance violations",
                time_to_manifestation=timedelta(days=7),
                prevention_actions=[
                    "Update security-related dependencies",
                    "Fix insecure code patterns",
                    "Implement missing security headers",
                    "Conduct security audit"
                ],
                monitoring_metrics=[
                    "Dependency vulnerability count",
                    "Security scan results",
                    "Authentication failure rates",
                    "Access pattern anomalies"
                ],
                context={
                    'risk_factors': risk_factors,
                    'outdated_security_deps': outdated_security_deps,
                    'insecure_patterns': len(insecure_patterns)
                }
            )
        
        return None
    
    async def _detect_maintainability_risks(self, context: Dict[str, Any]) -> Optional[PreventiveAlert]:
        """Detect risks to code maintainability."""
        documentation_coverage = context.get('documentation_coverage', 100)
        team_knowledge_distribution = context.get('team_knowledge_distribution', 1.0)
        code_ownership_concentration = context.get('code_ownership_concentration', 0.5)
        
        risk_factors = []
        likelihood = 0.0
        
        if documentation_coverage < 50:
            risk_factors.append(f"Low documentation coverage: {documentation_coverage}%")
            likelihood += 0.3
        
        if team_knowledge_distribution < 0.3:  # Knowledge concentrated in few people
            risk_factors.append("Knowledge concentrated in few team members")
            likelihood += 0.4
        
        if code_ownership_concentration > 0.8:  # One person owns most code
            risk_factors.append("High code ownership concentration")
            likelihood += 0.3
        
        if likelihood > 0.5:
            return PreventiveAlert(
                id=f"maintainability_risk_{datetime.now().isoformat()}",
                issue_type=IssueType.MAINTAINABILITY_RISK,
                title="Code Maintainability Risk",
                description="Factors indicate potential maintainability challenges",
                likelihood=likelihood,
                potential_impact="Difficulty onboarding new developers, knowledge silos, maintenance bottlenecks",
                time_to_manifestation=timedelta(days=60),
                prevention_actions=[
                    "Improve code documentation",
                    "Implement knowledge sharing sessions",
                    "Distribute code ownership",
                    "Create architectural decision records"
                ],
                monitoring_metrics=[
                    "Documentation coverage",
                    "Code review participation",
                    "Knowledge sharing frequency",
                    "Bus factor analysis"
                ],
                context={
                    'risk_factors': risk_factors,
                    'documentation_coverage': documentation_coverage,
                    'team_knowledge_distribution': team_knowledge_distribution
                }
            )
        
        return None
    
    async def _detect_scalability_concerns(self, context: Dict[str, Any]) -> Optional[PreventiveAlert]:
        """Detect potential scalability concerns."""
        user_growth_rate = context.get('user_growth_rate_monthly', 0)
        current_capacity_utilization = context.get('capacity_utilization', 0)
        architecture_scalability_score = context.get('architecture_scalability_score', 1.0)
        
        risk_factors = []
        likelihood = 0.0
        
        if user_growth_rate > 0.2 and current_capacity_utilization > 0.7:
            risk_factors.append("High user growth with high capacity utilization")
            likelihood += 0.5
        
        if architecture_scalability_score < 0.6:
            risk_factors.append("Architecture has scalability limitations")
            likelihood += 0.3
        
        database_connection_pool_usage = context.get('db_connection_pool_usage', 0)
        if database_connection_pool_usage > 0.8:
            risk_factors.append("High database connection pool usage")
            likelihood += 0.2
        
        if likelihood > 0.4:
            return PreventiveAlert(
                id=f"scalability_risk_{datetime.now().isoformat()}",
                issue_type=IssueType.SCALABILITY_CONCERN,
                title="Scalability Concern",
                description="Growth patterns indicate potential scalability challenges",
                likelihood=likelihood,
                potential_impact="Service degradation under load, user experience issues, infrastructure costs",
                time_to_manifestation=timedelta(days=45),
                prevention_actions=[
                    "Plan infrastructure scaling",
                    "Optimize database queries and connections",
                    "Implement caching strategies",
                    "Review architecture for bottlenecks"
                ],
                monitoring_metrics=[
                    "Response time under load",
                    "Resource utilization trends",
                    "Database performance metrics",
                    "User growth patterns"
                ],
                context={
                    'risk_factors': risk_factors,
                    'user_growth_rate': user_growth_rate,
                    'capacity_utilization': current_capacity_utilization
                }
            )
        
        return None


# Context Analyzer Classes
class CodeContextAnalyzer:
    """Analyzes code-level context for suggestions."""
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code context."""
        code_files = context.get('code_files', [])
        semantic_analysis = context.get('semantic_analysis', {})
        
        # Analyze function complexity
        complex_functions = []
        functions_without_error_handling = []
        
        for file_analysis in semantic_analysis.get('files', []):
            for function in file_analysis.get('functions', []):
                complexity = function.get('complexity_score', 0)
                if complexity > 10:
                    complex_functions.append({
                        'name': function.get('name', 'unknown'),
                        'complexity_score': complexity,
                        'line_count': function.get('line_count', 0),
                        'param_count': function.get('param_count', 0)
                    })
                
                if not function.get('has_error_handling', False):
                    functions_without_error_handling.append(function.get('name', 'unknown'))
        
        return {
            'complex_functions': complex_functions,
            'functions_without_error_handling': functions_without_error_handling,
            'total_functions': sum(len(f.get('functions', [])) for f in semantic_analysis.get('files', [])),
            'average_complexity': sum(f.get('complexity_score', 0) for file_analysis in semantic_analysis.get('files', []) for f in file_analysis.get('functions', [])) / max(1, sum(len(f.get('functions', [])) for f in semantic_analysis.get('files', [])))
        }


class ProjectContextAnalyzer:
    """Analyzes project-level context for suggestions."""
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project context."""
        project_metrics = context.get('project_metrics', {})
        dependencies = context.get('dependencies', [])
        
        # Analyze test coverage
        test_coverage = project_metrics.get('test_coverage', 0)
        uncovered_lines = project_metrics.get('uncovered_lines', 0)
        
        # Analyze dependencies
        outdated_dependencies = []
        for dep in dependencies:
            if dep.get('is_outdated', False):
                outdated_dependencies.append({
                    'name': dep.get('name', ''),
                    'current_version': dep.get('current_version', ''),
                    'latest_version': dep.get('latest_version', ''),
                    'security_risk': dep.get('has_security_vulnerabilities', False),
                    'major_update': dep.get('is_major_update', False)
                })
        
        return {
            'test_coverage': test_coverage,
            'uncovered_lines': uncovered_lines,
            'outdated_dependencies': outdated_dependencies,
            'total_dependencies': len(dependencies),
            'security_risk_dependencies': len([d for d in outdated_dependencies if d.get('security_risk', False)])
        }


class TeamContextAnalyzer:
    """Analyzes team collaboration context for suggestions."""
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team context."""
        team_metrics = context.get('team_metrics', {})
        
        return {
            'code_review_participation': team_metrics.get('code_review_participation', 100),
            'unreviewed_prs': team_metrics.get('unreviewed_prs', 0),
            'team_size': team_metrics.get('team_size', 1),
            'knowledge_sharing_frequency': team_metrics.get('knowledge_sharing_frequency', 0)
        }


class WorkflowContextAnalyzer:
    """Analyzes development workflow context for suggestions."""
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow context."""
        workflow_metrics = context.get('workflow_metrics', {})
        
        return {
            'average_build_time_minutes': workflow_metrics.get('average_build_time_minutes', 0),
            'build_steps': workflow_metrics.get('build_steps', 0),
            'deployment_frequency': workflow_metrics.get('deployment_frequency', 0),
            'lead_time_hours': workflow_metrics.get('lead_time_hours', 0)
        }