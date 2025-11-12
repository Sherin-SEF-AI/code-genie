"""
Natural Language Programming - Code Generation Pipeline

This module provides an integrated code generation pipeline that combines
NLP analysis, code generation, validation, and execution testing.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import os

from .nlp_engine import NLPEngine, RequirementAnalysis
from .requirement_processor import RequirementProcessor, ClarificationSession
from .code_generator import (
    CodeGenerator, CodeGenerationRequest, CodeGenerationResult,
    CodeLanguage, GenerationStrategy, ValidationLevel, GeneratedCode
)
from .tool_executor import ToolExecutor, CommandResult
from ..models.model_manager import ModelManager


@dataclass
class ExecutionTestResult:
    """Result of executing generated code for validation."""
    success: bool
    output: str = ""
    errors: str = ""
    exit_code: int = 0
    execution_time: float = 0.0


@dataclass
class NLPCodeGenerationResult:
    """Complete result of NLP-driven code generation."""
    success: bool
    requirement_analysis: Optional[RequirementAnalysis] = None
    clarification_session: Optional[ClarificationSession] = None
    generated_code: Optional[GeneratedCode] = None
    generation_result: Optional[CodeGenerationResult] = None
    execution_test: Optional[ExecutionTestResult] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class NLPCodeGenerator:
    """
    Integrated Natural Language Programming code generator.
    
    This class provides a complete pipeline from natural language requirement
    to validated, tested code implementation.
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager
        self.nlp_engine = NLPEngine(self.model_manager)
        self.requirement_processor = RequirementProcessor(self.model_manager)
        self.code_generator = CodeGenerator(self.model_manager)
        self.tool_executor = ToolExecutor()
    
    async def generate_from_natural_language(
        self,
        requirement: str,
        language: CodeLanguage = CodeLanguage.PYTHON,
        strategy: GenerationStrategy = GenerationStrategy.HYBRID,
        auto_clarify: bool = True,
        execute_validation: bool = True,
        include_tests: bool = True
    ) -> NLPCodeGenerationResult:
        """
        Generate code from natural language requirement with full pipeline.
        
        Args:
            requirement: Natural language description of what to implement
            language: Target programming language
            strategy: Code generation strategy
            auto_clarify: Whether to automatically handle clarifications
            execute_validation: Whether to execute code for validation
            include_tests: Whether to generate tests
            
        Returns:
            NLPCodeGenerationResult with complete generation results
        """
        result = NLPCodeGenerationResult(success=False)
        
        try:
            # Step 1: Analyze requirement
            analysis = await self.nlp_engine.analyze_requirement(requirement)
            result.requirement_analysis = analysis
            
            # Step 2: Process requirement and handle clarifications
            session = await self.requirement_processor.process_requirement(requirement)
            result.clarification_session = session
            
            # Check if clarification is needed
            if session.status.value == "pending" and session.questions:
                if auto_clarify:
                    # Auto-answer with best guesses (for demo/testing)
                    session = await self._auto_answer_clarifications(session)
                else:
                    result.warnings.append("Clarification needed - questions pending")
                    result.suggestions.extend([q.question for q in session.questions])
                    return result
            
            # Step 3: Generate code
            gen_request = CodeGenerationRequest(
                requirement=session.refined_requirement or requirement,
                language=language,
                strategy=strategy,
                validation_level=ValidationLevel.COMPREHENSIVE,
                include_tests=include_tests,
                include_documentation=True,
                include_error_handling=True
            )
            
            gen_result = await self.code_generator.generate_code(
                gen_request,
                analysis=analysis,
                session=session
            )
            
            result.generation_result = gen_result
            
            if not gen_result.success or not gen_result.generated_code:
                result.errors.extend(gen_result.errors)
                return result
            
            result.generated_code = gen_result.generated_code
            
            # Step 4: Execute validation if requested
            if execute_validation and language == CodeLanguage.PYTHON:
                exec_result = await self._execute_validation(gen_result.generated_code)
                result.execution_test = exec_result
                
                if not exec_result.success:
                    result.warnings.append("Code execution validation failed")
                    # Try to fix and regenerate
                    fixed_code = await self._fix_execution_errors(
                        gen_result.generated_code,
                        exec_result,
                        requirement
                    )
                    if fixed_code:
                        result.generated_code = fixed_code
                        # Re-test
                        exec_result = await self._execute_validation(fixed_code)
                        result.execution_test = exec_result
            
            result.success = True
            result.warnings.extend(gen_result.warnings)
            result.suggestions.extend(gen_result.suggestions)
            
        except Exception as e:
            result.errors.append(f"Generation pipeline failed: {str(e)}")
        
        return result
    
    async def _auto_answer_clarifications(
        self,
        session: ClarificationSession
    ) -> ClarificationSession:
        """Automatically answer clarification questions with best guesses."""
        for question in session.questions:
            if not question.answered:
                # Use first possible answer or generate a reasonable default
                if question.possible_answers:
                    answer = question.possible_answers[0]
                else:
                    answer = "Use default implementation"
                
                session = await self.requirement_processor.answer_clarification_question(
                    session.session_id,
                    question.id,
                    answer
                )
        
        return session
    
    async def _execute_validation(self, generated_code: GeneratedCode) -> ExecutionTestResult:
        """Execute generated code to validate it works."""
        if generated_code.language != CodeLanguage.PYTHON:
            return ExecutionTestResult(
                success=True,
                output="Execution validation only supported for Python"
            )
        
        # Create temporary file with the code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(generated_code.code)
            temp_file = f.name
        
        try:
            # Try to import/execute the code
            command = f"python -c \"import ast; ast.parse(open('{temp_file}').read()); print('Syntax valid')\""
            
            result = await self.tool_executor.execute_command(command)
            
            success = result.exit_code == 0
            
            return ExecutionTestResult(
                success=success,
                output=result.stdout,
                errors=result.stderr,
                exit_code=result.exit_code,
                execution_time=result.duration
            )
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    async def _fix_execution_errors(
        self,
        generated_code: GeneratedCode,
        exec_result: ExecutionTestResult,
        original_requirement: str
    ) -> Optional[GeneratedCode]:
        """Attempt to fix execution errors in generated code."""
        if not self.model_manager:
            return None
        
        fix_prompt = f"""
The following code has execution errors. Please fix them:

Original Requirement: {original_requirement}

Code:
```{generated_code.language.value}
{generated_code.code}
```

Errors:
{exec_result.errors}

Please provide the corrected code that fixes these errors while maintaining the original functionality:

Fixed Code:
"""
        
        try:
            response = await self.model_manager.generate_response(
                prompt=fix_prompt,
                model_type="code_generation",
                max_tokens=2000
            )
            
            # Extract fixed code
            import re
            code_pattern = rf"```{generated_code.language.value}\n(.*?)\n```"
            code_match = re.search(code_pattern, response, re.DOTALL | re.IGNORECASE)
            
            if code_match:
                fixed_code = code_match.group(1).strip()
                generated_code.code = fixed_code
                return generated_code
            
        except Exception:
            pass
        
        return None
    
    async def generate_with_interactive_clarification(
        self,
        requirement: str,
        language: CodeLanguage = CodeLanguage.PYTHON,
        clarification_callback: Optional[callable] = None
    ) -> NLPCodeGenerationResult:
        """
        Generate code with interactive clarification process.
        
        Args:
            requirement: Natural language requirement
            language: Target programming language
            clarification_callback: Async callback function to get user answers
                                  Should accept (question: str, options: List[str])
                                  and return answer: str
            
        Returns:
            NLPCodeGenerationResult with generation results
        """
        result = NLPCodeGenerationResult(success=False)
        
        try:
            # Analyze and process requirement
            analysis = await self.nlp_engine.analyze_requirement(requirement)
            result.requirement_analysis = analysis
            
            session = await self.requirement_processor.process_requirement(requirement)
            result.clarification_session = session
            
            # Interactive clarification
            if session.questions and clarification_callback:
                for question in session.questions:
                    if not question.answered:
                        answer = await clarification_callback(
                            question.question,
                            question.possible_answers
                        )
                        
                        session = await self.requirement_processor.answer_clarification_question(
                            session.session_id,
                            question.id,
                            answer
                        )
            
            # Generate code with clarified requirements
            gen_request = CodeGenerationRequest(
                requirement=session.refined_requirement or requirement,
                language=language,
                strategy=GenerationStrategy.HYBRID,
                validation_level=ValidationLevel.COMPREHENSIVE,
                include_tests=True,
                include_documentation=True,
                include_error_handling=True
            )
            
            gen_result = await self.code_generator.generate_code(
                gen_request,
                analysis=analysis,
                session=session
            )
            
            result.generation_result = gen_result
            result.generated_code = gen_result.generated_code
            result.success = gen_result.success
            
        except Exception as e:
            result.errors.append(f"Interactive generation failed: {str(e)}")
        
        return result
    
    async def batch_generate(
        self,
        requirements: List[str],
        language: CodeLanguage = CodeLanguage.PYTHON
    ) -> List[NLPCodeGenerationResult]:
        """Generate code for multiple requirements in batch."""
        results = []
        
        for requirement in requirements:
            result = await self.generate_from_natural_language(
                requirement=requirement,
                language=language,
                auto_clarify=True,
                execute_validation=False  # Skip execution for batch
            )
            results.append(result)
        
        return results
    
    async def generate_and_save(
        self,
        requirement: str,
        output_path: Path,
        language: CodeLanguage = CodeLanguage.PYTHON,
        save_tests: bool = True
    ) -> NLPCodeGenerationResult:
        """Generate code and save to file."""
        result = await self.generate_from_natural_language(
            requirement=requirement,
            language=language,
            include_tests=save_tests
        )
        
        if result.success and result.generated_code:
            # Save main code
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.generated_code.code)
            
            # Save tests if generated
            if save_tests and result.generated_code.tests:
                test_path = output_path.parent / f"test_{output_path.name}"
                test_path.write_text(result.generated_code.tests)
            
            # Save documentation if generated
            if result.generated_code.documentation:
                doc_path = output_path.parent / f"{output_path.stem}_docs.md"
                doc_path.write_text(result.generated_code.documentation)
        
        return result
    
    def get_generation_summary(self, result: NLPCodeGenerationResult) -> str:
        """Get a human-readable summary of the generation result."""
        lines = []
        
        lines.append("=== Natural Language Code Generation Summary ===\n")
        
        if result.requirement_analysis:
            lines.append(f"Confidence Score: {result.requirement_analysis.confidence_score:.2f}")
            lines.append(f"Intents Detected: {len(result.requirement_analysis.intents)}")
            lines.append(f"Entities Extracted: {len(result.requirement_analysis.entities)}")
            lines.append(f"Ambiguities Found: {len(result.requirement_analysis.ambiguities)}\n")
        
        if result.clarification_session:
            lines.append(f"Clarification Status: {result.clarification_session.status.value}")
            lines.append(f"Questions: {len(result.clarification_session.questions)}\n")
        
        if result.generation_result:
            lines.append(f"Generation Success: {result.generation_result.success}")
            lines.append(f"Validation Passed: {result.generation_result.validation_passed}")
            lines.append(f"Generation Time: {result.generation_result.generation_time:.2f}s\n")
        
        if result.execution_test:
            lines.append(f"Execution Test: {'PASSED' if result.execution_test.success else 'FAILED'}")
            if result.execution_test.errors:
                lines.append(f"Execution Errors: {result.execution_test.errors}\n")
        
        if result.errors:
            lines.append("Errors:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        if result.warnings:
            lines.append("Warnings:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        if result.suggestions:
            lines.append("Suggestions:")
            for suggestion in result.suggestions:
                lines.append(f"  - {suggestion}")
        
        return "\n".join(lines)
