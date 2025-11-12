"""
Code Generation Engine for Natural Language Programming

This module provides code generation capabilities from natural language requirements,
including template-based and AI-driven code generation with validation and testing.
"""

import re
import ast
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import tempfile
import subprocess

from .nlp_engine import RequirementAnalysis, Intent, Entity, IntentType, EntityType
from .requirement_processor import ClarificationSession
from ..models.model_manager import ModelManager
from ..utils.code_analyzer import CodeAnalyzer


class CodeLanguage(Enum):
    """Supported programming languages for code generation."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"


class GenerationStrategy(Enum):
    """Code generation strategies."""
    TEMPLATE_BASED = "template_based"
    AI_DRIVEN = "ai_driven"
    HYBRID = "hybrid"


class ValidationLevel(Enum):
    """Code validation levels."""
    SYNTAX_ONLY = "syntax_only"
    BASIC_VALIDATION = "basic_validation"
    COMPREHENSIVE = "comprehensive"


@dataclass
class CodeTemplate:
    """Represents a code template for generation."""
    name: str
    language: CodeLanguage
    intent_type: IntentType
    template: str
    placeholders: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    test_template: Optional[str] = None


@dataclass
class GeneratedCode:
    """Represents generated code with metadata."""
    code: str
    language: CodeLanguage
    file_path: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    tests: Optional[str] = None
    documentation: Optional[str] = None
    validation_results: Optional[Dict[str, Any]] = None


@dataclass
class CodeGenerationRequest:
    """Request for code generation."""
    requirement: str
    language: CodeLanguage
    strategy: GenerationStrategy = GenerationStrategy.HYBRID
    validation_level: ValidationLevel = ValidationLevel.COMPREHENSIVE
    include_tests: bool = True
    include_documentation: bool = True
    include_error_handling: bool = True
    target_file: Optional[str] = None
    existing_context: Optional[Dict[str, Any]] = None


@dataclass
class CodeGenerationResult:
    """Result of code generation process."""
    success: bool
    generated_code: Optional[GeneratedCode] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    generation_time: float = 0.0
    validation_passed: bool = False


class CodeGenerator:
    """
    Generates code from natural language requirements using various strategies.
    
    This class provides comprehensive code generation capabilities including
    template-based generation, AI-driven generation, and hybrid approaches.
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager
        self.code_analyzer = CodeAnalyzer()
        self.templates = self._load_templates()
        self._language_configs = self._load_language_configs()
    
    def _load_templates(self) -> Dict[Tuple[IntentType, CodeLanguage], CodeTemplate]:
        """Load code templates for different intents and languages."""
        templates = {}
        
        # Python function template
        templates[(IntentType.CREATE_FUNCTION, CodeLanguage.PYTHON)] = CodeTemplate(
            name="python_function",
            language=CodeLanguage.PYTHON,
            intent_type=IntentType.CREATE_FUNCTION,
            template='''def {function_name}({parameters}){return_type_hint}:
    """
    {docstring}
    
    Args:
{parameter_docs}
    
    Returns:
        {return_description}
    
    Raises:
        {exceptions}
    """
    {error_handling_start}
    {implementation}
    {error_handling_end}''',
            placeholders=[
                "function_name", "parameters", "return_type_hint", "docstring",
                "parameter_docs", "return_description", "exceptions",
                "error_handling_start", "implementation", "error_handling_end"
            ],
            test_template='''def test_{function_name}():
    """Test {function_name} function."""
    # Test normal case
    {normal_test}
    
    # Test edge cases
    {edge_case_tests}
    
    # Test error cases
    {error_tests}'''
        )
        
        # Python class template
        templates[(IntentType.CREATE_CLASS, CodeLanguage.PYTHON)] = CodeTemplate(
            name="python_class",
            language=CodeLanguage.PYTHON,
            intent_type=IntentType.CREATE_CLASS,
            template='''class {class_name}{inheritance}:
    """
    {class_docstring}
    
    Attributes:
{attribute_docs}
    """
    
    def __init__(self{init_parameters}):
        """
        Initialize {class_name}.
        
        Args:
{init_parameter_docs}
        """
        {init_implementation}
    
{methods}''',
            placeholders=[
                "class_name", "inheritance", "class_docstring", "attribute_docs",
                "init_parameters", "init_parameter_docs", "init_implementation", "methods"
            ],
            test_template='''class Test{class_name}:
    """Test suite for {class_name}."""
    
    def setup_method(self):
        """Set up test fixtures."""
        {setup_code}
    
    def test_init(self):
        """Test initialization."""
        {init_tests}
    
{method_tests}'''
        )
        
        # JavaScript function template
        templates[(IntentType.CREATE_FUNCTION, CodeLanguage.JAVASCRIPT)] = CodeTemplate(
            name="javascript_function",
            language=CodeLanguage.JAVASCRIPT,
            intent_type=IntentType.CREATE_FUNCTION,
            template='''/**
 * {docstring}
 * @param {{{parameter_types}}} {parameter_names} - {parameter_descriptions}
 * @returns {{{return_type}}} {return_description}
 * @throws {{{exception_types}}} {exception_descriptions}
 */
{function_type} {function_name}({parameters}) {{
    {error_handling_start}
    {implementation}
    {error_handling_end}
}}''',
            placeholders=[
                "docstring", "parameter_types", "parameter_names", "parameter_descriptions",
                "return_type", "return_description", "exception_types", "exception_descriptions",
                "function_type", "function_name", "parameters", "error_handling_start",
                "implementation", "error_handling_end"
            ],
            test_template='''describe('{function_name}', () => {{
    test('should handle normal cases', () => {{
        {normal_tests}
    }});
    
    test('should handle edge cases', () => {{
        {edge_case_tests}
    }});
    
    test('should handle error cases', () => {{
        {error_tests}
    }});
}});'''
        )
        
        return templates
    
    def _load_language_configs(self) -> Dict[CodeLanguage, Dict[str, Any]]:
        """Load language-specific configurations."""
        return {
            CodeLanguage.PYTHON: {
                "file_extension": ".py",
                "comment_style": "#",
                "docstring_style": '"""',
                "import_style": "import {module}",
                "test_framework": "pytest",
                "syntax_checker": "ast.parse"
            },
            CodeLanguage.JAVASCRIPT: {
                "file_extension": ".js",
                "comment_style": "//",
                "docstring_style": "/**",
                "import_style": "import {{ {items} }} from '{module}';",
                "test_framework": "jest",
                "syntax_checker": "node --check"
            },
            CodeLanguage.TYPESCRIPT: {
                "file_extension": ".ts",
                "comment_style": "//",
                "docstring_style": "/**",
                "import_style": "import {{ {items} }} from '{module}';",
                "test_framework": "jest",
                "syntax_checker": "tsc --noEmit"
            }
        }
    
    async def generate_code(self, request: CodeGenerationRequest, 
                          analysis: Optional[RequirementAnalysis] = None,
                          session: Optional[ClarificationSession] = None) -> CodeGenerationResult:
        """
        Generate code from a natural language requirement.
        
        Args:
            request: Code generation request with requirements and options
            analysis: Optional pre-computed requirement analysis
            session: Optional clarification session with refined requirements
            
        Returns:
            CodeGenerationResult with generated code and validation results
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Use session's final specification if available, otherwise use original requirement
            requirement_text = (
                session.final_specification if session and session.final_specification
                else request.requirement
            )
            
            # Analyze requirement if not provided
            if not analysis:
                from .nlp_engine import NLPEngine
                nlp_engine = NLPEngine(self.model_manager)
                analysis = await nlp_engine.analyze_requirement(requirement_text)
            
            # Generate code based on strategy
            if request.strategy == GenerationStrategy.TEMPLATE_BASED:
                generated_code = await self._generate_template_based(request, analysis)
            elif request.strategy == GenerationStrategy.AI_DRIVEN:
                generated_code = await self._generate_ai_driven(request, analysis)
            else:  # HYBRID
                generated_code = await self._generate_hybrid(request, analysis)
            
            if not generated_code:
                return CodeGenerationResult(
                    success=False,
                    errors=["Failed to generate code"]
                )
            
            # Validate generated code
            validation_passed = False
            if request.validation_level != ValidationLevel.SYNTAX_ONLY:
                validation_results = await self._validate_generated_code(
                    generated_code, request.validation_level
                )
                generated_code.validation_results = validation_results
                validation_passed = validation_results.get("passed", False)
            else:
                # Basic syntax validation
                validation_passed = await self._validate_syntax(generated_code)
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            return CodeGenerationResult(
                success=True,
                generated_code=generated_code,
                validation_passed=validation_passed,
                generation_time=generation_time
            )
            
        except Exception as e:
            generation_time = asyncio.get_event_loop().time() - start_time
            return CodeGenerationResult(
                success=False,
                errors=[f"Code generation failed: {str(e)}"],
                generation_time=generation_time
            )
    
    async def _generate_template_based(self, request: CodeGenerationRequest, 
                                     analysis: RequirementAnalysis) -> Optional[GeneratedCode]:
        """Generate code using template-based approach."""
        if not analysis.intents:
            return None
        
        primary_intent = analysis.intents[0]
        template_key = (primary_intent.type, request.language)
        
        if template_key not in self.templates:
            return None
        
        template = self.templates[template_key]
        
        # Extract values for template placeholders
        placeholder_values = await self._extract_template_values(analysis, request)
        
        # Fill template
        try:
            code = template.template.format(**placeholder_values)
            
            # Generate tests if requested
            tests = None
            if request.include_tests and template.test_template:
                test_values = await self._extract_test_values(analysis, placeholder_values)
                tests = template.test_template.format(**test_values)
            
            # Generate documentation if requested
            documentation = None
            if request.include_documentation:
                documentation = await self._generate_documentation(code, analysis)
            
            return GeneratedCode(
                code=code,
                language=request.language,
                file_path=request.target_file,
                dependencies=template.dependencies,
                tests=tests,
                documentation=documentation
            )
            
        except KeyError as e:
            # Missing placeholder value
            return None
    
    async def _generate_ai_driven(self, request: CodeGenerationRequest, 
                                analysis: RequirementAnalysis) -> Optional[GeneratedCode]:
        """Generate code using AI-driven approach."""
        prompt = await self._create_code_generation_prompt(request, analysis)
        
        try:
            response = await self.model_manager.generate_response(
                prompt=prompt,
                model_type="code_generation",
                max_tokens=2000
            )
            
            # Parse the AI response to extract code, tests, and documentation
            parsed_response = await self._parse_ai_response(response, request.language)
            
            return GeneratedCode(
                code=parsed_response["code"],
                language=request.language,
                file_path=request.target_file,
                dependencies=parsed_response.get("dependencies", []),
                imports=parsed_response.get("imports", []),
                tests=parsed_response.get("tests") if request.include_tests else None,
                documentation=parsed_response.get("documentation") if request.include_documentation else None
            )
            
        except Exception:
            return None
    
    async def _generate_hybrid(self, request: CodeGenerationRequest, 
                             analysis: RequirementAnalysis) -> Optional[GeneratedCode]:
        """Generate code using hybrid approach (template + AI enhancement)."""
        # First try template-based generation
        template_code = await self._generate_template_based(request, analysis)
        
        if template_code:
            # Enhance with AI if available
            if self.model_manager:
                enhanced_code = await self._enhance_with_ai(template_code, request, analysis)
                return enhanced_code or template_code
            return template_code
        
        # Fallback to AI-driven if template fails
        return await self._generate_ai_driven(request, analysis)
    
    async def _extract_template_values(self, analysis: RequirementAnalysis, 
                                     request: CodeGenerationRequest) -> Dict[str, str]:
        """Extract values for template placeholders from analysis."""
        values = {}
        
        # Extract entities
        entities_by_type = {}
        for entity in analysis.entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity.value)
        
        # Function name
        function_names = entities_by_type.get(EntityType.FUNCTION_NAME, [])
        values["function_name"] = function_names[0] if function_names else "generated_function"
        
        # Class name
        class_names = entities_by_type.get(EntityType.CLASS_NAME, [])
        values["class_name"] = class_names[0] if class_names else "GeneratedClass"
        
        # Parameters
        parameters = entities_by_type.get(EntityType.PARAMETER, [])
        if request.language == CodeLanguage.PYTHON:
            values["parameters"] = ", ".join(parameters) if parameters else ""
            values["init_parameters"] = ", " + ", ".join(parameters) if parameters else ""
        else:
            values["parameters"] = ", ".join(parameters) if parameters else ""
        
        # Return type
        return_types = entities_by_type.get(EntityType.RETURN_TYPE, [])
        if request.language == CodeLanguage.PYTHON:
            values["return_type_hint"] = f" -> {return_types[0]}" if return_types else ""
        values["return_type"] = return_types[0] if return_types else "Any"
        
        # Documentation
        values["docstring"] = analysis.original_text
        values["class_docstring"] = analysis.original_text
        values["return_description"] = f"Returns {return_types[0] if return_types else 'result'}"
        
        # Parameter documentation
        if parameters:
            param_docs = []
            for param in parameters:
                param_docs.append(f"        {param}: Description of {param}")
            values["parameter_docs"] = "\n".join(param_docs)
            values["init_parameter_docs"] = "\n".join(param_docs)
        else:
            values["parameter_docs"] = "        None"
            values["init_parameter_docs"] = "        None"
        
        # Attribute documentation
        values["attribute_docs"] = "        None"
        
        # Error handling
        if request.include_error_handling:
            values["error_handling_start"] = "try:"
            values["error_handling_end"] = "except Exception as e:\n        raise"
            values["exceptions"] = "Exception: If an error occurs"
        else:
            values["error_handling_start"] = ""
            values["error_handling_end"] = ""
            values["exceptions"] = "None"
        
        # Implementation placeholder
        values["implementation"] = "    # TODO: Implement functionality\n    pass"
        values["init_implementation"] = "        # TODO: Initialize attributes\n        pass"
        values["methods"] = "    # TODO: Add methods"
        
        # Inheritance
        values["inheritance"] = ""
        
        # JavaScript specific
        values["function_type"] = "function"
        values["parameter_types"] = "Object"
        values["parameter_names"] = ", ".join(parameters) if parameters else ""
        values["parameter_descriptions"] = "Function parameters"
        values["exception_types"] = "Error"
        values["exception_descriptions"] = "If an error occurs"
        
        return values
    
    async def _extract_test_values(self, analysis: RequirementAnalysis, 
                                 placeholder_values: Dict[str, str]) -> Dict[str, str]:
        """Extract values for test template placeholders."""
        test_values = placeholder_values.copy()
        
        # Generate basic test implementations
        function_name = placeholder_values.get("function_name", "test_function")
        class_name = placeholder_values.get("class_name", "TestClass")
        
        test_values["normal_test"] = f"    result = {function_name}()\n    assert result is not None"
        test_values["edge_case_tests"] = f"    # Test edge cases for {function_name}\n    pass"
        test_values["error_tests"] = f"    # Test error cases for {function_name}\n    pass"
        
        # Class-specific tests
        test_values["setup_code"] = f"self.instance = {class_name}()"
        test_values["init_tests"] = f"assert self.instance is not None"
        test_values["method_tests"] = "    # TODO: Add method tests"
        
        # JavaScript tests
        test_values["normal_tests"] = f"expect({function_name}()).toBeDefined();"
        test_values["edge_case_tests"] = "// Add edge case tests"
        test_values["error_tests"] = "// Add error case tests"
        
        return test_values
    
    async def _create_code_generation_prompt(self, request: CodeGenerationRequest, 
                                           analysis: RequirementAnalysis) -> str:
        """Create a prompt for AI-driven code generation."""
        intent_info = ""
        if analysis.intents:
            intent_info = f"Primary Intent: {analysis.intents[0].type.value}\n"
        
        entity_info = ""
        if analysis.entities:
            entities = [f"- {entity.type.value}: {entity.value}" for entity in analysis.entities]
            entity_info = f"Entities:\n{chr(10).join(entities)}\n"
        
        options = []
        if request.include_tests:
            options.append("Include comprehensive unit tests")
        if request.include_documentation:
            options.append("Include detailed documentation and comments")
        if request.include_error_handling:
            options.append("Include proper error handling")
        
        options_text = "\n".join(f"- {option}" for option in options)
        
        return f"""
Generate {request.language.value} code for the following requirement:

Requirement: {request.requirement}

{intent_info}{entity_info}

Requirements:
{options_text}
- Follow {request.language.value} best practices and conventions
- Write clean, readable, and maintainable code
- Include type hints where appropriate

Please provide the code in the following format:
```{request.language.value}
[MAIN CODE]
```

{f'''
```test
[TEST CODE]
``` ''' if request.include_tests else ''}

{f'''
```documentation
[DOCUMENTATION]
```''' if request.include_documentation else ''}

Generated Code:
"""
    
    async def _parse_ai_response(self, response: str, language: CodeLanguage) -> Dict[str, Any]:
        """Parse AI response to extract code components."""
        result = {
            "code": "",
            "tests": None,
            "documentation": None,
            "dependencies": [],
            "imports": []
        }
        
        # Extract code blocks
        code_pattern = rf"```{language.value}\n(.*?)\n```"
        test_pattern = r"```test\n(.*?)\n```"
        doc_pattern = r"```documentation\n(.*?)\n```"
        
        code_match = re.search(code_pattern, response, re.DOTALL | re.IGNORECASE)
        if code_match:
            result["code"] = code_match.group(1).strip()
        
        test_match = re.search(test_pattern, response, re.DOTALL | re.IGNORECASE)
        if test_match:
            result["tests"] = test_match.group(1).strip()
        
        doc_match = re.search(doc_pattern, response, re.DOTALL | re.IGNORECASE)
        if doc_match:
            result["documentation"] = doc_match.group(1).strip()
        
        # Extract imports and dependencies
        if result["code"]:
            result["imports"] = self._extract_imports(result["code"], language)
            result["dependencies"] = self._extract_dependencies(result["code"], language)
        
        return result
    
    def _extract_imports(self, code: str, language: CodeLanguage) -> List[str]:
        """Extract import statements from code."""
        imports = []
        
        if language == CodeLanguage.PYTHON:
            import_patterns = [
                r"^import\s+([^\s]+)",
                r"^from\s+([^\s]+)\s+import"
            ]
        elif language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
            import_patterns = [
                r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
                r"const\s+.*?\s+=\s+require\(['\"]([^'\"]+)['\"]\)"
            ]
        else:
            return imports
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                imports.append(match.group(1))
        
        return imports
    
    def _extract_dependencies(self, code: str, language: CodeLanguage) -> List[str]:
        """Extract external dependencies from code."""
        dependencies = []
        
        # This is a simplified implementation
        # In practice, you'd want more sophisticated dependency detection
        common_deps = {
            CodeLanguage.PYTHON: ["requests", "numpy", "pandas", "flask", "django"],
            CodeLanguage.JAVASCRIPT: ["express", "lodash", "axios", "react", "vue"],
            CodeLanguage.TYPESCRIPT: ["express", "lodash", "axios", "@types/node"]
        }
        
        if language in common_deps:
            for dep in common_deps[language]:
                if dep in code.lower():
                    dependencies.append(dep)
        
        return dependencies
    
    async def _enhance_with_ai(self, template_code: GeneratedCode, 
                             request: CodeGenerationRequest,
                             analysis: RequirementAnalysis) -> Optional[GeneratedCode]:
        """Enhance template-generated code with AI improvements."""
        enhancement_prompt = f"""
Improve and enhance this {request.language.value} code based on the requirement:

Original Requirement: {request.requirement}

Current Code:
```{request.language.value}
{template_code.code}
```

Please enhance the code by:
- Adding proper implementation details
- Improving error handling
- Adding meaningful comments
- Following best practices
- Ensuring the code actually fulfills the requirement

Enhanced Code:
"""
        
        try:
            response = await self.model_manager.generate_response(
                prompt=enhancement_prompt,
                model_type="code_generation",
                max_tokens=1500
            )
            
            # Extract enhanced code
            code_pattern = rf"```{request.language.value}\n(.*?)\n```"
            code_match = re.search(code_pattern, response, re.DOTALL | re.IGNORECASE)
            
            if code_match:
                enhanced_code = code_match.group(1).strip()
                template_code.code = enhanced_code
                return template_code
            
        except Exception:
            pass
        
        return None
    
    async def _validate_generated_code(self, generated_code: GeneratedCode, 
                                     validation_level: ValidationLevel) -> Dict[str, Any]:
        """Validate generated code comprehensively."""
        results = {
            "passed": False,
            "syntax_valid": False,
            "style_issues": [],
            "potential_bugs": [],
            "security_issues": [],
            "performance_issues": []
        }
        
        # Syntax validation
        syntax_valid = await self._validate_syntax(generated_code)
        results["syntax_valid"] = syntax_valid
        
        if not syntax_valid:
            return results
        
        if validation_level == ValidationLevel.SYNTAX_ONLY:
            results["passed"] = True
            return results
        
        # Use code analyzer for deeper validation
        try:
            analysis_result = await self.code_analyzer.analyze_code(
                generated_code.code, 
                generated_code.language.value
            )
            
            results["style_issues"] = analysis_result.get("style_issues", [])
            results["potential_bugs"] = analysis_result.get("potential_bugs", [])
            results["security_issues"] = analysis_result.get("security_issues", [])
            results["performance_issues"] = analysis_result.get("performance_issues", [])
            
            # Determine if validation passed
            if validation_level == ValidationLevel.BASIC_VALIDATION:
                results["passed"] = len(results["potential_bugs"]) == 0
            else:  # COMPREHENSIVE
                total_issues = (
                    len(results["style_issues"]) +
                    len(results["potential_bugs"]) +
                    len(results["security_issues"])
                )
                results["passed"] = total_issues == 0
            
        except Exception:
            results["passed"] = syntax_valid
        
        return results
    
    async def _validate_syntax(self, generated_code: GeneratedCode) -> bool:
        """Validate code syntax."""
        try:
            if generated_code.language == CodeLanguage.PYTHON:
                ast.parse(generated_code.code)
                return True
            elif generated_code.language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
                # For JS/TS, we'd need a proper parser or external tool
                # This is a simplified check
                return "syntax error" not in generated_code.code.lower()
            else:
                # For other languages, assume valid for now
                return True
        except SyntaxError:
            return False
        except Exception:
            return False
    
    async def _generate_documentation(self, code: str, analysis: RequirementAnalysis) -> str:
        """Generate documentation for the code."""
        if not self.model_manager:
            return f"Documentation for: {analysis.original_text}"
        
        doc_prompt = f"""
Generate comprehensive documentation for this code:

Code:
```
{code}
```

Original Requirement: {analysis.original_text}

Please provide:
1. Overview of what the code does
2. Usage examples
3. Parameter descriptions
4. Return value descriptions
5. Any important notes or limitations

Documentation:
"""
        
        try:
            response = await self.model_manager.generate_response(
                prompt=doc_prompt,
                model_type="text_generation",
                max_tokens=800
            )
            return response.strip()
        except Exception:
            return f"Documentation for: {analysis.original_text}"

    async def generate_edge_case_handling(self, generated_code: GeneratedCode, 
                                        analysis: RequirementAnalysis) -> GeneratedCode:
        """Generate additional edge case handling for the code."""
        if not self.model_manager:
            return generated_code
        
        edge_case_prompt = f"""
Analyze this code and add comprehensive edge case handling:

Original Requirement: {analysis.original_text}

Current Code:
```{generated_code.language.value}
{generated_code.code}
```

Please add:
1. Input validation
2. Edge case handling
3. Proper error messages
4. Boundary condition checks
5. Null/undefined checks where appropriate

Enhanced Code with Edge Cases:
"""
        
        try:
            response = await self.model_manager.generate_response(
                prompt=edge_case_prompt,
                model_type="code_generation",
                max_tokens=1500
            )
            
            # Extract enhanced code
            code_pattern = rf"```{generated_code.language.value}\n(.*?)\n```"
            code_match = re.search(code_pattern, response, re.DOTALL | re.IGNORECASE)
            
            if code_match:
                enhanced_code = code_match.group(1).strip()
                generated_code.code = enhanced_code
            
        except Exception:
            pass
        
        return generated_code

    def get_supported_languages(self) -> List[CodeLanguage]:
        """Get list of supported programming languages."""
        return list(CodeLanguage)

    def get_available_templates(self, language: Optional[CodeLanguage] = None) -> List[CodeTemplate]:
        """Get available code templates, optionally filtered by language."""
        if language:
            return [template for (intent, lang), template in self.templates.items() if lang == language]
        return list(self.templates.values())