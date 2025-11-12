"""
Comprehensive integration test framework for all integration components.

Tests the complete integration system including IDE, CI/CD, team collaboration,
and API systems working together.
"""

import pytest
import asyncio
import json
import tempfile
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from pathlib import Path

from src.codegenie.integrations.ide_integration import IDEIntegrationManager
from src.codegenie.integrations.cicd_integration import CICDIntegrationManager
from src.codegenie.integrations.team_collaboration import TeamCollaborationManager
from src.codegenie.integrations.api_system import APISystem
from src.codegenie.core.code_intelligence import CodeIntelligence
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.core.knowledge_graph import CodeKnowledgeGraph
from src.codegenie.agents.coordinator import AgentCoordinator
from src.codegenie.agents.security import SecurityAgent
from src.codegenie.agents.testing import TesterAgent
from src.codegenie.agents.performance import PerformanceAgent


@pytest.fixture
def mock_dependencies():
    """Create all mock dependencies for integration testing"""
    return {
        'code_intelligence': AsyncMock(spec=CodeIntelligence),
        'context_engine': AsyncMock(spec=ContextEngine),
        'knowledge_graph': AsyncMock(spec=CodeKnowledgeGraph),
        'agent_coordinator': AsyncMock(spec=AgentCoordinator),
        'security_agent': AsyncMock(spec=SecurityAgent),
        'tester_agent': AsyncMock(spec=TesterAgent),
        'performance_agent': AsyncMock(spec=PerformanceAgent),
        'redis': AsyncMock()
    }


@pytest.fixture
def integration_system(mock_dependencies):
    """Create complete integration system for testing"""
    deps = mock_dependencies
    
    # Setup mock Redis
    deps['redis'].ping.return_value = True
    mock_pipeline = AsyncMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    deps['redis'].pipeline.return_value = mock_pipeline
    
    # Create integration managers
    ide_manager = IDEIntegrationManager(deps['code_intelligence'], deps['context_engine'])
    
    cicd_manager = CICDIntegrationManager(
        deps['code_intelligence'], deps['security_agent'],
        deps['tester_agent'], deps['performance_agent']
    )
    
    team_manager = TeamCollaborationManager(deps['context_engine'], deps['knowledge_graph'])
    
    with patch('redis.asyncio.from_url', return_value=deps['redis']):
        api_system = APISystem(
            deps['code_intelligence'], deps['context_engine'],
            deps['agent_coordinator'], "test_secret", "redis://localhost"
        )
    
    return {
        'ide': ide_manager,
        'cicd': cicd_manager,
        'team': team_manager,
        'api': api_system,
        'deps': deps
    }


class TestIntegrationSystemStartup:
    """Test integration system startup and initialization"""
    
    @pytest.mark.asyncio
    async def test_complete_system_startup(self, integration_system):
        """Test starting up the complete integration system"""
        ide_manager = integration_system['ide']
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Mock startup methods
        with patch.object(ide_manager.vscode_extension, 'start_websocket_server') as mock_vscode:
            with patch.object(ide_manager.intellij_plugin, 'start_http_server') as mock_intellij:
                with patch.object(team_manager, 'initialize_integrations') as mock_team_init:
                    with patch.object(api_system, 'start_server') as mock_api_start:
                        
                        # Start all systems
                        await ide_manager.start_all_integrations()
                        await team_manager.initialize_integrations()
                        await api_system.start_server()
                        
                        # Verify all systems started
                        mock_vscode.assert_called_once()
                        mock_intellij.assert_called_once()
                        mock_team_init.assert_called_once()
                        mock_api_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_system_health_checks(self, integration_system):
        """Test health checks across all integration systems"""
        api_system = integration_system['api']
        
        # Mock health check request
        request = Mock()
        response = await api_system._health_check(request)
        
        assert response.status == 200
        
        # Verify Redis health check
        integration_system['deps']['redis'].ping.assert_called()
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, integration_system):
        """Test graceful shutdown of all integration systems"""
        ide_manager = integration_system['ide']
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Mock shutdown methods
        with patch.object(ide_manager, 'stop_all_integrations') as mock_ide_stop:
            with patch.object(team_manager, 'cleanup') as mock_team_cleanup:
                with patch.object(api_system, 'stop_server') as mock_api_stop:
                    
                    # Stop all systems
                    await ide_manager.stop_all_integrations()
                    await team_manager.cleanup()
                    await api_system.stop_server()
                    
                    # Verify all systems stopped
                    mock_ide_stop.assert_called_once()
                    mock_team_cleanup.assert_called_once()
                    mock_api_stop.assert_called_once()


class TestCrossSystemIntegration:
    """Test integration between different systems"""
    
    @pytest.mark.asyncio
    async def test_ide_to_api_workflow(self, integration_system):
        """Test workflow from IDE to API system"""
        ide_manager = integration_system['ide']
        api_system = integration_system['api']
        
        # Simulate IDE code analysis request
        code = "def hello(): return 'world'"
        
        # Mock IDE integration
        ide_manager.active_integrations["vscode"] = ide_manager.vscode_extension
        
        # Mock API system code analysis
        api_system.code_intelligence.analyze_code_semantics.return_value = Mock(
            issues=[], suggestions=[], complexity_score=0.5
        )
        
        # Process through IDE
        ide_context = Mock(
            file_path="/test.py", cursor_position=0, selected_text=None,
            project_root="/", language="python", workspace_files=["/test.py"]
        )
        
        suggestions = await ide_manager.vscode_extension.provide_code_suggestions(ide_context)
        
        # Process through API
        request = Mock()
        request.json = AsyncMock(return_value={"code": code, "language": "python"})
        
        response = await api_system._analyze_code(request)
        
        # Both should work
        assert isinstance(suggestions, list)
        assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_cicd_to_team_notification_workflow(self, integration_system):
        """Test workflow from CI/CD to team notification"""
        cicd_manager = integration_system['cicd']
        team_manager = integration_system['team']
        
        # Add GitHub integration
        cicd_manager.add_github_integration("test_token")
        
        # Add Slack integration
        team_manager.add_slack_integration("slack_token", "slack_secret")
        
        # Mock PR review
        pr = Mock(
            id="123", title="Test PR", description="Test", author="dev",
            source_branch="feature", target_branch="main", files_changed=["test.py"],
            additions=10, deletions=2, url="https://github.com/test/pr/123",
            created_at=datetime.now()
        )
        
        # Mock review result
        cicd_manager.integrations["github"].review_pull_request = AsyncMock(return_value=Mock(
            overall_score=0.8, security_issues=[], performance_issues=[],
            code_quality_issues=[], test_coverage=0.85, recommendations=[],
            approval_status="approved", detailed_feedback="Looks good!"
        ))
        
        # Mock team notification
        team_manager.slack_integration.send_notification = AsyncMock(return_value=True)
        
        # Execute workflow
        review_result = await cicd_manager.review_pull_request("github", pr)
        
        notification_sent = await team_manager.notify_team(
            "slack", "#dev", f"PR {pr.id} review completed: {review_result.approval_status}"
        )
        
        assert review_result.approval_status == "approved"
        assert notification_sent is True
    
    @pytest.mark.asyncio
    async def test_api_to_webhook_workflow(self, integration_system):
        """Test workflow from API to webhook system"""
        api_system = integration_system['api']
        
        # Register webhook
        webhook_data = {
            "url": "https://example.com/webhook",
            "events": ["code_analysis"],
            "secret": "test_secret"
        }
        
        request = Mock()
        request.json = AsyncMock(return_value=webhook_data)
        
        # Create webhook
        response = await api_system._create_webhook(request)
        assert response.status == 200
        
        # Trigger webhook event
        await api_system.trigger_webhook_event("code_analysis", {"result": "success"})
        
        # Verify event was queued
        assert not api_system.webhook_manager.event_queue.empty()
    
    @pytest.mark.asyncio
    async def test_knowledge_sharing_workflow(self, integration_system):
        """Test knowledge sharing across team collaboration and API"""
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Add knowledge item through team manager
        knowledge_item = Mock(
            id="kb001", title="Python Best Practices", content="Best practices...",
            category="development", tags=["python"], author="dev@example.com",
            created_at=datetime.now(), updated_at=datetime.now(),
            access_level="team", related_items=[]
        )
        
        # Mock knowledge base operations
        team_manager.knowledge_base.add_knowledge_item = AsyncMock(return_value=True)
        team_manager.knowledge_base.search_knowledge = AsyncMock(return_value=[knowledge_item])
        
        # Add knowledge
        result = await team_manager.add_team_knowledge(knowledge_item)
        assert result is True
        
        # Search through API context engine
        api_system.context_engine.retrieve_relevant_context.return_value = Mock(
            relevant_knowledge=[knowledge_item]
        )
        
        request = Mock()
        request.json = AsyncMock(return_value={"query": "Python best practices"})
        
        response = await api_system._search_context(request)
        assert response.status == 200


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows across all systems"""
    
    @pytest.mark.asyncio
    async def test_complete_development_workflow(self, integration_system):
        """Test complete development workflow from IDE to deployment"""
        ide_manager = integration_system['ide']
        cicd_manager = integration_system['cicd']
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Step 1: Developer writes code in IDE
        code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
        """
        
        # Mock IDE analysis
        ide_manager.active_integrations["vscode"] = ide_manager.vscode_extension
        ide_context = Mock(
            file_path="/fibonacci.py", cursor_position=100, selected_text=None,
            project_root="/project", language="python", workspace_files=["/fibonacci.py"]
        )
        
        suggestions = await ide_manager.vscode_extension.provide_code_suggestions(ide_context)
        
        # Step 2: Code is committed and triggers CI/CD
        cicd_manager.add_github_integration("github_token")
        
        pr = Mock(
            id="456", title="Add Fibonacci function", description="Implements Fibonacci calculation",
            author="developer", source_branch="feature/fibonacci", target_branch="main",
            files_changed=["fibonacci.py"], additions=6, deletions=0,
            url="https://github.com/project/pull/456", created_at=datetime.now()
        )
        
        # Mock CI/CD review
        cicd_manager.integrations["github"].review_pull_request = AsyncMock(return_value=Mock(
            overall_score=0.7, security_issues=[], performance_issues=[
                {"file": "fibonacci.py", "line": 4, "type": "inefficient_recursion",
                 "description": "Exponential time complexity", "optimization": "Use memoization"}
            ],
            code_quality_issues=[], test_coverage=0.8, recommendations=["Add memoization"],
            approval_status="needs_changes", detailed_feedback="Performance can be improved"
        ))
        
        review_result = await cicd_manager.review_pull_request("github", pr)
        
        # Step 3: Team is notified about review
        team_manager.add_slack_integration("slack_token", "slack_secret")
        team_manager.slack_integration.send_notification = AsyncMock(return_value=True)
        
        notification_sent = await team_manager.notify_team(
            "slack", "#dev", 
            f"PR {pr.id} needs changes: {review_result.detailed_feedback}"
        )
        
        # Step 4: Knowledge is shared about optimization
        knowledge_item = Mock(
            id="kb_fib", title="Fibonacci Optimization", 
            content="Use memoization to optimize recursive Fibonacci...",
            category="performance", tags=["fibonacci", "optimization", "memoization"],
            author="senior_dev@example.com", created_at=datetime.now(),
            updated_at=datetime.now(), access_level="team", related_items=[]
        )
        
        team_manager.knowledge_base.add_knowledge_item = AsyncMock(return_value=True)
        await team_manager.add_team_knowledge(knowledge_item)
        
        # Step 5: API tracks all activities
        api_request = Mock(
            request_id="req_456", api_key_id="key123", endpoint="/api/v1/code/review",
            method="POST", timestamp=datetime.now(), response_time=0.5,
            status_code=200, user_agent="CI/CD-Bot", ip_address="10.0.0.1"
        )
        
        await api_system.usage_analytics.record_api_request(api_request)
        
        # Verify workflow completion
        assert isinstance(suggestions, list)
        assert review_result.approval_status == "needs_changes"
        assert notification_sent is True
        
        # Verify analytics
        api_system.usage_analytics.redis.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_collaborative_code_review_workflow(self, integration_system):
        """Test collaborative code review workflow"""
        ide_manager = integration_system['ide']
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Step 1: Developer shares code snippet for review
        code_snippet = """
def process_user_data(users):
    result = []
    for user in users:
        if user.is_active:
            result.append(user.name.upper())
    return result
        """
        
        team_manager.add_slack_integration("slack_token", "slack_secret")
        team_manager.slack_integration.share_code_snippet = AsyncMock(return_value=True)
        
        shared = await team_manager.share_code_with_team(
            "slack", "#code-review", code_snippet, "python", "User data processing function"
        )
        
        # Step 2: Team creates discussion thread
        team_manager.slack_integration.create_thread = AsyncMock(return_value="thread_123")
        
        thread_id = await team_manager.create_team_discussion(
            "slack", "#code-review", "Code Review Discussion",
            "Please review the user data processing function"
        )
        
        # Step 3: IDE provides real-time collaboration
        ide_manager.active_integrations["vscode"] = ide_manager.vscode_extension
        
        collaboration_event = {
            "type": "cursor_move",
            "user": "reviewer1",
            "position": {"line": 5, "character": 20},
            "file": "/user_processor.py"
        }
        
        await ide_manager.vscode_extension.handle_real_time_collaboration(
            "review_session_123", collaboration_event
        )
        
        # Step 4: API logs all review activities
        review_activities = [
            {"action": "code_shared", "user": "developer", "timestamp": datetime.now()},
            {"action": "thread_created", "user": "developer", "timestamp": datetime.now()},
            {"action": "review_started", "user": "reviewer1", "timestamp": datetime.now()}
        ]
        
        for activity in review_activities:
            await api_system.trigger_webhook_event("review_activity", activity)
        
        # Verify workflow
        assert shared is True
        assert thread_id == "thread_123"
        assert api_system.webhook_manager.event_queue.qsize() == len(review_activities)
    
    @pytest.mark.asyncio
    async def test_automated_deployment_workflow(self, integration_system):
        """Test automated deployment workflow"""
        cicd_manager = integration_system['cicd']
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Step 1: Generate deployment plan
        cicd_manager.add_github_integration("github_token")
        
        changes = [
            {"type": "feature", "files": ["app.py", "utils.py"], "size": 150},
            {"type": "bugfix", "files": ["auth.py"], "size": 25}
        ]
        
        cicd_manager.integrations["github"].generate_deployment_plan = AsyncMock(return_value=Mock(
            environment="production", 
            steps=[
                {"name": "Build", "action": "build", "timeout": "10m"},
                {"name": "Test", "action": "test", "timeout": "15m"},
                {"name": "Deploy", "action": "deploy", "timeout": "20m"}
            ],
            rollback_plan=[{"name": "Rollback", "action": "rollback", "timeout": "10m"}],
            health_checks=[{"name": "Health Check", "endpoint": "/health", "timeout": "5m"}],
            estimated_duration=45,
            risk_assessment={"level": "medium", "score": 0.4, "factors": ["Large changes"]}
        ))
        
        deployment_plan = await cicd_manager.generate_deployment_plan("github", changes)
        
        # Step 2: Schedule team meeting for deployment review
        team_manager.add_slack_integration("slack_token", "slack_secret")
        team_manager.slack_integration.schedule_meeting = AsyncMock(return_value={
            "status": "scheduled", "meeting_id": "meeting_deploy_123",
            "topic": "Deployment Review", "participants": ["dev1", "dev2", "ops1"]
        })
        
        meeting_result = await team_manager.schedule_team_meeting(
            "slack", ["dev1", "dev2", "ops1"], "Deployment Review", 30
        )
        
        # Step 3: Monitor deployment through API
        cicd_manager.integrations["github"].monitor_deployment = AsyncMock(return_value={
            "deployment_id": "deploy_123", "status": "success",
            "environment": "production", "duration": 1800,
            "health": {"status": "healthy", "checks": [{"name": "API", "status": "passing"}]}
        })
        
        deployment_status = await cicd_manager.monitor_deployment("github", "deploy_123")
        
        # Step 4: Update team analytics
        team_analytics = await team_manager.get_team_analytics("team_123", 7)
        
        # Step 5: Log deployment metrics via API
        deployment_metrics = {
            "deployment_id": "deploy_123",
            "duration": 1800,
            "success": True,
            "changes_deployed": len(changes),
            "rollback_required": False
        }
        
        await api_system.trigger_webhook_event("deployment_completed", deployment_metrics)
        
        # Verify workflow
        assert deployment_plan.environment == "production"
        assert meeting_result["status"] == "scheduled"
        assert deployment_status["status"] == "success"
        assert isinstance(team_analytics, Mock)  # Mock analytics object


class TestIntegrationSystemResilience:
    """Test system resilience and error handling"""
    
    @pytest.mark.asyncio
    async def test_partial_system_failure_handling(self, integration_system):
        """Test handling when some systems fail"""
        ide_manager = integration_system['ide']
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Simulate IDE system failure
        with patch.object(ide_manager.vscode_extension, 'start_websocket_server', 
                         side_effect=Exception("WebSocket server failed")):
            
            # Other systems should still work
            team_manager.add_slack_integration("slack_token", "slack_secret")
            team_manager.slack_integration.send_notification = AsyncMock(return_value=True)
            
            # Team notification should still work
            result = await team_manager.notify_team("slack", "#general", "Test message")
            assert result is True
            
            # API should still work
            request = Mock()
            response = await api_system._health_check(request)
            assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, integration_system):
        """Test recovery from network failures"""
        team_manager = integration_system['team']
        
        # Simulate network failure then recovery
        team_manager.add_slack_integration("slack_token", "slack_secret")
        
        # First attempt fails
        team_manager.slack_integration.send_notification = AsyncMock(side_effect=Exception("Network error"))
        
        result1 = await team_manager.notify_team("slack", "#general", "Test message")
        assert result1 is False
        
        # Second attempt succeeds (network recovered)
        team_manager.slack_integration.send_notification = AsyncMock(return_value=True)
        
        result2 = await team_manager.notify_team("slack", "#general", "Test message")
        assert result2 is True
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_systems(self, integration_system):
        """Test data consistency across different systems"""
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Add knowledge item through team manager
        knowledge_item = Mock(
            id="kb_consistency", title="Consistency Test",
            content="Test content", category="test", tags=["test"],
            author="test@example.com", created_at=datetime.now(),
            updated_at=datetime.now(), access_level="team", related_items=[]
        )
        
        team_manager.knowledge_base.add_knowledge_item = AsyncMock(return_value=True)
        team_manager.knowledge_base.get_knowledge_item = AsyncMock(return_value=knowledge_item)
        
        # Add through team manager
        result1 = await team_manager.add_team_knowledge(knowledge_item)
        
        # Retrieve through team manager
        retrieved_item = await team_manager.knowledge_base.get_knowledge_item("kb_consistency")
        
        # Should be consistent
        assert result1 is True
        assert retrieved_item.id == knowledge_item.id
        assert retrieved_item.title == knowledge_item.title


class TestIntegrationSystemPerformance:
    """Test performance of integrated systems"""
    
    @pytest.mark.asyncio
    async def test_concurrent_cross_system_operations(self, integration_system):
        """Test concurrent operations across multiple systems"""
        ide_manager = integration_system['ide']
        team_manager = integration_system['team']
        api_system = integration_system['api']
        
        # Setup systems
        ide_manager.active_integrations["vscode"] = ide_manager.vscode_extension
        team_manager.add_slack_integration("slack_token", "slack_secret")
        team_manager.slack_integration.send_notification = AsyncMock(return_value=True)
        
        # Create concurrent tasks across systems
        tasks = []
        
        # IDE tasks
        for i in range(5):
            ide_context = Mock(
                file_path=f"/test{i}.py", cursor_position=i*10, selected_text=None,
                project_root="/", language="python", workspace_files=[f"/test{i}.py"]
            )
            task = ide_manager.vscode_extension.provide_code_suggestions(ide_context)
            tasks.append(task)
        
        # Team collaboration tasks
        for i in range(5):
            task = team_manager.notify_team("slack", "#general", f"Message {i}")
            tasks.append(task)
        
        # API tasks
        for i in range(5):
            request = Mock()
            request.json = AsyncMock(return_value={"code": f"def func{i}(): pass", "language": "python"})
            task = api_system._analyze_code(request)
            tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds max
        
        # All tasks should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_system_resource_usage(self, integration_system):
        """Test resource usage across integrated systems"""
        api_system = integration_system['api']
        
        # Simulate high load
        tasks = []
        for i in range(50):
            request = Mock()
            request.json = AsyncMock(return_value={"code": f"# Code {i}", "language": "python"})
            task = api_system._analyze_code(request)
            tasks.append(task)
        
        # Monitor resource usage (simplified)
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()
        
        # Should handle load efficiently
        assert end_time - start_time < 10.0  # 10 seconds max for 50 requests
        
        # All requests should succeed
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_requests == 50


if __name__ == "__main__":
    pytest.main([__file__])