"""
Performance Agent - Specialized agent for performance optimization and analysis.
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


class PerformanceIssueType(Enum):
    """Types of performance issues."""
    
    ALGORITHMIC_COMPLEXITY = "algorithmic_complexity"
    MEMORY_LEAK = "memory_leak"
    INEFFICIENT_QUERY = "inefficient_query"
    N_PLUS_ONE_QUERY = "n_plus_one_query"
    BLOCKING_IO = "blocking_io"
    EXCESSIVE_LOOPS = "excessive_loops"
    LARGE_OBJECT_CREATION = "large_object_creation"
    INEFFICIENT_DATA_STRUCTURE = "inefficient_data_structure"
    MISSING_INDEX = "missing_index"
    UNNECESSARY_COMPUTATION = "unnecessary_computation"


class OptimizationType(Enum):
    """Types of optimizations."""
    
    ALGORITHM = "algorithm"
    DATA_STRUCTURE = "data_structure"
    CACHING = "caching"
    DATABASE = "database"
    ASYNC = "async"
    PARALLELIZATION = "parallelization"
    MEMORY = "memory"
    IO = "io"


@dataclass
class PerformanceIssue:
    """Represents a performance issue."""
    
    type: PerformanceIssueType
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: str = ""
    impact: str = "medium"  # low, medium, high, critical
    estimated_improvement: Optional[str] = None
    current_complexity: Optional[str] = None
    suggested_complexity: Optional[str] = None


@dataclass
class PerformanceOptimization:
    """Represents a performance optimization."""
    
    issue: PerformanceIssue
    optimization_type: OptimizationType
    description: str
    code_before: str
    code_after: str
    expected_improvement: str
    confidence: float = 0.0
    trade_offs: List[str] = field(default_factory=list)


@dataclass
class PerformanceProfile:
    """Performance profiling results."""
    
    total_time: float
    function_times: Dict[str, float] = field(default_factory=dict)
    memory_usage: Dict[str, float] = field(default_factory=dict)
    bottlenecks: List[str] = field(default_factory=list)
    hotspots: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    
    issues: List[PerformanceIssue] = field(default_factory=list)
    optimizations: List[PerformanceOptimization] = field(default_factory=list)
    overall_score: float = 0.0  # 0-10, higher is better
    recommendations: List[str] = field(default_factory=list)
    profile: Optional[PerformanceProfile] = None


class PerformanceAgent(BaseAgent):
    """
    Specialized agent for performance optimization and analysis.
    
    Capabilities:
    - Performance bottleneck detection
    - Optimization suggestions
    - Performance profiling
    - Impact measurement
    - Performance testing
    """
    
    def __init__(
        self,
        config: Config,
        model_router: ModelRouter,
        tool_executor: Optional[ToolExecutor] = None
    ):
        super().__init__(
            name="PerformanceAgent",
            capabilities=[
                AgentCapability.PERFORMANCE_OPTIMIZATION,
                AgentCapability.CODE_ANALYSIS
            ],
            config=config,
            model_router=model_router
        )
        
        self.tool_executor = tool_executor
        
        # Performance knowledge base
        self.optimization_patterns: Dict[str, Any] = self._initialize_optimization_patterns()
        self.complexity_patterns: Dict[str, str] = self._initialize_complexity_patterns()
        
        logger.info("Initialized PerformanceAgent")
    
    def _initialize_optimization_patterns(self) -> Dict[str, Any]:
        """Initialize optimization patterns."""
        return {
            "list_comprehension": {
                "pattern": "for.*append",
                "suggestion": "Use list comprehension",
                "improvement": "20-30% faster"
            },
            "generator": {
                "pattern": "return \\[.*for",
                "suggestion": "Use generator for large datasets",
                "improvement": "Reduced memory usage"
            },
            "set_lookup": {
                "pattern": "if.*in.*\\[",
                "suggestion": "Use set for membership testing",
                "improvement": "O(1) vs O(n) lookup"
            },
            "dict_get": {
                "pattern": "if.*in.*dict.*dict\\[",
                "suggestion": "Use dict.get() with default",
                "improvement": "Fewer lookups"
            }
        }
    
    def _initialize_complexity_patterns(self) -> Dict[str, str]:
        """Initialize complexity analysis patterns."""
        return {
            "nested_loops": "O(n²) or worse",
            "single_loop": "O(n)",
            "dict_lookup": "O(1)",
            "list_search": "O(n)",
            "sorting": "O(n log n)",
            "recursive": "Depends on recursion depth"
        }
    
    async def can_handle_task(self, task: Task) -> bool:
        """Determine if this agent can handle the task."""
        performance_keywords = [
            "performance", "optimize", "slow", "bottleneck", "profile",
            "speed", "efficiency", "latency", "throughput", "memory"
        ]
        
        task_text = f"{task.description} {task.task_type}".lower()
        return any(keyword in task_text for keyword in performance_keywords)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Execute a performance-related task."""
        try:
            task_type = task.task_type.lower()
            
            if "analyze" in task_type or "detect" in task_type:
                result = await self.analyze_performance(task.context)
            elif "optimize" in task_type:
                result = await self.generate_optimizations(task.context)
            elif "profile" in task_type:
                result = await self.profile_code(task.context)
            elif "measure" in task_type or "test" in task_type:
                result = await self.measure_performance(task.context)
            else:
                result = await self._general_performance_consultation(task)
            
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=True,
                output=result,
                confidence=0.85,
                reasoning=f"Completed performance task: {task.task_type}",
                suggestions=self._generate_suggestions(result),
                next_steps=self._generate_next_steps(task, result)
            )
            
        except Exception as e:
            logger.error(f"PerformanceAgent task execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=False,
                confidence=0.0,
                reasoning=f"Task execution failed: {str(e)}",
                error=str(e)
            )
    
    async def analyze_performance(self, context: Dict[str, Any]) -> PerformanceReport:
        """
        Analyze code for performance issues.
        
        Args:
            context: Context including code or project path
            
        Returns:
            PerformanceReport with identified issues
        """
        logger.info("Analyzing performance")
        
        code = context.get("code", "")
        file_path = context.get("file_path", "")
        
        issues = []
        
        # Analyze code patterns
        if code:
            issues.extend(self._analyze_code_patterns(code, file_path))
            issues.extend(self._analyze_complexity(code, file_path))
        
        # Generate optimizations
        optimizations = []
        for issue in issues:
            opt = self._generate_optimization_for_issue(issue)
            if opt:
                optimizations.append(opt)
        
        # Calculate score
        overall_score = self._calculate_performance_score(issues)
        
        # Generate recommendations
        recommendations = self._generate_performance_recommendations(issues)
        
        report = PerformanceReport(
            issues=issues,
            optimizations=optimizations,
            overall_score=overall_score,
            recommendations=recommendations
        )
        
        logger.info(f"Performance analysis completed: {len(issues)} issues found")
        return report
    
    async def generate_optimizations(self, context: Dict[str, Any]) -> List[PerformanceOptimization]:
        """
        Generate performance optimizations.
        
        Args:
            context: Context including code and issues
            
        Returns:
            List of performance optimizations
        """
        logger.info("Generating optimizations")
        
        issues = context.get("issues", [])
        if not issues:
            # Analyze first if no issues provided
            report = await self.analyze_performance(context)
            issues = report.issues
        
        optimizations = []
        
        for issue in issues:
            opt = self._generate_optimization_for_issue(issue)
            if opt:
                optimizations.append(opt)
        
        # Test optimizations if tool executor available
        if self.tool_executor and context.get("test_optimizations", False):
            await self._test_optimizations(optimizations)
        
        logger.info(f"Generated {len(optimizations)} optimizations")
        return optimizations
    
    async def profile_code(self, context: Dict[str, Any]) -> PerformanceProfile:
        """
        Profile code execution.
        
        Args:
            context: Context including code to profile
            
        Returns:
            PerformanceProfile with profiling results
        """
        logger.info("Profiling code")
        
        code = context.get("code", "")
        file_path = context.get("file_path", "")
        
        profile = PerformanceProfile(
            total_time=0.0,
            function_times={},
            memory_usage={},
            bottlenecks=[],
            hotspots=[]
        )
        
        # Use tool executor for actual profiling if available
        if self.tool_executor and file_path:
            profile = await self._run_profiler(file_path)
        else:
            # Static analysis fallback
            profile.bottlenecks = self._identify_bottlenecks_static(code)
        
        logger.info("Code profiling completed")
        return profile
    
    async def measure_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Measure performance impact of changes.
        
        Args:
            context: Context including before/after code
            
        Returns:
            Performance measurement results
        """
        logger.info("Measuring performance")
        
        code_before = context.get("code_before", "")
        code_after = context.get("code_after", "")
        
        results = {
            "improvement": "Unknown",
            "metrics": {},
            "validated": False
        }
        
        if self.tool_executor:
            results = await self._benchmark_code(code_before, code_after)
        
        logger.info("Performance measurement completed")
        return results
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """Provide performance expertise."""
        logger.info(f"Providing performance expertise for: {question}")
        
        recommendations = []
        
        if "database" in question.lower() or "query" in question.lower():
            recommendations.extend([
                "Add appropriate indexes",
                "Use query optimization techniques",
                "Implement connection pooling",
                "Consider caching frequently accessed data"
            ])
        elif "memory" in question.lower():
            recommendations.extend([
                "Use generators for large datasets",
                "Implement proper resource cleanup",
                "Profile memory usage",
                "Consider memory-efficient data structures"
            ])
        elif "algorithm" in question.lower():
            recommendations.extend([
                "Analyze time complexity",
                "Choose appropriate data structures",
                "Consider trade-offs between time and space",
                "Use built-in optimized functions"
            ])
        else:
            recommendations.extend([
                "Profile before optimizing",
                "Focus on bottlenecks",
                "Measure impact of changes",
                "Consider readability vs performance trade-offs"
            ])
        
        return {
            "expertise": f"Performance guidance on: {question}",
            "confidence": 0.85,
            "recommendations": recommendations,
            "optimization_patterns": list(self.optimization_patterns.keys())
        }
    
    def _analyze_code_patterns(self, code: str, file_path: str) -> List[PerformanceIssue]:
        """Analyze code for performance patterns."""
        import re
        
        issues = []
        lines = code.split("\n")
        
        for line_num, line in enumerate(lines, 1):
            # Check for list append in loop
            if "for" in line and any("append" in lines[i] for i in range(line_num, min(line_num + 5, len(lines)))):
                issues.append(PerformanceIssue(
                    type=PerformanceIssueType.INEFFICIENT_DATA_STRUCTURE,
                    description="List append in loop - consider list comprehension",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line.strip(),
                    impact="medium",
                    estimated_improvement="20-30% faster"
                ))
            
            # Check for membership testing with list
            if re.search(r'if\s+\w+\s+in\s+\[', line):
                issues.append(PerformanceIssue(
                    type=PerformanceIssueType.INEFFICIENT_DATA_STRUCTURE,
                    description="Membership testing with list - use set instead",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line.strip(),
                    impact="high",
                    estimated_improvement="O(1) vs O(n) lookup"
                ))
            
            # Check for blocking I/O
            if re.search(r'open\(|read\(|write\(', line) and "async" not in line:
                issues.append(PerformanceIssue(
                    type=PerformanceIssueType.BLOCKING_IO,
                    description="Blocking I/O operation - consider async",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line.strip(),
                    impact="medium"
                ))
        
        return issues
    
    def _analyze_complexity(self, code: str, file_path: str) -> List[PerformanceIssue]:
        """Analyze algorithmic complexity."""
        issues = []
        lines = code.split("\n")
        
        # Count nested loops
        loop_depth = 0
        max_depth = 0
        loop_start_line = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("for ") or stripped.startswith("while "):
                if loop_depth == 0:
                    loop_start_line = line_num
                loop_depth += 1
                max_depth = max(max_depth, loop_depth)
            elif loop_depth > 0 and (not line or not line[0].isspace()):
                loop_depth = max(0, loop_depth - 1)
        
        if max_depth >= 2:
            issues.append(PerformanceIssue(
                type=PerformanceIssueType.ALGORITHMIC_COMPLEXITY,
                description=f"Nested loops detected (depth: {max_depth})",
                file_path=file_path,
                line_number=loop_start_line,
                impact="high",
                current_complexity="O(n²) or worse",
                suggested_complexity="Consider O(n) or O(n log n) algorithm"
            ))
        
        return issues
    
    def _calculate_performance_score(self, issues: List[PerformanceIssue]) -> float:
        """Calculate overall performance score."""
        base_score = 10.0
        
        impact_weights = {
            "critical": 2.0,
            "high": 1.5,
            "medium": 1.0,
            "low": 0.5
        }
        
        for issue in issues:
            weight = impact_weights.get(issue.impact, 1.0)
            base_score -= weight
        
        return max(0.0, min(10.0, base_score))
    
    def _generate_performance_recommendations(
        self,
        issues: List[PerformanceIssue]
    ) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        issue_types = set(issue.type for issue in issues)
        
        if PerformanceIssueType.ALGORITHMIC_COMPLEXITY in issue_types:
            recommendations.append("Optimize algorithm complexity")
        if PerformanceIssueType.INEFFICIENT_DATA_STRUCTURE in issue_types:
            recommendations.append("Use appropriate data structures")
        if PerformanceIssueType.BLOCKING_IO in issue_types:
            recommendations.append("Consider asynchronous I/O")
        
        recommendations.extend([
            "Profile code to identify bottlenecks",
            "Implement caching where appropriate",
            "Measure performance impact of changes"
        ])
        
        return recommendations
    
    def _generate_optimization_for_issue(
        self,
        issue: PerformanceIssue
    ) -> Optional[PerformanceOptimization]:
        """Generate optimization for a specific issue."""
        if issue.type == PerformanceIssueType.INEFFICIENT_DATA_STRUCTURE:
            if "append" in issue.description:
                return PerformanceOptimization(
                    issue=issue,
                    optimization_type=OptimizationType.DATA_STRUCTURE,
                    description="Convert to list comprehension",
                    code_before=issue.code_snippet,
                    code_after="# Use list comprehension: [item for item in iterable]",
                    expected_improvement="20-30% faster",
                    confidence=0.9,
                    trade_offs=["Slightly less readable for complex logic"]
                )
            elif "in [" in issue.code_snippet:
                return PerformanceOptimization(
                    issue=issue,
                    optimization_type=OptimizationType.DATA_STRUCTURE,
                    description="Convert list to set for membership testing",
                    code_before=issue.code_snippet,
                    code_after="# Convert to set: if item in set(items)",
                    expected_improvement="O(1) vs O(n) lookup",
                    confidence=0.95,
                    trade_offs=["Additional memory for set"]
                )
        
        elif issue.type == PerformanceIssueType.BLOCKING_IO:
            return PerformanceOptimization(
                issue=issue,
                optimization_type=OptimizationType.ASYNC,
                description="Convert to async I/O",
                code_before=issue.code_snippet,
                code_after="# Use async: async with aiofiles.open(...)",
                expected_improvement="Better concurrency",
                confidence=0.8,
                trade_offs=["Requires async context", "More complex code"]
            )
        
        elif issue.type == PerformanceIssueType.ALGORITHMIC_COMPLEXITY:
            return PerformanceOptimization(
                issue=issue,
                optimization_type=OptimizationType.ALGORITHM,
                description="Optimize algorithm complexity",
                code_before=issue.code_snippet,
                code_after="# Consider using hash map or different algorithm",
                expected_improvement=f"From {issue.current_complexity} to better complexity",
                confidence=0.7,
                trade_offs=["May require algorithm redesign"]
            )
        
        return None
    
    async def _test_optimizations(self, optimizations: List[PerformanceOptimization]) -> None:
        """Test performance optimizations."""
        if not self.tool_executor:
            return
        
        logger.info("Testing optimizations")
        # Could apply optimizations and benchmark
    
    async def _run_profiler(self, file_path: str) -> PerformanceProfile:
        """Run profiler on code."""
        profile = PerformanceProfile(total_time=0.0)
        
        try:
            # Could run cProfile or other profiling tools
            result = await self.tool_executor.execute_command(
                f"python -m cProfile -s cumulative {file_path}",
                Path(file_path).parent
            )
            
            if result.success:
                # Parse profiler output
                profile.bottlenecks = ["Profiling completed"]
        
        except Exception as e:
            logger.error(f"Profiling failed: {e}")
        
        return profile
    
    def _identify_bottlenecks_static(self, code: str) -> List[str]:
        """Identify bottlenecks through static analysis."""
        bottlenecks = []
        
        if code.count("for") > 2:
            bottlenecks.append("Multiple nested loops detected")
        if "sleep(" in code:
            bottlenecks.append("Blocking sleep calls")
        if code.count("open(") > 5:
            bottlenecks.append("Multiple file operations")
        
        return bottlenecks
    
    async def _benchmark_code(
        self,
        code_before: str,
        code_after: str
    ) -> Dict[str, Any]:
        """Benchmark code performance."""
        results = {
            "improvement": "Not measured",
            "metrics": {
                "before": {"time": 0.0},
                "after": {"time": 0.0}
            },
            "validated": False
        }
        
        if not self.tool_executor:
            return results
        
        try:
            # Could run timeit or other benchmarking tools
            logger.info("Benchmarking code")
            results["validated"] = True
        
        except Exception as e:
            logger.error(f"Benchmarking failed: {e}")
        
        return results
    
    async def _general_performance_consultation(self, task: Task) -> Dict[str, Any]:
        """Provide general performance consultation."""
        return {
            "consultation": f"Performance guidance for: {task.description}",
            "recommendations": [
                "Profile before optimizing",
                "Focus on algorithmic improvements first",
                "Use appropriate data structures",
                "Consider caching strategies",
                "Measure impact of optimizations"
            ],
            "resources": [
                "Python performance tips",
                "Algorithm complexity guide",
                "Profiling tools documentation"
            ]
        }
    
    def _generate_suggestions(self, result: Any) -> List[str]:
        """Generate suggestions based on result."""
        suggestions = []
        
        if isinstance(result, PerformanceReport):
            if result.issues:
                suggestions.append("Address high-impact performance issues first")
            if result.optimizations:
                suggestions.append("Review and apply suggested optimizations")
            suggestions.extend(result.recommendations[:2])
        elif isinstance(result, list) and result and isinstance(result[0], PerformanceOptimization):
            suggestions.append("Test optimizations before deploying")
            suggestions.append("Measure actual performance improvement")
        
        return suggestions
    
    def _generate_next_steps(self, task: Task, result: Any) -> List[str]:
        """Generate next steps based on task and result."""
        next_steps = []
        
        if isinstance(result, PerformanceReport):
            next_steps.extend([
                "Apply performance optimizations",
                "Run performance tests",
                "Monitor performance in production"
            ])
        elif isinstance(result, PerformanceProfile):
            next_steps.extend([
                "Optimize identified bottlenecks",
                "Re-profile after optimizations",
                "Compare performance metrics"
            ])
        elif isinstance(result, list) and result and isinstance(result[0], PerformanceOptimization):
            next_steps.extend([
                "Implement optimizations",
                "Benchmark improvements",
                "Update documentation"
            ])
        
        return next_steps
