"""
Telemetry and Analytics System for CodeGenie
Collects anonymous usage data to improve the product (opt-in only)
"""

import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TelemetryEvent:
    """Represents a telemetry event"""
    event_type: str
    timestamp: str
    session_id: str
    user_id: str  # Anonymous hash
    data: Dict[str, Any]
    version: str


class TelemetryManager:
    """Manages telemetry collection and reporting"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.telemetry_dir = config_dir.parent.parent / ".codegenie" / "telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        self.enabled = self._check_enabled()
        self.user_id = self._get_or_create_user_id()
        self.session_id = str(uuid.uuid4())
        
    def _check_enabled(self) -> bool:
        """Check if telemetry is enabled"""
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            import yaml
            with open(config_file) as f:
                config = yaml.safe_load(f)
                return config.get("telemetry", {}).get("enabled", False)
        return False
    
    def _get_or_create_user_id(self) -> str:
        """Get or create anonymous user ID"""
        user_id_file = self.telemetry_dir / "user_id"
        
        if user_id_file.exists():
            return user_id_file.read_text().strip()
        
        # Create anonymous user ID (hash of machine ID)
        import platform
        machine_id = f"{platform.node()}-{platform.machine()}"
        user_id = hashlib.sha256(machine_id.encode()).hexdigest()[:16]
        
        user_id_file.write_text(user_id)
        return user_id
    
    def track_event(self, event_type: str, data: Dict[str, Any]):
        """Track a telemetry event"""
        if not self.enabled:
            return
        
        event = TelemetryEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_id=self.user_id,
            data=self._sanitize_data(data),
            version=self._get_version()
        )
        
        self._save_event(event)
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from data"""
        sanitized = {}
        
        # List of keys to exclude
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'api_key',
            'auth', 'credential', 'private', 'email', 'username'
        }
        
        for key, value in data.items():
            # Skip sensitive keys
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                continue
            
            # Sanitize nested dicts
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            # Sanitize file paths
            elif isinstance(value, (str, Path)) and ('/' in str(value) or '\\' in str(value)):
                sanitized[key] = "<path>"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _save_event(self, event: TelemetryEvent):
        """Save event to local storage"""
        events_file = self.telemetry_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(events_file, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')
    
    def _get_version(self) -> str:
        """Get CodeGenie version"""
        try:
            from codegenie import __version__
            return __version__
        except:
            return "unknown"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get local usage statistics"""
        stats = {
            "total_events": 0,
            "events_by_type": {},
            "sessions": set(),
            "date_range": {"start": None, "end": None}
        }
        
        for events_file in self.telemetry_dir.glob("events_*.jsonl"):
            with open(events_file) as f:
                for line in f:
                    event = json.loads(line)
                    stats["total_events"] += 1
                    
                    event_type = event["event_type"]
                    stats["events_by_type"][event_type] = \
                        stats["events_by_type"].get(event_type, 0) + 1
                    
                    stats["sessions"].add(event["session_id"])
                    
                    timestamp = event["timestamp"]
                    if stats["date_range"]["start"] is None or timestamp < stats["date_range"]["start"]:
                        stats["date_range"]["start"] = timestamp
                    if stats["date_range"]["end"] is None or timestamp > stats["date_range"]["end"]:
                        stats["date_range"]["end"] = timestamp
        
        stats["sessions"] = len(stats["sessions"])
        return stats


class UsageAnalytics:
    """Analyzes usage patterns for insights"""
    
    def __init__(self, telemetry_manager: TelemetryManager):
        self.telemetry = telemetry_manager
    
    def track_task_execution(self, task_type: str, duration: float, success: bool):
        """Track task execution"""
        self.telemetry.track_event("task_execution", {
            "task_type": task_type,
            "duration_seconds": duration,
            "success": success
        })
    
    def track_agent_usage(self, agent_name: str, task_type: str):
        """Track agent usage"""
        self.telemetry.track_event("agent_usage", {
            "agent_name": agent_name,
            "task_type": task_type
        })
    
    def track_model_usage(self, model_name: str, tokens: int, duration: float):
        """Track model usage"""
        self.telemetry.track_event("model_usage", {
            "model_name": model_name,
            "tokens": tokens,
            "duration_seconds": duration
        })
    
    def track_error(self, error_type: str, error_message: str):
        """Track error occurrence"""
        self.telemetry.track_event("error", {
            "error_type": error_type,
            "error_message": error_message[:200]  # Truncate long messages
        })
    
    def track_feature_usage(self, feature_name: str):
        """Track feature usage"""
        self.telemetry.track_event("feature_usage", {
            "feature_name": feature_name
        })
    
    def track_autonomous_workflow(self, steps: int, duration: float, success: bool):
        """Track autonomous workflow execution"""
        self.telemetry.track_event("autonomous_workflow", {
            "steps": steps,
            "duration_seconds": duration,
            "success": success
        })
    
    def get_insights(self) -> Dict[str, Any]:
        """Get usage insights"""
        stats = self.telemetry.get_usage_stats()
        
        insights = {
            "summary": {
                "total_events": stats["total_events"],
                "total_sessions": stats["sessions"],
                "date_range": stats["date_range"]
            },
            "most_used_features": self._get_top_events(stats["events_by_type"], 5),
            "recommendations": self._generate_recommendations(stats)
        }
        
        return insights
    
    def _get_top_events(self, events_by_type: Dict[str, int], limit: int) -> list:
        """Get top N events by count"""
        sorted_events = sorted(events_by_type.items(), key=lambda x: x[1], reverse=True)
        return [{"event": event, "count": count} for event, count in sorted_events[:limit]]
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> list:
        """Generate usage recommendations"""
        recommendations = []
        
        events_by_type = stats["events_by_type"]
        
        # Check if user is using autonomous mode
        if events_by_type.get("autonomous_workflow", 0) == 0:
            recommendations.append({
                "type": "feature",
                "message": "Try autonomous mode for complex tasks: /autonomous on"
            })
        
        # Check if user is using specialized agents
        if events_by_type.get("agent_usage", 0) < 5:
            recommendations.append({
                "type": "feature",
                "message": "Use specialized agents for better results: @architect, @security, @performance"
            })
        
        return recommendations


class FeedbackCollector:
    """Collects user feedback"""
    
    def __init__(self, config_dir: Path):
        self.feedback_dir = config_dir.parent.parent / ".codegenie" / "feedback"
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_feedback(self, feedback_type: str, rating: int, comment: str, context: Dict[str, Any]):
        """Collect user feedback"""
        feedback = {
            "type": feedback_type,
            "rating": rating,
            "comment": comment,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        feedback_file = self.feedback_dir / f"feedback_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(feedback_file, 'a') as f:
            f.write(json.dumps(feedback) + '\n')
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get feedback summary"""
        summary = {
            "total_feedback": 0,
            "average_rating": 0,
            "feedback_by_type": {},
            "recent_feedback": []
        }
        
        all_ratings = []
        
        for feedback_file in self.feedback_dir.glob("feedback_*.jsonl"):
            with open(feedback_file) as f:
                for line in f:
                    feedback = json.loads(line)
                    summary["total_feedback"] += 1
                    all_ratings.append(feedback["rating"])
                    
                    feedback_type = feedback["type"]
                    if feedback_type not in summary["feedback_by_type"]:
                        summary["feedback_by_type"][feedback_type] = []
                    summary["feedback_by_type"][feedback_type].append(feedback)
                    
                    summary["recent_feedback"].append(feedback)
        
        if all_ratings:
            summary["average_rating"] = sum(all_ratings) / len(all_ratings)
        
        # Keep only 10 most recent
        summary["recent_feedback"] = sorted(
            summary["recent_feedback"],
            key=lambda x: x["timestamp"],
            reverse=True
        )[:10]
        
        return summary
