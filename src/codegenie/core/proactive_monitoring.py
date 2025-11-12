"""
Proactive Monitoring System for continuous codebase monitoring.

This module provides:
- ProactiveAssistant class with monitoring capabilities
- CodebaseMonitor for continuous change tracking
- IssueDetector for identifying problems proactively
- SuggestionEngine for generating improvement suggestions
- WorkflowPredictor for next step anticipation
"""

import asyncio
import ast
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import hashlib


class SuggestionType(Enum):
    """Types of proactive suggestions."""
    IMPROVEMENT = "improvement"
    FIX = "fix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"


class Severity(Enum):
    """Severity levels for issues and suggestions."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueType(Enum):
    """Types of issues that can be detected."""
    CODE_SMELL = "code_smell"
    INCONSISTENCY = "inconsistency"
    MISSING_TEST = "missing_test"
    MISSING_DOC = "missing_documentation"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_ISSUE = "performance_issue"
    CONVENTION_VIOLATION = "convention_violation"
    DEPRECATED_API = "deprecated_api"


@dataclass
class ProactiveSuggestion:
    """Represents a proactive suggestion."""
    type: SuggestionType
    severity: Severity
    title: str
    description: str
    affected_files: List[Path]
    suggested_action: str
    code_snippet: Optional[str] = None
    reasoning: str = ""
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DetectedIssue:
    """Represents a detected issue in the codebase."""
    issue_type: IssueType
    severity: Severity
    file_path: Path
    line_number: Optional[int]
    description: str
    context: str
    suggested_fix: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowPrediction:
    """Prediction of next logical steps in development workflow."""
    predicted_action: str
    reasoning: str
    confidence: float
    suggested_files: List[Path]
    estimated_effort: str  # low, medium, high
    priority: int  # 1-5, 5 being highest


@dataclass
class MonitoringResult:
    """Result of codebase monitoring."""
    issues: List[DetectedIssue]
    suggestions: List[ProactiveSuggestion]
    files_monitored: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ChangeEvent:
    """Represents a change in the codebase."""
    file_path: Path
    change_type: str  # created, modified, deleted
    timestamp: datetime
    content_hash: Optional[str] = None


class CodebaseMonitor:
    """Monitors codebase for continuous change tracking."""
    
    def __init__(self, project_root: Path):
        """
        Initialize codebase monitor.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.file_hashes: Dict[Path, str] = {}
        self.last_scan: Optional[datetime] = None
        self.change_history: List[ChangeEvent] = []
        self.ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.pytest_cache', '.mypy_cache'
        ]
    
    async def start_monitoring(self) -> None:
        """Start continuous monitoring of the codebase."""
        await self._initial_scan()
        self.last_scan = datetime.now()
    
    async def _initial_scan(self) -> None:
        """Perform initial scan of all files."""
        python_files = self._find_python_files()
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                content_hash = hashlib.md5(content.encode()).hexdigest()
                self.file_hashes[file_path] = content_hash
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in project."""
        python_files = []
        
        for path in self.project_root.rglob('*.py'):
            if any(ignore in str(path) for ignore in self.ignore_patterns):
                continue
            python_files.append(path)
        
        return python_files
    
    async def detect_changes(self) -> List[ChangeEvent]:
        """
        Detect changes since last scan.
        
        Returns:
            List of change events
        """
        changes = []
        current_files = set(self._find_python_files())
        previous_files = set(self.file_hashes.keys())
        
        # Detect new files
        new_files = current_files - previous_files
        for file_path in new_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                content_hash = hashlib.md5(content.encode()).hexdigest()
                self.file_hashes[file_path] = content_hash
                
                change = ChangeEvent(
                    file_path=file_path,
                    change_type='created',
                    timestamp=datetime.now(),
                    content_hash=content_hash
                )
                changes.append(change)
                self.change_history.append(change)
            except Exception as e:
                print(f"Error reading new file {file_path}: {e}")
        
        # Detect deleted files
        deleted_files = previous_files - current_files
        for file_path in deleted_files:
            change = ChangeEvent(
                file_path=file_path,
                change_type='deleted',
                timestamp=datetime.now()
            )
            changes.append(change)
            self.change_history.append(change)
            del self.file_hashes[file_path]
        
        # Detect modified files
        for file_path in current_files & previous_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if content_hash != self.file_hashes[file_path]:
                    self.file_hashes[file_path] = content_hash
                    change = ChangeEvent(
                        file_path=file_path,
                        change_type='modified',
                        timestamp=datetime.now(),
                        content_hash=content_hash
                    )
                    changes.append(change)
                    self.change_history.append(change)
            except Exception as e:
                print(f"Error checking file {file_path}: {e}")
        
        self.last_scan = datetime.now()
        return changes
    
    def get_recent_changes(self, since: Optional[datetime] = None) -> List[ChangeEvent]:
        """
        Get recent changes since a specific time.
        
        Args:
            since: Get changes since this time (default: last hour)
            
        Returns:
            List of recent change events
        """
        if since is None:
            since = datetime.now() - timedelta(hours=1)
        
        return [change for change in self.change_history if change.timestamp >= since]
    
    def get_change_frequency(self, file_path: Path) -> int:
        """
        Get how frequently a file has been changed.
        
        Args:
            file_path: Path to file
            
        Returns:
            Number of changes to the file
        """
        return sum(1 for change in self.change_history if change.file_path == file_path)


class IssueDetector:
    """Detects issues proactively in the codebase."""
    
    def __init__(self):
        """Initialize issue detector."""
        self.detected_issues: List[DetectedIssue] = []
    
    async def detect_issues(self, file_path: Path) -> List[DetectedIssue]:
        """
        Detect issues in a file.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            List of detected issues
        """
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse AST
            tree = ast.parse(content)
            
            # Detect missing docstrings
            issues.extend(self._detect_missing_docstrings(tree, file_path, content))
            
            # Detect code smells
            issues.extend(self._detect_code_smells(tree, file_path, content))
            
            # Detect inconsistencies
            issues.extend(self._detect_inconsistencies(tree, file_path, content))
            
        except Exception as e:
            print(f"Error detecting issues in {file_path}: {e}")
        
        self.detected_issues.extend(issues)
        return issues
    
    def _detect_missing_docstrings(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[DetectedIssue]:
        """Detect functions and classes without docstrings."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    # Skip private methods (starting with _)
                    if not node.name.startswith('_'):
                        issue = DetectedIssue(
                            issue_type=IssueType.MISSING_DOC,
                            severity=Severity.WARNING,
                            file_path=file_path,
                            line_number=node.lineno,
                            description=f"{node.__class__.__name__} '{node.name}' is missing a docstring",
                            context=ast.get_source_segment(content, node) or '',
                            suggested_fix=f"Add a docstring to {node.name}",
                            confidence=0.9
                        )
                        issues.append(issue)
        
        return issues
    
    def _detect_code_smells(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[DetectedIssue]:
        """Detect common code smells."""
        issues = []
        
        for node in ast.walk(tree):
            # Long functions (> 50 lines)
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    issue = DetectedIssue(
                        issue_type=IssueType.CODE_SMELL,
                        severity=Severity.INFO,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Function '{node.name}' is too long ({func_lines} lines)",
                        context=f"Function at line {node.lineno}",
                        suggested_fix="Consider breaking this function into smaller functions",
                        confidence=0.7
                    )
                    issues.append(issue)
                
                # Too many parameters (> 5)
                if len(node.args.args) > 5:
                    issue = DetectedIssue(
                        issue_type=IssueType.CODE_SMELL,
                        severity=Severity.INFO,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                        context=f"Function at line {node.lineno}",
                        suggested_fix="Consider using a configuration object or breaking down the function",
                        confidence=0.6
                    )
                    issues.append(issue)
        
        return issues
    
    def _detect_inconsistencies(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[DetectedIssue]:
        """Detect inconsistencies in code style."""
        issues = []
        
        # Check for inconsistent naming conventions
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
        
        # Check if mixing snake_case and camelCase
        snake_case = sum(1 for name in function_names if '_' in name)
        camel_case = sum(1 for name in function_names if any(c.isupper() for c in name[1:]))
        
        if snake_case > 0 and camel_case > 0:
            issue = DetectedIssue(
                issue_type=IssueType.INCONSISTENCY,
                severity=Severity.WARNING,
                file_path=file_path,
                line_number=None,
                description="Inconsistent naming convention: mixing snake_case and camelCase",
                context=f"File has {snake_case} snake_case and {camel_case} camelCase functions",
                suggested_fix="Use consistent naming convention (prefer snake_case for Python)",
                confidence=0.8
            )
            issues.append(issue)
        
        return issues
    
    def get_issues_by_severity(self, severity: Severity) -> List[DetectedIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.detected_issues if issue.severity == severity]
    
    def get_issues_by_file(self, file_path: Path) -> List[DetectedIssue]:
        """Get all issues for a specific file."""
        return [issue for issue in self.detected_issues if issue.file_path == file_path]



class SuggestionEngine:
    """Generates improvement suggestions based on detected issues and patterns."""
    
    def __init__(self):
        """Initialize suggestion engine."""
        self.suggestions: List[ProactiveSuggestion] = []
    
    async def generate_suggestions(
        self,
        issues: List[DetectedIssue],
        context: Dict[str, Any]
    ) -> List[ProactiveSuggestion]:
        """
        Generate suggestions based on detected issues.
        
        Args:
            issues: List of detected issues
            context: Additional context about the codebase
            
        Returns:
            List of proactive suggestions
        """
        suggestions = []
        
        # Group issues by file
        issues_by_file = defaultdict(list)
        for issue in issues:
            issues_by_file[issue.file_path].append(issue)
        
        # Generate suggestions for each file
        for file_path, file_issues in issues_by_file.items():
            # Suggest documentation improvements
            doc_issues = [i for i in file_issues if i.issue_type == IssueType.MISSING_DOC]
            if doc_issues:
                suggestion = ProactiveSuggestion(
                    type=SuggestionType.DOCUMENTATION,
                    severity=Severity.WARNING,
                    title=f"Add documentation to {file_path.name}",
                    description=f"Found {len(doc_issues)} functions/classes without docstrings",
                    affected_files=[file_path],
                    suggested_action="Add docstrings to improve code documentation",
                    reasoning="Well-documented code is easier to maintain and understand",
                    confidence=0.9
                )
                suggestions.append(suggestion)
            
            # Suggest refactoring for code smells
            smell_issues = [i for i in file_issues if i.issue_type == IssueType.CODE_SMELL]
            if smell_issues:
                suggestion = ProactiveSuggestion(
                    type=SuggestionType.REFACTOR,
                    severity=Severity.INFO,
                    title=f"Refactor code in {file_path.name}",
                    description=f"Found {len(smell_issues)} code smells that could be improved",
                    affected_files=[file_path],
                    suggested_action="Refactor long functions and reduce complexity",
                    reasoning="Simpler code is easier to test and maintain",
                    confidence=0.7
                )
                suggestions.append(suggestion)
            
            # Suggest fixing inconsistencies
            inconsistency_issues = [i for i in file_issues if i.issue_type == IssueType.INCONSISTENCY]
            if inconsistency_issues:
                suggestion = ProactiveSuggestion(
                    type=SuggestionType.IMPROVEMENT,
                    severity=Severity.WARNING,
                    title=f"Fix inconsistencies in {file_path.name}",
                    description=f"Found {len(inconsistency_issues)} style inconsistencies",
                    affected_files=[file_path],
                    suggested_action="Standardize naming conventions and code style",
                    reasoning="Consistent code style improves readability",
                    confidence=0.8
                )
                suggestions.append(suggestion)
        
        self.suggestions.extend(suggestions)
        return suggestions
    
    def get_high_priority_suggestions(self) -> List[ProactiveSuggestion]:
        """Get suggestions with high severity."""
        return [
            s for s in self.suggestions
            if s.severity in [Severity.ERROR, Severity.CRITICAL]
        ]
    
    def get_suggestions_by_type(self, suggestion_type: SuggestionType) -> List[ProactiveSuggestion]:
        """Get suggestions of a specific type."""
        return [s for s in self.suggestions if s.type == suggestion_type]


class WorkflowPredictor:
    """Predicts next logical steps in development workflow."""
    
    def __init__(self):
        """Initialize workflow predictor."""
        self.predictions: List[WorkflowPrediction] = []
    
    async def predict_next_steps(
        self,
        recent_changes: List[ChangeEvent],
        context: Dict[str, Any]
    ) -> List[WorkflowPrediction]:
        """
        Predict next logical steps based on recent changes.
        
        Args:
            recent_changes: Recent changes to the codebase
            context: Additional context
            
        Returns:
            List of workflow predictions
        """
        predictions = []
        
        # Analyze recent changes
        modified_files = [c.file_path for c in recent_changes if c.change_type == 'modified']
        created_files = [c.file_path for c in recent_changes if c.change_type == 'created']
        
        # If implementation files were modified, suggest adding tests
        impl_files = [f for f in modified_files if not str(f).startswith('test')]
        if impl_files:
            prediction = WorkflowPrediction(
                predicted_action="Add or update tests for modified implementation files",
                reasoning=f"{len(impl_files)} implementation files were modified",
                confidence=0.8,
                suggested_files=[Path(str(f).replace('src/', 'tests/test_')) for f in impl_files[:3]],
                estimated_effort="medium",
                priority=4
            )
            predictions.append(prediction)
        
        # If new files were created, suggest documentation
        if created_files:
            prediction = WorkflowPrediction(
                predicted_action="Add documentation for newly created files",
                reasoning=f"{len(created_files)} new files were created",
                confidence=0.7,
                suggested_files=created_files[:3],
                estimated_effort="low",
                priority=3
            )
            predictions.append(prediction)
        
        # If many files modified, suggest running full test suite
        if len(modified_files) > 5:
            prediction = WorkflowPrediction(
                predicted_action="Run full test suite to ensure no regressions",
                reasoning=f"{len(modified_files)} files were modified",
                confidence=0.9,
                suggested_files=[],
                estimated_effort="medium",
                priority=5
            )
            predictions.append(prediction)
        
        self.predictions.extend(predictions)
        return predictions
    
    def get_high_priority_predictions(self) -> List[WorkflowPrediction]:
        """Get high priority predictions."""
        return sorted(
            [p for p in self.predictions if p.priority >= 4],
            key=lambda x: x.priority,
            reverse=True
        )


class ProactiveAssistant:
    """
    Main proactive assistant that coordinates monitoring, detection, and suggestions.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize proactive assistant.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.monitor = CodebaseMonitor(project_root)
        self.issue_detector = IssueDetector()
        self.suggestion_engine = SuggestionEngine()
        self.workflow_predictor = WorkflowPredictor()
        self.monitoring_active = False
    
    async def start(self) -> None:
        """Start the proactive assistant."""
        await self.monitor.start_monitoring()
        self.monitoring_active = True
    
    async def monitor_and_suggest(self) -> MonitoringResult:
        """
        Perform a monitoring cycle: detect changes, find issues, generate suggestions.
        
        Returns:
            MonitoringResult with issues and suggestions
        """
        # Detect changes
        changes = await self.monitor.detect_changes()
        
        # Detect issues in changed files
        all_issues = []
        changed_files = [c.file_path for c in changes if c.change_type in ['created', 'modified']]
        
        for file_path in changed_files:
            if file_path.exists():
                issues = await self.issue_detector.detect_issues(file_path)
                all_issues.extend(issues)
        
        # Generate suggestions
        context = {
            'recent_changes': changes,
            'total_files': len(self.monitor.file_hashes)
        }
        suggestions = await self.suggestion_engine.generate_suggestions(all_issues, context)
        
        # Predict next steps
        predictions = await self.workflow_predictor.predict_next_steps(changes, context)
        
        # Add predictions as suggestions
        for pred in predictions:
            suggestion = ProactiveSuggestion(
                type=SuggestionType.IMPROVEMENT,
                severity=Severity.INFO,
                title=pred.predicted_action,
                description=pred.reasoning,
                affected_files=pred.suggested_files,
                suggested_action=pred.predicted_action,
                reasoning=pred.reasoning,
                confidence=pred.confidence
            )
            suggestions.append(suggestion)
        
        return MonitoringResult(
            issues=all_issues,
            suggestions=suggestions,
            files_monitored=len(changed_files)
        )
    
    async def scan_entire_codebase(self) -> MonitoringResult:
        """
        Scan entire codebase for issues and suggestions.
        
        Returns:
            MonitoringResult with all issues and suggestions
        """
        all_issues = []
        python_files = self.monitor._find_python_files()
        
        for file_path in python_files:
            issues = await self.issue_detector.detect_issues(file_path)
            all_issues.extend(issues)
        
        # Generate suggestions
        context = {'total_files': len(python_files)}
        suggestions = await self.suggestion_engine.generate_suggestions(all_issues, context)
        
        return MonitoringResult(
            issues=all_issues,
            suggestions=suggestions,
            files_monitored=len(python_files)
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of monitoring status.
        
        Returns:
            Dictionary with monitoring summary
        """
        return {
            'monitoring_active': self.monitoring_active,
            'files_tracked': len(self.monitor.file_hashes),
            'total_issues': len(self.issue_detector.detected_issues),
            'total_suggestions': len(self.suggestion_engine.suggestions),
            'high_priority_issues': len(self.issue_detector.get_issues_by_severity(Severity.CRITICAL)),
            'last_scan': self.monitor.last_scan
        }
    
    def get_actionable_items(self) -> Dict[str, List]:
        """
        Get actionable items (high priority issues and suggestions).
        
        Returns:
            Dictionary with actionable issues and suggestions
        """
        return {
            'critical_issues': self.issue_detector.get_issues_by_severity(Severity.CRITICAL),
            'high_priority_suggestions': self.suggestion_engine.get_high_priority_suggestions(),
            'next_steps': self.workflow_predictor.get_high_priority_predictions()
        }
