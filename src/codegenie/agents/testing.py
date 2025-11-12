"""
Testing Agent - Specialized agent for test generation and quality assurance.
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


class TestType(Enum):
    """Types of tests."""
    
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"


class TestFramework(Enum):
    """Supported test frameworks."""
    
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"
    JUNIT = "junit"


@dataclass
class TestCase:
    """Represents a test case."""
    
    name: str
    test_type: TestType
    description: str
    code: str
    framework: TestFramework
    file_path: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    assertions: List[str] = field(default_factory=list)
    setup_code: str = ""
    teardown_code: str = ""


@dataclass
class TestSuite:
    """Collection of test cases."""
    
    name: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_code: str = ""
    teardown_code: str = ""
    coverage_target: float = 80.0


@dataclass
class TestReport:
    """Test execution report."""
    
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage: float = 0.0
    failures: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class TesterAgent(BaseAgent):
    """
    Specialized agent for test generation and quality assurance.
    
    Capabilities:
    - Test case generation
    - Test strategy development
    - Test execution and reporting
    - Coverage analysis
    """
    
    def __init__(
        self,
        config: Config,
        model_router: ModelRouter,
        tool_executor: Optional[ToolExecutor] = None
    ):
        super().__init__(
            name="TesterAgent",
            capabilities=[
                AgentCapability.TESTING,
                AgentCapability.CODE_ANALYSIS
            ],
            config=config,
            model_router=model_router
        )
        
        self.tool_executor = tool_executor
        self.test_templates: Dict[str, str] = self._initialize_test_templates()
        
        logger.info("Initialized TesterAgent")
    
    def _initialize_test_templates(self) -> Dict[str, str]:
        """Initialize test templates."""
        return {
            "pytest_unit": '''def test_{function_name}():
    """Test {function_name} function."""
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assertions}
''',
            "pytest_class": '''class Test{class_name}:
    """Test suite for {class_name}."""
    
    def setup_method(self):
        """Setup test fixtures."""
        {setup}
    
    def test_{method_name}(self):
        """Test {method_name} method."""
        {test_body}
'''
        }
    
    async def can_handle_task(self, task: Task) -> bool:
        """Determine if this agent can handle the task."""
        testing_keywords = [
            "test", "testing", "coverage", "quality", "assertion",
            "unit test", "integration test", "e2e"
        ]
        
        task_text = f"{task.description} {task.task_type}".lower()
        return any(keyword in task_text for keyword in testing_keywords)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Execute a testing-related task."""
        try:
            task_type = task.task_type.lower()
            
            if "generate" in task_type or "create" in task_type:
                result = await self.generate_tests(task.context)
            elif "run" in task_type or "execute" in task_type:
                result = await self.run_tests(task.context)
            elif "strategy" in task_type:
                result = await self.create_test_strategy(task.context)
            else:
                result = await self._general_testing_consultation(task)
            
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=True,
                output=result,
                confidence=0.85,
                reasoning=f"Completed testing task: {task.task_type}",
                suggestions=self._generate_suggestions(result),
                next_steps=self._generate_next_steps(task, result)
            )
            
        except Exception as e:
            logger.error(f"TesterAgent task execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=False,
                confidence=0.0,
                reasoning=f"Task execution failed: {str(e)}",
                error=str(e)
            )
    
    async def generate_tests(self, context: Dict[str, Any]) -> TestSuite:
        """Generate test cases."""
        logger.info("Generating tests")
        
        code = context.get("code", "")
        test_type = context.get("test_type", TestType.UNIT)
        framework = context.get("framework", TestFramework.PYTEST)
        
        test_cases = []
        
        # Analyze code to generate tests
        if code:
            test_cases = self._generate_test_cases_from_code(code, test_type, framework)
        
        suite = TestSuite(
            name=context.get("suite_name", "TestSuite"),
            test_cases=test_cases,
            coverage_target=context.get("coverage_target", 80.0)
        )
        
        logger.info(f"Generated {len(test_cases)} test cases")
        return suite
    
    async def run_tests(self, context: Dict[str, Any]) -> TestReport:
        """Run tests and generate report."""
        logger.info("Running tests")
        
        test_path = context.get("test_path", "")
        
        report = TestReport()
        
        if self.tool_executor and test_path:
            report = await self._execute_tests(test_path)
        
        logger.info(f"Test execution completed: {report.passed}/{report.total_tests} passed")
        return report
    
    async def create_test_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create testing strategy."""
        logger.info("Creating test strategy")
        
        project_type = context.get("project_type", "")
        
        strategy = {
            "test_types": [TestType.UNIT.value, TestType.INTEGRATION.value],
            "framework": TestFramework.PYTEST.value,
            "coverage_target": 80.0,
            "test_structure": "tests/ directory with mirrors src/ structure",
            "naming_convention": "test_*.py files, test_* functions",
            "best_practices": [
                "Write tests before fixing bugs",
                "Aim for high code coverage",
                "Test edge cases and error conditions",
                "Use fixtures for test data",
                "Keep tests independent"
            ]
        }
        
        logger.info("Test strategy created")
        return strategy
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """Provide testing expertise."""
        logger.info(f"Providing testing expertise for: {question}")
        
        recommendations = [
            "Write tests for all public APIs",
            "Test edge cases and error conditions",
            "Use mocking for external dependencies",
            "Maintain high test coverage",
            "Run tests in CI/CD pipeline"
        ]
        
        return {
            "expertise": f"Testing guidance on: {question}",
            "confidence": 0.85,
            "recommendations": recommendations
        }
    
    def _generate_test_cases_from_code(
        self,
        code: str,
        test_type: TestType,
        framework: TestFramework
    ) -> List[TestCase]:
        """Generate test cases from code."""
        test_cases = []
        
        # Simple function detection
        import re
        functions = re.findall(r'def\s+(\w+)\s*\(', code)
        
        for func_name in functions:
            if not func_name.startswith('_'):  # Skip private functions
                test_case = TestCase(
                    name=f"test_{func_name}",
                    test_type=test_type,
                    description=f"Test {func_name} function",
                    code=self._generate_test_code(func_name, framework),
                    framework=framework,
                    assertions=["assert result is not None"]
                )
                test_cases.append(test_case)
        
        return test_cases
    
    def _generate_test_code(self, function_name: str, framework: TestFramework) -> str:
        """Generate test code."""
        if framework == TestFramework.PYTEST:
            template = self.test_templates["pytest_unit"]
            return template.format(
                function_name=function_name,
                arrange="# Setup test data",
                act=f"result = {function_name}()",
                assertions="assert result is not None"
            )
        return f"# Test for {function_name}"
    
    async def _execute_tests(self, test_path: str) -> TestReport:
        """Execute tests using tool executor."""
        report = TestReport()
        
        try:
            result = await self.tool_executor.execute_command(
                f"pytest {test_path} -v --tb=short",
                Path(test_path).parent
            )
            
            if result.success:
                # Parse pytest output
                report.total_tests = 1
                report.passed = 1
            else:
                report.total_tests = 1
                report.failed = 1
        
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
        
        return report
    
    async def _general_testing_consultation(self, task: Task) -> Dict[str, Any]:
        """Provide general testing consultation."""
        return {
            "consultation": f"Testing guidance for: {task.description}",
            "recommendations": [
                "Follow test-driven development",
                "Write clear test names",
                "Test one thing per test",
                "Use appropriate test types",
                "Maintain test quality"
            ]
        }
    
    def _generate_suggestions(self, result: Any) -> List[str]:
        """Generate suggestions based on result."""
        suggestions = []
        
        if isinstance(result, TestSuite):
            suggestions.append("Review generated tests")
            suggestions.append("Add edge case tests")
        elif isinstance(result, TestReport):
            if result.failed > 0:
                suggestions.append("Fix failing tests")
            if result.coverage < 80:
                suggestions.append("Increase test coverage")
        
        return suggestions
    
    def _generate_next_steps(self, task: Task, result: Any) -> List[str]:
        """Generate next steps."""
        next_steps = []
        
        if isinstance(result, TestSuite):
            next_steps.extend([
                "Run generated tests",
                "Add more test cases",
                "Integrate into CI/CD"
            ])
        elif isinstance(result, TestReport):
            next_steps.extend([
                "Address test failures",
                "Improve coverage",
                "Update test documentation"
            ])
        
        return next_steps
