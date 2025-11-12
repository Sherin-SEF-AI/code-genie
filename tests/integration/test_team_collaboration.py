"""
Integration tests for team collaboration functionality.

Tests Slack integration, Teams integration, shared knowledge base,
collaborative planning, and team analytics.
"""

import pytest
import asyncio
import json
import sqlite3
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from src.codegenie.integrations.team_collaboration import (
    TeamCollaborationManager, SlackIntegration, TeamsIntegration,
    SharedKnowledgeBase, CollaborativePlanningSystem, TeamAnalyticsDashboard,
    TeamMember, KnowledgeItem, CollaborativePlan, TeamAnalytics
)
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.core.knowledge_graph import CodeKnowledgeGraph


@pytest.fixture
def mock_context_engine():
    """Mock context engine for testing"""
    mock = AsyncMock(spec=ContextEngine)
    
    mock.retrieve_relevant_context.return_value = Mock(
        conversation_history=[],
        project_state=Mock(),
        user_goals=[],
        recent_changes=[],
        relevant_knowledge=[]
    )
    
    return mock


@pytest.fixture
def mock_knowledge_graph():
    """Mock knowledge graph for testing"""
    mock = AsyncMock(spec=CodeKnowledgeGraph)
    return mock


@pytest.fixture
def sample_team_member():
    """Sample team member for testing"""
    return TeamMember(
        id="user123",
        name="John Doe",
        email="john@example.com",
        role="developer",
        skills=["python", "javascript", "react"],
        timezone="UTC",
        availability={"monday": "9-17", "tuesday": "9-17"},
        preferences={"notification_style": "immediate"}
    )


@pytest.fixture
def sample_knowledge_item():
    """Sample knowledge item for testing"""
    return KnowledgeItem(
        id="kb001",
        title="Python Best Practices",
        content="Here are some Python best practices...",
        category="development",
        tags=["python", "best-practices", "coding"],
        author="john@example.com",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        access_level="team",
        related_items=["kb002", "kb003"]
    )


@pytest.fixture
def sample_collaborative_plan():
    """Sample collaborative plan for testing"""
    return CollaborativePlan(
        id="plan001",
        title="Implement user authentication",
        description="Add OAuth2 authentication to the application",
        type="feature",
        status="in_progress",
        priority="high",
        assignee="john@example.com",
        reviewers=["jane@example.com", "bob@example.com"],
        estimated_effort=40,
        actual_effort=None,
        dependencies=["plan002"],
        created_at=datetime.now(),
        due_date=datetime.now() + timedelta(days=14),
        tags=["authentication", "security", "oauth2"]
    )


@pytest.fixture
def slack_integration(mock_context_engine, mock_knowledge_graph):
    """Create Slack integration for testing"""
    return SlackIntegration(
        mock_context_engine, mock_knowledge_graph,
        slack_token="test_token", slack_signing_secret="test_secret"
    )


@pytest.fixture
def teams_integration(mock_context_engine, mock_knowledge_graph):
    """Create Teams integration for testing"""
    return TeamsIntegration(
        mock_context_engine, mock_knowledge_graph,
        teams_app_id="test_app_id", teams_app_password="test_password"
    )


@pytest.fixture
def knowledge_base():
    """Create shared knowledge base for testing"""
    # Use in-memory database for testing
    return SharedKnowledgeBase(":memory:")


@pytest.fixture
def planning_system():
    """Create collaborative planning system for testing"""
    # Use in-memory database for testing
    return CollaborativePlanningSystem(":memory:")


@pytest.fixture
def analytics_dashboard(mock_context_engine):
    """Create team analytics dashboard for testing"""
    return TeamAnalyticsDashboard(mock_context_engine)


@pytest.fixture
def team_collaboration_manager(mock_context_engine, mock_knowledge_graph):
    """Create team collaboration manager for testing"""
    return TeamCollaborationManager(mock_context_engine, mock_knowledge_graph)


class TestSlackIntegration:
    """Test Slack integration functionality"""
    
    @pytest.mark.asyncio
    async def test_initialize(self, slack_integration):
        """Test Slack integration initialization"""
        # Mock HTTP session and auth response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "ok": True,
            "user_id": "U123456",
            "user": "codegenie_bot"
        }
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch.object(slack_integration, '_get_session', return_value=mock_session):
            await slack_integration.initialize()
            
            assert slack_integration.bot_user_id == "U123456"
    
    @pytest.mark.asyncio
    async def test_send_notification(self, slack_integration):
        """Test sending Slack notifications"""
        # Mock HTTP session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"ok": True, "message": {"ts": "1234567890.123456"}}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(slack_integration, '_get_session', return_value=mock_session):
            result = await slack_integration.send_notification(
                "#general", "Test message", None
            )
            
            assert result is True
            mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_thread(self, slack_integration):
        """Test creating Slack discussion thread"""
        # Mock HTTP session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "ok": True,
            "message": {"ts": "1234567890.123456"}
        }
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(slack_integration, '_get_session', return_value=mock_session):
            thread_id = await slack_integration.create_thread(
                "#general", "Code Review", "Please review this PR"
            )
            
            assert thread_id == "1234567890.123456"
    
    @pytest.mark.asyncio
    async def test_share_code_snippet(self, slack_integration):
        """Test sharing code snippet in Slack"""
        # Mock HTTP session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"ok": True}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(slack_integration, '_get_session', return_value=mock_session):
            result = await slack_integration.share_code_snippet(
                "#general", "def hello(): return 'world'", "python", "Example function"
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_schedule_meeting(self, slack_integration):
        """Test scheduling meeting through Slack"""
        with patch.object(slack_integration, 'send_notification', return_value=True):
            result = await slack_integration.schedule_meeting(
                ["U123456", "U789012"], "Sprint Planning", 60
            )
            
            assert result["status"] == "scheduled"
            assert result["topic"] == "Sprint Planning"
            assert result["duration"] == 60
    
    @pytest.mark.asyncio
    async def test_handle_slash_command(self, slack_integration):
        """Test handling Slack slash commands"""
        # Test /codegenie command
        result = await slack_integration.handle_slash_command(
            "/codegenie", "help me with this code", "U123456", "C123456"
        )
        
        assert result["response_type"] == "in_channel"
        assert "CodeGenie is processing" in result["text"]
        
        # Test /code-review command
        result = await slack_integration.handle_slash_command(
            "/code-review", "https://github.com/repo/pull/123", "U123456", "C123456"
        )
        
        assert result["response_type"] == "in_channel"
        assert "Starting code review" in result["text"]
        
        # Test /knowledge command
        result = await slack_integration.handle_slash_command(
            "/knowledge", "search python best practices", "U123456", "C123456"
        )
        
        assert result["response_type"] == "ephemeral"
        assert "Searching knowledge base" in result["text"]


class TestTeamsIntegration:
    """Test Microsoft Teams integration functionality"""
    
    @pytest.mark.asyncio
    async def test_send_notification(self, teams_integration):
        """Test sending Teams notifications"""
        # Mock HTTP session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(teams_integration, '_get_session', return_value=mock_session):
            result = await teams_integration.send_notification(
                "team123", "Test message", None
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_create_thread(self, teams_integration):
        """Test creating Teams discussion thread"""
        # Mock HTTP session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {"id": "message123"}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(teams_integration, '_get_session', return_value=mock_session):
            thread_id = await teams_integration.create_thread(
                "team123", "Code Review", "Please review this PR"
            )
            
            assert thread_id == "message123"
    
    @pytest.mark.asyncio
    async def test_share_code_snippet(self, teams_integration):
        """Test sharing code snippet in Teams"""
        with patch.object(teams_integration, 'send_notification', return_value=True):
            result = await teams_integration.share_code_snippet(
                "team123", "def hello(): return 'world'", "python", "Example function"
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_schedule_meeting(self, teams_integration):
        """Test scheduling meeting in Teams"""
        # Mock HTTP session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {
            "id": "meeting123",
            "onlineMeeting": {"joinUrl": "https://teams.microsoft.com/l/meetup-join/..."}
        }
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(teams_integration, '_get_session', return_value=mock_session):
            result = await teams_integration.schedule_meeting(
                ["user1@example.com", "user2@example.com"], "Sprint Planning", 60
            )
            
            assert result["status"] == "scheduled"
            assert result["meeting_id"] == "meeting123"
            assert "join_url" in result


class TestSharedKnowledgeBase:
    """Test shared knowledge base functionality"""
    
    @pytest.mark.asyncio
    async def test_add_knowledge_item(self, knowledge_base, sample_knowledge_item):
        """Test adding knowledge item"""
        result = await knowledge_base.add_knowledge_item(sample_knowledge_item)
        
        assert result is True
        
        # Verify item was added
        retrieved_item = await knowledge_base.get_knowledge_item(sample_knowledge_item.id)
        assert retrieved_item is not None
        assert retrieved_item.title == sample_knowledge_item.title
    
    @pytest.mark.asyncio
    async def test_search_knowledge(self, knowledge_base, sample_knowledge_item):
        """Test searching knowledge base"""
        # Add item first
        await knowledge_base.add_knowledge_item(sample_knowledge_item)
        
        # Search for it
        results = await knowledge_base.search_knowledge("Python best practices")
        
        assert len(results) > 0
        assert results[0].title == sample_knowledge_item.title
    
    @pytest.mark.asyncio
    async def test_update_knowledge_item(self, knowledge_base, sample_knowledge_item):
        """Test updating knowledge item"""
        # Add item first
        await knowledge_base.add_knowledge_item(sample_knowledge_item)
        
        # Update item
        sample_knowledge_item.content = "Updated content"
        result = await knowledge_base.update_knowledge_item(sample_knowledge_item)
        
        assert result is True
        
        # Verify update
        retrieved_item = await knowledge_base.get_knowledge_item(sample_knowledge_item.id)
        assert retrieved_item.content == "Updated content"
    
    @pytest.mark.asyncio
    async def test_delete_knowledge_item(self, knowledge_base, sample_knowledge_item):
        """Test deleting knowledge item"""
        # Add item first
        await knowledge_base.add_knowledge_item(sample_knowledge_item)
        
        # Delete item
        result = await knowledge_base.delete_knowledge_item(sample_knowledge_item.id)
        
        assert result is True
        
        # Verify deletion
        retrieved_item = await knowledge_base.get_knowledge_item(sample_knowledge_item.id)
        assert retrieved_item is None
    
    @pytest.mark.asyncio
    async def test_get_categories(self, knowledge_base):
        """Test getting knowledge categories"""
        # Add items with different categories
        item1 = KnowledgeItem(
            id="kb001", title="Test 1", content="Content 1", category="development",
            tags=[], author="test", created_at=datetime.now(), updated_at=datetime.now(),
            access_level="team", related_items=[]
        )
        item2 = KnowledgeItem(
            id="kb002", title="Test 2", content="Content 2", category="design",
            tags=[], author="test", created_at=datetime.now(), updated_at=datetime.now(),
            access_level="team", related_items=[]
        )
        
        await knowledge_base.add_knowledge_item(item1)
        await knowledge_base.add_knowledge_item(item2)
        
        categories = await knowledge_base.get_categories()
        
        assert "development" in categories
        assert "design" in categories


class TestCollaborativePlanningSystem:
    """Test collaborative planning system functionality"""
    
    @pytest.mark.asyncio
    async def test_create_plan(self, planning_system, sample_collaborative_plan):
        """Test creating collaborative plan"""
        result = await planning_system.create_plan(sample_collaborative_plan)
        
        assert result is True
        
        # Verify plan was created
        plans = await planning_system.get_plans()
        assert len(plans) > 0
        assert plans[0].title == sample_collaborative_plan.title
    
    @pytest.mark.asyncio
    async def test_get_plans_with_filters(self, planning_system, sample_collaborative_plan):
        """Test getting plans with filters"""
        # Create plan
        await planning_system.create_plan(sample_collaborative_plan)
        
        # Get plans by status
        plans = await planning_system.get_plans(status="in_progress")
        assert len(plans) > 0
        assert plans[0].status == "in_progress"
        
        # Get plans by assignee
        plans = await planning_system.get_plans(assignee="john@example.com")
        assert len(plans) > 0
        assert plans[0].assignee == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_update_plan_status(self, planning_system, sample_collaborative_plan):
        """Test updating plan status"""
        # Create plan
        await planning_system.create_plan(sample_collaborative_plan)
        
        # Update status
        result = await planning_system.update_plan_status(sample_collaborative_plan.id, "completed")
        
        assert result is True
        
        # Verify update
        plans = await planning_system.get_plans(status="completed")
        assert len(plans) > 0
        assert plans[0].status == "completed"
    
    @pytest.mark.asyncio
    async def test_assign_reviewers(self, planning_system, sample_collaborative_plan):
        """Test assigning reviewers to plan"""
        # Create plan
        await planning_system.create_plan(sample_collaborative_plan)
        
        # Assign new reviewers
        new_reviewers = ["alice@example.com", "charlie@example.com"]
        result = await planning_system.assign_reviewers(sample_collaborative_plan.id, new_reviewers)
        
        assert result is True
        
        # Verify assignment
        plans = await planning_system.get_plans()
        assert len(plans) > 0
        assert plans[0].reviewers == new_reviewers


class TestTeamAnalyticsDashboard:
    """Test team analytics dashboard functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_team_analytics(self, analytics_dashboard):
        """Test generating team analytics"""
        team_id = "team123"
        
        analytics = await analytics_dashboard.generate_team_analytics(team_id, 30)
        
        assert isinstance(analytics, TeamAnalytics)
        assert analytics.team_id == team_id
        assert analytics.velocity > 0
        assert 0 <= analytics.productivity_score <= 1
        assert 0 <= analytics.collaboration_score <= 1
        assert isinstance(analytics.code_quality_trend, list)
        assert isinstance(analytics.member_contributions, dict)
        assert isinstance(analytics.bottlenecks, list)
        assert isinstance(analytics.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_calculate_velocity(self, analytics_dashboard):
        """Test velocity calculation"""
        team_id = "team123"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        velocity = await analytics_dashboard._calculate_velocity(team_id, start_date, end_date)
        
        assert isinstance(velocity, float)
        assert velocity > 0
    
    @pytest.mark.asyncio
    async def test_identify_bottlenecks(self, analytics_dashboard):
        """Test bottleneck identification"""
        team_id = "team123"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        bottlenecks = await analytics_dashboard._identify_bottlenecks(team_id, start_date, end_date)
        
        assert isinstance(bottlenecks, list)
        for bottleneck in bottlenecks:
            assert "type" in bottleneck
            assert "description" in bottleneck
            assert "impact" in bottleneck
            assert "suggestion" in bottleneck


class TestTeamCollaborationManager:
    """Test team collaboration manager functionality"""
    
    def test_add_integrations(self, team_collaboration_manager):
        """Test adding team collaboration integrations"""
        # Add Slack integration
        team_collaboration_manager.add_slack_integration("slack_token", "slack_secret")
        assert team_collaboration_manager.slack_integration is not None
        
        # Add Teams integration
        team_collaboration_manager.add_teams_integration("teams_app_id", "teams_password")
        assert team_collaboration_manager.teams_integration is not None
    
    @pytest.mark.asyncio
    async def test_notify_team(self, team_collaboration_manager):
        """Test team notification through manager"""
        # Add Slack integration
        team_collaboration_manager.add_slack_integration("slack_token", "slack_secret")
        
        # Mock Slack integration
        team_collaboration_manager.slack_integration.send_notification = AsyncMock(return_value=True)
        
        result = await team_collaboration_manager.notify_team(
            "slack", "#general", "Test notification"
        )
        
        assert result is True
        team_collaboration_manager.slack_integration.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_share_code_with_team(self, team_collaboration_manager):
        """Test sharing code with team through manager"""
        # Add Slack integration
        team_collaboration_manager.add_slack_integration("slack_token", "slack_secret")
        
        # Mock Slack integration
        team_collaboration_manager.slack_integration.share_code_snippet = AsyncMock(return_value=True)
        
        result = await team_collaboration_manager.share_code_with_team(
            "slack", "#general", "def hello(): pass", "python", "Example function"
        )
        
        assert result is True
        team_collaboration_manager.slack_integration.share_code_snippet.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_team_discussion(self, team_collaboration_manager):
        """Test creating team discussion through manager"""
        # Add Slack integration
        team_collaboration_manager.add_slack_integration("slack_token", "slack_secret")
        
        # Mock Slack integration
        team_collaboration_manager.slack_integration.create_thread = AsyncMock(return_value="thread123")
        
        thread_id = await team_collaboration_manager.create_team_discussion(
            "slack", "#general", "Code Review", "Please review this PR"
        )
        
        assert thread_id == "thread123"
        team_collaboration_manager.slack_integration.create_thread.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_team_meeting(self, team_collaboration_manager):
        """Test scheduling team meeting through manager"""
        # Add Slack integration
        team_collaboration_manager.add_slack_integration("slack_token", "slack_secret")
        
        # Mock Slack integration
        team_collaboration_manager.slack_integration.schedule_meeting = AsyncMock(return_value={
            "status": "scheduled",
            "meeting_id": "meeting123"
        })
        
        result = await team_collaboration_manager.schedule_team_meeting(
            "slack", ["user1", "user2"], "Sprint Planning", 60
        )
        
        assert result["status"] == "scheduled"
        team_collaboration_manager.slack_integration.schedule_meeting.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_knowledge_base_operations(self, team_collaboration_manager, sample_knowledge_item):
        """Test knowledge base operations through manager"""
        # Add knowledge item
        result = await team_collaboration_manager.add_team_knowledge(sample_knowledge_item)
        assert result is True
        
        # Search knowledge
        results = await team_collaboration_manager.search_team_knowledge("Python")
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_planning_operations(self, team_collaboration_manager, sample_collaborative_plan):
        """Test planning operations through manager"""
        # Create plan
        result = await team_collaboration_manager.create_collaborative_plan(sample_collaborative_plan)
        assert result is True
        
        # Get plans
        plans = await team_collaboration_manager.get_team_plans()
        assert len(plans) > 0
    
    @pytest.mark.asyncio
    async def test_analytics_operations(self, team_collaboration_manager):
        """Test analytics operations through manager"""
        team_id = "team123"
        
        analytics = await team_collaboration_manager.get_team_analytics(team_id)
        
        assert isinstance(analytics, TeamAnalytics)
        assert analytics.team_id == team_id
    
    def test_team_member_management(self, team_collaboration_manager, sample_team_member):
        """Test team member management"""
        # Add team member
        team_collaboration_manager.add_team_member(sample_team_member)
        
        # Get team member
        retrieved_member = team_collaboration_manager.get_team_member(sample_team_member.id)
        assert retrieved_member is not None
        assert retrieved_member.name == sample_team_member.name
        
        # Get all team members
        all_members = team_collaboration_manager.get_all_team_members()
        assert len(all_members) > 0
        assert sample_team_member in all_members
    
    @pytest.mark.asyncio
    async def test_cleanup(self, team_collaboration_manager):
        """Test cleanup of team collaboration resources"""
        # Add integrations with mock sessions
        team_collaboration_manager.add_slack_integration("slack_token", "slack_secret")
        team_collaboration_manager.slack_integration.session = AsyncMock()
        
        await team_collaboration_manager.cleanup()
        
        # Verify session was closed
        team_collaboration_manager.slack_integration.session.close.assert_called_once()


class TestTeamCollaborationErrorHandling:
    """Test error handling in team collaboration"""
    
    @pytest.mark.asyncio
    async def test_slack_api_error_handling(self, slack_integration):
        """Test Slack API error handling"""
        # Mock HTTP session with error response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"ok": False, "error": "channel_not_found"}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(slack_integration, '_get_session', return_value=mock_session):
            result = await slack_integration.send_notification("#nonexistent", "Test message")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, sample_knowledge_item):
        """Test database error handling"""
        # Create knowledge base with invalid path
        knowledge_base = SharedKnowledgeBase("/invalid/path/database.db")
        
        # This should handle the error gracefully
        result = await knowledge_base.add_knowledge_item(sample_knowledge_item)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, teams_integration):
        """Test network timeout handling"""
        # Mock session that raises timeout
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError("Request timeout")
        
        with patch.object(teams_integration, '_get_session', return_value=mock_session):
            result = await teams_integration.send_notification("team123", "Test message")
            
            assert result is False


class TestTeamCollaborationPerformance:
    """Test performance aspects of team collaboration"""
    
    @pytest.mark.asyncio
    async def test_concurrent_notifications(self, team_collaboration_manager):
        """Test handling concurrent notifications"""
        # Add Slack integration
        team_collaboration_manager.add_slack_integration("slack_token", "slack_secret")
        team_collaboration_manager.slack_integration.send_notification = AsyncMock(return_value=True)
        
        # Send multiple notifications concurrently
        tasks = []
        for i in range(10):
            task = team_collaboration_manager.notify_team(
                "slack", "#general", f"Test message {i}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All notifications should succeed
        assert all(results)
    
    @pytest.mark.asyncio
    async def test_large_knowledge_base_search(self, knowledge_base):
        """Test searching large knowledge base"""
        # Add many knowledge items
        for i in range(100):
            item = KnowledgeItem(
                id=f"kb{i:03d}",
                title=f"Knowledge Item {i}",
                content=f"Content for item {i} with Python and JavaScript",
                category="development",
                tags=["python", "javascript"],
                author="test@example.com",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                access_level="team",
                related_items=[]
            )
            await knowledge_base.add_knowledge_item(item)
        
        # Search should be fast
        start_time = asyncio.get_event_loop().time()
        results = await knowledge_base.search_knowledge("Python")
        end_time = asyncio.get_event_loop().time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second max
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_analytics_generation_performance(self, analytics_dashboard):
        """Test analytics generation performance"""
        team_id = "team123"
        
        start_time = asyncio.get_event_loop().time()
        analytics = await analytics_dashboard.generate_team_analytics(team_id, 90)  # 3 months
        end_time = asyncio.get_event_loop().time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 2.0  # 2 seconds max
        assert isinstance(analytics, TeamAnalytics)


if __name__ == "__main__":
    pytest.main([__file__])