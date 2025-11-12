"""
Basic integration tests for specialized agents to verify core functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.codegenie.agents.base_agent import Task, AgentCapability
from src.codegenie.agents.architect import ArchitectAgent
from src.codegenie.agents.developer import DeveloperAgent
from src.codegenie.agents.security import SecurityAgent
from src.codegenie.agents.performance import PerformanceAgent
from src.codegenie.agents.testing import TesterAgent
from src.codegenie.agents.documentation import DocumentationAgent
from src.codegenie.agents.refactoring import RefactoringAgent
from src.codegenie.core.config import Config
from src.codegenie.models.model_router import ModelRouter


class TestSpecializedAgentsBasic:
    """Basic tests to verify specialized agents can be instantiated and handle tasks."""
    
    @pytest.fixture
    def config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        return config
    
    @pytest.fixture
    def model_router(self):
        """Create mock model router."""
        router = Mock(spec=ModelRouter)
        router.route_request = AsyncMock()
        
        # Mock response
        mock_response = Mock()
        mock_response.message = Mock()
        mock_response.message.content = "Test response from AI model"
        router.route_request.return_value = mock_response
        
        return router
    
    def test_architect_agent_initialization(self, config, model_router):
        """Test architect agent can be initialized."""
        agent = ArchitectAgent(config, model_router)
        
        assert agent.name == "architect"
        assert AgentCapability.ARCHITECTURE_DESIGN in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
        assert AgentCapability.PROJECT_PLANNING in agent.capabilities
    
    def test_developer_agent_initialization(self, config, model_router):
        """Test developer agent can be initialized."""
        agent = DeveloperAgent(config, model_router)
        
        assert agent.name == "developer"
        assert AgentCapability.CODE_GENERATION in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
        assert AgentCapability.DEBUGGING in agent.capabilities
        assert AgentCapability.REFACTORING in agent.capabilities
    
    def test_security_agent_initialization(self, config, model_router):
        """Test security agent can be initialized."""
        agent = SecurityAgent(config, model_router)
        
        assert agent.name == "security"
        assert AgentCapability.SECURITY_ANALYSIS in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
    
    def test_performance_agent_initialization(self, config, model_router):
        """Test performance agent can be initialized."""
        agent = PerformanceAgent(config, model_router)
        
        assert agent.name == "performance"
        assert AgentCapability.PERFORMANCE_OPTIMIZATION in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
    
    def test_testing_agent_initialization(self, config, model_router):
        """Test testing agent can be initialized."""
        agent = TesterAgent(config, model_router)
        
        assert agent.name == "tester"
        assert AgentCapability.TESTING in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
        assert AgentCapability.CODE_GENERATION in agent.capabilities
    
    def test_documentation_agent_initialization(self, config, model_router):
        """Test documentation agent can be initialized."""
        agent = DocumentationAgent(config, model_router)
        
        assert agent.name == "documentation"
        assert AgentCapability.DOCUMENTATION in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
    
    def test_refactoring_agent_initialization(self, config, model_router):
        """Test refactoring agent can be initialized."""
        agent = RefactoringAgent(config, model_router)
        
        assert agent.name == "refactoring"
        assert AgentCapability.REFACTORING in agent.capabilities
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
        assert AgentCapability.CODE_GENERATION in agent.capabilities
    
    async def test_architect_task_handling(self, config, model_router):
        """Test architect agent can handle architecture tasks."""
        agent = ArchitectAgent(config, model_router)
        
        # Architecture task
        arch_task = Task(
            description="Design system architecture",
            task_type="architecture_design"
        )
        
        assert await agent.can_handle_task(arch_task)
        
        # Non-architecture task
        security_task = Task(
            description="Scan for vulnerabilities",
            task_type="security_analysis"
        )
        
        assert not await agent.can_handle_task(security_task)
    
    async def test_developer_task_handling(self, config, model_router):
        """Test developer agent can handle development tasks."""
        agent = DeveloperAgent(config, model_router)
        
        # Development task
        dev_task = Task(
            description="Implement user authentication",
            task_type="code_generation"
        )
        
        assert await agent.can_handle_task(dev_task)
        
        # Debug task
        debug_task = Task(
            description="Fix authentication bug",
            task_type="debugging"
        )
        
        assert await agent.can_handle_task(debug_task)
    
    async def test_security_task_handling(self, config, model_router):
        """Test security agent can handle security tasks."""
        agent = SecurityAgent(config, model_router)
        
        # Security task
        security_task = Task(
            description="Perform security audit",
            task_type="security_analysis"
        )
        
        assert await agent.can_handle_task(security_task)
        
        # Vulnerability task
        vuln_task = Task(
            description="Scan for SQL injection vulnerabilities",
            task_type="vulnerability_scan"
        )
        
        assert await agent.can_handle_task(vuln_task)
    
    async def test_performance_task_handling(self, config, model_router):
        """Test performance agent can handle performance tasks."""
        agent = PerformanceAgent(config, model_router)
        
        # Performance task
        perf_task = Task(
            description="Optimize database queries",
            task_type="performance_analysis"
        )
        
        assert await agent.can_handle_task(perf_task)
        
        # Bottleneck task
        bottleneck_task = Task(
            description="Identify performance bottlenecks",
            task_type="bottleneck_analysis"
        )
        
        assert await agent.can_handle_task(bottleneck_task)
    
    async def test_testing_task_handling(self, config, model_router):
        """Test testing agent can handle testing tasks."""
        agent = TesterAgent(config, model_router)
        
        # Test generation task
        test_task = Task(
            description="Generate unit tests",
            task_type="test_generation"
        )
        
        assert await agent.can_handle_task(test_task)
        
        # Coverage task
        coverage_task = Task(
            description="Analyze test coverage",
            task_type="coverage_analysis"
        )
        
        assert await agent.can_handle_task(coverage_task)
    
    async def test_documentation_task_handling(self, config, model_router):
        """Test documentation agent can handle documentation tasks."""
        agent = DocumentationAgent(config, model_router)
        
        # Documentation task
        doc_task = Task(
            description="Generate API documentation",
            task_type="documentation"
        )
        
        assert await agent.can_handle_task(doc_task)
        
        # README task
        readme_task = Task(
            description="Create README file",
            task_type="readme_generation"
        )
        
        assert await agent.can_handle_task(readme_task)
    
    async def test_refactoring_task_handling(self, config, model_router):
        """Test refactoring agent can handle refactoring tasks."""
        agent = RefactoringAgent(config, model_router)
        
        # Refactoring task
        refactor_task = Task(
            description="Refactor legacy code",
            task_type="refactoring"
        )
        
        assert await agent.can_handle_task(refactor_task)
        
        # Code cleanup task
        cleanup_task = Task(
            description="Clean up code smells",
            task_type="code_cleanup"
        )
        
        assert await agent.can_handle_task(cleanup_task)
    
    async def test_agent_expertise_provision(self, config, model_router):
        """Test that agents can provide expertise."""
        agents = [
            ArchitectAgent(config, model_router),
            DeveloperAgent(config, model_router),
            SecurityAgent(config, model_router),
            PerformanceAgent(config, model_router),
            TesterAgent(config, model_router),
            DocumentationAgent(config, model_router),
            RefactoringAgent(config, model_router)
        ]
        
        for agent in agents:
            expertise = await agent.provide_expertise("What are the best practices in your domain?")
            
            assert "expertise" in expertise
            assert expertise["confidence"] > 0.0
            assert len(expertise["expertise"]) > 0
    
    def test_agent_statistics(self, config, model_router):
        """Test that agents provide statistics."""
        agents = [
            ArchitectAgent(config, model_router),
            DeveloperAgent(config, model_router),
            SecurityAgent(config, model_router),
            PerformanceAgent(config, model_router),
            TesterAgent(config, model_router),
            DocumentationAgent(config, model_router),
            RefactoringAgent(config, model_router)
        ]
        
        for agent in agents:
            # Each agent should have a stats method
            if hasattr(agent, 'get_architecture_stats'):
                stats = agent.get_architecture_stats()
            elif hasattr(agent, 'get_development_stats'):
                stats = agent.get_development_stats()
            elif hasattr(agent, 'get_security_stats'):
                stats = agent.get_security_stats()
            elif hasattr(agent, 'get_performance_stats'):
                stats = agent.get_performance_stats()
            elif hasattr(agent, 'get_testing_stats'):
                stats = agent.get_testing_stats()
            elif hasattr(agent, 'get_documentation_stats'):
                stats = agent.get_documentation_stats()
            elif hasattr(agent, 'get_refactoring_stats'):
                stats = agent.get_refactoring_stats()
            else:
                continue
            
            assert isinstance(stats, dict)
            assert len(stats) > 0


if __name__ == "__main__":
    pytest.main([__file__])