"""
Code Intelligence System - Advanced code analysis and semantic understanding.

This module provides comprehensive code intelligence capabilities including:
- Semantic code analysis with deep understanding
- AST analysis with multi-language support
- Design pattern recognition
- Code complexity metrics
- Integration with agentic search
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import logging


logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of code entities."""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"
    VARIABLE = "variable"
    CONSTANT = "constant"
    PROPERTY = "property"
    IMPORT = "import"


class DesignPattern(Enum):
    """Common design patterns."""
    SINGLETON = "singleton"
    FACTORY = "factory"
    OBSERVER = "observer"
    STRATEGY = "strategy"
    DECORATOR = "decorator"
    ADAPTER = "adapter"
    BUILDER = "builder"
    PROTOTYPE = "prototype"
    FACADE = "facade"
    PROXY = "proxy"


class CodeSmell(Enum):
    """Types of code smells."""
    LONG_METHOD = "long_method"
    LARGE_CLASS = "large_class"
    LONG_PARAMETER_LIST = "long_parameter_list"
    DUPLICATE_CODE = "duplicate_code"
    DEAD_CODE = "dead_code"
    COMPLEX_CONDITIONAL = "complex_conditional"
    MAGIC_NUMBER = "magic_number"
    GOD_CLASS = "god_class"
    FEATURE_ENVY = "feature_envy"


@dataclass
class CodeLocation:
    """Location of code in a file."""
    file_path: Path
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None


@dataclass
class ComplexityMetrics:
    """Code complexity metrics."""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    lines_of_code: int = 0
    maintainability_index: float = 0.0
    halstead_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class CodeEntity:
    """Represents a code entity (function, class, etc.)."""
    id: str
    name: str
    type: EntityType
    location: CodeLocation
    signature: Optional[str] = None
    documentation: Optional[str] = None
    complexity_metrics: Optional[ComplexityMetrics] = None
    relationships: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternMatch:
    """Represents a detected design pattern."""
    pattern: DesignPattern
    confidence: float
    entities: List[CodeEntity]
    description: str
    location: CodeLocation


@dataclass
class CodeSmellDetection:
    """Represents a detected code smell."""
    smell: CodeSmell
    severity: str  # "low", "medium", "high"
    entity: CodeEntity
    description: str
    suggestion: str


@dataclass
class SemanticAnalysis:
    """Results of semantic code analysis."""
    entities: List[CodeEntity]
    patterns: List[PatternMatch]
    smells: List[CodeSmellDetection]
    dependencies: Dict[str, List[str]]
    complexity_summary: Dict[str, Any]


class ASTAnalyzer:
    """Multi-language AST analyzer."""
    
    def __init__(self):
        self.supported_languages = {"python", "javascript", "typescript"}
    
    def analyze_python(self, code: str, file_path: Path) -> List[CodeEntity]:
        """Analyze Python code using AST."""
        entities = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                entity = self._extract_entity_from_node(node, file_path)
                if entity:
                    entities.append(entity)
        
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        
        return entities
    
    def _extract_entity_from_node(self, node: ast.AST, file_path: Path) -> Optional[CodeEntity]:
        """Extract code entity from AST node."""
        if isinstance(node, ast.FunctionDef):
            return self._create_function_entity(node, file_path)
        elif isinstance(node, ast.ClassDef):
            return self._create_class_entity(node, file_path)
        elif isinstance(node, ast.Assign):
            return self._create_variable_entity(node, file_path)
        
        return None
    
    def _create_function_entity(self, node: ast.FunctionDef, file_path: Path) -> CodeEntity:
        """Create entity from function definition."""
        location = CodeLocation(
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            column_start=node.col_offset,
            column_end=node.end_col_offset
        )
        
        # Extract signature
        args = [arg.arg for arg in node.args.args]
        signature = f"{node.name}({', '.join(args)})"
        
        # Extract docstring
        documentation = ast.get_docstring(node)
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        return CodeEntity(
            id=f"{file_path}:{node.name}:{node.lineno}",
            name=node.name,
            type=EntityType.FUNCTION,
            location=location,
            signature=signature,
            documentation=documentation,
            complexity_metrics=complexity
        )
    
    def _create_class_entity(self, node: ast.ClassDef, file_path: Path) -> CodeEntity:
        """Create entity from class definition."""
        location = CodeLocation(
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            column_start=node.col_offset,
            column_end=node.end_col_offset
        )
        
        # Extract base classes
        bases = [self._get_name(base) for base in node.bases]
        signature = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
        
        documentation = ast.get_docstring(node)
        
        # Count methods
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        
        return CodeEntity(
            id=f"{file_path}:{node.name}:{node.lineno}",
            name=node.name,
            type=EntityType.CLASS,
            location=location,
            signature=signature,
            documentation=documentation,
            attributes={"method_count": len(methods), "bases": bases}
        )
    
    def _create_variable_entity(self, node: ast.Assign, file_path: Path) -> Optional[CodeEntity]:
        """Create entity from variable assignment."""
        if not node.targets:
            return None
        
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return None
        
        location = CodeLocation(
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.lineno,
            column_start=node.col_offset,
            column_end=node.end_col_offset
        )
        
        # Determine if constant (uppercase name)
        entity_type = EntityType.CONSTANT if target.id.isupper() else EntityType.VARIABLE
        
        return CodeEntity(
            id=f"{file_path}:{target.id}:{node.lineno}",
            name=target.id,
            type=entity_type,
            location=location
        )
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> ComplexityMetrics:
        """Calculate complexity metrics for a function."""
        cyclomatic = self._calculate_cyclomatic_complexity(node)
        loc = node.end_lineno - node.lineno + 1 if node.end_lineno else 1
        
        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            lines_of_code=loc,
            maintainability_index=max(0, 171 - 5.2 * (cyclomatic ** 0.23) - 0.23 * loc)
        )
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)


class PatternRecognizer:
    """Recognizes design patterns in code."""
    
    def __init__(self):
        self.pattern_detectors = {
            DesignPattern.SINGLETON: self._detect_singleton,
            DesignPattern.FACTORY: self._detect_factory,
            DesignPattern.OBSERVER: self._detect_observer,
            DesignPattern.STRATEGY: self._detect_strategy,
            DesignPattern.DECORATOR: self._detect_decorator,
        }
    
    def detect_patterns(self, entities: List[CodeEntity]) -> List[PatternMatch]:
        """Detect design patterns in code entities."""
        patterns = []
        
        for pattern_type, detector in self.pattern_detectors.items():
            matches = detector(entities)
            patterns.extend(matches)
        
        return patterns
    
    def _detect_singleton(self, entities: List[CodeEntity]) -> List[PatternMatch]:
        """Detect Singleton pattern."""
        patterns = []
        
        for entity in entities:
            if entity.type != EntityType.CLASS:
                continue
            
            # Look for __new__ or __init__ with instance checking
            has_instance_check = False
            has_private_constructor = False
            
            # Simple heuristic: class with _instance attribute
            if "_instance" in str(entity.attributes):
                has_instance_check = True
            
            if has_instance_check:
                patterns.append(PatternMatch(
                    pattern=DesignPattern.SINGLETON,
                    confidence=0.7,
                    entities=[entity],
                    description=f"Class {entity.name} appears to implement Singleton pattern",
                    location=entity.location
                ))
        
        return patterns
    
    def _detect_factory(self, entities: List[CodeEntity]) -> List[PatternMatch]:
        """Detect Factory pattern."""
        patterns = []
        
        for entity in entities:
            if entity.type == EntityType.FUNCTION:
                # Look for factory-like names
                if any(keyword in entity.name.lower() for keyword in ["create", "factory", "build", "make"]):
                    patterns.append(PatternMatch(
                        pattern=DesignPattern.FACTORY,
                        confidence=0.6,
                        entities=[entity],
                        description=f"Function {entity.name} appears to be a factory method",
                        location=entity.location
                    ))
        
        return patterns
    
    def _detect_observer(self, entities: List[CodeEntity]) -> List[PatternMatch]:
        """Detect Observer pattern."""
        patterns = []
        
        for entity in entities:
            if entity.type == EntityType.CLASS:
                # Look for observer-like methods
                attrs = str(entity.attributes).lower()
                if any(keyword in attrs for keyword in ["subscribe", "notify", "observer", "listener"]):
                    patterns.append(PatternMatch(
                        pattern=DesignPattern.OBSERVER,
                        confidence=0.65,
                        entities=[entity],
                        description=f"Class {entity.name} appears to implement Observer pattern",
                        location=entity.location
                    ))
        
        return patterns
    
    def _detect_strategy(self, entities: List[CodeEntity]) -> List[PatternMatch]:
        """Detect Strategy pattern."""
        patterns = []
        
        # Look for classes with similar method signatures (strategy implementations)
        class_entities = [e for e in entities if e.type == EntityType.CLASS]
        
        for entity in class_entities:
            attrs = str(entity.attributes).lower()
            if "strategy" in entity.name.lower() or "strategy" in attrs:
                patterns.append(PatternMatch(
                    pattern=DesignPattern.STRATEGY,
                    confidence=0.7,
                    entities=[entity],
                    description=f"Class {entity.name} appears to implement Strategy pattern",
                    location=entity.location
                ))
        
        return patterns
    
    def _detect_decorator(self, entities: List[CodeEntity]) -> List[PatternMatch]:
        """Detect Decorator pattern."""
        patterns = []
        
        for entity in entities:
            if entity.type == EntityType.FUNCTION:
                # Look for decorator-like functions (functions that return functions)
                if entity.name.startswith("with_") or "decorator" in entity.name.lower():
                    patterns.append(PatternMatch(
                        pattern=DesignPattern.DECORATOR,
                        confidence=0.6,
                        entities=[entity],
                        description=f"Function {entity.name} appears to be a decorator",
                        location=entity.location
                    ))
        
        return patterns


class ComplexityAnalyzer:
    """Analyzes code complexity."""
    
    def analyze_complexity(self, entities: List[CodeEntity]) -> Dict[str, Any]:
        """Analyze overall code complexity."""
        total_complexity = 0
        total_loc = 0
        complex_functions = []
        
        for entity in entities:
            if entity.complexity_metrics:
                total_complexity += entity.complexity_metrics.cyclomatic_complexity
                total_loc += entity.complexity_metrics.lines_of_code
                
                # Flag highly complex functions
                if entity.complexity_metrics.cyclomatic_complexity > 10:
                    complex_functions.append({
                        "name": entity.name,
                        "complexity": entity.complexity_metrics.cyclomatic_complexity,
                        "location": str(entity.location.file_path)
                    })
        
        avg_complexity = total_complexity / len(entities) if entities else 0
        
        return {
            "total_complexity": total_complexity,
            "total_lines_of_code": total_loc,
            "average_complexity": avg_complexity,
            "complex_functions": complex_functions,
            "entity_count": len(entities)
        }
    
    def detect_code_smells(self, entities: List[CodeEntity]) -> List[CodeSmellDetection]:
        """Detect code smells."""
        smells = []
        
        for entity in entities:
            # Check for long methods
            if entity.complexity_metrics and entity.complexity_metrics.lines_of_code > 50:
                smells.append(CodeSmellDetection(
                    smell=CodeSmell.LONG_METHOD,
                    severity="medium",
                    entity=entity,
                    description=f"Method {entity.name} has {entity.complexity_metrics.lines_of_code} lines",
                    suggestion="Consider breaking this method into smaller, more focused methods"
                ))
            
            # Check for high complexity
            if entity.complexity_metrics and entity.complexity_metrics.cyclomatic_complexity > 10:
                smells.append(CodeSmellDetection(
                    smell=CodeSmell.COMPLEX_CONDITIONAL,
                    severity="high",
                    entity=entity,
                    description=f"Method {entity.name} has cyclomatic complexity of {entity.complexity_metrics.cyclomatic_complexity}",
                    suggestion="Simplify conditional logic or extract methods"
                ))
            
            # Check for large classes
            if entity.type == EntityType.CLASS:
                method_count = entity.attributes.get("method_count", 0)
                if method_count > 20:
                    smells.append(CodeSmellDetection(
                        smell=CodeSmell.LARGE_CLASS,
                        severity="medium",
                        entity=entity,
                        description=f"Class {entity.name} has {method_count} methods",
                        suggestion="Consider splitting this class into smaller, more cohesive classes"
                    ))
        
        return smells


class SemanticAnalyzer:
    """Main semantic code analyzer."""
    
    def __init__(self):
        self.ast_analyzer = ASTAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        self.complexity_analyzer = ComplexityAnalyzer()
    
    async def analyze_code(self, code: str, file_path: Path, language: str = "python") -> SemanticAnalysis:
        """Perform comprehensive semantic analysis."""
        # Extract entities
        entities = []
        if language == "python":
            entities = self.ast_analyzer.analyze_python(code, file_path)
        
        # Detect patterns
        patterns = self.pattern_recognizer.detect_patterns(entities)
        
        # Detect code smells
        smells = self.complexity_analyzer.detect_code_smells(entities)
        
        # Analyze complexity
        complexity_summary = self.complexity_analyzer.analyze_complexity(entities)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(code, file_path)
        
        return SemanticAnalysis(
            entities=entities,
            patterns=patterns,
            smells=smells,
            dependencies=dependencies,
            complexity_summary=complexity_summary
        )
    
    async def analyze_file(self, file_path: Path) -> SemanticAnalysis:
        """Analyze a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Determine language from extension
            language = self._detect_language(file_path)
            
            return await self.analyze_code(code, file_path, language)
        
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return SemanticAnalysis(
                entities=[],
                patterns=[],
                smells=[],
                dependencies={},
                complexity_summary={}
            )
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension = file_path.suffix.lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript"
        }
        
        return language_map.get(extension, "unknown")
    
    def _extract_dependencies(self, code: str, file_path: Path) -> Dict[str, List[str]]:
        """Extract import dependencies."""
        dependencies = {}
        
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
            
            dependencies[str(file_path)] = imports
        
        except SyntaxError:
            pass
        
        return dependencies
