"""
Code Validation and Testing Integration System

This module provides comprehensive code validation, testing integration,
and quality assurance for generated code.
"""

import ast
import re
import subprocess
import tempfile
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

from .code_generator import GeneratedCode, CodeLanguage
from ..utils.code_analyzer import CodeAnalyzer


class TestFramework(Enum):
    """Supported testing frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"
    JUNIT = "junit"


class QualityMetric(Enum):
    """Code quality metrics."""
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    TESTABILITY = "testability"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class ValidationIssue:
    """Represents a code validation issue."""
    type: str
    severity: str  # "error", "warning", "info"
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class TestResult:
    """Represents test execution results."""
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    coverage_percentage: Optional[float] = None
    test_output: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class QualityScore:
    """Represents code quality assessment."""
    overall_score: float  # 0-100
    metrics: Dict[QualityMetric, float] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Complete validation result for generated code."""
    is_valid: bool
    syntax_valid: bool
    test_result: Optional[TestResult] = None
    quality_score: Optional[QualityScore] = None
    security_issues: List[ValidationIssue] = field(default_factory=list)
    performance_issues: List[ValidationIssue] = field(default_factory=list)
    style_issues: List[ValidationIssue] = field(default_factory=list)
    execution_time: float = 0.0


class CodeValidator:
    """
    Comprehensive code validation and testing system.
    
    This class provides validation, testing, and quality assessment
    capabilities for generated code across multiple languages.
    """
    
    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
        self._language_validators = self._setup_language_validators()
        self._test_frameworks = self._setup_test_frameworks()
    
    def _setup_language_validators(self) -> Dict[CodeLanguage, Dict[str, Any]]:
        """Setup language-specific validators."""
        return {
            CodeLanguage.PYTHON: {
                "syntax_checker": self._validate_python_syntax,
                "style_checker": self._check_python_style,
                "security_checker": self._check_python_security,
                "test_runner": self._run_python_tests,
                "linter": "pylint",
                "formatter": "black"
            },
            CodeLanguage.JAVASCRIPT: {
                "syntax_checker": self._validate_javascript_syntax,
                "style_checker": self._check_javascript_style,
                "security_checker": self._check_javascript_security,
                "test_runner": self._run_javascript_tests,
                "linter": "eslint",
                "formatter": "prettier"
            },
            CodeLanguage.TYPESCRIPT: {
                "syntax_checker": self._validate_typescript_syntax,
                "style_checker": self._check_typescript_style,
                "security_checker": self._check_typescript_security,
                "test_runner": self._run_typescript_tests,
                "linter": "tslint",
                "formatter": "prettier"
            }
        }
    
    def _setup_test_frameworks(self) -> Dict[TestFramework, Dict[str, Any]]:
        """Setup test framework configurations."""
        return {
            TestFramework.PYTEST: {
                "command": "python -m pytest",
                "file_pattern": "test_*.py",
                "coverage_flag": "--cov",
                "output_format": "json"
            },
            TestFramework.JEST: {
                "command": "npm test",
                "file_pattern": "*.test.js",
                "coverage_flag": "--coverage",
                "output_format": "json"
            },
            TestFramework.UNITTEST: {
                "command": "python -m unittest",
                "file_pattern": "test_*.py",
                "coverage_flag": None,
                "output_format": "text"
            }
        }
    
    async def validate_code(self, generated_code: GeneratedCode, 
                          run_tests: bool = True,
                          check_quality: bool = True) -> ValidationResult:
        """
        Perform comprehensive validation of generated code.
        
        Args:
            generated_code: The generated code to validate
            run_tests: Whether to run tests if available
            check_quality: Whether to perform quality assessment
            
        Returns:
            ValidationResult with all validation results
        """
        start_time = asyncio.get_event_loop().time()
        
        # Initialize result
        result = ValidationResult(
            is_valid=False,
            syntax_valid=False
        )
        
        try:
            # 1. Syntax validation
            result.syntax_valid = await self._validate_syntax(generated_code)
            
            if not result.syntax_valid:
                result.execution_time = asyncio.get_event_loop().time() - start_time
                return result
            
            # 2. Style validation
            result.style_issues = await self._validate_style(generated_code)
            
            # 3. Security validation
            result.security_issues = await self._validate_security(generated_code)
            
            # 4. Performance validation
            result.performance_issues = await self._validate_performance(generated_code)
            
            # 5. Run tests if available and requested
            if run_tests and generated_code.tests:
                result.test_result = await self._run_tests(generated_code)
            
            # 6. Quality assessment
            if check_quality:
                result.quality_score = await self._assess_quality(generated_code)
            
            # Determine overall validity
            critical_issues = [
                issue for issue in (result.security_issues + result.performance_issues)
                if issue.severity == "error"
            ]
            
            test_passed = result.test_result.passed if result.test_result else True
            
            result.is_valid = (
                result.syntax_valid and
                len(critical_issues) == 0 and
                test_passed
            )
            
            result.execution_time = asyncio.get_event_loop().time() - start_time
            
        except Exception as e:
            result.execution_time = asyncio.get_event_loop().time() - start_time
            result.style_issues.append(ValidationIssue(
                type="validation_error",
                severity="error",
                message=f"Validation failed: {str(e)}"
            ))
        
        return result
    
    async def _validate_syntax(self, generated_code: GeneratedCode) -> bool:
        """Validate code syntax."""
        language = generated_code.language
        
        if language in self._language_validators:
            validator = self._language_validators[language]["syntax_checker"]
            return await validator(generated_code.code)
        
        return True  # Assume valid for unsupported languages
    
    async def _validate_python_syntax(self, code: str) -> bool:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    async def _validate_javascript_syntax(self, code: str) -> bool:
        """Validate JavaScript syntax."""
        try:
            # Create temporary file and use Node.js to check syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['node', '--check', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            Path(temp_file).unlink()  # Clean up
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If Node.js is not available, do basic checks
            return self._basic_javascript_syntax_check(code)
    
    async def _validate_typescript_syntax(self, code: str) -> bool:
        """Validate TypeScript syntax."""
        try:
            # Create temporary file and use TypeScript compiler to check syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['tsc', '--noEmit', temp_file],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            Path(temp_file).unlink()  # Clean up
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to JavaScript syntax check
            return await self._validate_javascript_syntax(code)
    
    def _basic_javascript_syntax_check(self, code: str) -> bool:
        """Basic JavaScript syntax check without external tools."""
        # Check for basic syntax errors
        syntax_patterns = [
            r'\bfunction\s+\w+\s*\([^)]*\)\s*{',  # Function declaration
            r'\bconst\s+\w+\s*=',  # Const declaration
            r'\blet\s+\w+\s*=',    # Let declaration
            r'\bvar\s+\w+\s*=',    # Var declaration
        ]
        
        # Check for unmatched braces
        brace_count = code.count('{') - code.count('}')
        paren_count = code.count('(') - code.count(')')
        bracket_count = code.count('[') - code.count(']')
        
        return brace_count == 0 and paren_count == 0 and bracket_count == 0
    
    async def _validate_style(self, generated_code: GeneratedCode) -> List[ValidationIssue]:
        """Validate code style and formatting."""
        issues = []
        code = generated_code.code
        language = generated_code.language
        
        # Common style checks
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                issues.append(ValidationIssue(
                    type="style",
                    severity="warning",
                    message="Line too long (>120 characters)",
                    line_number=i,
                    suggestion="Break long lines into multiple lines"
                ))
            
            # Check trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                issues.append(ValidationIssue(
                    type="style",
                    severity="info",
                    message="Trailing whitespace",
                    line_number=i,
                    suggestion="Remove trailing whitespace"
                ))
        
        # Language-specific style checks
        if language == CodeLanguage.PYTHON:
            issues.extend(await self._check_python_style(code))
        elif language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
            issues.extend(await self._check_javascript_style(code))
        
        return issues
    
    async def _check_python_style(self, code: str) -> List[ValidationIssue]:
        """Check Python-specific style issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for missing docstrings in functions/classes
            if (stripped.startswith('def ') or stripped.startswith('class ')) and i < len(lines):
                next_line = lines[i].strip() if i < len(lines) else ""
                if not next_line.startswith('"""') and not next_line.startswith("'''"):
                    issues.append(ValidationIssue(
                        type="style",
                        severity="warning",
                        message="Missing docstring",
                        line_number=i,
                        suggestion="Add docstring to document the function/class"
                    ))
            
            # Check for proper import organization
            if stripped.startswith('import ') or stripped.startswith('from '):
                if i > 1 and not lines[i-2].strip().startswith(('import ', 'from ', '#', '"""', "'''")):
                    issues.append(ValidationIssue(
                        type="style",
                        severity="info",
                        message="Imports should be at the top of the file",
                        line_number=i,
                        suggestion="Move imports to the top of the file"
                    ))
        
        return issues
    
    async def _check_javascript_style(self, code: str) -> List[ValidationIssue]:
        """Check JavaScript/TypeScript-specific style issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for missing semicolons
            if (stripped and 
                not stripped.endswith((';', '{', '}', ':', ',')) and
                not stripped.startswith(('if', 'for', 'while', 'function', 'class', '//', '/*', '*'))):
                issues.append(ValidationIssue(
                    type="style",
                    severity="warning",
                    message="Missing semicolon",
                    line_number=i,
                    suggestion="Add semicolon at end of statement"
                ))
            
            # Check for var usage (prefer let/const)
            if 'var ' in stripped:
                issues.append(ValidationIssue(
                    type="style",
                    severity="warning",
                    message="Use 'let' or 'const' instead of 'var'",
                    line_number=i,
                    suggestion="Replace 'var' with 'let' or 'const'"
                ))
        
        return issues
    
    async def _validate_security(self, generated_code: GeneratedCode) -> List[ValidationIssue]:
        """Validate code for security issues."""
        issues = []
        code = generated_code.code
        language = generated_code.language
        
        # Common security patterns
        security_patterns = {
            "sql_injection": r"(SELECT|INSERT|UPDATE|DELETE).*\+.*",
            "xss_vulnerability": r"innerHTML\s*=\s*.*\+",
            "hardcoded_password": r"password\s*=\s*['\"][^'\"]+['\"]",
            "eval_usage": r"\beval\s*\(",
            "unsafe_deserialization": r"pickle\.loads?\s*\("
        }
        
        for pattern_name, pattern in security_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(ValidationIssue(
                    type="security",
                    severity="error",
                    message=f"Potential {pattern_name.replace('_', ' ')} vulnerability",
                    line_number=line_num,
                    suggestion=f"Review and secure the {pattern_name.replace('_', ' ')} pattern"
                ))
        
        # Language-specific security checks
        if language == CodeLanguage.PYTHON:
            issues.extend(await self._check_python_security(code))
        elif language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
            issues.extend(await self._check_javascript_security(code))
        
        return issues
    
    async def _check_python_security(self, code: str) -> List[ValidationIssue]:
        """Check Python-specific security issues."""
        issues = []
        
        # Check for dangerous imports
        dangerous_imports = ['os', 'subprocess', 'eval', 'exec', 'compile']
        for imp in dangerous_imports:
            if f"import {imp}" in code or f"from {imp}" in code:
                issues.append(ValidationIssue(
                    type="security",
                    severity="warning",
                    message=f"Potentially dangerous import: {imp}",
                    suggestion=f"Ensure {imp} usage is secure and necessary"
                ))
        
        return issues
    
    async def _check_javascript_security(self, code: str) -> List[ValidationIssue]:
        """Check JavaScript-specific security issues."""
        issues = []
        
        # Check for dangerous functions
        dangerous_functions = ['eval', 'setTimeout', 'setInterval']
        for func in dangerous_functions:
            if f"{func}(" in code:
                issues.append(ValidationIssue(
                    type="security",
                    severity="warning",
                    message=f"Potentially dangerous function: {func}",
                    suggestion=f"Avoid using {func} with user input"
                ))
        
        return issues
    
    async def _validate_performance(self, generated_code: GeneratedCode) -> List[ValidationIssue]:
        """Validate code for performance issues."""
        issues = []
        code = generated_code.code
        
        # Check for performance anti-patterns
        performance_patterns = {
            "nested_loops": r"for\s*\([^)]*\)\s*{[^}]*for\s*\([^)]*\)",
            "string_concatenation_in_loop": r"for\s*\([^)]*\)[^}]*\+=\s*['\"]",
            "inefficient_list_operations": r"\.append\s*\([^)]*\)\s*.*for.*in"
        }
        
        for pattern_name, pattern in performance_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE | re.DOTALL)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(ValidationIssue(
                    type="performance",
                    severity="warning",
                    message=f"Potential performance issue: {pattern_name.replace('_', ' ')}",
                    line_number=line_num,
                    suggestion=f"Consider optimizing the {pattern_name.replace('_', ' ')} pattern"
                ))
        
        return issues
    
    async def _run_tests(self, generated_code: GeneratedCode) -> TestResult:
        """Run tests for the generated code."""
        if not generated_code.tests:
            return TestResult(
                passed=True,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=0.0,
                test_output="No tests provided"
            )
        
        language = generated_code.language
        
        if language == CodeLanguage.PYTHON:
            return await self._run_python_tests(generated_code)
        elif language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
            return await self._run_javascript_tests(generated_code)
        
        # Default result for unsupported languages
        return TestResult(
            passed=True,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            execution_time=0.0,
            test_output="Test execution not supported for this language"
        )
    
    async def _run_python_tests(self, generated_code: GeneratedCode) -> TestResult:
        """Run Python tests using pytest."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create temporary files for code and tests
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write main code
                code_file = temp_path / "main.py"
                code_file.write_text(generated_code.code)
                
                # Write test code
                test_file = temp_path / "test_main.py"
                test_code = f"from main import *\n\n{generated_code.tests}"
                test_file.write_text(test_code)
                
                # Run pytest
                result = subprocess.run(
                    ['python', '-m', 'pytest', str(test_file), '-v', '--tb=short'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                # Parse pytest output
                return self._parse_pytest_output(result.stdout, result.stderr, execution_time)
                
        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=30.0,
                test_output="Test execution timed out",
                errors=["Test execution timed out after 30 seconds"]
            )
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            return TestResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=execution_time,
                test_output=f"Test execution failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _run_javascript_tests(self, generated_code: GeneratedCode) -> TestResult:
        """Run JavaScript tests using Jest."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create temporary files for code and tests
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write main code
                code_file = temp_path / "main.js"
                code_file.write_text(generated_code.code)
                
                # Write test code
                test_file = temp_path / "main.test.js"
                test_code = f"const {{ {self._extract_exports(generated_code.code)} }} = require('./main.js');\n\n{generated_code.tests}"
                test_file.write_text(test_code)
                
                # Create package.json for Jest
                package_json = {
                    "name": "test-project",
                    "version": "1.0.0",
                    "scripts": {"test": "jest"},
                    "devDependencies": {"jest": "^27.0.0"}
                }
                (temp_path / "package.json").write_text(json.dumps(package_json))
                
                # Run Jest
                result = subprocess.run(
                    ['npx', 'jest', '--verbose'],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                # Parse Jest output
                return self._parse_jest_output(result.stdout, result.stderr, execution_time)
                
        except subprocess.TimeoutExpired:
            return TestResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=30.0,
                test_output="Test execution timed out",
                errors=["Test execution timed out after 30 seconds"]
            )
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            return TestResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=execution_time,
                test_output=f"Test execution failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _extract_exports(self, code: str) -> str:
        """Extract exported functions/classes from JavaScript code."""
        # Simple extraction - in practice, you'd want more sophisticated parsing
        exports = []
        
        # Find function declarations
        func_matches = re.finditer(r'function\s+(\w+)', code)
        for match in func_matches:
            exports.append(match.group(1))
        
        # Find class declarations
        class_matches = re.finditer(r'class\s+(\w+)', code)
        for match in class_matches:
            exports.append(match.group(1))
        
        return ', '.join(exports) if exports else ''
    
    def _parse_pytest_output(self, stdout: str, stderr: str, execution_time: float) -> TestResult:
        """Parse pytest output to extract test results."""
        # Simple parsing - in practice, you'd want more robust parsing
        total_tests = stdout.count('::')
        passed_tests = stdout.count('PASSED')
        failed_tests = stdout.count('FAILED')
        skipped_tests = stdout.count('SKIPPED')
        
        passed = failed_tests == 0
        
        return TestResult(
            passed=passed,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            execution_time=execution_time,
            test_output=stdout,
            errors=[stderr] if stderr else []
        )
    
    def _parse_jest_output(self, stdout: str, stderr: str, execution_time: float) -> TestResult:
        """Parse Jest output to extract test results."""
        # Simple parsing - in practice, you'd want more robust parsing
        passed = "Tests:" in stdout and "failed" not in stdout.lower()
        
        # Extract test counts (simplified)
        total_tests = stdout.count('✓') + stdout.count('✗')
        passed_tests = stdout.count('✓')
        failed_tests = stdout.count('✗')
        
        return TestResult(
            passed=passed,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=0,
            execution_time=execution_time,
            test_output=stdout,
            errors=[stderr] if stderr else []
        )
    
    async def _assess_quality(self, generated_code: GeneratedCode) -> QualityScore:
        """Assess overall code quality."""
        metrics = {}
        issues = []
        suggestions = []
        
        code = generated_code.code
        lines = code.split('\n')
        
        # Calculate complexity (simplified)
        complexity = self._calculate_complexity(code)
        metrics[QualityMetric.COMPLEXITY] = min(100, max(0, 100 - complexity * 10))
        
        # Calculate maintainability
        maintainability = self._calculate_maintainability(code, lines)
        metrics[QualityMetric.MAINTAINABILITY] = maintainability
        
        # Calculate readability
        readability = self._calculate_readability(code, lines)
        metrics[QualityMetric.READABILITY] = readability
        
        # Calculate testability
        testability = self._calculate_testability(code)
        metrics[QualityMetric.TESTABILITY] = testability
        
        # Overall score (weighted average)
        weights = {
            QualityMetric.COMPLEXITY: 0.25,
            QualityMetric.MAINTAINABILITY: 0.25,
            QualityMetric.READABILITY: 0.20,
            QualityMetric.TESTABILITY: 0.30
        }
        
        overall_score = sum(
            metrics[metric] * weight 
            for metric, weight in weights.items()
        )
        
        # Generate suggestions based on low scores
        if metrics[QualityMetric.COMPLEXITY] < 70:
            suggestions.append("Consider breaking down complex functions into smaller ones")
        
        if metrics[QualityMetric.READABILITY] < 70:
            suggestions.append("Add more comments and improve variable naming")
        
        if metrics[QualityMetric.TESTABILITY] < 70:
            suggestions.append("Reduce dependencies and improve function isolation")
        
        return QualityScore(
            overall_score=overall_score,
            metrics=metrics,
            issues=issues,
            suggestions=suggestions
        )
    
    def _calculate_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity (simplified)."""
        # Count decision points
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'case']
        complexity = 1  # Base complexity
        
        for keyword in decision_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', code))
        
        return complexity
    
    def _calculate_maintainability(self, code: str, lines: List[str]) -> float:
        """Calculate maintainability score."""
        score = 100.0
        
        # Penalize long functions
        function_lines = 0
        in_function = False
        
        for line in lines:
            if 'def ' in line or 'function ' in line:
                in_function = True
                function_lines = 1
            elif in_function:
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    if function_lines > 50:
                        score -= 10
                    in_function = False
                else:
                    function_lines += 1
        
        # Penalize lack of documentation
        if '"""' not in code and "'''" not in code and '/*' not in code:
            score -= 20
        
        return max(0, score)
    
    def _calculate_readability(self, code: str, lines: List[str]) -> float:
        """Calculate readability score."""
        score = 100.0
        
        # Check average line length
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
            if avg_line_length > 100:
                score -= 20
        
        # Check for meaningful variable names
        short_vars = len(re.findall(r'\b[a-z]\b', code))
        if short_vars > 5:
            score -= 15
        
        # Check for comments
        comment_lines = len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')])
        comment_ratio = comment_lines / len(lines) if lines else 0
        if comment_ratio < 0.1:
            score -= 10
        
        return max(0, score)
    
    def _calculate_testability(self, code: str) -> float:
        """Calculate testability score."""
        score = 100.0
        
        # Check for global variables (reduces testability)
        global_vars = len(re.findall(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=', code, re.MULTILINE))
        score -= global_vars * 5
        
        # Check for external dependencies
        imports = len(re.findall(r'^import\s+|^from\s+', code, re.MULTILINE))
        if imports > 10:
            score -= 10
        
        # Check for pure functions (good for testability)
        functions = len(re.findall(r'def\s+\w+|function\s+\w+', code))
        if functions > 0:
            score += 10
        
        return max(0, min(100, score))