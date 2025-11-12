"""
Security and Performance Scanning System.

This module provides:
- Security vulnerability detection in monitoring
- Performance bottleneck identification
- Proactive alerting system
- Automatic fix generation for common issues
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SecurityIssueType(Enum):
    """Types of security issues."""
    SQL_INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    HARDCODED_SECRET = "hardcoded_secret"
    INSECURE_RANDOM = "insecure_random"
    UNSAFE_DESERIALIZATION = "unsafe_deserialization"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    WEAK_CRYPTO = "weak_crypto"


class PerformanceIssueType(Enum):
    """Types of performance issues."""
    INEFFICIENT_LOOP = "inefficient_loop"
    UNNECESSARY_COMPUTATION = "unnecessary_computation"
    MEMORY_LEAK = "memory_leak"
    BLOCKING_IO = "blocking_io"
    N_PLUS_ONE = "n_plus_one_query"
    LARGE_DATA_STRUCTURE = "large_data_structure"


class IssueSeverity(Enum):
    """Severity levels for issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityIssue:
    """Represents a security vulnerability."""
    issue_type: SecurityIssueType
    severity: IssueSeverity
    file_path: Path
    line_number: Optional[int]
    description: str
    vulnerable_code: str
    suggested_fix: Optional[str] = None
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)



@dataclass
class PerformanceIssue:
    """Represents a performance bottleneck."""
    issue_type: PerformanceIssueType
    severity: IssueSeverity
    file_path: Path
    line_number: Optional[int]
    description: str
    problematic_code: str
    suggested_fix: Optional[str] = None
    estimated_impact: str = ""  # e.g., "10x slower", "O(n^2) complexity"
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProactiveAlert:
    """Represents a proactive alert."""
    alert_type: str  # security, performance, quality
    severity: IssueSeverity
    title: str
    description: str
    affected_files: List[Path]
    action_required: str
    auto_fixable: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


class SecurityScanner:
    """Scans code for security vulnerabilities."""
    
    def __init__(self):
        """Initialize security scanner."""
        self.detected_issues: List[SecurityIssue] = []
        
        # Patterns for detecting security issues
        self.secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'aws[_-]?access[_-]?key',
        ]
        
        self.dangerous_functions = {
            'eval': SecurityIssueType.COMMAND_INJECTION,
            'exec': SecurityIssueType.COMMAND_INJECTION,
            'pickle.loads': SecurityIssueType.UNSAFE_DESERIALIZATION,
            'yaml.load': SecurityIssueType.UNSAFE_DESERIALIZATION,
            'os.system': SecurityIssueType.COMMAND_INJECTION,
            'subprocess.call': SecurityIssueType.COMMAND_INJECTION,
        }
    
    async def scan_file(self, file_path: Path) -> List[SecurityIssue]:
        """
        Scan a file for security vulnerabilities.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            List of security issues
        """
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for hardcoded secrets
            issues.extend(self._detect_hardcoded_secrets(file_path, content))
            
            # Parse AST for deeper analysis
            tree = ast.parse(content)
            
            # Check for dangerous function calls
            issues.extend(self._detect_dangerous_functions(tree, file_path, content))
            
            # Check for SQL injection vulnerabilities
            issues.extend(self._detect_sql_injection(tree, file_path, content))
            
            # Check for insecure random usage
            issues.extend(self._detect_insecure_random(tree, file_path, content))
            
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        self.detected_issues.extend(issues)
        return issues
    
    def _detect_hardcoded_secrets(self, file_path: Path, content: str) -> List[SecurityIssue]:
        """Detect hardcoded secrets in code."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        issue_type=SecurityIssueType.HARDCODED_SECRET,
                        severity=IssueSeverity.HIGH,
                        file_path=file_path,
                        line_number=i,
                        description="Potential hardcoded secret detected",
                        vulnerable_code=line.strip(),
                        suggested_fix="Use environment variables or a secrets management system",
                        cwe_id="CWE-798",
                        confidence=0.7
                    ))
        
        return issues
    
    def _detect_dangerous_functions(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[SecurityIssue]:
        """Detect usage of dangerous functions."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                
                if func_name in self.dangerous_functions:
                    issue_type = self.dangerous_functions[func_name]
                    
                    issues.append(SecurityIssue(
                        issue_type=issue_type,
                        severity=IssueSeverity.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Dangerous function '{func_name}' detected",
                        vulnerable_code=ast.get_source_segment(content, node) or func_name,
                        suggested_fix=self._get_safe_alternative(func_name),
                        confidence=0.9
                    ))
        
        return issues
    
    def _get_function_name(self, node: ast.Call) -> str:
        """Extract function name from call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
        return ""
    
    def _get_safe_alternative(self, dangerous_func: str) -> str:
        """Get safe alternative for dangerous function."""
        alternatives = {
            'eval': "Use ast.literal_eval() for safe evaluation",
            'exec': "Avoid dynamic code execution or use restricted execution",
            'pickle.loads': "Use json.loads() or implement custom serialization",
            'yaml.load': "Use yaml.safe_load() instead",
            'os.system': "Use subprocess.run() with shell=False",
            'subprocess.call': "Use subprocess.run() with proper argument escaping",
        }
        return alternatives.get(dangerous_func, "Use a safer alternative")
    
    def _detect_sql_injection(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[SecurityIssue]:
        """Detect potential SQL injection vulnerabilities."""
        issues = []
        
        for node in ast.walk(tree):
            # Look for string formatting in SQL queries
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                
                # Check for execute() calls with string formatting
                if 'execute' in func_name.lower():
                    for arg in node.args:
                        if isinstance(arg, (ast.JoinedStr, ast.BinOp)):
                            issues.append(SecurityIssue(
                                issue_type=SecurityIssueType.SQL_INJECTION,
                                severity=IssueSeverity.CRITICAL,
                                file_path=file_path,
                                line_number=node.lineno,
                                description="Potential SQL injection: string formatting in query",
                                vulnerable_code=ast.get_source_segment(content, node) or '',
                                suggested_fix="Use parameterized queries with placeholders",
                                cwe_id="CWE-89",
                                confidence=0.8
                            ))
        
        return issues
    
    def _detect_insecure_random(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[SecurityIssue]:
        """Detect insecure random number generation."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'random':
                        issues.append(SecurityIssue(
                            issue_type=SecurityIssueType.INSECURE_RANDOM,
                            severity=IssueSeverity.MEDIUM,
                            file_path=file_path,
                            line_number=node.lineno,
                            description="Using 'random' module for security-sensitive operations",
                            vulnerable_code="import random",
                            suggested_fix="Use 'secrets' module for cryptographic randomness",
                            cwe_id="CWE-338",
                            confidence=0.6
                        ))
        
        return issues
    
    def get_critical_issues(self) -> List[SecurityIssue]:
        """Get critical security issues."""
        return [
            issue for issue in self.detected_issues
            if issue.severity == IssueSeverity.CRITICAL
        ]



class PerformanceScanner:
    """Scans code for performance bottlenecks."""
    
    def __init__(self):
        """Initialize performance scanner."""
        self.detected_issues: List[PerformanceIssue] = []
    
    async def scan_file(self, file_path: Path) -> List[PerformanceIssue]:
        """
        Scan a file for performance issues.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            List of performance issues
        """
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Detect inefficient loops
            issues.extend(self._detect_inefficient_loops(tree, file_path, content))
            
            # Detect blocking I/O
            issues.extend(self._detect_blocking_io(tree, file_path, content))
            
            # Detect unnecessary computations
            issues.extend(self._detect_unnecessary_computation(tree, file_path, content))
            
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        self.detected_issues.extend(issues)
        return issues
    
    def _detect_inefficient_loops(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[PerformanceIssue]:
        """Detect inefficient loop patterns."""
        issues = []
        
        for node in ast.walk(tree):
            # Nested loops (potential O(n^2) or worse)
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = [
                    n for n in ast.walk(node)
                    if isinstance(n, (ast.For, ast.While)) and n != node
                ]
                
                if len(nested_loops) >= 2:
                    issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.INEFFICIENT_LOOP,
                        severity=IssueSeverity.MEDIUM,
                        file_path=file_path,
                        line_number=node.lineno,
                        description="Deeply nested loops detected",
                        problematic_code=ast.get_source_segment(content, node) or '',
                        suggested_fix="Consider using more efficient algorithms or data structures",
                        estimated_impact="O(n^3) or worse complexity",
                        confidence=0.7
                    ))
        
        return issues
    
    def _detect_blocking_io(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[PerformanceIssue]:
        """Detect blocking I/O operations."""
        issues = []
        
        blocking_functions = ['open', 'read', 'write', 'requests.get', 'requests.post']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                
                if any(blocking in func_name for blocking in blocking_functions):
                    # Check if it's in an async function
                    parent_func = self._find_parent_function(tree, node)
                    if parent_func and isinstance(parent_func, ast.AsyncFunctionDef):
                        issues.append(PerformanceIssue(
                            issue_type=PerformanceIssueType.BLOCKING_IO,
                            severity=IssueSeverity.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            description=f"Blocking I/O '{func_name}' in async function",
                            problematic_code=ast.get_source_segment(content, node) or '',
                            suggested_fix="Use async I/O operations (aiofiles, aiohttp, etc.)",
                            estimated_impact="Blocks event loop",
                            confidence=0.8
                        ))
        
        return issues
    
    def _get_function_name(self, node: ast.Call) -> str:
        """Extract function name from call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
        return ""
    
    def _find_parent_function(self, tree: ast.AST, target: ast.AST) -> Optional[ast.FunctionDef]:
        """Find parent function of a node."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if target in ast.walk(node):
                    return node
        return None
    
    def _detect_unnecessary_computation(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str
    ) -> List[PerformanceIssue]:
        """Detect unnecessary computations."""
        issues = []
        
        for node in ast.walk(tree):
            # Look for repeated function calls in loops
            if isinstance(node, (ast.For, ast.While)):
                calls_in_loop = [n for n in ast.walk(node.body[0] if node.body else node) 
                               if isinstance(n, ast.Call)]
                
                # Check for calls that could be moved outside loop
                if len(calls_in_loop) > 0:
                    for call in calls_in_loop:
                        # Simple heuristic: if call has no loop variable, might be movable
                        func_name = self._get_function_name(call)
                        if func_name and not any(isinstance(arg, ast.Name) for arg in call.args):
                            issues.append(PerformanceIssue(
                                issue_type=PerformanceIssueType.UNNECESSARY_COMPUTATION,
                                severity=IssueSeverity.LOW,
                                file_path=file_path,
                                line_number=call.lineno,
                                description=f"Function '{func_name}' called repeatedly in loop",
                                problematic_code=ast.get_source_segment(content, call) or '',
                                suggested_fix="Consider moving invariant computation outside loop",
                                estimated_impact="Unnecessary repeated computation",
                                confidence=0.5
                            ))
                            break  # Only report once per loop
        
        return issues
    
    def get_high_impact_issues(self) -> List[PerformanceIssue]:
        """Get high-impact performance issues."""
        return [
            issue for issue in self.detected_issues
            if issue.severity in [IssueSeverity.HIGH, IssueSeverity.CRITICAL]
        ]


class ProactiveAlertSystem:
    """Generates proactive alerts based on detected issues."""
    
    def __init__(self):
        """Initialize alert system."""
        self.alerts: List[ProactiveAlert] = []
    
    async def generate_alerts(
        self,
        security_issues: List[SecurityIssue],
        performance_issues: List[PerformanceIssue]
    ) -> List[ProactiveAlert]:
        """
        Generate proactive alerts from detected issues.
        
        Args:
            security_issues: List of security issues
            performance_issues: List of performance issues
            
        Returns:
            List of proactive alerts
        """
        alerts = []
        
        # Generate security alerts
        critical_security = [i for i in security_issues if i.severity == IssueSeverity.CRITICAL]
        if critical_security:
            alert = ProactiveAlert(
                alert_type='security',
                severity=IssueSeverity.CRITICAL,
                title=f"Critical Security Issues Detected ({len(critical_security)})",
                description="Critical security vulnerabilities found that require immediate attention",
                affected_files=list(set(i.file_path for i in critical_security)),
                action_required="Review and fix critical security issues immediately",
                auto_fixable=False
            )
            alerts.append(alert)
        
        # Generate performance alerts
        high_perf_issues = [i for i in performance_issues if i.severity == IssueSeverity.HIGH]
        if high_perf_issues:
            alert = ProactiveAlert(
                alert_type='performance',
                severity=IssueSeverity.HIGH,
                title=f"Performance Bottlenecks Detected ({len(high_perf_issues)})",
                description="High-impact performance issues found",
                affected_files=list(set(i.file_path for i in high_perf_issues)),
                action_required="Review and optimize performance bottlenecks",
                auto_fixable=False
            )
            alerts.append(alert)
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_active_alerts(self) -> List[ProactiveAlert]:
        """Get all active alerts."""
        return self.alerts
    
    def get_alerts_by_severity(self, severity: IssueSeverity) -> List[ProactiveAlert]:
        """Get alerts of specific severity."""
        return [alert for alert in self.alerts if alert.severity == severity]


class AutoFixGenerator:
    """Generates automatic fixes for common security and performance issues."""
    
    def __init__(self):
        """Initialize auto fix generator."""
        self.generated_fixes: List[Dict[str, Any]] = []
    
    async def generate_fixes(
        self,
        security_issues: List[SecurityIssue],
        performance_issues: List[PerformanceIssue]
    ) -> List[Dict[str, Any]]:
        """
        Generate automatic fixes for issues.
        
        Args:
            security_issues: List of security issues
            performance_issues: List of performance issues
            
        Returns:
            List of generated fixes
        """
        fixes = []
        
        # Generate fixes for security issues
        for issue in security_issues:
            if issue.suggested_fix:
                fix = {
                    'issue_type': 'security',
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'description': issue.description,
                    'current_code': issue.vulnerable_code,
                    'suggested_fix': issue.suggested_fix,
                    'auto_applicable': self._is_auto_fixable(issue)
                }
                fixes.append(fix)
        
        # Generate fixes for performance issues
        for issue in performance_issues:
            if issue.suggested_fix:
                fix = {
                    'issue_type': 'performance',
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'description': issue.description,
                    'current_code': issue.problematic_code,
                    'suggested_fix': issue.suggested_fix,
                    'auto_applicable': False  # Performance fixes usually need review
                }
                fixes.append(fix)
        
        self.generated_fixes.extend(fixes)
        return fixes
    
    def _is_auto_fixable(self, issue: SecurityIssue) -> bool:
        """Determine if an issue can be automatically fixed."""
        # Only simple replacements are auto-fixable
        auto_fixable_types = [
            SecurityIssueType.INSECURE_RANDOM,
        ]
        return issue.issue_type in auto_fixable_types



class SecurityPerformanceScanner:
    """
    Main class for proactive security and performance scanning.
    """
    
    def __init__(self):
        """Initialize security and performance scanner."""
        self.security_scanner = SecurityScanner()
        self.performance_scanner = PerformanceScanner()
        self.alert_system = ProactiveAlertSystem()
        self.fix_generator = AutoFixGenerator()
    
    async def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan a file for security and performance issues.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            Dictionary with scan results
        """
        security_issues = await self.security_scanner.scan_file(file_path)
        performance_issues = await self.performance_scanner.scan_file(file_path)
        
        alerts = await self.alert_system.generate_alerts(security_issues, performance_issues)
        fixes = await self.fix_generator.generate_fixes(security_issues, performance_issues)
        
        return {
            'file': file_path,
            'security_issues': security_issues,
            'performance_issues': performance_issues,
            'alerts': alerts,
            'suggested_fixes': fixes,
            'total_issues': len(security_issues) + len(performance_issues)
        }
    
    async def scan_codebase(self, project_root: Path) -> Dict[str, Any]:
        """
        Scan entire codebase for issues.
        
        Args:
            project_root: Root directory of project
            
        Returns:
            Dictionary with comprehensive scan results
        """
        python_files = self._find_python_files(project_root)
        
        all_security_issues = []
        all_performance_issues = []
        
        for file_path in python_files:
            result = await self.scan_file(file_path)
            all_security_issues.extend(result['security_issues'])
            all_performance_issues.extend(result['performance_issues'])
        
        # Generate comprehensive alerts
        alerts = await self.alert_system.generate_alerts(
            all_security_issues,
            all_performance_issues
        )
        
        # Generate fixes
        fixes = await self.fix_generator.generate_fixes(
            all_security_issues,
            all_performance_issues
        )
        
        return {
            'files_scanned': len(python_files),
            'security_issues': {
                'total': len(all_security_issues),
                'critical': len([i for i in all_security_issues if i.severity == IssueSeverity.CRITICAL]),
                'high': len([i for i in all_security_issues if i.severity == IssueSeverity.HIGH]),
                'medium': len([i for i in all_security_issues if i.severity == IssueSeverity.MEDIUM]),
                'low': len([i for i in all_security_issues if i.severity == IssueSeverity.LOW]),
                'issues': all_security_issues
            },
            'performance_issues': {
                'total': len(all_performance_issues),
                'high_impact': len([i for i in all_performance_issues if i.severity == IssueSeverity.HIGH]),
                'issues': all_performance_issues
            },
            'alerts': alerts,
            'suggested_fixes': fixes,
            'auto_fixable_count': len([f for f in fixes if f.get('auto_applicable', False)])
        }
    
    def _find_python_files(self, project_root: Path) -> List[Path]:
        """Find all Python files in project."""
        ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.pytest_cache', '.mypy_cache'
        ]
        
        python_files = []
        for path in project_root.rglob('*.py'):
            if any(ignore in str(path) for ignore in ignore_patterns):
                continue
            python_files.append(path)
        
        return python_files
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of scanning results.
        
        Returns:
            Dictionary with summary
        """
        return {
            'total_security_issues': len(self.security_scanner.detected_issues),
            'critical_security_issues': len(self.security_scanner.get_critical_issues()),
            'total_performance_issues': len(self.performance_scanner.detected_issues),
            'high_impact_performance': len(self.performance_scanner.get_high_impact_issues()),
            'active_alerts': len(self.alert_system.get_active_alerts()),
            'generated_fixes': len(self.fix_generator.generated_fixes)
        }
