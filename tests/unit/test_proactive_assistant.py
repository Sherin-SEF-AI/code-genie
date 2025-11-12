"""
Unit tests for the Proactive Development Assistant.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from src.codegenie.core.proactive_assistant import (
    ContextAwareSuggestionEngine,
    PreventiveIssueDetector,
    ContextualSuggestion,
    PreventiveAlert,
    OptimizationOpportunity,
    SuggestionCategory,
    IssueType,
    ConfidenceLevel,
    CodeContextAnalyzer,
    ProjectContextAnalyzer,
    TeamContextAnalyzer,
    WorkflowContextAnalyzer
)
from src.codegenie.core.context_engine import ContextEngine


class TestContextAwareSuggestionEngine:
    """Test cases for ContextAwareSuggestionEngine."""
    
    @pytest.fixture
    def context_engine(self):
        """Create a mock context engine."""
        return Mock(spec=ContextEngine)
    
    @pytest.fixture
    def suggestion_engine(self, context_engine):
        """Create a ContextAwareSuggestionEngine instance."""
        return ContextAwareSuggestionEngine(context_engine)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return {
            'code_files': ['src/main.py', 'src/utils.py'],
            'semantic_analysis': {
                'files': [
                    {
                        'functions': [
                            {
                                'name': 'complex_function',
                                'complexity_score': 15,
                                'line_count': 100,
                                'param_count': 8,
                                'has_error_handling': False
                            },
                            {
                                'name': 'simple_function',
                                'complexity_score': 3,
                                'line_count': 20,
                                'param_count': 2,
                                'has_error_handling': True
                            }
                        ]
                    }
                ]
            },
            'project_metrics': {
                'test_coverage': 65,
                'uncovered_lines': 150
            },
            'dependencies': [
                {
                    'name': 'requests',
                    'current_version': '2.25.0',
                    'latest_version': '2.28.0',
                    'is_outdated': True,
                    'has_security_vulnerabilities': True,
                    'is_major_update': False
                }
            ],
            'team_metrics': {
                'code_review_participation': 75,
                'unreviewed_prs': 3,
                'team_size': 5
            },
            'workflow_metrics': {
                'average_build_time_minutes': 12,
                'build_steps': 8,
                'deployment_frequency': 2
            }
        }
    
    @pytest.mark.asyncio
    async def test_generate_contextual_suggestions(self, suggestion_engine, sample_context):
        """Test contextual suggestion generation."""
        suggestions = await suggestion_engine.generate_contextual_suggestions(sample_context)
        
        assert isinstance(suggestions, list)
        assert all(isinstance(s, ContextualSuggestion) for s in suggestions)
        assert len(suggestions) <= 10  # Should be filtered to top 10
        
        # Should include various types of suggestions
        categories = {s.category for s in suggestions}
        assert len(categories) > 0
    
    @pytest.mark.asyncio
    async def test_generate_code_suggestions_complex_function(self, suggestion_engine):
        """Test code suggestions for complex functions."""
        code_context = {
            'complex_functions': [
                {
                    'name': 'very_complex_function',
                    'complexity_score': 20,
                    'line_count': 150,
                    'param_count': 10
                }
            ],
            'functions_without_error_handling': ['risky_function']
        }
        
        suggestions = await suggestion_engine._generate_code_suggestions(code_context)
        
        # Should suggest refactoring complex function
        refactor_suggestions = [s for s in suggestions if 'refactor' in s.title.lower()]
        assert len(refactor_suggestions) > 0
        
        # Should suggest adding error handling
        error_handling_suggestions = [s for s in suggestions if 'error handling' in s.title.lower()]
        assert len(error_handling_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_project_suggestions_low_coverage(self, suggestion_engine):
        """Test project suggestions for low test coverage."""
        project_context = {
            'test_coverage': 60,
            'uncovered_lines': 200,
            'outdated_dependencies': [
                {
                    'name': 'vulnerable_lib',
                    'security_risk': True,
                    'major_update': False
                }
            ]
        }
        
        suggestions = await suggestion_engine._generate_project_suggestions(project_context)
        
        # Should suggest improving test coverage
        coverage_suggestions = [s for s in suggestions if 'coverage' in s.title.lower()]
        assert len(coverage_suggestions) > 0
        
        # Should suggest updating dependencies
        dep_suggestions = [s for s in suggestions if 'dependencies' in s.title.lower()]
        assert len(dep_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_team_suggestions_low_participation(self, suggestion_engine):
        """Test team suggestions for low code review participation."""
        team_context = {
            'code_review_participation': 60,
            'unreviewed_prs': 5,
            'team_size': 8
        }
        
        suggestions = await suggestion_engine._generate_team_suggestions(team_context)
        
        # Should suggest improving code review participation
        review_suggestions = [s for s in suggestions if 'review' in s.title.lower()]
        assert len(review_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_workflow_suggestions_slow_builds(self, suggestion_engine):
        """Test workflow suggestions for slow builds."""
        workflow_context = {
            'average_build_time_minutes': 20,
            'build_steps': 12,
            'deployment_frequency': 1
        }
        
        suggestions = await suggestion_engine._generate_workflow_suggestions(workflow_context)
        
        # Should suggest build optimization
        build_suggestions = [s for s in suggestions if 'build' in s.title.lower()]
        assert len(build_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_filter_and_prioritize_suggestions(self, suggestion_engine):
        """Test suggestion filtering and prioritization."""
        suggestions = [
            ContextualSuggestion(
                id="suggestion1",
                category=SuggestionCategory.SECURITY,
                title="Security Fix",
                description="Fix security issue",
                context_factors=[],
                confidence=ConfidenceLevel.HIGH,
                priority=8,
                reasoning="Security is important",
                implementation_steps=[],
                expected_benefits=[],
                potential_risks=[],
                estimated_effort_hours=2.0
            ),
            ContextualSuggestion(
                id="suggestion2",
                category=SuggestionCategory.CODE_QUALITY,
                title="Code Quality",
                description="Improve code quality",
                context_factors=[],
                confidence=ConfidenceLevel.MEDIUM,
                priority=5,
                reasoning="Quality matters",
                implementation_steps=[],
                expected_benefits=[],
                potential_risks=[],
                estimated_effort_hours=1.0
            )
        ]
        
        context = {'project_phase': 'production', 'team_size': 3}
        filtered = await suggestion_engine._filter_and_prioritize(suggestions, context)
        
        # Should boost security suggestions in production
        security_suggestion = next(s for s in filtered if s.category == SuggestionCategory.SECURITY)
        assert security_suggestion.priority >= 8
        
        # Should be sorted by priority
        assert filtered[0].priority >= filtered[1].priority


class TestPreventiveIssueDetector:
    """Test cases for PreventiveIssueDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create a PreventiveIssueDetector instance."""
        return PreventiveIssueDetector()
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for issue detection."""
        return {
            'complexity_trend': 'increasing',
            'test_coverage_trend': 'decreasing',
            'code_duplication_percentage': 20,
            'refactoring_frequency': 0.05,
            'response_time_trend': 'increasing',
            'memory_usage_trend': 'stable',
            'database_queries_per_request': 15,
            'outdated_security_dependencies': 2,
            'insecure_code_patterns': ['sql_injection', 'xss'],
            'missing_security_headers': ['CSP', 'HSTS', 'X-Frame-Options'],
            'authentication_complexity': 'low',
            'documentation_coverage': 40,
            'team_knowledge_distribution': 0.2,
            'code_ownership_concentration': 0.9,
            'user_growth_rate_monthly': 0.3,
            'capacity_utilization': 0.8,
            'architecture_scalability_score': 0.5,
            'db_connection_pool_usage': 0.9
        }
    
    @pytest.mark.asyncio
    async def test_detect_potential_issues(self, detector, sample_context):
        """Test comprehensive issue detection."""
        alerts = await detector.detect_potential_issues(sample_context)
        
        assert isinstance(alerts, list)
        assert all(isinstance(alert, PreventiveAlert) for alert in alerts)
        
        # Should detect multiple types of issues
        issue_types = {alert.issue_type for alert in alerts}
        assert len(issue_types) > 0
    
    @pytest.mark.asyncio
    async def test_detect_technical_debt_risk(self, detector):
        """Test technical debt risk detection."""
        context = {
            'complexity_trend': 'increasing',
            'test_coverage_trend': 'decreasing',
            'code_duplication_percentage': 25,
            'refactoring_frequency': 0.02
        }
        
        alert = await detector._detect_technical_debt_risk(context)
        
        assert alert is not None
        assert alert.issue_type == IssueType.TECHNICAL_DEBT
        assert alert.likelihood > 0.5
        assert len(alert.prevention_actions) > 0
        assert len(alert.monitoring_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_detect_technical_debt_risk_low_risk(self, detector):
        """Test technical debt risk detection with low risk."""
        context = {
            'complexity_trend': 'stable',
            'test_coverage_trend': 'stable',
            'code_duplication_percentage': 5,
            'refactoring_frequency': 0.2
        }
        
        alert = await detector._detect_technical_debt_risk(context)
        
        # Should not generate alert for low risk
        assert alert is None
    
    @pytest.mark.asyncio
    async def test_detect_performance_risks(self, detector):
        """Test performance risk detection."""
        context = {
            'response_time_trend': 'increasing',
            'memory_usage_trend': 'increasing',
            'database_queries_per_request': 20
        }
        
        alert = await detector._detect_performance_risks(context)
        
        assert alert is not None
        assert alert.issue_type == IssueType.PERFORMANCE_BOTTLENECK
        assert alert.likelihood > 0.6
        assert 'performance' in alert.title.lower()
    
    @pytest.mark.asyncio
    async def test_detect_security_risks(self, detector):
        """Test security risk detection."""
        context = {
            'outdated_security_dependencies': 3,
            'insecure_code_patterns': ['sql_injection', 'xss', 'csrf'],
            'missing_security_headers': ['CSP', 'HSTS'],
            'authentication_complexity': 'low'
        }
        
        alert = await detector._detect_security_risks(context)
        
        assert alert is not None
        assert alert.issue_type == IssueType.SECURITY_VULNERABILITY
        assert alert.likelihood > 0.4
        assert 'security' in alert.title.lower()
    
    @pytest.mark.asyncio
    async def test_detect_maintainability_risks(self, detector):
        """Test maintainability risk detection."""
        context = {
            'documentation_coverage': 30,
            'team_knowledge_distribution': 0.1,
            'code_ownership_concentration': 0.95
        }
        
        alert = await detector._detect_maintainability_risks(context)
        
        assert alert is not None
        assert alert.issue_type == IssueType.MAINTAINABILITY_RISK
        assert alert.likelihood > 0.5
        assert 'maintainability' in alert.title.lower()
    
    @pytest.mark.asyncio
    async def test_detect_scalability_concerns(self, detector):
        """Test scalability concern detection."""
        context = {
            'user_growth_rate_monthly': 0.4,
            'capacity_utilization': 0.85,
            'architecture_scalability_score': 0.4,
            'db_connection_pool_usage': 0.9
        }
        
        alert = await detector._detect_scalability_concerns(context)
        
        assert alert is not None
        assert alert.issue_type == IssueType.SCALABILITY_CONCERN
        assert alert.likelihood > 0.4
        assert 'scalability' in alert.title.lower()


class TestContextAnalyzers:
    """Test cases for context analyzer classes."""
    
    @pytest.mark.asyncio
    async def test_code_context_analyzer(self):
        """Test CodeContextAnalyzer."""
        analyzer = CodeContextAnalyzer()
        
        context = {
            'semantic_analysis': {
                'files': [
                    {
                        'functions': [
                            {
                                'name': 'complex_func',
                                'complexity_score': 15,
                                'line_count': 80,
                                'param_count': 6,
                                'has_error_handling': False
                            },
                            {
                                'name': 'simple_func',
                                'complexity_score': 2,
                                'line_count': 10,
                                'param_count': 1,
                                'has_error_handling': True
                            }
                        ]
                    }
                ]
            }
        }
        
        result = await analyzer.analyze(context)
        
        assert 'complex_functions' in result
        assert 'functions_without_error_handling' in result
        assert 'total_functions' in result
        assert 'average_complexity' in result
        
        assert len(result['complex_functions']) == 1
        assert result['complex_functions'][0]['name'] == 'complex_func'
        assert 'complex_func' in result['functions_without_error_handling']
        assert result['total_functions'] == 2
    
    @pytest.mark.asyncio
    async def test_project_context_analyzer(self):
        """Test ProjectContextAnalyzer."""
        analyzer = ProjectContextAnalyzer()
        
        context = {
            'project_metrics': {
                'test_coverage': 75,
                'uncovered_lines': 100
            },
            'dependencies': [
                {
                    'name': 'lib1',
                    'is_outdated': True,
                    'has_security_vulnerabilities': True,
                    'is_major_update': False
                },
                {
                    'name': 'lib2',
                    'is_outdated': False
                }
            ]
        }
        
        result = await analyzer.analyze(context)
        
        assert result['test_coverage'] == 75
        assert result['uncovered_lines'] == 100
        assert len(result['outdated_dependencies']) == 1
        assert result['total_dependencies'] == 2
        assert result['security_risk_dependencies'] == 1
    
    @pytest.mark.asyncio
    async def test_team_context_analyzer(self):
        """Test TeamContextAnalyzer."""
        analyzer = TeamContextAnalyzer()
        
        context = {
            'team_metrics': {
                'code_review_participation': 85,
                'unreviewed_prs': 2,
                'team_size': 6,
                'knowledge_sharing_frequency': 3
            }
        }
        
        result = await analyzer.analyze(context)
        
        assert result['code_review_participation'] == 85
        assert result['unreviewed_prs'] == 2
        assert result['team_size'] == 6
        assert result['knowledge_sharing_frequency'] == 3
    
    @pytest.mark.asyncio
    async def test_workflow_context_analyzer(self):
        """Test WorkflowContextAnalyzer."""
        analyzer = WorkflowContextAnalyzer()
        
        context = {
            'workflow_metrics': {
                'average_build_time_minutes': 8,
                'build_steps': 6,
                'deployment_frequency': 4,
                'lead_time_hours': 24
            }
        }
        
        result = await analyzer.analyze(context)
        
        assert result['average_build_time_minutes'] == 8
        assert result['build_steps'] == 6
        assert result['deployment_frequency'] == 4
        assert result['lead_time_hours'] == 24


class TestDataModels:
    """Test cases for proactive assistant data models."""
    
    def test_contextual_suggestion_creation(self):
        """Test ContextualSuggestion creation."""
        suggestion = ContextualSuggestion(
            id="test_suggestion",
            category=SuggestionCategory.CODE_QUALITY,
            title="Test Suggestion",
            description="A test suggestion",
            context_factors=["factor1", "factor2"],
            confidence=ConfidenceLevel.HIGH,
            priority=8,
            reasoning="Test reasoning",
            implementation_steps=["step1", "step2"],
            expected_benefits=["benefit1"],
            potential_risks=["risk1"],
            estimated_effort_hours=3.5
        )
        
        assert suggestion.id == "test_suggestion"
        assert suggestion.category == SuggestionCategory.CODE_QUALITY
        assert suggestion.priority == 8
        assert len(suggestion.context_factors) == 2
        assert len(suggestion.implementation_steps) == 2
        assert suggestion.estimated_effort_hours == 3.5
        assert isinstance(suggestion.dependencies, list)
        assert isinstance(suggestion.created_at, datetime)
    
    def test_preventive_alert_creation(self):
        """Test PreventiveAlert creation."""
        alert = PreventiveAlert(
            id="test_alert",
            issue_type=IssueType.TECHNICAL_DEBT,
            title="Test Alert",
            description="A test alert",
            likelihood=0.75,
            potential_impact="High impact",
            time_to_manifestation=timedelta(days=30),
            prevention_actions=["action1", "action2"],
            monitoring_metrics=["metric1", "metric2"],
            context={'key': 'value'}
        )
        
        assert alert.id == "test_alert"
        assert alert.issue_type == IssueType.TECHNICAL_DEBT
        assert alert.likelihood == 0.75
        assert alert.time_to_manifestation == timedelta(days=30)
        assert len(alert.prevention_actions) == 2
        assert len(alert.monitoring_metrics) == 2
        assert isinstance(alert.created_at, datetime)
    
    def test_optimization_opportunity_creation(self):
        """Test OptimizationOpportunity creation."""
        opportunity = OptimizationOpportunity(
            id="test_opportunity",
            area="Performance",
            title="Test Optimization",
            description="A test optimization opportunity",
            current_state={'metric': 100},
            target_state={'metric': 50},
            optimization_steps=["step1", "step2"],
            expected_improvement="50% improvement",
            effort_required="Medium",
            roi_estimate=2.5
        )
        
        assert opportunity.id == "test_opportunity"
        assert opportunity.area == "Performance"
        assert opportunity.roi_estimate == 2.5
        assert len(opportunity.optimization_steps) == 2
        assert isinstance(opportunity.prerequisites, list)
    
    def test_suggestion_category_enum(self):
        """Test SuggestionCategory enum values."""
        categories = list(SuggestionCategory)
        
        assert SuggestionCategory.CODE_QUALITY in categories
        assert SuggestionCategory.PERFORMANCE in categories
        assert SuggestionCategory.SECURITY in categories
        assert SuggestionCategory.TESTING in categories
        assert SuggestionCategory.DOCUMENTATION in categories
        assert SuggestionCategory.ARCHITECTURE in categories
        assert SuggestionCategory.WORKFLOW in categories
        assert SuggestionCategory.MAINTENANCE in categories
    
    def test_issue_type_enum(self):
        """Test IssueType enum values."""
        issue_types = list(IssueType)
        
        assert IssueType.TECHNICAL_DEBT in issue_types
        assert IssueType.PERFORMANCE_BOTTLENECK in issue_types
        assert IssueType.SECURITY_VULNERABILITY in issue_types
        assert IssueType.MAINTAINABILITY_RISK in issue_types
        assert IssueType.SCALABILITY_CONCERN in issue_types
        assert IssueType.DEPENDENCY_RISK in issue_types
        assert IssueType.QUALITY_DEGRADATION in issue_types


if __name__ == '__main__':
    pytest.main([__file__])