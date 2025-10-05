"""
Integrated safety system combining error detection, recovery, and safe execution.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from .error_detector import ErrorDetector, DetectedError
from .error_recovery import ErrorRecovery, RecoveryResult
from .safe_executor import SafeExecutor, ExecutionContext, ExecutionResult
from .enhanced_file_ops import EnhancedFileOperations, FileValidationResult

logger = logging.getLogger(__name__)


class SafetyReport(BaseModel):
    """Comprehensive safety report for an operation."""
    
    operation_id: str
    operation_type: str
    success: bool
    errors_detected: List[DetectedError] = []
    recovery_attempts: List[RecoveryResult] = []
    execution_result: Optional[ExecutionResult] = None
    file_validation: Optional[FileValidationResult] = None
    security_violations: List[str] = []
    recommendations: List[str] = []
    duration: float = 0.0


class IntegratedSafetySystem:
    """Integrated safety system combining all safety features."""
    
    def __init__(self, config):
        self.config = config
        self.error_detector = ErrorDetector()
        self.error_recovery = ErrorRecovery(config)
        self.safe_executor = SafeExecutor(config)
        self.file_ops = EnhancedFileOperations(config)
        self.safety_reports: List[SafetyReport] = []
    
    async def safe_execute_with_recovery(
        self,
        command: str,
        context: Optional[ExecutionContext] = None,
        max_recovery_attempts: int = 3,
        auto_recover: bool = True,
    ) -> SafetyReport:
        """Execute a command safely with automatic error detection and recovery."""
        
        operation_id = f"exec_{int(asyncio.get_event_loop().time())}"
        start_time = asyncio.get_event_loop().time()
        
        logger.info(f"Starting safe execution with recovery: {command}")
        
        report = SafetyReport(
            operation_id=operation_id,
            operation_type="command_execution",
            success=False,
        )
        
        try:
            # Initial execution attempt
            execution_result = await self.safe_executor.execute_safe(command, context)
            report.execution_result = execution_result
            
            # Check for security violations
            if execution_result.security_violations:
                report.security_violations.extend(execution_result.security_violations)
                report.success = False
                report.recommendations.append("Security violations detected - command blocked")
                return report
            
            # If execution failed, detect errors and attempt recovery
            if not execution_result.success and auto_recover:
                # Detect errors in the output
                error_output = execution_result.stderr or execution_result.stdout
                detected_errors = self.error_detector.detect_errors(error_output)
                report.errors_detected = detected_errors
                
                # Attempt recovery for each detected error
                recovery_attempts = 0
                for error in detected_errors:
                    if recovery_attempts >= max_recovery_attempts:
                        break
                    
                    logger.info(f"Attempting recovery for error: {error.error_type}")
                    recovery_results = await self.error_recovery.recover_from_error(error)
                    report.recovery_attempts.extend(recovery_results)
                    recovery_attempts += 1
                    
                    # If recovery was successful, try executing again
                    if any(result.success for result in recovery_results):
                        logger.info("Recovery successful, retrying execution")
                        execution_result = await self.safe_executor.execute_safe(command, context)
                        report.execution_result = execution_result
                        
                        if execution_result.success:
                            break
            
            # Final success determination
            report.success = report.execution_result.success if report.execution_result else False
            
            # Generate recommendations
            report.recommendations.extend(self._generate_recommendations(report))
            
        except Exception as e:
            logger.error(f"Safe execution failed: {e}")
            report.recommendations.append(f"Execution failed with exception: {str(e)}")
        
        finally:
            end_time = asyncio.get_event_loop().time()
            report.duration = end_time - start_time
            self.safety_reports.append(report)
        
        return report
    
    async def safe_file_operation_with_validation(
        self,
        operation_type: str,
        file_path: Union[str, Path],
        content: Optional[str] = None,
        backup: bool = True,
        validate: bool = True,
    ) -> SafetyReport:
        """Perform safe file operations with comprehensive validation."""
        
        operation_id = f"file_{operation_type}_{int(asyncio.get_event_loop().time())}"
        start_time = asyncio.get_event_loop().time()
        
        logger.info(f"Starting safe file operation: {operation_type} on {file_path}")
        
        report = SafetyReport(
            operation_id=operation_id,
            operation_type=f"file_{operation_type}",
            success=False,
        )
        
        try:
            file_path = Path(file_path)
            
            # Validate file if it exists
            if file_path.exists():
                validation_result = self.file_ops.validate_file(file_path)
                report.file_validation = validation_result
                
                if not validation_result.is_valid:
                    report.security_violations.extend(validation_result.issues)
                    report.recommendations.append("File validation failed - operation blocked")
                    return report
            
            # Perform the file operation
            if operation_type == "create":
                success, message, validation = self.file_ops.safe_create_file(
                    file_path, content or "", backup, validate
                )
            elif operation_type == "modify":
                success, message, validation = self.file_ops.safe_modify_file(
                    file_path, content or "", backup, validate
                )
            elif operation_type == "delete":
                success, message = self.file_ops.safe_delete_file(file_path, backup)
                validation = None
            else:
                report.recommendations.append(f"Unknown operation type: {operation_type}")
                return report
            
            report.success = success
            
            if not success:
                # Detect errors in the failure message
                detected_errors = self.error_detector.detect_errors(message)
                report.errors_detected = detected_errors
                
                # Attempt recovery
                for error in detected_errors:
                    recovery_results = await self.error_recovery.recover_from_error(error)
                    report.recovery_attempts.extend(recovery_results)
            
            # Generate recommendations
            report.recommendations.extend(self._generate_recommendations(report))
            
        except Exception as e:
            logger.error(f"Safe file operation failed: {e}")
            report.recommendations.append(f"File operation failed with exception: {str(e)}")
        
        finally:
            end_time = asyncio.get_event_loop().time()
            report.duration = end_time - start_time
            self.safety_reports.append(report)
        
        return report
    
    async def safe_python_execution_with_analysis(
        self,
        code: str,
        context: Optional[ExecutionContext] = None,
        analyze_code: bool = True,
        auto_fix: bool = True,
    ) -> SafetyReport:
        """Execute Python code safely with analysis and auto-fixing."""
        
        operation_id = f"python_{int(asyncio.get_event_loop().time())}"
        start_time = asyncio.get_event_loop().time()
        
        logger.info("Starting safe Python execution with analysis")
        
        report = SafetyReport(
            operation_id=operation_id,
            operation_type="python_execution",
            success=False,
        )
        
        try:
            # Analyze code for potential issues
            if analyze_code:
                # Create temporary file for analysis
                temp_file = Path("temp_analysis.py")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                validation_result = self.file_ops.validate_file(temp_file)
                report.file_validation = validation_result
                
                if not validation_result.is_valid:
                    report.security_violations.extend(validation_result.issues)
                    report.recommendations.append("Code analysis failed - potential security issues detected")
                    
                    # Attempt to fix issues automatically
                    if auto_fix and validation_result.issues:
                        fixed_code = self._attempt_code_fixes(code, validation_result.issues)
                        if fixed_code != code:
                            code = fixed_code
                            report.recommendations.append("Code automatically fixed based on analysis")
                
                # Clean up temp file
                temp_file.unlink()
            
            # Execute the Python code
            execution_result = await self.safe_executor.execute_python_code(code, context)
            report.execution_result = execution_result
            
            # Check for errors and attempt recovery
            if not execution_result.success:
                error_output = execution_result.stderr or execution_result.stdout
                detected_errors = self.error_detector.detect_errors(error_output)
                report.errors_detected = detected_errors
                
                # Attempt recovery
                for error in detected_errors:
                    recovery_results = await self.error_recovery.recover_from_error(error)
                    report.recovery_attempts.extend(recovery_results)
            
            report.success = execution_result.success
            report.recommendations.extend(self._generate_recommendations(report))
            
        except Exception as e:
            logger.error(f"Safe Python execution failed: {e}")
            report.recommendations.append(f"Python execution failed with exception: {str(e)}")
        
        finally:
            end_time = asyncio.get_event_loop().time()
            report.duration = end_time - start_time
            self.safety_reports.append(report)
        
        return report
    
    def _attempt_code_fixes(self, code: str, issues: List[str]) -> str:
        """Attempt to automatically fix code issues."""
        
        fixed_code = code
        
        for issue in issues:
            if "syntax error" in issue.lower():
                # Basic syntax fixes
                if "missing colon" in issue.lower():
                    # Add missing colons after function/class definitions
                    lines = fixed_code.split('\n')
                    for i, line in enumerate(lines):
                        if (line.strip().endswith(')') and 
                            not line.strip().endswith(':') and
                            ('def ' in line or 'class ' in line or 'if ' in line or 'for ' in line or 'while ' in line)):
                            lines[i] = line + ':'
                    fixed_code = '\n'.join(lines)
                
                elif "unmatched" in issue.lower():
                    # Fix unmatched parentheses/brackets
                    open_parens = fixed_code.count('(')
                    close_parens = fixed_code.count(')')
                    if open_parens > close_parens:
                        fixed_code += ')' * (open_parens - close_parens)
                    
                    open_brackets = fixed_code.count('[')
                    close_brackets = fixed_code.count(']')
                    if open_brackets > close_brackets:
                        fixed_code += ']' * (open_brackets - close_brackets)
            
            elif "indentation" in issue.lower():
                # Fix indentation issues
                lines = fixed_code.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                        # Add basic indentation for function/class bodies
                        if i > 0 and (lines[i-1].strip().endswith(':') or 
                                     'def ' in lines[i-1] or 'class ' in lines[i-1]):
                            lines[i] = '    ' + line
                fixed_code = '\n'.join(lines)
        
        return fixed_code
    
    def _generate_recommendations(self, report: SafetyReport) -> List[str]:
        """Generate recommendations based on the safety report."""
        
        recommendations = []
        
        # Security recommendations
        if report.security_violations:
            recommendations.append("Review and address security violations before proceeding")
        
        # Error-based recommendations
        if report.errors_detected:
            error_categories = set(error.category for error in report.errors_detected)
            
            if "syntax" in error_categories:
                recommendations.append("Use a linter or IDE to catch syntax errors early")
            
            if "import" in error_categories:
                recommendations.append("Set up proper dependency management (requirements.txt, package.json)")
            
            if "runtime" in error_categories:
                recommendations.append("Add more comprehensive error handling and validation")
            
            if "type" in error_categories:
                recommendations.append("Consider adding type hints or using a type checker")
        
        # Recovery recommendations
        if report.recovery_attempts:
            successful_recoveries = sum(1 for result in report.recovery_attempts if result.success)
            if successful_recoveries > 0:
                recommendations.append(f"Automatic recovery successful for {successful_recoveries} issues")
            else:
                recommendations.append("Consider manual intervention for failed recovery attempts")
        
        # Performance recommendations
        if report.duration > 30:  # More than 30 seconds
            recommendations.append("Consider optimizing the operation for better performance")
        
        # General recommendations
        if not report.success:
            recommendations.append("Review the operation and consider alternative approaches")
        
        return recommendations
    
    def get_safety_statistics(self) -> Dict[str, Any]:
        """Get comprehensive safety statistics."""
        
        if not self.safety_reports:
            return {"message": "No safety reports yet"}
        
        total_operations = len(self.safety_reports)
        successful_operations = sum(1 for report in self.safety_reports if report.success)
        
        # Count by operation type
        operation_types = {}
        for report in self.safety_reports:
            op_type = report.operation_type
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
        
        # Count security violations
        total_security_violations = sum(len(report.security_violations) for report in self.safety_reports)
        
        # Count errors detected
        total_errors_detected = sum(len(report.errors_detected) for report in self.safety_reports)
        
        # Count recovery attempts
        total_recovery_attempts = sum(len(report.recovery_attempts) for report in self.safety_reports)
        successful_recoveries = sum(
            sum(1 for result in report.recovery_attempts if result.success)
            for report in self.safety_reports
        )
        
        # Average duration
        total_duration = sum(report.duration for report in self.safety_reports)
        average_duration = total_duration / total_operations if total_operations > 0 else 0.0
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0.0,
            "operation_types": operation_types,
            "security_violations": total_security_violations,
            "errors_detected": total_errors_detected,
            "recovery_attempts": total_recovery_attempts,
            "successful_recoveries": successful_recoveries,
            "recovery_success_rate": successful_recoveries / total_recovery_attempts if total_recovery_attempts > 0 else 0.0,
            "average_duration": average_duration,
        }
    
    def get_recent_reports(self, limit: int = 10) -> List[SafetyReport]:
        """Get recent safety reports."""
        return self.safety_reports[-limit:] if self.safety_reports else []
    
    def clear_history(self) -> None:
        """Clear all safety history."""
        self.safety_reports.clear()
        self.error_detector.clear_history()
        self.error_recovery.clear_history()
        self.safe_executor.clear_execution_history()
        logger.info("Cleared all safety history")
    
    def cleanup(self) -> None:
        """Clean up all resources."""
        self.error_recovery.cleanup()
        self.safe_executor.cleanup()
        self.file_ops.cleanup()
        logger.info("Cleaned up integrated safety system")
