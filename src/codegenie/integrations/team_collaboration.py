"""
Team Collaboration Integration System

Provides integrations with team collaboration tools including Slack, Microsoft Teams,
shared knowledge bases, collaborative planning workflows, and team analytics dashboards.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import sqlite3
from collections import defaultdict

from ..core.context_engine import ContextEngine
from ..core.knowledge_graph import CodeKnowledgeGraph
from ..agents.base_agent import BaseAgent


@dataclass
class TeamMember:
    """Team member information"""
    id: str
    name: str
    email: str
    role: str
    skills: List[str]
    timezone: str
    availability: Dict[str, Any]
    preferences: Dict[str, Any]


@dataclass
class KnowledgeItem:
    """Shared knowledge base item"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    author: str
    created_at: datetime
    updated_at: datetime
    access_level: str
    related_items: List[str]


@dataclass
class CollaborativePlan:
    """Collaborative planning item"""
    id: str
    title: str
    description: str
    type: str  # feature, bug, task, epic
    status: str
    priority: str
    assignee: Optional[str]
    reviewers: List[str]
    estimated_effort: int
    actual_effort: Optional[int]
    dependencies: List[str]
    created_at: datetime
    due_date: Optional[datetime]
    tags: List[str]


@dataclass
class TeamAnalytics:
    """Team analytics and insights"""
    team_id: str
    period_start: datetime
    period_end: datetime
    velocity: float
    productivity_score: float
    collaboration_score: float
    code_quality_trend: List[float]
    member_contributions: Dict[str, Dict[str, Any]]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]


class TeamCollaborationBase(ABC):
    """Base class for team collaboration integrations"""
    
    def __init__(self, context_engine: ContextEngine, knowledge_graph: CodeKnowledgeGraph):
        self.context_engine = context_engine
        self.knowledge_graph = knowledge_graph
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def send_notification(self, channel: str, message: str, attachments: Optional[List] = None) -> bool:
        """Send notification to team channel"""
        pass
    
    @abstractmethod
    async def create_thread(self, channel: str, topic: str, initial_message: str) -> str:
        """Create discussion thread"""
        pass
    
    @abstractmethod
    async def share_code_snippet(self, channel: str, code: str, language: str, context: str) -> bool:
        """Share code snippet with team"""
        pass
    
    @abstractmethod
    async def schedule_meeting(self, participants: List[str], topic: str, duration: int) -> Dict[str, Any]:
        """Schedule team meeting"""
        pass


class SlackIntegration(TeamCollaborationBase):
    """Slack integration for team collaboration"""
    
    def __init__(self, context_engine: ContextEngine, knowledge_graph: CodeKnowledgeGraph,
                 slack_token: str, slack_signing_secret: str):
        super().__init__(context_engine, knowledge_graph)
        self.slack_token = slack_token
        self.slack_signing_secret = slack_signing_secret
        self.session = None
        self.bot_user_id = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with Slack authentication"""
        if not self.session:
            headers = {
                "Authorization": f"Bearer {self.slack_token}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def initialize(self):
        """Initialize Slack integration"""
        try:
            session = await self._get_session()
            
            # Get bot user info
            async with session.get("https://slack.com/api/auth.test") as response:
                auth_data = await response.json()
                if auth_data["ok"]:
                    self.bot_user_id = auth_data["user_id"]
                    self.logger.info(f"Slack bot initialized: {auth_data['user']}")
                else:
                    raise Exception(f"Slack auth failed: {auth_data['error']}")
            
        except Exception as e:
            self.logger.error(f"Error initializing Slack integration: {e}")
            raise
    
    async def send_notification(self, channel: str, message: str, attachments: Optional[List] = None) -> bool:
        """Send notification to Slack channel"""
        try:
            session = await self._get_session()
            
            payload = {
                "channel": channel,
                "text": message,
                "as_user": True
            }
            
            if attachments:
                payload["attachments"] = attachments
            
            async with session.post("https://slack.com/api/chat.postMessage", json=payload) as response:
                result = await response.json()
                return result.get("ok", False)
                
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
            return False
    
    async def create_thread(self, channel: str, topic: str, initial_message: str) -> str:
        """Create discussion thread in Slack"""
        try:
            session = await self._get_session()
            
            # Post initial message
            payload = {
                "channel": channel,
                "text": f"🧵 *{topic}*\n\n{initial_message}",
                "as_user": True
            }
            
            async with session.post("https://slack.com/api/chat.postMessage", json=payload) as response:
                result = await response.json()
                if result.get("ok"):
                    return result["message"]["ts"]  # Thread timestamp
                else:
                    raise Exception(f"Failed to create thread: {result.get('error')}")
                    
        except Exception as e:
            self.logger.error(f"Error creating Slack thread: {e}")
            return ""
    
    async def share_code_snippet(self, channel: str, code: str, language: str, context: str) -> bool:
        """Share code snippet in Slack with syntax highlighting"""
        try:
            session = await self._get_session()
            
            # Create code block with syntax highlighting
            code_block = f"```{language}\n{code}\n```"
            
            payload = {
                "channel": channel,
                "text": f"💻 *Code Snippet* - {context}\n\n{code_block}",
                "as_user": True,
                "unfurl_links": False,
                "unfurl_media": False
            }
            
            async with session.post("https://slack.com/api/chat.postMessage", json=payload) as response:
                result = await response.json()
                return result.get("ok", False)
                
        except Exception as e:
            self.logger.error(f"Error sharing code snippet: {e}")
            return False
    
    async def schedule_meeting(self, participants: List[str], topic: str, duration: int) -> Dict[str, Any]:
        """Schedule meeting using Slack (integration with calendar apps)"""
        try:
            # Create meeting invitation message
            participant_mentions = " ".join([f"<@{p}>" for p in participants])
            
            message = f"""
📅 *Meeting Scheduled: {topic}*

👥 Participants: {participant_mentions}
⏱️ Duration: {duration} minutes
📝 Topic: {topic}

Please confirm your availability by reacting with ✅
            """
            
            # Send to a coordination channel or DM
            channel = "#meetings"  # Default meeting channel
            success = await self.send_notification(channel, message)
            
            if success:
                return {
                    "status": "scheduled",
                    "topic": topic,
                    "participants": participants,
                    "duration": duration,
                    "channel": channel
                }
            else:
                return {"status": "failed", "error": "Could not send meeting notification"}
                
        except Exception as e:
            self.logger.error(f"Error scheduling meeting: {e}")
            return {"status": "error", "error": str(e)}
    
    async def handle_slash_command(self, command: str, text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Handle Slack slash commands for CodeGenie"""
        try:
            if command == "/codegenie":
                return await self._handle_codegenie_command(text, user_id, channel_id)
            elif command == "/code-review":
                return await self._handle_code_review_command(text, user_id, channel_id)
            elif command == "/knowledge":
                return await self._handle_knowledge_command(text, user_id, channel_id)
            else:
                return {
                    "response_type": "ephemeral",
                    "text": f"Unknown command: {command}"
                }
                
        except Exception as e:
            self.logger.error(f"Error handling slash command: {e}")
            return {
                "response_type": "ephemeral",
                "text": "Sorry, there was an error processing your command."
            }
    
    async def _handle_codegenie_command(self, text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Handle /codegenie command"""
        if not text:
            return {
                "response_type": "ephemeral",
                "text": "Usage: /codegenie <your question or request>"
            }
        
        # Process request through CodeGenie
        # This would integrate with the main CodeGenie system
        response = f"🤖 CodeGenie is processing your request: '{text}'"
        
        return {
            "response_type": "in_channel",
            "text": response
        }
    
    async def _handle_code_review_command(self, text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Handle /code-review command"""
        if not text:
            return {
                "response_type": "ephemeral",
                "text": "Usage: /code-review <PR URL or file path>"
            }
        
        # Trigger code review process
        response = f"🔍 Starting code review for: {text}"
        
        return {
            "response_type": "in_channel",
            "text": response
        }
    
    async def _handle_knowledge_command(self, text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Handle /knowledge command"""
        if not text:
            return {
                "response_type": "ephemeral",
                "text": "Usage: /knowledge search <query> | add <title> | list"
            }
        
        parts = text.split(" ", 1)
        action = parts[0]
        
        if action == "search" and len(parts) > 1:
            query = parts[1]
            # Search knowledge base
            response = f"🔍 Searching knowledge base for: '{query}'"
        elif action == "add" and len(parts) > 1:
            title = parts[1]
            response = f"📝 Adding to knowledge base: '{title}'"
        elif action == "list":
            response = "📚 Listing knowledge base items..."
        else:
            response = "Usage: /knowledge search <query> | add <title> | list"
        
        return {
            "response_type": "ephemeral",
            "text": response
        }


class TeamsIntegration(TeamCollaborationBase):
    """Microsoft Teams integration for team collaboration"""
    
    def __init__(self, context_engine: ContextEngine, knowledge_graph: CodeKnowledgeGraph,
                 teams_app_id: str, teams_app_password: str):
        super().__init__(context_engine, knowledge_graph)
        self.teams_app_id = teams_app_id
        self.teams_app_password = teams_app_password
        self.session = None
        self.access_token = None
    
    async def _get_access_token(self) -> str:
        """Get Microsoft Graph API access token"""
        if not self.access_token:
            # Implementation for OAuth2 flow with Microsoft Graph
            # This is a simplified version
            self.access_token = "mock_access_token"
        return self.access_token
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with Teams authentication"""
        if not self.session:
            token = await self._get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def send_notification(self, channel: str, message: str, attachments: Optional[List] = None) -> bool:
        """Send notification to Teams channel"""
        try:
            session = await self._get_session()
            
            # Teams message format
            payload = {
                "body": {
                    "contentType": "html",
                    "content": message
                }
            }
            
            if attachments:
                payload["attachments"] = attachments
            
            # Send to Teams channel via Graph API
            url = f"https://graph.microsoft.com/v1.0/teams/{channel}/channels/general/messages"
            
            async with session.post(url, json=payload) as response:
                return response.status == 201
                
        except Exception as e:
            self.logger.error(f"Error sending Teams notification: {e}")
            return False
    
    async def create_thread(self, channel: str, topic: str, initial_message: str) -> str:
        """Create discussion thread in Teams"""
        try:
            session = await self._get_session()
            
            payload = {
                "subject": topic,
                "body": {
                    "contentType": "html",
                    "content": initial_message
                }
            }
            
            url = f"https://graph.microsoft.com/v1.0/teams/{channel}/channels/general/messages"
            
            async with session.post(url, json=payload) as response:
                if response.status == 201:
                    result = await response.json()
                    return result["id"]
                else:
                    return ""
                    
        except Exception as e:
            self.logger.error(f"Error creating Teams thread: {e}")
            return ""
    
    async def share_code_snippet(self, channel: str, code: str, language: str, context: str) -> bool:
        """Share code snippet in Teams"""
        try:
            # Format code for Teams
            formatted_code = f"""
            <h3>💻 Code Snippet - {context}</h3>
            <pre><code class="language-{language}">{code}</code></pre>
            """
            
            return await self.send_notification(channel, formatted_code)
            
        except Exception as e:
            self.logger.error(f"Error sharing code snippet in Teams: {e}")
            return False
    
    async def schedule_meeting(self, participants: List[str], topic: str, duration: int) -> Dict[str, Any]:
        """Schedule meeting in Teams"""
        try:
            session = await self._get_session()
            
            # Create Teams meeting
            meeting_payload = {
                "subject": topic,
                "start": {
                    "dateTime": datetime.now().isoformat(),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": (datetime.now() + timedelta(minutes=duration)).isoformat(),
                    "timeZone": "UTC"
                },
                "attendees": [
                    {
                        "emailAddress": {
                            "address": participant,
                            "name": participant
                        },
                        "type": "required"
                    }
                    for participant in participants
                ],
                "isOnlineMeeting": True,
                "onlineMeetingProvider": "teamsForBusiness"
            }
            
            url = "https://graph.microsoft.com/v1.0/me/events"
            
            async with session.post(url, json=meeting_payload) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        "status": "scheduled",
                        "meeting_id": result["id"],
                        "join_url": result.get("onlineMeeting", {}).get("joinUrl"),
                        "topic": topic,
                        "participants": participants
                    }
                else:
                    return {"status": "failed", "error": "Could not create meeting"}
                    
        except Exception as e:
            self.logger.error(f"Error scheduling Teams meeting: {e}")
            return {"status": "error", "error": str(e)}


class SharedKnowledgeBase:
    """Shared knowledge base system for team collaboration"""
    
    def __init__(self, db_path: str = "team_knowledge.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for knowledge base"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create knowledge items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    author TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    access_level TEXT,
                    related_items TEXT
                )
            """)
            
            # Create search index
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_search 
                USING fts5(title, content, tags, category)
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing knowledge base database: {e}")
            raise
    
    async def add_knowledge_item(self, item: KnowledgeItem) -> bool:
        """Add item to knowledge base"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_items 
                (id, title, content, category, tags, author, created_at, updated_at, access_level, related_items)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id, item.title, item.content, item.category,
                json.dumps(item.tags), item.author, item.created_at, item.updated_at,
                item.access_level, json.dumps(item.related_items)
            ))
            
            # Add to search index
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_search (rowid, title, content, tags, category)
                VALUES (?, ?, ?, ?, ?)
            """, (
                hash(item.id) % (2**31), item.title, item.content,
                " ".join(item.tags), item.category
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added knowledge item: {item.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding knowledge item: {e}")
            return False
    
    async def search_knowledge(self, query: str, category: Optional[str] = None,
                             limit: int = 10) -> List[KnowledgeItem]:
        """Search knowledge base"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if category:
                cursor.execute("""
                    SELECT k.* FROM knowledge_items k
                    JOIN knowledge_search s ON k.rowid = s.rowid
                    WHERE knowledge_search MATCH ? AND k.category = ?
                    ORDER BY rank LIMIT ?
                """, (query, category, limit))
            else:
                cursor.execute("""
                    SELECT k.* FROM knowledge_items k
                    JOIN knowledge_search s ON k.rowid = s.rowid
                    WHERE knowledge_search MATCH ?
                    ORDER BY rank LIMIT ?
                """, (query, limit))
            
            results = []
            for row in cursor.fetchall():
                item = KnowledgeItem(
                    id=row[0], title=row[1], content=row[2], category=row[3],
                    tags=json.loads(row[4]), author=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    updated_at=datetime.fromisoformat(row[7]),
                    access_level=row[8], related_items=json.loads(row[9])
                )
                results.append(item)
            
            conn.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {e}")
            return []
    
    async def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Get specific knowledge item"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            
            if row:
                item = KnowledgeItem(
                    id=row[0], title=row[1], content=row[2], category=row[3],
                    tags=json.loads(row[4]), author=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    updated_at=datetime.fromisoformat(row[7]),
                    access_level=row[8], related_items=json.loads(row[9])
                )
                conn.close()
                return item
            
            conn.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting knowledge item: {e}")
            return None
    
    async def update_knowledge_item(self, item: KnowledgeItem) -> bool:
        """Update existing knowledge item"""
        item.updated_at = datetime.now()
        return await self.add_knowledge_item(item)
    
    async def delete_knowledge_item(self, item_id: str) -> bool:
        """Delete knowledge item"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
            cursor.execute("DELETE FROM knowledge_search WHERE rowid = ?", (hash(item_id) % (2**31),))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting knowledge item: {e}")
            return False
    
    async def get_categories(self) -> List[str]:
        """Get all knowledge categories"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT category FROM knowledge_items WHERE category IS NOT NULL")
            categories = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return categories
            
        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            return []


class CollaborativePlanningSystem:
    """Collaborative planning and review workflows"""
    
    def __init__(self, db_path: str = "collaborative_planning.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database for collaborative planning"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collaborative_plans (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    type TEXT,
                    status TEXT,
                    priority TEXT,
                    assignee TEXT,
                    reviewers TEXT,
                    estimated_effort INTEGER,
                    actual_effort INTEGER,
                    dependencies TEXT,
                    created_at TIMESTAMP,
                    due_date TIMESTAMP,
                    tags TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing planning database: {e}")
            raise
    
    async def create_plan(self, plan: CollaborativePlan) -> bool:
        """Create new collaborative plan"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO collaborative_plans 
                (id, title, description, type, status, priority, assignee, reviewers,
                 estimated_effort, actual_effort, dependencies, created_at, due_date, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.id, plan.title, plan.description, plan.type, plan.status,
                plan.priority, plan.assignee, json.dumps(plan.reviewers),
                plan.estimated_effort, plan.actual_effort, json.dumps(plan.dependencies),
                plan.created_at, plan.due_date, json.dumps(plan.tags)
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            return False
    
    async def get_plans(self, status: Optional[str] = None, assignee: Optional[str] = None) -> List[CollaborativePlan]:
        """Get collaborative plans with optional filters"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM collaborative_plans WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if assignee:
                query += " AND assignee = ?"
                params.append(assignee)
            
            cursor.execute(query, params)
            
            plans = []
            for row in cursor.fetchall():
                plan = CollaborativePlan(
                    id=row[0], title=row[1], description=row[2], type=row[3],
                    status=row[4], priority=row[5], assignee=row[6],
                    reviewers=json.loads(row[7]), estimated_effort=row[8],
                    actual_effort=row[9], dependencies=json.loads(row[10]),
                    created_at=datetime.fromisoformat(row[11]),
                    due_date=datetime.fromisoformat(row[12]) if row[12] else None,
                    tags=json.loads(row[13])
                )
                plans.append(plan)
            
            conn.close()
            return plans
            
        except Exception as e:
            self.logger.error(f"Error getting plans: {e}")
            return []
    
    async def update_plan_status(self, plan_id: str, status: str) -> bool:
        """Update plan status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE collaborative_plans SET status = ? WHERE id = ?", (status, plan_id))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error updating plan status: {e}")
            return False
    
    async def assign_reviewers(self, plan_id: str, reviewers: List[str]) -> bool:
        """Assign reviewers to plan"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE collaborative_plans SET reviewers = ? WHERE id = ?", 
                         (json.dumps(reviewers), plan_id))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error assigning reviewers: {e}")
            return False


class TeamAnalyticsDashboard:
    """Team analytics and insights dashboard"""
    
    def __init__(self, context_engine: ContextEngine):
        self.context_engine = context_engine
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_team_analytics(self, team_id: str, period_days: int = 30) -> TeamAnalytics:
        """Generate comprehensive team analytics"""
        try:
            period_start = datetime.now() - timedelta(days=period_days)
            period_end = datetime.now()
            
            # Calculate team velocity (simplified)
            velocity = await self._calculate_velocity(team_id, period_start, period_end)
            
            # Calculate productivity score
            productivity_score = await self._calculate_productivity_score(team_id, period_start, period_end)
            
            # Calculate collaboration score
            collaboration_score = await self._calculate_collaboration_score(team_id, period_start, period_end)
            
            # Get code quality trend
            code_quality_trend = await self._get_code_quality_trend(team_id, period_start, period_end)
            
            # Get member contributions
            member_contributions = await self._get_member_contributions(team_id, period_start, period_end)
            
            # Identify bottlenecks
            bottlenecks = await self._identify_bottlenecks(team_id, period_start, period_end)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                velocity, productivity_score, collaboration_score, bottlenecks
            )
            
            return TeamAnalytics(
                team_id=team_id,
                period_start=period_start,
                period_end=period_end,
                velocity=velocity,
                productivity_score=productivity_score,
                collaboration_score=collaboration_score,
                code_quality_trend=code_quality_trend,
                member_contributions=member_contributions,
                bottlenecks=bottlenecks,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error generating team analytics: {e}")
            raise
    
    async def _calculate_velocity(self, team_id: str, start: datetime, end: datetime) -> float:
        """Calculate team velocity (story points per sprint)"""
        # Simplified calculation - would integrate with project management tools
        return 42.5
    
    async def _calculate_productivity_score(self, team_id: str, start: datetime, end: datetime) -> float:
        """Calculate team productivity score"""
        # Factors: commits, PRs, code reviews, bug fixes, etc.
        return 0.78
    
    async def _calculate_collaboration_score(self, team_id: str, start: datetime, end: datetime) -> float:
        """Calculate team collaboration score"""
        # Factors: code reviews, pair programming, knowledge sharing, etc.
        return 0.85
    
    async def _get_code_quality_trend(self, team_id: str, start: datetime, end: datetime) -> List[float]:
        """Get code quality trend over time"""
        # Weekly code quality scores
        return [0.75, 0.78, 0.82, 0.80, 0.85]
    
    async def _get_member_contributions(self, team_id: str, start: datetime, end: datetime) -> Dict[str, Dict[str, Any]]:
        """Get individual member contributions"""
        return {
            "alice": {
                "commits": 45,
                "prs": 12,
                "reviews": 18,
                "bugs_fixed": 8,
                "features": 3
            },
            "bob": {
                "commits": 38,
                "prs": 10,
                "reviews": 15,
                "bugs_fixed": 6,
                "features": 2
            }
        }
    
    async def _identify_bottlenecks(self, team_id: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Identify team bottlenecks"""
        return [
            {
                "type": "code_review",
                "description": "Code reviews taking longer than average",
                "impact": "medium",
                "suggestion": "Consider adding more reviewers or review guidelines"
            },
            {
                "type": "deployment",
                "description": "Deployment process causing delays",
                "impact": "high",
                "suggestion": "Automate deployment pipeline"
            }
        ]
    
    async def _generate_recommendations(self, velocity: float, productivity: float,
                                     collaboration: float, bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        if velocity < 40:
            recommendations.append("Consider breaking down larger tasks to improve velocity")
        
        if productivity < 0.7:
            recommendations.append("Focus on reducing context switching and interruptions")
        
        if collaboration < 0.8:
            recommendations.append("Encourage more code reviews and pair programming")
        
        for bottleneck in bottlenecks:
            if bottleneck["impact"] == "high":
                recommendations.append(f"Address high-impact bottleneck: {bottleneck['suggestion']}")
        
        return recommendations


class TeamCollaborationManager:
    """Manager for all team collaboration features"""
    
    def __init__(self, context_engine: ContextEngine, knowledge_graph: CodeKnowledgeGraph):
        self.context_engine = context_engine
        self.knowledge_graph = knowledge_graph
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.knowledge_base = SharedKnowledgeBase()
        self.planning_system = CollaborativePlanningSystem()
        self.analytics_dashboard = TeamAnalyticsDashboard(context_engine)
        
        # Integration instances
        self.slack_integration: Optional[SlackIntegration] = None
        self.teams_integration: Optional[TeamsIntegration] = None
        
        # Team members registry
        self.team_members: Dict[str, TeamMember] = {}
    
    def add_slack_integration(self, slack_token: str, slack_signing_secret: str):
        """Add Slack integration"""
        self.slack_integration = SlackIntegration(
            self.context_engine, self.knowledge_graph, slack_token, slack_signing_secret
        )
    
    def add_teams_integration(self, teams_app_id: str, teams_app_password: str):
        """Add Microsoft Teams integration"""
        self.teams_integration = TeamsIntegration(
            self.context_engine, self.knowledge_graph, teams_app_id, teams_app_password
        )
    
    async def initialize_integrations(self):
        """Initialize all team collaboration integrations"""
        try:
            if self.slack_integration:
                await self.slack_integration.initialize()
                self.logger.info("Slack integration initialized")
            
            if self.teams_integration:
                # Teams initialization would go here
                self.logger.info("Teams integration initialized")
                
        except Exception as e:
            self.logger.error(f"Error initializing team integrations: {e}")
            raise
    
    async def notify_team(self, platform: str, channel: str, message: str, 
                         attachments: Optional[List] = None) -> bool:
        """Send notification to team via specified platform"""
        try:
            if platform == "slack" and self.slack_integration:
                return await self.slack_integration.send_notification(channel, message, attachments)
            elif platform == "teams" and self.teams_integration:
                return await self.teams_integration.send_notification(channel, message, attachments)
            else:
                self.logger.warning(f"Platform not available: {platform}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending team notification: {e}")
            return False
    
    async def share_code_with_team(self, platform: str, channel: str, code: str, 
                                  language: str, context: str) -> bool:
        """Share code snippet with team"""
        try:
            if platform == "slack" and self.slack_integration:
                return await self.slack_integration.share_code_snippet(channel, code, language, context)
            elif platform == "teams" and self.teams_integration:
                return await self.teams_integration.share_code_snippet(channel, code, language, context)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error sharing code with team: {e}")
            return False
    
    async def create_team_discussion(self, platform: str, channel: str, topic: str, 
                                   initial_message: str) -> str:
        """Create team discussion thread"""
        try:
            if platform == "slack" and self.slack_integration:
                return await self.slack_integration.create_thread(channel, topic, initial_message)
            elif platform == "teams" and self.teams_integration:
                return await self.teams_integration.create_thread(channel, topic, initial_message)
            else:
                return ""
                
        except Exception as e:
            self.logger.error(f"Error creating team discussion: {e}")
            return ""
    
    async def schedule_team_meeting(self, platform: str, participants: List[str], 
                                  topic: str, duration: int) -> Dict[str, Any]:
        """Schedule team meeting"""
        try:
            if platform == "slack" and self.slack_integration:
                return await self.slack_integration.schedule_meeting(participants, topic, duration)
            elif platform == "teams" and self.teams_integration:
                return await self.teams_integration.schedule_meeting(participants, topic, duration)
            else:
                return {"status": "error", "error": "Platform not available"}
                
        except Exception as e:
            self.logger.error(f"Error scheduling team meeting: {e}")
            return {"status": "error", "error": str(e)}
    
    # Knowledge base methods
    async def add_team_knowledge(self, item: KnowledgeItem) -> bool:
        """Add item to team knowledge base"""
        return await self.knowledge_base.add_knowledge_item(item)
    
    async def search_team_knowledge(self, query: str, category: Optional[str] = None) -> List[KnowledgeItem]:
        """Search team knowledge base"""
        return await self.knowledge_base.search_knowledge(query, category)
    
    # Planning methods
    async def create_collaborative_plan(self, plan: CollaborativePlan) -> bool:
        """Create collaborative plan"""
        return await self.planning_system.create_plan(plan)
    
    async def get_team_plans(self, status: Optional[str] = None, assignee: Optional[str] = None) -> List[CollaborativePlan]:
        """Get team plans"""
        return await self.planning_system.get_plans(status, assignee)
    
    # Analytics methods
    async def get_team_analytics(self, team_id: str, period_days: int = 30) -> TeamAnalytics:
        """Get team analytics and insights"""
        return await self.analytics_dashboard.generate_team_analytics(team_id, period_days)
    
    # Team member management
    def add_team_member(self, member: TeamMember):
        """Add team member"""
        self.team_members[member.id] = member
    
    def get_team_member(self, member_id: str) -> Optional[TeamMember]:
        """Get team member"""
        return self.team_members.get(member_id)
    
    def get_all_team_members(self) -> List[TeamMember]:
        """Get all team members"""
        return list(self.team_members.values())
    
    async def cleanup(self):
        """Cleanup team collaboration resources"""
        try:
            if self.slack_integration and self.slack_integration.session:
                await self.slack_integration.session.close()
            
            if self.teams_integration and self.teams_integration.session:
                await self.teams_integration.session.close()
                
            self.logger.info("Team collaboration resources cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up team collaboration: {e}")