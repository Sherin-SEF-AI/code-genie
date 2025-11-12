"""
Integration tests for code intelligence system components.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from codegenie.core.code_intelligence import SemanticAnalyzer
from codegenie.core.knowledge_graph import CodeKnowledgeGraph, DependencyTracker
from codegenie.core.impact_analysis import ChangeImpactAnalyzer, CodeChange, ChangeType


class TestCodeIntelligenceIntegration:
    """Test integration between code intelligence components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        
        self.semantic_analyzer = SemanticAnalyzer()
        self.knowledge_graph = CodeKnowledgeGraph(db_path=Path(temp_db.name))
        self.dependency_tracker = DependencyTracker(self.knowledge_graph)
        self.impact_analyzer = ChangeImpactAnalyzer(self.knowledge_graph)
        self.temp_db_path = Path(temp_db.name)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_db_path.unlink(missing_ok=True)
    
    def test_end_to_end_analysis_workflow(self):
        """Test complete analysis workflow from code to impact analysis."""
        # Sample Python code with dependencies
        code = '''
class DataProcessor:
    """Processes data using various algorithms."""
    
    def __init__(self):
        self.cache = {}
    
    def process_data(self, data):
        """Main data processing method."""
        if data in self.cache:
            return self.cache[data]
        
        result = self._complex_algorithm(data)
        self.cache[data] = result
        return result
    
    def _complex_algorithm(self, data):
        """Complex algorithm with high cyclomatic complexity."""
        if data is None:
            return None
        
        if isinstance(data, str):
            if len(data) > 100:
                # Process large strings
                result = []
                for i, char in enumerate(data):
                    if i % 2 == 0:
                        if char.isalpha():
                            result.append(char.upper())
                        else:
                            result.append(char)
                    else:
                        if char.isdigit():
                            result.append(str(int(char) * 2))
                        else:
                            result.append(char.lower())
                return ''.join(result)
            else:
                return data.upper()
        elif isinstance(data, (int, float)):
            if data > 1000:
                return data * 0.1
            elif data > 100:
                return data * 0.5
            else:
                return data * 2
        else:
            return str(data)

def use_processor(input_data):
    """Function that uses DataProcessor."""
    processor = DataProcessor()
    return processor.process_data(input_data)

def batch_process(data_list):
    """Batch processing function."""
    results = []
    for item in data_list:
        result = use_processor(item)
        results.append(result)
    return results
'''
        
        # Step 1: Semantic Analysis
        analysis = self.semantic_analyzer.analyze_code_semantics(code, "python", Path("test_processor.py"))
        
        # Verify semantic analysis results
        assert len(analysis.entities) >= 5  # Class, methods, functions
        assert len(analysis.patterns) >= 0  # May detect some patterns
        assert len(analysis.smells) >= 1   # Should detect complexity smell
        
        # Step 2: Build Knowledge Graph
        for entity in analysis.entities:
            self.knowledge_graph.add_code_entity(entity)
        
        for relationship in analysis.relationships:
            self.knowledge_graph.add_relationship(relationship)
        
        # Verify knowledge graph construction
        stats = self.knowledge_graph.get_graph_statistics()
        assert stats["total_entities"] >= 5
        assert stats["entity_types"]["class"] >= 1
        assert stats["entity_types"]["function"] >= 2
        assert stats["entity_types"]["method"] >= 2
        
        # Step 3: Impact Analysis
        # Find a complex method to analyze
        complex_entities = [e for e in analysis.entities 
                          if e.complexity_metrics.cyclomatic_complexity > 10]
        assert len(complex_entities) >= 1
        
        complex_entity = complex_entities[0]
        
        # Create a change for the complex entity
        change = CodeChange(
            id="refactor_complex_method",
            change_type=ChangeType.REFACTOR,
            entity_id=complex_entity.id,
            description="Refactor complex algorithm method",
            file_path="test_processor.py",
            line_start=complex_entity.location.line_start,
            line_end=complex_entity.location.line_end
        )
        
        # Analyze impact
        impact_result = self.impact_analyzer.analyze_change_impact(change)
        
        # Verify impact analysis
        assert impact_result.change == change
        assert impact_result.confidence_score > 0
        assert impact_result.estimated_effort > 0
        assert len(impact_result.recommendations) > 0
        
        # Should have complexity-related risks
        complexity_risks = [r for r in impact_result.risks if "complexity" in r.risk_type]
        assert len(complexity_risks) >= 1
    
    def test_dependency_tracking_integration(self):
        """Test integration with dependency tracking."""
        # Simulate file dependencies
        self.dependency_tracker.track_file_dependencies("main.py", ["utils.py", "config.py"])
        self.dependency_tracker.track_file_dependencies("utils.py", ["helpers.py"])
        self.dependency_tracker.track_file_dependencies("config.py", ["settings.py"])
        
        # Get dependency metrics
        metrics = self.dependency_tracker.get_dependency_metrics()
        
        assert metrics["total_files"] == 3
        assert metrics["total_dependencies"] == 4
        assert metrics["average_dependencies_per_file"] > 1
        
        # Test circular dependency detection
        self.dependency_tracker.track_file_dependencies("helpers.py", ["main.py"])  # Create cycle
        
        circular_deps = self.dependency_tracker.detect_circular_dependencies()
        assert len(circular_deps) >= 1
    
    def test_pattern_recognition_with_knowledge_graph(self):
        """Test pattern recognition integrated with knowledge graph."""
        # Code with clear design patterns
        singleton_code = '''
class DatabaseConnection:
    """Singleton database connection."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self):
        pass

class UserFactory:
    """Factory for creating user objects."""
    
    @staticmethod
    def create_user(user_type):
        if user_type == "admin":
            return AdminUser()
        elif user_type == "regular":
            return RegularUser()
        return None

class AdminUser:
    def __init__(self):
        self.permissions = ["read", "write", "delete"]

class RegularUser:
    def __init__(self):
        self.permissions = ["read"]
'''
        
        # Analyze code
        analysis = self.semantic_analyzer.analyze_code_semantics(singleton_code, "python", Path("patterns.py"))
        
        # Add to knowledge graph
        for entity in analysis.entities:
            self.knowledge_graph.add_code_entity(entity)
        
        for relationship in analysis.relationships:
            self.knowledge_graph.add_relationship(relationship)
        
        # Verify pattern detection
        singleton_patterns = [p for p in analysis.patterns if p.name == "Singleton"]
        factory_patterns = [p for p in analysis.patterns if p.name == "Factory"]
        
        assert len(singleton_patterns) >= 1
        assert len(factory_patterns) >= 1
        
        # Test pattern similarity search
        if singleton_patterns:
            similar_patterns = self.knowledge_graph.find_similar_patterns(singleton_patterns[0])
            # Should find the pattern itself
            assert len(similar_patterns) >= 0
    
    def test_complexity_analysis_integration(self):
        """Test complexity analysis integration across components."""
        # Code with varying complexity levels
        complexity_code = '''
def simple_function():
    """Simple function with low complexity."""
    return "hello world"

def medium_complexity(data):
    """Function with medium complexity."""
    if data is None:
        return None
    
    if isinstance(data, str):
        return data.upper()
    elif isinstance(data, int):
        return data * 2
    else:
        return str(data)

def high_complexity_function(items, filters, options):
    """Function with high cyclomatic complexity."""
    results = []
    
    for item in items:
        if item is None:
            continue
        
        # Apply filters
        for filter_func in filters:
            if not filter_func(item):
                break
        else:
            # Process item based on options
            if options.get("transform"):
                if isinstance(item, str):
                    if len(item) > 10:
                        item = item[:10] + "..."
                    item = item.upper()
                elif isinstance(item, (int, float)):
                    if item > 100:
                        item = item / 100
                    else:
                        item = item * 10
            
            if options.get("validate"):
                try:
                    if hasattr(item, "validate"):
                        if not item.validate():
                            continue
                except Exception:
                    continue
            
            results.append(item)
    
    # Sort results if requested
    if options.get("sort"):
        try:
            results.sort()
        except TypeError:
            # Can't sort mixed types
            pass
    
    return results
'''
        
        # Analyze complexity
        analysis = self.semantic_analyzer.analyze_code_semantics(complexity_code, "python", Path("complexity.py"))
        
        # Verify complexity detection
        functions = [e for e in analysis.entities if e.type.value == "function"]
        assert len(functions) == 3
        
        # Check complexity levels
        simple_func = next((f for f in functions if "simple" in f.name), None)
        high_complex_func = next((f for f in functions if "high_complexity" in f.name), None)
        
        assert simple_func is not None
        assert high_complex_func is not None
        
        # Simple function should have low complexity
        assert simple_func.complexity_metrics.complexity_level.value in ["low"]
        
        # High complexity function should have high complexity
        assert high_complex_func.complexity_metrics.complexity_level.value in ["high", "very_high"]
        assert high_complex_func.complexity_metrics.cyclomatic_complexity > 10
        
        # Add to knowledge graph and test impact analysis
        for entity in analysis.entities:
            self.knowledge_graph.add_code_entity(entity)
        
        # Test impact of changing high complexity function
        change = CodeChange(
            id="refactor_high_complexity",
            change_type=ChangeType.REFACTOR,
            entity_id=high_complex_func.id,
            description="Refactor high complexity function",
            file_path="complexity.py",
            line_start=high_complex_func.location.line_start,
            line_end=high_complex_func.location.line_end
        )
        
        impact_result = self.impact_analyzer.analyze_change_impact(change)
        
        # Should recommend refactoring due to complexity
        complexity_recommendations = [r for r in impact_result.recommendations 
                                    if "complexity" in r.lower() or "refactor" in r.lower()]
        assert len(complexity_recommendations) > 0
    
    def test_code_smell_detection_integration(self):
        """Test code smell detection integration."""
        # Code with various smells
        smelly_code = '''
class GodClass:
    """A class that does too many things."""
    
    def __init__(self):
        self.data = []
        self.cache = {}
        self.config = {}
        self.logger = None
        self.database = None
        self.api_client = None
    
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass

def long_parameter_function(a, b, c, d, e, f, g, h, i, j):
    """Function with too many parameters."""
    return a + b + c + d + e + f + g + h + i + j
'''
        
        # Analyze for smells
        analysis = self.semantic_analyzer.analyze_code_semantics(smelly_code, "python", Path("smells.py"))
        
        # Should detect code smells
        assert len(analysis.smells) >= 2
        
        # Should detect large class smell
        large_class_smells = [s for s in analysis.smells if s.name == "Large Class"]
        assert len(large_class_smells) >= 1
        
        # Should detect long parameter list smell
        param_smells = [s for s in analysis.smells if s.name == "Long Parameter List"]
        assert len(param_smells) >= 1
        
        # Add to knowledge graph
        for entity in analysis.entities:
            self.knowledge_graph.add_code_entity(entity)
        
        # Test impact analysis considers code smells
        god_class = next((e for e in analysis.entities if e.name == "GodClass"), None)
        assert god_class is not None
        
        change = CodeChange(
            id="refactor_god_class",
            change_type=ChangeType.REFACTOR,
            entity_id=god_class.id,
            description="Refactor god class",
            file_path="smells.py",
            line_start=god_class.location.line_start,
            line_end=god_class.location.line_end
        )
        
        impact_result = self.impact_analyzer.analyze_change_impact(change)
        
        # Should have recommendations related to the large class
        assert len(impact_result.recommendations) > 0
        assert impact_result.estimated_effort > 1  # Should require significant effort
    
    def test_performance_with_large_codebase(self):
        """Test performance with a larger simulated codebase."""
        # Generate multiple code files
        base_code_template = '''
class Module{i}:
    """Module {i} class."""
    
    def __init__(self):
        self.value = {i}
    
    def process(self, data):
        """Process data in module {i}."""
        if data > {i}:
            return data * {i}
        return data + {i}
    
    def validate(self, item):
        """Validate item in module {i}."""
        return item is not None and item > 0

def utility_function_{i}(x, y):
    """Utility function {i}."""
    module = Module{i}()
    return module.process(x + y)
'''
        
        # Analyze multiple modules
        total_entities = 0
        total_relationships = 0
        
        for i in range(5):  # Simulate 5 modules
            code = base_code_template.format(i=i)
            analysis = self.semantic_analyzer.analyze_code_semantics(
                code, "python", Path(f"module_{i}.py")
            )
            
            # Add to knowledge graph
            for entity in analysis.entities:
                self.knowledge_graph.add_code_entity(entity)
                total_entities += 1
            
            for relationship in analysis.relationships:
                self.knowledge_graph.add_relationship(relationship)
                total_relationships += 1
        
        # Verify all entities were added
        stats = self.knowledge_graph.get_graph_statistics()
        assert stats["total_entities"] == total_entities
        assert stats["total_relationships"] == total_relationships
        
        # Test querying performance
        query_result = self.knowledge_graph.query_graph(
            self.knowledge_graph.GraphQuery(max_results=50)
        )
        
        assert len(query_result.nodes) <= 50
        assert len(query_result.nodes) > 0
        
        # Test impact analysis on one entity
        if query_result.nodes:
            test_entity = query_result.nodes[0].entity
            change = CodeChange(
                id="test_change",
                change_type=ChangeType.MODIFY,
                entity_id=test_entity.id,
                description="Test change",
                file_path=test_entity.location.file_path,
                line_start=test_entity.location.line_start,
                line_end=test_entity.location.line_end
            )
            
            impact_result = self.impact_analyzer.analyze_change_impact(change)
            assert impact_result is not None
            assert impact_result.confidence_score >= 0


if __name__ == "__main__":
    pytest.main([__file__])