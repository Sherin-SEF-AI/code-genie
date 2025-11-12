"""
End-to-end tests for agent specialization workflows.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.codegenie.agents.base_agent import Task, AgentResult
from src.codegenie.agents.architect import ArchitectAgent, TechnologyRecommendation, SystemDesign
from src.codegenie.agents.developer import DeveloperAgent, CodeGenerationType, ProgrammingLanguage
from src.codegenie.agents.security import SecurityAgent, Vulnerability, VulnerabilityType, SeverityLevel
from src.codegenie.agents.performance import PerformanceAgent, PerformanceIssue, OptimizationRecommendation
from src.codegenie.agents.testing import TesterAgent, TestType, TestFramework, TestSuite
from src.codegenie.agents.documentation import DocumentationAgent, DocumentationType, DocumentationFormat
from src.codegenie.agents.refactoring import RefactoringAgent, RefactoringType, RefactoringOpportunity
from src.codegenie.core.config import Config
from src.codegenie.models.model_router import ModelRouter


class TestAgentSpecializationE2E:
    """End-to-end tests for specialized agent workflows."""
    
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
        """Create mock model router with realistic responses."""
        router = Mock(spec=ModelRouter)
        router.route_request = AsyncMock()
        router.analyze_task = Mock(return_value=("code_generation", "medium"))
        
        # Mock realistic AI responses
        mock_response = Mock()
        mock_response.message = Mock()
        mock_response.message.content = """
        Based on the requirements, I recommend implementing a microservices architecture
        with the following components:
        
        1. API Gateway for request routing
        2. Authentication service for user management
        3. Business logic services for core functionality
        4. Database layer with proper indexing
        
        This approach provides scalability and maintainability.
        """
        router.route_request.return_value = mock_response
        
        return router
    
    @pytest.fixture
    async def all_agents(self, config, model_router):
        """Create all specialized agents."""
        return {
            "architect": ArchitectAgent(config, model_router),
            "developer": DeveloperAgent(config, model_router),
            "security": SecurityAgent(config, model_router),
            "performance": PerformanceAgent(config, model_router),
            "tester": TesterAgent(config, model_router),
            "documentation": DocumentationAgent(config, model_router),
            "refactoring": RefactoringAgent(config, model_router)
        }
    
    async def test_complete_development_workflow(self, all_agents):
        """Test complete development workflow using all specialized agents."""
        
        # 1. Architecture Design Phase
        architect = all_agents["architect"]
        
        arch_task = Task(
            description="Design architecture for e-commerce platform",
            task_type="architecture_design",
            context={
                "requirements": {
                    "functional": ["user_registration", "product_catalog", "shopping_cart", "payment"],
                    "non_functional": {"scalability": "high", "security": "high", "performance": "medium"}
                },
                "constraints": {"budget": "medium", "timeline": "6_months", "team_size": 5}
            }
        )
        
        arch_result = await architect.execute_task(arch_task)
        assert arch_result.success
        assert arch_result.confidence > 0.7
        
        # 2. Code Generation Phase
        developer = all_agents["developer"]
        
        dev_task = Task(
            description="Implement user authentication service",
            task_type="code_generation",
            context={
                "language": "python",
                "code_type": "api_endpoint",
                "architecture": arch_result.output
            }
        )
        
        dev_result = await developer.execute_task(dev_task)
        assert dev_result.success
        assert "code" in dev_result.output
        
        # 3. Security Analysis Phase
        security = all_agents["security"]
        
        sec_task = Task(
            description="Analyze authentication code for security vulnerabilities",
            task_type="security_analysis",
            context={
                "code": dev_result.output.get("code", ""),
                "language": "python"
            }
        )
        
        sec_result = await security.execute_task(sec_task)
        assert sec_result.success
        assert isinstance(sec_result.output, list)  # List of vulnerabilities
        
        # 4. Performance Analysis Phase
        performance = all_agents["performance"]
        
        perf_task = Task(
            description="Analyze authentication code for performance bottlenecks",
            task_type="performance_analysis",
            context={
                "code": dev_result.output.get("code", ""),
                "language": "python"
            }
        )
        
        perf_result = await performance.execute_task(perf_task)
        assert perf_result.success
        assert isinstance(perf_result.output, list)  # List of performance issues
        
        # 5. Test Generation Phase
        tester = all_agents["tester"]
        
        test_task = Task(
            description="Generate unit tests for authentication service",
            task_type="test_generation",
            context={
                "code": dev_result.output.get("code", ""),
                "test_type": "unit",
                "framework": "pytest",
                "language": "python"
            }
        )
        
        test_result = await tester.execute_task(test_task)
        assert test_result.success
        assert hasattr(test_result.output, 'test_cases')
        
        # 6. Documentation Generation Phase
        documentation = all_agents["documentation"]
        
        doc_task = Task(
            description="Generate API documentation for authentication service",
            task_type="documentation",
            context={
                "code": dev_result.output.get("code", ""),
                "doc_type": "api",
                "format": "markdown"
            }
        )
        
        doc_result = await documentation.execute_task(doc_task)
        assert doc_result.success
        assert hasattr(doc_result.output, 'content')
        
        # 7. Refactoring Phase (if needed)
        refactoring = all_agents["refactoring"]
        
        refactor_task = Task(
            description="Analyze code for refactoring opportunities",
            task_type="refactoring",
            context={
                "code": dev_result.output.get("code", ""),
                "language": "python"
            }
        )
        
        refactor_result = await refactoring.execute_task(refactor_task)
        assert refactor_result.success
        assert isinstance(refactor_result.output, list)  # List of refactoring opportunities
        
        # Verify workflow completion
        workflow_results = {
            "architecture": arch_result,
            "development": dev_result,
            "security": sec_result,
            "performance": perf_result,
            "testing": test_result,
            "documentation": doc_result,
            "refactoring": refactor_result
        }
        
        # All phases should complete successfully
        assert all(result.success for result in workflow_results.values())
        
        # Results should have appropriate confidence levels
        avg_confidence = sum(result.confidence for result in workflow_results.values()) / len(workflow_results)
        assert avg_confidence > 0.7
        
        print("Complete development workflow executed successfully!")
        for phase, result in workflow_results.items():
            print(f"  {phase}: Success={result.success}, Confidence={result.confidence:.2f}")
    
    async def test_security_focused_workflow(self, all_agents):
        """Test security-focused development workflow."""
        
        # Sample vulnerable code for testing
        vulnerable_code = """
def authenticate_user(username, password):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    return cursor.fetchone()

def process_payment(card_number, amount):
    # Store credit card in plain text
    with open('payments.txt', 'a') as f:
        f.write(f"{card_number},{amount}\\n")
    return True
"""
        
        security = all_agents["security"]
        developer = all_agents["developer"]
        
        # 1. Security Analysis
        sec_analysis_task = Task(
            description="Perform comprehensive security analysis",
            task_type="security_analysis",
            context={
                "code": vulnerable_code,
                "language": "python"
            }
        )
        
        sec_result = await security.execute_task(sec_analysis_task)
        assert sec_result.success
        
        vulnerabilities = sec_result.output
        assert len(vulnerabilities) > 0
        
        # Should detect SQL injection and hardcoded credentials issues
        vuln_types = [v.type if hasattr(v, 'type') else 'unknown' for v in vulnerabilities]
        print(f"Detected vulnerabilities: {vuln_types}")
        
        # 2. Generate Security Fixes
        sec_fix_task = Task(
            description="Generate security fixes for identified vulnerabilities",
            task_type="security_fix",
            context={
                "vulnerabilities": vulnerabilities,
                "code": vulnerable_code
            }
        )
        
        fix_result = await security.execute_task(sec_fix_task)
        assert fix_result.success
        
        # 3. Implement Secure Code
        secure_dev_task = Task(
            description="Implement secure authentication and payment processing",
            task_type="code_generation",
            context={
                "language": "python",
                "security_requirements": fix_result.output,
                "original_code": vulnerable_code
            }
        )
        
        secure_code_result = await developer.execute_task(secure_dev_task)
        assert secure_code_result.success
        
        # 4. Verify Security Improvements
        verification_task = Task(
            description="Verify security improvements in refactored code",
            task_type="security_analysis",
            context={
                "code": secure_code_result.output.get("code", ""),
                "language": "python"
            }
        )
        
        verification_result = await security.execute_task(verification_task)
        assert verification_result.success
        
        # Should have fewer or less severe vulnerabilities
        new_vulnerabilities = verification_result.output
        print(f"Vulnerabilities after fixes: {len(new_vulnerabilities)}")
        
        # Security workflow should show improvement
        assert len(new_vulnerabilities) <= len(vulnerabilities)
    
    async def test_performance_optimization_workflow(self, all_agents):
        """Test performance optimization workflow."""
        
        # Sample inefficient code
        inefficient_code = """
def process_data(items):
    results = []
    for item in items:
        for other_item in items:  # O(n²) nested loop
            if item.id == other_item.related_id:
                results.append(process_item(item, other_item))
    return results

def get_user_data(user_ids):
    users = []
    for user_id in user_ids:  # N+1 query problem
        user = database.query(f"SELECT * FROM users WHERE id = {user_id}")
        users.append(user)
    return users
"""
        
        performance = all_agents["performance"]
        developer = all_agents["developer"]
        
        # 1. Performance Analysis
        perf_analysis_task = Task(
            description="Analyze code for performance bottlenecks",
            task_type="performance_analysis",
            context={
                "code": inefficient_code,
                "language": "python"
            }
        )
        
        perf_result = await performance.execute_task(perf_analysis_task)
        assert perf_result.success
        
        issues = perf_result.output
        assert len(issues) > 0
        
        # 2. Generate Optimization Recommendations
        optimization_task = Task(
            description="Generate performance optimization recommendations",
            task_type="optimization",
            context={
                "issues": issues,
                "code": inefficient_code
            }
        )
        
        opt_result = await performance.execute_task(optimization_task)
        assert opt_result.success
        
        # 3. Implement Optimizations
        optimized_dev_task = Task(
            description="Implement performance optimizations",
            task_type="code_generation",
            context={
                "language": "python",
                "optimization_requirements": opt_result.output,
                "original_code": inefficient_code
            }
        )
        
        optimized_code_result = await developer.execute_task(optimized_dev_task)
        assert optimized_code_result.success
        
        # 4. Verify Performance Improvements
        verification_task = Task(
            description="Verify performance improvements",
            task_type="performance_analysis",
            context={
                "code": optimized_code_result.output.get("code", ""),
                "language": "python"
            }
        )
        
        verification_result = await performance.execute_task(verification_task)
        assert verification_result.success
        
        new_issues = verification_result.output
        print(f"Performance issues before: {len(issues)}")
        print(f"Performance issues after: {len(new_issues)}")
        
        # Should have fewer performance issues
        assert len(new_issues) <= len(issues)
    
    async def test_quality_assurance_workflow(self, all_agents):
        """Test comprehensive quality assurance workflow."""
        
        # Sample code for quality analysis
        sample_code = """
class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, name, email):
        user = {"name": name, "email": email}
        self.users.append(user)
        return user
    
    def find_user(self, email):
        for user in self.users:
            if user["email"] == email:
                return user
        return None
"""
        
        tester = all_agents["tester"]
        documentation = all_agents["documentation"]
        refactoring = all_agents["refactoring"]
        
        # 1. Generate Comprehensive Tests
        test_generation_task = Task(
            description="Generate comprehensive test suite",
            task_type="test_generation",
            context={
                "code": sample_code,
                "test_type": "unit",
                "framework": "pytest",
                "language": "python"
            }
        )
        
        test_result = await tester.execute_task(test_generation_task)
        assert test_result.success
        
        test_suite = test_result.output
        assert hasattr(test_suite, 'test_cases')
        assert len(test_suite.test_cases) > 0
        
        # 2. Generate Documentation
        doc_generation_task = Task(
            description="Generate comprehensive documentation",
            task_type="documentation",
            context={
                "code": sample_code,
                "doc_type": "api",
                "format": "markdown",
                "language": "python"
            }
        )
        
        doc_result = await documentation.execute_task(doc_generation_task)
        assert doc_result.success
        
        # 3. Identify Refactoring Opportunities
        refactoring_analysis_task = Task(
            description="Identify code improvement opportunities",
            task_type="refactoring",
            context={
                "code": sample_code,
                "language": "python"
            }
        )
        
        refactor_result = await refactoring.execute_task(refactoring_analysis_task)
        assert refactor_result.success
        
        opportunities = refactor_result.output
        assert isinstance(opportunities, list)
        
        # 4. Create Quality Report
        quality_metrics = {
            "test_coverage": len(test_suite.test_cases),
            "documentation_completeness": len(doc_result.output.content) > 100,
            "refactoring_opportunities": len(opportunities),
            "overall_quality": "good" if len(opportunities) < 3 else "needs_improvement"
        }
        
        print("Quality Assurance Results:")
        for metric, value in quality_metrics.items():
            print(f"  {metric}: {value}")
        
        # Quality workflow should provide comprehensive analysis
        assert quality_metrics["test_coverage"] > 0
        assert quality_metrics["documentation_completeness"]
    
    async def test_cross_agent_collaboration(self, all_agents):
        """Test collaboration between different specialized agents."""
        
        architect = all_agents["architect"]
        security = all_agents["security"]
        performance = all_agents["performance"]
        
        # 1. Architect designs system
        arch_task = Task(
            description="Design secure, high-performance API system",
            task_type="architecture_design",
            context={
                "requirements": {
                    "functional": ["api_endpoints", "authentication", "data_processing"],
                    "non_functional": {"security": "critical", "performance": "high"}
                }
            }
        )
        
        arch_result = await architect.execute_task(arch_task)
        assert arch_result.success
        
        # 2. Security agent reviews architecture
        sec_review_task = Task(
            description="Review architecture for security considerations",
            task_type="security_review",
            context={
                "architecture": arch_result.output
            }
        )
        
        sec_review_result = await security.execute_task(sec_review_task)
        assert sec_review_result.success
        
        # 3. Performance agent reviews architecture
        perf_review_task = Task(
            description="Review architecture for performance considerations",
            task_type="performance_review",
            context={
                "architecture": arch_result.output
            }
        )
        
        perf_review_result = await performance.execute_task(perf_review_task)
        assert perf_review_result.success
        
        # 4. Simulate collaboration through shared context
        collaboration_context = {
            "original_architecture": arch_result.output,
            "security_feedback": sec_review_result.output,
            "performance_feedback": perf_review_result.output
        }
        
        # 5. Architect incorporates feedback
        refined_arch_task = Task(
            description="Refine architecture based on security and performance feedback",
            task_type="architecture_refinement",
            context=collaboration_context
        )
        
        refined_arch_result = await architect.execute_task(refined_arch_task)
        assert refined_arch_result.success
        
        # Collaboration should result in improved architecture
        assert refined_arch_result.confidence >= arch_result.confidence
        
        print("Cross-agent collaboration completed successfully!")
        print(f"Original architecture confidence: {arch_result.confidence:.2f}")
        print(f"Refined architecture confidence: {refined_arch_result.confidence:.2f}")
    
    async def test_agent_expertise_provision(self, all_agents):
        """Test agents providing expertise on domain-specific questions."""
        
        expertise_questions = {
            "architect": "What are the best practices for microservices architecture?",
            "developer": "How should I implement error handling in Python?",
            "security": "What are the most common web application vulnerabilities?",
            "performance": "How can I optimize database query performance?",
            "tester": "What testing strategies should I use for API endpoints?",
            "documentation": "How should I structure API documentation?",
            "refactoring": "When should I extract a method from existing code?"
        }
        
        expertise_results = {}
        
        for agent_name, question in expertise_questions.items():
            agent = all_agents[agent_name]
            expertise = await agent.provide_expertise(question)
            
            assert "expertise" in expertise
            assert expertise["confidence"] > 0.8
            assert len(expertise["expertise"]) > 100  # Substantial response
            
            expertise_results[agent_name] = expertise
            
            print(f"{agent_name.title()} Agent Expertise:")
            print(f"  Question: {question}")
            print(f"  Confidence: {expertise['confidence']:.2f}")
            print(f"  Response length: {len(expertise['expertise'])} characters")
        
        # All agents should provide domain-specific expertise
        assert len(expertise_results) == len(all_agents)
        
        # Average confidence should be high
        avg_confidence = sum(
            result["confidence"] for result in expertise_results.values()
        ) / len(expertise_results)
        assert avg_confidence > 0.85


if __name__ == "__main__":
    pytest.main([__file__])