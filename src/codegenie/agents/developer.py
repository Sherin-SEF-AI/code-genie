"""
Developer Agent - Specialized agent for code generation and development tasks.
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


class CodeGenerationType(Enum):
    """Types of code generation."""
    
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    TEST = "test"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    BUG_FIX = "bug_fix"
    FEATURE = "feature"


class ProgrammingLanguage(Enum):
    """Supported programming languages."""
    
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    CSHARP = "csharp"


@dataclass
class CodeSuggestion:
    """Code suggestion or completion."""
    
    code: str
    language: ProgrammingLanguage
    description: str
    confidence: float
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    alternatives: List[str] = field(default_factory=list)
    explanation: str = ""
    imports_needed: List[str] = field(default_factory=list)


@dataclass
class DebugAnalysis:
    """Analysis of a debugging issue."""
    
    issue_description: str
    root_cause: str
    affected_files: List[str] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)
    code_snippets: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class CodeReview:
    """Code review results."""
    
    overall_quality: float  # 0-10
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    security_concerns: List[str] = field(default_factory=list)
    performance_notes: List[str] = field(default_factory=list)


class DeveloperAgent(BaseAgent):
    """
    Specialized agent for code development and generation.
    
    Capabilities:
    - Code generation and completion
    - Debugging assistance
    - Code review and improvement
    - Error resolution
    - Feature implementation
    """
    
    def __init__(
        self,
        config: Config,
        model_router: ModelRouter,
        tool_executor: Optional[ToolExecutor] = None
    ):
        super().__init__(
            name="DeveloperAgent",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.DEBUGGING
            ],
            config=config,
            model_router=model_router
        )
        
        self.tool_executor = tool_executor
        
        # Code generation templates and patterns
        self.code_templates: Dict[str, str] = self._initialize_code_templates()
        self.best_practices: Dict[str, List[str]] = self._initialize_best_practices()
        
        logger.info("Initialized DeveloperAgent")
    
    def _initialize_code_templates(self) -> Dict[str, str]:
        """Initialize code generation templates."""
        return {
            "python_function": '''def {function_name}({parameters}):
    """
    {docstring}
    """
    {body}
''',
            "python_class": '''class {class_name}:
    """
    {docstring}
    """
    
    def __init__(self{init_params}):
        {init_body}
''',
            "test_function": '''def test_{function_name}():
    """Test {function_name} function."""
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assert_statements}
'''
        }
    
    def _initialize_best_practices(self) -> Dict[str, List[str]]:
        """Initialize best practices by language."""
        return {
            "python": [
                "Follow PEP 8 style guide",
                "Use type hints for function signatures",
                "Write docstrings for all public functions and classes",
                "Use list comprehensions for simple transformations",
                "Handle exceptions appropriately",
                "Use context managers for resource management"
            ],
            "typescript": [
                "Use strict type checking",
                "Prefer const over let",
                "Use async/await for asynchronous operations",
                "Implement proper error handling",
                "Follow consistent naming conventions"
            ],
            "general": [
                "Keep functions small and focused",
                "Use meaningful variable names",
                "Avoid deep nesting",
                "Write self-documenting code",
                "Test edge cases"
            ]
        }
    
    async def can_handle_task(self, task: Task) -> bool:
        """Determine if this agent can handle the task."""
        development_keywords = [
            "code", "implement", "function", "class", "debug", "fix",
            "develop", "create", "write", "generate", "bug", "error"
        ]
        
        task_text = f"{task.description} {task.task_type}".lower()
        return any(keyword in task_text for keyword in development_keywords)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Execute a development task."""
        try:
            task_type = task.task_type.lower()
            
            if "generate" in task_type or "create" in task_type or "implement" in task_type:
                result = await self.generate_code(task.context)
            elif "debug" in task_type or "fix" in task_type:
                result = await self.debug_code(task.context)
            elif "review" in task_type:
                result = await self.review_code(task.context)
            elif "complete" in task_type or "suggestion" in task_type:
                result = await self.suggest_code_completion(task.context)
            else:
                # General development assistance
                result = await self._general_development_assistance(task)
            
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=True,
                output=result,
                confidence=0.85,
                reasoning=f"Completed development task: {task.task_type}",
                suggestions=self._generate_suggestions(result),
                next_steps=self._generate_next_steps(task, result)
            )
            
        except Exception as e:
            logger.error(f"DeveloperAgent task execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=False,
                confidence=0.0,
                reasoning=f"Task execution failed: {str(e)}",
                error=str(e)
            )
    
    async def generate_code(self, context: Dict[str, Any]) -> CodeSuggestion:
        """
        Generate code based on requirements.
        
        Args:
            context: Context including requirements, language, and specifications
            
        Returns:
            CodeSuggestion with generated code
        """
        logger.info("Generating code")
        
        generation_type = context.get("type", CodeGenerationType.FUNCTION)
        language = context.get("language", ProgrammingLanguage.PYTHON)
        requirements = context.get("requirements", "")
        specifications = context.get("specifications", {})
        
        # Generate code based on type
        if generation_type == CodeGenerationType.FUNCTION:
            code = self._generate_function(language, specifications)
        elif generation_type == CodeGenerationType.CLASS:
            code = self._generate_class(language, specifications)
        elif generation_type == CodeGenerationType.TEST:
            code = self._generate_test(language, specifications)
        else:
            code = self._generate_generic_code(language, requirements, specifications)
        
        # Identify needed imports
        imports = self._identify_imports(code, language)
        
        # Generate explanation
        explanation = self._generate_code_explanation(code, language, requirements)
        
        suggestion = CodeSuggestion(
            code=code,
            language=language,
            description=requirements,
            confidence=0.85,
            file_path=context.get("file_path"),
            line_number=context.get("line_number"),
            explanation=explanation,
            imports_needed=imports
        )
        
        # Test code if tool executor available
        if self.tool_executor and context.get("test_code", False):
            await self._test_generated_code(suggestion)
        
        logger.info("Code generation completed")
        return suggestion
    
    async def debug_code(self, context: Dict[str, Any]) -> DebugAnalysis:
        """
        Analyze and debug code issues.
        
        Args:
            context: Context including error message, code, and stack trace
            
        Returns:
            DebugAnalysis with root cause and fixes
        """
        logger.info("Debugging code")
        
        error_message = context.get("error_message", "")
        code = context.get("code", "")
        stack_trace = context.get("stack_trace", "")
        file_path = context.get("file_path", "")
        
        # Analyze error
        root_cause = self._analyze_error(error_message, code, stack_trace)
        
        # Identify affected files
        affected_files = self._identify_affected_files(stack_trace, file_path)
        
        # Generate fix suggestions
        suggested_fixes = self._generate_fix_suggestions(error_message, code, root_cause)
        
        # Create code snippets for fixes
        code_snippets = self._create_fix_snippets(code, suggested_fixes)
        
        analysis = DebugAnalysis(
            issue_description=error_message,
            root_cause=root_cause,
            affected_files=affected_files,
            suggested_fixes=suggested_fixes,
            code_snippets=code_snippets,
            confidence=0.8
        )
        
        # Test fixes if tool executor available
        if self.tool_executor and context.get("test_fixes", False):
            await self._test_fixes(analysis, context)
        
        logger.info("Debug analysis completed")
        return analysis
    
    async def review_code(self, context: Dict[str, Any]) -> CodeReview:
        """
        Review code for quality and best practices.
        
        Args:
            context: Context including code to review
            
        Returns:
            CodeReview with analysis and suggestions
        """
        logger.info("Reviewing code")
        
        code = context.get("code", "")
        language = context.get("language", ProgrammingLanguage.PYTHON)
        file_path = context.get("file_path", "")
        
        # Analyze code quality
        quality_score = self._calculate_code_quality(code, language)
        
        # Identify issues
        issues = self._identify_code_issues(code, language)
        
        # Generate suggestions
        suggestions = self._generate_improvement_suggestions(code, language, issues)
        
        # Check best practices
        best_practices = self._check_best_practices(code, language)
        
        # Security analysis
        security_concerns = self._analyze_security(code, language)
        
        # Performance analysis
        performance_notes = self._analyze_performance(code, language)
        
        review = CodeReview(
            overall_quality=quality_score,
            issues=issues,
            suggestions=suggestions,
            best_practices=best_practices,
            security_concerns=security_concerns,
            performance_notes=performance_notes
        )
        
        logger.info(f"Code review completed with quality score: {quality_score}/10")
        return review
    
    async def suggest_code_completion(self, context: Dict[str, Any]) -> List[CodeSuggestion]:
        """
        Suggest code completions.
        
        Args:
            context: Context including partial code and cursor position
            
        Returns:
            List of code completion suggestions
        """
        logger.info("Generating code completions")
        
        partial_code = context.get("partial_code", "")
        cursor_position = context.get("cursor_position", 0)
        language = context.get("language", ProgrammingLanguage.PYTHON)
        
        suggestions = []
        
        # Analyze context
        code_context = self._analyze_code_context(partial_code, cursor_position)
        
        # Generate completions based on context
        if code_context["type"] == "function_call":
            completions = self._suggest_function_completions(code_context, language)
        elif code_context["type"] == "import":
            completions = self._suggest_import_completions(code_context, language)
        elif code_context["type"] == "variable":
            completions = self._suggest_variable_completions(code_context, language)
        else:
            completions = self._suggest_generic_completions(code_context, language)
        
        for completion in completions:
            suggestions.append(CodeSuggestion(
                code=completion["code"],
                language=language,
                description=completion["description"],
                confidence=completion["confidence"],
                explanation=completion.get("explanation", "")
            ))
        
        logger.info(f"Generated {len(suggestions)} code completions")
        return suggestions
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """Provide development expertise."""
        logger.info(f"Providing development expertise for: {question}")
        
        recommendations = []
        
        if "error" in question.lower() or "bug" in question.lower():
            recommendations.extend([
                "Check error messages and stack traces carefully",
                "Use debugger to step through code",
                "Add logging to understand execution flow",
                "Write tests to reproduce the issue"
            ])
        elif "performance" in question.lower():
            recommendations.extend([
                "Profile code to identify bottlenecks",
                "Optimize algorithms and data structures",
                "Use caching where appropriate",
                "Consider asynchronous processing"
            ])
        elif "test" in question.lower():
            recommendations.extend([
                "Write tests before fixing bugs",
                "Aim for high code coverage",
                "Test edge cases and error conditions",
                "Use mocking for external dependencies"
            ])
        else:
            recommendations.extend([
                "Write clean, readable code",
                "Follow language-specific best practices",
                "Document complex logic",
                "Refactor regularly"
            ])
        
        return {
            "expertise": f"Development guidance on: {question}",
            "confidence": 0.85,
            "recommendations": recommendations,
            "code_examples": self._get_relevant_examples(question)
        }
    
    def _generate_function(self, language: ProgrammingLanguage, specs: Dict[str, Any]) -> str:
        """Generate a function."""
        if language == ProgrammingLanguage.PYTHON:
            template = self.code_templates["python_function"]
            return template.format(
                function_name=specs.get("name", "new_function"),
                parameters=specs.get("parameters", ""),
                docstring=specs.get("docstring", "Function description"),
                body=specs.get("body", "pass")
            )
        return "# Function generation not implemented for this language"
    
    def _generate_class(self, language: ProgrammingLanguage, specs: Dict[str, Any]) -> str:
        """Generate a class."""
        if language == ProgrammingLanguage.PYTHON:
            template = self.code_templates["python_class"]
            return template.format(
                class_name=specs.get("name", "NewClass"),
                docstring=specs.get("docstring", "Class description"),
                init_params=specs.get("init_params", ""),
                init_body=specs.get("init_body", "pass")
            )
        return "# Class generation not implemented for this language"
    
    def _generate_test(self, language: ProgrammingLanguage, specs: Dict[str, Any]) -> str:
        """Generate a test."""
        if language == ProgrammingLanguage.PYTHON:
            template = self.code_templates["test_function"]
            return template.format(
                function_name=specs.get("function_name", "function"),
                arrange=specs.get("arrange", "# Setup test data"),
                act=specs.get("act", "# Call function"),
                assert_statements=specs.get("assert", "# Verify results")
            )
        return "# Test generation not implemented for this language"
    
    def _generate_generic_code(
        self,
        language: ProgrammingLanguage,
        requirements: str,
        specs: Dict[str, Any]
    ) -> str:
        """Generate generic code based on requirements."""
        # Simplified implementation
        return f"# Generated code for: {requirements}\n# TODO: Implement based on specifications"
    
    def _identify_imports(self, code: str, language: ProgrammingLanguage) -> List[str]:
        """Identify needed imports for code."""
        imports = []
        
        if language == ProgrammingLanguage.PYTHON:
            # Check for common patterns
            if "Path" in code:
                imports.append("from pathlib import Path")
            if "Dict" in code or "List" in code:
                imports.append("from typing import Dict, List, Optional")
            if "dataclass" in code:
                imports.append("from dataclasses import dataclass")
        
        return imports
    
    def _generate_code_explanation(
        self,
        code: str,
        language: ProgrammingLanguage,
        requirements: str
    ) -> str:
        """Generate explanation for generated code."""
        return f"This code implements {requirements} using {language.value} best practices."
    
    def _analyze_error(self, error_message: str, code: str, stack_trace: str) -> str:
        """Analyze error to find root cause."""
        if "AttributeError" in error_message:
            return "Attempting to access an attribute that doesn't exist"
        elif "TypeError" in error_message:
            return "Type mismatch in operation or function call"
        elif "ValueError" in error_message:
            return "Invalid value passed to function"
        elif "KeyError" in error_message:
            return "Accessing dictionary key that doesn't exist"
        elif "IndexError" in error_message:
            return "List index out of range"
        else:
            return "Error analysis requires more context"
    
    def _identify_affected_files(self, stack_trace: str, file_path: str) -> List[str]:
        """Identify files affected by error."""
        files = []
        if file_path:
            files.append(file_path)
        
        # Parse stack trace for file names
        for line in stack_trace.split("\n"):
            if "File" in line and ".py" in line:
                # Extract file path from stack trace line
                parts = line.split('"')
                if len(parts) >= 2:
                    files.append(parts[1])
        
        return list(set(files))
    
    def _generate_fix_suggestions(
        self,
        error_message: str,
        code: str,
        root_cause: str
    ) -> List[str]:
        """Generate fix suggestions."""
        suggestions = []
        
        if "AttributeError" in error_message:
            suggestions.append("Check if object has the attribute before accessing")
            suggestions.append("Use hasattr() or getattr() with default value")
        elif "TypeError" in error_message:
            suggestions.append("Verify function arguments match expected types")
            suggestions.append("Add type checking or conversion")
        elif "KeyError" in error_message:
            suggestions.append("Use dict.get() with default value")
            suggestions.append("Check if key exists before accessing")
        
        return suggestions
    
    def _create_fix_snippets(self, code: str, suggestions: List[str]) -> Dict[str, str]:
        """Create code snippets for fixes."""
        snippets = {}
        
        for i, suggestion in enumerate(suggestions):
            snippets[f"fix_{i+1}"] = f"# {suggestion}\n# TODO: Apply fix"
        
        return snippets
    
    def _calculate_code_quality(self, code: str, language: ProgrammingLanguage) -> float:
        """Calculate code quality score."""
        score = 7.0  # Base score
        
        # Check for documentation
        if '"""' in code or "'''" in code or "/*" in code:
            score += 1.0
        
        # Check for type hints (Python)
        if language == ProgrammingLanguage.PYTHON and "->" in code:
            score += 0.5
        
        # Penalize very long lines
        lines = code.split("\n")
        if any(len(line) > 120 for line in lines):
            score -= 0.5
        
        # Penalize deep nesting
        max_indent = max((len(line) - len(line.lstrip()) for line in lines if line.strip()), default=0)
        if max_indent > 16:
            score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def _identify_code_issues(self, code: str, language: ProgrammingLanguage) -> List[Dict[str, Any]]:
        """Identify issues in code."""
        issues = []
        
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                issues.append({
                    "line": i,
                    "type": "style",
                    "severity": "low",
                    "message": "Line too long (>120 characters)"
                })
            
            # Check for bare except
            if "except:" in line:
                issues.append({
                    "line": i,
                    "type": "best_practice",
                    "severity": "medium",
                    "message": "Avoid bare except clauses"
                })
        
        return issues
    
    def _generate_improvement_suggestions(
        self,
        code: str,
        language: ProgrammingLanguage,
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        if any(issue["type"] == "style" for issue in issues):
            suggestions.append("Format code according to style guide")
        
        if any(issue["type"] == "best_practice" for issue in issues):
            suggestions.append("Follow language best practices")
        
        if not ('"""' in code or "'''" in code):
            suggestions.append("Add docstrings to functions and classes")
        
        return suggestions
    
    def _check_best_practices(self, code: str, language: ProgrammingLanguage) -> List[str]:
        """Check code against best practices."""
        practices = []
        lang_key = language.value if language.value in self.best_practices else "general"
        
        # Return relevant best practices
        practices.extend(self.best_practices[lang_key][:3])
        
        return practices
    
    def _analyze_security(self, code: str, language: ProgrammingLanguage) -> List[str]:
        """Analyze code for security concerns."""
        concerns = []
        
        # Check for common security issues
        if "eval(" in code:
            concerns.append("Avoid using eval() - security risk")
        if "exec(" in code:
            concerns.append("Avoid using exec() - security risk")
        if "pickle" in code:
            concerns.append("Be cautious with pickle - can execute arbitrary code")
        if "sql" in code.lower() and "%" in code:
            concerns.append("Potential SQL injection - use parameterized queries")
        
        return concerns
    
    def _analyze_performance(self, code: str, language: ProgrammingLanguage) -> List[str]:
        """Analyze code for performance issues."""
        notes = []
        
        # Check for common performance issues
        if "for" in code and "append" in code:
            notes.append("Consider list comprehension for better performance")
        if code.count("for") > 2:
            notes.append("Multiple nested loops - consider optimization")
        
        return notes
    
    def _analyze_code_context(self, partial_code: str, cursor_position: int) -> Dict[str, Any]:
        """Analyze code context for completions."""
        # Simplified context analysis
        before_cursor = partial_code[:cursor_position]
        
        if before_cursor.strip().endswith("import"):
            return {"type": "import", "prefix": ""}
        elif "def " in before_cursor:
            return {"type": "function_call", "prefix": ""}
        else:
            return {"type": "generic", "prefix": ""}
    
    def _suggest_function_completions(
        self,
        context: Dict[str, Any],
        language: ProgrammingLanguage
    ) -> List[Dict[str, Any]]:
        """Suggest function completions."""
        return [
            {
                "code": "function_name()",
                "description": "Function call completion",
                "confidence": 0.8,
                "explanation": "Complete function call"
            }
        ]
    
    def _suggest_import_completions(
        self,
        context: Dict[str, Any],
        language: ProgrammingLanguage
    ) -> List[Dict[str, Any]]:
        """Suggest import completions."""
        if language == ProgrammingLanguage.PYTHON:
            return [
                {
                    "code": "from typing import Dict, List, Optional",
                    "description": "Common typing imports",
                    "confidence": 0.9
                },
                {
                    "code": "from pathlib import Path",
                    "description": "Path handling",
                    "confidence": 0.85
                }
            ]
        return []
    
    def _suggest_variable_completions(
        self,
        context: Dict[str, Any],
        language: ProgrammingLanguage
    ) -> List[Dict[str, Any]]:
        """Suggest variable completions."""
        return [
            {
                "code": "variable_name",
                "description": "Variable completion",
                "confidence": 0.7
            }
        ]
    
    def _suggest_generic_completions(
        self,
        context: Dict[str, Any],
        language: ProgrammingLanguage
    ) -> List[Dict[str, Any]]:
        """Suggest generic completions."""
        return [
            {
                "code": "# TODO: Implement",
                "description": "Generic completion",
                "confidence": 0.6
            }
        ]
    
    async def _test_generated_code(self, suggestion: CodeSuggestion) -> None:
        """Test generated code using tool executor."""
        if not self.tool_executor:
            return
        
        logger.info("Testing generated code")
        # Could write code to temp file and test it
    
    async def _test_fixes(self, analysis: DebugAnalysis, context: Dict[str, Any]) -> None:
        """Test suggested fixes using tool executor."""
        if not self.tool_executor:
            return
        
        logger.info("Testing suggested fixes")
        # Could apply fixes and run tests
    
    async def _general_development_assistance(self, task: Task) -> Dict[str, Any]:
        """Provide general development assistance."""
        return {
            "assistance": f"Development guidance for: {task.description}",
            "recommendations": [
                "Break down complex tasks into smaller steps",
                "Write tests to verify functionality",
                "Follow coding standards and best practices",
                "Document your code"
            ],
            "resources": [
                "Language documentation",
                "Best practices guides",
                "Code examples"
            ]
        }
    
    def _generate_suggestions(self, result: Any) -> List[str]:
        """Generate suggestions based on result."""
        suggestions = []
        
        if isinstance(result, CodeSuggestion):
            suggestions.append("Review generated code for correctness")
            suggestions.append("Add tests for the new code")
            if result.imports_needed:
                suggestions.append("Add required imports")
        elif isinstance(result, DebugAnalysis):
            suggestions.extend(result.suggested_fixes[:2])
        elif isinstance(result, CodeReview):
            suggestions.extend(result.suggestions[:3])
        
        return suggestions
    
    def _generate_next_steps(self, task: Task, result: Any) -> List[str]:
        """Generate next steps based on task and result."""
        next_steps = []
        
        if isinstance(result, CodeSuggestion):
            next_steps.extend([
                "Integrate generated code into project",
                "Write tests for new functionality",
                "Update documentation"
            ])
        elif isinstance(result, DebugAnalysis):
            next_steps.extend([
                "Apply suggested fixes",
                "Test fixes thoroughly",
                "Add regression tests"
            ])
        elif isinstance(result, CodeReview):
            next_steps.extend([
                "Address identified issues",
                "Refactor problematic code",
                "Re-review after changes"
            ])
        
        return next_steps
    
    def _get_relevant_examples(self, question: str) -> List[str]:
        """Get relevant code examples for question."""
        examples = []
        
        if "error handling" in question.lower():
            examples.append("""
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    handle_error(e)
finally:
    cleanup()
""")
        
        return examples
