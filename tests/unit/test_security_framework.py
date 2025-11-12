"""
Unit tests for the security framework components.
"""

import asyncio
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.codegenie.core.security_framework import (
    SecurityFramework,
    EncryptionManager,
    AccessControlManager,
    AuditLogger,
    VulnerabilityScanner,
    SecurityContext,
    SecurityEvent,
    ThreatLevel,
    AccessLevel,
    SecurityLevel
)


class TestEncryptionManager:
    """Test encryption manager functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def encryption_manager(self, temp_dir):
        config = {
            'key_file': temp_dir / 'master.key',
            'rsa_key_file': temp_dir / 'rsa_private.pem'
        }
        return EncryptionManager(config)
    
    def test_encrypt_decrypt_data(self, encryption_manager):
        """Test symmetric encryption and decryption."""
        original_data = "sensitive information"
        
        encrypted = encryption_manager.encrypt_data(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, str)
        
        decrypted = encryption_manager.decrypt_data(encrypted)
        assert decrypted == original_data
    
    def test_encrypt_decrypt_rsa(self, encryption_manager):
        """Test RSA encryption and decryption."""
        original_data = "secret message"
        
        encrypted = encryption_manager.encrypt_with_rsa(original_data)
        assert encrypted != original_data
        assert isinstance(encrypted, str)
        
        decrypted = encryption_manager.decrypt_with_rsa(encrypted)
        assert decrypted == original_data
    
    def test_password_hashing(self, encryption_manager):
        """Test password hashing and verification."""
        password = "secure_password123"
        
        hashed, salt = encryption_manager.hash_password(password)
        assert hashed != password
        assert len(salt) > 0
        
        # Verify correct password
        assert encryption_manager.verify_password(password, hashed, salt)
        
        # Verify incorrect password
        assert not encryption_manager.verify_password("wrong_password", hashed, salt)
    
    def test_secure_token_generation(self, encryption_manager):
        """Test secure token generation."""
        token1 = encryption_manager.generate_secure_token()
        token2 = encryption_manager.generate_secure_token()
        
        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0
    
    def test_key_persistence(self, temp_dir):
        """Test that keys are persisted and reloaded correctly."""
        config = {
            'key_file': temp_dir / 'master.key',
            'rsa_key_file': temp_dir / 'rsa_private.pem'
        }
        
        # Create first manager
        manager1 = EncryptionManager(config)
        original_data = "test data"
        encrypted = manager1.encrypt_data(original_data)
        
        # Create second manager with same config
        manager2 = EncryptionManager(config)
        decrypted = manager2.decrypt_data(encrypted)
        
        assert decrypted == original_data


class TestAccessControlManager:
    """Test access control manager functionality."""
    
    @pytest.fixture
    def access_manager(self):
        config = {}
        return AccessControlManager(config)
    
    def test_create_security_context(self, access_manager):
        """Test security context creation."""
        context = access_manager.create_security_context(
            user_id="test_user",
            role="developer",
            agent_id="test_agent"
        )
        
        assert context.user_id == "test_user"
        assert context.agent_id == "test_agent"
        assert len(context.session_id) > 0
        assert context.expires_at is not None
        assert 'read' in context.permissions
        assert 'write' in context.permissions
    
    def test_validate_context(self, access_manager):
        """Test context validation."""
        # Create valid context
        context = access_manager.create_security_context("test_user")
        
        # Should validate successfully
        validated = access_manager.validate_context(context.session_id)
        assert validated is not None
        assert validated.user_id == "test_user"
        
        # Invalid session ID should return None
        invalid = access_manager.validate_context("invalid_session")
        assert invalid is None
    
    def test_expired_context(self, access_manager):
        """Test expired context handling."""
        # Create context with short expiration
        context = access_manager.create_security_context(
            "test_user", 
            duration_hours=-1  # Already expired
        )
        
        # Should not validate
        validated = access_manager.validate_context(context.session_id)
        assert validated is None
    
    def test_permission_checking(self, access_manager):
        """Test permission checking."""
        context = access_manager.create_security_context("test_user", "developer")
        
        # Should have basic permissions
        assert access_manager.check_permission(context, "read")
        assert access_manager.check_permission(context, "write")
        assert access_manager.check_permission(context, "execute")
        
        # Should not have admin permissions
        assert not access_manager.check_permission(context, "manage_users")
    
    def test_permission_management(self, access_manager):
        """Test granting and revoking permissions."""
        user_id = "test_user"
        
        # Grant permission
        access_manager.grant_permission(user_id, "special_action")
        
        # Check permission exists
        assert user_id in access_manager.permissions_db
        assert "special_action" in access_manager.permissions_db[user_id]['permissions']
        
        # Revoke permission
        access_manager.revoke_permission(user_id, "special_action")
        assert "special_action" not in access_manager.permissions_db[user_id]['permissions']
    
    def test_session_cleanup(self, access_manager):
        """Test expired session cleanup."""
        # Create expired context
        context = access_manager.create_security_context(
            "test_user",
            duration_hours=-1
        )
        
        # Should be in active sessions
        assert context.session_id in access_manager.active_sessions
        
        # Cleanup should remove it
        cleaned = access_manager.cleanup_expired_sessions()
        assert cleaned == 1
        assert context.session_id not in access_manager.active_sessions


class TestAuditLogger:
    """Test audit logging functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def encryption_manager(self, temp_dir):
        config = {
            'key_file': temp_dir / 'master.key',
            'rsa_key_file': temp_dir / 'rsa_private.pem'
        }
        return EncryptionManager(config)
    
    @pytest.fixture
    def audit_logger(self, temp_dir, encryption_manager):
        config = {
            'audit_log_file': temp_dir / 'audit.log',
            'max_events_in_memory': 100
        }
        return AuditLogger(config, encryption_manager)
    
    def test_log_event(self, audit_logger):
        """Test event logging."""
        event_id = audit_logger.log_event(
            event_type="test_event",
            user_id="test_user",
            resource="test_resource",
            action="test_action",
            result="success",
            threat_level=ThreatLevel.INFO
        )
        
        assert len(event_id) > 0
        assert len(audit_logger.events) == 1
        
        event = audit_logger.events[0]
        assert event.event_type == "test_event"
        assert event.user_id == "test_user"
        assert event.resource == "test_resource"
        assert event.action == "test_action"
        assert event.result == "success"
        assert event.threat_level == ThreatLevel.INFO
    
    def test_query_events(self, audit_logger):
        """Test event querying."""
        # Log multiple events
        audit_logger.log_event("event1", "user1", "resource1", "action1", "success")
        audit_logger.log_event("event2", "user2", "resource2", "action2", "failure")
        audit_logger.log_event("event1", "user1", "resource3", "action3", "success")
        
        # Query by user
        user1_events = audit_logger.query_events(user_id="user1")
        assert len(user1_events) == 2
        assert all(event.user_id == "user1" for event in user1_events)
        
        # Query by event type
        event1_events = audit_logger.query_events(event_type="event1")
        assert len(event1_events) == 2
        assert all(event.event_type == "event1" for event in event1_events)
    
    def test_security_summary(self, audit_logger):
        """Test security summary generation."""
        # Log events with different threat levels
        audit_logger.log_event("event1", "user1", "resource1", "action1", "success", ThreatLevel.INFO)
        audit_logger.log_event("event2", "user2", "resource2", "action2", "failure", ThreatLevel.HIGH)
        audit_logger.log_event("event3", "user3", "resource3", "action3", "success", ThreatLevel.CRITICAL)
        
        summary = audit_logger.get_security_summary(hours=24)
        
        assert summary['total_events'] == 3
        assert summary['threat_level_counts']['info'] == 1
        assert summary['threat_level_counts']['high'] == 1
        assert summary['threat_level_counts']['critical'] == 1
        assert summary['high_threat_events'] == 2
    
    @patch('src.codegenie.core.security_framework.logger')
    def test_security_alert(self, mock_logger, audit_logger):
        """Test security alert generation."""
        # Log high-threat event
        audit_logger.log_event(
            "security_breach",
            "attacker",
            "sensitive_data",
            "unauthorized_access",
            "success",
            ThreatLevel.CRITICAL
        )
        
        # Should trigger security alert
        mock_logger.warning.assert_called()


class TestVulnerabilityScanner:
    """Test vulnerability scanner functionality."""
    
    @pytest.fixture
    def scanner(self):
        config = {}
        return VulnerabilityScanner(config)
    
    @pytest.mark.asyncio
    async def test_scan_python_code(self, scanner):
        """Test Python code vulnerability scanning."""
        vulnerable_code = """
import os
password = "hardcoded_password"
user_input = input("Enter command: ")
os.system(user_input)
eval(user_input)
"""
        
        report = await scanner.scan_code(vulnerable_code, "python")
        
        assert report.target == "python_code"
        assert len(report.vulnerabilities) > 0
        assert report.risk_score > 0
        
        # Check for specific vulnerabilities
        vuln_types = [v['type'] for v in report.vulnerabilities]
        assert 'code_vulnerability' in vuln_types
    
    @pytest.mark.asyncio
    async def test_scan_javascript_code(self, scanner):
        """Test JavaScript code vulnerability scanning."""
        vulnerable_code = """
var userInput = document.getElementById('input').value;
document.innerHTML = userInput;
eval(userInput);
"""
        
        report = await scanner.scan_code(vulnerable_code, "javascript")
        
        assert len(report.vulnerabilities) > 0
        assert any('eval' in v['description'].lower() for v in report.vulnerabilities)
    
    @pytest.mark.asyncio
    async def test_scan_file(self, scanner, temp_dir):
        """Test file scanning."""
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("eval('malicious code')")
        
        report = await scanner.scan_file(test_file)
        
        assert report.target == str(test_file)
        assert len(report.vulnerabilities) > 0
    
    def test_risk_score_calculation(self, scanner):
        """Test risk score calculation."""
        # High severity vulnerabilities
        high_vulns = [
            {'severity': 'high'},
            {'severity': 'critical'},
            {'severity': 'medium'}
        ]
        
        score = scanner._calculate_risk_score(high_vulns)
        assert score > 50  # Should be high risk
        
        # Low severity vulnerabilities
        low_vulns = [
            {'severity': 'low'},
            {'severity': 'low'}
        ]
        
        score = scanner._calculate_risk_score(low_vulns)
        assert score < 50  # Should be lower risk
    
    def test_language_detection(self, scanner):
        """Test programming language detection."""
        assert scanner._detect_language(Path("test.py")) == "python"
        assert scanner._detect_language(Path("test.js")) == "javascript"
        assert scanner._detect_language(Path("test.java")) == "java"
        assert scanner._detect_language(Path("test.unknown")) == "unknown"


class TestSecurityFramework:
    """Test main security framework integration."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def security_framework(self, temp_dir):
        config = {
            'encryption': {
                'key_file': temp_dir / 'master.key',
                'rsa_key_file': temp_dir / 'rsa_private.pem'
            },
            'access_control': {},
            'audit': {
                'audit_log_file': temp_dir / 'audit.log'
            },
            'vulnerability_scanner': {}
        }
        return SecurityFramework(config)
    
    def test_initialization(self, security_framework):
        """Test security framework initialization."""
        assert security_framework.encryption_manager is not None
        assert security_framework.access_control is not None
        assert security_framework.audit_logger is not None
        assert security_framework.vulnerability_scanner is not None
    
    @pytest.mark.asyncio
    async def test_secure_operation(self, security_framework):
        """Test secure operation execution."""
        # Create security context
        context = security_framework.access_control.create_security_context(
            "test_user", "admin"
        )
        
        # Define test operation
        async def test_operation():
            return "operation_result"
        
        # Execute secure operation
        result = await security_framework.secure_operation(
            context,
            "test_operation",
            "test_resource",
            test_operation
        )
        
        assert result == "operation_result"
        
        # Check that audit events were logged
        assert len(security_framework.audit_logger.events) >= 2  # start and complete
    
    @pytest.mark.asyncio
    async def test_secure_operation_permission_denied(self, security_framework):
        """Test secure operation with insufficient permissions."""
        # Create limited context
        context = security_framework.access_control.create_security_context(
            "test_user", "user"  # Limited permissions
        )
        
        async def admin_operation():
            return "admin_result"
        
        # Should raise permission error
        with pytest.raises(PermissionError):
            await security_framework.secure_operation(
                context,
                "admin_operation",
                "admin_resource",
                admin_operation
            )
    
    def test_security_status(self, security_framework):
        """Test security status reporting."""
        status = security_framework.get_security_status()
        
        assert 'active_sessions' in status
        assert 'audit_summary' in status
        assert 'recent_scans' in status
        assert 'encryption_status' in status
        assert 'monitoring_status' in status
        
        assert status['encryption_status'] == 'active'
        assert status['monitoring_status'] == 'active'


# Performance tests for security components
class TestSecurityPerformance:
    """Performance tests for security components."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def encryption_manager(self, temp_dir):
        config = {
            'key_file': temp_dir / 'master.key',
            'rsa_key_file': temp_dir / 'rsa_private.pem'
        }
        return EncryptionManager(config)
    
    def test_encryption_performance(self, encryption_manager):
        """Test encryption performance with large data."""
        import time
        
        # Test with 1MB of data
        large_data = "x" * (1024 * 1024)
        
        start_time = time.time()
        encrypted = encryption_manager.encrypt_data(large_data)
        encryption_time = time.time() - start_time
        
        start_time = time.time()
        decrypted = encryption_manager.decrypt_data(encrypted)
        decryption_time = time.time() - start_time
        
        assert decrypted == large_data
        assert encryption_time < 1.0  # Should encrypt 1MB in under 1 second
        assert decryption_time < 1.0  # Should decrypt 1MB in under 1 second
    
    @pytest.mark.asyncio
    async def test_vulnerability_scanning_performance(self):
        """Test vulnerability scanning performance."""
        import time
        
        scanner = VulnerabilityScanner({})
        
        # Large code sample
        large_code = """
def process_data(user_input):
    # This is a large code sample for performance testing
    """ + "\n".join([f"    line_{i} = 'code line {i}'" for i in range(1000)])
        
        start_time = time.time()
        report = await scanner.scan_code(large_code, "python")
        scan_time = time.time() - start_time
        
        assert scan_time < 5.0  # Should scan large code in under 5 seconds
        assert report is not None
    
    def test_audit_logging_performance(self, temp_dir):
        """Test audit logging performance."""
        import time
        
        encryption_manager = EncryptionManager({
            'key_file': temp_dir / 'master.key',
            'rsa_key_file': temp_dir / 'rsa_private.pem'
        })
        
        audit_logger = AuditLogger({
            'audit_log_file': temp_dir / 'audit.log'
        }, encryption_manager)
        
        # Log many events
        start_time = time.time()
        for i in range(100):
            audit_logger.log_event(
                f"event_{i}",
                f"user_{i}",
                f"resource_{i}",
                f"action_{i}",
                "success"
            )
        logging_time = time.time() - start_time
        
        assert logging_time < 2.0  # Should log 100 events in under 2 seconds
        assert len(audit_logger.events) == 100


if __name__ == "__main__":
    pytest.main([__file__])