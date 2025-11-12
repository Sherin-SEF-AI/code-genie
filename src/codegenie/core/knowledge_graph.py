"""
Code Knowledge Graph System - Tracks relationships and dependencies across codebase.

This module provides a knowledge graph for code relationships including:
- Entity and relationship tracking
- Dependency analysis across files and modules
- Graph querying and traversal
- Integration with agentic search
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import logging
import json
from collections import defaultdict, deque


logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between code entities."""
    CALLS = "calls"
    INHERITS = "inherits"
    IMPORTS = "imports"
    USES = "uses"
    DEFINES = "defines"
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    OVERRIDES = "overrides"
    REFERENCES = "references"


@dataclass
class CodeRelationship:
    """Represents a relationship between code entities."""
    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: RelationshipType
    metadata: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0  # Relationship strength (0-1)


@dataclass
class GraphNode:
    """Node in the knowledge graph."""
    entity_id: str
    entity_type: str
    name: str
    file_path: Path
    metadata: Dict[str, Any] = field(default_factory=dict)
    incoming_edges: List[str] = field(default_factory=list)
    outgoing_edges: List[str] = field(default_factory=list)


@dataclass
class GraphQueryResult:
    """Result of a graph query."""
    nodes: List[GraphNode]
    relationships: List[CodeRelationship]
    paths: List[List[str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyChain:
    """Represents a chain of dependencies."""
    entities: List[str]
    relationship_types: List[RelationshipType]
    total_strength: float
    is_circular: bool = False


class CodeKnowledgeGraph:
    """Knowledge graph for code relationships and dependencies."""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.relationships: Dict[str, CodeRelationship] = {}
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)  # Index by entity type
        self.file_index: Dict[Path, Set[str]] = defaultdict(set)  # Index by file
        self.relationship_index: Dict[RelationshipType, Set[str]] = defaultdict(set)
    
    def add_entity(self, entity_id: str, entity_type: str, name: str, 
                   file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a code entity to the graph."""
        if entity_id in self.nodes:
            logger.debug(f"Entity {entity_id} already exists, updating")
        
        node = GraphNode(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            file_path=file_path,
            metadata=metadata or {}
        )
        
        self.nodes[entity_id] = node
        self.entity_index[entity_type].add(entity_id)
        self.file_index[file_path].add(entity_id)
    
    def add_relationship(self, source_id: str, target_id: str, 
                        relationship_type: RelationshipType,
                        metadata: Optional[Dict[str, Any]] = None,
                        strength: float = 1.0) -> None:
        """Add a relationship between entities."""
        if source_id not in self.nodes:
            logger.warning(f"Source entity {source_id} not found in graph")
            return
        
        if target_id not in self.nodes:
            logger.warning(f"Target entity {target_id} not found in graph")
            return
        
        relationship_id = f"{source_id}:{relationship_type.value}:{target_id}"
        
        relationship = CodeRelationship(
            id=relationship_id,
            source_entity_id=source_id,
            target_entity_id=target_id,
            relationship_type=relationship_type,
            metadata=metadata or {},
            strength=strength
        )
        
        self.relationships[relationship_id] = relationship
        self.relationship_index[relationship_type].add(relationship_id)
        
        # Update node edges
        self.nodes[source_id].outgoing_edges.append(relationship_id)
        self.nodes[target_id].incoming_edges.append(relationship_id)
    
    def get_entity(self, entity_id: str) -> Optional[GraphNode]:
        """Get an entity by ID."""
        return self.nodes.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[GraphNode]:
        """Get all entities of a specific type."""
        entity_ids = self.entity_index.get(entity_type, set())
        return [self.nodes[eid] for eid in entity_ids if eid in self.nodes]
    
    def get_entities_in_file(self, file_path: Path) -> List[GraphNode]:
        """Get all entities in a specific file."""
        entity_ids = self.file_index.get(file_path, set())
        return [self.nodes[eid] for eid in entity_ids if eid in self.nodes]
    
    def get_relationships(self, entity_id: str, 
                         relationship_type: Optional[RelationshipType] = None,
                         direction: str = "both") -> List[CodeRelationship]:
        """Get relationships for an entity."""
        if entity_id not in self.nodes:
            return []
        
        node = self.nodes[entity_id]
        relationship_ids = []
        
        if direction in ("outgoing", "both"):
            relationship_ids.extend(node.outgoing_edges)
        
        if direction in ("incoming", "both"):
            relationship_ids.extend(node.incoming_edges)
        
        relationships = [self.relationships[rid] for rid in relationship_ids 
                        if rid in self.relationships]
        
        if relationship_type:
            relationships = [r for r in relationships 
                           if r.relationship_type == relationship_type]
        
        return relationships
    
    def find_dependencies(self, entity_id: str, max_depth: int = 5) -> List[str]:
        """Find all dependencies of an entity (BFS traversal)."""
        if entity_id not in self.nodes:
            return []
        
        visited = set()
        queue = deque([(entity_id, 0)])
        dependencies = []
        
        while queue:
            current_id, depth = queue.popleft()
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            if current_id != entity_id:
                dependencies.append(current_id)
            
            # Get outgoing relationships
            relationships = self.get_relationships(current_id, direction="outgoing")
            
            for rel in relationships:
                if rel.target_entity_id not in visited:
                    queue.append((rel.target_entity_id, depth + 1))
        
        return dependencies
    
    def find_dependents(self, entity_id: str, max_depth: int = 5) -> List[str]:
        """Find all entities that depend on this entity."""
        if entity_id not in self.nodes:
            return []
        
        visited = set()
        queue = deque([(entity_id, 0)])
        dependents = []
        
        while queue:
            current_id, depth = queue.popleft()
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            if current_id != entity_id:
                dependents.append(current_id)
            
            # Get incoming relationships
            relationships = self.get_relationships(current_id, direction="incoming")
            
            for rel in relationships:
                if rel.source_entity_id not in visited:
                    queue.append((rel.source_entity_id, depth + 1))
        
        return dependents
    
    def find_path(self, source_id: str, target_id: str, 
                  max_depth: int = 10) -> Optional[List[str]]:
        """Find shortest path between two entities."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        visited = set()
        queue = deque([(source_id, [source_id])])
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == target_id:
                return path
            
            if current_id in visited or len(path) > max_depth:
                continue
            
            visited.add(current_id)
            
            # Explore neighbors
            relationships = self.get_relationships(current_id, direction="outgoing")
            
            for rel in relationships:
                if rel.target_entity_id not in visited:
                    new_path = path + [rel.target_entity_id]
                    queue.append((rel.target_entity_id, new_path))
        
        return None
    
    def find_circular_dependencies(self) -> List[DependencyChain]:
        """Find circular dependencies in the graph."""
        circular_deps = []
        visited = set()
        
        for entity_id in self.nodes:
            if entity_id in visited:
                continue
            
            # Try to find a path back to itself
            path = self._find_cycle(entity_id, set(), [])
            
            if path:
                circular_deps.append(DependencyChain(
                    entities=path,
                    relationship_types=[RelationshipType.DEPENDS_ON] * (len(path) - 1),
                    total_strength=1.0,
                    is_circular=True
                ))
                visited.update(path)
        
        return circular_deps
    
    def _find_cycle(self, entity_id: str, visited: Set[str], 
                    path: List[str]) -> Optional[List[str]]:
        """Helper to find cycles using DFS."""
        if entity_id in visited:
            # Found a cycle
            if entity_id in path:
                cycle_start = path.index(entity_id)
                return path[cycle_start:] + [entity_id]
            return None
        
        visited.add(entity_id)
        path.append(entity_id)
        
        relationships = self.get_relationships(entity_id, direction="outgoing")
        
        for rel in relationships:
            cycle = self._find_cycle(rel.target_entity_id, visited.copy(), path.copy())
            if cycle:
                return cycle
        
        return None
    
    def query_graph(self, entity_type: Optional[str] = None,
                   relationship_type: Optional[RelationshipType] = None,
                   file_path: Optional[Path] = None,
                   name_pattern: Optional[str] = None) -> GraphQueryResult:
        """Query the graph with various filters."""
        nodes = []
        
        # Filter by entity type
        if entity_type:
            nodes = self.get_entities_by_type(entity_type)
        elif file_path:
            nodes = self.get_entities_in_file(file_path)
        else:
            nodes = list(self.nodes.values())
        
        # Filter by name pattern
        if name_pattern:
            import re
            pattern = re.compile(name_pattern)
            nodes = [n for n in nodes if pattern.search(n.name)]
        
        # Get relevant relationships
        node_ids = {n.entity_id for n in nodes}
        relationships = []
        
        for rel in self.relationships.values():
            if rel.source_entity_id in node_ids or rel.target_entity_id in node_ids:
                if not relationship_type or rel.relationship_type == relationship_type:
                    relationships.append(rel)
        
        return GraphQueryResult(
            nodes=nodes,
            relationships=relationships,
            metadata={"total_nodes": len(nodes), "total_relationships": len(relationships)}
        )
    
    def get_related_entities(self, entity_id: str, 
                            relationship_types: Optional[List[RelationshipType]] = None,
                            max_distance: int = 2) -> List[Tuple[str, int]]:
        """Get entities related to the given entity within max_distance hops."""
        if entity_id not in self.nodes:
            return []
        
        visited = {entity_id: 0}
        queue = deque([(entity_id, 0)])
        related = []
        
        while queue:
            current_id, distance = queue.popleft()
            
            if distance >= max_distance:
                continue
            
            # Get all relationships
            relationships = self.get_relationships(current_id)
            
            for rel in relationships:
                if relationship_types and rel.relationship_type not in relationship_types:
                    continue
                
                # Determine the neighbor
                neighbor_id = (rel.target_entity_id if rel.source_entity_id == current_id 
                             else rel.source_entity_id)
                
                if neighbor_id not in visited:
                    visited[neighbor_id] = distance + 1
                    related.append((neighbor_id, distance + 1))
                    queue.append((neighbor_id, distance + 1))
        
        return related
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export graph to dictionary format."""
        return {
            "nodes": [
                {
                    "id": node.entity_id,
                    "type": node.entity_type,
                    "name": node.name,
                    "file": str(node.file_path),
                    "metadata": node.metadata
                }
                for node in self.nodes.values()
            ],
            "relationships": [
                {
                    "id": rel.id,
                    "source": rel.source_entity_id,
                    "target": rel.target_entity_id,
                    "type": rel.relationship_type.value,
                    "strength": rel.strength,
                    "metadata": rel.metadata
                }
                for rel in self.relationships.values()
            ]
        }
    
    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """Import graph from dictionary format."""
        # Clear existing data
        self.nodes.clear()
        self.relationships.clear()
        self.entity_index.clear()
        self.file_index.clear()
        self.relationship_index.clear()
        
        # Import nodes
        for node_data in data.get("nodes", []):
            self.add_entity(
                entity_id=node_data["id"],
                entity_type=node_data["type"],
                name=node_data["name"],
                file_path=Path(node_data["file"]),
                metadata=node_data.get("metadata", {})
            )
        
        # Import relationships
        for rel_data in data.get("relationships", []):
            self.add_relationship(
                source_id=rel_data["source"],
                target_id=rel_data["target"],
                relationship_type=RelationshipType(rel_data["type"]),
                metadata=rel_data.get("metadata", {}),
                strength=rel_data.get("strength", 1.0)
            )
    
    def save_to_file(self, file_path: Path) -> None:
        """Save graph to JSON file."""
        data = self.export_to_dict()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, file_path: Path) -> None:
        """Load graph from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.import_from_dict(data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        entity_type_counts = {
            entity_type: len(entities)
            for entity_type, entities in self.entity_index.items()
        }
        
        relationship_type_counts = {
            rel_type.value: len(rels)
            for rel_type, rels in self.relationship_index.items()
        }
        
        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "entity_types": entity_type_counts,
            "relationship_types": relationship_type_counts,
            "files_indexed": len(self.file_index)
        }
