"""
Advanced error detection and analysis system.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorPattern(BaseModel):
    """Pattern for detecting specific types of errors."""
    
    name: str
    pattern: str
    severity: str  # "error", "warning", "info"
    category: str  # "syntax", "runtime", "import", "type", "logic", "security"
    description: str
    suggested_fix: Optional[str] = None
    confidence: float = 0.8


class DetectedError(BaseModel):
    """A detected error with context and analysis."""
    
    error_type: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    severity: str
    category: str
    confidence: float
    context: Dict[str, Any] = {}
    suggested_fixes: List[str] = []
    related_errors: List[str] = []


class ErrorDetector:
    """Advanced error detection and analysis system."""
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.error_history: List[DetectedError] = []
        self.error_statistics: Dict[str, int] = {}
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize common error patterns."""
        
        patterns = [
            # Python errors
            ErrorPattern(
                name="python_syntax_error",
                pattern=r"SyntaxError: (.+)",
                severity="error",
                category="syntax",
                description="Python syntax error",
                suggested_fix="Check syntax and fix the reported issue",
            ),
            ErrorPattern(
                name="python_indentation_error",
                pattern=r"IndentationError: (.+)",
                severity="error",
                category="syntax",
                description="Python indentation error",
                suggested_fix="Fix indentation using consistent spaces or tabs",
            ),
            ErrorPattern(
                name="python_import_error",
                pattern=r"ImportError: (.+)",
                severity="error",
                category="import",
                description="Python import error",
                suggested_fix="Install missing package or fix import path",
            ),
            ErrorPattern(
                name="python_name_error",
                pattern=r"NameError: name '(.+)' is not defined",
                severity="error",
                category="runtime",
                description="Python name error",
                suggested_fix="Define the variable or import the module",
            ),
            ErrorPattern(
                name="python_type_error",
                pattern=r"TypeError: (.+)",
                severity="error",
                category="type",
                description="Python type error",
                suggested_fix="Check data types and fix type mismatch",
            ),
            ErrorPattern(
                name="python_attribute_error",
                pattern=r"AttributeError: (.+)",
                severity="error",
                category="runtime",
                description="Python attribute error",
                suggested_fix="Check if the attribute exists or fix the object reference",
            ),
            ErrorPattern(
                name="python_value_error",
                pattern=r"ValueError: (.+)",
                severity="error",
                category="logic",
                description="Python value error",
                suggested_fix="Check the value and ensure it's valid for the operation",
            ),
            ErrorPattern(
                name="python_key_error",
                pattern=r"KeyError: (.+)",
                severity="error",
                category="runtime",
                description="Python key error",
                suggested_fix="Check if the key exists in the dictionary",
            ),
            ErrorPattern(
                name="python_file_not_found",
                pattern=r"FileNotFoundError: (.+)",
                severity="error",
                category="runtime",
                description="File not found error",
                suggested_fix="Check if the file exists and the path is correct",
            ),
            ErrorPattern(
                name="python_permission_error",
                pattern=r"PermissionError: (.+)",
                severity="error",
                category="runtime",
                description="Permission error",
                suggested_fix="Check file permissions or run with appropriate privileges",
            ),
            
            # JavaScript/TypeScript errors
            ErrorPattern(
                name="js_syntax_error",
                pattern=r"SyntaxError: (.+)",
                severity="error",
                category="syntax",
                description="JavaScript syntax error",
                suggested_fix="Check JavaScript syntax and fix the reported issue",
            ),
            ErrorPattern(
                name="js_reference_error",
                pattern=r"ReferenceError: (.+)",
                severity="error",
                category="runtime",
                description="JavaScript reference error",
                suggested_fix="Define the variable or check the scope",
            ),
            ErrorPattern(
                name="js_type_error",
                pattern=r"TypeError: (.+)",
                severity="error",
                category="type",
                description="JavaScript type error",
                suggested_fix="Check data types and fix type mismatch",
            ),
            ErrorPattern(
                name="js_module_not_found",
                pattern=r"Cannot resolve module '(.+)'",
                severity="error",
                category="import",
                description="Module not found error",
                suggested_fix="Install the missing module or check the import path",
            ),
            
            # Go errors
            ErrorPattern(
                name="go_compile_error",
                pattern=r"cannot use (.+)",
                severity="error",
                category="type",
                description="Go compilation error",
                suggested_fix="Fix type mismatch or variable usage",
            ),
            ErrorPattern(
                name="go_undefined_error",
                pattern=r"undefined: (.+)",
                severity="error",
                category="runtime",
                description="Go undefined variable error",
                suggested_fix="Define the variable or import the package",
            ),
            ErrorPattern(
                name="go_import_error",
                pattern=r"imported and not used: (.+)",
                severity="warning",
                category="import",
                description="Go unused import warning",
                suggested_fix="Remove unused import or use the imported package",
            ),
            
            # Rust errors
            ErrorPattern(
                name="rust_compile_error",
                pattern=r"error\[E\d+\]: (.+)",
                severity="error",
                category="compile",
                description="Rust compilation error",
                suggested_fix="Fix the compilation issue as suggested by the error",
            ),
            ErrorPattern(
                name="rust_borrow_checker",
                pattern=r"cannot borrow (.+) as (.+)",
                severity="error",
                category="memory",
                description="Rust borrow checker error",
                suggested_fix="Fix borrowing rules or restructure the code",
            ),
            
            # General errors
            ErrorPattern(
                name="command_not_found",
                pattern=r"command not found: (.+)",
                severity="error",
                category="runtime",
                description="Command not found error",
                suggested_fix="Install the missing command or check the PATH",
            ),
            ErrorPattern(
                name="permission_denied",
                pattern=r"Permission denied",
                severity="error",
                category="security",
                description="Permission denied error",
                suggested_fix="Check permissions or run with appropriate privileges",
            ),
            ErrorPattern(
                name="connection_error",
                pattern=r"ConnectionError: (.+)",
                severity="error",
                category="network",
                description="Network connection error",
                suggested_fix="Check network connection and server availability",
            ),
            ErrorPattern(
                name="timeout_error",
                pattern=r"TimeoutError: (.+)",
                severity="error",
                category="runtime",
                description="Operation timeout error",
                suggested_fix="Increase timeout or optimize the operation",
            ),
        ]
        
        return patterns
    
    def detect_errors(self, output: str, file_path: Optional[str] = None) -> List[DetectedError]:
        """Detect errors in command output or file content."""
        
        detected_errors = []
        lines = output.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.error_patterns:
                match = re.search(pattern.pattern, line, re.IGNORECASE)
                if match:
                    error = DetectedError(
                        error_type=pattern.name,
                        message=line.strip(),
                        file_path=file_path,
                        line_number=line_num,
                        severity=pattern.severity,
                        category=pattern.category,
                        confidence=pattern.confidence,
                        context={
                            "matched_pattern": pattern.pattern,
                            "full_line": line,
                            "match_groups": match.groups(),
                        },
                        suggested_fixes=[pattern.suggested_fix] if pattern.suggested_fix else [],
                    )
                    
                    # Enhance with additional context
                    error = self._enhance_error_context(error, lines, line_num)
                    
                    detected_errors.append(error)
        
        # Add to history and update statistics
        for error in detected_errors:
            self.error_history.append(error)
            self.error_statistics[error.error_type] = self.error_statistics.get(error.error_type, 0) + 1
        
        return detected_errors
    
    def _enhance_error_context(self, error: DetectedError, lines: List[str], line_num: int) -> DetectedError:
        """Enhance error with additional context."""
        
        # Add surrounding lines for context
        start_line = max(0, line_num - 3)
        end_line = min(len(lines), line_num + 3)
        error.context["surrounding_lines"] = lines[start_line:end_line]
        
        # Add file-specific context
        if error.file_path:
            error.context["file_exists"] = Path(error.file_path).exists()
            if Path(error.file_path).exists():
                try:
                    with open(error.file_path, 'r', encoding='utf-8') as f:
                        file_lines = f.readlines()
                        if error.line_number and error.line_number <= len(file_lines):
                            error.context["file_line_content"] = file_lines[error.line_number - 1].strip()
                except Exception:
                    pass
        
        # Add related errors
        error.related_errors = self._find_related_errors(error)
        
        # Generate additional suggested fixes
        error.suggested_fixes.extend(self._generate_additional_fixes(error))
        
        return error
    
    def _find_related_errors(self, error: DetectedError) -> List[str]:
        """Find related errors in the history."""
        
        related = []
        
        for historical_error in self.error_history[-10:]:  # Check last 10 errors
            if (historical_error.error_type == error.error_type and 
                historical_error.file_path == error.file_path and
                historical_error != error):
                related.append(historical_error.message)
        
        return related[:3]  # Return up to 3 related errors
    
    def _generate_additional_fixes(self, error: DetectedError) -> List[str]:
        """Generate additional suggested fixes based on error type and context."""
        
        additional_fixes = []
        
        if error.category == "import":
            if "module" in error.message.lower():
                additional_fixes.append("Check if the module is installed: pip install <module_name>")
                additional_fixes.append("Verify the import path is correct")
        
        elif error.category == "syntax":
            additional_fixes.append("Check for missing parentheses, brackets, or quotes")
            additional_fixes.append("Verify indentation is consistent")
        
        elif error.category == "type":
            additional_fixes.append("Add type hints to clarify expected types")
            additional_fixes.append("Use type conversion functions if appropriate")
        
        elif error.category == "runtime":
            additional_fixes.append("Add null/undefined checks before using variables")
            additional_fixes.append("Verify the variable is in scope")
        
        elif error.category == "security":
            additional_fixes.append("Check file permissions and ownership")
            additional_fixes.append("Consider using sudo if appropriate")
        
        return additional_fixes
    
    def analyze_error_trends(self) -> Dict[str, Any]:
        """Analyze error trends and patterns."""
        
        if not self.error_history:
            return {"message": "No errors detected yet"}
        
        # Count errors by category
        category_counts = {}
        severity_counts = {}
        file_counts = {}
        
        for error in self.error_history:
            category_counts[error.category] = category_counts.get(error.category, 0) + 1
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1
            
            if error.file_path:
                file_counts[error.file_path] = file_counts.get(error.file_path, 0) + 1
        
        # Find most common errors
        most_common_errors = sorted(
            self.error_statistics.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Find most problematic files
        most_problematic_files = sorted(
            file_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_errors": len(self.error_history),
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "most_common_errors": most_common_errors,
            "most_problematic_files": most_problematic_files,
            "error_rate": len(self.error_history) / max(1, len(set(e.file_path for e in self.error_history if e.file_path))),
        }
    
    def get_error_recommendations(self) -> List[str]:
        """Get recommendations based on error analysis."""
        
        recommendations = []
        trends = self.analyze_error_trends()
        
        if not trends or "total_errors" not in trends:
            return ["No errors detected - keep up the good work!"]
        
        # Category-based recommendations
        category_dist = trends.get("category_distribution", {})
        
        if category_dist.get("syntax", 0) > 5:
            recommendations.append("Consider using a linter to catch syntax errors early")
        
        if category_dist.get("import", 0) > 3:
            recommendations.append("Set up a requirements.txt or package.json to manage dependencies")
        
        if category_dist.get("type", 0) > 3:
            recommendations.append("Add type hints or use a type checker like mypy")
        
        if category_dist.get("runtime", 0) > 5:
            recommendations.append("Add more comprehensive error handling and validation")
        
        # File-based recommendations
        problematic_files = trends.get("most_problematic_files", [])
        if problematic_files:
            most_problematic = problematic_files[0]
            recommendations.append(f"Focus on fixing errors in {most_problematic[0]} (has {most_problematic[1]} errors)")
        
        # General recommendations
        if trends["total_errors"] > 20:
            recommendations.append("Consider implementing automated testing to catch errors early")
        
        if not recommendations:
            recommendations.append("Error patterns look normal - continue with current practices")
        
        return recommendations
    
    def clear_history(self) -> None:
        """Clear error history and statistics."""
        self.error_history.clear()
        self.error_statistics.clear()
        logger.info("Cleared error detection history")
    
    def get_recent_errors(self, limit: int = 10) -> List[DetectedError]:
        """Get recent errors."""
        return self.error_history[-limit:] if self.error_history else []
    
    def get_errors_by_file(self, file_path: str) -> List[DetectedError]:
        """Get all errors for a specific file."""
        return [error for error in self.error_history if error.file_path == file_path]
    
    def get_errors_by_category(self, category: str) -> List[DetectedError]:
        """Get all errors of a specific category."""
        return [error for error in self.error_history if error.category == category]
    
    def get_errors_by_severity(self, severity: str) -> List[DetectedError]:
        """Get all errors of a specific severity."""
        return [error for error in self.error_history if error.severity == severity]
