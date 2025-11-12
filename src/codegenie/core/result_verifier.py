"""
Result Verifier for step-by-step validation in workflows.

This module provides:
- Result verification for workflow steps
- Success criteria validation
- Automatic iteration on failures
- Verification strategies
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime


logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of verification."""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class VerificationMethod(Enum):
    """Method used for verification."""
    OUTPUT_CHECK = "output_check"
    STATE_VALIDATION = "state_validation"
    TEST_EXECUTION = "test_execution"
    MANUAL_REVIEW = "manual_review"
    AUTOMATED_ANALYSIS = "automated_analysis"


@dataclass
class VerificationCriteria:
    """Criteria for verifying a result."""
    name: str
    description: str
    check_fn: Callable[[Any], bool]
    required: bool = True
    weight: float = 1.0


@dataclass
class VerificationResult:
    """Result of verification."""
    status: VerificationStatus
    passed_criteria: List[str]
    failed_criteria: List[str]
    confidence: float
    details: Dict[str, Any]
    suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class IterationPlan:
    """Plan for iterating on a failed step."""
    iteration_number: int
    changes_to_make: List[str]
    expected_improvements: List[str]
    max_iterations: int = 3
    backoff_delay: float = 1.0


class OutputVerifier:
    """Verifies output against expected patterns."""
    
    def __init__(self):
        """Initialize output verifier."""
        self.verification_patterns = {
            'success_indicators': [
                'success', 'completed', 'done', 'finished', 'passed'
            ],
            'failure_indicators': [
                'error', 'failed', 'exception', 'traceback', 'fatal'
            ],
            'warning_indicators': [
                'warning', 'deprecated', 'caution'
            ]
        }
    
    def verify_output(
        self,
        output: str,
        expected_patterns: Optional[List[str]] = None
    ) -> VerificationResult:
        """
        Verify output against expected patterns.
        
        Args:
            output: Output to verify
            expected_patterns: Optional list of expected patterns
            
        Returns:
            VerificationResult
        """
        output_lower = output.lower()
        passed_criteria = []
        failed_criteria = []
        suggestions = []
        
        # Check for success indicators
        has_success = any(
            indicator in output_lower
            for indicator in self.verification_patterns['success_indicators']
        )
        
        # Check for failure indicators
        has_failure = any(
            indicator in output_lower
            for indicator in self.verification_patterns['failure_indicators']
        )
        
        # Check for warnings
        has_warnings = any(
            indicator in output_lower
            for indicator in self.verification_patterns['warning_indicators']
        )
        
        # Determine status
        if has_failure:
            status = VerificationStatus.FAILED
            failed_criteria.append("Output contains failure indicators")
            suggestions.append("Review error messages and fix issues")
        elif has_success:
            status = VerificationStatus.PASSED
            passed_criteria.append("Output contains success indicators")
        else:
            status = VerificationStatus.PARTIAL
            suggestions.append("Output unclear - manual review recommended")
        
        # Check expected patterns if provided
        if expected_patterns:
            for pattern in expected_patterns:
                if pattern.lower() in output_lower:
                    passed_criteria.append(f"Found expected pattern: {pattern}")
                else:
                    failed_criteria.append(f"Missing expected pattern: {pattern}")
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            has_success, has_failure, has_warnings, expected_patterns, output
        )
        
        return VerificationResult(
            status=status,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            confidence=confidence,
            details={
                'has_success': has_success,
                'has_failure': has_failure,
                'has_warnings': has_warnings,
                'output_length': len(output)
            },
            suggestions=suggestions
        )
    
    def _calculate_confidence(
        self,
        has_success: bool,
        has_failure: bool,
        has_warnings: bool,
        expected_patterns: Optional[List[str]],
        output: str
    ) -> float:
        """Calculate confidence in verification result."""
        confidence = 0.5  # Base confidence
        
        if has_success and not has_failure:
            confidence += 0.3
        elif has_failure:
            confidence += 0.4  # High confidence in failure
        
        if expected_patterns:
            # Increase confidence if we have specific patterns to check
            confidence += 0.2
        
        if len(output) > 100:
            # More output generally means more information
            confidence += 0.1
        
        return min(1.0, confidence)


class StateValidator:
    """Validates system state after operations."""
    
    def __init__(self):
        """Initialize state validator."""
        self.state_checks: Dict[str, Callable] = {}
    
    def register_state_check(self, name: str, check_fn: Callable) -> None:
        """
        Register a state validation check.
        
        Args:
            name: Name of the check
            check_fn: Function that performs the check
        """
        self.state_checks[name] = check_fn
    
    async def validate_state(
        self,
        state: Dict[str, Any],
        required_checks: Optional[List[str]] = None
    ) -> VerificationResult:
        """
        Validate system state.
        
        Args:
            state: Current system state
            required_checks: Optional list of specific checks to run
            
        Returns:
            VerificationResult
        """
        passed_criteria = []
        failed_criteria = []
        suggestions = []
        
        # Determine which checks to run
        checks_to_run = required_checks or list(self.state_checks.keys())
        
        # Run each check
        for check_name in checks_to_run:
            if check_name not in self.state_checks:
                failed_criteria.append(f"Unknown check: {check_name}")
                continue
            
            try:
                check_fn = self.state_checks[check_name]
                result = check_fn(state)
                
                if result:
                    passed_criteria.append(f"State check passed: {check_name}")
                else:
                    failed_criteria.append(f"State check failed: {check_name}")
                    suggestions.append(f"Review state for: {check_name}")
            
            except Exception as e:
                failed_criteria.append(f"Error in check {check_name}: {str(e)}")
                suggestions.append(f"Fix check implementation: {check_name}")
        
        # Determine overall status
        if not failed_criteria:
            status = VerificationStatus.PASSED
        elif not passed_criteria:
            status = VerificationStatus.FAILED
        else:
            status = VerificationStatus.PARTIAL
        
        # Calculate confidence
        total_checks = len(checks_to_run)
        passed_checks = len(passed_criteria)
        confidence = passed_checks / max(total_checks, 1)
        
        return VerificationResult(
            status=status,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            confidence=confidence,
            details={
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'state_snapshot': state
            },
            suggestions=suggestions
        )


class TestExecutor:
    """Executes tests to verify results."""
    
    def __init__(self):
        """Initialize test executor."""
        self.test_suites: Dict[str, List[Callable]] = {}
    
    def register_test_suite(self, name: str, tests: List[Callable]) -> None:
        """
        Register a test suite.
        
        Args:
            name: Name of the test suite
            tests: List of test functions
        """
        self.test_suites[name] = tests
    
    async def run_tests(
        self,
        suite_name: str,
        context: Dict[str, Any]
    ) -> VerificationResult:
        """
        Run a test suite.
        
        Args:
            suite_name: Name of the test suite to run
            context: Context for test execution
            
        Returns:
            VerificationResult
        """
        if suite_name not in self.test_suites:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                passed_criteria=[],
                failed_criteria=[f"Test suite not found: {suite_name}"],
                confidence=0.0,
                details={},
                suggestions=["Register the test suite before running"]
            )
        
        tests = self.test_suites[suite_name]
        passed_criteria = []
        failed_criteria = []
        suggestions = []
        
        # Run each test
        for i, test_fn in enumerate(tests):
            try:
                result = test_fn(context)
                
                if result:
                    passed_criteria.append(f"Test {i+1} passed")
                else:
                    failed_criteria.append(f"Test {i+1} failed")
                    suggestions.append(f"Review test {i+1} failure")
            
            except Exception as e:
                failed_criteria.append(f"Test {i+1} error: {str(e)}")
                suggestions.append(f"Fix test {i+1} implementation")
        
        # Determine status
        if not failed_criteria:
            status = VerificationStatus.PASSED
        elif not passed_criteria:
            status = VerificationStatus.FAILED
        else:
            status = VerificationStatus.PARTIAL
        
        # Calculate confidence
        total_tests = len(tests)
        passed_tests = len(passed_criteria)
        confidence = passed_tests / max(total_tests, 1)
        
        return VerificationResult(
            status=status,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            confidence=confidence,
            details={
                'suite_name': suite_name,
                'total_tests': total_tests,
                'passed_tests': passed_tests
            },
            suggestions=suggestions
        )


class ResultVerifier:
    """
    Main result verifier that coordinates verification strategies.
    """
    
    def __init__(self):
        """Initialize result verifier."""
        self.output_verifier = OutputVerifier()
        self.state_validator = StateValidator()
        self.test_executor = TestExecutor()
        self.verification_history: List[VerificationResult] = []
        
        logger.info("Initialized ResultVerifier")
    
    async def verify_result(
        self,
        result: Any,
        criteria: List[VerificationCriteria],
        method: VerificationMethod = VerificationMethod.AUTOMATED_ANALYSIS
    ) -> VerificationResult:
        """
        Verify a result against criteria.
        
        Args:
            result: Result to verify
            criteria: List of verification criteria
            method: Verification method to use
            
        Returns:
            VerificationResult
        """
        logger.info(f"Verifying result using method: {method.value}")
        
        passed_criteria = []
        failed_criteria = []
        suggestions = []
        
        # Check each criterion
        for criterion in criteria:
            try:
                passed = criterion.check_fn(result)
                
                if passed:
                    passed_criteria.append(criterion.name)
                else:
                    failed_criteria.append(criterion.name)
                    
                    if criterion.required:
                        suggestions.append(f"Required criterion failed: {criterion.description}")
            
            except Exception as e:
                failed_criteria.append(criterion.name)
                suggestions.append(f"Error checking {criterion.name}: {str(e)}")
        
        # Determine status
        required_criteria = [c for c in criteria if c.required]
        required_passed = all(
            c.name in passed_criteria
            for c in required_criteria
        )
        
        if required_passed and not failed_criteria:
            status = VerificationStatus.PASSED
        elif not required_passed:
            status = VerificationStatus.FAILED
        else:
            status = VerificationStatus.PARTIAL
        
        # Calculate confidence based on weights
        total_weight = sum(c.weight for c in criteria)
        passed_weight = sum(
            c.weight for c in criteria
            if c.name in passed_criteria
        )
        confidence = passed_weight / max(total_weight, 1)
        
        verification_result = VerificationResult(
            status=status,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            confidence=confidence,
            details={
                'method': method.value,
                'total_criteria': len(criteria),
                'required_criteria': len(required_criteria)
            },
            suggestions=suggestions
        )
        
        self.verification_history.append(verification_result)
        
        logger.info(f"Verification result: {status.value} (confidence: {confidence:.2f})")
        
        return verification_result
    
    async def verify_step_result(
        self,
        step_result: Any,
        success_criteria: List[str],
        context: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify a workflow step result.
        
        Args:
            step_result: Result from step execution
            success_criteria: List of success criteria descriptions
            context: Execution context
            
        Returns:
            VerificationResult
        """
        # Convert success criteria to verification criteria
        criteria = []
        for criterion_desc in success_criteria:
            criterion = VerificationCriteria(
                name=criterion_desc,
                description=criterion_desc,
                check_fn=lambda r: self._check_criterion(r, criterion_desc, context),
                required=True
            )
            criteria.append(criterion)
        
        return await self.verify_result(
            step_result,
            criteria,
            VerificationMethod.AUTOMATED_ANALYSIS
        )
    
    def _check_criterion(
        self,
        result: Any,
        criterion: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check a single criterion."""
        criterion_lower = criterion.lower()
        
        # Check for common success patterns
        if 'success' in criterion_lower or 'complete' in criterion_lower:
            if hasattr(result, 'success'):
                return result.success
            return True
        
        # Check for error absence
        if 'no error' in criterion_lower or 'error-free' in criterion_lower:
            if hasattr(result, 'error'):
                return result.error is None
            return True
        
        # Check for output presence
        if 'output' in criterion_lower or 'result' in criterion_lower:
            if hasattr(result, 'output'):
                return result.output is not None
            return result is not None
        
        # Default: assume success if we got a result
        return result is not None
    
    def create_iteration_plan(
        self,
        verification_result: VerificationResult,
        current_iteration: int = 0
    ) -> IterationPlan:
        """
        Create a plan for iterating on a failed verification.
        
        Args:
            verification_result: Result of failed verification
            current_iteration: Current iteration number
            
        Returns:
            IterationPlan
        """
        changes_to_make = []
        expected_improvements = []
        
        # Analyze failed criteria
        for failed_criterion in verification_result.failed_criteria:
            changes_to_make.append(f"Address: {failed_criterion}")
            expected_improvements.append(f"Pass criterion: {failed_criterion}")
        
        # Add suggestions from verification
        changes_to_make.extend(verification_result.suggestions)
        
        # Adjust based on iteration number
        backoff_delay = 1.0 * (2 ** current_iteration)  # Exponential backoff
        
        return IterationPlan(
            iteration_number=current_iteration + 1,
            changes_to_make=changes_to_make,
            expected_improvements=expected_improvements,
            max_iterations=3,
            backoff_delay=backoff_delay
        )
    
    def should_retry(
        self,
        verification_result: VerificationResult,
        iteration_plan: IterationPlan
    ) -> bool:
        """
        Determine if a step should be retried.
        
        Args:
            verification_result: Result of verification
            iteration_plan: Current iteration plan
            
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if passed
        if verification_result.status == VerificationStatus.PASSED:
            return False
        
        # Don't retry if max iterations reached
        if iteration_plan.iteration_number >= iteration_plan.max_iterations:
            logger.info(f"Max iterations ({iteration_plan.max_iterations}) reached")
            return False
        
        # Retry if there are actionable suggestions
        if verification_result.suggestions:
            return True
        
        # Retry if confidence is low but not zero
        if 0.1 < verification_result.confidence < 0.5:
            return True
        
        return False
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """Get verification statistics."""
        if not self.verification_history:
            return {}
        
        total = len(self.verification_history)
        passed = sum(1 for v in self.verification_history if v.status == VerificationStatus.PASSED)
        failed = sum(1 for v in self.verification_history if v.status == VerificationStatus.FAILED)
        partial = sum(1 for v in self.verification_history if v.status == VerificationStatus.PARTIAL)
        
        avg_confidence = sum(v.confidence for v in self.verification_history) / total
        
        return {
            'total_verifications': total,
            'passed': passed,
            'failed': failed,
            'partial': partial,
            'success_rate': passed / total,
            'average_confidence': avg_confidence
        }
