"""
Integration tests for multi-agent coordination system.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.codegenie.agents.base_agent import BaseAgent, Task, AgentResult, AgentCapability, TaskPriority
from src.codegenie.agents.communication import AgentCommunicationBus, Message, MessageType
from src.codegenie.agents.coordinator import AgentCoordinator, CoordinationStrategy, CoordinationPlan
from src.codegenie.agents.architect import ArchitectAgent
from src.codegenie.agents.developer import DeveloperAgent
from src.codegenie.agents.security import SecurityAgent
from src.codegenie.agents.performance import PerformanceAgent
from src.codegenie.agents.testing import TesterAgent
from src.codegenie.agents.documentation import DocumentationAgent
from src.codegenie.agents.refactoring import RefactoringAgent
from src.codegenie.core.config import Config
from src.codegenie.models.model_router import ModelRouter


class TestMultiAgentCoordination:
    """Test multi-agent coordination functionality."""
    
    @pytest.fixture
    async def config(self):
        """Create test configuration."""
        config = Mock(spec=Config)
        config.execution = Mock()
        config.execution.blocked_commands = []
        config.execution.allowed_commands = ["python", "pytest", "pip"]
        return config
    
    @pytest.fixture
    async def model_router(self):
        """Create mock model router."""
        router = Mock(spec=ModelRouter)
        router.route_request = AsyncMock()
        router.analyze_task = Mock(return_value=("code_generation", "medium"))
        return router
    
    @pytest.fixture
    async def communication_bus(self):
        """Create communication bus."""
        bus = AgentCommunicationBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.fixture
    async def coordinator(self, communication_bus):
        """Create agent coordinator."""
        return AgentCoordinator(communication_bus)
    
    @pytest.fixture
    async def specialized_agents(self, config, model_router):
        """Create all specialized agents."""
        agents = {
            "architect": ArchitectAgent(config, model_router),
            "developer": DeveloperAgent(config, model_router),
            "security": SecurityAgent(config, model_router),
            "performance": PerformanceAgent(config, model_router),
            "tester": TesterAgent(config, model_router),
            "documentation": DocumentationAgent(config, model_router),
            "refactoring": RefactoringAgent(config, model_router)
        }
        return agents
    
    @pytest.fixture
    async def coordinated_system(self, coordinator, specialized_agents, communication_bus):
        """Create fully coordinated multi-agent system."""
        # Register all agents
        for name, agent in specialized_agents.items():
            coordinator.register_agent(agent, priority=1)
        
        return {
            "coordinator": coordinator,
            "agents": specialized_agents,
            "communication_bus": communication_bus
        }
    
    async def test_agent_registration(self, coordinator, specialized_agents):
        """Test agent registration with coordinator."""
        # Register agents
        for name, agent in specialized_agents.items():
            coordinator.register_agent(agent, priority=1)
        
        # Verify registration
        assert len(coordinator.agents) == len(specialized_agents)
        assert all(name in coordinator.agents for name in specialized_agents.keys())
        
        # Test agent capabilities
        architect = coordinator.agents["architect"]
        assert AgentCapability.ARCHITECTURE_DESIGN in architect.capabilities
        
        developer = coordinator.agents["developer"]
        assert AgentCapability.CODE_GENERATION in developer.capabilities
        
        security = coordinator.agents["security"]
        assert AgentCapability.SECURITY_ANALYSIS in security.capabilities
    
    async def test_task_delegation(self, coordinated_system):
        """Test task delegation to appropriate agents."""
        coordinator = coordinated_system["coordinator"]
        
        # Create architecture task
        arch_task = Task(
            description="Design system architecture for web application",
            task_type="architecture_design",
            context={"project_type": "web_app", "scale": "medium"}
        )
        
        # Delegate task
        assignment = await coordinator.delegate_task(arch_task)
        
        # Verify delegation
        assert assignment is not None
        assert assignment.agent_name == "architect"
        assert assignment.task.id == arch_task.id
    
    async def test_sequential_coordination(self, coordinated_system):
        """Test sequential task coordination."""
        coordinator = coordinated_system["coordinator"]
        
        # Create related tasks
        tasks = [
            Task(
                id="task_1",
                description="Design system architecture",
                task_type="architecture_design"
            ),
            Task(
                id="task_2",
                description="Implement core functionality",
                task_type="code_generation"
            ),
            Task(
                id="task_3",
                description="Add security measures",
                task_type="security_analysis"
            )
        ]
        
        # Create coordination plan
        plan = await coordinator.coordinate_complex_task(
            description="Build secure web application",
            subtasks=tasks,
            strategy=CoordinationStrategy.SEQUENTIAL
        )
        
        # Verify plan
        assert plan is not None
        assert len(plan.assignments) == 3
        assert plan.strategy == CoordinationStrategy.SEQUENTIAL
        
        # Mock task execution for testing
        with patch.object(coordinator, '_execute_assignment') as mock_execute:
            mock_execute.return_value = AgentResult(
                agent_name="test_agent",
                task_id="test_task",
                success=True,
                confidence=0.9
            )
            
            # Execute plan
            success = await coordinator.execute_coordination_plan(plan)
            assert success
            assert mock_execute.call_count == 3
    
    async def test_parallel_coordination(self, coordinated_system):
        """Test parallel task coordination."""
        coordinator = coordinated_system["coordinator"]
        
        # Create independent tasks
        tasks = [
            Task(
                id="task_1",
                description="Generate documentation",
                task_type="documentation"
            ),
            Task(
                id="task_2",
                description="Write unit tests",
                task_type="test_generation"
            ),
            Task(
                id="task_3",
                description="Analyze performance",
                task_type="performance_analysis"
            )
        ]
        
        # Create coordination plan
        plan = await coordinator.coordinate_complex_task(
            description="Quality assurance tasks",
            subtasks=tasks,
            strategy=CoordinationStrategy.PARALLEL
        )
        
        # Verify plan
        assert plan is not None
        assert len(plan.assignments) == 3
        assert plan.strategy == CoordinationStrategy.PARALLEL
        
        # Mock parallel execution
        with patch.object(coordinator, '_execute_assignment') as mock_execute:
            mock_execute.return_value = AgentResult(
                agent_name="test_agent",
                task_id="test_task",
                success=True,
                confidence=0.8
            )
            
            # Execute plan
            success = await coordinator.execute_coordination_plan(plan)
            assert success
    
    async def test_agent_communication(self, coordinated_system):
        """Test inter-agent communication."""
        communication_bus = coordinated_system["communication_bus"]
        agents = coordinated_system["agents"]
        
        # Register message handlers
        received_messages = []
        
        def message_handler(message):
            received_messages.append(message)
        
        communication_bus.register_message_handler(
            "developer",
            MessageType.COLLABORATION_REQUEST,
            message_handler
        )
        
        # Send collaboration request
        success = await communication_bus.request_collaboration(
            sender="architect",
            recipient="developer",
            task_description="Implement authentication system",
            collaboration_type="consultation"
        )
        
        # Allow message processing
        await asyncio.sleep(0.1)
        
        assert success
        # Note: In a real test, we'd verify the message was received and processed
    
    async def test_conflict_resolution(self, coordinated_system):
        """Test conflict resolution between agents."""
        coordinator = coordinated_system["coordinator"]
        
        # Create conflicting results
        from src.codegenie.agents.coordinator import AgentConflict
        
        conflict = AgentConflict(
            task_id="test_task",
            conflicting_agents=["security", "performance"],
            conflicting_results=[
                AgentResult(
                    agent_name="security",
                    task_id="test_task",
                    success=True,
                    output="Use encryption",
                    confidence=0.9
                ),
                AgentResult(
                    agent_name="performance",
                    task_id="test_task",
                    success=True,
                    output="Avoid encryption for speed",
                    confidence=0.8
                )
            ],
            conflict_type="recommendation"
        )
        
        # Resolve conflict
        resolution = await coordinator.resolve_conflict(conflict)
        
        # Verify resolution
        assert resolution is not None
        assert resolution.success
        # Security agent should win due to higher confidence
        assert "encryption" in resolution.output.lower()
    
    async def test_agent_specialization(self, specialized_agents):
        """Test that agents handle appropriate tasks."""
        
        # Test architect agent
        architect = specialized_agents["architect"]
        arch_task = Task(
            description="Design microservices architecture",
            task_type="architecture_design"
        )
        assert await architect.can_handle_task(arch_task)
        
        # Test developer agent
        developer = specialized_agents["developer"]
        dev_task = Task(
            description="Implement user authentication",
            task_type="code_generation"
        )
        assert await developer.can_handle_task(dev_task)
        
        # Test security agent
        security = specialized_agents["security"]
        sec_task = Task(
            description="Scan for vulnerabilities",
            task_type="security_analysis"
        )
        assert await security.can_handle_task(sec_task)
        
        # Test performance agent
        performance = specialized_agents["performance"]
        perf_task = Task(
            description="Optimize database queries",
            task_type="performance_analysis"
        )
        assert await performance.can_handle_task(perf_task)
        
        # Test cross-specialization (agents should not handle inappropriate tasks)
        assert not await architect.can_handle_task(sec_task)
        assert not await security.can_handle_task(arch_task)
    
    async def test_coordination_with_dependencies(self, coordinated_system):
        """Test coordination with task dependencies."""
        coordinator = coordinated_system["coordinator"]
        
        # Create tasks with dependencies
        tasks = [
            Task(id="design", description="Design architecture", task_type="architecture_design"),
            Task(id="implement", description="Implement code", task_type="code_generation"),
            Task(id="test", description="Write tests", task_type="test_generation"),
            Task(id="document", description="Create documentation", task_type="documentation")
        ]
        
        # Define dependencies
        dependencies = {
            "implement": ["design"],
            "test": ["implement"],
            "document": ["implement"]
        }
        
        # Create coordination plan
        plan = await coordinator.coordinate_complex_task(
            description="Complete development workflow",
            subtasks=tasks,
            strategy=CoordinationStrategy.PIPELINE,
            dependencies=dependencies
        )
        
        # Verify dependencies are respected
        assert plan is not None
        assert plan.dependencies == dependencies
        
        # Mock execution to test dependency handling
        with patch.object(coordinator, '_execute_assignment') as mock_execute:
            mock_execute.return_value = AgentResult(
                agent_name="test_agent",
                task_id="test_task",
                success=True,
                confidence=0.85
            )
            
            success = await coordinator.execute_coordination_plan(plan)
            assert success
    
    async def test_agent_collaboration(self, specialized_agents):
        """Test collaboration between agents."""
        architect = specialized_agents["architect"]
        developer = specialized_agents["developer"]
        
        # Create collaboration task
        task = Task(
            description="Design and implement API",
            task_type="collaboration"
        )
        
        # Mock collaboration
        with patch.object(developer, 'execute_task') as mock_dev_execute:
            mock_dev_execute.return_value = AgentResult(
                agent_name="developer",
                task_id=task.id,
                success=True,
                output="API implementation",
                confidence=0.8
            )
            
            # Test collaboration
            result = await architect.collaborate_with(
                developer, task, "consultation"
            )
            
            assert result.success
            assert "developer" in result.participating_agents
            assert "architect" in result.participating_agents
    
    async def test_system_performance_under_load(self, coordinated_system):
        """Test system performance with multiple concurrent tasks."""
        coordinator = coordinated_system["coordinator"]
        
        # Create multiple tasks
        tasks = []
        for i in range(10):
            task = Task(
                id=f"task_{i}",
                description=f"Process item {i}",
                task_type="code_generation"
            )
            tasks.append(task)
        
        # Create coordination plan
        plan = await coordinator.coordinate_complex_task(
            description="Batch processing",
            subtasks=tasks,
            strategy=CoordinationStrategy.PARALLEL
        )
        
        # Mock fast execution
        with patch.object(coordinator, '_execute_assignment') as mock_execute:
            mock_execute.return_value = AgentResult(
                agent_name="developer",
                task_id="test_task",
                success=True,
                confidence=0.9
            )
            
            # Measure execution time
            import time
            start_time = time.time()
            success = await coordinator.execute_coordination_plan(plan)
            execution_time = time.time() - start_time
            
            assert success
            assert execution_time < 5.0  # Should complete within 5 seconds
            assert mock_execute.call_count == 10
    
    async def test_error_handling_and_recovery(self, coordinated_system):
        """Test error handling and recovery in coordination."""
        coordinator = coordinated_system["coordinator"]
        
        # Create tasks
        tasks = [
            Task(id="task_1", description="Normal task", task_type="code_generation"),
            Task(id="task_2", description="Failing task", task_type="code_generation"),
            Task(id="task_3", description="Recovery task", task_type="code_generation")
        ]
        
        # Create plan
        plan = await coordinator.coordinate_complex_task(
            description="Error handling test",
            subtasks=tasks,
            strategy=CoordinationStrategy.SEQUENTIAL
        )
        
        # Mock execution with one failure
        def mock_execute_side_effect(assignment):
            if assignment.task.id == "task_2":
                return AgentResult(
                    agent_name="developer",
                    task_id=assignment.task.id,
                    success=False,
                    error="Simulated failure"
                )
            return AgentResult(
                agent_name="developer",
                task_id=assignment.task.id,
                success=True,
                confidence=0.9
            )
        
        with patch.object(coordinator, '_execute_assignment', side_effect=mock_execute_side_effect):
            # Execute plan (should handle failure gracefully)
            success = await coordinator.execute_coordination_plan(plan)
            
            # Plan should fail due to sequential execution with failure
            assert not success
    
    async def test_coordination_statistics(self, coordinated_system):
        """Test coordination statistics and monitoring."""
        coordinator = coordinated_system["coordinator"]
        
        # Get initial stats
        initial_stats = coordinator.get_coordination_stats()
        assert "registered_agents" in initial_stats
        assert initial_stats["registered_agents"] == 7  # All specialized agents
        
        # Create and execute a simple plan
        task = Task(description="Test task", task_type="code_generation")
        plan = await coordinator.coordinate_complex_task(
            description="Stats test",
            subtasks=[task],
            strategy=CoordinationStrategy.SEQUENTIAL
        )
        
        # Mock execution
        with patch.object(coordinator, '_execute_assignment') as mock_execute:
            mock_execute.return_value = AgentResult(
                agent_name="developer",
                task_id=task.id,
                success=True,
                confidence=0.9
            )
            
            await coordinator.execute_coordination_plan(plan)
        
        # Check updated stats
        updated_stats = coordinator.get_coordination_stats()
        assert updated_stats["active_plans"] >= initial_stats["active_plans"]
        assert updated_stats["completed_plans"] >= initial_stats["completed_plans"]


class TestAgentSpecialization:
    """Test individual agent specialization and capabilities."""
    
    @pytest.fixture
    async def config(self):
        """Create test configuration."""
        config = Mock(spec=Config)
        return config
    
    @pytest.fixture
    async def model_router(self):
        """Create mock model router."""
        router = Mock(spec=ModelRouter)
        router.route_request = AsyncMock()
        
        # Mock response
        mock_response = Mock()
        mock_response.message = Mock()
        mock_response.message.content = "Test response"
        router.route_request.return_value = mock_response
        
        return router
    
    async def test_architect_agent_capabilities(self, config, model_router):
        """Test architect agent specific capabilities."""
        agent = ArchitectAgent(config, model_router)
        
        # Test capability identification
        assert AgentCapability.ARCHITECTURE_DESIGN in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
        
        # Test task handling
        arch_task = Task(
            description="Design microservices architecture",
            task_type="architecture_design"
        )
        assert await agent.can_handle_task(arch_task)
        
        # Test non-architecture task
        security_task = Task(
            description="Scan for vulnerabilities",
            task_type="security_analysis"
        )
        assert not await agent.can_handle_task(security_task)
    
    async def test_developer_agent_capabilities(self, config, model_router):
        """Test developer agent specific capabilities."""
        agent = DeveloperAgent(config, model_router)
        
        # Test capabilities
        assert AgentCapability.CODE_GENERATION in agent.capabilities
        assert AgentCapability.DEBUGGING in agent.capabilities
        
        # Test task handling
        dev_task = Task(
            description="Implement user authentication",
            task_type="code_generation"
        )
        assert await agent.can_handle_task(dev_task)
        
        debug_task = Task(
            description="Fix authentication bug",
            task_type="debugging"
        )
        assert await agent.can_handle_task(debug_task)
    
    async def test_security_agent_capabilities(self, config, model_router):
        """Test security agent specific capabilities."""
        agent = SecurityAgent(config, model_router)
        
        # Test capabilities
        assert AgentCapability.SECURITY_ANALYSIS in agent.capabilities
        
        # Test task handling
        security_task = Task(
            description="Perform security audit",
            task_type="security_analysis"
        )
        assert await agent.can_handle_task(security_task)
        
        vuln_task = Task(
            description="Scan for SQL injection vulnerabilities",
            task_type="vulnerability_scan"
        )
        assert await agent.can_handle_task(vuln_task)
    
    async def test_performance_agent_capabilities(self, config, model_router):
        """Test performance agent specific capabilities."""
        agent = PerformanceAgent(config, model_router)
        
        # Test capabilities
        assert AgentCapability.PERFORMANCE_OPTIMIZATION in agent.capabilities
        
        # Test task handling
        perf_task = Task(
            description="Optimize database queries",
            task_type="performance_analysis"
        )
        assert await agent.can_handle_task(perf_task)
        
        bottleneck_task = Task(
            description="Identify performance bottlenecks",
            task_type="bottleneck_analysis"
        )
        assert await agent.can_handle_task(bottleneck_task)
    
    async def test_testing_agent_capabilities(self, config, model_router):
        """Test testing agent specific capabilities."""
        agent = TesterAgent(config, model_router)
        
        # Test capabilities
        assert AgentCapability.TESTING in agent.capabilities
        
        # Test task handling
        test_task = Task(
            description="Generate unit tests",
            task_type="test_generation"
        )
        assert await agent.can_handle_task(test_task)
        
        coverage_task = Task(
            description="Analyze test coverage",
            task_type="coverage_analysis"
        )
        assert await agent.can_handle_task(coverage_task)
    
    async def test_documentation_agent_capabilities(self, config, model_router):
        """Test documentation agent specific capabilities."""
        agent = DocumentationAgent(config, model_router)
        
        # Test capabilities
        assert AgentCapability.DOCUMENTATION in agent.capabilities
        
        # Test task handling
        doc_task = Task(
            description="Generate API documentation",
            task_type="documentation"
        )
        assert await agent.can_handle_task(doc_task)
        
        readme_task = Task(
            description="Create README file",
            task_type="readme_generation"
        )
        assert await agent.can_handle_task(readme_task)
    
    async def test_refactoring_agent_capabilities(self, config, model_router):
        """Test refactoring agent specific capabilities."""
        agent = RefactoringAgent(config, model_router)
        
        # Test capabilities
        assert AgentCapability.REFACTORING in agent.capabilities
        
        # Test task handling
        refactor_task = Task(
            description="Refactor legacy code",
            task_type="refactoring"
        )
        assert await agent.can_handle_task(refactor_task)
        
        cleanup_task = Task(
            description="Clean up code smells",
            task_type="code_cleanup"
        )
        assert await agent.can_handle_task(cleanup_task)


if __name__ == "__main__":
    pytest.main([__file__])