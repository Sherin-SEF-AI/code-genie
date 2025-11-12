"""
Comprehensive security framework for CodeGenie AI agents.
Provides agent isolation, encryption, access control, and audit logging.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from enum import Enum
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccessLevel(Enum):
    """Access levels for users and agents."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class ThreatLevel(Enum):
    """Threat levels for security events."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityContext:
    """Security context for operations."""
    user_id: str
    session_id: str
    agent_id: Optional[str] = None
    access_level: AccessLevel = AccessLevel.READ
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    permissions: Set[str] = field(default_factory=set)
    restrictions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class SecurityEvent:
    """Security event for audit logging."""
    event_id: str
    event_type: str
    user_id: str
    agent_id: Optional[str]
    resource: str
    action: str
    result: str
    threat_level: ThreatLevel
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class VulnerabilityReport:
    """Vulnerability scan report."""
    scan_id: str
    target: str
    scan_type: str
    vulnerabilities: List[Dict[str, Any]]
    risk_score: float
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class EncryptionManager:
    """Manages encryption for data at rest and in transit."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.master_key = self._generate_or_load_master_key()
        self.fernet = Fernet(self.master_key)
        self.rsa_private_key = self._generate_or_load_rsa_key()
        self.rsa_public_key = self.rsa_private_key.public_key()
    
    def _generate_or_load_master_key(self) -> bytes:
        """Generate or load master encryption key."""
        key_file = Path(self.config.get('key_file', 'master.key'))
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict permissions
            return key
    
    def _generate_or_load_rsa_key(self) -> rsa.RSAPrivateKey:
        """Generate or load RSA key pair."""
        key_file = Path(self.config.get('rsa_key_file', 'rsa_private.pem'))
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return serialization.load_pem_private_key(f.read(), password=None)
        else:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(pem)
            os.chmod(key_file, 0o600)
            
            return private_key
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """Encrypt data using symmetric encryption."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self.fernet.encrypt(data)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption."""
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    
    def encrypt_with_rsa(self, data: Union[str, bytes]) -> str:
        """Encrypt data using RSA public key."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self.rsa_public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_with_rsa(self, encrypted_data: str) -> str:
        """Decrypt data using RSA private key."""
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted = self.rsa_private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode('utf-8')
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=100000,
        )
        key = kdf.derive(password.encode('utf-8'))
        return base64.b64encode(key).decode('utf-8'), salt
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode('utf-8'),
                iterations=100000,
            )
            kdf.verify(password.encode('utf-8'), base64.b64decode(hashed.encode('utf-8')))
            return True
        except Exception:
            return False


class AccessControlManager:
    """Manages access control and permissions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.permissions_db: Dict[str, Dict[str, Any]] = {}
        self.role_permissions: Dict[str, Set[str]] = {
            'user': {'read', 'write'},
            'developer': {'read', 'write', 'execute'},
            'admin': {'read', 'write', 'execute', 'manage_users', 'manage_agents'},
            'system': {'*'}  # All permissions
        }
        self.active_sessions: Dict[str, SecurityContext] = {}
    
    def create_security_context(
        self,
        user_id: str,
        role: str = 'user',
        agent_id: Optional[str] = None,
        duration_hours: int = 24
    ) -> SecurityContext:
        """Create a new security context."""
        session_id = secrets.token_urlsafe(32)
        
        permissions = self.role_permissions.get(role, set())
        if '*' in permissions:
            permissions = set(self.role_permissions.keys())
        
        expires_at = datetime.now() + timedelta(hours=duration_hours)
        
        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id,
            access_level=AccessLevel.READ if role == 'user' else AccessLevel.ADMIN,
            permissions=permissions,
            expires_at=expires_at
        )
        
        self.active_sessions[session_id] = context
        return context
    
    def validate_context(self, session_id: str) -> Optional[SecurityContext]:
        """Validate and return security context."""
        context = self.active_sessions.get(session_id)
        
        if not context:
            return None
        
        if context.expires_at and datetime.now() > context.expires_at:
            del self.active_sessions[session_id]
            return None
        
        return context
    
    def check_permission(self, context: SecurityContext, permission: str, resource: str = "") -> bool:
        """Check if context has permission for resource."""
        if '*' in context.permissions:
            return True
        
        if permission in context.permissions:
            return True
        
        # Check resource-specific permissions
        resource_permission = f"{permission}:{resource}"
        if resource_permission in context.permissions:
            return True
        
        return False
    
    def grant_permission(self, user_id: str, permission: str, resource: str = "") -> None:
        """Grant permission to user."""
        if user_id not in self.permissions_db:
            self.permissions_db[user_id] = {'permissions': set()}
        
        perm = f"{permission}:{resource}" if resource else permission
        self.permissions_db[user_id]['permissions'].add(perm)
    
    def revoke_permission(self, user_id: str, permission: str, resource: str = "") -> None:
        """Revoke permission from user."""
        if user_id not in self.permissions_db:
            return
        
        perm = f"{permission}:{resource}" if resource else permission
        self.permissions_db[user_id]['permissions'].discard(perm)
    
    def invalidate_session(self, session_id: str) -> None:
        """Invalidate a session."""
        self.active_sessions.pop(session_id, None)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        now = datetime.now()
        expired = [
            sid for sid, ctx in self.active_sessions.items()
            if ctx.expires_at and now > ctx.expires_at
        ]
        
        for sid in expired:
            del self.active_sessions[sid]
        
        return len(expired)


class AuditLogger:
    """Comprehensive audit logging system."""
    
    def __init__(self, config: Dict[str, Any], encryption_manager: EncryptionManager):
        self.config = config
        self.encryption_manager = encryption_manager
        self.log_file = Path(config.get('audit_log_file', 'audit.log'))
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[SecurityEvent] = []
        self.max_events_in_memory = config.get('max_events_in_memory', 1000)
    
    def log_event(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        result: str,
        threat_level: ThreatLevel = ThreatLevel.INFO,
        agent_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Log a security event."""
        event_id = secrets.token_urlsafe(16)
        
        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            agent_id=agent_id,
            resource=resource,
            action=action,
            result=result,
            threat_level=threat_level,
            details=details or {},
            source_ip=source_ip,
            user_agent=user_agent
        )
        
        # Add to memory
        self.events.append(event)
        
        # Maintain memory limit
        if len(self.events) > self.max_events_in_memory:
            self.events = self.events[-self.max_events_in_memory:]
        
        # Write to file (encrypted)
        self._write_event_to_file(event)
        
        # Alert on high-threat events
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            self._send_security_alert(event)
        
        return event_id
    
    def _write_event_to_file(self, event: SecurityEvent) -> None:
        """Write event to encrypted log file."""
        try:
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'user_id': event.user_id,
                'agent_id': event.agent_id,
                'resource': event.resource,
                'action': event.action,
                'result': event.result,
                'threat_level': event.threat_level.value,
                'details': event.details,
                'timestamp': event.timestamp.isoformat(),
                'source_ip': event.source_ip,
                'user_agent': event.user_agent
            }
            
            encrypted_data = self.encryption_manager.encrypt_data(json.dumps(event_data))
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{encrypted_data}\n")
                
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")
    
    def _send_security_alert(self, event: SecurityEvent) -> None:
        """Send security alert for high-threat events."""
        logger.warning(f"SECURITY ALERT: {event.event_type} - {event.threat_level.value}")
        logger.warning(f"User: {event.user_id}, Resource: {event.resource}, Action: {event.action}")
        logger.warning(f"Details: {event.details}")
    
    def query_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        threat_level: Optional[ThreatLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Query security events with filters."""
        filtered_events = self.events
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        
        if threat_level:
            filtered_events = [e for e in filtered_events if e.threat_level == threat_level]
        
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
        
        return filtered_events[-limit:]
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security summary for the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        
        threat_counts = {}
        event_type_counts = {}
        user_activity = {}
        
        for event in recent_events:
            # Count by threat level
            threat_level = event.threat_level.value
            threat_counts[threat_level] = threat_counts.get(threat_level, 0) + 1
            
            # Count by event type
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
            
            # Count by user
            user_activity[event.user_id] = user_activity.get(event.user_id, 0) + 1
        
        return {
            'period_hours': hours,
            'total_events': len(recent_events),
            'threat_level_counts': threat_counts,
            'event_type_counts': event_type_counts,
            'top_users': sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10],
            'high_threat_events': len([e for e in recent_events if e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]])
        }


class VulnerabilityScanner:
    """Scans for security vulnerabilities in code and configurations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.scan_history: List[VulnerabilityReport] = []
    
    def _load_vulnerability_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load vulnerability detection patterns."""
        return {
            'python': [
                {
                    'pattern': r'eval\s*\(',
                    'severity': 'high',
                    'description': 'Use of eval() can lead to code injection',
                    'recommendation': 'Use ast.literal_eval() or avoid dynamic code execution'
                },
                {
                    'pattern': r'exec\s*\(',
                    'severity': 'high',
                    'description': 'Use of exec() can lead to code injection',
                    'recommendation': 'Avoid dynamic code execution'
                },
                {
                    'pattern': r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
                    'severity': 'medium',
                    'description': 'Shell injection vulnerability',
                    'recommendation': 'Use shell=False or validate input'
                },
                {
                    'pattern': r'pickle\.loads?\s*\(',
                    'severity': 'high',
                    'description': 'Pickle deserialization can execute arbitrary code',
                    'recommendation': 'Use json or other safe serialization formats'
                },
                {
                    'pattern': r'input\s*\([^)]*\)',
                    'severity': 'low',
                    'description': 'User input without validation',
                    'recommendation': 'Validate and sanitize user input'
                }
            ],
            'javascript': [
                {
                    'pattern': r'eval\s*\(',
                    'severity': 'high',
                    'description': 'Use of eval() can lead to code injection',
                    'recommendation': 'Use JSON.parse() or avoid dynamic code execution'
                },
                {
                    'pattern': r'innerHTML\s*=',
                    'severity': 'medium',
                    'description': 'Potential XSS vulnerability',
                    'recommendation': 'Use textContent or sanitize HTML'
                },
                {
                    'pattern': r'document\.write\s*\(',
                    'severity': 'medium',
                    'description': 'Potential XSS vulnerability',
                    'recommendation': 'Use safer DOM manipulation methods'
                }
            ],
            'sql': [
                {
                    'pattern': r'SELECT\s+.*\+.*FROM',
                    'severity': 'high',
                    'description': 'Potential SQL injection',
                    'recommendation': 'Use parameterized queries'
                },
                {
                    'pattern': r'INSERT\s+.*\+.*VALUES',
                    'severity': 'high',
                    'description': 'Potential SQL injection',
                    'recommendation': 'Use parameterized queries'
                }
            ]
        }
    
    async def scan_code(self, code: str, language: str) -> VulnerabilityReport:
        """Scan code for vulnerabilities."""
        scan_id = secrets.token_urlsafe(16)
        vulnerabilities = []
        
        patterns = self.vulnerability_patterns.get(language.lower(), [])
        
        for pattern_info in patterns:
            import re
            matches = re.finditer(pattern_info['pattern'], code, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                vulnerabilities.append({
                    'type': 'code_vulnerability',
                    'severity': pattern_info['severity'],
                    'description': pattern_info['description'],
                    'recommendation': pattern_info['recommendation'],
                    'line': line_num,
                    'match': match.group(),
                    'pattern': pattern_info['pattern']
                })
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(vulnerabilities)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(vulnerabilities)
        
        report = VulnerabilityReport(
            scan_id=scan_id,
            target=f"{language}_code",
            scan_type="static_analysis",
            vulnerabilities=vulnerabilities,
            risk_score=risk_score,
            recommendations=recommendations
        )
        
        self.scan_history.append(report)
        return report
    
    async def scan_file(self, file_path: Path) -> VulnerabilityReport:
        """Scan a file for vulnerabilities."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            language = self._detect_language(file_path)
            report = await self.scan_code(code, language)
            report.target = str(file_path)
            
            return report
            
        except Exception as e:
            return VulnerabilityReport(
                scan_id=secrets.token_urlsafe(16),
                target=str(file_path),
                scan_type="file_scan",
                vulnerabilities=[{
                    'type': 'scan_error',
                    'severity': 'low',
                    'description': f'Failed to scan file: {str(e)}',
                    'recommendation': 'Check file permissions and format'
                }],
                risk_score=0.0,
                recommendations=['Fix file access issues']
            )
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.sql': 'sql',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }
        return extension_map.get(file_path.suffix.lower(), 'unknown')
    
    def _calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score."""
        if not vulnerabilities:
            return 0.0
        
        severity_weights = {
            'low': 1.0,
            'medium': 3.0,
            'high': 7.0,
            'critical': 10.0
        }
        
        total_score = sum(severity_weights.get(v.get('severity', 'low'), 1.0) for v in vulnerabilities)
        max_possible = len(vulnerabilities) * 10.0
        
        return min(total_score / max_possible * 100, 100.0) if max_possible > 0 else 0.0
    
    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations."""
        recommendations = set()
        
        for vuln in vulnerabilities:
            recommendations.add(vuln.get('recommendation', 'Review and fix security issue'))
        
        # Add general recommendations
        if vulnerabilities:
            recommendations.add('Implement regular security scanning in CI/CD pipeline')
            recommendations.add('Use static analysis tools for continuous monitoring')
            recommendations.add('Provide security training for development team')
        
        return list(recommendations)


class SecurityFramework:
    """Main security framework coordinating all security components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.encryption_manager = EncryptionManager(config.get('encryption', {}))
        self.access_control = AccessControlManager(config.get('access_control', {}))
        self.audit_logger = AuditLogger(config.get('audit', {}), self.encryption_manager)
        self.vulnerability_scanner = VulnerabilityScanner(config.get('vulnerability_scanner', {}))
        
        # Initialize security monitoring
        self._start_security_monitoring()
    
    def _start_security_monitoring(self) -> None:
        """Start background security monitoring tasks."""
        asyncio.create_task(self._periodic_cleanup())
        asyncio.create_task(self._security_health_check())
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired sessions and old logs."""
        while True:
            try:
                # Clean up expired sessions
                expired_count = self.access_control.cleanup_expired_sessions()
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _security_health_check(self) -> None:
        """Periodic security health check."""
        while True:
            try:
                # Check for security anomalies
                summary = self.audit_logger.get_security_summary(hours=1)
                
                if summary['high_threat_events'] > 10:
                    self.audit_logger.log_event(
                        'security_alert',
                        'system',
                        'security_framework',
                        'health_check',
                        'high_threat_activity_detected',
                        ThreatLevel.HIGH,
                        details={'high_threat_count': summary['high_threat_events']}
                    )
                
                # Wait 15 minutes before next check
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Error in security health check: {e}")
                await asyncio.sleep(300)
    
    async def secure_operation(
        self,
        context: SecurityContext,
        operation: str,
        resource: str,
        operation_func,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with full security controls."""
        
        # Check permissions
        if not self.access_control.check_permission(context, operation, resource):
            self.audit_logger.log_event(
                'access_denied',
                context.user_id,
                resource,
                operation,
                'permission_denied',
                ThreatLevel.MEDIUM,
                agent_id=context.agent_id
            )
            raise PermissionError(f"Access denied for {operation} on {resource}")
        
        # Log operation start
        self.audit_logger.log_event(
            'operation_start',
            context.user_id,
            resource,
            operation,
            'started',
            ThreatLevel.INFO,
            agent_id=context.agent_id
        )
        
        try:
            # Execute operation
            result = await operation_func(*args, **kwargs)
            
            # Log success
            self.audit_logger.log_event(
                'operation_complete',
                context.user_id,
                resource,
                operation,
                'success',
                ThreatLevel.INFO,
                agent_id=context.agent_id
            )
            
            return result
            
        except Exception as e:
            # Log failure
            self.audit_logger.log_event(
                'operation_failed',
                context.user_id,
                resource,
                operation,
                'failed',
                ThreatLevel.MEDIUM,
                agent_id=context.agent_id,
                details={'error': str(e)}
            )
            raise
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status."""
        return {
            'active_sessions': len(self.access_control.active_sessions),
            'audit_summary': self.audit_logger.get_security_summary(),
            'recent_scans': len(self.vulnerability_scanner.scan_history),
            'encryption_status': 'active',
            'monitoring_status': 'active'
        }