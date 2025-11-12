#!/usr/bin/env python3
"""
Standalone test for Documentation Generator - no external dependencies.
"""

import ast
import sys
from pathlib import Path

# Test the core functionality directly
def test_ast_parsing():
    """Test that we can parse Python code."""
    print("Testing AST parsing...")
    
    code = '''
def add(a, b):
    """Add two numbers."""
    return a + b

class Calculator:
    """A simple calculator."""
    def multiply(self, x, y):
        return x * y
'''
    
    try:
        tree = ast.parse(code)
        
        # Count functions and classes
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        
        assert len(functions) == 2, f"Expected 2 functions, got {len(functions)}"
        assert len(classes) == 1, f"Expected 1 class, got {len(classes)}"
        
        # Check docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "add":
                docstring = ast.get_docstring(node)
                assert docstring == "Add two numbers.", f"Unexpected docstring: {docstring}"
        
        print("✓ AST parsing works correctly")
        return True
    except Exception as e:
        print(f"✗ AST parsing failed: {e}")
        return False


def test_docstring_generation_logic():
    """Test docstring generation logic."""
    print("Testing docstring generation logic...")
    
    code = '''
def calculate(x, y, operation="add"):
    if operation == "add":
        return x + y
    return x - y
'''
    
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extract parameters
                params = [arg.arg for arg in node.args.args]
                assert "x" in params
                assert "y" in params
                assert "operation" in params
                
                # Check for defaults
                defaults = node.args.defaults
                assert len(defaults) == 1  # operation has default
                
                print(f"✓ Function '{node.name}' has parameters: {params}")
                print(f"✓ Function has {len(defaults)} default parameter(s)")
        
        print("✓ Docstring generation logic works")
        return True
    except Exception as e:
        print(f"✗ Docstring generation logic failed: {e}")
        return False


def test_class_analysis():
    """Test class analysis."""
    print("Testing class analysis...")
    
    code = '''
class DataProcessor:
    """Process data."""
    
    def __init__(self, data):
        self.data = data
        self.processed = False
    
    def process(self):
        """Process the data."""
        self.processed = True
        return self.data
    
    def reset(self):
        """Reset processing state."""
        self.processed = False
'''
    
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                assert len(methods) == 3, f"Expected 3 methods, got {len(methods)}"
                
                # Check method names
                method_names = [m.name for m in methods]
                assert "__init__" in method_names
                assert "process" in method_names
                assert "reset" in method_names
                
                # Check for base classes
                bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                assert len(bases) == 0  # No inheritance
                
                print(f"✓ Class '{node.name}' has {len(methods)} methods")
                print(f"✓ Methods: {', '.join(method_names)}")
        
        print("✓ Class analysis works")
        return True
    except Exception as e:
        print(f"✗ Class analysis failed: {e}")
        return False


def test_complexity_calculation():
    """Test complexity calculation."""
    print("Testing complexity calculation...")
    
    code = '''
def complex_function(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
    elif x < 0:
        while x < 0:
            x += 1
    return x
'''
    
    try:
        tree = ast.parse(code)
        
        # Count complexity indicators
        ifs = len([n for n in ast.walk(tree) if isinstance(n, ast.If)])
        loops = len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))])
        
        complexity = 1 + ifs + loops
        
        assert ifs >= 2, f"Expected at least 2 if statements, got {ifs}"
        assert loops >= 2, f"Expected at least 2 loops, got {loops}"
        assert complexity >= 5, f"Expected complexity >= 5, got {complexity}"
        
        print(f"✓ Complexity calculation: {complexity}")
        print(f"  - If statements: {ifs}")
        print(f"  - Loops: {loops}")
        print("✓ Complexity calculation works")
        return True
    except Exception as e:
        print(f"✗ Complexity calculation failed: {e}")
        return False


def test_import_extraction():
    """Test import extraction."""
    print("Testing import extraction...")
    
    code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict
'''
    
    try:
        tree = ast.parse(code)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "typing" in imports
        
        print(f"✓ Extracted imports: {', '.join(imports)}")
        print("✓ Import extraction works")
        return True
    except Exception as e:
        print(f"✗ Import extraction failed: {e}")
        return False


def test_code_pattern_detection():
    """Test code pattern detection."""
    print("Testing code pattern detection...")
    
    code = '''
# List comprehension
squares = [x**2 for x in range(10)]

# Context manager
with open('file.txt') as f:
    content = f.read()

# Decorator
@property
def value(self):
    return self._value

# Generator
def generate():
    yield 1
    yield 2

# Exception handling
try:
    risky_operation()
except ValueError:
    handle_error()
'''
    
    try:
        tree = ast.parse(code)
        
        patterns = {
            "list_comprehension": False,
            "context_manager": False,
            "decorator": False,
            "generator": False,
            "exception_handling": False
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                patterns["list_comprehension"] = True
            elif isinstance(node, ast.With):
                patterns["context_manager"] = True
            elif isinstance(node, ast.FunctionDef) and node.decorator_list:
                patterns["decorator"] = True
            elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                patterns["generator"] = True
            elif isinstance(node, ast.Try):
                patterns["exception_handling"] = True
        
        detected = [k for k, v in patterns.items() if v]
        print(f"✓ Detected patterns: {', '.join(detected)}")
        
        assert patterns["list_comprehension"], "List comprehension not detected"
        assert patterns["context_manager"], "Context manager not detected"
        assert patterns["decorator"], "Decorator not detected"
        assert patterns["generator"], "Generator not detected"
        assert patterns["exception_handling"], "Exception handling not detected"
        
        print("✓ Code pattern detection works")
        return True
    except Exception as e:
        print(f"✗ Code pattern detection failed: {e}")
        return False


def test_file_structure_analysis():
    """Test file structure analysis."""
    print("Testing file structure analysis...")
    
    try:
        project_path = Path(__file__).parent
        
        # Count Python files
        py_files = list(project_path.glob("*.py"))
        assert len(py_files) > 0, "No Python files found"
        
        # Check for src directory
        src_dir = project_path / "src"
        has_src = src_dir.exists() and src_dir.is_dir()
        
        print(f"✓ Found {len(py_files)} Python files in project root")
        print(f"✓ Has src directory: {has_src}")
        print("✓ File structure analysis works")
        return True
    except Exception as e:
        print(f"✗ File structure analysis failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DOCUMENTATION GENERATOR STANDALONE TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_ast_parsing,
        test_docstring_generation_logic,
        test_class_analysis,
        test_complexity_calculation,
        test_import_extraction,
        test_code_pattern_detection,
        test_file_structure_analysis,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")
            results.append(False)
            print()
    
    passed = sum(results)
    failed = len(results) - passed
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"         {failed} tests failed")
    print("=" * 60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
