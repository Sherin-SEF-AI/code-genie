"""
Memory system for maintaining context and learning from interactions.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MemoryEntry(BaseModel):
    """A single memory entry."""
    
    id: str
    timestamp: float
    type: str  # "conversation", "error", "solution", "pattern", "preference"
    content: Dict[str, Any]
    importance: float = Field(default=1.0, ge=0.0, le=10.0)
    tags: List[str] = Field(default_factory=list)
    accessed_count: int = 0
    last_accessed: Optional[float] = None


class Memory:
    """Memory system for the agent."""
    
    def __init__(self, config, cache_dir: Path):
        self.config = config
        self.cache_dir = cache_dir
        self.memory_file = cache_dir / "memory.json"
        self.entries: Dict[str, MemoryEntry] = {}
        self.max_memory_size = self._parse_size(config.learning.max_memory_size)
        self._load_memory()
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '100MB' to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _load_memory(self) -> None:
        """Load memory from disk."""
        if not self.memory_file.exists():
            return
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for entry_data in data.get('entries', []):
                entry = MemoryEntry(**entry_data)
                self.entries[entry.id] = entry
            
            logger.info(f"Loaded {len(self.entries)} memory entries")
            
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            self.entries = {}
    
    def _save_memory(self) -> None:
        """Save memory to disk."""
        try:
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert entries to dict
            data = {
                'entries': [entry.dict() for entry in self.entries.values()],
                'last_saved': time.time(),
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.entries)} memory entries")
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def add_memory(
        self,
        memory_type: str,
        content: Dict[str, Any],
        importance: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Add a new memory entry."""
        
        entry_id = f"{memory_type}_{int(time.time() * 1000)}"
        
        entry = MemoryEntry(
            id=entry_id,
            timestamp=time.time(),
            type=memory_type,
            content=content,
            importance=importance,
            tags=tags or [],
        )
        
        self.entries[entry_id] = entry
        
        # Check memory size and clean up if needed
        self._cleanup_memory()
        
        # Save to disk
        self._save_memory()
        
        logger.debug(f"Added memory entry: {entry_id}")
        return entry_id
    
    def get_memory(
        self,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[MemoryEntry]:
        """Get memory entries matching criteria."""
        
        results = []
        
        for entry in self.entries.values():
            # Filter by type
            if memory_type and entry.type != memory_type:
                continue
            
            # Filter by importance
            if entry.importance < min_importance:
                continue
            
            # Filter by tags
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            
            results.append(entry)
        
        # Sort by importance and recency
        results.sort(
            key=lambda x: (x.importance, x.timestamp),
            reverse=True
        )
        
        # Update access statistics
        for entry in results[:limit]:
            entry.accessed_count += 1
            entry.last_accessed = time.time()
        
        return results[:limit]
    
    def search_memory(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Search memory entries by content."""
        
        query_lower = query.lower()
        results = []
        
        for entry in self.entries.values():
            # Search in content
            content_str = json.dumps(entry.content, default=str).lower()
            if query_lower in content_str:
                results.append(entry)
                continue
            
            # Search in tags
            if any(query_lower in tag.lower() for tag in entry.tags):
                results.append(entry)
                continue
        
        # Sort by relevance (importance + recency)
        results.sort(
            key=lambda x: (x.importance, x.timestamp),
            reverse=True
        )
        
        # Update access statistics
        for entry in results[:limit]:
            entry.accessed_count += 1
            entry.last_accessed = time.time()
        
        return results[:limit]
    
    def update_memory(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory entry."""
        
        if entry_id not in self.entries:
            return False
        
        entry = self.entries[entry_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        # Save to disk
        self._save_memory()
        
        logger.debug(f"Updated memory entry: {entry_id}")
        return True
    
    def delete_memory(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        
        if entry_id not in self.entries:
            return False
        
        del self.entries[entry_id]
        self._save_memory()
        
        logger.debug(f"Deleted memory entry: {entry_id}")
        return True
    
    def _cleanup_memory(self) -> None:
        """Clean up memory to stay within size limits."""
        
        # Calculate current memory size
        current_size = sum(
            len(json.dumps(entry.dict(), default=str))
            for entry in self.entries.values()
        )
        
        if current_size <= self.max_memory_size:
            return
        
        logger.info(f"Memory size ({current_size}) exceeds limit ({self.max_memory_size}), cleaning up...")
        
        # Sort entries by importance and recency
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda x: (x.importance, x.timestamp),
            reverse=True
        )
        
        # Remove least important entries until under limit
        while current_size > self.max_memory_size and sorted_entries:
            entry = sorted_entries.pop()
            current_size -= len(json.dumps(entry.dict(), default=str))
            del self.entries[entry.id]
        
        logger.info(f"Cleaned up memory, now {len(self.entries)} entries")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        
        stats = {
            "total_entries": len(self.entries),
            "memory_size": sum(
                len(json.dumps(entry.dict(), default=str))
                for entry in self.entries.values()
            ),
            "max_memory_size": self.max_memory_size,
            "types": {},
            "tags": {},
        }
        
        # Count by type
        for entry in self.entries.values():
            stats["types"][entry.type] = stats["types"].get(entry.type, 0) + 1
            
            for tag in entry.tags:
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1
        
        return stats
    
    def add_conversation_memory(
        self,
        user_input: str,
        agent_response: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a conversation to memory."""
        
        content = {
            "user_input": user_input,
            "agent_response": agent_response,
            "context": context or {},
        }
        
        return self.add_memory(
            memory_type="conversation",
            content=content,
            importance=1.0,
            tags=["conversation"],
        )
    
    def add_error_memory(
        self,
        error_message: str,
        solution: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add an error and its solution to memory."""
        
        content = {
            "error_message": error_message,
            "solution": solution,
            "context": context or {},
        }
        
        return self.add_memory(
            memory_type="error",
            content=content,
            importance=2.0,
            tags=["error", "solution"],
        )
    
    def add_pattern_memory(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        success_rate: float = 1.0,
    ) -> str:
        """Add a learned pattern to memory."""
        
        content = {
            "pattern_type": pattern_type,
            "pattern_data": pattern_data,
            "success_rate": success_rate,
        }
        
        importance = 3.0 + success_rate  # Higher importance for successful patterns
        
        return self.add_memory(
            memory_type="pattern",
            content=content,
            importance=importance,
            tags=["pattern", pattern_type],
        )
    
    def add_preference_memory(
        self,
        preference_type: str,
        preference_data: Dict[str, Any],
    ) -> str:
        """Add a user preference to memory."""
        
        content = {
            "preference_type": preference_type,
            "preference_data": preference_data,
        }
        
        return self.add_memory(
            memory_type="preference",
            content=content,
            importance=2.5,
            tags=["preference", preference_type],
        )
