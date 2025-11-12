"""
Unit tests for code knowledge graph system.
"""

import pytest
from pathlib import Path
import tempfile
import json

from codegenie.core.knowledge_graph import (
    CodeKnowledgeGraph, RelationshipType, GraphNode, CodeRelationship,
    GraphQueryResult, DependencyChain
)


class TestCodeKnowledgeGraph:
    """Test code knowledge graph functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.graph = CodeKnowledgeGraph()
    
    def test_add_entity(self):
        """Test adding entities to the graph."""
        self.graph.add_entity(
            entity_id="func1",
            entity_type="function",
            name="my_function",
            file_path=Path("test.py"),
            metadata={"complexity": 5}
        )
        
        entity = self.graph.get_entity("func1")
        assert entity is not None
        assert entity.name == "my_function"
        assert entity.entity_type == "function"
        assert entity.metadata["complexity"] == 5
    
    def test_add_relationship(self):
        """Test adding relationships between entities."""
        # Add entities
        self.graph.add_entity("func1", "function", "caller", Path("test.py"))
        self.graph.add_entity("func2", "function", "callee", Path("test.py"))
        
        # Add relationship
        self.graph.add_relationship(
            "func1", "func2", RelationshipType.CALLS, strength=0.8
        )
        
        relationships = self.graph.get_relationships("func1")
        assert len(relationships) == 1
        assert relationships[0].relationship_type == RelationshipType.CALLS
        assert relationships[0].strength == 0.8
    
    def test_find_dependencies(self):
        """Test finding dependencies."""
        # Create a dependency chain: A -> B -> C
        self.graph.add_entity("A", "function", "A", Path("test.py"))
        self.graph.add_entity("B", "function", "B", Path("test.py"))
        self.graph.add_entity("C", "function", "C", Path("test.py"))
        
        self.graph.add_relationship("A", "B", RelationshipType.CALLS)
        self.graph.add_relationship("B", "C", RelationshipType.CALLS)
        
        deps = self.graph.find_dependencies("A")
        assert "B" in deps
        assert "C" in deps
    
    def test_find_dependents(self):
        """Test finding dependents."""
        # Create a dependency chain: A -> B -> C
        self.graph.add_entity("A", "function", "A", Path("test.py"))
        self.graph.add_entity("B", "function", "B", Path("test.py"))
        self.graph.add_entity("C", "function", "C", Path("test.py"))
        
        self.graph.add_relationship("A", "B", RelationshipType.CALLS)
        self.graph.add_relationship("B", "C", RelationshipType.CALLS)
        
        dependents = self.graph.find_dependents("C")
        assert "B" in dependents
        assert "A" in dependents
    
    def test_find_path(self):
        """Test finding path between entities."""
        # Create a path: A -> B -> C
        self.graph.add_entity("A", "function", "A", Path("test.py"))
        self.graph.add_entity("B", "function", "B", Path("test.py"))
        self.graph.add_entity("C", "function", "C", Path("test.py"))
        
        self.graph.add_relationship("A", "B", RelationshipType.CALLS)
        self.graph.add_relationship("B", "C", RelationshipType.CALLS)
        
        path = self.graph.find_path("A", "C")
        assert path is not None
        assert path == ["A", "B", "C"]
    
    def test_find_circular_dependencies(self):
        """Test finding circular dependencies."""
        # Create a circular dependency: A -> B -> C -> A
        self.graph.add_entity("A", "function", "A", Path("test.py"))
        self.graph.add_entity("B", "function", "B", Path("test.py"))
        self.graph.add_entity("C", "function", "C", Path("test.py"))
        
        self.graph.add_relationship("A", "B", RelationshipType.DEPENDS_ON)
        self.graph.add_relationship("B", "C", RelationshipType.DEPENDS_ON)
        self.graph.add_relationship("C", "A", RelationshipType.DEPENDS_ON)
        
        circular = self.graph.find_circular_dependencies()
        assert len(circular) > 0
        assert circular[0].is_circular
    
    def test_query_graph(self):
        """Test querying the graph."""
        # Add multiple entities
        self.graph.add_entity("func1", "function", "func1", Path("test.py"))
        self.graph.add_entity("func2", "function", "func2", Path("test.py"))
        self.graph.add_entity("class1", "class", "MyClass", Path("test.py"))
        
        # Query by entity type
        result = self.graph.query_graph(entity_type="function")
        assert len(result.nodes) == 2
        
        # Query by file
        result = self.graph.query_graph(file_path=Path("test.py"))
        assert len(result.nodes) == 3
    
    def test_get_related_entities(self):
        """Test getting related entities."""
        # Create a network: A -> B -> C, A -> D
        self.graph.add_entity("A", "function", "A", Path("test.py"))
        self.graph.add_entity("B", "function", "B", Path("test.py"))
        self.graph.add_entity("C", "function", "C", Path("test.py"))
        self.graph.add_entity("D", "function", "D", Path("test.py"))
        
        self.graph.add_relationship("A", "B", RelationshipType.CALLS)
        self.graph.add_relationship("B", "C", RelationshipType.CALLS)
        self.graph.add_relationship("A", "D", RelationshipType.CALLS)
        
        related = self.graph.get_related_entities("A", max_distance=2)
        entity_ids = [e[0] for e in related]
        
        assert "B" in entity_ids
        assert "C" in entity_ids
        assert "D" in entity_ids
    
    def test_export_import(self):
        """Test exporting and importing graph."""
        # Add some data
        self.graph.add_entity("func1", "function", "func1", Path("test.py"))
        self.graph.add_entity("func2", "function", "func2", Path("test.py"))
        self.graph.add_relationship("func1", "func2", RelationshipType.CALLS)
        
        # Export
        data = self.graph.export_to_dict()
        assert len(data["nodes"]) == 2
        assert len(data["relationships"]) == 1
        
        # Import into new graph
        new_graph = CodeKnowledgeGraph()
        new_graph.import_from_dict(data)
        
        assert len(new_graph.nodes) == 2
        assert len(new_graph.relationships) == 1
    
    def test_save_load_file(self):
        """Test saving and loading graph from file."""
        # Add some data
        self.graph.add_entity("func1", "function", "func1", Path("test.py"))
        self.graph.add_entity("func2", "function", "func2", Path("test.py"))
        self.graph.add_relationship("func1", "func2", RelationshipType.CALLS)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)
        
        try:
            self.graph.save_to_file(temp_path)
            
            # Load into new graph
            new_graph = CodeKnowledgeGraph()
            new_graph.load_from_file(temp_path)
            
            assert len(new_graph.nodes) == 2
            assert len(new_graph.relationships) == 1
        finally:
            temp_path.unlink()
    
    def test_get_statistics(self):
        """Test getting graph statistics."""
        # Add entities and relationships
        self.graph.add_entity("func1", "function", "func1", Path("test.py"))
        self.graph.add_entity("func2", "function", "func2", Path("test.py"))
        self.graph.add_entity("class1", "class", "MyClass", Path("test.py"))
        
        self.graph.add_relationship("func1", "func2", RelationshipType.CALLS)
        self.graph.add_relationship("class1", "func1", RelationshipType.CONTAINS)
        
        stats = self.graph.get_statistics()
        
        assert stats["total_nodes"] == 3
        assert stats["total_relationships"] == 2
        assert "function" in stats["entity_types"]
        assert "class" in stats["entity_types"]
        assert stats["files_indexed"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
