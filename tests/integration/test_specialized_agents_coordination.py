"""
Integration tests for specialized agent coordination.
"""

import pytest
import asyncio
from pathlib import Path

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

from src.codegenie.agents import (
    ArchitectAgent, DeveloperAgent, SecurityAgent, PerformanceAgent,
    TesterAgent, DocumentationAgent, RefactoringAgent,
    AgentCoordinator, AgentCommunicationBus, Task, TaskPriority,
    CoordinationStrategy
)
from src.codegenie.core.config import Config
from src.codegenie.core.tool_executor import ToolExecutor
from src.codegenie.models.model_router import ModelRouter


@pytest.fixture
def config():
    """Create test configuration."""
    return Config()


@pytest.fixture
def model_router(config):
    """Create model router."""
    return ModelRouter(config)


@pytest.fixture
def tool_executor():
    """Create tool executor."""
    return ToolExecutor()


@pytest.fixture
def communication_bus():
    """Create communication bus."""
    return AgentCommunicationBus()


@pytest.fixture
def coordinator(communication_bus):
    """Create agent coordinator."""
    return AgentCoordinator(communication_bus)


@pytest.fixture
def architect_agent(config, model_router, tool_executor):
    """Create architect agent."""
    return ArchitectAgent(config, model_router, tool_executor)


@pytest.fixture
def developer_agent(config, model_router, tool_executor):
    """Create developer agent."""
    return DeveloperAgent(config, model_router, tool_executor)


@pytest.fixture
def security_agent(config, model_router, tool_executor):
    """Create security agent."""
    return SecurityAgent(config, model_router, tool_executor)


@pytest.fixture
def performance_agent(config, model_router, tool_executor):
    """Create performance agent."""
    return PerformanceAgent(config, model_router, tool_executor)


@pytest.fixture
def tester_agent(config, model_router, tool_executor):
    """Create tester agent."""
    return TesterAgent(config, model_router, tool_executor)


@pytest.fixture
def documentation_agent(config, model_router, tool_executor):
    """Create documentation agent."""
    return DocumentationAgent(config, model_router, tool_executor)


@pytest.fixture
def refactoring_agent(config, model_router, tool_executor):
    """Create refactoring agent."""
    return RefactoringAgent(config, model_router, tool_executor)


class TestAgentRegistration:
    """Test agent registration with coordinator."""
    
    @pytest.mark.asyncio
    async def test_register_all_agents(
        self,
        coordinator,
        architect_agent,
        developer_agent,
        security_agent,
        performance_agent,
        tester_agent,
        documentation_agent,
        refactoring_agent
    ):
        """Test registering all specialized agents."""
        # Register agents with different priorities
        coordinator.register_agent(architect_agent, priority=5)
        coordinator.register_agent(developer_agent, priority=4)
        coordinator.register_agent(security_agent, priority=5)
        coordinator.register_agent(performance_agent, priority=3)
        coordinator.register_agent(tester_agent, priority=3)
        coordinator.register_agent(documentation_agent, priority=2)
        coordinator.register_agent(refactoring_agent, priority=3)
        
        # Verify all agents registered
        assert len(coordinator.agents) == 7
        assert "ArchitectAgent" in coordinator.agents
        assert "DeveloperAgent" in coordinator.agents
        assert "SecurityAgent" in coordinator.agents
        
        # Verify priorities
        assert coordinator.agent_priorities["ArchitectAgent"] == 5
        assert coordinator.agent_priorities["SecurityAgent"] == 5
        assert coordinator.agent_priorities["DeveloperAgent"] == 4


class TestTaskDelegation:
    """Test task delegation to appropriate agents."""
    
    @pytest.mark.asyncio
    async def test_delegate_architecture_task(self, coordinator, architect_agent):
        """Test delegating architecture task."""
        coordinator.register_agent(architect_agent, priority=5)
        
        task = Task(
            description="Design system architecture",
            task_type="architecture_design",
            priority=TaskPriority.HIGH
        )
        
        assignment = await coordinator.delegate_task(task)
        
        assert assignment is not None
        assert assignment.agent_name == "ArchitectAgent"
        assert assignment.task.id == task.id
    
    @pytest.mark.asyncio
    async def test_delegate_security_task(self, coordinator, security_agent):
        """Test delegating security task."""
        coordinator.register_agent(security_agent, priority=5)
        
        task = Task(
            description="Scan code for vulnerabilities",
            task_type="security_scan",
            priority=TaskPriority.CRITICAL
        )
        
        assignment = await coordinator.delegate_task(task)
        
        assert assignment is not None
        assert assignment.agent_name == "SecurityAgent"
    
    @pytest.mark.asyncio
    async def test_delegate_to_multiple_capable_agents(
        self,
        coordinator,
        developer_agent,
        refactoring_agent
    ):
        """Test delegation when multiple agents can handle task."""
        coordinator.register_agent(developer_agent, priority=4)
        coordinator.register_agent(refactoring_agent, priority=3)
        
        task = Task(
            description="Improve code quality",
            task_type="code_improvement",
            priority=TaskPriority.MEDIUM
        )
        
        assignment = await coordinator.delegate_task(task)
        
        assert assignment is not None
        # Should select developer agent due to higher priority
        assert assignment.agent_name == "DeveloperAgent"


class TestAgentCollaboration:
    """Test collaboration between agents."""
    
    @pytest.mark.asyncio
    async def test_architect_developer_collaboration(
        self,
        architect_agent,
        developer_agent
    ):
        """Test collaboration between architect and developer."""
        task = Task(
            description="Implement new feature",
            task_type="feature_implementation"
        )
        
        # Architect provides design
        collab_result = await architect_agent.collaborate_with(
            developer_agent,
            task,
            collaboration_type="consultation"
        )
        
        assert collab_result.success
        assert "ArchitectAgent" in collab_result.participating_agents
        assert "DeveloperAgent" in collab_result.participating_agents
    
    @pytest.mark.asyncio
    async def test_security_developer_collaboration(
        self,
        security_agent,
        developer_agent
    ):
        """Test security agent consulting with developer."""
        task = Task(
            description="Fix security vulnerability",
            task_type="security_fix"
        )
        
        collab_result = await security_agent.collaborate_with(
            developer_agent,
            task,
            collaboration_type="delegation"
        )
        
        assert collab_result.success
        assert len(collab_result.participating_agents) == 2


class TestCoordinationStrategies:
    """Test different coordination strategies."""
    
    @pytest.mark.asyncio
    async def test_sequential_coordination(
        self,
        coordinator,
        architect_agent,
        developer_agent,
        tester_agent
    ):
        """Test sequential task coordination."""
        coordinator.register_agent(architect_agent, priority=5)
        coordinator.register_agent(developer_agent, priority=4)
        coordinator.register_agent(tester_agent, priority=3)
        
        # Create subtasks
        design_task = Task(
            description="Design architecture",
            task_type="architecture_design"
        )
        implement_task = Task(
            description="Implement code",
            task_type="code_implementation"
        )
        test_task = Task(
            description="Write tests",
            task_type="test_generation"
        )
        
        plan = await coordinator.coordinate_complex_task(
            description="Build new feature",
            subtasks=[design_task, implement_task, test_task],
            strategy=CoordinationStrategy.SEQUENTIAL
        )
        
        assert plan is not None
        assert len(plan.assignments) == 3
        assert plan.strategy == CoordinationStrategy.SEQUENTIAL
    
    @pytest.mark.asyncio
    async def test_parallel_coordination(
        self,
        coordinator,
        security_agent,
        performance_agent,
        documentation_agent
    ):
        """Test parallel task coordination."""
        coordinator.register_agent(security_agent, priority=5)
        coordinator.register_agent(performance_agent, priority=3)
        coordinator.register_agent(documentation_agent, priority=2)
        
        # Create independent tasks
        security_task = Task(
            description="Security scan",
            task_type="security_scan"
        )
        performance_task = Task(
            description="Performance analysis",
            task_type="performance_analysis"
        )
        doc_task = Task(
            description="Generate documentation",
            task_type="documentation_generation"
        )
        
        plan = await coordinator.coordinate_complex_task(
            description="Code quality review",
            subtasks=[security_task, performance_task, doc_task],
            strategy=CoordinationStrategy.PARALLEL
        )
        
        assert plan is not None
        assert len(plan.assignments) == 3
        assert plan.strategy == CoordinationStrategy.PARALLEL


class TestConflictResolution:
    """Test conflict resolution between agents."""
    
    @pytest.mark.asyncio
    async def test_resolve_by_priority(self, coordinator, architect_agent, developer_agent):
        """Test conflict resolution by priority."""
        coordinator.register_agent(architect_agent, priority=5)
        coordinator.register_agent(developer_agent, priority=3)
        
        from src.codegenie.agents.coordinator import AgentConflict
        
        # Create conflicting results
        conflict = AgentConflict(
            task_id="test_task",
            conflicting_agents=["ArchitectAgent", "DeveloperAgent"],
            conflicting_results=[
                architect_agent.get_status(),
                developer_agent.get_status()
            ],
            conflict_type="recommendation"
        )
        
        resolution = await coordinator.resolve_conflict(conflict)
        
        assert resolution is not None
        # Should prefer architect due to higher priority


class TestToolExecutorIntegration:
    """Test agent integration with ToolExecutor."""
    
    @pytest.mark.asyncio
    async def test_security_agent_with_tool_executor(
        self,
        security_agent,
        tmp_path
    ):
        """Test security agent using tool executor."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def unsafe_function():
    password = "hardcoded_secret"
    eval(user_input)
""")
        
        task = Task(
            description="Scan for vulnerabilities",
            task_type="security_scan",
            context={
                "code": test_file.read_text(),
                "file_path": str(test_file)
            }
        )
        
        result = await security_agent.execute_task(task)
        
        assert result.success
        assert result.output is not None
    
    @pytest.mark.asyncio
    async def test_performance_agent_with_tool_executor(
        self,
        performance_agent
    ):
        """Test performance agent using tool executor."""
        code = """
for i in range(1000):
    for j in range(1000):
        result = i * j
"""
        
        task = Task(
            description="Analyze performance",
            task_type="performance_analysis",
            context={"code": code, "file_path": "test.py"}
        )
        
        result = await performance_agent.execute_task(task)
        
        assert result.success
        assert result.output is not None


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_feature_development_workflow(
        self,
        coordinator,
        architect_agent,
        developer_agent,
        security_agent,
        tester_agent,
        documentation_agent
    ):
        """Test complete feature development workflow."""
        # Register all agents
        coordinator.register_agent(architect_agent, priority=5)
        coordinator.register_agent(developer_agent, priority=4)
        coordinator.register_agent(security_agent, priority=5)
        coordinator.register_agent(tester_agent, priority=3)
        coordinator.register_agent(documentation_agent, priority=2)
        
        # Create workflow tasks
        tasks = [
            Task(description="Design architecture", task_type="architecture_design"),
            Task(description="Implement feature", task_type="code_implementation"),
            Task(description="Security review", task_type="security_scan"),
            Task(description="Generate tests", task_type="test_generation"),
            Task(description="Create documentation", task_type="documentation_generation")
        ]
        
        # Create coordination plan
        plan = await coordinator.coordinate_complex_task(
            description="Develop new feature",
            subtasks=tasks,
            strategy=CoordinationStrategy.PIPELINE,
            dependencies={
                tasks[1].id: [tasks[0].id],  # Implementation depends on design
                tasks[2].id: [tasks[1].id],  # Security depends on implementation
                tasks[3].id: [tasks[1].id],  # Tests depend on implementation
                tasks[4].id: [tasks[1].id]   # Docs depend on implementation
            }
        )
        
        assert plan is not None
        assert len(plan.assignments) == 5
        assert plan.strategy == CoordinationStrategy.PIPELINE
        
        # Verify dependencies are set
        assert len(plan.dependencies) > 0


class TestAgentPerformance:
    """Test agent performance and metrics."""
    
    @pytest.mark.asyncio
    async def test_agent_performance_tracking(self, developer_agent):
        """Test that agent tracks performance metrics."""
        task = Task(
            description="Generate code",
            task_type="code_generation",
            context={"requirements": "Create a function"}
        )
        
        # Start and execute task
        await developer_agent.start_task(task)
        result = await developer_agent.execute_task(task)
        await developer_agent.complete_task(result)
        
        # Check performance metrics
        status = developer_agent.get_status()
        assert "performance_metrics" in status
        assert status["performance_metrics"].get("total_tasks", 0) > 0
    
    @pytest.mark.asyncio
    async def test_coordinator_statistics(
        self,
        coordinator,
        architect_agent,
        developer_agent
    ):
        """Test coordinator statistics tracking."""
        coordinator.register_agent(architect_agent, priority=5)
        coordinator.register_agent(developer_agent, priority=4)
        
        stats = coordinator.get_coordination_stats()
        
        assert "registered_agents" in stats
        assert stats["registered_agents"] == 2
        assert "active_plans" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
