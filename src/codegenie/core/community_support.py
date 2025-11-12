"""
Community Support System for CodeGenie
Facilitates community interaction and support
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class SupportTicket:
    """Represents a support ticket"""
    ticket_id: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    user_id: str
    attachments: List[str]
    responses: List[Dict[str, Any]]


class CommunitySupport:
    """Manages community support features"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.support_dir = data_dir / "support"
        self.support_dir.mkdir(parents=True, exist_ok=True)
        self.tickets_dir = self.support_dir / "tickets"
        self.tickets_dir.mkdir(parents=True, exist_ok=True)
    
    def create_ticket(
        self,
        title: str,
        description: str,
        category: str,
        priority: str = "medium"
    ) -> str:
        """Create a new support ticket"""
        import uuid
        
        ticket_id = str(uuid.uuid4())[:8]
        
        ticket = SupportTicket(
            ticket_id=ticket_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status="open",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            user_id=self._get_user_id(),
            attachments=[],
            responses=[]
        )
        
        self._save_ticket(ticket)
        return ticket_id
    
    def _get_user_id(self) -> str:
        """Get anonymous user ID"""
        user_id_file = self.support_dir / "user_id"
        
        if user_id_file.exists():
            return user_id_file.read_text().strip()
        
        import platform
        machine_id = f"{platform.node()}-{platform.machine()}"
        user_id = hashlib.sha256(machine_id.encode()).hexdigest()[:16]
        
        user_id_file.write_text(user_id)
        return user_id
    
    def _save_ticket(self, ticket: SupportTicket):
        """Save ticket to file"""
        ticket_file = self.tickets_dir / f"{ticket.ticket_id}.json"
        
        with open(ticket_file, 'w') as f:
            json.dump(asdict(ticket), f, indent=2)
    
    def get_ticket(self, ticket_id: str) -> Optional[SupportTicket]:
        """Get ticket by ID"""
        ticket_file = self.tickets_dir / f"{ticket_id}.json"
        
        if not ticket_file.exists():
            return None
        
        with open(ticket_file) as f:
            data = json.load(f)
            return SupportTicket(**data)
    
    def update_ticket(self, ticket_id: str, updates: Dict[str, Any]):
        """Update ticket"""
        ticket = self.get_ticket(ticket_id)
        
        if not ticket:
            return False
        
        for key, value in updates.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        
        ticket.updated_at = datetime.now().isoformat()
        self._save_ticket(ticket)
        return True
    
    def add_response(self, ticket_id: str, response: str, author: str = "user"):
        """Add response to ticket"""
        ticket = self.get_ticket(ticket_id)
        
        if not ticket:
            return False
        
        ticket.responses.append({
            "author": author,
            "message": response,
            "timestamp": datetime.now().isoformat()
        })
        
        ticket.updated_at = datetime.now().isoformat()
        self._save_ticket(ticket)
        return True
    
    def list_tickets(self, status: Optional[str] = None) -> List[SupportTicket]:
        """List tickets, optionally filtered by status"""
        tickets = []
        
        for ticket_file in self.tickets_dir.glob("*.json"):
            with open(ticket_file) as f:
                data = json.load(f)
                ticket = SupportTicket(**data)
                
                if status is None or ticket.status == status:
                    tickets.append(ticket)
        
        return sorted(tickets, key=lambda t: t.created_at, reverse=True)
    
    def get_faq(self) -> List[Dict[str, str]]:
        """Get frequently asked questions"""
        return [
            {
                "question": "How do I install CodeGenie?",
                "answer": "Run: curl -fsSL https://codegenie.dev/install.sh | bash",
                "category": "installation"
            },
            {
                "question": "How do I update CodeGenie?",
                "answer": "Run: ./scripts/update.sh or pip install --upgrade codegenie",
                "category": "installation"
            },
            {
                "question": "Why is CodeGenie slow?",
                "answer": "Try using a smaller model (llama3.1:8b) or enable caching in config",
                "category": "performance"
            },
            {
                "question": "How do I enable autonomous mode?",
                "answer": "Type: /autonomous on",
                "category": "features"
            },
            {
                "question": "How do I use specialized agents?",
                "answer": "Prefix your request with @agent_name, e.g., @security review this code",
                "category": "features"
            },
            {
                "question": "Where are my logs?",
                "answer": "Logs are in ~/.codegenie/logs/codegenie.log",
                "category": "troubleshooting"
            },
            {
                "question": "How do I report a bug?",
                "answer": "Use: codegenie report-bug or visit github.com/your-org/codegenie/issues",
                "category": "support"
            }
        ]
    
    def search_faq(self, query: str) -> List[Dict[str, str]]:
        """Search FAQ"""
        query_lower = query.lower()
        results = []
        
        for faq in self.get_faq():
            if (query_lower in faq["question"].lower() or
                query_lower in faq["answer"].lower()):
                results.append(faq)
        
        return results
    
    def get_community_resources(self) -> Dict[str, Any]:
        """Get community resources"""
        return {
            "documentation": {
                "user_guide": "docs/USER_GUIDE.md",
                "api_reference": "docs/API_REFERENCE.md",
                "tutorials": "docs/TUTORIALS.md",
                "troubleshooting": "docs/TROUBLESHOOTING.md",
                "faq": "docs/FAQ.md"
            },
            "community": {
                "discord": "https://discord.gg/codegenie",
                "forum": "https://community.codegenie.dev",
                "github": "https://github.com/your-org/codegenie"
            },
            "support": {
                "email": "support@codegenie.dev",
                "twitter": "@codegenie_dev"
            },
            "learning": {
                "video_tutorials": "docs/VIDEO_TUTORIALS.md",
                "examples": "examples/",
                "blog": "https://blog.codegenie.dev"
            }
        }
    
    def generate_support_report(self) -> Dict[str, Any]:
        """Generate support statistics report"""
        tickets = self.list_tickets()
        
        stats = {
            "total_tickets": len(tickets),
            "open_tickets": len([t for t in tickets if t.status == "open"]),
            "closed_tickets": len([t for t in tickets if t.status == "closed"]),
            "by_category": {},
            "by_priority": {},
            "average_response_time": 0
        }
        
        for ticket in tickets:
            # Count by category
            stats["by_category"][ticket.category] = \
                stats["by_category"].get(ticket.category, 0) + 1
            
            # Count by priority
            stats["by_priority"][ticket.priority] = \
                stats["by_priority"].get(ticket.priority, 0) + 1
        
        return stats


class KnowledgeBase:
    """Community knowledge base"""
    
    def __init__(self, data_dir: Path):
        self.kb_dir = data_dir / "knowledge_base"
        self.kb_dir.mkdir(parents=True, exist_ok=True)
    
    def add_article(self, title: str, content: str, category: str, tags: List[str]):
        """Add article to knowledge base"""
        import uuid
        
        article_id = str(uuid.uuid4())[:8]
        
        article = {
            "id": article_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags,
            "created_at": datetime.now().isoformat(),
            "views": 0,
            "helpful_count": 0
        }
        
        article_file = self.kb_dir / f"{article_id}.json"
        with open(article_file, 'w') as f:
            json.dump(article, f, indent=2)
        
        return article_id
    
    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get article by ID"""
        article_file = self.kb_dir / f"{article_id}.json"
        
        if not article_file.exists():
            return None
        
        with open(article_file) as f:
            article = json.load(f)
        
        # Increment view count
        article["views"] += 1
        with open(article_file, 'w') as f:
            json.dump(article, f, indent=2)
        
        return article
    
    def search_articles(self, query: str) -> List[Dict[str, Any]]:
        """Search articles"""
        query_lower = query.lower()
        results = []
        
        for article_file in self.kb_dir.glob("*.json"):
            with open(article_file) as f:
                article = json.load(f)
            
            if (query_lower in article["title"].lower() or
                query_lower in article["content"].lower() or
                any(query_lower in tag.lower() for tag in article["tags"])):
                results.append(article)
        
        return sorted(results, key=lambda a: a["views"], reverse=True)
    
    def mark_helpful(self, article_id: str):
        """Mark article as helpful"""
        article = self.get_article(article_id)
        
        if article:
            article["helpful_count"] += 1
            article_file = self.kb_dir / f"{article_id}.json"
            with open(article_file, 'w') as f:
                json.dump(article, f, indent=2)
