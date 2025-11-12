"""
Comprehensive monitoring and analytics system for CodeGenie AI agents.
Provides logging, metrics collection, performance dashboards, and health monitoring.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import uuid

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """System alert."""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageStats:
    """Usage statistics."""
    feature: str
    usage_count: int
    last_used: datetime
    total_duration: float = 0.0
    error_count: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0


class MetricsCollector:
    """Collects and stores system metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics: deque = deque(maxlen=config.get('max_metrics', 10000))
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.metric_handlers: Dict[str, Callable] = {}
        
        # Database for persistent storage
        self.db_path = Path(config.get('db_path', 'metrics.db'))
        self._init_database()
        
        # Background aggregation
        self._aggregation_task = asyncio.create_task(self._aggregate_metrics())
    
    def _init_database(self) -> None:
        """Initialize metrics database."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tags TEXT,
                    labels TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp 
                ON metrics(name, timestamp)
            ''')
    
    async def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric."""
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            labels=labels or {}
        )
        
        # Add to in-memory storage
        self.metrics.append(metric)
        
        # Store in database
        await self._store_metric_db(metric)
        
        # Call custom handlers
        if name in self.metric_handlers:
            try:
                await self.metric_handlers[name](metric)
            except Exception as e:
                logger.error(f"Metric handler error for {name}: {e}")
    
    async def _store_metric_db(self, metric: Metric) -> None:
        """Store metric in database."""
        
        def store():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO metrics (name, value, metric_type, timestamp, tags, labels)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metric.name,
                    metric.value,
                    metric.metric_type.value,
                    metric.timestamp.isoformat(),
                    json.dumps(metric.tags),
                    json.dumps(metric.labels)
                ))
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, store)
    
    async def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        
        # Get current value
        current = self.aggregated_metrics.get(name, {}).get('value', 0)
        new_value = current + value
        
        await self.record_metric(name, new_value, MetricType.COUNTER, tags)
        
        # Update aggregated value
        self.aggregated_metrics[name]['value'] = new_value
        self.aggregated_metrics[name]['last_updated'] = datetime.now()
    
    async def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        
        await self.record_metric(name, value, MetricType.GAUGE, tags)
        
        # Update aggregated value
        self.aggregated_metrics[name]['value'] = value
        self.aggregated_metrics[name]['last_updated'] = datetime.now()
    
    async def record_timer(
        self,
        name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer metric."""
        
        await self.record_metric(name, duration, MetricType.TIMER, tags)
        
        # Update aggregated statistics
        if name not in self.aggregated_metrics:
            self.aggregated_metrics[name] = {
                'count': 0,
                'total': 0.0,
                'min': float('inf'),
                'max': 0.0,
                'values': deque(maxlen=100)
            }
        
        stats = self.aggregated_metrics[name]
        stats['count'] += 1
        stats['total'] += duration
        stats['min'] = min(stats['min'], duration)
        stats['max'] = max(stats['max'], duration)
        stats['values'].append(duration)
        stats['avg'] = stats['total'] / stats['count']
        stats['last_updated'] = datetime.now()
    
    def register_handler(self, metric_name: str, handler: Callable) -> None:
        """Register a custom handler for a metric."""
        self.metric_handlers[metric_name] = handler
    
    async def get_metrics(
        self,
        name_pattern: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Metric]:
        """Get metrics from storage."""
        
        def query():
            with sqlite3.connect(self.db_path) as conn:
                query_sql = "SELECT * FROM metrics WHERE 1=1"
                params = []
                
                if name_pattern:
                    query_sql += " AND name LIKE ?"
                    params.append(f"%{name_pattern}%")
                
                if start_time:
                    query_sql += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query_sql += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query_sql += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query_sql, params)
                rows = cursor.fetchall()
                
                metrics = []
                for row in rows:
                    metric = Metric(
                        name=row[1],
                        value=row[2],
                        metric_type=MetricType(row[3]),
                        timestamp=datetime.fromisoformat(row[4]),
                        tags=json.loads(row[5]) if row[5] else {},
                        labels=json.loads(row[6]) if row[6] else {}
                    )
                    metrics.append(metric)
                
                return metrics
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, query)
    
    async def _aggregate_metrics(self) -> None:
        """Background task to aggregate metrics."""
        
        while True:
            try:
                # Aggregate metrics every minute
                await asyncio.sleep(60)
                
                # Clean up old aggregated data
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for name, data in list(self.aggregated_metrics.items()):
                    last_updated = data.get('last_updated')
                    if last_updated and last_updated < cutoff_time:
                        del self.aggregated_metrics[name]
                
            except Exception as e:
                logger.error(f"Metrics aggregation error: {e}")
                await asyncio.sleep(60)
    
    def get_aggregated_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current aggregated metrics."""
        return dict(self.aggregated_metrics)


class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_handlers: List[Callable] = []
        
        # Database for persistent storage
        self.db_path = Path(config.get('db_path', 'alerts.db'))
        self._init_database()
        
        # Background processing
        self._processing_task = asyncio.create_task(self._process_alerts())
    
    def _init_database(self) -> None:
        """Initialize alerts database."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0,
                    resolved_at TEXT,
                    metadata TEXT
                )
            ''')
    
    async def create_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new alert."""
        
        alert_id = str(uuid.uuid4())
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            source=source,
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        
        # Store in database
        await self._store_alert_db(alert)
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.info(f"Created alert {alert_id}: {title}")
        return alert_id
    
    async def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """Resolve an alert."""
        
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now()
        alert.metadata['resolution_note'] = resolution_note
        
        # Update database
        await self._update_alert_db(alert)
        
        logger.info(f"Resolved alert {alert_id}")
        return True
    
    async def _store_alert_db(self, alert: Alert) -> None:
        """Store alert in database."""
        
        def store():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO alerts (id, title, description, severity, source, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.id,
                    alert.title,
                    alert.description,
                    alert.severity.value,
                    alert.source,
                    alert.timestamp.isoformat(),
                    json.dumps(alert.metadata)
                ))
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, store)
    
    async def _update_alert_db(self, alert: Alert) -> None:
        """Update alert in database."""
        
        def update():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE alerts 
                    SET resolved = ?, resolved_at = ?, metadata = ?
                    WHERE id = ?
                ''', (
                    1 if alert.resolved else 0,
                    alert.resolved_at.isoformat() if alert.resolved_at else None,
                    json.dumps(alert.metadata),
                    alert.id
                ))
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, update)
    
    async def _send_notifications(self, alert: Alert) -> None:
        """Send alert notifications."""
        
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
    
    def add_notification_handler(self, handler: Callable) -> None:
        """Add a notification handler."""
        self.notification_handlers.append(handler)
    
    def add_alert_rule(
        self,
        name: str,
        condition: Callable,
        severity: AlertSeverity,
        description: str
    ) -> None:
        """Add an alert rule."""
        
        self.alert_rules.append({
            'name': name,
            'condition': condition,
            'severity': severity,
            'description': description
        })
    
    async def _process_alerts(self) -> None:
        """Background task to process alert rules."""
        
        while True:
            try:
                # Process alert rules every 30 seconds
                await asyncio.sleep(30)
                
                for rule in self.alert_rules:
                    try:
                        if await rule['condition']():
                            await self.create_alert(
                                title=f"Alert Rule: {rule['name']}",
                                description=rule['description'],
                                severity=rule['severity'],
                                source="alert_rule"
                            )
                    except Exception as e:
                        logger.error(f"Alert rule processing error: {e}")
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(60)
    
    async def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts from storage."""
        
        def query():
            with sqlite3.connect(self.db_path) as conn:
                query_sql = "SELECT * FROM alerts WHERE 1=1"
                params = []
                
                if severity:
                    query_sql += " AND severity = ?"
                    params.append(severity.value)
                
                if resolved is not None:
                    query_sql += " AND resolved = ?"
                    params.append(1 if resolved else 0)
                
                query_sql += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query_sql, params)
                rows = cursor.fetchall()
                
                alerts = []
                for row in rows:
                    alert = Alert(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        severity=AlertSeverity(row[3]),
                        source=row[4],
                        timestamp=datetime.fromisoformat(row[5]),
                        resolved=bool(row[6]),
                        resolved_at=datetime.fromisoformat(row[7]) if row[7] else None,
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    alerts.append(alert)
                
                return alerts
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, query)


class HealthMonitor:
    """System health monitoring."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, HealthCheck] = {}
        self.overall_status = HealthStatus.HEALTHY
        
        # Background monitoring
        self._monitor_task = asyncio.create_task(self._monitor_health())
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """Register a health check function."""
        self.health_checks[name] = check_func
    
    async def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        
        if name not in self.health_checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check '{name}' not found"
            )
        
        start_time = time.time()
        
        try:
            check_func = self.health_checks[name]
            
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheck):
                result.duration_ms = duration_ms
                return result
            elif isinstance(result, bool):
                return HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    message="Health check passed" if result else "Health check failed",
                    duration_ms=duration_ms
                )
            else:
                return HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=str(result),
                    duration_ms=duration_ms
                )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms
            )
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        
        results = {}
        
        for name in self.health_checks:
            results[name] = await self.run_health_check(name)
        
        # Update overall status
        self._update_overall_status(results)
        
        return results
    
    def _update_overall_status(self, results: Dict[str, HealthCheck]) -> None:
        """Update overall system health status."""
        
        if not results:
            self.overall_status = HealthStatus.HEALTHY
            return
        
        statuses = [check.status for check in results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            self.overall_status = HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            self.overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            self.overall_status = HealthStatus.DEGRADED
        else:
            self.overall_status = HealthStatus.HEALTHY
    
    async def _monitor_health(self) -> None:
        """Background health monitoring."""
        
        while True:
            try:
                # Run health checks every 60 seconds
                await asyncio.sleep(60)
                
                results = await self.run_all_health_checks()
                self.health_status.update(results)
                
                # Log unhealthy checks
                for name, check in results.items():
                    if check.status != HealthStatus.HEALTHY:
                        logger.warning(f"Health check '{name}' is {check.status.value}: {check.message}")
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        
        return {
            'overall_status': self.overall_status.value,
            'checks_count': len(self.health_checks),
            'last_check_time': max(
                (check.timestamp for check in self.health_status.values()),
                default=datetime.now()
            ).isoformat(),
            'unhealthy_checks': [
                name for name, check in self.health_status.items()
                if check.status != HealthStatus.HEALTHY
            ]
        }


class UsageTracker:
    """Tracks feature usage and generates insights."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.usage_stats: Dict[str, UsageStats] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}
        
        # Database for persistent storage
        self.db_path = Path(config.get('db_path', 'usage.db'))
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize usage database."""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration REAL,
                    success INTEGER,
                    metadata TEXT
                )
            ''')
    
    async def track_usage(
        self,
        feature: str,
        event_type: str = "usage",
        duration: Optional[float] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track feature usage."""
        
        # Update in-memory stats
        if feature not in self.usage_stats:
            self.usage_stats[feature] = UsageStats(
                feature=feature,
                usage_count=0,
                last_used=datetime.now()
            )
        
        stats = self.usage_stats[feature]
        stats.usage_count += 1
        stats.last_used = datetime.now()
        
        if duration:
            stats.total_duration += duration
            stats.avg_duration = stats.total_duration / stats.usage_count
        
        if not success:
            stats.error_count += 1
        
        stats.success_rate = (stats.usage_count - stats.error_count) / stats.usage_count
        
        # Store in database
        await self._store_usage_event(feature, event_type, duration, success, metadata)
    
    async def _store_usage_event(
        self,
        feature: str,
        event_type: str,
        duration: Optional[float],
        success: bool,
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Store usage event in database."""
        
        def store():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO usage_events (feature, event_type, timestamp, duration, success, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    feature,
                    event_type,
                    datetime.now().isoformat(),
                    duration,
                    1 if success else 0,
                    json.dumps(metadata) if metadata else None
                ))
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, store)
    
    async def get_usage_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get usage insights for the last N days."""
        
        def query():
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Most used features
                cursor = conn.execute('''
                    SELECT feature, COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY feature
                    ORDER BY usage_count DESC
                    LIMIT 10
                ''', (cutoff_date,))
                
                most_used = [{'feature': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                # Error rates
                cursor = conn.execute('''
                    SELECT feature, 
                           COUNT(*) as total,
                           SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY feature
                ''', (cutoff_date,))
                
                error_rates = []
                for row in cursor.fetchall():
                    feature, total, errors = row
                    error_rate = (errors / total) * 100 if total > 0 else 0
                    error_rates.append({
                        'feature': feature,
                        'error_rate': error_rate,
                        'total_uses': total
                    })
                
                # Average durations
                cursor = conn.execute('''
                    SELECT feature, AVG(duration) as avg_duration
                    FROM usage_events
                    WHERE timestamp >= ? AND duration IS NOT NULL
                    GROUP BY feature
                ''', (cutoff_date,))
                
                avg_durations = [
                    {'feature': row[0], 'avg_duration': row[1]}
                    for row in cursor.fetchall()
                ]
                
                return {
                    'most_used_features': most_used,
                    'error_rates': error_rates,
                    'average_durations': avg_durations
                }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, query)
    
    def get_current_stats(self) -> Dict[str, UsageStats]:
        """Get current usage statistics."""
        return {name: asdict(stats) for name, stats in self.usage_stats.items()}


class MonitoringAnalytics:
    """Main monitoring and analytics system coordinator."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_collector = MetricsCollector(config.get('metrics', {}))
        self.alert_manager = AlertManager(config.get('alerts', {}))
        self.health_monitor = HealthMonitor(config.get('health', {}))
        self.usage_tracker = UsageTracker(config.get('usage', {}))
        
        # Setup default health checks
        self._setup_default_health_checks()
        
        # Setup default alert rules
        self._setup_default_alert_rules()
    
    def _setup_default_health_checks(self) -> None:
        """Setup default system health checks."""
        
        async def cpu_health_check():
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            
            if cpu_usage > 90:
                return HealthCheck(
                    name="cpu_usage",
                    status=HealthStatus.CRITICAL,
                    message=f"CPU usage critical: {cpu_usage:.1f}%"
                )
            elif cpu_usage > 80:
                return HealthCheck(
                    name="cpu_usage",
                    status=HealthStatus.DEGRADED,
                    message=f"CPU usage high: {cpu_usage:.1f}%"
                )
            else:
                return HealthCheck(
                    name="cpu_usage",
                    status=HealthStatus.HEALTHY,
                    message=f"CPU usage normal: {cpu_usage:.1f}%"
                )
        
        async def memory_health_check():
            import psutil
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                return HealthCheck(
                    name="memory_usage",
                    status=HealthStatus.CRITICAL,
                    message=f"Memory usage critical: {memory.percent:.1f}%"
                )
            elif memory.percent > 80:
                return HealthCheck(
                    name="memory_usage",
                    status=HealthStatus.DEGRADED,
                    message=f"Memory usage high: {memory.percent:.1f}%"
                )
            else:
                return HealthCheck(
                    name="memory_usage",
                    status=HealthStatus.HEALTHY,
                    message=f"Memory usage normal: {memory.percent:.1f}%"
                )
        
        async def disk_health_check():
            import psutil
            disk = psutil.disk_usage('/')
            
            if disk.percent > 95:
                return HealthCheck(
                    name="disk_usage",
                    status=HealthStatus.CRITICAL,
                    message=f"Disk usage critical: {disk.percent:.1f}%"
                )
            elif disk.percent > 85:
                return HealthCheck(
                    name="disk_usage",
                    status=HealthStatus.DEGRADED,
                    message=f"Disk usage high: {disk.percent:.1f}%"
                )
            else:
                return HealthCheck(
                    name="disk_usage",
                    status=HealthStatus.HEALTHY,
                    message=f"Disk usage normal: {disk.percent:.1f}%"
                )
        
        self.health_monitor.register_health_check("cpu_usage", cpu_health_check)
        self.health_monitor.register_health_check("memory_usage", memory_health_check)
        self.health_monitor.register_health_check("disk_usage", disk_health_check)
    
    def _setup_default_alert_rules(self) -> None:
        """Setup default alert rules."""
        
        async def high_error_rate_rule():
            # Check if error rate is above threshold
            metrics = self.metrics_collector.get_aggregated_metrics()
            error_rate = metrics.get('error_rate', {}).get('value', 0)
            return error_rate > 0.1  # 10% error rate
        
        async def high_response_time_rule():
            # Check if average response time is too high
            metrics = self.metrics_collector.get_aggregated_metrics()
            response_time = metrics.get('response_time', {}).get('avg', 0)
            return response_time > 5.0  # 5 seconds
        
        self.alert_manager.add_alert_rule(
            name="high_error_rate",
            condition=high_error_rate_rule,
            severity=AlertSeverity.WARNING,
            description="Error rate is above acceptable threshold"
        )
        
        self.alert_manager.add_alert_rule(
            name="high_response_time",
            condition=high_response_time_rule,
            severity=AlertSeverity.WARNING,
            description="Average response time is too high"
        )
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        
        # Get recent metrics
        recent_metrics = await self.metrics_collector.get_metrics(
            start_time=datetime.now() - timedelta(hours=1),
            limit=1000
        )
        
        # Get recent alerts
        recent_alerts = await self.alert_manager.get_alerts(
            resolved=False,
            limit=50
        )
        
        # Get health status
        health_summary = self.health_monitor.get_health_summary()
        
        # Get usage insights
        usage_insights = await self.usage_tracker.get_usage_insights(days=1)
        
        # Get aggregated metrics
        aggregated_metrics = self.metrics_collector.get_aggregated_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health': health_summary,
            'metrics': {
                'recent_count': len(recent_metrics),
                'aggregated': aggregated_metrics
            },
            'alerts': {
                'active_count': len(recent_alerts),
                'recent': [asdict(alert) for alert in recent_alerts[:10]]
            },
            'usage': usage_insights,
            'system_info': {
                'uptime': time.time(),  # Would track actual uptime
                'version': '1.0.0'  # Would get from config
            }
        }
    
    async def cleanup(self) -> None:
        """Clean up monitoring system."""
        
        # Cancel background tasks
        if hasattr(self.metrics_collector, '_aggregation_task'):
            self.metrics_collector._aggregation_task.cancel()
        
        if hasattr(self.alert_manager, '_processing_task'):
            self.alert_manager._processing_task.cancel()
        
        if hasattr(self.health_monitor, '_monitor_task'):
            self.health_monitor._monitor_task.cancel()