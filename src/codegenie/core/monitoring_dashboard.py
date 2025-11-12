"""
Monitoring Dashboard for CodeGenie
Provides real-time monitoring and analytics visualization
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict


class MonitoringDashboard:
    """Real-time monitoring dashboard for CodeGenie"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.telemetry_dir = data_dir / "telemetry"
        self.metrics_dir = data_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_sessions": self._count_active_sessions(),
            "tasks_in_progress": self._count_tasks_in_progress(),
            "model_usage": self._get_model_usage(),
            "system_health": self._get_system_health()
        }
    
    def _count_active_sessions(self) -> int:
        """Count currently active sessions"""
        sessions_dir = self.data_dir / "sessions"
        if not sessions_dir.exists():
            return 0
        
        active = 0
        cutoff = datetime.now() - timedelta(hours=1)
        
        for session_file in sessions_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                if mtime > cutoff:
                    active += 1
            except:
                pass
        
        return active
    
    def _count_tasks_in_progress(self) -> int:
        """Count tasks currently in progress"""
        # This would integrate with the workflow engine
        return 0  # Placeholder
    
    def _get_model_usage(self) -> Dict[str, int]:
        """Get model usage statistics"""
        usage = defaultdict(int)
        
        if not self.telemetry_dir.exists():
            return dict(usage)
        
        today = datetime.now().strftime('%Y%m%d')
        events_file = self.telemetry_dir / f"events_{today}.jsonl"
        
        if events_file.exists():
            with open(events_file) as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event["event_type"] == "model_usage":
                            model = event["data"].get("model_name", "unknown")
                            usage[model] += 1
                    except:
                        pass
        
        return dict(usage)
    
    def _get_system_health(self) -> Dict[str, str]:
        """Get system health status"""
        return {
            "ollama": "healthy",
            "models": "healthy",
            "storage": "healthy",
            "overall": "healthy"
        }
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        metrics = {
            "task_completion_rate": 0.0,
            "average_task_duration": 0.0,
            "error_rate": 0.0,
            "model_response_time": 0.0,
            "tasks_completed": 0,
            "tasks_failed": 0
        }
        
        if not self.telemetry_dir.exists():
            return metrics
        
        task_durations = []
        tasks_completed = 0
        tasks_failed = 0
        
        for events_file in self.telemetry_dir.glob("events_*.jsonl"):
            with open(events_file) as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event["timestamp"])
                        
                        if event_time < cutoff:
                            continue
                        
                        if event["event_type"] == "task_execution":
                            duration = event["data"].get("duration_seconds", 0)
                            task_durations.append(duration)
                            
                            if event["data"].get("success"):
                                tasks_completed += 1
                            else:
                                tasks_failed += 1
                    except:
                        pass
        
        total_tasks = tasks_completed + tasks_failed
        
        if total_tasks > 0:
            metrics["task_completion_rate"] = tasks_completed / total_tasks
            metrics["error_rate"] = tasks_failed / total_tasks
        
        if task_durations:
            metrics["average_task_duration"] = sum(task_durations) / len(task_durations)
        
        metrics["tasks_completed"] = tasks_completed
        metrics["tasks_failed"] = tasks_failed
        
        return metrics
    
    def get_usage_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get usage trends over the last N days"""
        trends = {
            "daily_usage": [],
            "feature_usage": defaultdict(int),
            "agent_usage": defaultdict(int),
            "peak_hours": defaultdict(int)
        }
        
        if not self.telemetry_dir.exists():
            return trends
        
        cutoff = datetime.now() - timedelta(days=days)
        daily_counts = defaultdict(int)
        
        for events_file in self.telemetry_dir.glob("events_*.jsonl"):
            with open(events_file) as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event["timestamp"])
                        
                        if event_time < cutoff:
                            continue
                        
                        # Daily usage
                        day = event_time.strftime('%Y-%m-%d')
                        daily_counts[day] += 1
                        
                        # Peak hours
                        hour = event_time.hour
                        trends["peak_hours"][hour] += 1
                        
                        # Feature usage
                        if event["event_type"] == "feature_usage":
                            feature = event["data"].get("feature_name")
                            if feature:
                                trends["feature_usage"][feature] += 1
                        
                        # Agent usage
                        if event["event_type"] == "agent_usage":
                            agent = event["data"].get("agent_name")
                            if agent:
                                trends["agent_usage"][agent] += 1
                    except:
                        pass
        
        # Convert daily counts to list
        trends["daily_usage"] = [
            {"date": date, "count": count}
            for date, count in sorted(daily_counts.items())
        ]
        
        # Convert defaultdicts to regular dicts
        trends["feature_usage"] = dict(trends["feature_usage"])
        trends["agent_usage"] = dict(trends["agent_usage"])
        trends["peak_hours"] = dict(trends["peak_hours"])
        
        return trends
    
    def generate_report(self, output_file: Path):
        """Generate comprehensive monitoring report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "realtime_metrics": self.get_realtime_metrics(),
            "performance_24h": self.get_performance_metrics(hours=24),
            "usage_trends_7d": self.get_usage_trends(days=7)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def print_dashboard(self):
        """Print dashboard to console"""
        print("\n" + "="*70)
        print("CodeGenie Monitoring Dashboard")
        print("="*70)
        
        # Real-time metrics
        realtime = self.get_realtime_metrics()
        print("\n📊 Real-time Metrics:")
        print(f"  Active Sessions: {realtime['active_sessions']}")
        print(f"  Tasks in Progress: {realtime['tasks_in_progress']}")
        print(f"  System Health: {realtime['system_health']['overall']}")
        
        # Model usage
        if realtime['model_usage']:
            print("\n  Model Usage (today):")
            for model, count in realtime['model_usage'].items():
                print(f"    {model}: {count} requests")
        
        # Performance metrics
        perf = self.get_performance_metrics(hours=24)
        print("\n⚡ Performance (Last 24 hours):")
        print(f"  Tasks Completed: {perf['tasks_completed']}")
        print(f"  Tasks Failed: {perf['tasks_failed']}")
        print(f"  Completion Rate: {perf['task_completion_rate']*100:.1f}%")
        print(f"  Average Duration: {perf['average_task_duration']:.1f}s")
        print(f"  Error Rate: {perf['error_rate']*100:.1f}%")
        
        # Usage trends
        trends = self.get_usage_trends(days=7)
        print("\n📈 Usage Trends (Last 7 days):")
        
        if trends['daily_usage']:
            print("  Daily Usage:")
            for day_data in trends['daily_usage'][-7:]:
                print(f"    {day_data['date']}: {day_data['count']} events")
        
        if trends['feature_usage']:
            print("\n  Top Features:")
            sorted_features = sorted(
                trends['feature_usage'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for feature, count in sorted_features:
                print(f"    {feature}: {count} uses")
        
        if trends['agent_usage']:
            print("\n  Agent Usage:")
            for agent, count in sorted(trends['agent_usage'].items(), key=lambda x: x[1], reverse=True):
                print(f"    {agent}: {count} tasks")
        
        print("\n" + "="*70 + "\n")


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.alerts_dir = data_dir / "alerts"
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        
        # Check disk space
        import shutil
        try:
            usage = shutil.disk_usage(str(self.data_dir))
            free_gb = usage.free / (1024**3)
            
            if free_gb < 5:
                alerts.append({
                    "severity": "critical",
                    "type": "disk_space",
                    "message": f"Low disk space: {free_gb:.1f}GB remaining",
                    "action": "Free up disk space or clean cache"
                })
            elif free_gb < 10:
                alerts.append({
                    "severity": "warning",
                    "type": "disk_space",
                    "message": f"Disk space running low: {free_gb:.1f}GB remaining",
                    "action": "Consider freeing up disk space"
                })
        except:
            pass
        
        # Check for high error rate
        dashboard = MonitoringDashboard(self.data_dir)
        perf = dashboard.get_performance_metrics(hours=1)
        
        if perf['error_rate'] > 0.5:
            alerts.append({
                "severity": "critical",
                "type": "high_error_rate",
                "message": f"High error rate: {perf['error_rate']*100:.1f}%",
                "action": "Check error logs and system health"
            })
        elif perf['error_rate'] > 0.2:
            alerts.append({
                "severity": "warning",
                "type": "elevated_error_rate",
                "message": f"Elevated error rate: {perf['error_rate']*100:.1f}%",
                "action": "Monitor system for issues"
            })
        
        return alerts
    
    def save_alert(self, alert: Dict[str, Any]):
        """Save alert to file"""
        alert_file = self.alerts_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        alert["timestamp"] = datetime.now().isoformat()
        
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts from the last hour"""
        cutoff = datetime.now() - timedelta(hours=1)
        alerts = []
        
        for alert_file in self.alerts_dir.glob("alert_*.json"):
            try:
                mtime = datetime.fromtimestamp(alert_file.stat().st_mtime)
                if mtime > cutoff:
                    with open(alert_file) as f:
                        alerts.append(json.load(f))
            except:
                pass
        
        return alerts
