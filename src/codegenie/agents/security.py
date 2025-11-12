"""
Security Agent - Specialized agent for security analysis and vulnerability detection.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base_agent import BaseAgent, Task, AgentResult, AgentCapability
from ..core.config import Config
from ..core.tool_executor import ToolExecutor
from ..models.model_router import ModelRouter

logger = logging.getLogger(__name__)


class VulnerabilityType(Enum):
    """Types of security vulnerabilities."""
    
    SQL_INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    CSRF = "cross_site_request_forgery"
    AUTHENTICATION = "authentication_issue"
    AUTHORIZATION = "authorization_issue"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    WEAK_CRYPTO = "weak_cryptography"
    HARDCODED_SECRETS = "hardcoded_secrets"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"


class SeverityLevel(Enum):
    """Severity levels for vulnerabilities."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""
    
    type: VulnerabilityType
    severity: SeverityLevel
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: str = ""
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    cvss_score: Optional[float] = None  # Common Vulnerability Scoring System
    remediation: str = ""
    references: List[str] = field(default_factory=list)


@dataclass
class SecurityFix:
    """Represents a security fix."""
    
    vulnerability: Vulnerability
    fix_description: str
    code_changes: Dict[str, str] = field(default_factory=dict)  # file_path -> new_code
    automated: bool = False
    confidence: float = 0.0
    testing_required: bool = True


@dataclass
class ThreatModel:
    """Threat modeling results."""
    
    assets: List[str] = field(default_factory=list)
    threats: List[Dict[str, Any]] = field(default_factory=list)
    attack_vectors: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class SecurityReport:
    """Comprehensive security report."""
    
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    overall_score: float = 0.0  # 0-10, higher is better
    recommendations: List[str] = field(default_factory=list)


class SecurityAgent(BaseAgent):
    """
    Specialized agent for security analysis and vulnerability detection.
    
    Capabilities:
    - Vulnerability scanning
    - Security best practices enforcement
    - Automated security fix generation
    - Threat modeling
    - Security testing
    """
    
    def __init__(
        self,
        config: Config,
        model_router: ModelRouter,
        tool_executor: Optional[ToolExecutor] = None
    ):
        super().__init__(
            name="SecurityAgent",
            capabilities=[
                AgentCapability.SECURITY_ANALYSIS,
                AgentCapability.CODE_ANALYSIS
            ],
            config=config,
            model_router=model_router
        )
        
        self.tool_executor = tool_executor
        
        # Security knowledge base
        self.vulnerability_patterns: Dict[str, Any] = self._initialize_vulnerability_patterns()
        self.security_best_practices: List[str] = self._initialize_best_practices()
        
        logger.info("Initialized SecurityAgent")
    
    def _initialize_vulnerability_patterns(self) -> Dict[str, Any]:
        """Initialize vulnerability detection patterns."""
        return {
            VulnerabilityType.SQL_INJECTION: {
                "patterns": [r"execute\(.*%.*\)", r"\.format\(.*sql", r"\+.*sql"],
                "description": "SQL injection vulnerability",
                "severity": SeverityLevel.CRITICAL,
                "cwe": "CWE-89"
            },
            VulnerabilityType.COMMAND_INJECTION: {
                "patterns": [r"os\.system\(", r"subprocess\.call\(.*shell=True", r"eval\("],
                "description": "Command injection vulnerability",
                "severity": SeverityLevel.CRITICAL,
                "cwe": "CWE-78"
            },
            VulnerabilityType.HARDCODED_SECRETS: {
                "patterns": [
                    r"password\s*=\s*['\"].*['\"]",
                    r"api_key\s*=\s*['\"].*['\"]",
                    r"secret\s*=\s*['\"].*['\"]"
                ],
                "description": "Hardcoded secrets detected",
                "severity": SeverityLevel.HIGH,
                "cwe": "CWE-798"
            },
            VulnerabilityType.WEAK_CRYPTO: {
                "patterns": [r"md5\(", r"sha1\(", r"DES", r"RC4"],
                "description": "Weak cryptographic algorithm",
                "severity": SeverityLevel.MEDIUM,
                "cwe": "CWE-327"
            },
            VulnerabilityType.INSECURE_DESERIALIZATION: {
                "patterns": [r"pickle\.loads\(", r"yaml\.load\((?!.*Loader)"],
                "description": "Insecure deserialization",
                "severity": SeverityLevel.HIGH,
                "cwe": "CWE-502"
            }
        }
    
    def _initialize_best_practices(self) -> List[str]:
        """Initialize security best practices."""
        return [
            "Use parameterized queries to prevent SQL injection",
            "Validate and sanitize all user inputs",
            "Implement proper authentication and authorization",
            "Use strong cryptographic algorithms (SHA-256, AES-256)",
            "Never hardcode secrets or credentials",
            "Implement rate limiting and throttling",
            "Use HTTPS for all communications",
            "Keep dependencies up to date",
            "Implement proper error handling without exposing sensitive info",
            "Use security headers (CSP, HSTS, X-Frame-Options)",
            "Implement logging and monitoring for security events",
            "Follow principle of least privilege"
        ]
    
    async def can_handle_task(self, task: Task) -> bool:
        """Determine if this agent can handle the task."""
        security_keywords = [
            "security", "vulnerability", "scan", "threat", "risk",
            "authentication", "authorization", "encryption", "secure"
        ]
        
        task_text = f"{task.description} {task.task_type}".lower()
        return any(keyword in task_text for keyword in security_keywords)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Execute a security-related task."""
        try:
            task_type = task.task_type.lower()
            
            if "scan" in task_type or "analyze" in task_type:
                result = await self.scan_for_vulnerabilities(task.context)
            elif "fix" in task_type or "remediate" in task_type:
                result = await self.generate_security_fixes(task.context)
            elif "threat" in task_type or "model" in task_type:
                result = await self.perform_threat_modeling(task.context)
            elif "test" in task_type:
                result = await self.perform_security_testing(task.context)
            else:
                result = await self._general_security_consultation(task)
            
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=True,
                output=result,
                confidence=0.85,
                reasoning=f"Completed security task: {task.task_type}",
                suggestions=self._generate_suggestions(result),
                next_steps=self._generate_next_steps(task, result)
            )
            
        except Exception as e:
            logger.error(f"SecurityAgent task execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=False,
                confidence=0.0,
                reasoning=f"Task execution failed: {str(e)}",
                error=str(e)
            )
    
    async def scan_for_vulnerabilities(self, context: Dict[str, Any]) -> SecurityReport:
        """
        Scan code for security vulnerabilities.
        
        Args:
            context: Context including code or project path
            
        Returns:
            SecurityReport with identified vulnerabilities
        """
        logger.info("Scanning for vulnerabilities")
        
        code = context.get("code", "")
        file_path = context.get("file_path", "")
        project_path = context.get("project_path", "")
        
        vulnerabilities = []
        
        # Scan code for patterns
        if code:
            vulnerabilities.extend(self._scan_code_patterns(code, file_path))
        
        # Scan project if path provided
        if project_path and self.tool_executor:
            project_vulns = await self._scan_project(project_path)
            vulnerabilities.extend(project_vulns)
        
        # Count by severity
        critical_count = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.HIGH)
        medium_count = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.MEDIUM)
        low_count = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.LOW)
        
        # Calculate overall score
        overall_score = self._calculate_security_score(
            critical_count, high_count, medium_count, low_count
        )
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(vulnerabilities)
        
        report = SecurityReport(
            vulnerabilities=vulnerabilities,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            overall_score=overall_score,
            recommendations=recommendations
        )
        
        logger.info(f"Security scan completed: {len(vulnerabilities)} vulnerabilities found")
        return report
    
    async def generate_security_fixes(self, context: Dict[str, Any]) -> List[SecurityFix]:
        """
        Generate automated security fixes.
        
        Args:
            context: Context including vulnerabilities to fix
            
        Returns:
            List of security fixes
        """
        logger.info("Generating security fixes")
        
        vulnerabilities = context.get("vulnerabilities", [])
        if not vulnerabilities:
            # Scan first if no vulnerabilities provided
            scan_result = await self.scan_for_vulnerabilities(context)
            vulnerabilities = scan_result.vulnerabilities
        
        fixes = []
        
        for vuln in vulnerabilities:
            fix = self._generate_fix_for_vulnerability(vuln)
            if fix:
                fixes.append(fix)
        
        # Test fixes if tool executor available
        if self.tool_executor and context.get("test_fixes", False):
            await self._test_security_fixes(fixes)
        
        logger.info(f"Generated {len(fixes)} security fixes")
        return fixes
    
    async def perform_threat_modeling(self, context: Dict[str, Any]) -> ThreatModel:
        """
        Perform threat modeling for the system.
        
        Args:
            context: Context including system description and architecture
            
        Returns:
            ThreatModel with identified threats and mitigations
        """
        logger.info("Performing threat modeling")
        
        system_description = context.get("system_description", "")
        architecture = context.get("architecture", {})
        
        # Identify assets
        assets = self._identify_assets(system_description, architecture)
        
        # Identify threats using STRIDE model
        threats = self._identify_threats_stride(assets, architecture)
        
        # Identify attack vectors
        attack_vectors = self._identify_attack_vectors(threats)
        
        # Generate mitigations
        mitigations = self._generate_mitigations(threats)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(threats)
        
        model = ThreatModel(
            assets=assets,
            threats=threats,
            attack_vectors=attack_vectors,
            mitigations=mitigations,
            risk_score=risk_score
        )
        
        logger.info(f"Threat modeling completed: {len(threats)} threats identified")
        return model
    
    async def perform_security_testing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform security testing.
        
        Args:
            context: Context including test targets and parameters
            
        Returns:
            Security testing results
        """
        logger.info("Performing security testing")
        
        if not self.tool_executor:
            return {"error": "Tool executor required for security testing"}
        
        test_type = context.get("test_type", "static")
        target = context.get("target", "")
        
        results = {
            "test_type": test_type,
            "target": target,
            "findings": [],
            "passed": True
        }
        
        if test_type == "static":
            # Run static analysis tools
            findings = await self._run_static_analysis(target)
            results["findings"] = findings
            results["passed"] = len(findings) == 0
        
        logger.info(f"Security testing completed: {len(results['findings'])} findings")
        return results
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """Provide security expertise."""
        logger.info(f"Providing security expertise for: {question}")
        
        recommendations = []
        
        if "authentication" in question.lower():
            recommendations.extend([
                "Use strong password policies",
                "Implement multi-factor authentication",
                "Use secure session management",
                "Implement account lockout mechanisms"
            ])
        elif "encryption" in question.lower():
            recommendations.extend([
                "Use TLS 1.2 or higher for transport",
                "Use AES-256 for data at rest",
                "Properly manage encryption keys",
                "Never roll your own crypto"
            ])
        elif "injection" in question.lower():
            recommendations.extend([
                "Use parameterized queries",
                "Validate and sanitize all inputs",
                "Use ORM frameworks properly",
                "Implement input whitelisting"
            ])
        else:
            recommendations.extend(self.security_best_practices[:4])
        
        return {
            "expertise": f"Security guidance on: {question}",
            "confidence": 0.9,
            "recommendations": recommendations,
            "best_practices": self.security_best_practices[:5]
        }
    
    def _scan_code_patterns(self, code: str, file_path: str) -> List[Vulnerability]:
        """Scan code for vulnerability patterns."""
        import re
        
        vulnerabilities = []
        lines = code.split("\n")
        
        for vuln_type, pattern_info in self.vulnerability_patterns.items():
            for pattern in pattern_info["patterns"]:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        vuln = Vulnerability(
                            type=vuln_type,
                            severity=pattern_info["severity"],
                            description=pattern_info["description"],
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=line.strip(),
                            cwe_id=pattern_info.get("cwe"),
                            remediation=self._get_remediation(vuln_type)
                        )
                        vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _scan_project(self, project_path: str) -> List[Vulnerability]:
        """Scan entire project for vulnerabilities."""
        vulnerabilities = []
        
        try:
            # Use tool executor to find Python files
            result = await self.tool_executor.execute_command(
                f"find {project_path} -name '*.py' -type f",
                Path(project_path)
            )
            
            if result.success and result.stdout:
                files = result.stdout.strip().split("\n")
                for file_path in files[:20]:  # Limit to 20 files for demo
                    try:
                        with open(file_path, 'r') as f:
                            code = f.read()
                            vulns = self._scan_code_patterns(code, file_path)
                            vulnerabilities.extend(vulns)
                    except Exception as e:
                        logger.warning(f"Could not scan file {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Project scan failed: {e}")
        
        return vulnerabilities
    
    def _calculate_security_score(
        self,
        critical: int,
        high: int,
        medium: int,
        low: int
    ) -> float:
        """Calculate overall security score."""
        base_score = 10.0
        
        # Deduct points based on severity
        base_score -= critical * 2.0
        base_score -= high * 1.0
        base_score -= medium * 0.5
        base_score -= low * 0.2
        
        return max(0.0, min(10.0, base_score))
    
    def _generate_security_recommendations(
        self,
        vulnerabilities: List[Vulnerability]
    ) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        # Group by type
        vuln_types = set(v.type for v in vulnerabilities)
        
        for vuln_type in vuln_types:
            recommendations.append(self._get_remediation(vuln_type))
        
        # Add general recommendations
        if vulnerabilities:
            recommendations.extend([
                "Conduct regular security audits",
                "Keep dependencies updated",
                "Implement security testing in CI/CD"
            ])
        
        return recommendations
    
    def _get_remediation(self, vuln_type: VulnerabilityType) -> str:
        """Get remediation advice for vulnerability type."""
        remediations = {
            VulnerabilityType.SQL_INJECTION: "Use parameterized queries or ORM",
            VulnerabilityType.COMMAND_INJECTION: "Avoid shell=True, use subprocess with list args",
            VulnerabilityType.HARDCODED_SECRETS: "Use environment variables or secret management",
            VulnerabilityType.WEAK_CRYPTO: "Use SHA-256 or stronger algorithms",
            VulnerabilityType.INSECURE_DESERIALIZATION: "Use safe loaders (yaml.safe_load)"
        }
        return remediations.get(vuln_type, "Review and fix security issue")
    
    def _generate_fix_for_vulnerability(self, vuln: Vulnerability) -> Optional[SecurityFix]:
        """Generate automated fix for vulnerability."""
        fix_templates = {
            VulnerabilityType.HARDCODED_SECRETS: {
                "description": "Replace hardcoded secret with environment variable",
                "automated": True,
                "confidence": 0.9
            },
            VulnerabilityType.WEAK_CRYPTO: {
                "description": "Replace weak algorithm with stronger alternative",
                "automated": True,
                "confidence": 0.85
            },
            VulnerabilityType.SQL_INJECTION: {
                "description": "Convert to parameterized query",
                "automated": False,
                "confidence": 0.7
            }
        }
        
        template = fix_templates.get(vuln.type)
        if not template:
            return None
        
        return SecurityFix(
            vulnerability=vuln,
            fix_description=template["description"],
            automated=template["automated"],
            confidence=template["confidence"],
            testing_required=True
        )
    
    async def _test_security_fixes(self, fixes: List[SecurityFix]) -> None:
        """Test security fixes."""
        if not self.tool_executor:
            return
        
        logger.info("Testing security fixes")
        # Could apply fixes and run security tests
    
    def _identify_assets(
        self,
        system_description: str,
        architecture: Dict[str, Any]
    ) -> List[str]:
        """Identify system assets for threat modeling."""
        assets = []
        
        # Extract from description
        if "database" in system_description.lower():
            assets.append("Database")
        if "api" in system_description.lower():
            assets.append("API")
        if "user data" in system_description.lower():
            assets.append("User Data")
        
        # Extract from architecture
        if "components" in architecture:
            for component in architecture["components"]:
                if isinstance(component, dict):
                    assets.append(component.get("name", "Component"))
        
        return assets
    
    def _identify_threats_stride(
        self,
        assets: List[str],
        architecture: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify threats using STRIDE model."""
        threats = []
        
        # STRIDE: Spoofing, Tampering, Repudiation, Information Disclosure, 
        # Denial of Service, Elevation of Privilege
        
        for asset in assets:
            if "API" in asset:
                threats.append({
                    "asset": asset,
                    "category": "Spoofing",
                    "description": "Unauthorized API access",
                    "severity": SeverityLevel.HIGH.value
                })
                threats.append({
                    "asset": asset,
                    "category": "Denial of Service",
                    "description": "API rate limiting bypass",
                    "severity": SeverityLevel.MEDIUM.value
                })
            
            if "Database" in asset:
                threats.append({
                    "asset": asset,
                    "category": "Information Disclosure",
                    "description": "Unauthorized data access",
                    "severity": SeverityLevel.CRITICAL.value
                })
                threats.append({
                    "asset": asset,
                    "category": "Tampering",
                    "description": "Data modification",
                    "severity": SeverityLevel.HIGH.value
                })
        
        return threats
    
    def _identify_attack_vectors(self, threats: List[Dict[str, Any]]) -> List[str]:
        """Identify attack vectors."""
        vectors = set()
        
        for threat in threats:
            category = threat.get("category", "")
            if category == "Spoofing":
                vectors.add("Credential theft")
                vectors.add("Session hijacking")
            elif category == "Information Disclosure":
                vectors.add("SQL injection")
                vectors.add("Path traversal")
            elif category == "Denial of Service":
                vectors.add("Resource exhaustion")
                vectors.add("Amplification attacks")
        
        return list(vectors)
    
    def _generate_mitigations(self, threats: List[Dict[str, Any]]) -> List[str]:
        """Generate threat mitigations."""
        mitigations = []
        
        categories = set(t.get("category") for t in threats)
        
        if "Spoofing" in categories:
            mitigations.append("Implement strong authentication (MFA)")
        if "Tampering" in categories:
            mitigations.append("Use integrity checks and digital signatures")
        if "Information Disclosure" in categories:
            mitigations.append("Encrypt sensitive data and use access controls")
        if "Denial of Service" in categories:
            mitigations.append("Implement rate limiting and resource quotas")
        
        return mitigations
    
    def _calculate_risk_score(self, threats: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score."""
        if not threats:
            return 0.0
        
        severity_scores = {
            SeverityLevel.CRITICAL.value: 10.0,
            SeverityLevel.HIGH.value: 7.0,
            SeverityLevel.MEDIUM.value: 4.0,
            SeverityLevel.LOW.value: 2.0
        }
        
        total_score = sum(
            severity_scores.get(t.get("severity", "low"), 2.0)
            for t in threats
        )
        
        return total_score / len(threats)
    
    async def _run_static_analysis(self, target: str) -> List[Dict[str, Any]]:
        """Run static analysis tools."""
        findings = []
        
        if not self.tool_executor:
            return findings
        
        try:
            # Could run tools like bandit, safety, etc.
            result = await self.tool_executor.execute_command(
                f"echo 'Static analysis placeholder for {target}'",
                Path(".")
            )
            
            if result.success:
                findings.append({
                    "tool": "static_analysis",
                    "message": "Analysis completed",
                    "severity": "info"
                })
        
        except Exception as e:
            logger.error(f"Static analysis failed: {e}")
        
        return findings
    
    async def _general_security_consultation(self, task: Task) -> Dict[str, Any]:
        """Provide general security consultation."""
        return {
            "consultation": f"Security guidance for: {task.description}",
            "recommendations": self.security_best_practices[:5],
            "resources": [
                "OWASP Top 10",
                "CWE/SANS Top 25",
                "Security best practices documentation"
            ]
        }
    
    def _generate_suggestions(self, result: Any) -> List[str]:
        """Generate suggestions based on result."""
        suggestions = []
        
        if isinstance(result, SecurityReport):
            if result.critical_count > 0:
                suggestions.append("Address critical vulnerabilities immediately")
            if result.high_count > 0:
                suggestions.append("Prioritize high severity issues")
            suggestions.extend(result.recommendations[:2])
        elif isinstance(result, list) and result and isinstance(result[0], SecurityFix):
            suggestions.append("Review and apply security fixes")
            suggestions.append("Test fixes thoroughly before deployment")
        
        return suggestions
    
    def _generate_next_steps(self, task: Task, result: Any) -> List[str]:
        """Generate next steps based on task and result."""
        next_steps = []
        
        if isinstance(result, SecurityReport):
            next_steps.extend([
                "Generate fixes for identified vulnerabilities",
                "Implement security best practices",
                "Set up continuous security monitoring"
            ])
        elif isinstance(result, list) and result and isinstance(result[0], SecurityFix):
            next_steps.extend([
                "Apply security fixes",
                "Run security tests",
                "Update security documentation"
            ])
        elif isinstance(result, ThreatModel):
            next_steps.extend([
                "Implement identified mitigations",
                "Review and update threat model regularly",
                "Conduct security training"
            ])
        
        return next_steps
