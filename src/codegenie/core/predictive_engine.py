"""
Predictive Development Assistant Engine

This module implements development pattern analysis, proactive suggestions,
and future issue prediction capabilities for enhanced development workflow optimization.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
from pathlib import Path
import statistics
from collections import defaultdict, Counter

from .code_intelligence import CodeEntity, SemanticAnalysis
from .context_engine import ProjectEvolutionTracker
from .learning_engine import UserPreferenceModeler


class PatternType(Enum):
    """Types of development patterns that can be detected."""
    WORKFLOW = "workflow"
    CODING_STYLE = "coding_style"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    COLLABORATION = "collaboration"
    PERFORMANCE = "performance"
    SECURITY = "security"


class PredictionType(Enum):
    """Types of predictions the system can make."""
    NEXT_TASK = "next_task"
    POTENTIAL_ISSUE = "potential_issue"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    REFACTORING_NEED = "refactoring_need"
    TESTING_GAP = "testing_gap"
    SECURITY_RISK = "security_risk"


class ConfidenceLevel(Enum):
    """Confidence levels for predictions and suggestions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class DevelopmentPattern:
    """Represents a detected development pattern."""
    id: str
    type: PatternType
    name: str
    description: str
    frequency: int
    confidence: ConfidenceLevel
    context: Dict[str, Any]
    first_seen: datetime
    last_seen: datetime
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VelocityMetrics:
    """Development velocity and productivity metrics."""
    commits_per_day: float
    lines_changed_per_day: float
    files_modified_per_day: float
    features_completed_per_week: float
    bugs_fixed_per_week: float
    code_review_time_hours: float
    build_success_rate: float
    test_coverage_percentage: float
    technical_debt_ratio: float


@dataclass
class CollaborationPattern:
    """Team collaboration patterns and metrics."""
    pair_programming_frequency: float
    code_review_participation: float
    knowledge_sharing_events: int
    cross_team_interactions: int
    communication_channels_used: List[str]
    meeting_frequency: float
    documentation_updates: int


@dataclass
class ProjectTrend:
    """Project evolution trends and insights."""
    complexity_trend: str  # increasing, decreasing, stable
    quality_trend: str
    velocity_trend: str
    team_size_trend: str
    technology_adoption_rate: float
    refactoring_frequency: float
    bug_introduction_rate: float
    feature_completion_rate: float


@dataclass
class PredictiveSuggestion:
    """A proactive suggestion from the predictive engine."""
    id: str
    type: PredictionType
    title: str
    description: str
    confidence: ConfidenceLevel
    priority: int  # 1-10, 10 being highest
    reasoning: str
    suggested_actions: List[str]
    estimated_impact: str
    estimated_effort: str
    context: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None


class DevelopmentPatternAnalyzer:
    """Analyzes development patterns and workflows."""
    
    def __init__(self):
        self.patterns: Dict[str, DevelopmentPattern] = {}
        self.pattern_history: List[Dict[str, Any]] = []
        self.velocity_history: List[VelocityMetrics] = []
        self.collaboration_history: List[CollaborationPattern] = []
        
    async def analyze_workflow_patterns(self, project_data: Dict[str, Any]) -> List[DevelopmentPattern]:
        """Analyze workflow patterns from project data."""
        patterns = []
        
        # Analyze commit patterns
        commit_pattern = await self._analyze_commit_patterns(project_data.get('commits', []))
        if commit_pattern:
            patterns.append(commit_pattern)
            
        # Analyze file modification patterns
        file_pattern = await self._analyze_file_modification_patterns(project_data.get('file_changes', []))
        if file_pattern:
            patterns.append(file_pattern)
            
        # Analyze testing patterns
        test_pattern = await self._analyze_testing_patterns(project_data.get('test_data', {}))
        if test_pattern:
            patterns.append(test_pattern)
            
        # Store patterns
        for pattern in patterns:
            self.patterns[pattern.id] = pattern
            
        return patterns
    
    async def _analyze_commit_patterns(self, commits: List[Dict[str, Any]]) -> Optional[DevelopmentPattern]:
        """Analyze commit timing and frequency patterns."""
        if not commits:
            return None
            
        # Analyze commit timing
        commit_times = [datetime.fromisoformat(c['timestamp']) for c in commits if 'timestamp' in c]
        if not commit_times:
            return None
            
        # Calculate patterns
        hourly_distribution = defaultdict(int)
        daily_distribution = defaultdict(int)
        
        for commit_time in commit_times:
            hourly_distribution[commit_time.hour] += 1
            daily_distribution[commit_time.weekday()] += 1
            
        # Find peak hours and days
        peak_hour = max(hourly_distribution.items(), key=lambda x: x[1])[0]
        peak_day = max(daily_distribution.items(), key=lambda x: x[1])[0]
        
        # Calculate frequency
        if len(commit_times) > 1:
            time_span = (max(commit_times) - min(commit_times)).days
            frequency = len(commit_times) / max(time_span, 1)
        else:
            frequency = 1
            
        confidence = ConfidenceLevel.HIGH if len(commits) > 50 else ConfidenceLevel.MEDIUM
        
        return DevelopmentPattern(
            id=f"commit_pattern_{datetime.now().isoformat()}",
            type=PatternType.WORKFLOW,
            name="Commit Timing Pattern",
            description=f"Developer typically commits at hour {peak_hour} on weekday {peak_day}",
            frequency=int(frequency),
            confidence=confidence,
            context={
                'peak_hour': peak_hour,
                'peak_day': peak_day,
                'total_commits': len(commits),
                'hourly_distribution': dict(hourly_distribution),
                'daily_distribution': dict(daily_distribution)
            },
            first_seen=min(commit_times),
            last_seen=max(commit_times)
        )
    
    async def _analyze_file_modification_patterns(self, file_changes: List[Dict[str, Any]]) -> Optional[DevelopmentPattern]:
        """Analyze file modification patterns."""
        if not file_changes:
            return None
            
        # Analyze file types and modification frequency
        file_types = defaultdict(int)
        modification_sizes = []
        
        for change in file_changes:
            file_path = change.get('file_path', '')
            if '.' in file_path:
                ext = file_path.split('.')[-1]
                file_types[ext] += 1
                
            lines_changed = change.get('lines_added', 0) + change.get('lines_deleted', 0)
            if lines_changed > 0:
                modification_sizes.append(lines_changed)
        
        if not file_types:
            return None
            
        # Find most common file type
        most_common_type = max(file_types.items(), key=lambda x: x[1])[0]
        avg_modification_size = statistics.mean(modification_sizes) if modification_sizes else 0
        
        confidence = ConfidenceLevel.HIGH if len(file_changes) > 20 else ConfidenceLevel.MEDIUM
        
        return DevelopmentPattern(
            id=f"file_pattern_{datetime.now().isoformat()}",
            type=PatternType.CODING_STYLE,
            name="File Modification Pattern",
            description=f"Developer primarily works with {most_common_type} files, avg {avg_modification_size:.1f} lines per change",
            frequency=len(file_changes),
            confidence=confidence,
            context={
                'file_types': dict(file_types),
                'most_common_type': most_common_type,
                'avg_modification_size': avg_modification_size,
                'total_changes': len(file_changes)
            },
            first_seen=datetime.now() - timedelta(days=30),  # Placeholder
            last_seen=datetime.now()
        )
    
    async def _analyze_testing_patterns(self, test_data: Dict[str, Any]) -> Optional[DevelopmentPattern]:
        """Analyze testing patterns and practices."""
        if not test_data:
            return None
            
        test_frequency = test_data.get('test_runs_per_week', 0)
        test_coverage = test_data.get('average_coverage', 0)
        test_types = test_data.get('test_types', [])
        
        if test_frequency == 0:
            return None
            
        # Determine testing pattern
        if test_frequency > 20:
            pattern_name = "High-Frequency Testing"
            description = "Developer runs tests very frequently (TDD approach)"
        elif test_frequency > 10:
            pattern_name = "Regular Testing"
            description = "Developer maintains regular testing schedule"
        else:
            pattern_name = "Infrequent Testing"
            description = "Developer tests infrequently, potential risk area"
            
        confidence = ConfidenceLevel.HIGH if test_frequency > 5 else ConfidenceLevel.LOW
        
        return DevelopmentPattern(
            id=f"test_pattern_{datetime.now().isoformat()}",
            type=PatternType.TESTING,
            name=pattern_name,
            description=description,
            frequency=int(test_frequency),
            confidence=confidence,
            context={
                'test_frequency': test_frequency,
                'test_coverage': test_coverage,
                'test_types': test_types
            },
            first_seen=datetime.now() - timedelta(days=30),
            last_seen=datetime.now()
        )
    
    async def calculate_velocity_metrics(self, project_data: Dict[str, Any]) -> VelocityMetrics:
        """Calculate development velocity and productivity metrics."""
        commits = project_data.get('commits', [])
        file_changes = project_data.get('file_changes', [])
        features = project_data.get('features', [])
        bugs = project_data.get('bugs', [])
        reviews = project_data.get('code_reviews', [])
        builds = project_data.get('builds', [])
        tests = project_data.get('test_results', {})
        
        # Calculate time span
        if commits:
            commit_times = [datetime.fromisoformat(c['timestamp']) for c in commits if 'timestamp' in c]
            if commit_times:
                time_span_days = (max(commit_times) - min(commit_times)).days or 1
            else:
                time_span_days = 30
        else:
            time_span_days = 30
            
        # Calculate metrics
        commits_per_day = len(commits) / time_span_days
        
        total_lines_changed = sum(
            fc.get('lines_added', 0) + fc.get('lines_deleted', 0) 
            for fc in file_changes
        )
        lines_changed_per_day = total_lines_changed / time_span_days
        
        files_modified_per_day = len(file_changes) / time_span_days
        
        completed_features = [f for f in features if f.get('status') == 'completed']
        features_completed_per_week = len(completed_features) / (time_span_days / 7)
        
        fixed_bugs = [b for b in bugs if b.get('status') == 'fixed']
        bugs_fixed_per_week = len(fixed_bugs) / (time_span_days / 7)
        
        # Code review metrics
        if reviews:
            review_times = [r.get('review_time_hours', 0) for r in reviews]
            code_review_time_hours = statistics.mean(review_times) if review_times else 0
        else:
            code_review_time_hours = 0
            
        # Build success rate
        if builds:
            successful_builds = [b for b in builds if b.get('status') == 'success']
            build_success_rate = len(successful_builds) / len(builds) * 100
        else:
            build_success_rate = 100
            
        # Test coverage
        test_coverage_percentage = tests.get('coverage_percentage', 0)
        
        # Technical debt (simplified calculation)
        code_smells = project_data.get('code_smells', [])
        total_lines = sum(fc.get('lines_added', 0) for fc in file_changes)
        technical_debt_ratio = len(code_smells) / max(total_lines, 1) * 100
        
        return VelocityMetrics(
            commits_per_day=commits_per_day,
            lines_changed_per_day=lines_changed_per_day,
            files_modified_per_day=files_modified_per_day,
            features_completed_per_week=features_completed_per_week,
            bugs_fixed_per_week=bugs_fixed_per_week,
            code_review_time_hours=code_review_time_hours,
            build_success_rate=build_success_rate,
            test_coverage_percentage=test_coverage_percentage,
            technical_debt_ratio=technical_debt_ratio
        )
    
    async def analyze_collaboration_patterns(self, team_data: Dict[str, Any]) -> CollaborationPattern:
        """Analyze team collaboration patterns."""
        pair_sessions = team_data.get('pair_programming_sessions', [])
        reviews = team_data.get('code_reviews', [])
        meetings = team_data.get('meetings', [])
        docs = team_data.get('documentation_updates', [])
        communications = team_data.get('communications', [])
        
        # Calculate collaboration metrics
        time_span_days = 30  # Default analysis period
        
        pair_programming_frequency = len(pair_sessions) / time_span_days
        
        # Code review participation
        total_reviews = len(reviews)
        participated_reviews = len([r for r in reviews if r.get('participated', False)])
        code_review_participation = participated_reviews / max(total_reviews, 1) * 100
        
        knowledge_sharing_events = len([m for m in meetings if m.get('type') == 'knowledge_sharing'])
        cross_team_interactions = len([c for c in communications if c.get('cross_team', False)])
        
        communication_channels = list(set(c.get('channel', '') for c in communications))
        meeting_frequency = len(meetings) / (time_span_days / 7)  # per week
        documentation_updates = len(docs)
        
        return CollaborationPattern(
            pair_programming_frequency=pair_programming_frequency,
            code_review_participation=code_review_participation,
            knowledge_sharing_events=knowledge_sharing_events,
            cross_team_interactions=cross_team_interactions,
            communication_channels_used=communication_channels,
            meeting_frequency=meeting_frequency,
            documentation_updates=documentation_updates
        )
    
    async def analyze_project_trends(self, historical_data: List[Dict[str, Any]]) -> ProjectTrend:
        """Analyze project evolution trends over time."""
        if len(historical_data) < 2:
            return ProjectTrend(
                complexity_trend="stable",
                quality_trend="stable", 
                velocity_trend="stable",
                team_size_trend="stable",
                technology_adoption_rate=0.0,
                refactoring_frequency=0.0,
                bug_introduction_rate=0.0,
                feature_completion_rate=0.0
            )
        
        # Calculate trends
        complexity_values = [d.get('complexity_score', 0) for d in historical_data]
        quality_values = [d.get('quality_score', 0) for d in historical_data]
        velocity_values = [d.get('velocity_score', 0) for d in historical_data]
        team_sizes = [d.get('team_size', 1) for d in historical_data]
        
        # Determine trends
        complexity_trend = self._calculate_trend(complexity_values)
        quality_trend = self._calculate_trend(quality_values)
        velocity_trend = self._calculate_trend(velocity_values)
        team_size_trend = self._calculate_trend(team_sizes)
        
        # Calculate rates
        total_days = len(historical_data)
        technology_changes = sum(d.get('technology_changes', 0) for d in historical_data)
        technology_adoption_rate = technology_changes / total_days
        
        refactoring_events = sum(d.get('refactoring_events', 0) for d in historical_data)
        refactoring_frequency = refactoring_events / total_days
        
        bugs_introduced = sum(d.get('bugs_introduced', 0) for d in historical_data)
        bug_introduction_rate = bugs_introduced / total_days
        
        features_completed = sum(d.get('features_completed', 0) for d in historical_data)
        feature_completion_rate = features_completed / total_days
        
        return ProjectTrend(
            complexity_trend=complexity_trend,
            quality_trend=quality_trend,
            velocity_trend=velocity_trend,
            team_size_trend=team_size_trend,
            technology_adoption_rate=technology_adoption_rate,
            refactoring_frequency=refactoring_frequency,
            bug_introduction_rate=bug_introduction_rate,
            feature_completion_rate=feature_completion_rate
        )
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return "stable"
            
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"


class ProactiveSuggestionEngine:
    """Generates proactive suggestions based on patterns and predictions."""
    
    def __init__(self, pattern_analyzer: DevelopmentPatternAnalyzer):
        self.pattern_analyzer = pattern_analyzer
        self.suggestions: List[PredictiveSuggestion] = []
        self.suggestion_history: List[PredictiveSuggestion] = []
        
    async def generate_task_recommendations(self, context: Dict[str, Any]) -> List[PredictiveSuggestion]:
        """Generate recommendations for next tasks based on patterns."""
        suggestions = []
        
        # Analyze current context
        current_files = context.get('current_files', [])
        recent_changes = context.get('recent_changes', [])
        project_state = context.get('project_state', {})
        
        # Generate suggestions based on patterns
        suggestions.extend(await self._suggest_based_on_file_patterns(current_files))
        suggestions.extend(await self._suggest_based_on_change_patterns(recent_changes))
        suggestions.extend(await self._suggest_based_on_project_state(project_state))
        
        # Store suggestions
        self.suggestions.extend(suggestions)
        
        return suggestions
    
    async def _suggest_based_on_file_patterns(self, current_files: List[str]) -> List[PredictiveSuggestion]:
        """Generate suggestions based on current file patterns."""
        suggestions = []
        
        # Analyze file types
        file_extensions = [Path(f).suffix for f in current_files if Path(f).suffix]
        
        if '.py' in file_extensions:
            # Python-specific suggestions
            if not any('test_' in f for f in current_files):
                suggestions.append(PredictiveSuggestion(
                    id=f"test_suggestion_{datetime.now().isoformat()}",
                    type=PredictionType.TESTING_GAP,
                    title="Add Unit Tests",
                    description="No test files detected for Python modules",
                    confidence=ConfidenceLevel.HIGH,
                    priority=7,
                    reasoning="Python modules should have corresponding test files for quality assurance",
                    suggested_actions=[
                        "Create test files for existing modules",
                        "Set up pytest configuration",
                        "Add test coverage reporting"
                    ],
                    estimated_impact="High - Improves code quality and reliability",
                    estimated_effort="Medium - 2-4 hours",
                    context={'file_types': file_extensions},
                    created_at=datetime.now()
                ))
        
        if '.js' in file_extensions or '.ts' in file_extensions:
            # JavaScript/TypeScript suggestions
            if not any('package.json' in f for f in current_files):
                suggestions.append(PredictiveSuggestion(
                    id=f"package_suggestion_{datetime.now().isoformat()}",
                    type=PredictionType.OPTIMIZATION_OPPORTUNITY,
                    title="Initialize Package Management",
                    description="JavaScript/TypeScript files without package.json",
                    confidence=ConfidenceLevel.MEDIUM,
                    priority=5,
                    reasoning="Package.json is essential for dependency management in JS/TS projects",
                    suggested_actions=[
                        "Run npm init or yarn init",
                        "Add necessary dependencies",
                        "Configure build scripts"
                    ],
                    estimated_impact="Medium - Enables proper dependency management",
                    estimated_effort="Low - 30 minutes",
                    context={'file_types': file_extensions},
                    created_at=datetime.now()
                ))
        
        return suggestions
    
    async def _suggest_based_on_change_patterns(self, recent_changes: List[Dict[str, Any]]) -> List[PredictiveSuggestion]:
        """Generate suggestions based on recent change patterns."""
        suggestions = []
        
        if not recent_changes:
            return suggestions
        
        # Analyze change frequency and size
        large_changes = [c for c in recent_changes if c.get('lines_changed', 0) > 100]
        
        if len(large_changes) > len(recent_changes) * 0.5:
            suggestions.append(PredictiveSuggestion(
                id=f"refactor_suggestion_{datetime.now().isoformat()}",
                type=PredictionType.REFACTORING_NEED,
                title="Consider Breaking Down Large Changes",
                description="Recent changes are consistently large, consider smaller incremental changes",
                confidence=ConfidenceLevel.MEDIUM,
                priority=6,
                reasoning="Large changes are harder to review and more likely to introduce bugs",
                suggested_actions=[
                    "Break down features into smaller tasks",
                    "Use feature flags for incremental delivery",
                    "Implement more frequent commits"
                ],
                estimated_impact="High - Reduces risk and improves code review quality",
                estimated_effort="Low - Process change",
                context={'large_changes_ratio': len(large_changes) / len(recent_changes)},
                created_at=datetime.now()
            ))
        
        # Check for security-related changes
        security_files = [c for c in recent_changes if any(
            keyword in c.get('file_path', '').lower() 
            for keyword in ['auth', 'security', 'password', 'token', 'crypto']
        )]
        
        if security_files:
            suggestions.append(PredictiveSuggestion(
                id=f"security_review_{datetime.now().isoformat()}",
                type=PredictionType.SECURITY_RISK,
                title="Security Review Recommended",
                description="Recent changes involve security-related files",
                confidence=ConfidenceLevel.HIGH,
                priority=9,
                reasoning="Security-related changes require careful review to prevent vulnerabilities",
                suggested_actions=[
                    "Conduct security code review",
                    "Run security scanning tools",
                    "Update security documentation"
                ],
                estimated_impact="Critical - Prevents security vulnerabilities",
                estimated_effort="Medium - 1-2 hours",
                context={'security_files': len(security_files)},
                created_at=datetime.now()
            ))
        
        return suggestions
    
    async def _suggest_based_on_project_state(self, project_state: Dict[str, Any]) -> List[PredictiveSuggestion]:
        """Generate suggestions based on overall project state."""
        suggestions = []
        
        # Check test coverage
        test_coverage = project_state.get('test_coverage', 0)
        if test_coverage < 70:
            suggestions.append(PredictiveSuggestion(
                id=f"coverage_suggestion_{datetime.now().isoformat()}",
                type=PredictionType.TESTING_GAP,
                title="Improve Test Coverage",
                description=f"Current test coverage is {test_coverage}%, below recommended 70%",
                confidence=ConfidenceLevel.HIGH,
                priority=8,
                reasoning="Low test coverage increases risk of bugs and makes refactoring dangerous",
                suggested_actions=[
                    "Add tests for uncovered code paths",
                    "Focus on critical business logic",
                    "Set up coverage reporting in CI"
                ],
                estimated_impact="High - Reduces bug risk and enables safe refactoring",
                estimated_effort="High - 4-8 hours",
                context={'current_coverage': test_coverage},
                created_at=datetime.now()
            ))
        
        # Check documentation
        has_readme = project_state.get('has_readme', False)
        if not has_readme:
            suggestions.append(PredictiveSuggestion(
                id=f"docs_suggestion_{datetime.now().isoformat()}",
                type=PredictionType.OPTIMIZATION_OPPORTUNITY,
                title="Add Project Documentation",
                description="Project lacks README documentation",
                confidence=ConfidenceLevel.MEDIUM,
                priority=4,
                reasoning="Documentation improves project maintainability and onboarding",
                suggested_actions=[
                    "Create comprehensive README.md",
                    "Add installation instructions",
                    "Document API and usage examples"
                ],
                estimated_impact="Medium - Improves project accessibility",
                estimated_effort="Medium - 1-3 hours",
                context={'documentation_status': 'missing'},
                created_at=datetime.now()
            ))
        
        return suggestions
    
    async def detect_potential_issues(self, context: Dict[str, Any]) -> List[PredictiveSuggestion]:
        """Detect potential future issues based on current patterns."""
        suggestions = []
        
        # Analyze complexity trends
        complexity_trend = context.get('complexity_trend', 'stable')
        if complexity_trend == 'increasing':
            suggestions.append(PredictiveSuggestion(
                id=f"complexity_warning_{datetime.now().isoformat()}",
                type=PredictionType.POTENTIAL_ISSUE,
                title="Rising Code Complexity Detected",
                description="Code complexity has been increasing, may lead to maintenance issues",
                confidence=ConfidenceLevel.MEDIUM,
                priority=7,
                reasoning="Increasing complexity makes code harder to understand and maintain",
                suggested_actions=[
                    "Review and refactor complex functions",
                    "Extract common functionality",
                    "Add code complexity monitoring"
                ],
                estimated_impact="High - Prevents future maintenance problems",
                estimated_effort="High - 4-6 hours",
                context={'trend': complexity_trend},
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            ))
        
        # Check for performance issues
        performance_metrics = context.get('performance_metrics', {})
        if performance_metrics.get('response_time_trend') == 'increasing':
            suggestions.append(PredictiveSuggestion(
                id=f"performance_warning_{datetime.now().isoformat()}",
                type=PredictionType.POTENTIAL_ISSUE,
                title="Performance Degradation Trend",
                description="Application response times are increasing",
                confidence=ConfidenceLevel.HIGH,
                priority=8,
                reasoning="Performance degradation affects user experience and scalability",
                suggested_actions=[
                    "Profile application performance",
                    "Identify and optimize bottlenecks",
                    "Add performance monitoring"
                ],
                estimated_impact="High - Maintains user experience",
                estimated_effort="Medium - 2-4 hours",
                context=performance_metrics,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=3)
            ))
        
        return suggestions
    
    async def identify_optimization_opportunities(self, context: Dict[str, Any]) -> List[PredictiveSuggestion]:
        """Identify opportunities for process and code optimization."""
        suggestions = []
        
        # Check build times
        build_time = context.get('average_build_time_minutes', 0)
        if build_time > 10:
            suggestions.append(PredictiveSuggestion(
                id=f"build_optimization_{datetime.now().isoformat()}",
                type=PredictionType.OPTIMIZATION_OPPORTUNITY,
                title="Optimize Build Performance",
                description=f"Build time is {build_time} minutes, consider optimization",
                confidence=ConfidenceLevel.MEDIUM,
                priority=5,
                reasoning="Long build times slow down development feedback loops",
                suggested_actions=[
                    "Analyze build bottlenecks",
                    "Implement build caching",
                    "Parallelize build steps"
                ],
                estimated_impact="Medium - Improves development velocity",
                estimated_effort="Medium - 2-3 hours",
                context={'build_time': build_time},
                created_at=datetime.now()
            ))
        
        # Check dependency management
        outdated_deps = context.get('outdated_dependencies', 0)
        if outdated_deps > 5:
            suggestions.append(PredictiveSuggestion(
                id=f"deps_optimization_{datetime.now().isoformat()}",
                type=PredictionType.OPTIMIZATION_OPPORTUNITY,
                title="Update Dependencies",
                description=f"{outdated_deps} dependencies are outdated",
                confidence=ConfidenceLevel.HIGH,
                priority=6,
                reasoning="Outdated dependencies may have security vulnerabilities and missing features",
                suggested_actions=[
                    "Review and update dependencies",
                    "Test for breaking changes",
                    "Set up automated dependency monitoring"
                ],
                estimated_impact="Medium - Improves security and features",
                estimated_effort="Medium - 1-2 hours",
                context={'outdated_count': outdated_deps},
                created_at=datetime.now()
            ))
        
        return suggestions


class PredictiveDevelopmentAssistant:
    """Main predictive development assistant that coordinates all predictive capabilities."""
    
    def __init__(self):
        self.pattern_analyzer = DevelopmentPatternAnalyzer()
        self.suggestion_engine = ProactiveSuggestionEngine(self.pattern_analyzer)
        self.prediction_history: List[Dict[str, Any]] = []
        
    async def analyze_development_context(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis of development context."""
        # Analyze patterns
        patterns = await self.pattern_analyzer.analyze_workflow_patterns(project_data)
        
        # Calculate metrics
        velocity_metrics = await self.pattern_analyzer.calculate_velocity_metrics(project_data)
        
        # Analyze collaboration
        team_data = project_data.get('team_data', {})
        collaboration_patterns = await self.pattern_analyzer.analyze_collaboration_patterns(team_data)
        
        # Analyze trends
        historical_data = project_data.get('historical_data', [])
        project_trends = await self.pattern_analyzer.analyze_project_trends(historical_data)
        
        return {
            'patterns': patterns,
            'velocity_metrics': velocity_metrics,
            'collaboration_patterns': collaboration_patterns,
            'project_trends': project_trends,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    async def generate_proactive_suggestions(self, context: Dict[str, Any]) -> List[PredictiveSuggestion]:
        """Generate comprehensive proactive suggestions."""
        all_suggestions = []
        
        # Generate different types of suggestions
        task_suggestions = await self.suggestion_engine.generate_task_recommendations(context)
        all_suggestions.extend(task_suggestions)
        
        issue_predictions = await self.suggestion_engine.detect_potential_issues(context)
        all_suggestions.extend(issue_predictions)
        
        optimization_opportunities = await self.suggestion_engine.identify_optimization_opportunities(context)
        all_suggestions.extend(optimization_opportunities)
        
        # Sort by priority and confidence
        all_suggestions.sort(key=lambda s: (s.priority, s.confidence.value), reverse=True)
        
        # Store prediction history
        self.prediction_history.append({
            'timestamp': datetime.now().isoformat(),
            'context_summary': self._summarize_context(context),
            'suggestions_count': len(all_suggestions),
            'high_priority_count': len([s for s in all_suggestions if s.priority >= 7])
        })
        
        return all_suggestions
    
    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the analysis context."""
        return {
            'files_analyzed': len(context.get('current_files', [])),
            'recent_changes': len(context.get('recent_changes', [])),
            'has_project_state': bool(context.get('project_state')),
            'has_team_data': bool(context.get('team_data')),
            'has_historical_data': bool(context.get('historical_data'))
        }
    
    async def get_prediction_accuracy_metrics(self) -> Dict[str, float]:
        """Calculate accuracy metrics for predictions (placeholder for future implementation)."""
        # This would be implemented with actual feedback data
        return {
            'overall_accuracy': 0.75,
            'task_prediction_accuracy': 0.80,
            'issue_prediction_accuracy': 0.70,
            'optimization_accuracy': 0.85,
            'false_positive_rate': 0.15
        }