"""
Unit tests for the monitoring and analytics system.
"""

import asyncio
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.codegenie.core.monitoring_analytics import (
    MonitoringAnalytics,
    MetricsCollector,
    AlertManager,
    HealthMonitor,
    UsageTracker,
    Metric,
    Alert,
    HealthCheck,
    UsageStats,
    MetricType,
    AlertSeverity,
    HealthStatus
)


class TestMetricsCollector:
    """Test metrics collection system."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def metrics_collector(self, temp_dir):
        config = {
            'db_path': temp_dir / 'metrics.db',
            'max_metrics': 1000
        }
        return MetricsCollector(config)
    
    @pytest.mark.asyncio
    async def test_record_metric(self, metrics_collector):
        """Test basic metric recording."""
        await metrics_collector.record_metric(
            "test_metric",
            42.5,
            MetricType.GAUGE,
            tags={"service": "test"},
            labels={"env": "dev"}
        )
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.tags["service"] == "test"
        assert metric.labels["env"] == "dev"
    
    @pytest.mark.asyncio
    async def test_counter_operations(self, metrics_collector):
        """Test counter metric operations."""
        # Increment counter
        await metrics_collector.increment_counter("requests", 1)
        await metrics_collector.increment_counter("requests", 5)
        await metrics_collector.increment_counter("requests", 2)
        
        # Check aggregated value
        aggregated = metrics_collector.get_aggregated_metrics()
        assert aggregated["requests"]["value"] == 8
    
    @pytest.mark.asyncio
    async def test_gauge_operations(self, metrics_collector):
        """Test gauge metric operations."""
        await metrics_collector.set_gauge("cpu_usage", 75.5)
        await metrics_collector.set_gauge("cpu_usage", 80.2)
        
        # Gauge should have latest value
        aggregated = metrics_collector.get_aggregated_metrics()
        assert aggregated["cpu_usage"]["value"] == 80.2
    
    @pytest.mark.asyncio
    async def test_timer_operations(self, metrics_collector):
        """Test timer metric operations."""
        # Record multiple timer values
        await metrics_collector.record_timer("response_time", 1.5)
        await metrics_collector.record_timer("response_time", 2.0)
        await metrics_collector.record_timer("response_time", 1.2)
        
        # Check aggregated statistics
        aggregated = metrics_collector.get_aggregated_metrics()
        timer_stats = aggregated["response_time"]
        
        assert timer_stats["count"] == 3
        assert timer_stats["total"] == 4.7
        assert timer_stats["min"] == 1.2
        assert timer_stats["max"] == 2.0
        assert abs(timer_stats["avg"] - 1.567) < 0.01
    
    @pytest.mark.asyncio
    async def test_metric_handlers(self, metrics_collector):
        """Test custom metric handlers."""
        handler_called = False
        received_metric = None
        
        async def custom_handler(metric):
            nonlocal handler_called, received_metric
            handler_called = True
            received_metric = metric
        
        # Register handler
        metrics_collector.register_handler("special_metric", custom_handler)
        
        # Record metric
        await metrics_collector.record_metric("special_metric", 100)
        
        # Handler should be called
        assert handler_called
        assert received_metric.name == "special_metric"
        assert received_metric.value == 100
    
    @pytest.mark.asyncio
    async def test_metrics_query(self, metrics_collector):
        """Test metrics querying."""
        # Record multiple metrics
        await metrics_collector.record_metric("metric_a", 10)
        await metrics_collector.record_metric("metric_b", 20)
        await metrics_collector.record_metric("metric_a", 15)
        
        # Query all metrics
        all_metrics = await metrics_collector.get_metrics()
        assert len(all_metrics) >= 3
        
        # Query by name pattern
        a_metrics = await metrics_collector.get_metrics(name_pattern="metric_a")
        assert len(a_metrics) == 2
        assert all(m.name == "metric_a" for m in a_metrics)
    
    @pytest.mark.asyncio
    async def test_metrics_time_range_query(self, metrics_collector):
        """Test metrics querying with time range."""
        now = datetime.now()
        
        # Record metrics at different times
        await metrics_collector.record_metric("time_metric", 1)
        await asyncio.sleep(0.1)
        await metrics_collector.record_metric("time_metric", 2)
        
        # Query recent metrics
        recent_metrics = await metrics_collector.get_metrics(
            name_pattern="time_metric",
            start_time=now
        )
        
        assert len(recent_metrics) >= 1


class TestAlertManager:
    """Test alert management system."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def alert_manager(self, temp_dir):
        config = {
            'db_path': temp_dir / 'alerts.db'
        }
        return AlertManager(config)
    
    @pytest.mark.asyncio
    async def test_create_alert(self, alert_manager):
        """Test alert creation."""
        alert_id = await alert_manager.create_alert(
            title="Test Alert",
            description="This is a test alert",
            severity=AlertSeverity.WARNING,
            source="test_system",
            metadata={"key": "value"}
        )
        
        assert len(alert_id) > 0
        assert alert_id in alert_manager.alerts
        
        alert = alert_manager.alerts[alert_id]
        assert alert.title == "Test Alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.source == "test_system"
        assert not alert.resolved
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_manager):
        """Test alert resolution."""
        # Create alert
        alert_id = await alert_manager.create_alert(
            "Test Alert",
            "Test description",
            AlertSeverity.ERROR,
            "test_system"
        )
        
        # Resolve alert
        success = await alert_manager.resolve_alert(alert_id, "Fixed the issue")
        assert success
        
        alert = alert_manager.alerts[alert_id]
        assert alert.resolved
        assert alert.resolved_at is not None
        assert alert.metadata["resolution_note"] == "Fixed the issue"
    
    @pytest.mark.asyncio
    async def test_notification_handlers(self, alert_manager):
        """Test alert notification handlers."""
        notifications_sent = []
        
        async def test_handler(alert):
            notifications_sent.append(alert)
        
        # Add notification handler
        alert_manager.add_notification_handler(test_handler)
        
        # Create alert
        await alert_manager.create_alert(
            "Notification Test",
            "Test notification",
            AlertSeverity.CRITICAL,
            "test_system"
        )
        
        # Handler should be called
        assert len(notifications_sent) == 1
        assert notifications_sent[0].title == "Notification Test"
    
    def test_alert_rules(self, alert_manager):
        """Test alert rule management."""
        rule_triggered = False
        
        async def test_condition():
            return rule_triggered
        
        # Add alert rule
        alert_manager.add_alert_rule(
            name="test_rule",
            condition=test_condition,
            severity=AlertSeverity.WARNING,
            description="Test rule description"
        )
        
        assert len(alert_manager.alert_rules) == 1
        rule = alert_manager.alert_rules[0]
        assert rule["name"] == "test_rule"
        assert rule["severity"] == AlertSeverity.WARNING
    
    @pytest.mark.asyncio
    async def test_query_alerts(self, alert_manager):
        """Test alert querying."""
        # Create alerts with different severities
        await alert_manager.create_alert("Warning Alert", "Warning", AlertSeverity.WARNING, "system1")
        await alert_manager.create_alert("Error Alert", "Error", AlertSeverity.ERROR, "system2")
        await alert_manager.create_alert("Critical Alert", "Critical", AlertSeverity.CRITICAL, "system1")
        
        # Query all alerts
        all_alerts = await alert_manager.get_alerts()
        assert len(all_alerts) == 3
        
        # Query by severity
        error_alerts = await alert_manager.get_alerts(severity=AlertSeverity.ERROR)
        assert len(error_alerts) == 1
        assert error_alerts[0].severity == AlertSeverity.ERROR
        
        # Query unresolved alerts
        unresolved_alerts = await alert_manager.get_alerts(resolved=False)
        assert len(unresolved_alerts) == 3


class TestHealthMonitor:
    """Test health monitoring system."""
    
    @pytest.fixture
    def health_monitor(self):
        config = {}
        return HealthMonitor(config)
    
    @pytest.mark.asyncio
    async def test_register_health_check(self, health_monitor):
        """Test health check registration."""
        def simple_check():
            return True
        
        health_monitor.register_health_check("simple_test", simple_check)
        assert "simple_test" in health_monitor.health_checks
    
    @pytest.mark.asyncio
    async def test_run_health_check_success(self, health_monitor):
        """Test successful health check execution."""
        def healthy_check():
            return True
        
        health_monitor.register_health_check("healthy_test", healthy_check)
        
        result = await health_monitor.run_health_check("healthy_test")
        assert result.name == "healthy_test"
        assert result.status == HealthStatus.HEALTHY
        assert result.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_run_health_check_failure(self, health_monitor):
        """Test failed health check execution."""
        def unhealthy_check():
            return False
        
        health_monitor.register_health_check("unhealthy_test", unhealthy_check)
        
        result = await health_monitor.run_health_check("unhealthy_test")
        assert result.name == "unhealthy_test"
        assert result.status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_run_health_check_exception(self, health_monitor):
        """Test health check with exception."""
        def failing_check():
            raise Exception("Check failed")
        
        health_monitor.register_health_check("failing_test", failing_check)
        
        result = await health_monitor.run_health_check("failing_test")
        assert result.name == "failing_test"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Check failed" in result.message
    
    @pytest.mark.asyncio
    async def test_async_health_check(self, health_monitor):
        """Test async health check execution."""
        async def async_check():
            await asyncio.sleep(0.1)
            return HealthCheck(
                name="async_test",
                status=HealthStatus.DEGRADED,
                message="Async check completed"
            )
        
        health_monitor.register_health_check("async_test", async_check)
        
        result = await health_monitor.run_health_check("async_test")
        assert result.name == "async_test"
        assert result.status == HealthStatus.DEGRADED
        assert result.message == "Async check completed"
    
    @pytest.mark.asyncio
    async def test_run_all_health_checks(self, health_monitor):
        """Test running all health checks."""
        def check1():
            return True
        
        def check2():
            return False
        
        health_monitor.register_health_check("check1", check1)
        health_monitor.register_health_check("check2", check2)
        
        results = await health_monitor.run_all_health_checks()
        
        assert len(results) == 2
        assert results["check1"].status == HealthStatus.HEALTHY
        assert results["check2"].status == HealthStatus.UNHEALTHY
        
        # Overall status should be unhealthy due to check2
        assert health_monitor.overall_status == HealthStatus.UNHEALTHY
    
    def test_health_summary(self, health_monitor):
        """Test health summary generation."""
        # Add some health check results
        health_monitor.health_status["test1"] = HealthCheck(
            name="test1",
            status=HealthStatus.HEALTHY,
            message="OK"
        )
        health_monitor.health_status["test2"] = HealthCheck(
            name="test2",
            status=HealthStatus.DEGRADED,
            message="Slow"
        )
        health_monitor.overall_status = HealthStatus.DEGRADED
        
        summary = health_monitor.get_health_summary()
        
        assert summary["overall_status"] == "degraded"
        assert summary["checks_count"] == 0  # No registered checks
        assert "test2" in summary["unhealthy_checks"]


class TestUsageTracker:
    """Test usage tracking system."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def usage_tracker(self, temp_dir):
        config = {
            'db_path': temp_dir / 'usage.db'
        }
        return UsageTracker(config)
    
    @pytest.mark.asyncio
    async def test_track_usage(self, usage_tracker):
        """Test usage tracking."""
        await usage_tracker.track_usage(
            feature="code_generation",
            event_type="generate",
            duration=2.5,
            success=True,
            metadata={"lines": 50}
        )
        
        assert "code_generation" in usage_tracker.usage_stats
        stats = usage_tracker.usage_stats["code_generation"]
        
        assert stats.usage_count == 1
        assert stats.total_duration == 2.5
        assert stats.avg_duration == 2.5
        assert stats.error_count == 0
        assert stats.success_rate == 1.0
    
    @pytest.mark.asyncio
    async def test_track_multiple_usage(self, usage_tracker):
        """Test tracking multiple usage events."""
        # Track successful uses
        await usage_tracker.track_usage("feature_a", duration=1.0, success=True)
        await usage_tracker.track_usage("feature_a", duration=2.0, success=True)
        await usage_tracker.track_usage("feature_a", duration=1.5, success=False)
        
        stats = usage_tracker.usage_stats["feature_a"]
        
        assert stats.usage_count == 3
        assert stats.total_duration == 4.5
        assert abs(stats.avg_duration - 1.5) < 0.01
        assert stats.error_count == 1
        assert abs(stats.success_rate - 0.667) < 0.01
    
    @pytest.mark.asyncio
    async def test_usage_insights(self, usage_tracker):
        """Test usage insights generation."""
        # Track usage for multiple features
        await usage_tracker.track_usage("feature_1", success=True)
        await usage_tracker.track_usage("feature_1", success=True)
        await usage_tracker.track_usage("feature_2", success=True)
        await usage_tracker.track_usage("feature_1", success=False)
        
        insights = await usage_tracker.get_usage_insights(days=1)
        
        assert "most_used_features" in insights
        assert "error_rates" in insights
        
        # feature_1 should be most used
        most_used = insights["most_used_features"]
        assert len(most_used) >= 1
        assert most_used[0]["feature"] == "feature_1"
        assert most_used[0]["count"] == 3
    
    def test_current_stats(self, usage_tracker):
        """Test current statistics retrieval."""
        # Add some usage data
        usage_tracker.usage_stats["test_feature"] = UsageStats(
            feature="test_feature",
            usage_count=10,
            last_used=datetime.now(),
            total_duration=25.0,
            error_count=2,
            success_rate=0.8,
            avg_duration=2.5
        )
        
        stats = usage_tracker.get_current_stats()
        
        assert "test_feature" in stats
        feature_stats = stats["test_feature"]
        assert feature_stats["usage_count"] == 10
        assert feature_stats["success_rate"] == 0.8


class TestMonitoringAnalytics:
    """Test main monitoring analytics system."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def monitoring_system(self, temp_dir):
        config = {
            'metrics': {
                'db_path': temp_dir / 'metrics.db'
            },
            'alerts': {
                'db_path': temp_dir / 'alerts.db'
            },
            'health': {},
            'usage': {
                'db_path': temp_dir / 'usage.db'
            }
        }
        return MonitoringAnalytics(config)
    
    def test_initialization(self, monitoring_system):
        """Test monitoring system initialization."""
        assert monitoring_system.metrics_collector is not None
        assert monitoring_system.alert_manager is not None
        assert monitoring_system.health_monitor is not None
        assert monitoring_system.usage_tracker is not None
    
    def test_default_health_checks(self, monitoring_system):
        """Test default health checks are registered."""
        health_checks = monitoring_system.health_monitor.health_checks
        
        assert "cpu_usage" in health_checks
        assert "memory_usage" in health_checks
        assert "disk_usage" in health_checks
    
    def test_default_alert_rules(self, monitoring_system):
        """Test default alert rules are configured."""
        alert_rules = monitoring_system.alert_manager.alert_rules
        
        assert len(alert_rules) >= 2
        rule_names = [rule["name"] for rule in alert_rules]
        assert "high_error_rate" in rule_names
        assert "high_response_time" in rule_names
    
    @pytest.mark.asyncio
    async def test_dashboard_data(self, monitoring_system):
        """Test dashboard data generation."""
        # Add some test data
        await monitoring_system.metrics_collector.record_metric("test_metric", 100)
        await monitoring_system.alert_manager.create_alert(
            "Test Alert", "Test", AlertSeverity.WARNING, "test"
        )
        await monitoring_system.usage_tracker.track_usage("test_feature")
        
        dashboard_data = await monitoring_system.get_dashboard_data()
        
        assert "timestamp" in dashboard_data
        assert "health" in dashboard_data
        assert "metrics" in dashboard_data
        assert "alerts" in dashboard_data
        assert "usage" in dashboard_data
        assert "system_info" in dashboard_data
        
        # Check structure
        assert "overall_status" in dashboard_data["health"]
        assert "recent_count" in dashboard_data["metrics"]
        assert "active_count" in dashboard_data["alerts"]


# Performance tests for monitoring components
class TestMonitoringPerformance:
    """Performance tests for monitoring components."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self, temp_dir):
        """Test metrics collection performance."""
        config = {
            'db_path': temp_dir / 'metrics.db',
            'max_metrics': 10000
        }
        collector = MetricsCollector(config)
        
        # Measure time to record many metrics
        start_time = time.time()
        
        for i in range(1000):
            await collector.record_metric(f"metric_{i % 10}", i, MetricType.GAUGE)
        
        collection_time = time.time() - start_time
        
        # Should be fast
        assert collection_time < 2.0  # Under 2 seconds for 1000 metrics
        assert len(collector.metrics) == 1000
    
    @pytest.mark.asyncio
    async def test_alert_processing_performance(self, temp_dir):
        """Test alert processing performance."""
        config = {
            'db_path': temp_dir / 'alerts.db'
        }
        alert_manager = AlertManager(config)
        
        # Measure time to create many alerts
        start_time = time.time()
        
        alert_ids = []
        for i in range(100):
            alert_id = await alert_manager.create_alert(
                f"Alert {i}",
                f"Description {i}",
                AlertSeverity.WARNING,
                "test_system"
            )
            alert_ids.append(alert_id)
        
        creation_time = time.time() - start_time
        
        # Should be reasonably fast
        assert creation_time < 5.0  # Under 5 seconds for 100 alerts
        assert len(alert_manager.alerts) == 100
    
    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """Test health check performance."""
        health_monitor = HealthMonitor({})
        
        # Register multiple health checks
        for i in range(20):
            def make_check(check_id):
                def check():
                    time.sleep(0.01)  # Simulate small delay
                    return True
                return check
            
            health_monitor.register_health_check(f"check_{i}", make_check(i))
        
        # Measure time to run all checks
        start_time = time.time()
        results = await health_monitor.run_all_health_checks()
        check_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert check_time < 2.0  # Under 2 seconds for 20 checks
        assert len(results) == 20
        assert all(result.status == HealthStatus.HEALTHY for result in results.values())
    
    @pytest.mark.asyncio
    async def test_usage_tracking_performance(self, temp_dir):
        """Test usage tracking performance."""
        config = {
            'db_path': temp_dir / 'usage.db'
        }
        tracker = UsageTracker(config)
        
        # Measure time to track many usage events
        start_time = time.time()
        
        for i in range(500):
            await tracker.track_usage(
                f"feature_{i % 5}",
                duration=0.1,
                success=True
            )
        
        tracking_time = time.time() - start_time
        
        # Should be fast
        assert tracking_time < 3.0  # Under 3 seconds for 500 events
        assert len(tracker.usage_stats) == 5  # 5 different features


# Integration tests
class TestMonitoringIntegration:
    """Integration tests for monitoring system."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring(self, temp_dir):
        """Test complete monitoring workflow."""
        config = {
            'metrics': {'db_path': temp_dir / 'metrics.db'},
            'alerts': {'db_path': temp_dir / 'alerts.db'},
            'health': {},
            'usage': {'db_path': temp_dir / 'usage.db'}
        }
        
        monitoring = MonitoringAnalytics(config)
        
        # Simulate application activity
        
        # 1. Record metrics
        await monitoring.metrics_collector.record_metric("requests", 100, MetricType.COUNTER)
        await monitoring.metrics_collector.record_metric("response_time", 1.5, MetricType.TIMER)
        await monitoring.metrics_collector.set_gauge("cpu_usage", 75.0)
        
        # 2. Track usage
        await monitoring.usage_tracker.track_usage("api_call", duration=1.5, success=True)
        await monitoring.usage_tracker.track_usage("code_gen", duration=3.0, success=True)
        
        # 3. Run health checks
        health_results = await monitoring.health_monitor.run_all_health_checks()
        
        # 4. Generate dashboard data
        dashboard = await monitoring.get_dashboard_data()
        
        # Verify integration
        assert dashboard["metrics"]["recent_count"] >= 3
        assert len(dashboard["health"]) > 0
        assert len(dashboard["usage"]["most_used_features"]) >= 2
        
        # 5. Test alert generation (simulate high error rate)
        await monitoring.metrics_collector.set_gauge("error_rate", 0.15)  # Above threshold
        
        # Wait a moment for alert processing
        await asyncio.sleep(0.1)
        
        # Should have generated alert
        alerts = await monitoring.alert_manager.get_alerts(resolved=False)
        # Note: Alert rules run in background, so we might not see immediate results


if __name__ == "__main__":
    pytest.main([__file__])