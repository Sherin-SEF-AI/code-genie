"""
Context engine for cross-session context management and intelligent retrieval.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context information."""
    
    CONVERSATION = "conversation"
    PROJECT = "project"
    USER_PREFERENCE = "user_preference"
    DECISION = "decision"
    GOAL = "goal"
    ERROR = "error"
    SUCCESS = "success"
    PATTERN = "pattern"


class ContextPriority(Enum):
    """Priority levels for context information."""
    
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ContextItem:
    """Represents a single piece of context information."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    content: Any = None
    context_type: ContextType = ContextType.CONVERSATION
    priority: ContextPriority = ContextPriority.MEDIUM
    timestamp: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Relevance and retrieval
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    # Relationships
    related_items: Set[str] = field(default_factory=set)
    parent_id: Optional[str] = None
    children_ids: Set[str] = field(default_factory=set)


@dataclass
class ContextBundle:
    """Bundle of related context items."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    items: List[ContextItem] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    relevance_score: float = 0.0


@dataclass
class SessionSummary:
    """Summary of a session's context and activities."""
    
    session_id: str
    start_time: float
    end_time: float
    duration: float
    conversation_turns: int
    goals_achieved: List[str]
    decisions_made: List[str]
    errors_encountered: List[str]
    key_insights: List[str]
    context_items_created: int
    summary_text: str = ""


class PersistentMemoryManager:
    """Manages persistent storage and retrieval of context information."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.context_file = self.storage_path / "context_items.json"
        self.sessions_file = self.storage_path / "sessions.json"
        self.metadata_file = self.storage_path / "metadata.json"
        
        # In-memory caches
        self.context_items: Dict[str, ContextItem] = {}
        self.sessions: Dict[str, SessionSummary] = {}
        self.metadata: Dict[str, Any] = {}
        
        # Load existing data
        self._load_data()
        
        logger.info(f"Initialized PersistentMemoryManager with storage at {storage_path}")
    
    def _load_data(self) -> None:
        """Load data from persistent storage."""
        try:
            # Load context items
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        item = self._deserialize_context_item(item_data)
                        self.context_items[item.id] = item
            
            # Load sessions
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for session_data in data:
                        session = self._deserialize_session_summary(session_data)
                        self.sessions[session.session_id] = session
            
            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            
            logger.info(f"Loaded {len(self.context_items)} context items and {len(self.sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Error loading persistent memory: {e}")
    
    def _save_data(self) -> None:
        """Save data to persistent storage."""
        try:
            # Save context items
            context_data = [self._serialize_context_item(item) for item in self.context_items.values()]
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2)
            
            # Save sessions
            session_data = [self._serialize_session_summary(session) for session in self.sessions.values()]
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            # Save metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            
            logger.debug("Saved persistent memory data")
            
        except Exception as e:
            logger.error(f"Error saving persistent memory: {e}")
    
    def store_context_item(self, item: ContextItem) -> None:
        """Store a context item in persistent memory."""
        self.context_items[item.id] = item
        self._save_data()
    
    def retrieve_context_item(self, item_id: str) -> Optional[ContextItem]:
        """Retrieve a context item by ID."""
        item = self.context_items.get(item_id)
        if item:
            item.access_count += 1
            item.last_accessed = time.time()
            self._save_data()
        return item
    
    def store_session_summary(self, summary: SessionSummary) -> None:
        """Store a session summary."""
        self.sessions[summary.session_id] = summary
        self._save_data()
    
    def retrieve_session_summary(self, session_id: str) -> Optional[SessionSummary]:
        """Retrieve a session summary by ID."""
        return self.sessions.get(session_id)
    
    def search_context_items(
        self,
        query: str = "",
        context_type: Optional[ContextType] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 10
    ) -> List[ContextItem]:
        """Search for context items based on criteria."""
        results = []
        
        for item in self.context_items.values():
            # Filter by type
            if context_type and item.context_type != context_type:
                continue
            
            # Filter by tags
            if tags and not tags.intersection(item.tags):
                continue
            
            # Filter by query (simple text search)
            if query:
                content_str = str(item.content).lower()
                if query.lower() not in content_str:
                    continue
            
            results.append(item)
        
        # Sort by relevance and recency
        results.sort(key=lambda x: (x.relevance_score, x.timestamp), reverse=True)
        
        return results[:limit]
    
    def get_recent_context_items(self, limit: int = 20) -> List[ContextItem]:
        """Get most recent context items."""
        items = list(self.context_items.values())
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[:limit]
    
    def cleanup_old_items(self, max_age_days: int = 30) -> int:
        """Clean up old context items."""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        items_to_remove = []
        for item_id, item in self.context_items.items():
            if item.timestamp < cutoff_time and item.priority == ContextPriority.LOW:
                items_to_remove.append(item_id)
        
        for item_id in items_to_remove:
            del self.context_items[item_id]
        
        if items_to_remove:
            self._save_data()
        
        logger.info(f"Cleaned up {len(items_to_remove)} old context items")
        return len(items_to_remove)
    
    def _serialize_context_item(self, item: ContextItem) -> Dict[str, Any]:
        """Serialize a context item for storage."""
        return {
            "id": item.id,
            "content": item.content,
            "context_type": item.context_type.value,
            "priority": item.priority.value,
            "timestamp": item.timestamp,
            "tags": list(item.tags),
            "metadata": item.metadata,
            "relevance_score": item.relevance_score,
            "access_count": item.access_count,
            "last_accessed": item.last_accessed,
            "related_items": list(item.related_items),
            "parent_id": item.parent_id,
            "children_ids": list(item.children_ids)
        }
    
    def _deserialize_context_item(self, data: Dict[str, Any]) -> ContextItem:
        """Deserialize a context item from storage."""
        return ContextItem(
            id=data["id"],
            content=data["content"],
            context_type=ContextType(data["context_type"]),
            priority=ContextPriority(data["priority"]),
            timestamp=data["timestamp"],
            tags=set(data["tags"]),
            metadata=data["metadata"],
            relevance_score=data.get("relevance_score", 0.0),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed", data["timestamp"]),
            related_items=set(data.get("related_items", [])),
            parent_id=data.get("parent_id"),
            children_ids=set(data.get("children_ids", []))
        )
    
    def _serialize_session_summary(self, summary: SessionSummary) -> Dict[str, Any]:
        """Serialize a session summary for storage."""
        return {
            "session_id": summary.session_id,
            "start_time": summary.start_time,
            "end_time": summary.end_time,
            "duration": summary.duration,
            "conversation_turns": summary.conversation_turns,
            "goals_achieved": summary.goals_achieved,
            "decisions_made": summary.decisions_made,
            "errors_encountered": summary.errors_encountered,
            "key_insights": summary.key_insights,
            "context_items_created": summary.context_items_created,
            "summary_text": summary.summary_text
        }
    
    def _deserialize_session_summary(self, data: Dict[str, Any]) -> SessionSummary:
        """Deserialize a session summary from storage."""
        return SessionSummary(
            session_id=data["session_id"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            duration=data["duration"],
            conversation_turns=data["conversation_turns"],
            goals_achieved=data["goals_achieved"],
            decisions_made=data["decisions_made"],
            errors_encountered=data["errors_encountered"],
            key_insights=data["key_insights"],
            context_items_created=data["context_items_created"],
            summary_text=data.get("summary_text", "")
        )
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "context_items": len(self.context_items),
            "sessions": len(self.sessions),
            "storage_path": str(self.storage_path),
            "total_access_count": sum(item.access_count for item in self.context_items.values()),
            "average_relevance": sum(item.relevance_score for item in self.context_items.values()) / max(len(self.context_items), 1)
        }


class SemanticIndexer:
    """Provides semantic indexing and retrieval of context information."""
    
    def __init__(self):
        # Simple keyword-based indexing for now
        # In a real implementation, you'd use embeddings or other semantic techniques
        self.keyword_index: Dict[str, Set[str]] = {}  # keyword -> set of item_ids
        self.item_keywords: Dict[str, Set[str]] = {}  # item_id -> set of keywords
        
        logger.info("Initialized SemanticIndexer")
    
    def index_context_item(self, item: ContextItem) -> None:
        """Index a context item for semantic search."""
        keywords = self._extract_keywords(item)
        self.item_keywords[item.id] = keywords
        
        for keyword in keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()
            self.keyword_index[keyword].add(item.id)
    
    def search_semantic(self, query: str, limit: int = 10) -> List[str]:
        """
        Perform semantic search and return item IDs.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of item IDs ranked by relevance
        """
        query_keywords = self._extract_keywords_from_text(query)
        
        # Score items based on keyword overlap
        item_scores: Dict[str, float] = {}
        
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for item_id in self.keyword_index[keyword]:
                    if item_id not in item_scores:
                        item_scores[item_id] = 0.0
                    
                    # Simple TF-IDF-like scoring
                    tf = 1.0  # Term frequency (simplified)
                    idf = len(self.item_keywords) / len(self.keyword_index[keyword])
                    item_scores[item_id] += tf * idf
        
        # Sort by score and return top results
        sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        return [item_id for item_id, score in sorted_items[:limit]]
    
    def find_related_items(self, item_id: str, limit: int = 5) -> List[str]:
        """Find items related to the given item."""
        if item_id not in self.item_keywords:
            return []
        
        item_keywords = self.item_keywords[item_id]
        related_scores: Dict[str, float] = {}
        
        for keyword in item_keywords:
            if keyword in self.keyword_index:
                for related_id in self.keyword_index[keyword]:
                    if related_id != item_id:
                        if related_id not in related_scores:
                            related_scores[related_id] = 0.0
                        related_scores[related_id] += 1.0
        
        # Calculate similarity based on shared keywords
        for related_id, score in related_scores.items():
            related_keywords = self.item_keywords.get(related_id, set())
            shared_keywords = len(item_keywords.intersection(related_keywords))
            total_keywords = len(item_keywords.union(related_keywords))
            
            if total_keywords > 0:
                similarity = shared_keywords / total_keywords
                related_scores[related_id] = similarity
        
        # Sort and return top results
        sorted_related = sorted(related_scores.items(), key=lambda x: x[1], reverse=True)
        return [item_id for item_id, score in sorted_related[:limit]]
    
    def _extract_keywords(self, item: ContextItem) -> Set[str]:
        """Extract keywords from a context item."""
        text = str(item.content)
        keywords = self._extract_keywords_from_text(text)
        
        # Add tags as keywords
        keywords.update(item.tags)
        
        # Add metadata keywords
        for key, value in item.metadata.items():
            keywords.add(key.lower())
            if isinstance(value, str):
                keywords.update(self._extract_keywords_from_text(value))
        
        return keywords
    
    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract keywords from text."""
        # Simple keyword extraction (in practice, you'd use NLP libraries)
        import re
        
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}
        
        return keywords
    
    def remove_item(self, item_id: str) -> None:
        """Remove an item from the index."""
        if item_id in self.item_keywords:
            keywords = self.item_keywords[item_id]
            
            for keyword in keywords:
                if keyword in self.keyword_index:
                    self.keyword_index[keyword].discard(item_id)
                    if not self.keyword_index[keyword]:
                        del self.keyword_index[keyword]
            
            del self.item_keywords[item_id]


class ProjectEvolutionTracker:
    """Tracks long-term project evolution and provides insights."""
    
    def __init__(self):
        self.project_timeline: List[Dict[str, Any]] = []
        self.milestones: List[Dict[str, Any]] = []
        self.patterns: Dict[str, Any] = {}
        
        logger.info("Initialized ProjectEvolutionTracker")
    
    def track_event(
        self,
        event_type: str,
        description: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Track a project evolution event."""
        event = {
            "id": str(uuid4()),
            "timestamp": time.time(),
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {}
        }
        
        self.project_timeline.append(event)
        self._update_patterns(event)
    
    def add_milestone(
        self,
        name: str,
        description: str,
        achievement_data: Dict[str, Any] = None
    ) -> None:
        """Add a project milestone."""
        milestone = {
            "id": str(uuid4()),
            "timestamp": time.time(),
            "name": name,
            "description": description,
            "achievement_data": achievement_data or {}
        }
        
        self.milestones.append(milestone)
    
    def get_project_insights(self) -> Dict[str, Any]:
        """Get insights about project evolution."""
        if not self.project_timeline:
            return {"insights": [], "patterns": {}, "recommendations": []}
        
        insights = []
        recommendations = []
        
        # Analyze activity patterns
        recent_events = [e for e in self.project_timeline if time.time() - e["timestamp"] < 7 * 24 * 60 * 60]  # Last week
        
        if len(recent_events) > 10:
            insights.append("High development activity in the past week")
            recommendations.append("Consider code review and testing to maintain quality")
        
        # Analyze error patterns
        error_events = [e for e in self.project_timeline if e["event_type"] == "error"]
        if len(error_events) > len(self.project_timeline) * 0.2:
            insights.append("High error rate detected")
            recommendations.append("Focus on debugging and error prevention")
        
        # Analyze milestone progress
        recent_milestones = [m for m in self.milestones if time.time() - m["timestamp"] < 30 * 24 * 60 * 60]  # Last month
        if recent_milestones:
            insights.append(f"Achieved {len(recent_milestones)} milestones in the past month")
        else:
            recommendations.append("Consider setting and tracking development milestones")
        
        return {
            "insights": insights,
            "patterns": self.patterns,
            "recommendations": recommendations,
            "timeline_length": len(self.project_timeline),
            "milestones_count": len(self.milestones)
        }
    
    def _update_patterns(self, event: Dict[str, Any]) -> None:
        """Update detected patterns based on new event."""
        event_type = event["event_type"]
        
        if event_type not in self.patterns:
            self.patterns[event_type] = {
                "count": 0,
                "frequency": 0.0,
                "last_occurrence": 0.0
            }
        
        pattern = self.patterns[event_type]
        pattern["count"] += 1
        pattern["last_occurrence"] = event["timestamp"]
        
        # Calculate frequency (events per day)
        if len(self.project_timeline) > 1:
            time_span = self.project_timeline[-1]["timestamp"] - self.project_timeline[0]["timestamp"]
            if time_span > 0:
                pattern["frequency"] = pattern["count"] / (time_span / (24 * 60 * 60))


class ContextEngine:
    """Main context engine that coordinates all context management components."""
    
    def __init__(self, storage_path: Path):
        self.memory_manager = PersistentMemoryManager(storage_path)
        self.semantic_indexer = SemanticIndexer()
        self.evolution_tracker = ProjectEvolutionTracker()
        
        # Initialize indexer with existing items
        for item in self.memory_manager.context_items.values():
            self.semantic_indexer.index_context_item(item)
        
        logger.info("Initialized ContextEngine")
    
    async def store_context(
        self,
        content: Any,
        context_type: ContextType,
        tags: Set[str] = None,
        priority: ContextPriority = ContextPriority.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> ContextItem:
        """Store new context information."""
        item = ContextItem(
            content=content,
            context_type=context_type,
            priority=priority,
            tags=tags or set(),
            metadata=metadata or {}
        )
        
        # Store in persistent memory
        self.memory_manager.store_context_item(item)
        
        # Index for semantic search
        self.semantic_indexer.index_context_item(item)
        
        # Track evolution event
        self.evolution_tracker.track_event(
            event_type=f"context_{context_type.value}",
            description=f"Added {context_type.value} context",
            metadata={"item_id": item.id}
        )
        
        return item
    
    async def retrieve_relevant_context(
        self,
        query: str,
        context_types: Optional[List[ContextType]] = None,
        limit: int = 10
    ) -> ContextBundle:
        """Retrieve relevant context for a query."""
        # Semantic search
        semantic_results = self.semantic_indexer.search_semantic(query, limit * 2)
        
        # Get context items
        relevant_items = []
        for item_id in semantic_results:
            item = self.memory_manager.retrieve_context_item(item_id)
            if item:
                # Filter by type if specified
                if context_types and item.context_type not in context_types:
                    continue
                
                # Calculate relevance score
                item.relevance_score = self._calculate_relevance(item, query)
                relevant_items.append(item)
        
        # Sort by relevance and recency
        relevant_items.sort(key=lambda x: (x.relevance_score, x.timestamp), reverse=True)
        relevant_items = relevant_items[:limit]
        
        # Create context bundle
        bundle = ContextBundle(
            name=f"Context for: {query[:50]}...",
            description=f"Relevant context retrieved for query: {query}",
            items=relevant_items,
            relevance_score=sum(item.relevance_score for item in relevant_items) / max(len(relevant_items), 1)
        )
        
        return bundle
    
    async def summarize_session(
        self,
        session_id: str,
        start_time: float,
        end_time: float,
        conversation_turns: int,
        context_items: List[ContextItem]
    ) -> SessionSummary:
        """Create a summary of a session."""
        duration = end_time - start_time
        
        # Extract key information from context items
        goals_achieved = []
        decisions_made = []
        errors_encountered = []
        key_insights = []
        
        for item in context_items:
            if item.context_type == ContextType.GOAL:
                goals_achieved.append(str(item.content))
            elif item.context_type == ContextType.DECISION:
                decisions_made.append(str(item.content))
            elif item.context_type == ContextType.ERROR:
                errors_encountered.append(str(item.content))
            elif item.context_type == ContextType.SUCCESS:
                key_insights.append(str(item.content))
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            duration, conversation_turns, goals_achieved, decisions_made, errors_encountered
        )
        
        summary = SessionSummary(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            conversation_turns=conversation_turns,
            goals_achieved=goals_achieved,
            decisions_made=decisions_made,
            errors_encountered=errors_encountered,
            key_insights=key_insights,
            context_items_created=len(context_items),
            summary_text=summary_text
        )
        
        # Store summary
        self.memory_manager.store_session_summary(summary)
        
        return summary
    
    def get_project_insights(self) -> Dict[str, Any]:
        """Get comprehensive project insights."""
        evolution_insights = self.evolution_tracker.get_project_insights()
        storage_stats = self.memory_manager.get_storage_stats()
        
        return {
            "evolution": evolution_insights,
            "storage": storage_stats,
            "recent_activity": self._analyze_recent_activity(),
            "context_patterns": self._analyze_context_patterns()
        }
    
    def _calculate_relevance(self, item: ContextItem, query: str) -> float:
        """Calculate relevance score for a context item."""
        score = 0.0
        
        # Base score from semantic similarity (simplified)
        content_str = str(item.content).lower()
        query_lower = query.lower()
        
        # Simple keyword matching
        query_words = set(query_lower.split())
        content_words = set(content_str.split())
        
        if query_words and content_words:
            overlap = len(query_words.intersection(content_words))
            score += overlap / len(query_words)
        
        # Boost score based on priority
        priority_boost = {
            ContextPriority.LOW: 0.0,
            ContextPriority.MEDIUM: 0.1,
            ContextPriority.HIGH: 0.2,
            ContextPriority.CRITICAL: 0.3
        }.get(item.priority, 0.0)
        
        score += priority_boost
        
        # Boost score based on recency (items from last 24 hours get boost)
        if time.time() - item.timestamp < 24 * 60 * 60:
            score += 0.1
        
        # Boost score based on access frequency
        if item.access_count > 0:
            score += min(item.access_count * 0.01, 0.1)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _generate_summary_text(
        self,
        duration: float,
        conversation_turns: int,
        goals_achieved: List[str],
        decisions_made: List[str],
        errors_encountered: List[str]
    ) -> str:
        """Generate human-readable summary text."""
        duration_minutes = int(duration / 60)
        
        summary_parts = [
            f"Session lasted {duration_minutes} minutes with {conversation_turns} conversation turns."
        ]
        
        if goals_achieved:
            summary_parts.append(f"Achieved {len(goals_achieved)} goals: {', '.join(goals_achieved[:3])}{'...' if len(goals_achieved) > 3 else ''}.")
        
        if decisions_made:
            summary_parts.append(f"Made {len(decisions_made)} key decisions.")
        
        if errors_encountered:
            summary_parts.append(f"Encountered {len(errors_encountered)} errors that were addressed.")
        
        return " ".join(summary_parts)
    
    def _analyze_recent_activity(self) -> Dict[str, Any]:
        """Analyze recent context activity."""
        recent_items = self.memory_manager.get_recent_context_items(50)
        
        # Count by type
        type_counts = {}
        for item in recent_items:
            type_name = item.context_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "recent_items_count": len(recent_items),
            "type_distribution": type_counts,
            "most_active_type": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }
    
    def _analyze_context_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in context usage."""
        all_items = list(self.memory_manager.context_items.values())
        
        if not all_items:
            return {}
        
        # Analyze access patterns
        most_accessed = max(all_items, key=lambda x: x.access_count)
        avg_access_count = sum(item.access_count for item in all_items) / len(all_items)
        
        # Analyze tag patterns
        all_tags = set()
        for item in all_items:
            all_tags.update(item.tags)
        
        return {
            "total_items": len(all_items),
            "most_accessed_item": {
                "id": most_accessed.id,
                "access_count": most_accessed.access_count,
                "type": most_accessed.context_type.value
            },
            "average_access_count": avg_access_count,
            "unique_tags": len(all_tags),
            "common_tags": list(all_tags)[:10]  # Top 10 tags
        }