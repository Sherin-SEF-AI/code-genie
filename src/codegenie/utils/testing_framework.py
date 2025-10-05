"""
Testing framework integration and test generation capabilities.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TestingFramework:
    """Testing framework integration and test generation."""
    
    def __init__(self):
        self.test_frameworks = {
            "python": {
                "pytest": {
                    "test_file_patterns": ["test_*.py", "*_test.py"],
                    "test_directory": "tests/",
                    "fixture_patterns": ["conftest.py"],
                    "imports": ["import pytest", "from pytest import"],
                },
                "unittest": {
                    "test_file_patterns": ["test_*.py"],
                    "test_directory": "tests/",
                    "imports": ["import unittest", "from unittest import"],
                },
                "nose": {
                    "test_file_patterns": ["test_*.py", "*_test.py"],
                    "test_directory": "tests/",
                    "imports": ["import nose", "from nose import"],
                }
            },
            "javascript": {
                "jest": {
                    "test_file_patterns": ["*.test.js", "*.spec.js", "__tests__/*.js"],
                    "test_directory": "__tests__/",
                    "config_files": ["jest.config.js", "package.json"],
                    "imports": ["import { describe, it, expect } from '@jest/globals'"],
                },
                "mocha": {
                    "test_file_patterns": ["*.test.js", "*.spec.js"],
                    "test_directory": "test/",
                    "config_files": ["mocha.opts", ".mocharc.js"],
                    "imports": ["import { describe, it } from 'mocha'"],
                },
                "jasmine": {
                    "test_file_patterns": ["*.spec.js"],
                    "test_directory": "spec/",
                    "config_files": ["jasmine.json"],
                    "imports": ["import { describe, it, expect } from 'jasmine'"],
                }
            },
            "typescript": {
                "jest": {
                    "test_file_patterns": ["*.test.ts", "*.spec.ts", "__tests__/*.ts"],
                    "test_directory": "__tests__/",
                    "config_files": ["jest.config.js", "tsconfig.json"],
                    "imports": ["import { describe, it, expect } from '@jest/globals'"],
                },
                "vitest": {
                    "test_file_patterns": ["*.test.ts", "*.spec.ts"],
                    "test_directory": "tests/",
                    "config_files": ["vitest.config.ts"],
                    "imports": ["import { describe, it, expect } from 'vitest'"],
                }
            },
            "go": {
                "testing": {
                    "test_file_patterns": ["*_test.go"],
                    "test_directory": "",
                    "imports": ["import \"testing\""],
                }
            },
            "rust": {
                "cargo_test": {
                    "test_file_patterns": ["*_test.rs", "tests/*.rs"],
                    "test_directory": "tests/",
                    "imports": ["#[cfg(test)]", "use super::*;"],
                }
            }
        }
        
        self.test_types = {
            "unit": "Test individual functions or methods in isolation",
            "integration": "Test interaction between multiple components",
            "end_to_end": "Test complete user workflows",
            "performance": "Test performance characteristics",
            "security": "Test security vulnerabilities",
            "accessibility": "Test accessibility compliance",
        }
    
    def detect_testing_framework(self, project_path: Path) -> Dict[str, Any]:
        """Detect the testing framework used in the project."""
        
        detection = {
            "frameworks": [],
            "test_files": [],
            "coverage_setup": False,
            "ci_integration": False,
            "recommendations": [],
        }
        
        # Analyze project structure
        files = list(project_path.rglob("*"))
        file_names = [f.name for f in files if f.is_file()]
        file_paths = [str(f.relative_to(project_path)) for f in files if f.is_file()]
        
        # Detect language
        language = self._detect_primary_language(project_path)
        
        if language in self.test_frameworks:
            frameworks = self.test_frameworks[language]
            
            for framework_name, config in frameworks.items():
                if self._check_framework_presence(project_path, config, file_names, file_paths):
                    detection["frameworks"].append({
                        "name": framework_name,
                        "language": language,
                        "config": config,
                    })
        
        # Find test files
        detection["test_files"] = self._find_test_files(project_path)
        
        # Check for coverage setup
        detection["coverage_setup"] = self._check_coverage_setup(project_path)
        
        # Check for CI integration
        detection["ci_integration"] = self._check_ci_integration(project_path)
        
        # Generate recommendations
        detection["recommendations"] = self._generate_testing_recommendations(detection, language)
        
        return detection
    
    def _detect_primary_language(self, project_path: Path) -> str:
        """Detect the primary programming language of the project."""
        
        language_counts = {}
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                
                if suffix == '.py':
                    language_counts['python'] = language_counts.get('python', 0) + 1
                elif suffix in ['.js', '.jsx']:
                    language_counts['javascript'] = language_counts.get('javascript', 0) + 1
                elif suffix in ['.ts', '.tsx']:
                    language_counts['typescript'] = language_counts.get('typescript', 0) + 1
                elif suffix == '.go':
                    language_counts['go'] = language_counts.get('go', 0) + 1
                elif suffix == '.rs':
                    language_counts['rust'] = language_counts.get('rust', 0) + 1
        
        return max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else "unknown"
    
    def _check_framework_presence(self, project_path: Path, config: Dict[str, Any], file_names: List[str], file_paths: List[str]) -> bool:
        """Check if a testing framework is present in the project."""
        
        # Check for config files
        if "config_files" in config:
            for config_file in config["config_files"]:
                if config_file in file_names:
                    return True
        
        # Check for test files matching patterns
        if "test_file_patterns" in config:
            for pattern in config["test_file_patterns"]:
                if any(re.match(pattern.replace("*", ".*"), f) for f in file_names):
                    return True
        
        # Check for imports in files
        if "imports" in config:
            for file_path in project_path.rglob("*.py"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if any(imp in content for imp in config["imports"]):
                            return True
                except Exception:
                    continue
        
        return False
    
    def _find_test_files(self, project_path: Path) -> List[Dict[str, Any]]:
        """Find all test files in the project."""
        
        test_files = []
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                # Check if it's a test file based on naming patterns
                if self._is_test_file(file_path):
                    test_info = {
                        "path": str(file_path.relative_to(project_path)),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "language": self._get_file_language(file_path),
                        "test_count": self._count_tests_in_file(file_path),
                    }
                    test_files.append(test_info)
        
        return test_files
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        
        name = file_path.name.lower()
        patterns = [
            "test_", "_test", ".test.", ".spec.", "__tests__"
        ]
        
        return any(pattern in name for pattern in patterns)
    
    def _get_file_language(self, file_path: Path) -> str:
        """Get the programming language of a file."""
        
        suffix = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
        }
        
        return language_map.get(suffix, 'unknown')
    
    def _count_tests_in_file(self, file_path: Path) -> int:
        """Count the number of tests in a file."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count test functions/methods
            test_patterns = [
                r'def test_',  # Python
                r'function test',  # JavaScript
                r'it\(',  # Jest/Mocha
                r'describe\(',  # Jest/Mocha
                r'func Test',  # Go
                r'#\[test\]',  # Rust
            ]
            
            count = 0
            for pattern in test_patterns:
                count += len(re.findall(pattern, content, re.IGNORECASE))
            
            return count
            
        except Exception:
            return 0
    
    def _check_coverage_setup(self, project_path: Path) -> bool:
        """Check if code coverage is set up."""
        
        coverage_indicators = [
            "coverage/", ".coverage", "coverage.xml", "coverage.json",
            "coverage.py", "pytest-cov", "jest --coverage", "nyc"
        ]
        
        for indicator in coverage_indicators:
            if any(indicator in str(f) for f in project_path.rglob("*")):
                return True
        
        return False
    
    def _check_ci_integration(self, project_path: Path) -> bool:
        """Check if testing is integrated with CI/CD."""
        
        ci_files = [
            ".github/workflows/", ".gitlab-ci.yml", "Jenkinsfile",
            ".travis.yml", "circle.yml"
        ]
        
        for ci_file in ci_files:
            if any(ci_file in str(f) for f in project_path.rglob("*")):
                # Check if CI file contains test commands
                try:
                    for file_path in project_path.rglob("*"):
                        if ci_file.replace("/", "").replace(".", "") in str(file_path):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if any(cmd in content.lower() for cmd in ["test", "pytest", "jest", "npm test"]):
                                    return True
                except Exception:
                    continue
        
        return False
    
    def _generate_testing_recommendations(self, detection: Dict[str, Any], language: str) -> List[str]:
        """Generate testing recommendations."""
        
        recommendations = []
        
        if not detection["frameworks"]:
            if language == "python":
                recommendations.append("Add pytest for testing")
            elif language in ["javascript", "typescript"]:
                recommendations.append("Add Jest or Mocha for testing")
            elif language == "go":
                recommendations.append("Use Go's built-in testing package")
            elif language == "rust":
                recommendations.append("Use Cargo's built-in testing")
        
        if not detection["test_files"]:
            recommendations.append("Create test files for your code")
        
        if not detection["coverage_setup"]:
            recommendations.append("Set up code coverage reporting")
        
        if not detection["ci_integration"]:
            recommendations.append("Integrate testing with CI/CD pipeline")
        
        return recommendations
    
    def generate_test_for_function(self, function_code: str, language: str, framework: str = None) -> str:
        """Generate test code for a function."""
        
        if language == "python":
            return self._generate_python_test(function_code, framework)
        elif language in ["javascript", "typescript"]:
            return self._generate_javascript_test(function_code, framework)
        elif language == "go":
            return self._generate_go_test(function_code)
        elif language == "rust":
            return self._generate_rust_test(function_code)
        else:
            return f"# Test generation not supported for {language}"
    
    def _generate_python_test(self, function_code: str, framework: str = None) -> str:
        """Generate Python test code."""
        
        if framework is None:
            framework = "pytest"
        
        # Parse function to extract information
        try:
            tree = ast.parse(function_code)
            function_def = None
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_def = node
                    break
            
            if not function_def:
                return "# Could not parse function definition"
            
            function_name = function_def.name
            args = [arg.arg for arg in function_def.args.args]
            
            # Generate test code
            if framework == "pytest":
                test_code = f"""import pytest
from your_module import {function_name}


def test_{function_name}_basic():
    \"\"\"Test basic functionality of {function_name}.\"\"\"
    # Arrange
    # TODO: Set up test data
    
    # Act
    result = {function_name}({', '.join(['arg' + str(i) for i in range(len(args))])})
    
    # Assert
    assert result is not None
    # TODO: Add specific assertions


def test_{function_name}_edge_cases():
    \"\"\"Test edge cases for {function_name}.\"\"\"
    # Test with None values
    with pytest.raises(ValueError):
        {function_name}(None)
    
    # Test with empty values
    # TODO: Add more edge case tests


def test_{function_name}_error_handling():
    \"\"\"Test error handling in {function_name}.\"\"\"
    # Test invalid inputs
    with pytest.raises((ValueError, TypeError)):
        {function_name}("invalid_input")
"""
            
            elif framework == "unittest":
                test_code = f"""import unittest
from your_module import {function_name}


class Test{function_name.title()}(unittest.TestCase):
    
    def test_{function_name}_basic(self):
        \"\"\"Test basic functionality of {function_name}.\"\"\"
        # Arrange
        # TODO: Set up test data
        
        # Act
        result = {function_name}({', '.join(['arg' + str(i) for i in range(len(args))])})
        
        # Assert
        self.assertIsNotNone(result)
        # TODO: Add specific assertions
    
    def test_{function_name}_edge_cases(self):
        \"\"\"Test edge cases for {function_name}.\"\"\"
        # Test with None values
        with self.assertRaises(ValueError):
            {function_name}(None)
        
        # Test with empty values
        # TODO: Add more edge case tests
    
    def test_{function_name}_error_handling(self):
        \"\"\"Test error handling in {function_name}.\"\"\"
        # Test invalid inputs
        with self.assertRaises((ValueError, TypeError)):
            {function_name}("invalid_input")


if __name__ == '__main__':
    unittest.main()
"""
            
            return test_code
            
        except Exception as e:
            return f"# Error generating test: {e}"
    
    def _generate_javascript_test(self, function_code: str, framework: str = None) -> str:
        """Generate JavaScript test code."""
        
        if framework is None:
            framework = "jest"
        
        # Extract function name (simple regex)
        function_match = re.search(r'function\s+(\w+)|const\s+(\w+)\s*=|let\s+(\w+)\s*=', function_code)
        function_name = None
        
        if function_match:
            function_name = function_match.group(1) or function_match.group(2) or function_match.group(3)
        
        if not function_name:
            return "// Could not extract function name"
        
        if framework == "jest":
            test_code = f"""import {{ {function_name} }} from './your-module';


describe('{function_name}', () => {{
    test('should work with basic input', () => {{
        // Arrange
        const input = 'test_input';
        
        // Act
        const result = {function_name}(input);
        
        // Assert
        expect(result).toBeDefined();
        // TODO: Add specific assertions
    }});
    
    test('should handle edge cases', () => {{
        // Test with null/undefined
        expect(() => {function_name}(null)).toThrow();
        expect(() => {function_name}(undefined)).toThrow();
        
        // Test with empty values
        // TODO: Add more edge case tests
    }});
    
    test('should handle errors gracefully', () => {{
        // Test invalid inputs
        expect(() => {function_name}('invalid_input')).toThrow();
    }});
}});
"""
        
        elif framework == "mocha":
            test_code = f"""const {{ expect }} = require('chai');
const {{ {function_name} }} = require('./your-module');


describe('{function_name}', () => {{
    it('should work with basic input', () => {{
        // Arrange
        const input = 'test_input';
        
        // Act
        const result = {function_name}(input);
        
        // Assert
        expect(result).to.be.defined;
        // TODO: Add specific assertions
    }});
    
    it('should handle edge cases', () => {{
        // Test with null/undefined
        expect(() => {function_name}(null)).to.throw();
        expect(() => {function_name}(undefined)).to.throw();
        
        // Test with empty values
        // TODO: Add more edge case tests
    }});
    
    it('should handle errors gracefully', () => {{
        // Test invalid inputs
        expect(() => {function_name}('invalid_input')).to.throw();
    }});
}});
"""
        
        return test_code
    
    def _generate_go_test(self, function_code: str) -> str:
        """Generate Go test code."""
        
        # Extract function name
        function_match = re.search(r'func\s+(\w+)', function_code)
        if not function_match:
            return "// Could not extract function name"
        
        function_name = function_match.group(1)
        
        test_code = f"""package yourpackage

import (
    "testing"
)


func Test{function_name.title()}(t *testing.T) {{
    t.Run("basic functionality", func(t *testing.T) {{
        // Arrange
        // TODO: Set up test data
        
        // Act
        result := {function_name}()
        
        // Assert
        if result == nil {{
            t.Error("Expected non-nil result")
        }}
        // TODO: Add specific assertions
    }})
    
    t.Run("edge cases", func(t *testing.T) {{
        // Test with nil values
        // TODO: Add edge case tests
    }})
    
    t.Run("error handling", func(t *testing.T) {{
        // Test invalid inputs
        // TODO: Add error handling tests
    }})
}}
"""
        
        return test_code
    
    def _generate_rust_test(self, function_code: str) -> str:
        """Generate Rust test code."""
        
        # Extract function name
        function_match = re.search(r'fn\s+(\w+)', function_code)
        if not function_match:
            return "// Could not extract function name"
        
        function_name = function_match.group(1)
        
        test_code = f"""#[cfg(test)]
mod tests {{
    use super::*;
    
    #[test]
    fn test_{function_name}_basic() {{
        // Arrange
        // TODO: Set up test data
        
        // Act
        let result = {function_name}();
        
        // Assert
        assert!(result.is_some());
        // TODO: Add specific assertions
    }}
    
    #[test]
    fn test_{function_name}_edge_cases() {{
        // Test with None values
        // TODO: Add edge case tests
    }}
    
    #[test]
    fn test_{function_name}_error_handling() {{
        // Test invalid inputs
        // TODO: Add error handling tests
    }}
}}
"""
        
        return test_code
    
    def analyze_test_coverage(self, project_path: Path) -> Dict[str, Any]:
        """Analyze test coverage of the project."""
        
        coverage = {
            "overall_coverage": 0.0,
            "file_coverage": {},
            "uncovered_functions": [],
            "uncovered_classes": [],
            "recommendations": [],
        }
        
        # This is a simplified analysis - in a real implementation,
        # you would integrate with actual coverage tools
        
        # Find all source files
        source_files = []
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.go', '.rs']:
                if not self._is_test_file(file_path):
                    source_files.append(file_path)
        
        # Find all test files
        test_files = [f for f in project_path.rglob("*") if f.is_file() and self._is_test_file(f)]
        
        # Calculate basic coverage metrics
        total_functions = 0
        tested_functions = 0
        
        for source_file in source_files:
            functions = self._extract_functions(source_file)
            total_functions += len(functions)
            
            # Check if functions are tested
            for func in functions:
                if self._is_function_tested(func, test_files):
                    tested_functions += 1
                else:
                    coverage["uncovered_functions"].append({
                        "file": str(source_file.relative_to(project_path)),
                        "function": func,
                    })
        
        if total_functions > 0:
            coverage["overall_coverage"] = tested_functions / total_functions
        
        # Generate recommendations
        if coverage["overall_coverage"] < 0.8:
            coverage["recommendations"].append("Increase test coverage to at least 80%")
        
        if coverage["uncovered_functions"]:
            coverage["recommendations"].append(f"Add tests for {len(coverage['uncovered_functions'])} uncovered functions")
        
        return coverage
    
    def _extract_functions(self, file_path: Path) -> List[str]:
        """Extract function names from a file."""
        
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            suffix = file_path.suffix.lower()
            
            if suffix == '.py':
                # Python functions
                func_matches = re.findall(r'def\s+(\w+)', content)
                functions.extend(func_matches)
            elif suffix in ['.js', '.ts']:
                # JavaScript/TypeScript functions
                func_matches = re.findall(r'function\s+(\w+)|const\s+(\w+)\s*=|let\s+(\w+)\s*=', content)
                for match in func_matches:
                    functions.extend([m for m in match if m])
            elif suffix == '.go':
                # Go functions
                func_matches = re.findall(r'func\s+(\w+)', content)
                functions.extend(func_matches)
            elif suffix == '.rs':
                # Rust functions
                func_matches = re.findall(r'fn\s+(\w+)', content)
                functions.extend(func_matches)
            
        except Exception:
            pass
        
        return functions
    
    def _is_function_tested(self, function_name: str, test_files: List[Path]) -> bool:
        """Check if a function is tested."""
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for function name in test file
                if function_name in content:
                    return True
                    
            except Exception:
                continue
        
        return False
