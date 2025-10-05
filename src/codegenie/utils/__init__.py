"""
Utility modules for Claude Code Agent.
"""

from .code_analyzer import CodeAnalyzer
from .file_operations import FileOperations
from .project_analyzer import ProjectAnalyzer
from .testing_framework import TestingFramework
from .error_detector import ErrorDetector, DetectedError
from .error_recovery import ErrorRecovery, RecoveryAction, RecoveryResult
from .safe_executor import SafeExecutor, ExecutionContext, ExecutionResult
from .enhanced_file_ops import EnhancedFileOperations, FileOperation, FileValidationResult
from .integrated_safety import IntegratedSafetySystem, SafetyReport

__all__ = [
    "CodeAnalyzer",
    "FileOperations",
    "ProjectAnalyzer",
    "TestingFramework",
    "ErrorDetector",
    "DetectedError",
    "ErrorRecovery",
    "RecoveryAction",
    "RecoveryResult",
    "SafeExecutor",
    "ExecutionContext",
    "ExecutionResult",
    "EnhancedFileOperations",
    "FileOperation",
    "FileValidationResult",
    "IntegratedSafetySystem",
    "SafetyReport",
]
