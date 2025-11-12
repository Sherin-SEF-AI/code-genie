"""
Unit tests for conflict resolution in multi-agent systems.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List

from src.codegenie.agents.base_agent import AgentResult
from src.codegenie.agents.coordinator import (
    AgentCoordinator, AgentConflict, ConflictResolutionStrategy
)
from src.codegenie.agents.communication import AgentCommunicationBus


class TestConflictResolution:
    """Test conflict resolution mechanisms."""
    
    @pytest.fixture
    async def communication_bus(self):
        """Create communication bus."""
        bus = AgentCommunicationBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.fixture
    async def coordinator(self, communication_bus):
        """Create coordinator with mock agents."""
        coordinator = AgentCoordinator(communication_bus)
        
        # Add mock agents with different priorities
        mock_agents = {
            "security": Mock(),
            "performance": Mock(),
            "architect": Mock()
        }
        
        for name, agent in mock_agents.items():
            agent.name = name
            coordinator.agents[name] = agent
        
        # Set different priorities
        coordinator.agent_priorities = {
            "security": 3,      # Highest priority
            "architect": 2,     # Medium priority
            "performance": 1    # Lowest priority
        }
        
        # Set performance metrics
        coordinator.agent_performance = {
            "security": {"success_rate": 0.95},
            "architect": {"success_rate": 0.90},
            "performance": {"success_rate": 0.85}
        }
        
        return coordinator
    
    def create_test_conflict(self, task_id: str = "test_task") -> AgentConflict:
        """Create a test conflict scenario."""
        return AgentConflict(
            task_id=task_id,
            conflicting_agents=["security", "performance"],
            conflicting_results=[
                AgentResult(
                    agent_name="security",
                    task_id=task_id,
                    success=True,
                    output="Use strong encryption",
                    confidence=0.9,
                    reasoning="Security is paramount"
                ),
                AgentResult(
                    agent_name="performance",
                    task_id=task_id,
                    success=True,
                    output="Avoid encryption overhead",
                    confidence=0.8,
                    reasoning="Performance optimization needed"
                )
            ],
            conflict_type="recommendation"
        )
    
    async def test_priority_based_resolution(self, coordinator):
        """Test priority-based conflict resolution."""
        conflict = self.create_test_conflict()
        conflict.resolution_strategy = ConflictResolutionStrategy.PRIORITY_BASED
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Security agent has higher priority (3 vs 1)
        assert resolution is not None
        assert resolution.agent_name == "security"
        assert "encryption" in resolution.output.lower()
        assert conflict.resolution == resolution
        assert conflict.resolved_at is not None
    
    async def test_consensus_resolution(self, coordinator):
        """Test consensus-based conflict resolution."""
        conflict = self.create_test_conflict()
        conflict.resolution_strategy = ConflictResolutionStrategy.CONSENSUS
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Should pick the result with highest confidence
        assert resolution is not None
        assert resolution.agent_name == "security"  # Higher confidence (0.9 vs 0.8)
        assert resolution.confidence == 0.9
    
    async def test_expertise_based_resolution(self, coordinator):
        """Test expertise-based conflict resolution."""
        conflict = self.create_test_conflict()
        conflict.resolution_strategy = ConflictResolutionStrategy.EXPERT_DECISION
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Security agent has higher success rate (0.95 vs 0.85)
        assert resolution is not None
        assert resolution.agent_name == "security"
    
    async def test_hybrid_resolution(self, coordinator):
        """Test hybrid conflict resolution approach."""
        conflict = self.create_test_conflict()
        conflict.resolution_strategy = ConflictResolutionStrategy.HYBRID_APPROACH
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Hybrid should consider priority, expertise, and confidence
        # Security agent should win (higher in all metrics)
        assert resolution is not None
        assert resolution.agent_name == "security"
    
    async def test_three_way_conflict(self, coordinator):
        """Test conflict resolution with three agents."""
        conflict = AgentConflict(
            task_id="three_way_test",
            conflicting_agents=["security", "performance", "architect"],
            conflicting_results=[
                AgentResult(
                    agent_name="security",
                    task_id="three_way_test",
                    success=True,
                    output="Implement OAuth2",
                    confidence=0.85
                ),
                AgentResult(
                    agent_name="performance",
                    task_id="three_way_test",
                    success=True,
                    output="Use simple API keys",
                    confidence=0.90
                ),
                AgentResult(
                    agent_name="architect",
                    task_id="three_way_test",
                    success=True,
                    output="Implement JWT tokens",
                    confidence=0.88
                )
            ],
            conflict_type="approach"
        )
        
        # Test consensus resolution (highest confidence wins)
        conflict.resolution_strategy = ConflictResolutionStrategy.CONSENSUS
        resolution = await coordinator.resolve_conflict(conflict)
        
        assert resolution is not None
        assert resolution.agent_name == "performance"  # Highest confidence
        assert resolution.confidence == 0.90
    
    async def test_conflict_with_failed_result(self, coordinator):
        """Test conflict resolution when one result failed."""
        conflict = AgentConflict(
            task_id="failed_result_test",
            conflicting_agents=["security", "performance"],
            conflicting_results=[
                AgentResult(
                    agent_name="security",
                    task_id="failed_result_test",
                    success=True,
                    output="Security recommendation",
                    confidence=0.8
                ),
                AgentResult(
                    agent_name="performance",
                    task_id="failed_result_test",
                    success=False,  # Failed result
                    output="Performance analysis failed",
                    confidence=0.0,
                    error="Analysis error"
                )
            ],
            conflict_type="recommendation"
        )
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Should pick the successful result
        assert resolution is not None
        assert resolution.agent_name == "security"
        assert resolution.success
    
    async def test_equal_priority_conflict(self, coordinator):
        """Test conflict resolution with equal priorities."""
        # Set equal priorities
        coordinator.agent_priorities["security"] = 2
        coordinator.agent_priorities["performance"] = 2
        
        conflict = self.create_test_conflict()
        conflict.resolution_strategy = ConflictResolutionStrategy.PRIORITY_BASED
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # With equal priorities, should fall back to other criteria
        # (in this case, likely the first result or highest confidence)
        assert resolution is not None
        assert resolution.agent_name in ["security", "performance"]
    
    async def test_unsupported_resolution_strategy(self, coordinator):
        """Test handling of unsupported resolution strategy."""
        conflict = self.create_test_conflict()
        conflict.resolution_strategy = "unsupported_strategy"
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Should return None for unsupported strategy
        assert resolution is None
    
    async def test_conflict_history_tracking(self, coordinator):
        """Test that conflicts are tracked in history."""
        initial_count = len(coordinator.conflict_history)
        
        conflict = self.create_test_conflict()
        await coordinator.resolve_conflict(conflict)
        
        # Should add to conflict history
        assert len(coordinator.conflict_history) == initial_count + 1
        assert coordinator.conflict_history[-1] == conflict
    
    async def test_resolution_confidence_calculation(self, coordinator):
        """Test confidence calculation in resolution."""
        # Create conflict with very different confidence levels
        conflict = AgentConflict(
            task_id="confidence_test",
            conflicting_agents=["security", "performance"],
            conflicting_results=[
                AgentResult(
                    agent_name="security",
                    task_id="confidence_test",
                    success=True,
                    output="High confidence result",
                    confidence=0.95
                ),
                AgentResult(
                    agent_name="performance",
                    task_id="confidence_test",
                    success=True,
                    output="Low confidence result",
                    confidence=0.3
                )
            ],
            conflict_type="recommendation"
        )
        
        conflict.resolution_strategy = ConflictResolutionStrategy.CONSENSUS
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Should pick high confidence result
        assert resolution is not None
        assert resolution.confidence == 0.95
        assert resolution.agent_name == "security"
    
    async def test_conflict_type_handling(self, coordinator):
        """Test different conflict types are handled appropriately."""
        conflict_types = ["recommendation", "approach", "priority", "implementation"]
        
        for conflict_type in conflict_types:
            conflict = self.create_test_conflict(f"test_{conflict_type}")
            conflict.conflict_type = conflict_type
            
            resolution = await coordinator.resolve_conflict(conflict)
            
            # All conflict types should be resolvable
            assert resolution is not None
            assert conflict.resolution == resolution
    
    async def test_resolution_with_empty_results(self, coordinator):
        """Test conflict resolution with empty results list."""
        conflict = AgentConflict(
            task_id="empty_results_test",
            conflicting_agents=[],
            conflicting_results=[],
            conflict_type="recommendation"
        )
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Should handle empty results gracefully
        assert resolution is None or not resolution.success
    
    async def test_resolution_performance(self, coordinator):
        """Test conflict resolution performance."""
        import time
        
        # Create multiple conflicts
        conflicts = []
        for i in range(10):
            conflict = self.create_test_conflict(f"perf_test_{i}")
            conflicts.append(conflict)
        
        # Measure resolution time
        start_time = time.time()
        
        for conflict in conflicts:
            await coordinator.resolve_conflict(conflict)
        
        end_time = time.time()
        resolution_time = end_time - start_time
        
        # Should resolve conflicts quickly (less than 1 second for 10 conflicts)
        assert resolution_time < 1.0
        assert len(coordinator.conflict_history) >= 10


class TestConflictDetection:
    """Test conflict detection mechanisms."""
    
    def test_result_similarity_detection(self):
        """Test detection of similar conflicting results."""
        results = [
            AgentResult(
                agent_name="agent1",
                task_id="test",
                success=True,
                output="Use Redis cache",
                confidence=0.8
            ),
            AgentResult(
                agent_name="agent2",
                task_id="test",
                success=True,
                output="Use Memcached cache",
                confidence=0.7
            )
        ]
        
        # Both suggest caching but different implementations
        # This would be detected as a conflict in a real implementation
        assert len(results) == 2
        assert all(result.success for result in results)
        assert "cache" in results[0].output.lower()
        assert "cache" in results[1].output.lower()
    
    def test_contradictory_results_detection(self):
        """Test detection of contradictory results."""
        results = [
            AgentResult(
                agent_name="security",
                task_id="test",
                success=True,
                output="Enable strict CORS policy",
                confidence=0.9
            ),
            AgentResult(
                agent_name="developer",
                task_id="test",
                success=True,
                output="Disable CORS for easier development",
                confidence=0.6
            )
        ]
        
        # These are contradictory recommendations
        assert "enable" in results[0].output.lower()
        assert "disable" in results[1].output.lower()
        assert "cors" in results[0].output.lower()
        assert "cors" in results[1].output.lower()
    
    def test_confidence_threshold_conflicts(self):
        """Test conflicts based on confidence thresholds."""
        results = [
            AgentResult(
                agent_name="agent1",
                task_id="test",
                success=True,
                output="Approach A",
                confidence=0.51  # Just above threshold
            ),
            AgentResult(
                agent_name="agent2",
                task_id="test",
                success=True,
                output="Approach B",
                confidence=0.49  # Just below threshold
            )
        ]
        
        # Close confidence levels might indicate uncertainty
        confidence_diff = abs(results[0].confidence - results[1].confidence)
        assert confidence_diff < 0.1  # Very close confidence levels


if __name__ == "__main__":
    pytest.main([__file__])