#!/usr/bin/env python3
"""
Comprehensive test runner for CodeGenie test suite.
Provides easy interface to run different test categories.
"""

import sys
import subprocess
import argparse
from pathlib import Path


class TestRunner:
    """Test runner for comprehensive test suite."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        
    def run_command(self, cmd, description):
        """Run a command and report results."""
        print(f"\n{'='*80}")
        print(f"Running: {description}")
        print(f"{'='*80}\n")
        
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=self.project_root,
            capture_output=False
        )
        
        return result.returncode == 0
    
    def run_all_tests(self, verbose=False):
        """Run all tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/ {v_flag}",
            "All Tests"
        )
    
    def run_e2e_tests(self, verbose=False):
        """Run end-to-end tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/e2e/ {v_flag}",
            "End-to-End Tests"
        )
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/integration/ {v_flag}",
            "Integration Tests"
        )
    
    def run_unit_tests(self, verbose=False):
        """Run unit tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/unit/ {v_flag}",
            "Unit Tests"
        )
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/performance/ {v_flag} -s",
            "Performance Tests"
        )
    
    def run_regression_tests(self, verbose=False):
        """Run regression tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/regression/ {v_flag}",
            "Regression Tests"
        )
    
    def run_scalability_tests(self, verbose=False):
        """Run scalability tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/scalability/ {v_flag} -s",
            "Scalability Tests"
        )
    
    def run_comprehensive_integration(self, verbose=False):
        """Run comprehensive integration tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/e2e/test_comprehensive_integration.py {v_flag}",
            "Comprehensive Integration Tests"
        )
    
    def run_user_experience_tests(self, verbose=False):
        """Run user experience tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/e2e/test_user_experience.py {v_flag}",
            "User Experience Tests"
        )
    
    def run_with_coverage(self, verbose=False):
        """Run tests with coverage report."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/ {v_flag} --cov=src/codegenie --cov-report=html --cov-report=term",
            "Tests with Coverage"
        )
    
    def run_quick_tests(self, verbose=False):
        """Run quick smoke tests."""
        v_flag = "-v" if verbose else ""
        return self.run_command(
            f"python3 -m pytest tests/unit/ tests/regression/ {v_flag} -x",
            "Quick Smoke Tests"
        )
    
    def run_ci_tests(self, verbose=False):
        """Run CI test suite."""
        v_flag = "-v" if verbose else ""
        success = True
        
        # Run in order of importance
        success &= self.run_command(
            f"python3 -m pytest tests/unit/ {v_flag}",
            "CI: Unit Tests"
        )
        
        success &= self.run_command(
            f"python3 -m pytest tests/regression/ {v_flag}",
            "CI: Regression Tests"
        )
        
        success &= self.run_command(
            f"python3 -m pytest tests/integration/ {v_flag}",
            "CI: Integration Tests"
        )
        
        success &= self.run_command(
            f"python3 -m pytest tests/e2e/ {v_flag}",
            "CI: End-to-End Tests"
        )
        
        return success
    
    def validate_syntax(self):
        """Validate test file syntax."""
        print("\nValidating test file syntax...")
        
        test_files = [
            "tests/e2e/test_comprehensive_integration.py",
            "tests/e2e/test_user_experience.py",
            "tests/regression/test_regression_suite.py",
            "tests/scalability/test_system_scalability.py"
        ]
        
        all_valid = True
        
        for test_file in test_files:
            result = subprocess.run(
                f"python3 -c \"import ast; ast.parse(open('{test_file}').read())\"",
                shell=True,
                cwd=self.project_root,
                capture_output=True
            )
            
            if result.returncode == 0:
                print(f"✓ {test_file}")
            else:
                print(f"✗ {test_file}")
                print(result.stderr.decode())
                all_valid = False
        
        return all_valid
    
    def list_tests(self):
        """List all available tests."""
        return self.run_command(
            "python3 -m pytest tests/ --collect-only -q",
            "Available Tests"
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for CodeGenie",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all              Run all tests
  %(prog)s --e2e              Run end-to-end tests
  %(prog)s --quick            Run quick smoke tests
  %(prog)s --coverage         Run tests with coverage
  %(prog)s --validate         Validate test syntax
  %(prog)s --list             List all available tests
        """
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run end-to-end tests"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests"
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests"
    )
    
    parser.add_argument(
        "--regression",
        action="store_true",
        help="Run regression tests"
    )
    
    parser.add_argument(
        "--scalability",
        action="store_true",
        help="Run scalability tests"
    )
    
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive integration tests"
    )
    
    parser.add_argument(
        "--ux",
        action="store_true",
        help="Run user experience tests"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick smoke tests"
    )
    
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run CI test suite"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate test file syntax"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tests"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    success = True
    
    if args.validate:
        success &= runner.validate_syntax()
    
    if args.list:
        success &= runner.list_tests()
    
    if args.all:
        success &= runner.run_all_tests(args.verbose)
    
    if args.e2e:
        success &= runner.run_e2e_tests(args.verbose)
    
    if args.integration:
        success &= runner.run_integration_tests(args.verbose)
    
    if args.unit:
        success &= runner.run_unit_tests(args.verbose)
    
    if args.performance:
        success &= runner.run_performance_tests(args.verbose)
    
    if args.regression:
        success &= runner.run_regression_tests(args.verbose)
    
    if args.scalability:
        success &= runner.run_scalability_tests(args.verbose)
    
    if args.comprehensive:
        success &= runner.run_comprehensive_integration(args.verbose)
    
    if args.ux:
        success &= runner.run_user_experience_tests(args.verbose)
    
    if args.coverage:
        success &= runner.run_with_coverage(args.verbose)
    
    if args.quick:
        success &= runner.run_quick_tests(args.verbose)
    
    if args.ci:
        success &= runner.run_ci_tests(args.verbose)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
