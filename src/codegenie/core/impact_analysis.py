"""
Impact Analysis and Change Prediction System.

This module provides comprehensive impact analysis for code changes including:
- Ripple effect analysis for changes
- Dependency impact calculation
- Change risk assessment
- Multi-file change coordination
- Change suggestion validation
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import logging
from collections import defaultdict

from .knowledge_graph import CodeKnowledgeGraph, RelationshipType


logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of code changes."""
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"
    MOVE = "move"
    REFACTOR = "refactor"


class RiskLevel(Enum):
    """Risk levels for changes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImpactScope(Enum):
    """Scope of impact."""
    LOCAL = "local"  # Within same file
    MODULE = "module"  # Within same module
    PACKAGE = "package"  # Within same package
    GLOBAL = "global"  # Across entire codebase


@dataclass
class CodeChange:
    """Represents a code change."""
    id: str
    change_type: ChangeType
    entity_id: str
    file_path: Path
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None


@dataclass
class ImpactedEntity:
    """Entity impacted by a change."""
    entity_id: str
    entity_name: str
    file_path: Path
    impact_reason: str
    impact_severity: float  # 0-1 scale
    suggested_action: Optional[str] = None
    requires_update: bool = False


@dataclass
class ImpactAnalysis:
    """Results of impact analysis."""
    change: CodeChange
    directly_impacted: List[ImpactedEntity]
    indirectly_impacted: List[ImpactedEntity]
    risk_level: RiskLevel
    impact_scope: ImpactScope
    risk_factors: List[str]
    recommendations: List[str]
    estimated_effort: str  # "low", "medium", "high"
    affected_files: Set[Path] = field(default_factory=set)
    test_coverage_impact: Optional[Dict[str, Any]] = None


@dataclass
class MultiFileChange:
    """Coordinated changes across multiple files."""
    id: str
    description: str
    changes: List[CodeChange]
    dependencies: List[Tuple[str, str]]  # (change_id, depends_on_change_id)
    execution_order: List[str]  # Ordered list of change IDs
    total_risk: RiskLevel
    validation_steps: List[str]


@dataclass
class ChangeValidation:
    """Validation result for a change."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    confidence: float  # 0-1 scale


class ChangeImpactAnalyzer:
    """Analyzes the impact of code changes."""
    
    def __init__(self, knowledge_graph: CodeKnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.impact_cache: Dict[str, ImpactAnalysis] = {}
    
    async def analyze_change_impact(self, change: CodeChange) -> ImpactAnalysis:
        """Analyze the impact of a code change."""
        # Check cache
        cache_key = f"{change.id}:{change.entity_id}"
        if cache_key in self.impact_cache:
            return self.impact_cache[cache_key]
        
        # Find directly impacted entities
        directly_impacted = self._find_directly_impacted(change)
        
        # Find indirectly impacted entities
        indirectly_impacted = self._find_indirectly_impacted(change, directly_impacted)
        
        # Assess risk
        risk_level, risk_factors = self._assess_risk(change, directly_impacted, indirectly_impacted)
        
        # Determine impact scope
        impact_scope = self._determine_impact_scope(change, directly_impacted, indirectly_impacted)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(change, directly_impacted, indirectly_impacted, risk_level)
        
        # Estimate effort
        estimated_effort = self._estimate_effort(directly_impacted, indirectly_impacted)
        
        # Collect affected files
        affected_files = {change.file_path}
        affected_files.update(e.file_path for e in directly_impacted)
        affected_files.update(e.file_path for e in indirectly_impacted)
        
        analysis = ImpactAnalysis(
            change=change,
            directly_impacted=directly_impacted,
            indirectly_impacted=indirectly_impacted,
            risk_level=risk_level,
            impact_scope=impact_scope,
            risk_factors=risk_factors,
            recommendations=recommendations,
            estimated_effort=estimated_effort,
            affected_files=affected_files
        )
        
        # Cache result
        self.impact_cache[cache_key] = analysis
        
        return analysis
    
    def _find_directly_impacted(self, change: CodeChange) -> List[ImpactedEntity]:
        """Find entities directly impacted by the change."""
        impacted = []
        
        # Get the entity being changed
        entity = self.knowledge_graph.get_entity(change.entity_id)
        if not entity:
            return impacted
        
        # Find all entities that depend on this entity
        dependents = self.knowledge_graph.find_dependents(change.entity_id, max_depth=1)
        
        for dependent_id in dependents:
            dependent = self.knowledge_graph.get_entity(dependent_id)
            if not dependent:
                continue
            
            # Determine impact severity based on relationship strength
            relationships = self.knowledge_graph.get_relationships(dependent_id)
            severity = max(
                (r.strength for r in relationships if r.target_entity_id == change.entity_id),
                default=0.5
            )
            
            # Determine if update is required
            requires_update = self._requires_update(change, dependent_id)
            
            impacted.append(ImpactedEntity(
                entity_id=dependent_id,
                entity_name=dependent.name,
                file_path=dependent.file_path,
                impact_reason=f"Depends on {entity.name} which is being {change.change_type.value}d",
                impact_severity=severity,
                suggested_action=self._suggest_action(change, dependent_id),
                requires_update=requires_update
            ))
        
        return impacted
    
    def _find_indirectly_impacted(self, change: CodeChange, 
                                  directly_impacted: List[ImpactedEntity]) -> List[ImpactedEntity]:
        """Find entities indirectly impacted by the change."""
        impacted = []
        visited = {change.entity_id}
        visited.update(e.entity_id for e in directly_impacted)
        
        # For each directly impacted entity, find its dependents
        for direct_impact in directly_impacted:
            dependents = self.knowledge_graph.find_dependents(direct_impact.entity_id, max_depth=2)
            
            for dependent_id in dependents:
                if dependent_id in visited:
                    continue
                
                visited.add(dependent_id)
                dependent = self.knowledge_graph.get_entity(dependent_id)
                if not dependent:
                    continue
                
                # Lower severity for indirect impacts
                severity = direct_impact.impact_severity * 0.5
                
                impacted.append(ImpactedEntity(
                    entity_id=dependent_id,
                    entity_name=dependent.name,
                    file_path=dependent.file_path,
                    impact_reason=f"Indirectly affected through {direct_impact.entity_name}",
                    impact_severity=severity,
                    suggested_action="Review for potential issues",
                    requires_update=False
                ))
        
        return impacted
    
    def _requires_update(self, change: CodeChange, dependent_id: str) -> bool:
        """Determine if a dependent entity requires updates."""
        # Deletions and renames typically require updates
        if change.change_type in (ChangeType.DELETE, ChangeType.RENAME):
            return True
        
        # Check relationship type
        relationships = self.knowledge_graph.get_relationships(dependent_id)
        for rel in relationships:
            if rel.target_entity_id == change.entity_id:
                # Strong dependencies require updates
                if rel.relationship_type in (RelationshipType.CALLS, RelationshipType.USES):
                    if change.change_type == ChangeType.MODIFY:
                        # Signature changes require updates
                        return "signature" in change.description.lower()
        
        return False
    
    def _suggest_action(self, change: CodeChange, dependent_id: str) -> str:
        """Suggest action for impacted entity."""
        if change.change_type == ChangeType.DELETE:
            return "Remove or replace usage of deleted entity"
        elif change.change_type == ChangeType.RENAME:
            return "Update references to use new name"
        elif change.change_type == ChangeType.MODIFY:
            return "Review and update usage if needed"
        elif change.change_type == ChangeType.MOVE:
            return "Update import statements"
        else:
            return "Review for compatibility"
    
    def _assess_risk(self, change: CodeChange, 
                    directly_impacted: List[ImpactedEntity],
                    indirectly_impacted: List[ImpactedEntity]) -> Tuple[RiskLevel, List[str]]:
        """Assess the risk level of a change."""
        risk_factors = []
        risk_score = 0
        
        # Factor 1: Number of impacted entities
        total_impacted = len(directly_impacted) + len(indirectly_impacted)
        if total_impacted > 20:
            risk_score += 3
            risk_factors.append(f"High number of impacted entities ({total_impacted})")
        elif total_impacted > 10:
            risk_score += 2
            risk_factors.append(f"Moderate number of impacted entities ({total_impacted})")
        elif total_impacted > 5:
            risk_score += 1
            risk_factors.append(f"Several impacted entities ({total_impacted})")
        
        # Factor 2: Change type
        if change.change_type in (ChangeType.DELETE, ChangeType.RENAME):
            risk_score += 2
            risk_factors.append(f"Breaking change type: {change.change_type.value}")
        elif change.change_type == ChangeType.REFACTOR:
            risk_score += 1
            risk_factors.append("Refactoring changes require careful testing")
        
        # Factor 3: Impact severity
        max_severity = max(
            (e.impact_severity for e in directly_impacted),
            default=0
        )
        if max_severity > 0.8:
            risk_score += 2
            risk_factors.append("High impact severity on dependent entities")
        elif max_severity > 0.5:
            risk_score += 1
            risk_factors.append("Moderate impact severity on dependent entities")
        
        # Factor 4: Required updates
        required_updates = sum(1 for e in directly_impacted if e.requires_update)
        if required_updates > 10:
            risk_score += 2
            risk_factors.append(f"Many entities require updates ({required_updates})")
        elif required_updates > 5:
            risk_score += 1
            risk_factors.append(f"Several entities require updates ({required_updates})")
        
        # Determine risk level
        if risk_score >= 7:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 5:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return risk_level, risk_factors
    
    def _determine_impact_scope(self, change: CodeChange,
                               directly_impacted: List[ImpactedEntity],
                               indirectly_impacted: List[ImpactedEntity]) -> ImpactScope:
        """Determine the scope of impact."""
        affected_files = {change.file_path}
        affected_files.update(e.file_path for e in directly_impacted)
        affected_files.update(e.file_path for e in indirectly_impacted)
        
        # Check if all in same file
        if len(affected_files) == 1:
            return ImpactScope.LOCAL
        
        # Check if all in same directory (module)
        directories = {f.parent for f in affected_files}
        if len(directories) == 1:
            return ImpactScope.MODULE
        
        # Check if all in same top-level package
        top_level_dirs = {f.parts[0] if f.parts else "" for f in affected_files}
        if len(top_level_dirs) <= 2:
            return ImpactScope.PACKAGE
        
        return ImpactScope.GLOBAL
    
    def _generate_recommendations(self, change: CodeChange,
                                 directly_impacted: List[ImpactedEntity],
                                 indirectly_impacted: List[ImpactedEntity],
                                 risk_level: RiskLevel) -> List[str]:
        """Generate recommendations for handling the change."""
        recommendations = []
        
        # Risk-based recommendations
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recommendations.append("Create comprehensive test coverage before making changes")
            recommendations.append("Consider breaking this change into smaller, incremental steps")
            recommendations.append("Schedule code review with team before implementation")
        
        # Update recommendations
        entities_requiring_updates = [e for e in directly_impacted if e.requires_update]
        if entities_requiring_updates:
            recommendations.append(
                f"Update {len(entities_requiring_updates)} dependent entities that require changes"
            )
        
        # Testing recommendations
        if len(directly_impacted) > 5:
            recommendations.append("Add integration tests to verify dependent functionality")
        
        # Documentation recommendations
        if change.change_type in (ChangeType.DELETE, ChangeType.RENAME, ChangeType.MOVE):
            recommendations.append("Update documentation to reflect the changes")
        
        # Rollback recommendations
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recommendations.append("Prepare rollback plan in case of issues")
        
        return recommendations
    
    def _estimate_effort(self, directly_impacted: List[ImpactedEntity],
                        indirectly_impacted: List[ImpactedEntity]) -> str:
        """Estimate effort required for the change."""
        total_impacted = len(directly_impacted) + len(indirectly_impacted)
        required_updates = sum(1 for e in directly_impacted if e.requires_update)
        
        if total_impacted > 20 or required_updates > 10:
            return "high"
        elif total_impacted > 10 or required_updates > 5:
            return "medium"
        else:
            return "low"
    
    async def coordinate_multi_file_changes(self, changes: List[CodeChange]) -> MultiFileChange:
        """Coordinate changes across multiple files."""
        # Analyze each change
        analyses = []
        for change in changes:
            analysis = await self.analyze_change_impact(change)
            analyses.append(analysis)
        
        # Build dependency graph between changes
        dependencies = self._build_change_dependencies(changes, analyses)
        
        # Determine execution order
        execution_order = self._determine_execution_order(changes, dependencies)
        
        # Assess total risk
        total_risk = self._assess_total_risk(analyses)
        
        # Generate validation steps
        validation_steps = self._generate_validation_steps(changes, analyses)
        
        return MultiFileChange(
            id=f"multi_change_{len(changes)}",
            description=f"Coordinated changes across {len(changes)} entities",
            changes=changes,
            dependencies=dependencies,
            execution_order=execution_order,
            total_risk=total_risk,
            validation_steps=validation_steps
        )
    
    def _build_change_dependencies(self, changes: List[CodeChange],
                                   analyses: List[ImpactAnalysis]) -> List[Tuple[str, str]]:
        """Build dependencies between changes."""
        dependencies = []
        
        for i, change1 in enumerate(changes):
            for j, change2 in enumerate(changes):
                if i == j:
                    continue
                
                # Check if change2 impacts change1's entity
                analysis2 = analyses[j]
                impacted_ids = {e.entity_id for e in analysis2.directly_impacted}
                
                if change1.entity_id in impacted_ids:
                    # change1 depends on change2
                    dependencies.append((change1.id, change2.id))
        
        return dependencies
    
    def _determine_execution_order(self, changes: List[CodeChange],
                                   dependencies: List[Tuple[str, str]]) -> List[str]:
        """Determine optimal execution order using topological sort."""
        # Build adjacency list
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for change in changes:
            in_degree[change.id] = 0
        
        for dependent, dependency in dependencies:
            graph[dependency].append(dependent)
            in_degree[dependent] += 1
        
        # Topological sort
        queue = [change.id for change in changes if in_degree[change.id] == 0]
        order = []
        
        while queue:
            current = queue.pop(0)
            order.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If not all changes are in order, there's a cycle
        if len(order) != len(changes):
            logger.warning("Circular dependency detected in changes")
            # Return original order
            return [c.id for c in changes]
        
        return order
    
    def _assess_total_risk(self, analyses: List[ImpactAnalysis]) -> RiskLevel:
        """Assess total risk across all changes."""
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        max_risk_score = max(risk_scores[a.risk_level] for a in analyses)
        
        for score, level in sorted(risk_scores.items(), key=lambda x: x[1], reverse=True):
            if max_risk_score >= score:
                return level
        
        return RiskLevel.LOW
    
    def _generate_validation_steps(self, changes: List[CodeChange],
                                   analyses: List[ImpactAnalysis]) -> List[str]:
        """Generate validation steps for multi-file changes."""
        steps = [
            "Run all existing tests to establish baseline",
            "Apply changes in the determined execution order",
        ]
        
        # Add specific validation for each change
        for i, analysis in enumerate(analyses):
            if analysis.directly_impacted:
                steps.append(
                    f"Verify {len(analysis.directly_impacted)} entities impacted by change {i+1}"
                )
        
        steps.extend([
            "Run full test suite to verify no regressions",
            "Perform integration testing on affected modules",
            "Review all modified files for consistency"
        ])
        
        return steps
    
    async def validate_change(self, change: CodeChange) -> ChangeValidation:
        """Validate a proposed change."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check if entity exists
        entity = self.knowledge_graph.get_entity(change.entity_id)
        if not entity:
            errors.append(f"Entity {change.entity_id} not found in knowledge graph")
            return ChangeValidation(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                confidence=0.0
            )
        
        # Analyze impact
        analysis = await self.analyze_change_impact(change)
        
        # Check for high-risk changes
        if analysis.risk_level == RiskLevel.CRITICAL:
            warnings.append("This is a critical-risk change that requires careful review")
        
        # Check for breaking changes
        if change.change_type in (ChangeType.DELETE, ChangeType.RENAME):
            entities_requiring_updates = [e for e in analysis.directly_impacted if e.requires_update]
            if entities_requiring_updates:
                warnings.append(
                    f"This change will break {len(entities_requiring_updates)} dependent entities"
                )
        
        # Add suggestions from analysis
        suggestions.extend(analysis.recommendations)
        
        # Calculate confidence
        confidence = 1.0
        if analysis.risk_level == RiskLevel.CRITICAL:
            confidence -= 0.3
        elif analysis.risk_level == RiskLevel.HIGH:
            confidence -= 0.2
        elif analysis.risk_level == RiskLevel.MEDIUM:
            confidence -= 0.1
        
        is_valid = len(errors) == 0
        
        return ChangeValidation(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence=confidence
        )
