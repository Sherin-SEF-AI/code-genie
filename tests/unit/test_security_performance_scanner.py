"""
Unit tests for Security and Performance Scanner.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.codegenie.core.security_performance_scanner import (
    SecurityPerformanceScanner,
    SecurityScanner,
    PerformanceScanner,
    ProactiveAlertSystem,
    AutoFixGenerator,
    SecurityIssue,
    PerformanceIssue,
    ProactiveAlert,
    SecurityIssueType,
    PerformanceIssueType,
    IssueSeverity
)


class TestSecurityScanner:
    """Test cases for SecurityScanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create a SecurityScanner instance."""
        return SecurityScanner()
    
    @pytest.fixture
    def file_with_hardcoded_secret(self, tmp_path):
        """Create a file with hardcoded secrets."""
        file_path = tmp_path / "secrets.py"
        file_path.write_text('''
API_KEY = "sk-1234567890abcdef"
password = "my_secret_password"
token = "bearer_token_12345"
''')
        return file_path
    
    @pytest.fixture
    def file_with_dangerous_functions(self, tmp_path):
        """Create a file with dangerous function calls."""
        file_path = tmp_path / "dangerous.py"
        file_path.write_text('''
import pickle
import os

def unsafe_function(user_input):
    eval(user_input)
    exec(user_input)
    os.system(user_input)
    data = pickle.loads(user_input)
''')
        return file_path
    
    @pytest.fixture
    def file_with_sql_injection(self, tmp_path):
        """Create a file with SQL injection vulnerability."""
        file_path = tmp_path / "sql_vuln.py"
        file_path.write_text('''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
''')
        return file_path
    
    @pytest.mark.asyncio
    async def test_detect_hardcoded_secrets(self, scanner, file_with_hardcoded_secret):
        """Test detection of hardcoded secrets."""
        issues = await scanner.scan_file(file_with_hardcoded_secret)
        
        secret_issues = [i for i in issues if i.issue_type == SecurityIssueType.HARDCODED_SECRET]
        assert len(secret_issues) > 0
        assert all(i.severity == IssueSeverity.HIGH for i in secret_issues)
    
    @pytest.mark.asyncio
    async def test_detect_dangerous_functions(self, scanner, file_with_dangerous_functions):
        """Test detection of dangerous functions."""
        issues = await scanner.scan_file(file_with_dangerous_functions)
        
        # Should detect eval, exec, os.system, pickle.loads
        assert len(issues) >= 3
        
        dangerous_types = {i.issue_type for i in issues}
        assert SecurityIssueType.COMMAND_INJECTION in dangerous_types or \
               SecurityIssueType.UNSAFE_DESERIALIZATION in dangerous_types
    
    @pytest.mark.asyncio
    async def test_detect_sql_injection(self, scanner, file_with_sql_injection):
        """Test detection of SQL injection vulnerabilities."""
        issues = await scanner.scan_file(file_with_sql_injection)
        
        sql_issues = [i for i in issues if i.issue_type == SecurityIssueType.SQL_INJECTION]
        assert len(sql_issues) > 0
        assert all(i.severity == IssueSeverity.CRITICAL for i in sql_issues)
    
    @pytest.mark.asyncio
    async def test_detect_insecure_random(self, scanner, tmp_path):
        """Test detection of insecure random usage."""
        file_path = tmp_path / "random_usage.py"
        file_path.write_text('''
import random

def generate_token():
    return random.randint(1000, 9999)
''')
        
        issues = await scanner.scan_file(file_path)
        
        random_issues = [i for i in issues if i.issue_type == SecurityIssueType.INSECURE_RANDOM]
        assert len(random_issues) > 0
    
    def test_get_critical_issues(self, scanner):
        """Test getting critical issues."""
        scanner.detected_issues = [
            SecurityIssue(
                SecurityIssueType.SQL_INJECTION,
                IssueSeverity.CRITICAL,
                Path("test.py"), 1, "SQL injection", "code"
            ),
            SecurityIssue(
                SecurityIssueType.HARDCODED_SECRET,
                IssueSeverity.HIGH,
                Path("test.py"), 2, "Secret", "code"
            )
        ]
        
        critical = scanner.get_critical_issues()
        assert len(critical) == 1
        assert critical[0].severity == IssueSeverity.CRITICAL


class TestPerformanceScanner:
    """Test cases for PerformanceScanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create a PerformanceScanner instance."""
        return PerformanceScanner()
    
    @pytest.fixture
    def file_with_nested_loops(self, tmp_path):
        """Create a file with deeply nested loops."""
        file_path = tmp_path / "nested_loops.py"
        file_path.write_text('''
def inefficient_function():
    result = 0
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result += i + j + k
    return result
''')
        return file_path
    
    @pytest.fixture
    def file_with_blocking_io(self, tmp_path):
        """Create a file with blocking I/O in async function."""
        file_path = tmp_path / "blocking_io.py"
        file_path.write_text('''
import requests

async def fetch_data():
    response = requests.get("https://api.example.com")
    return response.json()
''')
        return file_path
    
    @pytest.mark.asyncio
    async def test_detect_nested_loops(self, scanner, file_with_nested_loops):
        """Test detection of inefficient nested loops."""
        issues = await scanner.scan_file(file_with_nested_loops)
        
        loop_issues = [i for i in issues if i.issue_type == PerformanceIssueType.INEFFICIENT_LOOP]
        assert len(loop_issues) > 0
        assert any('O(n^3)' in i.estimated_impact or 'nested' in i.description.lower() 
                  for i in loop_issues)
    
    @pytest.mark.asyncio
    async def test_detect_blocking_io(self, scanner, file_with_blocking_io):
        """Test detection of blocking I/O in async functions."""
        issues = await scanner.scan_file(file_with_blocking_io)
        
        blocking_issues = [i for i in issues if i.issue_type == PerformanceIssueType.BLOCKING_IO]
        assert len(blocking_issues) > 0
        assert all(i.severity == IssueSeverity.HIGH for i in blocking_issues)
    
    def test_get_high_impact_issues(self, scanner):
        """Test getting high-impact issues."""
        scanner.detected_issues = [
            PerformanceIssue(
                PerformanceIssueType.BLOCKING_IO,
                IssueSeverity.HIGH,
                Path("test.py"), 1, "Blocking I/O", "code"
            ),
            PerformanceIssue(
                PerformanceIssueType.UNNECESSARY_COMPUTATION,
                IssueSeverity.LOW,
                Path("test.py"), 2, "Unnecessary", "code"
            )
        ]
        
        high_impact = scanner.get_high_impact_issues()
        assert len(high_impact) == 1
        assert high_impact[0].severity == IssueSeverity.HIGH


class TestProactiveAlertSystem:
    """Test cases for ProactiveAlertSystem."""
    
    @pytest.fixture
    def alert_system(self):
        """Create a ProactiveAlertSystem instance."""
        return ProactiveAlertSystem()
    
    @pytest.fixture
    def sample_security_issues(self):
        """Create sample security issues."""
        return [
            SecurityIssue(
                SecurityIssueType.SQL_INJECTION,
                IssueSeverity.CRITICAL,
                Path("vuln.py"), 10, "SQL injection", "code"
            ),
            SecurityIssue(
                SecurityIssueType.HARDCODED_SECRET,
                IssueSeverity.HIGH,
                Path("secrets.py"), 5, "Hardcoded secret", "code"
            )
        ]
    
    @pytest.fixture
    def sample_performance_issues(self):
        """Create sample performance issues."""
        return [
            PerformanceIssue(
                PerformanceIssueType.BLOCKING_IO,
                IssueSeverity.HIGH,
                Path("slow.py"), 20, "Blocking I/O", "code"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_generate_security_alerts(self, alert_system, sample_security_issues):
        """Test generating security alerts."""
        alerts = await alert_system.generate_alerts(sample_security_issues, [])
        
        security_alerts = [a for a in alerts if a.alert_type == 'security']
        assert len(security_alerts) > 0
        assert any(a.severity == IssueSeverity.CRITICAL for a in security_alerts)
    
    @pytest.mark.asyncio
    async def test_generate_performance_alerts(self, alert_system, sample_performance_issues):
        """Test generating performance alerts."""
        alerts = await alert_system.generate_alerts([], sample_performance_issues)
        
        perf_alerts = [a for a in alerts if a.alert_type == 'performance']
        assert len(perf_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_generate_combined_alerts(
        self, alert_system, sample_security_issues, sample_performance_issues
    ):
        """Test generating alerts from both security and performance issues."""
        alerts = await alert_system.generate_alerts(
            sample_security_issues,
            sample_performance_issues
        )
        
        assert len(alerts) >= 2  # At least one security and one performance alert
        alert_types = {a.alert_type for a in alerts}
        assert 'security' in alert_types
        assert 'performance' in alert_types
    
    def test_get_alerts_by_severity(self, alert_system):
        """Test filtering alerts by severity."""
        alert_system.alerts = [
            ProactiveAlert(
                'security', IssueSeverity.CRITICAL,
                "Critical Alert", "Description", [], "Action"
            ),
            ProactiveAlert(
                'performance', IssueSeverity.HIGH,
                "High Alert", "Description", [], "Action"
            )
        ]
        
        critical_alerts = alert_system.get_alerts_by_severity(IssueSeverity.CRITICAL)
        assert len(critical_alerts) == 1


class TestAutoFixGenerator:
    """Test cases for AutoFixGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create an AutoFixGenerator instance."""
        return AutoFixGenerator()
    
    @pytest.fixture
    def sample_issues(self):
        """Create sample issues with fixes."""
        security_issues = [
            SecurityIssue(
                SecurityIssueType.INSECURE_RANDOM,
                IssueSeverity.MEDIUM,
                Path("test.py"), 10,
                "Insecure random", "import random",
                suggested_fix="Use secrets module"
            )
        ]
        
        performance_issues = [
            PerformanceIssue(
                PerformanceIssueType.INEFFICIENT_LOOP,
                IssueSeverity.MEDIUM,
                Path("test.py"), 20,
                "Inefficient loop", "for i in range(n):",
                suggested_fix="Use list comprehension"
            )
        ]
        
        return security_issues, performance_issues
    
    @pytest.mark.asyncio
    async def test_generate_fixes(self, generator, sample_issues):
        """Test generating fixes."""
        security_issues, performance_issues = sample_issues
        fixes = await generator.generate_fixes(security_issues, performance_issues)
        
        assert len(fixes) == 2
        assert all('suggested_fix' in fix for fix in fixes)
        assert all('issue_type' in fix for fix in fixes)
    
    @pytest.mark.asyncio
    async def test_auto_fixable_detection(self, generator, sample_issues):
        """Test detection of auto-fixable issues."""
        security_issues, performance_issues = sample_issues
        fixes = await generator.generate_fixes(security_issues, performance_issues)
        
        # Insecure random should be auto-fixable
        security_fixes = [f for f in fixes if f['issue_type'] == 'security']
        assert len(security_fixes) > 0


class TestSecurityPerformanceScanner:
    """Test cases for SecurityPerformanceScanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create a SecurityPerformanceScanner instance."""
        return SecurityPerformanceScanner()
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with various issues."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # File with security issue
        (project_root / "security_issue.py").write_text('''
password = "hardcoded_password"
''')
        
        # File with performance issue
        (project_root / "performance_issue.py").write_text('''
def slow_function():
    for i in range(100):
        for j in range(100):
            pass
''')
        
        return project_root
    
    @pytest.mark.asyncio
    async def test_scan_file(self, scanner, temp_project):
        """Test scanning a single file."""
        file_path = temp_project / "security_issue.py"
        result = await scanner.scan_file(file_path)
        
        assert 'file' in result
        assert 'security_issues' in result
        assert 'performance_issues' in result
        assert 'alerts' in result
        assert 'suggested_fixes' in result
    
    @pytest.mark.asyncio
    async def test_scan_codebase(self, scanner, temp_project):
        """Test scanning entire codebase."""
        result = await scanner.scan_codebase(temp_project)
        
        assert 'files_scanned' in result
        assert result['files_scanned'] == 2
        assert 'security_issues' in result
        assert 'performance_issues' in result
        assert 'alerts' in result
        assert 'suggested_fixes' in result
        
        # Should find at least one security issue
        assert result['security_issues']['total'] > 0
    
    def test_get_summary(self, scanner):
        """Test getting scanner summary."""
        scanner.security_scanner.detected_issues = [
            SecurityIssue(
                SecurityIssueType.HARDCODED_SECRET,
                IssueSeverity.HIGH,
                Path("test.py"), 1, "Secret", "code"
            )
        ]
        
        summary = scanner.get_summary()
        
        assert 'total_security_issues' in summary
        assert summary['total_security_issues'] == 1
        assert 'total_performance_issues' in summary
        assert 'active_alerts' in summary


class TestIntegration:
    """Integration tests for the complete scanning system."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a comprehensive test project."""
        project_root = tmp_path / "integration_test"
        project_root.mkdir()
        
        # Create a file with multiple types of issues
        (project_root / "complex_file.py").write_text('''
import random

API_KEY = "sk-1234567890"

def unsafe_query(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

async def blocking_operation():
    import requests
    response = requests.get("https://api.example.com")
    return response.json()

def nested_loops():
    for i in range(100):
        for j in range(100):
            for k in range(100):
                pass
''')
        
        return project_root
    
    @pytest.mark.asyncio
    async def test_comprehensive_scan(self, temp_project):
        """Test comprehensive scanning of a complex file."""
        scanner = SecurityPerformanceScanner()
        result = await scanner.scan_codebase(temp_project)
        
        # Should detect multiple types of issues
        assert result['security_issues']['total'] > 0
        assert result['performance_issues']['total'] > 0
        
        # Should generate alerts
        assert len(result['alerts']) > 0
        
        # Should suggest fixes
        assert len(result['suggested_fixes']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
