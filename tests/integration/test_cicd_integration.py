"""
Integration tests for CI/CD pipeline integration functionality.

Tests GitHub Actions, Jenkins, and GitLab CI integrations.
"""

import pytest
import asyncio
import json
import yaml
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from src.codegenie.integrations.cicd_integration import (
    CICDIntegrationManager, GitHubActionsIntegration, JenkinsIntegration,
    GitLabCIIntegration, PullRequest, ReviewResult, DeploymentPlan, QualityGate
)
from src.codegenie.core.code_intelligence import CodeIntelligence
from src.codegenie.agents.security import SecurityAgent
from src.codegenie.agents.testing import TesterAgent
from src.codegenie.agents.performance import PerformanceAgent


@pytest.fixture
def mock_code_intelligence():
    """Mock code intelligence for testing"""
    mock = AsyncMock(spec=CodeIntelligence)
    
    mock.analyze_code_quality.return_value = Mock(
        issues=[
            Mock(
                line_number=10,
                type="code_smell",
                description="Long method",
                fix_suggestion="Break into smaller methods"
            )
        ]
    )
    
    return mock


@pytest.fixture
def mock_security_agent():
    """Mock security agent for testing"""
    mock = AsyncMock(spec=SecurityAgent)
    
    mock.scan_for_vulnerabilities.return_value = Mock(
        vulnerabilities=[
            Mock(
                line_number=15,
                severity="high",
                description="SQL injection vulnerability",
                fix_suggestion="Use parameterized queries"
            )
        ]
    )
    
    return mock


@pytest.fixture
def mock_tester_agent():
    """Mock tester agent for testing"""
    mock = AsyncMock(spec=TesterAgent)
    return mock


@pytest.fixture
def mock_performance_agent():
    """Mock performance agent for testing"""
    mock = AsyncMock(spec=PerformanceAgent)
    
    mock.analyze_performance.return_value = Mock(
        bottlenecks=[
            Mock(
                line_number=25,
                type="inefficient_loop",
                description="Nested loop with O(n²) complexity",
                optimization_suggestion="Use hash map for O(n) lookup"
            )
        ]
    )
    
    return mock


@pytest.fixture
def sample_pull_request():
    """Sample pull request for testing"""
    return PullRequest(
        id="123",
        title="Add new feature",
        description="This PR adds a new feature",
        author="developer",
        source_branch="feature/new-feature",
        target_branch="main",
        files_changed=["src/main.py", "tests/test_main.py"],
        additions=50,
        deletions=10,
        url="https://github.com/repo/pull/123",
        created_at=datetime.now()
    )


@pytest.fixture
def github_integration(mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent):
    """Create GitHub Actions integration for testing"""
    return GitHubActionsIntegration(
        mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent,
        github_token="test_token"
    )


@pytest.fixture
def jenkins_integration(mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent):
    """Create Jenkins integration for testing"""
    return JenkinsIntegration(
        mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent,
        jenkins_url="http://jenkins.test", jenkins_user="test_user", jenkins_token="test_token"
    )


@pytest.fixture
def gitlab_integration(mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent):
    """Create GitLab CI integration for testing"""
    return GitLabCIIntegration(
        mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent,
        gitlab_url="https://gitlab.test", gitlab_token="test_token"
    )


@pytest.fixture
def cicd_manager(mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent):
    """Create CI/CD integration manager for testing"""
    return CICDIntegrationManager(
        mock_code_intelligence, mock_security_agent, mock_tester_agent, mock_performance_agent
    )


class TestGitHubActionsIntegration:
    """Test GitHub Actions integration functionality"""
    
    @pytest.mark.asyncio
    async def test_review_pull_request(self, github_integration, sample_pull_request):
        """Test automated pull request review"""
        # Mock HTTP session and responses
        mock_session = AsyncMock()
        github_integration.session = mock_session
        
        # Mock PR files response
        mock_session.get.return_value.__aenter__.return_value.json.return_value = [
            {
                "filename": "src/main.py",
                "status": "modified",
                "additions": 30,
                "deletions": 5
            }
        ]
        
        # Mock file content
        github_integration._get_file_content = AsyncMock(return_value="def test(): pass")
        github_integration._calculate_test_coverage = AsyncMock(return_value=0.85)
        github_integration._post_review_to_github = AsyncMock()
        
        result = await github_integration.review_pull_request(sample_pull_request)
        
        assert isinstance(result, ReviewResult)
        assert result.overall_score >= 0.0
        assert result.overall_score <= 1.0
        assert isinstance(result.security_issues, list)
        assert isinstance(result.performance_issues, list)
        assert isinstance(result.code_quality_issues, list)
        assert result.test_coverage == 0.85
        assert result.approval_status in ["approved", "needs_changes", "rejected"]
    
    @pytest.mark.asyncio
    async def test_generate_deployment_plan(self, github_integration):
        """Test deployment plan generation"""
        changes = [
            {"type": "feature", "files": ["src/main.py"], "size": 100},
            {"type": "bugfix", "files": ["src/utils.py"], "size": 20}
        ]
        
        plan = await github_integration.generate_deployment_plan(changes)
        
        assert isinstance(plan, DeploymentPlan)
        assert plan.environment == "production"
        assert len(plan.steps) > 0
        assert len(plan.rollback_plan) > 0
        assert len(plan.health_checks) > 0
        assert plan.estimated_duration > 0
        assert "level" in plan.risk_assessment
    
    @pytest.mark.asyncio
    async def test_setup_quality_gates(self, github_integration):
        """Test quality gates setup"""
        project_config = {
            "language": "python",
            "test_framework": "pytest",
            "coverage_threshold": 80
        }
        
        quality_gates = await github_integration.setup_quality_gates(project_config)
        
        assert isinstance(quality_gates, list)
        assert len(quality_gates) > 0
        
        for gate in quality_gates:
            assert isinstance(gate, QualityGate)
            assert gate.name
            assert len(gate.conditions) > 0
            assert isinstance(gate.blocking, bool)
    
    @pytest.mark.asyncio
    async def test_monitor_deployment(self, github_integration):
        """Test deployment monitoring"""
        deployment_id = "test/repo"
        
        # Mock GitHub API response
        mock_session = AsyncMock()
        github_integration.session = mock_session
        
        mock_session.get.return_value.__aenter__.return_value.json.return_value = [
            {
                "id": 1,
                "state": "success",
                "environment": "production",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T01:00:00Z",
                "statuses_url": "https://api.github.com/repos/test/repo/deployments/1/statuses",
                "url": "https://github.com/test/repo/deployments/1"
            }
        ]
        
        github_integration._check_deployment_health = AsyncMock(return_value={
            "status": "healthy",
            "checks": [{"name": "API Health", "status": "passing"}]
        })
        
        result = await github_integration.monitor_deployment(deployment_id)
        
        assert result["deployment_id"] == deployment_id
        assert result["status"] == "success"
        assert result["environment"] == "production"
        assert "health" in result
    
    @pytest.mark.asyncio
    async def test_workflow_generation(self, github_integration):
        """Test GitHub Actions workflow generation"""
        quality_gates = [
            QualityGate(
                name="Security Gate",
                conditions=[{"metric": "security_score", "operator": ">=", "value": 0.8}],
                threshold=0.8,
                blocking=True,
                description="Security quality gate"
            )
        ]
        
        project_config = {"language": "python"}
        
        # Test workflow generation (this creates a file)
        await github_integration._generate_quality_gate_workflow(quality_gates, project_config)
        
        # Check if workflow file was created
        workflow_path = Path(".github/workflows/codegenie-quality-gates.yml")
        if workflow_path.exists():
            with open(workflow_path, 'r') as f:
                workflow_content = yaml.safe_load(f)
            
            assert "name" in workflow_content
            assert "on" in workflow_content
            assert "jobs" in workflow_content
            
            # Cleanup
            workflow_path.unlink()
            workflow_path.parent.rmdir()
            workflow_path.parent.parent.rmdir()


class TestJenkinsIntegration:
    """Test Jenkins integration functionality"""
    
    @pytest.mark.asyncio
    async def test_review_pull_request(self, jenkins_integration, sample_pull_request):
        """Test Jenkins-based pull request review"""
        # Mock Jenkins job trigger and completion
        jenkins_integration._trigger_jenkins_job = AsyncMock(return_value=123)
        jenkins_integration._wait_for_job_completion = AsyncMock(return_value={
            "result": "SUCCESS",
            "building": False
        })
        jenkins_integration._parse_jenkins_results = AsyncMock(return_value=ReviewResult(
            overall_score=0.8,
            security_issues=[],
            performance_issues=[],
            code_quality_issues=[],
            test_coverage=0.85,
            recommendations=["Jenkins analysis completed"],
            approval_status="approved",
            detailed_feedback="Jenkins pipeline completed successfully"
        ))
        
        result = await jenkins_integration.review_pull_request(sample_pull_request)
        
        assert isinstance(result, ReviewResult)
        assert result.overall_score == 0.8
        assert result.approval_status == "approved"
    
    @pytest.mark.asyncio
    async def test_generate_deployment_plan(self, jenkins_integration):
        """Test Jenkins deployment plan generation"""
        changes = [{"type": "feature", "files": ["src/main.py"]}]
        
        jenkins_integration._create_or_update_pipeline_job = AsyncMock()
        
        plan = await jenkins_integration.generate_deployment_plan(changes)
        
        assert isinstance(plan, DeploymentPlan)
        assert plan.environment == "production"
        assert len(plan.steps) > 0
    
    @pytest.mark.asyncio
    async def test_setup_quality_gates(self, jenkins_integration):
        """Test Jenkins quality gates setup"""
        project_config = {"language": "java", "build_tool": "maven"}
        
        jenkins_integration._create_or_update_pipeline_job = AsyncMock()
        
        quality_gates = await jenkins_integration.setup_quality_gates(project_config)
        
        assert isinstance(quality_gates, list)
        assert len(quality_gates) > 0
    
    @pytest.mark.asyncio
    async def test_monitor_deployment(self, jenkins_integration):
        """Test Jenkins deployment monitoring"""
        deployment_id = "test-job/123"
        
        # Mock Jenkins API response
        mock_session = AsyncMock()
        jenkins_integration.session = mock_session
        
        mock_session.get.return_value.__aenter__.return_value.json.return_value = {
            "result": "SUCCESS",
            "duration": 300000,  # 5 minutes in milliseconds
            "url": "http://jenkins.test/job/test-job/123/",
            "building": False
        }
        
        jenkins_integration._get_console_output = AsyncMock(return_value="Build completed successfully")
        
        result = await jenkins_integration.monitor_deployment(deployment_id)
        
        assert result["deployment_id"] == deployment_id
        assert result["status"] == "success"
        assert "duration" in result
        assert "console_output" in result
    
    @pytest.mark.asyncio
    async def test_pipeline_generation(self, jenkins_integration):
        """Test Jenkins pipeline script generation"""
        changes = [{"type": "feature", "files": ["src/main.py"]}]
        
        pipeline_script = jenkins_integration._generate_jenkins_pipeline(changes)
        
        assert isinstance(pipeline_script, str)
        assert "pipeline" in pipeline_script.lower()
        assert "stages" in pipeline_script.lower()
        assert "build" in pipeline_script.lower()
        assert "test" in pipeline_script.lower()


class TestGitLabCIIntegration:
    """Test GitLab CI integration functionality"""
    
    @pytest.mark.asyncio
    async def test_review_pull_request(self, gitlab_integration, sample_pull_request):
        """Test GitLab merge request review"""
        # Mock GitLab API
        mock_session = AsyncMock()
        gitlab_integration.session = mock_session
        
        result = await gitlab_integration.review_pull_request(sample_pull_request)
        
        assert isinstance(result, ReviewResult)
        assert result.overall_score >= 0.0
        assert result.overall_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_generate_deployment_plan(self, gitlab_integration):
        """Test GitLab CI deployment plan generation"""
        changes = [{"type": "feature", "files": ["src/main.py"]}]
        
        plan = await gitlab_integration.generate_deployment_plan(changes)
        
        assert isinstance(plan, DeploymentPlan)
        
        # Check if .gitlab-ci.yml was created
        gitlab_ci_path = Path(".gitlab-ci.yml")
        if gitlab_ci_path.exists():
            with open(gitlab_ci_path, 'r') as f:
                gitlab_ci_content = yaml.safe_load(f)
            
            assert "stages" in gitlab_ci_content
            assert "build" in gitlab_ci_content
            
            # Cleanup
            gitlab_ci_path.unlink()
    
    @pytest.mark.asyncio
    async def test_setup_quality_gates(self, gitlab_integration):
        """Test GitLab CI quality gates setup"""
        project_config = {"language": "javascript", "package_manager": "npm"}
        
        quality_gates = await gitlab_integration.setup_quality_gates(project_config)
        
        assert isinstance(quality_gates, list)
        assert len(quality_gates) > 0
    
    @pytest.mark.asyncio
    async def test_monitor_deployment(self, gitlab_integration):
        """Test GitLab deployment monitoring"""
        deployment_id = "project/123"
        
        # Mock GitLab API response
        mock_session = AsyncMock()
        gitlab_integration.session = mock_session
        
        mock_session.get.return_value.__aenter__.return_value.json.return_value = [
            {
                "id": 1,
                "status": "success",
                "environment": {"name": "production"},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T01:00:00Z"
            }
        ]
        
        result = await gitlab_integration.monitor_deployment(deployment_id)
        
        assert result["deployment_id"] == deployment_id
        assert result["status"] == "success"
        assert result["environment"] == "production"
    
    def test_gitlab_ci_config_generation(self, gitlab_integration):
        """Test GitLab CI configuration generation"""
        changes = [{"type": "feature", "files": ["src/main.py"]}]
        
        config = gitlab_integration._generate_gitlab_ci_config(changes)
        
        assert isinstance(config, dict)
        assert "stages" in config
        assert "build" in config
        assert "test" in config
        assert "security_scan" in config
        assert "deploy" in config


class TestCICDIntegrationManager:
    """Test CI/CD integration manager"""
    
    def test_add_integrations(self, cicd_manager):
        """Test adding different CI/CD integrations"""
        # Add GitHub integration
        cicd_manager.add_github_integration("github_token")
        assert "github" in cicd_manager.integrations
        
        # Add Jenkins integration
        cicd_manager.add_jenkins_integration("http://jenkins.test", "user", "token")
        assert "jenkins" in cicd_manager.integrations
        
        # Add GitLab integration
        cicd_manager.add_gitlab_integration("https://gitlab.test", "gitlab_token")
        assert "gitlab" in cicd_manager.integrations
    
    @pytest.mark.asyncio
    async def test_review_pull_request(self, cicd_manager, sample_pull_request):
        """Test pull request review through manager"""
        # Add GitHub integration
        cicd_manager.add_github_integration("github_token")
        
        # Mock the integration's review method
        cicd_manager.integrations["github"].review_pull_request = AsyncMock(return_value=ReviewResult(
            overall_score=0.8,
            security_issues=[],
            performance_issues=[],
            code_quality_issues=[],
            test_coverage=0.85,
            recommendations=[],
            approval_status="approved",
            detailed_feedback="Review completed"
        ))
        
        result = await cicd_manager.review_pull_request("github", sample_pull_request)
        
        assert isinstance(result, ReviewResult)
        assert result.overall_score == 0.8
    
    @pytest.mark.asyncio
    async def test_generate_deployment_plan(self, cicd_manager):
        """Test deployment plan generation through manager"""
        # Add GitHub integration
        cicd_manager.add_github_integration("github_token")
        
        changes = [{"type": "feature", "files": ["src/main.py"]}]
        
        # Mock the integration's deployment plan method
        cicd_manager.integrations["github"].generate_deployment_plan = AsyncMock(return_value=DeploymentPlan(
            environment="production",
            steps=[{"name": "deploy", "action": "deploy"}],
            rollback_plan=[{"name": "rollback", "action": "rollback"}],
            health_checks=[{"name": "health", "endpoint": "/health"}],
            estimated_duration=30,
            risk_assessment={"level": "low", "score": 0.2}
        ))
        
        result = await cicd_manager.generate_deployment_plan("github", changes)
        
        assert isinstance(result, DeploymentPlan)
        assert result.environment == "production"
    
    @pytest.mark.asyncio
    async def test_setup_quality_gates(self, cicd_manager):
        """Test quality gates setup through manager"""
        # Add GitHub integration
        cicd_manager.add_github_integration("github_token")
        
        project_config = {"language": "python"}
        
        # Mock the integration's quality gates method
        cicd_manager.integrations["github"].setup_quality_gates = AsyncMock(return_value=[
            QualityGate(
                name="Test Gate",
                conditions=[{"metric": "coverage", "operator": ">=", "value": 80}],
                threshold=0.8,
                blocking=True,
                description="Test quality gate"
            )
        ])
        
        result = await cicd_manager.setup_quality_gates("github", project_config)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], QualityGate)
    
    @pytest.mark.asyncio
    async def test_monitor_deployment(self, cicd_manager):
        """Test deployment monitoring through manager"""
        # Add GitHub integration
        cicd_manager.add_github_integration("github_token")
        
        deployment_id = "test/deployment"
        
        # Mock the integration's monitoring method
        cicd_manager.integrations["github"].monitor_deployment = AsyncMock(return_value={
            "deployment_id": deployment_id,
            "status": "success",
            "environment": "production"
        })
        
        result = await cicd_manager.monitor_deployment("github", deployment_id)
        
        assert result["deployment_id"] == deployment_id
        assert result["status"] == "success"
    
    def test_get_supported_platforms(self, cicd_manager):
        """Test getting supported platforms"""
        cicd_manager.add_github_integration("github_token")
        cicd_manager.add_jenkins_integration("http://jenkins.test", "user", "token")
        
        platforms = cicd_manager.get_supported_platforms()
        
        assert "github" in platforms
        assert "jenkins" in platforms
        assert len(platforms) == 2
    
    @pytest.mark.asyncio
    async def test_cleanup(self, cicd_manager):
        """Test cleanup of integrations"""
        # Add integrations with mock sessions
        cicd_manager.add_github_integration("github_token")
        cicd_manager.integrations["github"].session = AsyncMock()
        
        await cicd_manager.cleanup()
        
        # Verify session was closed
        cicd_manager.integrations["github"].session.close.assert_called_once()
        
        # Verify integrations were cleared
        assert len(cicd_manager.integrations) == 0


class TestCICDIntegrationErrorHandling:
    """Test error handling in CI/CD integrations"""
    
    @pytest.mark.asyncio
    async def test_invalid_platform_error(self, cicd_manager, sample_pull_request):
        """Test error handling for invalid platform"""
        with pytest.raises(ValueError, match="Platform not configured"):
            await cicd_manager.review_pull_request("invalid_platform", sample_pull_request)
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, github_integration, sample_pull_request):
        """Test network error handling"""
        # Mock network error
        github_integration._get_session = AsyncMock(side_effect=Exception("Network error"))
        
        with pytest.raises(Exception):
            await github_integration.review_pull_request(sample_pull_request)
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, github_integration):
        """Test API error handling"""
        # Mock API error response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        github_integration.session = mock_session
        
        deployment_id = "test/repo"
        result = await github_integration.monitor_deployment(deployment_id)
        
        # Should handle error gracefully
        assert "status" in result


class TestCICDIntegrationPerformance:
    """Test performance aspects of CI/CD integrations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_reviews(self, github_integration):
        """Test handling concurrent pull request reviews"""
        # Create multiple PRs
        prs = []
        for i in range(5):
            pr = PullRequest(
                id=str(i),
                title=f"PR {i}",
                description=f"Test PR {i}",
                author="developer",
                source_branch=f"feature/{i}",
                target_branch="main",
                files_changed=[f"src/file{i}.py"],
                additions=10,
                deletions=2,
                url=f"https://github.com/repo/pull/{i}",
                created_at=datetime.now()
            )
            prs.append(pr)
        
        # Mock dependencies
        github_integration._get_pr_files = AsyncMock(return_value=[])
        github_integration._calculate_test_coverage = AsyncMock(return_value=0.8)
        github_integration._post_review_to_github = AsyncMock()
        
        # Process PRs concurrently
        tasks = [github_integration.review_pull_request(pr) for pr in prs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All reviews should complete
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, ReviewResult)
    
    @pytest.mark.asyncio
    async def test_large_deployment_plan(self, github_integration):
        """Test deployment plan for large changes"""
        # Create large change set
        changes = []
        for i in range(100):
            changes.append({
                "type": "feature" if i % 2 == 0 else "bugfix",
                "files": [f"src/module{i}.py"],
                "size": 50
            })
        
        start_time = asyncio.get_event_loop().time()
        plan = await github_integration.generate_deployment_plan(changes)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 2.0  # 2 seconds max
        assert isinstance(plan, DeploymentPlan)


if __name__ == "__main__":
    pytest.main([__file__])