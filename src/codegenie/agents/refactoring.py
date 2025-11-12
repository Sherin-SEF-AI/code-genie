"""
Refactoring Agent - Specialized agent for code refactoring and improvement.
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


class RefactoringType(Enum):
    """Types of refactoring operations."""
    
    EXTRACT_METHOD = "extract_method"
    RENAME = "rename"
    MOVE_CLASS = "move_class"
    INLINE = "inline"
    EXTRACT_VARIABLE = "extract_variable"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    REMOVE_DUPLICATION = "remove_duplication"
    IMPROVE_NAMING = "improve_naming"


class CodeSmell(Enum):
    """Common code smells."""
    
    LONG_METHOD = "long_method"
    LARGE_CLASS = "large_class"
    DUPLICATE_CODE = "duplicate_code"
    LONG_PARAMETER_LIST = "long_parameter_list"
    DIVERGENT_CHANGE = "divergent_change"
    SHOTGUN_SURGERY = "shotgun_surgery"
    FEATURE_ENVY = "feature_envy"
    DATA_CLUMPS = "data_clumps"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    SWITCH_STATEMENTS = "switch_statements"


@dataclass
class RefactoringOpportunity:
    """Represents a refactoring opportunity."""
    
    smell: CodeSmell
    refactoring_type: RefactoringType
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: str = ""
    suggested_refactoring: str = ""
    impact: str = "medium"  # low, medium, high
    confidence: float = 0.0
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class RefactoringPlan:
    """Plan for refactoring operations."""
    
    opportunities: List[RefactoringOpportunity] = field(default_factory=list)
    priority_order: List[int] = field(default_factory=list)
    estimated_effort: str = ""
    expected_benefits: List[str] = field(default_factory=list)


class RefactoringAgent(BaseAgent):
    """
    Specialized agent for code refactoring and improvement.
    
    Capabilities:
    - Code smell detection
    - Refactoring suggestions
    - Safe refactoring execution
    - Code quality improvement
    """
    
    def __init__(
        self,
        config: Config,
        model_router: ModelRouter,
        tool_executor: Optional[ToolExecutor] = None
    ):
        super().__init__(
            name="RefactoringAgent",
            capabilities=[
                AgentCapability.REFACTORING,
                AgentCapability.CODE_ANALYSIS
            ],
            config=config,
            model_router=model_router
        )
        
        self.tool_executor = tool_executor
        self.smell_patterns: Dict[str, Any] = self._initialize_smell_patterns()
        
        logger.info("Initialized RefactoringAgent")
    
    def _initialize_smell_patterns(self) -> Dict[str, Any]:
        """Initialize code smell detection patterns."""
        return {
            CodeSmell.LONG_METHOD: {
                "threshold": 50,  # lines
                "description": "Method is too long",
                "refactoring": RefactoringType.EXTRACT_METHOD
            },
            CodeSmell.LARGE_CLASS: {
                "threshold": 500,  # lines
                "description": "Class is too large",
                "refactoring": RefactoringType.EXTRACT_METHOD
            },
            CodeSmell.LONG_PARAMETER_LIST: {
                "threshold": 5,  # parameters
                "description": "Too many parameters",
                "refactoring": RefactoringType.EXTRACT_VARIABLE
            },
            CodeSmell.DUPLICATE_CODE: {
                "threshold": 10,  # lines
                "description": "Duplicate code detected",
                "refactoring": RefactoringType.EXTRACT_METHOD
            }
        }
    
    async def can_handle_task(self, task: Task) -> bool:
        """Determine if this agent can handle the task."""
        refactoring_keywords = [
            "refactor", "refactoring", "improve", "clean", "smell",
            "extract", "rename", "simplify", "restructure"
        ]
        
        task_text = f"{task.description} {task.task_type}".lower()
        return any(keyword in task_text for keyword in refactoring_keywords)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Execute a refactoring task."""
        try:
            task_type = task.task_type.lower()
            
            if "detect" in task_type or "identify" in task_type:
                result = await self.identify_refactoring_opportunities(task.context)
            elif "plan" in task_type:
                result = await self.create_refactoring_plan(task.context)
            elif "refactor" in task_type or "apply" in task_type:
                result = await self.apply_refactoring(task.context)
            else:
                result = await self._general_refactoring_consultation(task)
            
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=True,
                output=result,
                confidence=0.85,
                reasoning=f"Completed refactoring task: {task.task_type}",
                suggestions=self._generate_suggestions(result),
                next_steps=self._generate_next_steps(task, result)
            )
            
        except Exception as e:
            logger.error(f"RefactoringAgent task execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=False,
                confidence=0.0,
                reasoning=f"Task execution failed: {str(e)}",
                error=str(e)
            )
    
    async def identify_refactoring_opportunities(
        self,
        context: Dict[str, Any]
    ) -> List[RefactoringOpportunity]:
        """Identify refactoring opportunities in code."""
        logger.info("Identifying refactoring opportunities")
        
        code = context.get("code", "")
        file_path = context.get("file_path", "")
        
        opportunities = []
        
        if code:
            opportunities.extend(self._detect_code_smells(code, file_path))
        
        logger.info(f"Identified {len(opportunities)} refactoring opportunities")
        return opportunities
    
    async def create_refactoring_plan(self, context: Dict[str, Any]) -> RefactoringPlan:
        """Create a refactoring plan."""
        logger.info("Creating refactoring plan")
        
        opportunities = context.get("opportunities", [])
        if not opportunities:
            opportunities = await self.identify_refactoring_opportunities(context)
        
        # Prioritize opportunities
        priority_order = self._prioritize_refactorings(opportunities)
        
        # Estimate effort
        estimated_effort = self._estimate_refactoring_effort(opportunities)
        
        # Identify benefits
        expected_benefits = self._identify_refactoring_benefits(opportunities)
        
        plan = RefactoringPlan(
            opportunities=opportunities,
            priority_order=priority_order,
            estimated_effort=estimated_effort,
            expected_benefits=expected_benefits
        )
        
        logger.info("Refactoring plan created")
        return plan
    
    async def apply_refactoring(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply refactoring to code."""
        logger.info("Applying refactoring")
        
        opportunity = context.get("opportunity")
        code = context.get("code", "")
        
        result = {
            "success": False,
            "refactored_code": "",
            "changes_made": []
        }
        
        if opportunity and code:
            refactored_code = self._perform_refactoring(opportunity, code)
            result["success"] = True
            result["refactored_code"] = refactored_code
            result["changes_made"] = [opportunity.description]
        
        logger.info("Refactoring applied")
        return result
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """Provide refactoring expertise."""
        logger.info(f"Providing refactoring expertise for: {question}")
        
        recommendations = [
            "Refactor in small, safe steps",
            "Run tests after each refactoring",
            "Use automated refactoring tools when possible",
            "Focus on improving code readability",
            "Address code smells systematically"
        ]
        
        return {
            "expertise": f"Refactoring guidance on: {question}",
            "confidence": 0.85,
            "recommendations": recommendations
        }
    
    def _detect_code_smells(self, code: str, file_path: str) -> List[RefactoringOpportunity]:
        """Detect code smells in code."""
        opportunities = []
        lines = code.split("\n")
        
        # Detect long methods
        current_method = None
        method_start = 0
        method_lines = 0
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("def "):
                if current_method and method_lines > self.smell_patterns[CodeSmell.LONG_METHOD]["threshold"]:
                    opportunities.append(RefactoringOpportunity(
                        smell=CodeSmell.LONG_METHOD,
                        refactoring_type=RefactoringType.EXTRACT_METHOD,
                        description=f"Method {current_method} is too long ({method_lines} lines)",
                        file_path=file_path,
                        line_number=method_start,
                        impact="medium",
                        confidence=0.9,
                        benefits=["Improved readability", "Better testability"],
                        risks=["May introduce bugs if not careful"]
                    ))
                
                current_method = line.strip().split("(")[0].replace("def ", "")
                method_start = i
                method_lines = 0
            elif current_method:
                method_lines += 1
        
        # Detect long parameter lists
        import re
        for i, line in enumerate(lines, 1):
            if "def " in line:
                params = re.findall(r'\((.*?)\)', line)
                if params:
                    param_count = len([p.strip() for p in params[0].split(",") if p.strip()])
                    if param_count > self.smell_patterns[CodeSmell.LONG_PARAMETER_LIST]["threshold"]:
                        opportunities.append(RefactoringOpportunity(
                            smell=CodeSmell.LONG_PARAMETER_LIST,
                            refactoring_type=RefactoringType.EXTRACT_VARIABLE,
                            description=f"Function has too many parameters ({param_count})",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip(),
                            impact="medium",
                            confidence=0.85,
                            benefits=["Simpler interface", "Easier to use"],
                            risks=["May require API changes"]
                        ))
        
        return opportunities
    
    def _prioritize_refactorings(
        self,
        opportunities: List[RefactoringOpportunity]
    ) -> List[int]:
        """Prioritize refactoring opportunities."""
        # Sort by impact and confidence
        impact_scores = {"high": 3, "medium": 2, "low": 1}
        
        scored = [
            (i, impact_scores.get(opp.impact, 1) * opp.confidence)
            for i, opp in enumerate(opportunities)
        ]
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [i for i, _ in scored]
    
    def _estimate_refactoring_effort(
        self,
        opportunities: List[RefactoringOpportunity]
    ) -> str:
        """Estimate effort for refactoring."""
        if len(opportunities) == 0:
            return "No refactoring needed"
        elif len(opportunities) <= 3:
            return "Low effort (1-2 hours)"
        elif len(opportunities) <= 10:
            return "Medium effort (1-2 days)"
        else:
            return "High effort (1+ weeks)"
    
    def _identify_refactoring_benefits(
        self,
        opportunities: List[RefactoringOpportunity]
    ) -> List[str]:
        """Identify benefits of refactoring."""
        benefits = set()
        
        for opp in opportunities:
            benefits.update(opp.benefits)
        
        return list(benefits)
    
    def _perform_refactoring(
        self,
        opportunity: RefactoringOpportunity,
        code: str
    ) -> str:
        """Perform the actual refactoring."""
        # Simplified implementation
        if opportunity.refactoring_type == RefactoringType.EXTRACT_METHOD:
            return code + "\n\n# Refactored: extracted method"
        elif opportunity.refactoring_type == RefactoringType.RENAME:
            return code + "\n\n# Refactored: renamed"
        
        return code
    
    async def _general_refactoring_consultation(self, task: Task) -> Dict[str, Any]:
        """Provide general refactoring consultation."""
        return {
            "consultation": f"Refactoring guidance for: {task.description}",
            "recommendations": [
                "Start with small, safe refactorings",
                "Ensure tests pass after each change",
                "Use version control to track changes",
                "Focus on improving code quality",
                "Document significant refactorings"
            ]
        }
    
    def _generate_suggestions(self, result: Any) -> List[str]:
        """Generate suggestions based on result."""
        suggestions = []
        
        if isinstance(result, list) and result and isinstance(result[0], RefactoringOpportunity):
            suggestions.append("Create refactoring plan")
            suggestions.append("Prioritize high-impact refactorings")
        elif isinstance(result, RefactoringPlan):
            suggestions.append("Start with highest priority items")
            suggestions.append("Test after each refactoring")
        
        return suggestions
    
    def _generate_next_steps(self, task: Task, result: Any) -> List[str]:
        """Generate next steps."""
        next_steps = []
        
        if isinstance(result, list) and result and isinstance(result[0], RefactoringOpportunity):
            next_steps.extend([
                "Create refactoring plan",
                "Prioritize opportunities",
                "Begin refactoring"
            ])
        elif isinstance(result, RefactoringPlan):
            next_steps.extend([
                "Apply refactorings in priority order",
                "Run tests after each change",
                "Review and commit changes"
            ])
        
        return next_steps
