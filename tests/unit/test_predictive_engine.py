"""
Unit tests for the Predictive Development Assistant Engine.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from src.codegenie.core.predictive_engine import (
    DevelopmentPatternAnalyzer,
    ProactiveSuggestionEngine,
    PredictiveDevelopmentAssistant,
    DevelopmentPattern,
    VelocityMetrics,
    CollaborationPattern,
    ProjectTrend,
    PredictiveSuggestion,
    PatternType,
    PredictionType,
    ConfidenceLevel
)


class TestDevelopmentPatternAnalyzer:
    """Test cases for DevelopmentPatternAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a DevelopmentPatternAnalyzer instance."""
        return DevelopmentPatternAnalyzer()
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            'commits': [
                {
                    'timestamp': '2024-01-01T10:00:00',
                    'message': 'Add feature A',
                    'author': 'dev1'
                },
                {
                    'timestamp': '2024-01-01T14:00:00',
                    'message': 'Fix bug B',
                    'author': 'dev1'
                },
                {
                    'timestamp': '2024-01-02T09:00:00',
                    'message': 'Update tests',
                    'author': 'dev1'
                }
            ],
            'file_changes': [
                {
                    'file_path': 'src/main.py',
                    'lines_added': 50,
                    'lines_deleted': 10
                },
                {
                    'file_path': 'tests/test_main.py',
                    'lines_added': 30,
                    'lines_deleted': 5
                }
            ],
            'test_data': {
                'test_runs_per_week': 15,
                'average_coverage': 85,
                'test_types': ['unit', 'integration']
            }
        }
    
    @pytest.mark.asyncio
    async def test_analyze_workflow_patterns(self, analyzer, sample_project_data):
        """Test workflow pattern analysis."""
        patterns = await analyzer.analyze_workflow_patterns(sample_project_data)
        
        assert len(patterns) >= 1
        assert all(isinstance(p, DevelopmentPattern) for p in patterns)
        
        # Check that patterns are stored
        assert len(analyzer.patterns) >= len(patterns)
    
    @pytest.mark.asyncio
    async def test_analyze_commit_patterns(self, analyzer, sample_project_data):
        """Test commit pattern analysis."""
        commits = sample_project_data['commits']
        pattern = await analyzer._analyze_commit_patterns(commits)
        
        assert pattern is not None
        assert pattern.type == PatternType.WORKFLOW
        assert pattern.name == "Commit Timing Pattern"
        assert pattern.frequency > 0
        assert 'peak_hour' in pattern.context
        assert 'peak_day' in pattern.context
    
    @pytest.mark.asyncio
    async def test_analyze_commit_patterns_empty(self, analyzer):
        """Test commit pattern analysis with empty data."""
        pattern = await analyzer._analyze_commit_patterns([])
        assert pattern is None
    
    @pytest.mark.asyncio
    async def test_analyze_file_modification_patterns(self, analyzer, sample_project_data):
        """Test file modification pattern analysis."""
        file_changes = sample_project_data['file_changes']
        pattern = await analyzer._analyze_file_modification_patterns(file_changes)
        
        assert pattern is not None
        assert pattern.type == PatternType.CODING_STYLE
        assert pattern.name == "File Modification Pattern"
        assert 'most_common_type' in pattern.context
        assert 'avg_modification_size' in pattern.context
    
    @pytest.mark.asyncio
    async def test_analyze_testing_patterns(self, analyzer, sample_project_data):
        """Test testing pattern analysis."""
        test_data = sample_project_data['test_data']
        pattern = await analyzer._analyze_testing_patterns(test_data)
        
        assert pattern is not None
        assert pattern.type == PatternType.TESTING
        assert pattern.frequency == test_data['test_runs_per_week']
        assert 'test_frequency' in pattern.context
    
    @pytest.mark.asyncio
    async def test_analyze_testing_patterns_no_data(self, analyzer):
        """Test testing pattern analysis with no data."""
        pattern = await analyzer._analyze_testing_patterns({})
        assert pattern is None
    
    @pytest.mark.asyncio
    async def test_calculate_velocity_metrics(self, analyzer, sample_project_data):
        """Test velocity metrics calculation."""
        metrics = await analyzer.calculate_velocity_metrics(sample_project_data)
        
        assert isinstance(metrics, VelocityMetrics)
        assert metrics.commits_per_day >= 0
        assert metrics.lines_changed_per_day >= 0
        assert metrics.files_modified_per_day >= 0
        assert 0 <= metrics.build_success_rate <= 100
        assert 0 <= metrics.test_coverage_percentage <= 100
    
    @pytest.mark.asyncio
    async def test_analyze_collaboration_patterns(self, analyzer):
        """Test collaboration pattern analysis."""
        team_data = {
            'pair_programming_sessions': [{'date': '2024-01-01'}],
            'code_reviews': [
                {'participated': True, 'review_time_hours': 2},
                {'participated': False, 'review_time_hours': 0}
            ],
            'meetings': [
                {'type': 'knowledge_sharing'},
                {'type': 'standup'}
            ],
            'communications': [
                {'channel': 'slack', 'cross_team': True},
                {'channel': 'email', 'cross_team': False}
            ],
            'documentation_updates': [{'file': 'README.md'}]
        }
        
        patterns = await analyzer.analyze_collaboration_patterns(team_data)
        
        assert isinstance(patterns, CollaborationPattern)
        assert patterns.pair_programming_frequency >= 0
        assert 0 <= patterns.code_review_participation <= 100
        assert patterns.knowledge_sharing_events >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_project_trends(self, analyzer):
        """Test project trend analysis."""
        historical_data = [
            {
                'complexity_score': 5.0,
                'quality_score': 8.0,
                'velocity_score': 7.0,
                'team_size': 3,
                'technology_changes': 1,
                'refactoring_events': 2,
                'bugs_introduced': 1,
                'features_completed': 3
            },
            {
                'complexity_score': 6.0,
                'quality_score': 8.5,
                'velocity_score': 7.5,
                'team_size': 4,
                'technology_changes': 0,
                'refactoring_events': 1,
                'bugs_introduced': 2,
                'features_completed': 2
            }
        ]
        
        trends = await analyzer.analyze_project_trends(historical_data)
        
        assert isinstance(trends, ProjectTrend)
        assert trends.complexity_trend in ['increasing', 'decreasing', 'stable']
        assert trends.quality_trend in ['increasing', 'decreasing', 'stable']
        assert trends.velocity_trend in ['increasing', 'decreasing', 'stable']
        assert trends.technology_adoption_rate >= 0
    
    def test_calculate_trend_increasing(self, analyzer):
        """Test trend calculation for increasing values."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        trend = analyzer._calculate_trend(values)
        assert trend == 'increasing'
    
    def test_calculate_trend_decreasing(self, analyzer):
        """Test trend calculation for decreasing values."""
        values = [5.0, 4.0, 3.0, 2.0, 1.0]
        trend = analyzer._calculate_trend(values)
        assert trend == 'decreasing'
    
    def test_calculate_trend_stable(self, analyzer):
        """Test trend calculation for stable values."""
        values = [3.0, 3.1, 2.9, 3.0, 3.1]
        trend = analyzer._calculate_trend(values)
        assert trend == 'stable'


class TestProactiveSuggestionEngine:
    """Test cases for ProactiveSuggestionEngine."""
    
    @pytest.fixture
    def pattern_analyzer(self):
        """Create a mock pattern analyzer."""
        return Mock(spec=DevelopmentPatternAnalyzer)
    
    @pytest.fixture
    def suggestion_engine(self, pattern_analyzer):
        """Create a ProactiveSuggestionEngine instance."""
        return ProactiveSuggestionEngine(pattern_analyzer)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return {
            'current_files': ['src/main.py', 'src/utils.py'],
            'recent_changes': [
                {
                    'file_path': 'src/main.py',
                    'lines_changed': 150
                }
            ],
            'project_state': {
                'test_coverage': 65,
                'has_readme': False
            }
        }
    
    @pytest.mark.asyncio
    async def test_generate_task_recommendations(self, suggestion_engine, sample_context):
        """Test task recommendation generation."""
        suggestions = await suggestion_engine.generate_task_recommendations(sample_context)
        
        assert isinstance(suggestions, list)
        assert all(isinstance(s, PredictiveSuggestion) for s in suggestions)
        
        # Should generate suggestions based on context
        assert len(suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_based_on_file_patterns_python(self, suggestion_engine):
        """Test suggestions based on Python file patterns."""
        current_files = ['src/main.py', 'src/utils.py']
        suggestions = await suggestion_engine._suggest_based_on_file_patterns(current_files)
        
        # Should suggest adding tests for Python files
        test_suggestions = [s for s in suggestions if s.type == PredictionType.TESTING_GAP]
        assert len(test_suggestions) > 0
        assert any('test' in s.title.lower() for s in test_suggestions)
    
    @pytest.mark.asyncio
    async def test_suggest_based_on_file_patterns_javascript(self, suggestion_engine):
        """Test suggestions based on JavaScript file patterns."""
        current_files = ['src/main.js', 'src/utils.ts']
        suggestions = await suggestion_engine._suggest_based_on_file_patterns(current_files)
        
        # Should suggest package.json for JS/TS files
        package_suggestions = [s for s in suggestions if 'package' in s.title.lower()]
        assert len(package_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_based_on_change_patterns_large_changes(self, suggestion_engine):
        """Test suggestions based on large change patterns."""
        recent_changes = [
            {'lines_changed': 200},
            {'lines_changed': 150},
            {'lines_changed': 180}
        ]
        suggestions = await suggestion_engine._suggest_based_on_change_patterns(recent_changes)
        
        # Should suggest breaking down large changes
        refactor_suggestions = [s for s in suggestions if s.type == PredictionType.REFACTORING_NEED]
        assert len(refactor_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_based_on_change_patterns_security(self, suggestion_engine):
        """Test suggestions based on security-related changes."""
        recent_changes = [
            {'file_path': 'src/auth.py'},
            {'file_path': 'src/security/crypto.py'}
        ]
        suggestions = await suggestion_engine._suggest_based_on_change_patterns(recent_changes)
        
        # Should suggest security review
        security_suggestions = [s for s in suggestions if s.type == PredictionType.SECURITY_RISK]
        assert len(security_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_based_on_project_state_low_coverage(self, suggestion_engine):
        """Test suggestions based on low test coverage."""
        project_state = {'test_coverage': 50, 'has_readme': True}
        suggestions = await suggestion_engine._suggest_based_on_project_state(project_state)
        
        # Should suggest improving test coverage
        coverage_suggestions = [s for s in suggestions if 'coverage' in s.title.lower()]
        assert len(coverage_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_based_on_project_state_missing_docs(self, suggestion_engine):
        """Test suggestions based on missing documentation."""
        project_state = {'test_coverage': 80, 'has_readme': False}
        suggestions = await suggestion_engine._suggest_based_on_project_state(project_state)
        
        # Should suggest adding documentation
        doc_suggestions = [s for s in suggestions if 'documentation' in s.title.lower()]
        assert len(doc_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_detect_potential_issues_complexity(self, suggestion_engine):
        """Test detection of complexity-related issues."""
        context = {
            'complexity_trend': 'increasing',
            'performance_metrics': {'response_time_trend': 'stable'}
        }
        suggestions = await suggestion_engine.detect_potential_issues(context)
        
        # Should detect complexity issues
        complexity_issues = [s for s in suggestions if 'complexity' in s.title.lower()]
        assert len(complexity_issues) > 0
    
    @pytest.mark.asyncio
    async def test_detect_potential_issues_performance(self, suggestion_engine):
        """Test detection of performance-related issues."""
        context = {
            'complexity_trend': 'stable',
            'performance_metrics': {'response_time_trend': 'increasing'}
        }
        suggestions = await suggestion_engine.detect_potential_issues(context)
        
        # Should detect performance issues
        performance_issues = [s for s in suggestions if 'performance' in s.title.lower()]
        assert len(performance_issues) > 0
    
    @pytest.mark.asyncio
    async def test_identify_optimization_opportunities_build_time(self, suggestion_engine):
        """Test identification of build time optimization opportunities."""
        context = {
            'average_build_time_minutes': 15,
            'outdated_dependencies': 3
        }
        suggestions = await suggestion_engine.identify_optimization_opportunities(context)
        
        # Should suggest build optimization
        build_optimizations = [s for s in suggestions if 'build' in s.title.lower()]
        assert len(build_optimizations) > 0
    
    @pytest.mark.asyncio
    async def test_identify_optimization_opportunities_dependencies(self, suggestion_engine):
        """Test identification of dependency optimization opportunities."""
        context = {
            'average_build_time_minutes': 5,
            'outdated_dependencies': 10
        }
        suggestions = await suggestion_engine.identify_optimization_opportunities(context)
        
        # Should suggest dependency updates
        dep_optimizations = [s for s in suggestions if 'dependencies' in s.title.lower()]
        assert len(dep_optimizations) > 0


class TestPredictiveDevelopmentAssistant:
    """Test cases for PredictiveDevelopmentAssistant."""
    
    @pytest.fixture
    def assistant(self):
        """Create a PredictiveDevelopmentAssistant instance."""
        return PredictiveDevelopmentAssistant()
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample comprehensive project data."""
        return {
            'commits': [
                {'timestamp': '2024-01-01T10:00:00', 'message': 'Add feature'}
            ],
            'file_changes': [
                {'file_path': 'src/main.py', 'lines_added': 50, 'lines_deleted': 10}
            ],
            'test_data': {
                'test_runs_per_week': 10,
                'average_coverage': 75
            },
            'team_data': {
                'code_reviews': [{'participated': True}],
                'meetings': [{'type': 'standup'}]
            },
            'historical_data': [
                {'complexity_score': 5.0, 'quality_score': 8.0}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_analyze_development_context(self, assistant, sample_project_data):
        """Test comprehensive development context analysis."""
        analysis = await assistant.analyze_development_context(sample_project_data)
        
        assert 'patterns' in analysis
        assert 'velocity_metrics' in analysis
        assert 'collaboration_patterns' in analysis
        assert 'project_trends' in analysis
        assert 'analysis_timestamp' in analysis
        
        # Check data types
        assert isinstance(analysis['patterns'], list)
        assert isinstance(analysis['velocity_metrics'], VelocityMetrics)
        assert isinstance(analysis['collaboration_patterns'], CollaborationPattern)
        assert isinstance(analysis['project_trends'], ProjectTrend)
    
    @pytest.mark.asyncio
    async def test_generate_proactive_suggestions(self, assistant):
        """Test proactive suggestion generation."""
        context = {
            'current_files': ['src/main.py'],
            'recent_changes': [],
            'project_state': {'test_coverage': 60}
        }
        
        suggestions = await assistant.generate_proactive_suggestions(context)
        
        assert isinstance(suggestions, list)
        assert all(isinstance(s, PredictiveSuggestion) for s in suggestions)
        
        # Should be sorted by priority
        if len(suggestions) > 1:
            for i in range(len(suggestions) - 1):
                assert suggestions[i].priority >= suggestions[i + 1].priority
    
    @pytest.mark.asyncio
    async def test_get_prediction_accuracy_metrics(self, assistant):
        """Test prediction accuracy metrics."""
        metrics = await assistant.get_prediction_accuracy_metrics()
        
        assert isinstance(metrics, dict)
        assert 'overall_accuracy' in metrics
        assert 'task_prediction_accuracy' in metrics
        assert 'issue_prediction_accuracy' in metrics
        assert 'optimization_accuracy' in metrics
        assert 'false_positive_rate' in metrics
        
        # Check value ranges
        for key, value in metrics.items():
            assert 0.0 <= value <= 1.0
    
    def test_summarize_context(self, assistant):
        """Test context summarization."""
        context = {
            'current_files': ['file1.py', 'file2.py'],
            'recent_changes': [{'change': 1}],
            'project_state': {'coverage': 80},
            'team_data': {'size': 5},
            'historical_data': [{'data': 1}]
        }
        
        summary = assistant._summarize_context(context)
        
        assert isinstance(summary, dict)
        assert summary['files_analyzed'] == 2
        assert summary['recent_changes'] == 1
        assert summary['has_project_state'] is True
        assert summary['has_team_data'] is True
        assert summary['has_historical_data'] is True


class TestDataModels:
    """Test cases for data models and enums."""
    
    def test_development_pattern_creation(self):
        """Test DevelopmentPattern creation."""
        pattern = DevelopmentPattern(
            id="test_pattern",
            type=PatternType.WORKFLOW,
            name="Test Pattern",
            description="A test pattern",
            frequency=5,
            confidence=ConfidenceLevel.HIGH,
            context={'key': 'value'},
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        
        assert pattern.id == "test_pattern"
        assert pattern.type == PatternType.WORKFLOW
        assert pattern.confidence == ConfidenceLevel.HIGH
        assert isinstance(pattern.examples, list)
        assert isinstance(pattern.metadata, dict)
    
    def test_predictive_suggestion_creation(self):
        """Test PredictiveSuggestion creation."""
        suggestion = PredictiveSuggestion(
            id="test_suggestion",
            type=PredictionType.NEXT_TASK,
            title="Test Suggestion",
            description="A test suggestion",
            confidence=ConfidenceLevel.MEDIUM,
            priority=5,
            reasoning="Test reasoning",
            suggested_actions=["Action 1", "Action 2"],
            estimated_impact="Medium impact",
            estimated_effort="2 hours",
            context={'key': 'value'},
            created_at=datetime.now()
        )
        
        assert suggestion.id == "test_suggestion"
        assert suggestion.type == PredictionType.NEXT_TASK
        assert suggestion.priority == 5
        assert len(suggestion.suggested_actions) == 2
        assert suggestion.expires_at is None
    
    def test_velocity_metrics_creation(self):
        """Test VelocityMetrics creation."""
        metrics = VelocityMetrics(
            commits_per_day=2.5,
            lines_changed_per_day=150.0,
            files_modified_per_day=3.2,
            features_completed_per_week=1.5,
            bugs_fixed_per_week=2.0,
            code_review_time_hours=1.5,
            build_success_rate=95.0,
            test_coverage_percentage=85.0,
            technical_debt_ratio=5.2
        )
        
        assert metrics.commits_per_day == 2.5
        assert metrics.build_success_rate == 95.0
        assert metrics.test_coverage_percentage == 85.0
    
    def test_collaboration_pattern_creation(self):
        """Test CollaborationPattern creation."""
        pattern = CollaborationPattern(
            pair_programming_frequency=0.5,
            code_review_participation=90.0,
            knowledge_sharing_events=2,
            cross_team_interactions=5,
            communication_channels_used=['slack', 'email'],
            meeting_frequency=3.0,
            documentation_updates=4
        )
        
        assert pattern.pair_programming_frequency == 0.5
        assert pattern.code_review_participation == 90.0
        assert len(pattern.communication_channels_used) == 2
    
    def test_project_trend_creation(self):
        """Test ProjectTrend creation."""
        trend = ProjectTrend(
            complexity_trend="increasing",
            quality_trend="stable",
            velocity_trend="decreasing",
            team_size_trend="stable",
            technology_adoption_rate=0.1,
            refactoring_frequency=0.2,
            bug_introduction_rate=0.05,
            feature_completion_rate=0.8
        )
        
        assert trend.complexity_trend == "increasing"
        assert trend.quality_trend == "stable"
        assert trend.technology_adoption_rate == 0.1


if __name__ == '__main__':
    pytest.main([__file__])