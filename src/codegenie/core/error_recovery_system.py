"""
Error Recovery System for intelligent error analysis and automatic fixes.

This module implements the ErrorRecoverySystem that analyzes errors,
suggests fixes, and attempts automatic recovery with learning capabilities.
"""

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be recovered."""
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    NAME_ERROR = "name_error"
    TYPE_ERROR = "type_error"
    ATTRIBUTE_ERROR = "attribute_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    COMMAND_ERROR = "command_error"
    DEPENDENCY_ERROR = "dependency_error"
    INDENTATION_ERROR = "indentation_error"
    RUNTIME_ERROR = "runtime_error"
    UNKNOWN = "unknown"


class FixConfidence(Enum):
    """Confidence level for automatic fixes."""
    HIGH = "high"  # 90%+ confidence, auto-apply
    MEDIUM = "medium"  # 60-90% confidence, suggest
    LOW = "low"  # <60% confidence, show as option


@dataclass
class ErrorContext:
    """Context information about an error."""
    error_type: ErrorType
    message: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code_snippet: Optional[str] = None
    stack_trace: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixSuggestion:
    """A suggested fix for an error."""
    description: str
    fix_type: str  # "code_change", "command", "install", "config"
    confidence: FixConfidence
    code_changes: Optional[Dict[str, str]] = None  # file_path -> new_content
    commands: Optional[List[str]] = None
    explanation: Optional[str] = None
    estimated_time: Optional[int] = None  # seconds
    requires_approval: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixResult:
    """Result of applying a fix."""
    success: bool
    suggestion: FixSuggestion
    output: Optional[str] = None
    error_message: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class ErrorRecoverySystem:
    """
    Intelligent error recovery system that analyzes errors,
    suggests fixes, and attempts automatic recovery.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the error recovery system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.fix_history: List[FixResult] = []
        self.learned_patterns: Dict[str, List[FixSuggestion]] = {}
        self.auto_fix_enabled = self.config.get("auto_fix_enabled", True)
        self.max_auto_fix_attempts = self.config.get("max_auto_fix_attempts", 3)
        
        # Load learned patterns from disk if available
        self._load_learned_patterns()
    
    def analyze_error(
        self,
        error_message: str,
        file_path: Optional[Path] = None,
        code_context: Optional[str] = None,
        **kwargs
    ) -> ErrorContext:
        """
        Analyze an error and extract context information.
        
        Args:
            error_message: The error message
            file_path: Path to the file where error occurred
            code_context: Code snippet around the error
            **kwargs: Additional context information
        
        Returns:
            ErrorContext with analyzed information
        """
        logger.info(f"Analyzing error: {error_message[:100]}...")
        
        # Detect error type
        error_type = self._detect_error_type(error_message)
        
        # Extract line and column numbers
        line_number, column_number = self._extract_location(error_message)
        
        # Extract stack trace if present
        stack_trace = kwargs.get("stack_trace")
        
        # Detect language and framework
        language = self._detect_language(file_path, error_message)
        framework = self._detect_framework(file_path, error_message)
        
        context = ErrorContext(
            error_type=error_type,
            message=error_message,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_context,
            stack_trace=stack_trace,
            language=language,
            framework=framework,
            additional_info=kwargs
        )
        
        logger.debug(f"Error analysis complete: type={error_type.value}, language={language}")
        return context
    
    def generate_fix_suggestions(
        self,
        error_context: ErrorContext,
        max_suggestions: int = 5
    ) -> List[FixSuggestion]:
        """
        Generate fix suggestions for an error.
        
        Args:
            error_context: Context about the error
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of fix suggestions ordered by confidence
        """
        logger.info(f"Generating fix suggestions for {error_context.error_type.value}")
        
        suggestions = []
        
        # Check learned patterns first
        learned_fixes = self._get_learned_fixes(error_context)
        suggestions.extend(learned_fixes)
        
        # Generate type-specific fixes
        type_specific_fixes = self._generate_type_specific_fixes(error_context)
        suggestions.extend(type_specific_fixes)
        
        # Sort by confidence and limit
        suggestions.sort(key=lambda s: (s.confidence.value, s.estimated_time or 0), reverse=True)
        suggestions = suggestions[:max_suggestions]
        
        logger.info(f"Generated {len(suggestions)} fix suggestions")
        return suggestions
    
    def apply_automatic_fix(
        self,
        error_context: ErrorContext,
        suggestion: Optional[FixSuggestion] = None
    ) -> FixResult:
        """
        Attempt to automatically fix an error.
        
        Args:
            error_context: Context about the error
            suggestion: Specific suggestion to apply (or auto-select best)
        
        Returns:
            Result of the fix attempt
        """
        if not self.auto_fix_enabled:
            return FixResult(
                success=False,
                suggestion=suggestion or FixSuggestion(
                    description="Auto-fix disabled",
                    fix_type="none",
                    confidence=FixConfidence.LOW
                ),
                error_message="Automatic fixes are disabled"
            )
        
        # Get suggestion if not provided
        if suggestion is None:
            suggestions = self.generate_fix_suggestions(error_context, max_suggestions=1)
            if not suggestions:
                return FixResult(
                    success=False,
                    suggestion=FixSuggestion(
                        description="No fix available",
                        fix_type="none",
                        confidence=FixConfidence.LOW
                    ),
                    error_message="No automatic fix suggestions available"
                )
            suggestion = suggestions[0]
        
        # Only auto-apply high confidence fixes
        if suggestion.confidence != FixConfidence.HIGH:
            return FixResult(
                success=False,
                suggestion=suggestion,
                error_message=f"Fix confidence too low for automatic application: {suggestion.confidence.value}"
            )
        
        logger.info(f"Applying automatic fix: {suggestion.description}")
        
        # Apply the fix based on type
        start_time = datetime.now()
        
        try:
            if suggestion.fix_type == "code_change":
                result = self._apply_code_changes(suggestion, error_context)
            elif suggestion.fix_type == "command":
                result = self._apply_command_fix(suggestion, error_context)
            elif suggestion.fix_type == "install":
                result = self._apply_install_fix(suggestion, error_context)
            elif suggestion.fix_type == "config":
                result = self._apply_config_fix(suggestion, error_context)
            else:
                result = FixResult(
                    success=False,
                    suggestion=suggestion,
                    error_message=f"Unknown fix type: {suggestion.fix_type}"
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            result.duration = duration
            
            # Record in history
            self.fix_history.append(result)
            
            # Learn from successful fixes
            if result.success:
                self._learn_from_fix(error_context, suggestion)
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            return FixResult(
                success=False,
                suggestion=suggestion,
                error_message=str(e),
                duration=duration
            )
    
    def _detect_error_type(self, error_message: str) -> ErrorType:
        """Detect the type of error from the message."""
        message_lower = error_message.lower()
        
        if "syntaxerror" in message_lower or "syntax error" in message_lower:
            return ErrorType.SYNTAX_ERROR
        elif "importerror" in message_lower or "modulenotfounderror" in message_lower:
            return ErrorType.IMPORT_ERROR
        elif "nameerror" in message_lower or "name" in message_lower and "not defined" in message_lower:
            return ErrorType.NAME_ERROR
        elif "typeerror" in message_lower or "type error" in message_lower:
            return ErrorType.TYPE_ERROR
        elif "attributeerror" in message_lower or "attribute error" in message_lower:
            return ErrorType.ATTRIBUTE_ERROR
        elif "filenotfounderror" in message_lower or "no such file" in message_lower:
            return ErrorType.FILE_NOT_FOUND
        elif "permissionerror" in message_lower or "permission denied" in message_lower:
            return ErrorType.PERMISSION_ERROR
        elif "command not found" in message_lower or "command failed" in message_lower:
            return ErrorType.COMMAND_ERROR
        elif "indentationerror" in message_lower or "indentation" in message_lower:
            return ErrorType.INDENTATION_ERROR
        elif "dependency" in message_lower or "package" in message_lower:
            return ErrorType.DEPENDENCY_ERROR
        else:
            return ErrorType.UNKNOWN
    
    def _extract_location(self, error_message: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract line and column numbers from error message."""
        line_number = None
        column_number = None
        
        # Try to find line number
        line_match = re.search(r'line (\d+)', error_message, re.IGNORECASE)
        if line_match:
            line_number = int(line_match.group(1))
        
        # Try to find column number
        col_match = re.search(r'column (\d+)', error_message, re.IGNORECASE)
        if col_match:
            column_number = int(col_match.group(1))
        
        return line_number, column_number
    
    def _detect_language(self, file_path: Optional[Path], error_message: str) -> Optional[str]:
        """Detect programming language from file path or error message."""
        if file_path:
            suffix = file_path.suffix.lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.go': 'go',
                '.rs': 'rust',
                '.java': 'java',
                '.cpp': 'cpp',
                '.c': 'c',
            }
            return language_map.get(suffix)
        
        # Try to detect from error message
        if 'python' in error_message.lower() or 'traceback' in error_message.lower():
            return 'python'
        elif 'javascript' in error_message.lower() or 'node' in error_message.lower():
            return 'javascript'
        
        return None
    
    def _detect_framework(self, file_path: Optional[Path], error_message: str) -> Optional[str]:
        """Detect framework from context."""
        message_lower = error_message.lower()
        
        frameworks = ['django', 'flask', 'fastapi', 'react', 'vue', 'angular', 'express']
        for framework in frameworks:
            if framework in message_lower:
                return framework
        
        return None
    
    def _generate_type_specific_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Generate fixes specific to the error type."""
        fixes = []
        
        if error_context.error_type == ErrorType.IMPORT_ERROR:
            fixes.extend(self._generate_import_error_fixes(error_context))
        elif error_context.error_type == ErrorType.SYNTAX_ERROR:
            fixes.extend(self._generate_syntax_error_fixes(error_context))
        elif error_context.error_type == ErrorType.NAME_ERROR:
            fixes.extend(self._generate_name_error_fixes(error_context))
        elif error_context.error_type == ErrorType.INDENTATION_ERROR:
            fixes.extend(self._generate_indentation_error_fixes(error_context))
        elif error_context.error_type == ErrorType.FILE_NOT_FOUND:
            fixes.extend(self._generate_file_not_found_fixes(error_context))
        elif error_context.error_type == ErrorType.DEPENDENCY_ERROR:
            fixes.extend(self._generate_dependency_error_fixes(error_context))
        
        return fixes

    
    def _generate_import_error_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Generate fixes for import errors."""
        fixes = []
        
        # Extract package name
        package_name = self._extract_package_name(error_context.message)
        
        if package_name:
            # Suggest installing the package
            if error_context.language == 'python':
                fixes.append(FixSuggestion(
                    description=f"Install missing Python package: {package_name}",
                    fix_type="install",
                    confidence=FixConfidence.HIGH,
                    commands=[f"pip install {package_name}"],
                    explanation=f"The module '{package_name}' is not installed. Installing it should resolve the import error.",
                    estimated_time=30,
                    requires_approval=True
                ))
            elif error_context.language in ['javascript', 'typescript']:
                fixes.append(FixSuggestion(
                    description=f"Install missing npm package: {package_name}",
                    fix_type="install",
                    confidence=FixConfidence.HIGH,
                    commands=[f"npm install {package_name}"],
                    explanation=f"The module '{package_name}' is not installed. Installing it should resolve the import error.",
                    estimated_time=30,
                    requires_approval=True
                ))
        
        return fixes
    
    def _generate_syntax_error_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Generate fixes for syntax errors."""
        fixes = []
        
        if error_context.code_snippet and error_context.file_path:
            # Check for common syntax issues
            if ":" in error_context.message and "expected" in error_context.message.lower():
                fixes.append(FixSuggestion(
                    description="Add missing colon",
                    fix_type="code_change",
                    confidence=FixConfidence.MEDIUM,
                    explanation="The line appears to be missing a colon at the end.",
                    estimated_time=5,
                    requires_approval=True
                ))
            
            if "parenthes" in error_context.message.lower():
                fixes.append(FixSuggestion(
                    description="Fix parentheses mismatch",
                    fix_type="code_change",
                    confidence=FixConfidence.MEDIUM,
                    explanation="There appears to be a mismatch in parentheses.",
                    estimated_time=5,
                    requires_approval=True
                ))
        
        return fixes
    
    def _generate_name_error_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Generate fixes for name errors."""
        fixes = []
        
        # Extract undefined name
        match = re.search(r"name '([^']+)' is not defined", error_context.message)
        if match and error_context.file_path:
            undefined_name = match.group(1)
            
            fixes.append(FixSuggestion(
                description=f"Add import for '{undefined_name}'",
                fix_type="code_change",
                confidence=FixConfidence.MEDIUM,
                explanation=f"The name '{undefined_name}' is not defined. It may need to be imported.",
                estimated_time=5,
                requires_approval=True,
                metadata={"undefined_name": undefined_name}
            ))
        
        return fixes
    
    def _generate_indentation_error_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Generate fixes for indentation errors."""
        fixes = []
        
        if error_context.file_path and error_context.language == 'python':
            fixes.append(FixSuggestion(
                description="Auto-format file with black",
                fix_type="command",
                confidence=FixConfidence.HIGH,
                commands=[f"black {error_context.file_path}"],
                explanation="Use black to automatically fix indentation issues.",
                estimated_time=10,
                requires_approval=True
            ))
            
            fixes.append(FixSuggestion(
                description="Auto-format file with autopep8",
                fix_type="command",
                confidence=FixConfidence.HIGH,
                commands=[f"autopep8 --in-place {error_context.file_path}"],
                explanation="Use autopep8 to automatically fix indentation issues.",
                estimated_time=10,
                requires_approval=True
            ))
        
        return fixes
    
    def _generate_file_not_found_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Generate fixes for file not found errors."""
        fixes = []
        
        # Extract file path from error
        file_match = re.search(r"['\"]([^'\"]+)['\"]", error_context.message)
        if file_match:
            missing_file = file_match.group(1)
            
            fixes.append(FixSuggestion(
                description=f"Create missing file: {missing_file}",
                fix_type="code_change",
                confidence=FixConfidence.MEDIUM,
                explanation=f"Create the missing file '{missing_file}'.",
                estimated_time=5,
                requires_approval=True,
                metadata={"missing_file": missing_file}
            ))
        
        return fixes
    
    def _generate_dependency_error_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Generate fixes for dependency errors."""
        fixes = []
        
        if error_context.language == 'python':
            fixes.append(FixSuggestion(
                description="Update dependencies with pip",
                fix_type="command",
                confidence=FixConfidence.MEDIUM,
                commands=["pip install -r requirements.txt"],
                explanation="Update all dependencies from requirements.txt",
                estimated_time=60,
                requires_approval=True
            ))
        elif error_context.language in ['javascript', 'typescript']:
            fixes.append(FixSuggestion(
                description="Update dependencies with npm",
                fix_type="command",
                confidence=FixConfidence.MEDIUM,
                commands=["npm install"],
                explanation="Update all dependencies from package.json",
                estimated_time=60,
                requires_approval=True
            ))
        
        return fixes
    
    def _extract_package_name(self, error_message: str) -> Optional[str]:
        """Extract package name from error message."""
        # Python import errors
        match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_message, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # JavaScript module errors
        match = re.search(r"Cannot find module ['\"]([^'\"]+)['\"]", error_message, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _apply_code_changes(self, suggestion: FixSuggestion, error_context: ErrorContext) -> FixResult:
        """Apply code changes from a fix suggestion."""
        if not suggestion.code_changes:
            return FixResult(
                success=False,
                suggestion=suggestion,
                error_message="No code changes specified"
            )
        
        try:
            for file_path, new_content in suggestion.code_changes.items():
                path = Path(file_path)
                
                # Create backup
                if path.exists():
                    backup_path = path.with_suffix(path.suffix + '.backup')
                    path.rename(backup_path)
                
                # Write new content
                path.write_text(new_content)
            
            return FixResult(
                success=True,
                suggestion=suggestion,
                output=f"Applied code changes to {len(suggestion.code_changes)} file(s)"
            )
        except Exception as e:
            return FixResult(
                success=False,
                suggestion=suggestion,
                error_message=str(e)
            )
    
    def _apply_command_fix(self, suggestion: FixSuggestion, error_context: ErrorContext) -> FixResult:
        """Apply a command-based fix."""
        if not suggestion.commands:
            return FixResult(
                success=False,
                suggestion=suggestion,
                error_message="No commands specified"
            )
        
        outputs = []
        for command in suggestion.commands:
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                outputs.append(result.stdout + result.stderr)
                
                if result.returncode != 0:
                    return FixResult(
                        success=False,
                        suggestion=suggestion,
                        output="\n".join(outputs),
                        error_message=f"Command failed with exit code {result.returncode}"
                    )
            except subprocess.TimeoutExpired:
                return FixResult(
                    success=False,
                    suggestion=suggestion,
                    output="\n".join(outputs),
                    error_message="Command timed out"
                )
            except Exception as e:
                return FixResult(
                    success=False,
                    suggestion=suggestion,
                    output="\n".join(outputs),
                    error_message=str(e)
                )
        
        return FixResult(
            success=True,
            suggestion=suggestion,
            output="\n".join(outputs)
        )
    
    def _apply_install_fix(self, suggestion: FixSuggestion, error_context: ErrorContext) -> FixResult:
        """Apply an installation fix."""
        return self._apply_command_fix(suggestion, error_context)
    
    def _apply_config_fix(self, suggestion: FixSuggestion, error_context: ErrorContext) -> FixResult:
        """Apply a configuration fix."""
        return self._apply_code_changes(suggestion, error_context)
    
    def _get_learned_fixes(self, error_context: ErrorContext) -> List[FixSuggestion]:
        """Get learned fixes for similar errors."""
        error_signature = self._get_error_signature(error_context)
        return self.learned_patterns.get(error_signature, [])
    
    def _learn_from_fix(self, error_context: ErrorContext, suggestion: FixSuggestion) -> None:
        """Learn from a successful fix."""
        error_signature = self._get_error_signature(error_context)
        
        if error_signature not in self.learned_patterns:
            self.learned_patterns[error_signature] = []
        
        # Add to learned patterns if not already present
        if suggestion not in self.learned_patterns[error_signature]:
            self.learned_patterns[error_signature].append(suggestion)
            logger.info(f"Learned new fix pattern for {error_signature}")
            
            # Save to disk
            self._save_learned_patterns()
    
    def _get_error_signature(self, error_context: ErrorContext) -> str:
        """Generate a signature for an error to match similar errors."""
        # Normalize error message by removing specific values
        normalized_message = re.sub(r"'[^']+'", "'*'", error_context.message)
        normalized_message = re.sub(r'"[^"]+"', '"*"', normalized_message)
        normalized_message = re.sub(r'\d+', '*', normalized_message)
        
        return f"{error_context.error_type.value}:{normalized_message[:100]}"
    
    def _load_learned_patterns(self) -> None:
        """Load learned patterns from disk."""
        patterns_file = Path.home() / ".codegenie" / "learned_patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert back to FixSuggestion objects
                for signature, suggestions_data in data.items():
                    self.learned_patterns[signature] = [
                        FixSuggestion(
                            description=s['description'],
                            fix_type=s['fix_type'],
                            confidence=FixConfidence(s['confidence']),
                            code_changes=s.get('code_changes'),
                            commands=s.get('commands'),
                            explanation=s.get('explanation'),
                            estimated_time=s.get('estimated_time'),
                            requires_approval=s.get('requires_approval', True),
                            metadata=s.get('metadata', {})
                        )
                        for s in suggestions_data
                    ]
                
                logger.info(f"Loaded {len(self.learned_patterns)} learned patterns")
            except Exception as e:
                logger.warning(f"Failed to load learned patterns: {e}")
    
    def _save_learned_patterns(self) -> None:
        """Save learned patterns to disk."""
        patterns_file = Path.home() / ".codegenie" / "learned_patterns.json"
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert to JSON-serializable format
            data = {}
            for signature, suggestions in self.learned_patterns.items():
                data[signature] = [
                    {
                        'description': s.description,
                        'fix_type': s.fix_type,
                        'confidence': s.confidence.value,
                        'code_changes': s.code_changes,
                        'commands': s.commands,
                        'explanation': s.explanation,
                        'estimated_time': s.estimated_time,
                        'requires_approval': s.requires_approval,
                        'metadata': s.metadata
                    }
                    for s in suggestions
                ]
            
            with open(patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved learned patterns to {patterns_file}")
        except Exception as e:
            logger.warning(f"Failed to save learned patterns: {e}")
    
    def get_fix_statistics(self) -> Dict[str, Any]:
        """Get statistics about fix attempts."""
        if not self.fix_history:
            return {
                "total_attempts": 0,
                "successful_fixes": 0,
                "success_rate": 0.0,
                "learned_patterns": len(self.learned_patterns)
            }
        
        total = len(self.fix_history)
        successful = sum(1 for r in self.fix_history if r.success)
        
        # Group by fix type
        by_type = {}
        for result in self.fix_history:
            fix_type = result.suggestion.fix_type
            if fix_type not in by_type:
                by_type[fix_type] = {"total": 0, "successful": 0}
            by_type[fix_type]["total"] += 1
            if result.success:
                by_type[fix_type]["successful"] += 1
        
        return {
            "total_attempts": total,
            "successful_fixes": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_duration": sum(r.duration for r in self.fix_history) / total,
            "by_fix_type": by_type,
            "learned_patterns": len(self.learned_patterns)
        }
    
    def clear_history(self) -> None:
        """Clear fix history."""
        self.fix_history.clear()
        logger.info("Cleared fix history")
    
    def reset_learned_patterns(self) -> None:
        """Reset all learned patterns."""
        self.learned_patterns.clear()
        self._save_learned_patterns()
        logger.info("Reset learned patterns")



class FixPatternLearner:
    """
    Learns patterns from successful fixes and recommends fixes
    based on historical success rates.
    """
    
    def __init__(self, recovery_system: ErrorRecoverySystem):
        """
        Initialize the pattern learner.
        
        Args:
            recovery_system: The error recovery system to learn from
        """
        self.recovery_system = recovery_system
        self.pattern_success_rates: Dict[str, Dict[str, float]] = {}
        self.pattern_usage_counts: Dict[str, Dict[str, int]] = {}
        self._load_pattern_statistics()
    
    def track_fix_success(self, error_context: ErrorContext, fix_result: FixResult) -> None:
        """
        Track the success of a fix for learning.
        
        Args:
            error_context: The error context
            fix_result: The result of the fix attempt
        """
        error_signature = self.recovery_system._get_error_signature(error_context)
        fix_signature = self._get_fix_signature(fix_result.suggestion)
        
        # Initialize tracking structures
        if error_signature not in self.pattern_success_rates:
            self.pattern_success_rates[error_signature] = {}
            self.pattern_usage_counts[error_signature] = {}
        
        # Update usage count
        if fix_signature not in self.pattern_usage_counts[error_signature]:
            self.pattern_usage_counts[error_signature][fix_signature] = 0
        self.pattern_usage_counts[error_signature][fix_signature] += 1
        
        # Update success rate using exponential moving average
        current_rate = self.pattern_success_rates[error_signature].get(fix_signature, 0.5)
        alpha = 0.3  # Learning rate
        new_rate = alpha * (1.0 if fix_result.success else 0.0) + (1 - alpha) * current_rate
        self.pattern_success_rates[error_signature][fix_signature] = new_rate
        
        logger.debug(f"Updated success rate for {fix_signature}: {new_rate:.2f}")
        
        # Save statistics
        self._save_pattern_statistics()
    
    def recommend_fixes(
        self,
        error_context: ErrorContext,
        candidate_fixes: List[FixSuggestion]
    ) -> List[FixSuggestion]:
        """
        Recommend fixes based on learned patterns.
        
        Args:
            error_context: The error context
            candidate_fixes: List of candidate fix suggestions
        
        Returns:
            Reordered list of fixes based on learned success rates
        """
        error_signature = self.recovery_system._get_error_signature(error_context)
        
        if error_signature not in self.pattern_success_rates:
            return candidate_fixes
        
        # Score each fix based on learned success rate
        scored_fixes = []
        for fix in candidate_fixes:
            fix_signature = self._get_fix_signature(fix)
            success_rate = self.pattern_success_rates[error_signature].get(fix_signature, 0.5)
            usage_count = self.pattern_usage_counts[error_signature].get(fix_signature, 0)
            
            # Combine success rate with usage count (more usage = more confidence)
            confidence_boost = min(usage_count / 10.0, 0.2)  # Max 20% boost
            final_score = success_rate + confidence_boost
            
            scored_fixes.append((final_score, fix))
        
        # Sort by score (descending)
        scored_fixes.sort(key=lambda x: x[0], reverse=True)
        
        return [fix for _, fix in scored_fixes]
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """
        Get insights about learned patterns.
        
        Returns:
            Dictionary with pattern insights
        """
        insights = {
            "total_error_patterns": len(self.pattern_success_rates),
            "total_fix_patterns": sum(len(fixes) for fixes in self.pattern_success_rates.values()),
            "top_successful_patterns": [],
            "problematic_patterns": []
        }
        
        # Find top successful patterns
        all_patterns = []
        for error_sig, fixes in self.pattern_success_rates.items():
            for fix_sig, success_rate in fixes.items():
                usage_count = self.pattern_usage_counts[error_sig].get(fix_sig, 0)
                if usage_count >= 3:  # Only consider patterns used at least 3 times
                    all_patterns.append({
                        "error": error_sig[:50],
                        "fix": fix_sig[:50],
                        "success_rate": success_rate,
                        "usage_count": usage_count
                    })
        
        # Sort by success rate
        all_patterns.sort(key=lambda x: x["success_rate"], reverse=True)
        insights["top_successful_patterns"] = all_patterns[:5]
        insights["problematic_patterns"] = [p for p in all_patterns if p["success_rate"] < 0.3][:5]
        
        return insights
    
    def _get_fix_signature(self, suggestion: FixSuggestion) -> str:
        """Generate a signature for a fix suggestion."""
        # Create a signature based on fix type and key characteristics
        sig_parts = [suggestion.fix_type]
        
        if suggestion.commands:
            # Normalize commands by removing specific values
            normalized_cmds = []
            for cmd in suggestion.commands:
                normalized = re.sub(r'\S+\.(py|js|ts|go|rs)', '*.ext', cmd)
                normalized = re.sub(r'["\']([^"\']+)["\']', '"*"', normalized)
                normalized_cmds.append(normalized)
            sig_parts.extend(normalized_cmds)
        
        return ":".join(sig_parts)[:100]
    
    def _load_pattern_statistics(self) -> None:
        """Load pattern statistics from disk."""
        stats_file = Path.home() / ".codegenie" / "pattern_statistics.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                    self.pattern_success_rates = data.get('success_rates', {})
                    self.pattern_usage_counts = data.get('usage_counts', {})
                
                logger.info(f"Loaded pattern statistics for {len(self.pattern_success_rates)} error patterns")
            except Exception as e:
                logger.warning(f"Failed to load pattern statistics: {e}")
    
    def _save_pattern_statistics(self) -> None:
        """Save pattern statistics to disk."""
        stats_file = Path.home() / ".codegenie" / "pattern_statistics.json"
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {
                'success_rates': self.pattern_success_rates,
                'usage_counts': self.pattern_usage_counts
            }
            
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved pattern statistics to {stats_file}")
        except Exception as e:
            logger.warning(f"Failed to save pattern statistics: {e}")


class InteractiveRecoveryAssistant:
    """
    Provides interactive, user-assisted error recovery with guided workflows.
    """
    
    def __init__(self, recovery_system: ErrorRecoverySystem):
        """
        Initialize the interactive recovery assistant.
        
        Args:
            recovery_system: The error recovery system
        """
        self.recovery_system = recovery_system
        self.interaction_callback: Optional[Callable] = None
    
    def set_interaction_callback(self, callback: Callable) -> None:
        """
        Set callback for user interaction.
        
        Args:
            callback: Function to call for user input (prompt) -> response
        """
        self.interaction_callback = callback
    
    def guided_recovery(
        self,
        error_context: ErrorContext,
        suggestions: Optional[List[FixSuggestion]] = None
    ) -> FixResult:
        """
        Guide user through error recovery process.
        
        Args:
            error_context: The error context
            suggestions: Optional list of fix suggestions
        
        Returns:
            Result of the selected fix
        """
        if not self.interaction_callback:
            return FixResult(
                success=False,
                suggestion=FixSuggestion(
                    description="No interaction callback set",
                    fix_type="none",
                    confidence=FixConfidence.LOW
                ),
                error_message="Interactive recovery requires an interaction callback"
            )
        
        # Get suggestions if not provided
        if suggestions is None:
            suggestions = self.recovery_system.generate_fix_suggestions(error_context)
        
        if not suggestions:
            return self._fallback_to_manual(error_context)
        
        # Present options to user
        options_text = self._format_fix_options(suggestions)
        prompt = f"""
Error detected: {error_context.error_type.value}
Message: {error_context.message}

Available fixes:
{options_text}

Select a fix (1-{len(suggestions)}), or 'm' for manual mode: """
        
        response = self.interaction_callback(prompt)
        
        # Handle response
        if response.lower() == 'm':
            return self._fallback_to_manual(error_context)
        
        try:
            selection = int(response) - 1
            if 0 <= selection < len(suggestions):
                selected_fix = suggestions[selection]
                
                # Confirm before applying
                if selected_fix.requires_approval:
                    confirm_prompt = f"\nApply fix: {selected_fix.description}?\n"
                    if selected_fix.commands:
                        confirm_prompt += f"Commands: {', '.join(selected_fix.commands)}\n"
                    confirm_prompt += "Proceed? (y/n): "
                    
                    confirm = self.interaction_callback(confirm_prompt)
                    if confirm.lower() != 'y':
                        return FixResult(
                            success=False,
                            suggestion=selected_fix,
                            error_message="User cancelled fix"
                        )
                
                # Apply the fix
                return self.recovery_system.apply_automatic_fix(error_context, selected_fix)
            else:
                return FixResult(
                    success=False,
                    suggestion=suggestions[0],
                    error_message="Invalid selection"
                )
        except ValueError:
            return FixResult(
                success=False,
                suggestion=suggestions[0],
                error_message="Invalid input"
            )
    
    def _format_fix_options(self, suggestions: List[FixSuggestion]) -> str:
        """Format fix suggestions for display."""
        lines = []
        for i, suggestion in enumerate(suggestions, 1):
            confidence_icon = {
                FixConfidence.HIGH: "✓",
                FixConfidence.MEDIUM: "~",
                FixConfidence.LOW: "?"
            }[suggestion.confidence]
            
            line = f"{i}. [{confidence_icon}] {suggestion.description}"
            if suggestion.explanation:
                line += f"\n   → {suggestion.explanation}"
            if suggestion.estimated_time:
                line += f" (est. {suggestion.estimated_time}s)"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _fallback_to_manual(self, error_context: ErrorContext) -> FixResult:
        """Fallback to manual mode with helpful information."""
        if not self.interaction_callback:
            return FixResult(
                success=False,
                suggestion=FixSuggestion(
                    description="Manual mode",
                    fix_type="manual",
                    confidence=FixConfidence.LOW
                ),
                error_message="No interaction callback available"
            )
        
        manual_info = f"""
Entering manual mode for error: {error_context.error_type.value}

Error details:
- Message: {error_context.message}
- File: {error_context.file_path or 'N/A'}
- Line: {error_context.line_number or 'N/A'}

Please fix the error manually and press Enter when done...
"""
        
        self.interaction_callback(manual_info)
        
        return FixResult(
            success=True,
            suggestion=FixSuggestion(
                description="Manual fix",
                fix_type="manual",
                confidence=FixConfidence.LOW
            ),
            output="User performed manual fix"
        )
