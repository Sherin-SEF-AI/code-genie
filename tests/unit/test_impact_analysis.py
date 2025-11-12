"""
Unit tests for impact analysis system.
"""

import pytest
from pathlib import Path
import asyncio

from codegenie.core.impact_analysis import (
    ChangeImpactAnalyzer, CodeChange, ChangeType, RiskLevel, ImpactScope,
    ImpactedEntity, MultiFileChange, ChangeValidation
)
from codegenie.core.knowledge_graph import CodeKnowledgeGraph, RelationshipType


class TestChangeImpactAnalyzer:
    """Test change impact analyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.graph = CodeKnowledgeGraph()
        self.analyzer = ChangeImpactAnalyzer(self.graph)
        
        # Set up a sample graph
        self._setup_sample_graph()
    
    def _setup_sample_graph(self):
        """Set up a sample knowledge graph for testing."""
        # Add entities
        self.graph.add_entity("func_a", "function", "function_a", Path("module_a.py"))
        self.graph.add_entity("func_b", "function", "function_b", Path("module_b.py"))
        self.graph.add_entity("func_c", "function", "function_c", Path("module_c.py"))
        self.graph.add_entity("class_x", "class", "ClassX", Path("module_x.py"))
        
        # Add relationships
        self.graph.add_relationship("func_b", "func_a", RelationshipType.CALLS, strength=0.9)
        self.graph.add_relationship("func_c", "func_a", RelationshipType.CALLS, strength=0.7)
        self.graph.add_relationship("class_x", "func_b", RelationshipType.USES, strength=0.8)
    
    @pytest.mark.asyncio
    async def test_analyze_change_impact_modify(self):
        """Test impact analysis for modification."""
        change = CodeChange(
            id="change1",
            change_type=ChangeType.MODIFY,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Modify function signature"
        )
        
        analysis = await self.analyzer.analyze_change_impact(change)
        
        assert analysis.change == change
        assert len(analysis.directly_impacted) >= 2  # func_b and func_c
        assert analysis.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
    
    @pytest.mark.asyncio
    async def test_analyze_change_impact_delete(self):
        """Test impact analysis for deletion."""
        change = CodeChange(
            id="change2",
            change_type=ChangeType.DELETE,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Delete function"
        )
        
        analysis = await self.analyzer.analyze_change_impact(change)
        
        # Deletion should have higher risk
        assert analysis.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Should identify entities that require updates
        entities_requiring_updates = [e for e in analysis.directly_impacted if e.requires_update]
        assert len(entities_requiring_updates) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_change_impact_rename(self):
        """Test impact analysis for rename."""
        change = CodeChange(
            id="change3",
            change_type=ChangeType.RENAME,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Rename function",
            old_value="function_a",
            new_value="function_a_renamed"
        )
        
        analysis = await self.analyzer.analyze_change_impact(change)
        
        # Rename should require updates to dependents
        entities_requiring_updates = [e for e in analysis.directly_impacted if e.requires_update]
        assert len(entities_requiring_updates) > 0
    
    @pytest.mark.asyncio
    async def test_impact_scope_determination(self):
        """Test impact scope determination."""
        # Local change (same file)
        self.graph.add_entity("func_local1", "function", "local1", Path("same.py"))
        self.graph.add_entity("func_local2", "function", "local2", Path("same.py"))
        self.graph.add_relationship("func_local2", "func_local1", RelationshipType.CALLS)
        
        change = CodeChange(
            id="local_change",
            change_type=ChangeType.MODIFY,
            entity_id="func_local1",
            file_path=Path("same.py"),
            description="Local change"
        )
        
        analysis = await self.analyzer.analyze_change_impact(change)
        
        # Should be local or module scope
        assert analysis.impact_scope in [ImpactScope.LOCAL, ImpactScope.MODULE]
    
    @pytest.mark.asyncio
    async def test_risk_assessment(self):
        """Test risk assessment."""
        # Create a high-impact change
        for i in range(15):
            entity_id = f"dependent_{i}"
            self.graph.add_entity(entity_id, "function", f"func_{i}", Path(f"module_{i}.py"))
            self.graph.add_relationship(entity_id, "func_a", RelationshipType.CALLS, strength=0.9)
        
        change = CodeChange(
            id="high_risk_change",
            change_type=ChangeType.DELETE,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Delete widely-used function"
        )
        
        analysis = await self.analyzer.analyze_change_impact(change)
        
        # Should be high or critical risk
        assert analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(analysis.risk_factors) > 0
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self):
        """Test recommendations generation."""
        change = CodeChange(
            id="change_with_recs",
            change_type=ChangeType.MODIFY,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Modify function"
        )
        
        analysis = await self.analyzer.analyze_change_impact(change)
        
        # Should have recommendations
        assert len(analysis.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_coordinate_multi_file_changes(self):
        """Test coordinating multi-file changes."""
        changes = [
            CodeChange(
                id="change1",
                change_type=ChangeType.MODIFY,
                entity_id="func_a",
                file_path=Path("module_a.py"),
                description="Modify func_a"
            ),
            CodeChange(
                id="change2",
                change_type=ChangeType.MODIFY,
                entity_id="func_b",
                file_path=Path("module_b.py"),
                description="Modify func_b"
            )
        ]
        
        multi_change = await self.analyzer.coordinate_multi_file_changes(changes)
        
        assert multi_change.id is not None
        assert len(multi_change.changes) == 2
        assert len(multi_change.execution_order) == 2
        assert len(multi_change.validation_steps) > 0
    
    @pytest.mark.asyncio
    async def test_validate_change(self):
        """Test change validation."""
        change = CodeChange(
            id="valid_change",
            change_type=ChangeType.MODIFY,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Valid modification"
        )
        
        validation = await self.analyzer.validate_change(change)
        
        assert validation.is_valid
        assert validation.confidence > 0
    
    @pytest.mark.asyncio
    async def test_validate_invalid_change(self):
        """Test validation of invalid change."""
        change = CodeChange(
            id="invalid_change",
            change_type=ChangeType.MODIFY,
            entity_id="nonexistent_entity",
            file_path=Path("module.py"),
            description="Invalid change"
        )
        
        validation = await self.analyzer.validate_change(change)
        
        assert not validation.is_valid
        assert len(validation.errors) > 0
    
    @pytest.mark.asyncio
    async def test_indirectly_impacted_entities(self):
        """Test finding indirectly impacted entities."""
        # Create a longer chain: func_d -> func_c -> func_a
        self.graph.add_entity("func_d", "function", "function_d", Path("module_d.py"))
        self.graph.add_relationship("func_d", "func_c", RelationshipType.CALLS, strength=0.6)
        
        change = CodeChange(
            id="change_indirect",
            change_type=ChangeType.MODIFY,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Modify func_a"
        )
        
        analysis = await self.analyzer.analyze_change_impact(change)
        
        # Should find indirect impacts
        assert len(analysis.indirectly_impacted) > 0
    
    @pytest.mark.asyncio
    async def test_effort_estimation(self):
        """Test effort estimation."""
        # Low effort change
        change_low = CodeChange(
            id="low_effort",
            change_type=ChangeType.MODIFY,
            entity_id="func_c",
            file_path=Path("module_c.py"),
            description="Small change"
        )
        
        analysis_low = await self.analyzer.analyze_change_impact(change_low)
        assert analysis_low.estimated_effort in ["low", "medium"]
        
        # High effort change (many dependents)
        for i in range(25):
            entity_id = f"many_deps_{i}"
            self.graph.add_entity(entity_id, "function", f"func_{i}", Path(f"mod_{i}.py"))
            self.graph.add_relationship(entity_id, "func_a", RelationshipType.CALLS)
        
        change_high = CodeChange(
            id="high_effort",
            change_type=ChangeType.DELETE,
            entity_id="func_a",
            file_path=Path("module_a.py"),
            description="Delete widely-used function"
        )
        
        analysis_high = await self.analyzer.analyze_change_impact(change_high)
        assert analysis_high.estimated_effort in ["medium", "high"]


if __name__ == "__main__":
    pytest.main([__file__])
