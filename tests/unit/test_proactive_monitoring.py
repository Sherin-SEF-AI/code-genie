"""
Unit tests for Proactive Monitoring System.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.codegenie.core.proactive_monitoring import (
    ProactiveAssistant,
    CodebaseMonitor,
    IssueDetector,
    SuggestionEngine,
    WorkflowPredictor,
    ProactiveSuggestion,
    DetectedIssue,
    WorkflowPrediction,
    MonitoringResult,
    ChangeEvent,
    SuggestionType,
    Severity,
    IssueType
)


class TestCodebaseMonitor:
    """Test cases for CodebaseMonitor."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Create some Python files
        (project_root / "main.py").write_text("def main():\n    pass\n")
        (project_root / "utils.py").write_text("def helper():\n    return True\n")
        
        return project_root
    
    @pytest.fixture
    def monitor(self, temp_project):
        """Create a CodebaseMonitor instance."""
        return CodebaseMonitor(temp_project)
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor, temp_project):
        """Test starting monitoring."""
        await monitor.start_monitoring()
        
        assert monitor.last_scan is not None
        assert len(monitor.file_hashes) > 0
        assert (temp_project / "main.py") in monitor.file_hashes
    
    @pytest.mark.asyncio
    async def test_detect_new_file(self, monitor, temp_project):
        """Test detecting new files."""
        await monitor.start_monitoring()
        
        # Create a new file
        new_file = temp_project / "new_module.py"
        new_file.write_text("def new_function():\n    pass\n")
        
        changes = await monitor.detect_changes()
        
        assert len(changes) > 0
        new_file_changes = [c for c in changes if c.file_path == new_file]
        assert len(new_file_changes) == 1
        assert new_file_changes[0].change_type == 'created'
    
    @pytest.mark.asyncio
    async def test_detect_modified_file(self, monitor, temp_project):
        """Test detecting modified files."""
        await monitor.start_monitoring()
        
        # Modify a file
        main_file = temp_project / "main.py"
        main_file.write_text("def main():\n    print('modified')\n")
        
        changes = await monitor.detect_changes()
        
        modified_changes = [c for c in changes if c.file_path == main_file]
        assert len(modified_changes) == 1
        assert modified_changes[0].change_type == 'modified'
    
    @pytest.mark.asyncio
    async def test_detect_deleted_file(self, monitor, temp_project):
        """Test detecting deleted files."""
        await monitor.start_monitoring()
        
        # Delete a file
        utils_file = temp_project / "utils.py"
        utils_file.unlink()
        
        changes = await monitor.detect_changes()
        
        deleted_changes = [c for c in changes if c.file_path == utils_file]
        assert len(deleted_changes) == 1
        assert deleted_changes[0].change_type == 'deleted'
    
    def test_get_recent_changes(self, monitor):
        """Test getting recent changes."""
        # Add some changes to history
        now = datetime.now()
        monitor.change_history = [
            ChangeEvent(Path("file1.py"), "modified", now - timedelta(minutes=30)),
            ChangeEvent(Path("file2.py"), "created", now - timedelta(hours=2)),
            ChangeEvent(Path("file3.py"), "modified", now - timedelta(minutes=10))
        ]
        
        recent = monitor.get_recent_changes(since=now - timedelta(hours=1))
        
        assert len(recent) == 2  # Only changes within last hour
    
    def test_get_change_frequency(self, monitor):
        """Test getting change frequency for a file."""
        file_path = Path("test.py")
        monitor.change_history = [
            ChangeEvent(file_path, "modified", datetime.now()),
            ChangeEvent(file_path, "modified", datetime.now()),
            ChangeEvent(Path("other.py"), "modified", datetime.now())
        ]
        
        frequency = monitor.get_change_frequency(file_path)
        
        assert frequency == 2


class TestIssueDetector:
    """Test cases for IssueDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create an IssueDetector instance."""
        return IssueDetector()
    
    @pytest.fixture
    def temp_file_with_issues(self, tmp_path):
        """Create a temporary file with various issues."""
        file_path = tmp_path / "problematic.py"
        content = '''
def long_function_without_docstring(param1, param2, param3, param4, param5, param6):
    result = 0
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result += i + j + k
    return result

class UndocumentedClass:
    def method_one(self):
        pass
    
    def methodTwo(self):
        pass
'''
        file_path.write_text(content)
        return file_path
    
    @pytest.mark.asyncio
    async def test_detect_missing_docstrings(self, detector, temp_file_with_issues):
        """Test detection of missing docstrings."""
        issues = await detector.detect_issues(temp_file_with_issues)
        
        doc_issues = [i for i in issues if i.issue_type == IssueType.MISSING_DOC]
        assert len(doc_issues) > 0
    
    @pytest.mark.asyncio
    async def test_detect_code_smells(self, detector, temp_file_with_issues):
        """Test detection of code smells."""
        issues = await detector.detect_issues(temp_file_with_issues)
        
        smell_issues = [i for i in issues if i.issue_type == IssueType.CODE_SMELL]
        assert len(smell_issues) > 0
        
        # Should detect long function
        long_func_issues = [i for i in smell_issues if 'too long' in i.description.lower()]
        assert len(long_func_issues) > 0
        
        # Should detect too many parameters
        param_issues = [i for i in smell_issues if 'too many parameters' in i.description.lower()]
        assert len(param_issues) > 0
    
    @pytest.mark.asyncio
    async def test_detect_inconsistencies(self, detector, temp_file_with_issues):
        """Test detection of naming inconsistencies."""
        issues = await detector.detect_issues(temp_file_with_issues)
        
        inconsistency_issues = [i for i in issues if i.issue_type == IssueType.INCONSISTENCY]
        # Should detect mixing of snake_case and camelCase
        assert len(inconsistency_issues) > 0
    
    def test_get_issues_by_severity(self, detector):
        """Test filtering issues by severity."""
        detector.detected_issues = [
            DetectedIssue(
                IssueType.CODE_SMELL, Severity.WARNING,
                Path("test.py"), 1, "Test issue", "context"
            ),
            DetectedIssue(
                IssueType.MISSING_DOC, Severity.INFO,
                Path("test.py"), 2, "Missing doc", "context"
            )
        ]
        
        warnings = detector.get_issues_by_severity(Severity.WARNING)
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING


class TestSuggestionEngine:
    """Test cases for SuggestionEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create a SuggestionEngine instance."""
        return SuggestionEngine()
    
    @pytest.fixture
    def sample_issues(self):
        """Create sample issues for testing."""
        return [
            DetectedIssue(
                IssueType.MISSING_DOC, Severity.WARNING,
                Path("module.py"), 10, "Missing docstring", "def func():"
            ),
            DetectedIssue(
                IssueType.CODE_SMELL, Severity.INFO,
                Path("module.py"), 20, "Long function", "def long_func():"
            ),
            DetectedIssue(
                IssueType.INCONSISTENCY, Severity.WARNING,
                Path("module.py"), 30, "Naming inconsistency", "def mixedCase():"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_generate_suggestions(self, engine, sample_issues):
        """Test suggestion generation from issues."""
        context = {'total_files': 10}
        suggestions = await engine.generate_suggestions(sample_issues, context)
        
        assert len(suggestions) > 0
        assert all(isinstance(s, ProactiveSuggestion) for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_documentation_suggestions(self, engine):
        """Test documentation suggestions."""
        issues = [
            DetectedIssue(
                IssueType.MISSING_DOC, Severity.WARNING,
                Path("test.py"), 1, "Missing docstring", "context"
            )
        ]
        
        suggestions = await engine.generate_suggestions(issues, {})
        
        doc_suggestions = [s for s in suggestions if s.type == SuggestionType.DOCUMENTATION]
        assert len(doc_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_refactoring_suggestions(self, engine):
        """Test refactoring suggestions."""
        issues = [
            DetectedIssue(
                IssueType.CODE_SMELL, Severity.INFO,
                Path("test.py"), 1, "Code smell", "context"
            )
        ]
        
        suggestions = await engine.generate_suggestions(issues, {})
        
        refactor_suggestions = [s for s in suggestions if s.type == SuggestionType.REFACTOR]
        assert len(refactor_suggestions) > 0
    
    def test_get_high_priority_suggestions(self, engine):
        """Test filtering high priority suggestions."""
        engine.suggestions = [
            ProactiveSuggestion(
                SuggestionType.IMPROVEMENT, Severity.ERROR,
                "High priority", "Description", [Path("test.py")],
                "Action", confidence=0.9
            ),
            ProactiveSuggestion(
                SuggestionType.IMPROVEMENT, Severity.INFO,
                "Low priority", "Description", [Path("test.py")],
                "Action", confidence=0.5
            )
        ]
        
        high_priority = engine.get_high_priority_suggestions()
        assert len(high_priority) == 1
        assert high_priority[0].severity == Severity.ERROR


class TestWorkflowPredictor:
    """Test cases for WorkflowPredictor."""
    
    @pytest.fixture
    def predictor(self):
        """Create a WorkflowPredictor instance."""
        return WorkflowPredictor()
    
    @pytest.fixture
    def sample_changes(self):
        """Create sample changes for testing."""
        return [
            ChangeEvent(Path("src/module.py"), "modified", datetime.now()),
            ChangeEvent(Path("src/utils.py"), "modified", datetime.now()),
            ChangeEvent(Path("src/new_feature.py"), "created", datetime.now())
        ]
    
    @pytest.mark.asyncio
    async def test_predict_test_needs(self, predictor, sample_changes):
        """Test prediction of test needs."""
        predictions = await predictor.predict_next_steps(sample_changes, {})
        
        test_predictions = [p for p in predictions if 'test' in p.predicted_action.lower()]
        assert len(test_predictions) > 0
    
    @pytest.mark.asyncio
    async def test_predict_documentation_needs(self, predictor):
        """Test prediction of documentation needs."""
        changes = [
            ChangeEvent(Path("new_module.py"), "created", datetime.now())
        ]
        
        predictions = await predictor.predict_next_steps(changes, {})
        
        doc_predictions = [p for p in predictions if 'documentation' in p.predicted_action.lower()]
        assert len(doc_predictions) > 0
    
    @pytest.mark.asyncio
    async def test_predict_full_test_suite(self, predictor):
        """Test prediction for running full test suite."""
        # Many modified files should trigger full test suite suggestion
        changes = [
            ChangeEvent(Path(f"file{i}.py"), "modified", datetime.now())
            for i in range(10)
        ]
        
        predictions = await predictor.predict_next_steps(changes, {})
        
        test_suite_predictions = [p for p in predictions if 'full test suite' in p.predicted_action.lower()]
        assert len(test_suite_predictions) > 0
    
    def test_get_high_priority_predictions(self, predictor):
        """Test filtering high priority predictions."""
        predictor.predictions = [
            WorkflowPrediction(
                "High priority action", "Reasoning", 0.9,
                [], "medium", 5
            ),
            WorkflowPrediction(
                "Low priority action", "Reasoning", 0.5,
                [], "low", 2
            )
        ]
        
        high_priority = predictor.get_high_priority_predictions()
        assert len(high_priority) == 1
        assert high_priority[0].priority == 5


class TestProactiveAssistant:
    """Test cases for ProactiveAssistant."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Create Python files with issues
        (project_root / "main.py").write_text('''
def function_without_docstring():
    pass

class ClassWithoutDocstring:
    pass
''')
        
        return project_root
    
    @pytest.fixture
    def assistant(self, temp_project):
        """Create a ProactiveAssistant instance."""
        return ProactiveAssistant(temp_project)
    
    @pytest.mark.asyncio
    async def test_start_assistant(self, assistant):
        """Test starting the proactive assistant."""
        await assistant.start()
        
        assert assistant.monitoring_active is True
        assert assistant.monitor.last_scan is not None
    
    @pytest.mark.asyncio
    async def test_monitor_and_suggest(self, assistant, temp_project):
        """Test monitoring and suggestion cycle."""
        await assistant.start()
        
        # Modify a file
        main_file = temp_project / "main.py"
        main_file.write_text('''
def new_function():
    pass
''')
        
        result = await assistant.monitor_and_suggest()
        
        assert isinstance(result, MonitoringResult)
        assert result.files_monitored >= 0
        assert isinstance(result.issues, list)
        assert isinstance(result.suggestions, list)
    
    @pytest.mark.asyncio
    async def test_scan_entire_codebase(self, assistant):
        """Test scanning entire codebase."""
        result = await assistant.scan_entire_codebase()
        
        assert isinstance(result, MonitoringResult)
        assert result.files_monitored > 0
        assert len(result.issues) > 0  # Should find missing docstrings
        assert len(result.suggestions) > 0
    
    def test_get_summary(self, assistant):
        """Test getting monitoring summary."""
        assistant.monitoring_active = True
        assistant.monitor.file_hashes = {Path("test.py"): "hash"}
        
        summary = assistant.get_summary()
        
        assert 'monitoring_active' in summary
        assert summary['monitoring_active'] is True
        assert 'files_tracked' in summary
        assert summary['files_tracked'] == 1
    
    def test_get_actionable_items(self, assistant):
        """Test getting actionable items."""
        # Add some test data
        assistant.issue_detector.detected_issues = [
            DetectedIssue(
                IssueType.CODE_SMELL, Severity.CRITICAL,
                Path("test.py"), 1, "Critical issue", "context"
            )
        ]
        
        actionable = assistant.get_actionable_items()
        
        assert 'critical_issues' in actionable
        assert 'high_priority_suggestions' in actionable
        assert 'next_steps' in actionable


class TestDataModels:
    """Test cases for data models."""
    
    def test_proactive_suggestion_creation(self):
        """Test ProactiveSuggestion creation."""
        suggestion = ProactiveSuggestion(
            type=SuggestionType.IMPROVEMENT,
            severity=Severity.WARNING,
            title="Test Suggestion",
            description="Description",
            affected_files=[Path("test.py")],
            suggested_action="Do something",
            reasoning="Because reasons",
            confidence=0.8
        )
        
        assert suggestion.type == SuggestionType.IMPROVEMENT
        assert suggestion.severity == Severity.WARNING
        assert len(suggestion.affected_files) == 1
        assert suggestion.confidence == 0.8
        assert isinstance(suggestion.timestamp, datetime)
    
    def test_detected_issue_creation(self):
        """Test DetectedIssue creation."""
        issue = DetectedIssue(
            issue_type=IssueType.CODE_SMELL,
            severity=Severity.WARNING,
            file_path=Path("test.py"),
            line_number=10,
            description="Code smell detected",
            context="def bad_function():",
            suggested_fix="Refactor this",
            confidence=0.7
        )
        
        assert issue.issue_type == IssueType.CODE_SMELL
        assert issue.line_number == 10
        assert issue.confidence == 0.7
        assert isinstance(issue.timestamp, datetime)
    
    def test_workflow_prediction_creation(self):
        """Test WorkflowPrediction creation."""
        prediction = WorkflowPrediction(
            predicted_action="Run tests",
            reasoning="Files were modified",
            confidence=0.9,
            suggested_files=[Path("test_module.py")],
            estimated_effort="medium",
            priority=4
        )
        
        assert prediction.predicted_action == "Run tests"
        assert prediction.confidence == 0.9
        assert prediction.priority == 4
        assert len(prediction.suggested_files) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
