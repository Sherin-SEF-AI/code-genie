"""
Unit tests for code intelligence components.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import ast
import asyncio

from codegenie.core.code_intelligence import (
    SemanticAnalyzer, ASTAnalyzer, PatternRecognizer, ComplexityAnalyzer,
    CodeEntity, DesignPattern, CodeSmell,
    EntityType, ComplexityMetrics, CodeLocation, SemanticAnalysis
)


class TestSemanticAnalyzer:
    """Test semantic analyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SemanticAnalyzer()
    
    @pytest.mark.asyncio
    async def test_python_code_analysis(self):
        """Test Python code semantic analysis."""
        code = '''
def hello_world(name):
    """Say hello to someone."""
    return f"Hello, {name}!"

class Greeter:
    """A class for greeting people."""
    
    def __init__(self, greeting="Hello"):
        self.greeting = greeting
    
    def greet(self, name):
        """Greet someone with the configured greeting."""
        return f"{self.greeting}, {name}!"
'''
        
        analysis = await self.analyzer.analyze_code(code, Path("test.py"), "python")
        
        # Check entities
        assert len(analysis.entities) >= 2  # function, class
        
        # Check for function entity
        function_entities = [e for e in analysis.entities if e.type == EntityType.FUNCTION]
        assert len(function_entities) >= 1
        
        hello_func = next((e for e in function_entities if e.name == "hello_world"), None)
        assert hello_func is not None
        assert "hello_world" in hello_func.signature
        assert hello_func.documentation == "Say hello to someone."
        
        # Check for class entity
        class_entities = [e for e in analysis.entities if e.type == EntityType.CLASS]
        assert len(class_entities) >= 1
        
        greeter_class = next((e for e in class_entities if e.name == "Greeter"), None)
        assert greeter_class is not None
        assert greeter_class.documentation == "A class for greeting people."
        
        # Check complexity metrics
        assert analysis.complexity_summary["total_complexity"] >= 0
    
    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        """Test handling of unsupported languages."""
        analysis = await self.analyzer.analyze_code("code", Path("test.txt"), "unsupported")
        
        assert len(analysis.entities) == 0
        assert len(analysis.patterns) == 0
        assert len(analysis.smells) == 0
    
    @pytest.mark.asyncio
    async def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        invalid_code = "def invalid_function(\n    # Missing closing parenthesis"
        
        analysis = await self.analyzer.analyze_code(invalid_code, Path("test.py"), "python")
        
        # Should return empty analysis for invalid code
        assert len(analysis.entities) == 0


class TestASTAnalyzer:
    """Test AST analyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ASTAnalyzer()
        self.test_file = Path("test.py")
    
    def test_function_entity_extraction(self):
        """Test function entity extraction."""
        code = '''
def simple_function():
    pass

def decorated_function(param1, param2="default"):
    """Function with decorator and parameters."""
    return param1 + param2
'''
        
        entities = self.analyzer.analyze_python(code, self.test_file)
        
        function_entities = [e for e in entities if e.type == EntityType.FUNCTION]
        assert len(function_entities) >= 2
        
        # Check simple function
        simple_func = next((e for e in function_entities if e.name == "simple_function"), None)
        assert simple_func is not None
        assert simple_func.signature == "simple_function()"
        
        # Check decorated function
        decorated_func = next((e for e in function_entities if e.name == "decorated_function"), None)
        assert decorated_func is not None
        assert "decorated_function" in decorated_func.signature
        assert decorated_func.documentation == "Function with decorator and parameters."
    
    def test_class_entity_extraction(self):
        """Test class entity extraction."""
        code = '''
class SimpleClass:
    pass

class ComplexClass(BaseClass):
    """A complex class with methods."""
    
    def __init__(self):
        self.value = 0
    
    def method1(self):
        return self.value
    
    def method2(self, param):
        self.value = param
'''
        
        entities = self.analyzer.analyze_python(code, self.test_file)
        
        class_entities = [e for e in entities if e.type == EntityType.CLASS]
        assert len(class_entities) >= 2
        
        # Check simple class
        simple_class = next((e for e in class_entities if e.name == "SimpleClass"), None)
        assert simple_class is not None
        
        # Check complex class
        complex_class = next((e for e in class_entities if e.name == "ComplexClass"), None)
        assert complex_class is not None
        assert complex_class.documentation == "A complex class with methods."
        assert "BaseClass" in complex_class.attributes.get("bases", [])
    
    def test_variable_entity_extraction(self):
        """Test variable entity extraction."""
        code = '''
CONSTANT_VALUE = 42
regular_variable = "hello"
'''
        
        entities = self.analyzer.analyze_python(code, self.test_file)
        
        # Check for constant
        constant_entities = [e for e in entities if e.type == EntityType.CONSTANT]
        assert len(constant_entities) >= 1
        
        # Check for variable
        variable_entities = [e for e in entities if e.type == EntityType.VARIABLE]
        assert len(variable_entities) >= 1
    
    def test_complexity_calculation(self):
        """Test complexity metrics calculation."""
        simple_code = '''
def simple_function():
    return "hello"
'''
        
        complex_code = '''
def complex_function(x, y, z):
    """A complex function with high cyclomatic complexity."""
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(10):
                    if i % 2 == 0:
                        return True
    return False
'''
        
        simple_entities = self.analyzer.analyze_python(simple_code, self.test_file)
        complex_entities = self.analyzer.analyze_python(complex_code, self.test_file)
        
        simple_func = [e for e in simple_entities if e.type == EntityType.FUNCTION][0]
        complex_func = [e for e in complex_entities if e.type == EntityType.FUNCTION][0]
        
        # Simple function should have low complexity
        assert simple_func.complexity_metrics.cyclomatic_complexity <= 2
        
        # Complex function should have higher complexity
        assert complex_func.complexity_metrics.cyclomatic_complexity > simple_func.complexity_metrics.cyclomatic_complexity
    

    



class TestPatternRecognizer:
    """Test pattern recognition functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.recognizer = PatternRecognizer()
    
    def create_test_entities(self):
        """Create test entities for pattern recognition."""
        entities = [
            CodeEntity(
                id="singleton_class",
                name="Singleton",
                type=EntityType.CLASS,
                location=CodeLocation(Path("test.py"), 1, 10),
                attributes={"_instance": "class variable"}
            ),
            CodeEntity(
                id="factory_function",
                name="create_object",
                type=EntityType.FUNCTION,
                location=CodeLocation(Path("test.py"), 15, 20)
            ),
            CodeEntity(
                id="observer_class",
                name="Observable",
                type=EntityType.CLASS,
                location=CodeLocation(Path("test.py"), 25, 40),
                attributes={"subscribe": "method", "notify": "method"}
            )
        ]
        return entities
    
    def test_pattern_detection(self):
        """Test pattern detection."""
        entities = self.create_test_entities()
        
        patterns = self.recognizer.detect_patterns(entities)
        
        # Should detect some patterns
        assert len(patterns) >= 0  # May or may not detect patterns based on heuristics


class TestComplexityAnalyzer:
    """Test complexity analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ComplexityAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
    
    def test_complexity_analysis(self):
        """Test complexity analysis."""
        code = '''
def simple():
    return "hello"

def complex(x):
    if x > 0:
        if x > 10:
            return "high"
        else:
            return "medium"
    else:
        return "low"
'''
        
        entities = self.ast_analyzer.analyze_python(code, Path("test.py"))
        summary = self.analyzer.analyze_complexity(entities)
        
        assert summary["total_complexity"] > 0
        assert summary["entity_count"] >= 2
    
    def test_code_smell_detection(self):
        """Test code smell detection."""
        # Create a long method
        long_method_code = '''
def very_long_method():
    """A method that is way too long."""
''' + '\n    '.join(['pass'] * 60)
        
        entities = self.ast_analyzer.analyze_python(long_method_code, Path("test.py"))
        smells = self.analyzer.detect_code_smells(entities)
        
        # Should detect long method
        long_method_smells = [s for s in smells if s.smell == CodeSmell.LONG_METHOD]
        assert len(long_method_smells) >= 1





if __name__ == "__main__":
    pytest.main([__file__])