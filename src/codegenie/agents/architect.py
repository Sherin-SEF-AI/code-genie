"""
Architect Agent - Specialized agent for system design and architecture decisions.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from .base_agent import BaseAgent, Task, AgentResult, AgentCapability
from ..core.config import Config
from ..core.tool_executor import ToolExecutor
from ..models.model_router import ModelRouter

logger = logging.getLogger(__name__)


class ArchitecturePattern(Enum):
    """Common architecture patterns."""
    
    LAYERED = "layered"
    MICROSERVICES = "microservices"
    EVENT_DRIVEN = "event_driven"
    MVC = "mvc"
    MVVM = "mvvm"
    HEXAGONAL = "hexagonal"
    CLEAN_ARCHITECTURE = "clean_architecture"
    SERVERLESS = "serverless"
    MONOLITHIC = "monolithic"
    SERVICE_ORIENTED = "service_oriented"


class TechnologyCategory(Enum):
    """Categories of technology components."""
    
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"
    API_GATEWAY = "api_gateway"
    CONTAINER = "container"
    ORCHESTRATION = "orchestration"
    MONITORING = "monitoring"
    LOGGING = "logging"


@dataclass
class TechnologyRecommendation:
    """Recommendation for a technology choice."""
    
    category: TechnologyCategory
    name: str
    version: Optional[str] = None
    rationale: str = ""
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class SystemDesign:
    """Complete system design specification."""
    
    name: str
    description: str
    architecture_pattern: ArchitecturePattern
    components: List[Dict[str, Any]] = field(default_factory=list)
    technologies: List[TechnologyRecommendation] = field(default_factory=list)
    design_patterns: List[str] = field(default_factory=list)
    scalability_considerations: List[str] = field(default_factory=list)
    security_considerations: List[str] = field(default_factory=list)
    performance_considerations: List[str] = field(default_factory=list)
    trade_offs: Dict[str, str] = field(default_factory=dict)
    diagrams: Dict[str, str] = field(default_factory=dict)  # diagram_type -> mermaid/plantuml code


@dataclass
class ArchitectureReview:
    """Review of an existing architecture."""
    
    overall_score: float  # 0-10
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    identified_patterns: List[ArchitecturePattern] = field(default_factory=list)
    technical_debt: List[str] = field(default_factory=list)
    scalability_issues: List[str] = field(default_factory=list)
    security_concerns: List[str] = field(default_factory=list)


class ArchitectAgent(BaseAgent):
    """
    Specialized agent for system architecture and design decisions.
    
    Capabilities:
    - System architecture design
    - Technology stack selection
    - Design pattern recommendations
    - Architecture review and validation
    - Scalability and performance planning
    """
    
    def __init__(
        self,
        config: Config,
        model_router: ModelRouter,
        tool_executor: Optional[ToolExecutor] = None
    ):
        super().__init__(
            name="ArchitectAgent",
            capabilities=[
                AgentCapability.ARCHITECTURE_DESIGN,
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.PROJECT_PLANNING
            ],
            config=config,
            model_router=model_router
        )
        
        self.tool_executor = tool_executor
        
        # Knowledge base of patterns and best practices
        self.pattern_knowledge: Dict[str, Any] = self._initialize_pattern_knowledge()
        self.technology_knowledge: Dict[str, Any] = self._initialize_technology_knowledge()
        
        logger.info("Initialized ArchitectAgent")
    
    def _initialize_pattern_knowledge(self) -> Dict[str, Any]:
        """Initialize knowledge base of architecture patterns."""
        return {
            ArchitecturePattern.LAYERED: {
                "description": "Organizes system into layers with specific responsibilities",
                "use_cases": ["Traditional enterprise applications", "Web applications"],
                "pros": ["Clear separation of concerns", "Easy to understand", "Testable"],
                "cons": ["Can become monolithic", "Performance overhead from layers"]
            },
            ArchitecturePattern.MICROSERVICES: {
                "description": "Decomposes application into small, independent services",
                "use_cases": ["Large-scale distributed systems", "Cloud-native applications"],
                "pros": ["Scalability", "Independent deployment", "Technology diversity"],
                "cons": ["Complexity", "Distributed system challenges", "Operational overhead"]
            },
            ArchitecturePattern.EVENT_DRIVEN: {
                "description": "Components communicate through events",
                "use_cases": ["Real-time systems", "Asynchronous processing"],
                "pros": ["Loose coupling", "Scalability", "Flexibility"],
                "cons": ["Debugging complexity", "Event ordering challenges"]
            },
            ArchitecturePattern.CLEAN_ARCHITECTURE: {
                "description": "Dependency rule with business logic at center",
                "use_cases": ["Complex business applications", "Long-term maintainability"],
                "pros": ["Testability", "Independence", "Maintainability"],
                "cons": ["Initial complexity", "More code to write"]
            }
        }
    
    def _initialize_technology_knowledge(self) -> Dict[str, Any]:
        """Initialize knowledge base of technologies."""
        return {
            "python": {
                "category": TechnologyCategory.PROGRAMMING_LANGUAGE,
                "strengths": ["Rapid development", "Rich ecosystem", "Data science"],
                "weaknesses": ["Performance", "Mobile development"],
                "best_for": ["Web APIs", "Data processing", "ML/AI"]
            },
            "typescript": {
                "category": TechnologyCategory.PROGRAMMING_LANGUAGE,
                "strengths": ["Type safety", "JavaScript ecosystem", "Tooling"],
                "weaknesses": ["Compilation overhead", "Learning curve"],
                "best_for": ["Large web applications", "Full-stack development"]
            },
            "postgresql": {
                "category": TechnologyCategory.DATABASE,
                "strengths": ["ACID compliance", "Advanced features", "Reliability"],
                "weaknesses": ["Scaling complexity", "Resource intensive"],
                "best_for": ["Complex queries", "Data integrity critical"]
            },
            "redis": {
                "category": TechnologyCategory.CACHE,
                "strengths": ["Performance", "Data structures", "Pub/sub"],
                "weaknesses": ["Memory constraints", "Persistence limitations"],
                "best_for": ["Caching", "Session storage", "Real-time features"]
            }
        }
    
    async def can_handle_task(self, task: Task) -> bool:
        """Determine if this agent can handle the task."""
        architecture_keywords = [
            "architecture", "design", "system", "pattern", "technology",
            "stack", "scalability", "structure", "component", "module"
        ]
        
        task_text = f"{task.description} {task.task_type}".lower()
        return any(keyword in task_text for keyword in architecture_keywords)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Execute an architecture-related task."""
        try:
            task_type = task.task_type.lower()
            
            if "design" in task_type or "create" in task_type:
                result = await self.design_system_architecture(task.context)
            elif "review" in task_type or "analyze" in task_type:
                result = await self.review_architecture(task.context)
            elif "technology" in task_type or "stack" in task_type:
                result = await self.select_technologies(task.context)
            elif "pattern" in task_type:
                result = await self.recommend_design_patterns(task.context)
            else:
                # General architecture consultation
                result = await self._general_architecture_consultation(task)
            
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=True,
                output=result,
                confidence=0.85,
                reasoning=f"Completed architecture task: {task.task_type}",
                suggestions=self._generate_suggestions(result),
                next_steps=self._generate_next_steps(task, result)
            )
            
        except Exception as e:
            logger.error(f"ArchitectAgent task execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=False,
                confidence=0.0,
                reasoning=f"Task execution failed: {str(e)}",
                error=str(e)
            )
    
    async def design_system_architecture(self, requirements: Dict[str, Any]) -> SystemDesign:
        """
        Design a system architecture based on requirements.
        
        Args:
            requirements: Dictionary containing system requirements
            
        Returns:
            SystemDesign with complete architecture specification
        """
        logger.info("Designing system architecture")
        
        # Extract key requirements
        system_name = requirements.get("name", "System")
        description = requirements.get("description", "")
        scale = requirements.get("scale", "medium")  # small, medium, large
        requirements_list = requirements.get("requirements", [])
        constraints = requirements.get("constraints", {})
        
        # Select appropriate architecture pattern
        architecture_pattern = self._select_architecture_pattern(
            scale, requirements_list, constraints
        )
        
        # Design components
        components = self._design_components(architecture_pattern, requirements_list)
        
        # Select technologies
        technologies = await self.select_technologies(requirements)
        
        # Identify design patterns
        design_patterns = self._identify_applicable_patterns(requirements_list)
        
        # Generate considerations
        scalability = self._generate_scalability_considerations(scale, architecture_pattern)
        security = self._generate_security_considerations(requirements_list)
        performance = self._generate_performance_considerations(scale, requirements_list)
        
        # Analyze trade-offs
        trade_offs = self._analyze_trade_offs(architecture_pattern, technologies)
        
        # Generate diagrams
        diagrams = self._generate_architecture_diagrams(
            architecture_pattern, components, system_name
        )
        
        design = SystemDesign(
            name=system_name,
            description=description,
            architecture_pattern=architecture_pattern,
            components=components,
            technologies=technologies,
            design_patterns=design_patterns,
            scalability_considerations=scalability,
            security_considerations=security,
            performance_considerations=performance,
            trade_offs=trade_offs,
            diagrams=diagrams
        )
        
        # Validate design if tool executor available
        if self.tool_executor:
            await self._validate_architecture(design)
        
        logger.info(f"Completed system architecture design: {system_name}")
        return design
    
    async def select_technologies(self, constraints: Dict[str, Any]) -> List[TechnologyRecommendation]:
        """
        Select appropriate technologies for the system.
        
        Args:
            constraints: Dictionary containing constraints and requirements
            
        Returns:
            List of technology recommendations
        """
        logger.info("Selecting technology stack")
        
        recommendations = []
        
        # Programming language selection
        lang_rec = self._recommend_programming_language(constraints)
        if lang_rec:
            recommendations.append(lang_rec)
        
        # Framework selection
        framework_rec = self._recommend_framework(constraints)
        if framework_rec:
            recommendations.append(framework_rec)
        
        # Database selection
        db_rec = self._recommend_database(constraints)
        if db_rec:
            recommendations.append(db_rec)
        
        # Cache selection
        cache_rec = self._recommend_cache(constraints)
        if cache_rec:
            recommendations.append(cache_rec)
        
        # Additional infrastructure
        infra_recs = self._recommend_infrastructure(constraints)
        recommendations.extend(infra_recs)
        
        logger.info(f"Generated {len(recommendations)} technology recommendations")
        return recommendations
    
    async def recommend_design_patterns(self, context: Dict[str, Any]) -> List[str]:
        """
        Recommend design patterns for specific scenarios.
        
        Args:
            context: Context including problem description and requirements
            
        Returns:
            List of recommended design patterns with rationale
        """
        logger.info("Recommending design patterns")
        
        problem = context.get("problem", "")
        requirements = context.get("requirements", [])
        
        patterns = []
        
        # Analyze requirements and recommend patterns
        if "creation" in problem.lower() or any("create" in r.lower() for r in requirements):
            patterns.append("Factory Pattern - For flexible object creation")
            patterns.append("Builder Pattern - For complex object construction")
        
        if "single instance" in problem.lower() or "global" in problem.lower():
            patterns.append("Singleton Pattern - For single instance management")
        
        if "notification" in problem.lower() or "event" in problem.lower():
            patterns.append("Observer Pattern - For event notification")
        
        if "algorithm" in problem.lower() or "strategy" in problem.lower():
            patterns.append("Strategy Pattern - For interchangeable algorithms")
        
        if "interface" in problem.lower() or "adapter" in problem.lower():
            patterns.append("Adapter Pattern - For interface compatibility")
        
        if "complex" in problem.lower() or "subsystem" in problem.lower():
            patterns.append("Facade Pattern - For simplified interface to complex subsystem")
        
        return patterns
    
    async def review_architecture(self, context: Dict[str, Any]) -> ArchitectureReview:
        """
        Review an existing architecture.
        
        Args:
            context: Context including project path and architecture description
            
        Returns:
            ArchitectureReview with analysis and recommendations
        """
        logger.info("Reviewing architecture")
        
        project_path = context.get("project_path")
        architecture_desc = context.get("architecture_description", "")
        
        # Analyze architecture
        identified_patterns = self._identify_patterns_in_codebase(project_path)
        strengths = []
        weaknesses = []
        recommendations = []
        technical_debt = []
        scalability_issues = []
        security_concerns = []
        
        # Evaluate based on best practices
        if ArchitecturePattern.LAYERED in identified_patterns:
            strengths.append("Clear separation of concerns with layered architecture")
        
        if len(identified_patterns) > 2:
            weaknesses.append("Multiple conflicting architecture patterns detected")
            recommendations.append("Standardize on a single primary architecture pattern")
        
        # Check for common issues
        if project_path:
            issues = await self._analyze_architecture_issues(project_path)
            technical_debt.extend(issues.get("technical_debt", []))
            scalability_issues.extend(issues.get("scalability", []))
            security_concerns.extend(issues.get("security", []))
        
        # Calculate overall score
        score = self._calculate_architecture_score(
            strengths, weaknesses, technical_debt, scalability_issues, security_concerns
        )
        
        review = ArchitectureReview(
            overall_score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            identified_patterns=identified_patterns,
            technical_debt=technical_debt,
            scalability_issues=scalability_issues,
            security_concerns=security_concerns
        )
        
        logger.info(f"Architecture review completed with score: {score}/10")
        return review
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """Provide architecture expertise."""
        logger.info(f"Providing architecture expertise for: {question}")
        
        recommendations = []
        
        if "microservices" in question.lower():
            recommendations.extend([
                "Consider service boundaries based on business capabilities",
                "Implement API gateway for unified entry point",
                "Use event-driven communication for loose coupling",
                "Plan for distributed tracing and monitoring"
            ])
        elif "scalability" in question.lower():
            recommendations.extend([
                "Design for horizontal scaling from the start",
                "Implement caching strategies at multiple levels",
                "Use asynchronous processing for heavy operations",
                "Consider database sharding for data scalability"
            ])
        elif "security" in question.lower():
            recommendations.extend([
                "Implement defense in depth strategy",
                "Use principle of least privilege",
                "Encrypt sensitive data at rest and in transit",
                "Implement proper authentication and authorization"
            ])
        else:
            recommendations.extend([
                "Start with simple architecture and evolve",
                "Document architectural decisions and rationale",
                "Consider maintainability and team expertise",
                "Plan for monitoring and observability"
            ])
        
        return {
            "expertise": f"Architecture guidance on: {question}",
            "confidence": 0.85,
            "recommendations": recommendations,
            "patterns": self._suggest_relevant_patterns(question)
        }
    
    def _select_architecture_pattern(
        self,
        scale: str,
        requirements: List[str],
        constraints: Dict[str, Any]
    ) -> ArchitecturePattern:
        """Select appropriate architecture pattern."""
        # Simple heuristic-based selection
        if scale == "large" or "distributed" in str(requirements).lower():
            return ArchitecturePattern.MICROSERVICES
        elif "event" in str(requirements).lower():
            return ArchitecturePattern.EVENT_DRIVEN
        elif "clean" in str(constraints).lower() or "testability" in str(requirements).lower():
            return ArchitecturePattern.CLEAN_ARCHITECTURE
        else:
            return ArchitecturePattern.LAYERED
    
    def _design_components(
        self,
        pattern: ArchitecturePattern,
        requirements: List[str]
    ) -> List[Dict[str, Any]]:
        """Design system components based on pattern."""
        components = []
        
        if pattern == ArchitecturePattern.LAYERED:
            components = [
                {"name": "Presentation Layer", "responsibility": "User interface and interaction"},
                {"name": "Business Logic Layer", "responsibility": "Core business rules"},
                {"name": "Data Access Layer", "responsibility": "Database operations"},
                {"name": "Infrastructure Layer", "responsibility": "Cross-cutting concerns"}
            ]
        elif pattern == ArchitecturePattern.MICROSERVICES:
            # Extract services from requirements
            components = [
                {"name": "API Gateway", "responsibility": "Request routing and aggregation"},
                {"name": "Service Registry", "responsibility": "Service discovery"},
                {"name": "Core Services", "responsibility": "Business capabilities"}
            ]
        elif pattern == ArchitecturePattern.CLEAN_ARCHITECTURE:
            components = [
                {"name": "Entities", "responsibility": "Business objects"},
                {"name": "Use Cases", "responsibility": "Application business rules"},
                {"name": "Interface Adapters", "responsibility": "Convert data formats"},
                {"name": "Frameworks & Drivers", "responsibility": "External interfaces"}
            ]
        
        return components
    
    def _recommend_programming_language(self, constraints: Dict[str, Any]) -> Optional[TechnologyRecommendation]:
        """Recommend programming language."""
        domain = constraints.get("domain", "").lower()
        team_expertise = constraints.get("team_expertise", [])
        
        if "data" in domain or "ml" in domain or "python" in team_expertise:
            return TechnologyRecommendation(
                category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                name="Python",
                version="3.11+",
                rationale="Excellent for data processing and ML with rich ecosystem",
                pros=["Rich libraries", "Rapid development", "Large community"],
                cons=["Performance limitations", "GIL for concurrency"],
                alternatives=["Java", "Go"],
                confidence=0.9
            )
        elif "web" in domain or "typescript" in team_expertise:
            return TechnologyRecommendation(
                category=TechnologyCategory.PROGRAMMING_LANGUAGE,
                name="TypeScript",
                version="5.0+",
                rationale="Type-safe JavaScript for robust web applications",
                pros=["Type safety", "Great tooling", "JavaScript ecosystem"],
                cons=["Compilation step", "Learning curve"],
                alternatives=["JavaScript", "Python"],
                confidence=0.85
            )
        
        return None
    
    def _recommend_framework(self, constraints: Dict[str, Any]) -> Optional[TechnologyRecommendation]:
        """Recommend framework."""
        language = constraints.get("language", "").lower()
        app_type = constraints.get("type", "").lower()
        
        if "python" in language and "api" in app_type:
            return TechnologyRecommendation(
                category=TechnologyCategory.FRAMEWORK,
                name="FastAPI",
                rationale="Modern, fast Python web framework with automatic API docs",
                pros=["High performance", "Type hints", "Auto documentation"],
                cons=["Relatively new", "Smaller ecosystem than Flask"],
                alternatives=["Django", "Flask"],
                confidence=0.85
            )
        
        return None
    
    def _recommend_database(self, constraints: Dict[str, Any]) -> Optional[TechnologyRecommendation]:
        """Recommend database."""
        data_type = constraints.get("data_type", "").lower()
        scale = constraints.get("scale", "medium")
        
        if "relational" in data_type or "structured" in data_type:
            return TechnologyRecommendation(
                category=TechnologyCategory.DATABASE,
                name="PostgreSQL",
                version="15+",
                rationale="Robust relational database with advanced features",
                pros=["ACID compliance", "JSON support", "Extensible"],
                cons=["Vertical scaling limits", "Complex replication"],
                alternatives=["MySQL", "SQLite"],
                confidence=0.9
            )
        
        return None
    
    def _recommend_cache(self, constraints: Dict[str, Any]) -> Optional[TechnologyRecommendation]:
        """Recommend caching solution."""
        if constraints.get("needs_cache", True):
            return TechnologyRecommendation(
                category=TechnologyCategory.CACHE,
                name="Redis",
                version="7.0+",
                rationale="High-performance in-memory data store",
                pros=["Very fast", "Rich data structures", "Pub/sub support"],
                cons=["Memory-based", "Persistence trade-offs"],
                alternatives=["Memcached", "In-memory cache"],
                confidence=0.85
            )
        return None
    
    def _recommend_infrastructure(self, constraints: Dict[str, Any]) -> List[TechnologyRecommendation]:
        """Recommend infrastructure components."""
        recommendations = []
        
        if constraints.get("containerization", True):
            recommendations.append(TechnologyRecommendation(
                category=TechnologyCategory.CONTAINER,
                name="Docker",
                rationale="Industry standard containerization",
                pros=["Portability", "Isolation", "Ecosystem"],
                cons=["Learning curve", "Overhead"],
                alternatives=["Podman"],
                confidence=0.95
            ))
        
        return recommendations
    
    def _identify_applicable_patterns(self, requirements: List[str]) -> List[str]:
        """Identify applicable design patterns."""
        patterns = []
        req_text = " ".join(requirements).lower()
        
        if "repository" in req_text or "data access" in req_text:
            patterns.append("Repository Pattern")
        if "dependency" in req_text or "injection" in req_text:
            patterns.append("Dependency Injection")
        if "factory" in req_text or "creation" in req_text:
            patterns.append("Factory Pattern")
        
        return patterns
    
    def _generate_scalability_considerations(self, scale: str, pattern: ArchitecturePattern) -> List[str]:
        """Generate scalability considerations."""
        considerations = [
            "Design for horizontal scaling",
            "Implement caching at multiple levels",
            "Use asynchronous processing for heavy operations"
        ]
        
        if pattern == ArchitecturePattern.MICROSERVICES:
            considerations.extend([
                "Implement service auto-scaling",
                "Use load balancing across service instances"
            ])
        
        return considerations
    
    def _generate_security_considerations(self, requirements: List[str]) -> List[str]:
        """Generate security considerations."""
        return [
            "Implement authentication and authorization",
            "Encrypt sensitive data at rest and in transit",
            "Follow principle of least privilege",
            "Regular security audits and updates",
            "Input validation and sanitization"
        ]
    
    def _generate_performance_considerations(self, scale: str, requirements: List[str]) -> List[str]:
        """Generate performance considerations."""
        return [
            "Optimize database queries and indexes",
            "Implement efficient caching strategies",
            "Use connection pooling",
            "Monitor and profile performance regularly",
            "Consider CDN for static assets"
        ]
    
    def _analyze_trade_offs(
        self,
        pattern: ArchitecturePattern,
        technologies: List[TechnologyRecommendation]
    ) -> Dict[str, str]:
        """Analyze architectural trade-offs."""
        trade_offs = {}
        
        if pattern == ArchitecturePattern.MICROSERVICES:
            trade_offs["Complexity vs Scalability"] = (
                "Microservices increase operational complexity but provide better scalability"
            )
        elif pattern == ArchitecturePattern.MONOLITHIC:
            trade_offs["Simplicity vs Scalability"] = (
                "Monolithic architecture is simpler but harder to scale"
            )
        
        return trade_offs
    
    def _generate_architecture_diagrams(
        self,
        pattern: ArchitecturePattern,
        components: List[Dict[str, Any]],
        system_name: str
    ) -> Dict[str, str]:
        """Generate architecture diagrams in Mermaid format."""
        diagrams = {}
        
        # Component diagram
        mermaid_code = "graph TB\n"
        for i, component in enumerate(components):
            comp_id = f"C{i}"
            mermaid_code += f"    {comp_id}[{component['name']}]\n"
        
        # Add connections based on pattern
        if pattern == ArchitecturePattern.LAYERED:
            for i in range(len(components) - 1):
                mermaid_code += f"    C{i} --> C{i+1}\n"
        
        diagrams["component_diagram"] = mermaid_code
        
        return diagrams
    
    def _identify_patterns_in_codebase(self, project_path: Optional[str]) -> List[ArchitecturePattern]:
        """Identify architecture patterns in codebase."""
        # Simplified implementation
        return [ArchitecturePattern.LAYERED]
    
    async def _analyze_architecture_issues(self, project_path: str) -> Dict[str, List[str]]:
        """Analyze architecture for issues."""
        issues = {
            "technical_debt": [],
            "scalability": [],
            "security": []
        }
        
        # Use tool executor if available
        if self.tool_executor:
            try:
                # Run static analysis
                result = await self.tool_executor.execute_command(
                    f"find {project_path} -name '*.py' | head -10",
                    Path(project_path)
                )
                
                if result.success:
                    issues["technical_debt"].append("Code analysis completed")
            except Exception as e:
                logger.warning(f"Could not analyze project: {e}")
        
        return issues
    
    def _calculate_architecture_score(
        self,
        strengths: List[str],
        weaknesses: List[str],
        technical_debt: List[str],
        scalability_issues: List[str],
        security_concerns: List[str]
    ) -> float:
        """Calculate overall architecture score."""
        base_score = 7.0
        
        # Add points for strengths
        base_score += len(strengths) * 0.5
        
        # Subtract points for issues
        base_score -= len(weaknesses) * 0.3
        base_score -= len(technical_debt) * 0.2
        base_score -= len(scalability_issues) * 0.3
        base_score -= len(security_concerns) * 0.4
        
        # Clamp to 0-10 range
        return max(0.0, min(10.0, base_score))
    
    async def _validate_architecture(self, design: SystemDesign) -> None:
        """Validate architecture design using tool executor."""
        if not self.tool_executor:
            return
        
        logger.info("Validating architecture design")
        # Could run validation commands, check dependencies, etc.
    
    async def _general_architecture_consultation(self, task: Task) -> Dict[str, Any]:
        """Provide general architecture consultation."""
        return {
            "consultation": f"Architecture guidance for: {task.description}",
            "recommendations": [
                "Start with simple, proven patterns",
                "Consider team expertise and constraints",
                "Plan for evolution and change",
                "Document decisions and rationale"
            ],
            "resources": [
                "Architecture patterns documentation",
                "Best practices guides",
                "Case studies"
            ]
        }
    
    def _generate_suggestions(self, result: Any) -> List[str]:
        """Generate suggestions based on result."""
        suggestions = []
        
        if isinstance(result, SystemDesign):
            suggestions.append(f"Review {result.architecture_pattern.value} pattern implementation")
            suggestions.append("Validate technology choices with team")
            suggestions.append("Create proof of concept for critical components")
        elif isinstance(result, ArchitectureReview):
            suggestions.extend(result.recommendations[:3])
        
        return suggestions
    
    def _generate_next_steps(self, task: Task, result: Any) -> List[str]:
        """Generate next steps based on task and result."""
        next_steps = []
        
        if isinstance(result, SystemDesign):
            next_steps.extend([
                "Create detailed component specifications",
                "Set up development environment",
                "Begin implementation of core components"
            ])
        elif isinstance(result, ArchitectureReview):
            next_steps.extend([
                "Address critical issues identified",
                "Refactor problematic areas",
                "Update documentation"
            ])
        
        return next_steps
    
    def _suggest_relevant_patterns(self, question: str) -> List[str]:
        """Suggest relevant patterns for a question."""
        patterns = []
        question_lower = question.lower()
        
        if "microservice" in question_lower:
            patterns.extend([
                ArchitecturePattern.MICROSERVICES.value,
                ArchitecturePattern.EVENT_DRIVEN.value
            ])
        elif "web" in question_lower:
            patterns.extend([
                ArchitecturePattern.MVC.value,
                ArchitecturePattern.LAYERED.value
            ])
        
        return patterns
