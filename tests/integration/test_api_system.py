"""
Integration tests for API and webhook system functionality.

Tests REST API, webhook system, authentication, rate limiting, and usage analytics.
"""

import pytest
import asyncio
import json
import time
import jwt
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
import redis.asyncio as redis

from src.codegenie.integrations.api_system import (
    APISystem, AuthenticationManager, RateLimiter, WebhookManager,
    UsageAnalytics, APIKey, WebhookEndpoint, WebhookEvent, APIRequest
)
from src.codegenie.core.code_intelligence import CodeIntelligence
from src.codegenie.core.context_engine import ContextEngine
from src.codegenie.agents.coordinator import AgentCoordinator


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock = AsyncMock(spec=redis.Redis)
    
    # Mock pipeline
    mock_pipeline = AsyncMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]  # Mock rate limit results
    mock.pipeline.return_value = mock_pipeline
    
    # Mock other Redis operations
    mock.ping.return_value = True
    mock.setex.return_value = True
    mock.hgetall.return_value = {}
    mock.lrange.return_value = []
    
    return mock


@pytest.fixture
def mock_code_intelligence():
    """Mock code intelligence for testing"""
    mock = AsyncMock(spec=CodeIntelligence)
    
    mock.analyze_code_semantics.return_value = Mock(
        issues=[],
        suggestions=[],
        complexity_score=0.5
    )
    
    mock.get_code_suggestions.return_value = [
        Mock(text="suggestion1", confidence=0.9),
        Mock(text="suggestion2", confidence=0.8)
    ]
    
    mock.review_code.return_value = Mock(
        overall_score=0.85,
        issues=[],
        recommendations=["Good code quality"]
    )
    
    return mock


@pytest.fixture
def mock_context_engine():
    """Mock context engine for testing"""
    mock = AsyncMock(spec=ContextEngine)
    
    mock.retrieve_relevant_context.return_value = Mock(
        conversation_history=[],
        project_state=Mock(),
        relevant_knowledge=[]
    )
    
    mock.store_context.return_value = "context123"
    
    return mock


@pytest.fixture
def mock_agent_coordinator():
    """Mock agent coordinator for testing"""
    mock = AsyncMock(spec=AgentCoordinator)
    
    mock.execute_task.return_value = "task123"
    mock.get_task_status.return_value = "completed"
    
    return mock


@pytest.fixture
def auth_manager(mock_redis):
    """Create authentication manager for testing"""
    return AuthenticationManager("test_secret_key", mock_redis)


@pytest.fixture
def rate_limiter(mock_redis):
    """Create rate limiter for testing"""
    return RateLimiter(mock_redis)


@pytest.fixture
def webhook_manager(mock_redis):
    """Create webhook manager for testing"""
    return WebhookManager(mock_redis)


@pytest.fixture
def usage_analytics(mock_redis):
    """Create usage analytics for testing"""
    return UsageAnalytics(mock_redis)


@pytest.fixture
def api_system(mock_code_intelligence, mock_context_engine, mock_agent_coordinator, mock_redis):
    """Create API system for testing"""
    with patch('redis.asyncio.from_url', return_value=mock_redis):
        return APISystem(
            mock_code_intelligence, mock_context_engine, mock_agent_coordinator,
            "test_secret_key", "redis://localhost"
        )


@pytest.fixture
def sample_api_key():
    """Sample API key for testing"""
    return APIKey(
        key_id="key123",
        key_hash="hash123",
        name="Test API Key",
        permissions=["read", "write"],
        rate_limit=1000,
        created_at=datetime.now(),
        expires_at=None,
        last_used=None,
        usage_count=0,
        is_active=True
    )


@pytest.fixture
def sample_webhook():
    """Sample webhook endpoint for testing"""
    return WebhookEndpoint(
        id="webhook123",
        url="https://example.com/webhook",
        events=["code_analysis", "task_completed"],
        secret="webhook_secret",
        headers={"Content-Type": "application/json"},
        retry_count=3,
        timeout=30,
        is_active=True,
        created_at=datetime.now(),
        last_triggered=None
    )


class TestAuthenticationManager:
    """Test authentication manager functionality"""
    
    def test_generate_api_key(self, auth_manager):
        """Test API key generation"""
        key, api_key = auth_manager.generate_api_key(
            "Test Key", ["read", "write"], 1000, 30
        )
        
        assert key.startswith("cg_")
        assert isinstance(api_key, APIKey)
        assert api_key.name == "Test Key"
        assert api_key.permissions == ["read", "write"]
        assert api_key.rate_limit == 1000
        assert api_key.is_active is True
    
    @pytest.mark.asyncio
    async def test_validate_api_key(self, auth_manager):
        """Test API key validation"""
        # Generate a key first
        key, api_key = auth_manager.generate_api_key("Test Key", ["read"])
        
        # Validate the key
        validated_key = await auth_manager.validate_api_key(key)
        
        assert validated_key is not None
        assert validated_key.key_id == api_key.key_id
        assert validated_key.usage_count == 1  # Should increment
    
    @pytest.mark.asyncio
    async def test_validate_invalid_api_key(self, auth_manager):
        """Test validation of invalid API key"""
        result = await auth_manager.validate_api_key("invalid_key")
        
        assert result is None
    
    def test_generate_jwt_token(self, auth_manager):
        """Test JWT token generation"""
        token = auth_manager.generate_jwt_token("user123", ["read", "write"], 3600)
        
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
        assert payload["user_id"] == "user123"
        assert payload["permissions"] == ["read", "write"]
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token(self, auth_manager):
        """Test JWT token validation"""
        # Generate token
        token = auth_manager.generate_jwt_token("user123", ["read", "write"])
        
        # Validate token
        payload = await auth_manager.validate_jwt_token(token)
        
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["permissions"] == ["read", "write"]
    
    @pytest.mark.asyncio
    async def test_validate_expired_jwt_token(self, auth_manager):
        """Test validation of expired JWT token"""
        # Generate expired token
        token = auth_manager.generate_jwt_token("user123", ["read"], -1)  # Expired
        
        # Validate token
        payload = await auth_manager.validate_jwt_token(token)
        
        assert payload is None
    
    def test_has_permission(self, auth_manager):
        """Test permission checking"""
        # Test specific permission
        assert auth_manager.has_permission(["read", "write"], "read") is True
        assert auth_manager.has_permission(["read"], "write") is False
        
        # Test admin permission
        assert auth_manager.has_permission(["admin"], "anything") is True


class TestRateLimiter:
    """Test rate limiter functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, rate_limiter):
        """Test rate limiting when requests are allowed"""
        # Mock Redis to return low count
        rate_limiter.redis.pipeline.return_value.execute.return_value = [None, 5, None, None]
        
        allowed, info = await rate_limiter.is_allowed("test_key", 100, 3600)
        
        assert allowed is True
        assert info["allowed"] is True
        assert info["limit"] == 100
        assert info["remaining"] >= 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limiting when limit is exceeded"""
        # Mock Redis to return high count
        rate_limiter.redis.pipeline.return_value.execute.return_value = [None, 150, None, None]
        rate_limiter.redis.zrange.return_value = [(b"123456789", 123456789.0)]
        
        allowed, info = await rate_limiter.is_allowed("test_key", 100, 3600)
        
        assert allowed is False
        assert info["allowed"] is False
        assert info["limit"] == 100
        assert info["remaining"] == 0
        assert info["retry_after"] > 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_redis_error(self, rate_limiter):
        """Test rate limiting when Redis fails"""
        # Mock Redis to raise exception
        rate_limiter.redis.pipeline.side_effect = Exception("Redis error")
        
        allowed, info = await rate_limiter.is_allowed("test_key", 100, 3600)
        
        # Should fail open (allow request)
        assert allowed is True
        assert info["allowed"] is True


class TestWebhookManager:
    """Test webhook manager functionality"""
    
    @pytest.mark.asyncio
    async def test_register_webhook(self, webhook_manager, sample_webhook):
        """Test webhook registration"""
        webhook_manager.register_webhook(sample_webhook)
        
        assert sample_webhook.id in webhook_manager.webhooks
        assert webhook_manager.webhooks[sample_webhook.id] == sample_webhook
    
    def test_unregister_webhook(self, webhook_manager, sample_webhook):
        """Test webhook unregistration"""
        # Register first
        webhook_manager.register_webhook(sample_webhook)
        
        # Unregister
        webhook_manager.unregister_webhook(sample_webhook.id)
        
        assert sample_webhook.id not in webhook_manager.webhooks
    
    @pytest.mark.asyncio
    async def test_trigger_event(self, webhook_manager, sample_webhook):
        """Test webhook event triggering"""
        # Register webhook
        webhook_manager.register_webhook(sample_webhook)
        
        # Create event
        event = WebhookEvent(
            event_id="event123",
            event_type="code_analysis",
            timestamp=datetime.now(),
            data={"result": "success"},
            source="api",
            webhook_endpoints=[]
        )
        
        # Trigger event
        await webhook_manager.trigger_event(event)
        
        # Event should be queued
        assert not webhook_manager.event_queue.empty()
    
    @pytest.mark.asyncio
    async def test_start_stop_workers(self, webhook_manager):
        """Test starting and stopping webhook workers"""
        # Start workers
        await webhook_manager.start_workers(2)
        
        assert len(webhook_manager.worker_tasks) == 2
        
        # Stop workers
        await webhook_manager.stop_workers()
        
        assert len(webhook_manager.worker_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_send_webhook(self, webhook_manager, sample_webhook):
        """Test sending webhook HTTP request"""
        event = WebhookEvent(
            event_id="event123",
            event_type="code_analysis",
            timestamp=datetime.now(),
            data={"result": "success"},
            source="api",
            webhook_endpoints=[]
        )
        
        # Mock aiohttp session
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            await webhook_manager._send_webhook(event, sample_webhook)
            
            # Verify HTTP request was made
            mock_session.post.assert_called_once()
    
    def test_generate_signature(self, webhook_manager):
        """Test webhook signature generation"""
        payload = '{"test": "data"}'
        secret = "test_secret"
        
        signature = webhook_manager._generate_signature(payload, secret)
        
        assert signature.startswith("sha256=")
        assert len(signature) > 10


class TestUsageAnalytics:
    """Test usage analytics functionality"""
    
    @pytest.mark.asyncio
    async def test_record_api_request(self, usage_analytics):
        """Test recording API request"""
        request = APIRequest(
            request_id="req123",
            api_key_id="key123",
            endpoint="/api/v1/code/analyze",
            method="POST",
            timestamp=datetime.now(),
            response_time=0.5,
            status_code=200,
            user_agent="TestClient/1.0",
            ip_address="127.0.0.1"
        )
        
        await usage_analytics.record_api_request(request)
        
        # Verify Redis operations were called
        usage_analytics.redis.setex.assert_called()
        usage_analytics.redis.pipeline.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_usage_stats(self, usage_analytics):
        """Test getting usage statistics"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # Mock Redis responses
        usage_analytics.redis.hgetall.return_value = {
            b"total_requests": b"100",
            b"status_200": b"90",
            b"status_400": b"10",
            b"endpoint_/api/v1/code/analyze": b"50"
        }
        usage_analytics.redis.lrange.return_value = [b"0.1", b"0.2", b"0.3"]
        
        stats = await usage_analytics.get_usage_stats(start_date, end_date)
        
        assert stats["total_requests"] >= 0
        assert "status_codes" in stats
        assert "endpoints" in stats
        assert "daily_breakdown" in stats
        assert "average_response_time" in stats
    
    @pytest.mark.asyncio
    async def test_get_api_key_usage(self, usage_analytics):
        """Test getting API key usage statistics"""
        api_key_id = "key123"
        
        # Mock Redis response
        usage_analytics.redis.hgetall.return_value = {
            b"total_requests": b"50",
            b"status_200": b"45",
            b"status_400": b"5"
        }
        
        stats = await usage_analytics.get_api_key_usage(api_key_id)
        
        assert stats["total_requests"] == 50
        assert "status_codes" in stats
        assert stats["status_codes"]["200"] == 45


class TestAPISystemEndpoints(AioHTTPTestCase):
    """Test API system endpoints using aiohttp test client"""
    
    async def get_application(self):
        """Create test application"""
        # Mock dependencies
        mock_code_intelligence = AsyncMock(spec=CodeIntelligence)
        mock_context_engine = AsyncMock(spec=ContextEngine)
        mock_agent_coordinator = AsyncMock(spec=AgentCoordinator)
        mock_redis = AsyncMock(spec=redis.Redis)
        
        # Mock Redis operations
        mock_redis.ping.return_value = True
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 5, None, None]
        mock_redis.pipeline.return_value = mock_pipeline
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            api_system = APISystem(
                mock_code_intelligence, mock_context_engine, mock_agent_coordinator,
                "test_secret_key", "redis://localhost"
            )
            
            # Generate test API key
            key, api_key = api_system.auth_manager.generate_api_key("Test Key", ["read", "write"])
            self.test_api_key = key
            
            return api_system.app
    
    @unittest_run_loop
    async def test_health_check(self):
        """Test health check endpoint"""
        resp = await self.client.request("GET", "/health")
        
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "healthy"
    
    @unittest_run_loop
    async def test_api_docs(self):
        """Test API documentation endpoint"""
        resp = await self.client.request("GET", "/api/docs")
        
        assert resp.status == 200
        data = await resp.json()
        assert "title" in data
        assert "endpoints" in data
    
    @unittest_run_loop
    async def test_analyze_code_endpoint(self):
        """Test code analysis endpoint"""
        headers = {"Authorization": f"ApiKey {self.test_api_key}"}
        payload = {
            "code": "def hello(): return 'world'",
            "language": "python"
        }
        
        resp = await self.client.request("POST", "/api/v1/code/analyze", 
                                       json=payload, headers=headers)
        
        assert resp.status == 200
        data = await resp.json()
        assert "analysis" in data
        assert "timestamp" in data
    
    @unittest_run_loop
    async def test_get_code_suggestions_endpoint(self):
        """Test code suggestions endpoint"""
        headers = {"Authorization": f"ApiKey {self.test_api_key}"}
        payload = {
            "code": "def hello():",
            "cursor_position": 12,
            "language": "python"
        }
        
        resp = await self.client.request("POST", "/api/v1/code/suggestions",
                                       json=payload, headers=headers)
        
        assert resp.status == 200
        data = await resp.json()
        assert "suggestions" in data
        assert "timestamp" in data
    
    @unittest_run_loop
    async def test_unauthorized_request(self):
        """Test request without authentication"""
        payload = {"code": "test"}
        
        resp = await self.client.request("POST", "/api/v1/code/analyze", json=payload)
        
        assert resp.status == 401
        data = await resp.json()
        assert "error" in data
    
    @unittest_run_loop
    async def test_invalid_api_key(self):
        """Test request with invalid API key"""
        headers = {"Authorization": "ApiKey invalid_key"}
        payload = {"code": "test"}
        
        resp = await self.client.request("POST", "/api/v1/code/analyze",
                                       json=payload, headers=headers)
        
        assert resp.status == 401
        data = await resp.json()
        assert "error" in data
    
    @unittest_run_loop
    async def test_create_webhook_endpoint(self):
        """Test webhook creation endpoint"""
        headers = {"Authorization": f"ApiKey {self.test_api_key}"}
        payload = {
            "url": "https://example.com/webhook",
            "events": ["code_analysis", "task_completed"],
            "secret": "webhook_secret"
        }
        
        resp = await self.client.request("POST", "/api/v1/webhooks",
                                       json=payload, headers=headers)
        
        assert resp.status == 200
        data = await resp.json()
        assert "webhook_id" in data
        assert data["status"] == "created"
    
    @unittest_run_loop
    async def test_list_webhooks_endpoint(self):
        """Test webhook listing endpoint"""
        headers = {"Authorization": f"ApiKey {self.test_api_key}"}
        
        resp = await self.client.request("GET", "/api/v1/webhooks", headers=headers)
        
        assert resp.status == 200
        data = await resp.json()
        assert "webhooks" in data
        assert "count" in data


class TestAPISystemIntegration:
    """Test API system integration functionality"""
    
    @pytest.mark.asyncio
    async def test_api_system_initialization(self, mock_code_intelligence, mock_context_engine, 
                                           mock_agent_coordinator, mock_redis):
        """Test API system initialization"""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            api_system = APISystem(
                mock_code_intelligence, mock_context_engine, mock_agent_coordinator,
                "test_secret_key", "redis://localhost"
            )
            
            assert api_system.code_intelligence == mock_code_intelligence
            assert api_system.context_engine == mock_context_engine
            assert api_system.agent_coordinator == mock_agent_coordinator
            assert api_system.auth_manager is not None
            assert api_system.rate_limiter is not None
            assert api_system.webhook_manager is not None
            assert api_system.usage_analytics is not None
    
    @pytest.mark.asyncio
    async def test_create_and_revoke_api_key(self, api_system):
        """Test API key creation and revocation"""
        # Create API key
        key, api_key = api_system.create_api_key("Test Key", ["read", "write"])
        
        assert key.startswith("cg_")
        assert api_key.is_active is True
        
        # Revoke API key
        result = api_system.revoke_api_key(api_key.key_hash)
        
        assert result is True
        assert api_key.is_active is False
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_event(self, api_system, sample_webhook):
        """Test triggering webhook event through API system"""
        # Register webhook
        api_system.webhook_manager.register_webhook(sample_webhook)
        
        # Trigger event
        await api_system.trigger_webhook_event(
            "code_analysis", {"result": "success"}, "test"
        )
        
        # Event should be queued
        assert not api_system.webhook_manager.event_queue.empty()
    
    @pytest.mark.asyncio
    async def test_server_start_stop(self, api_system):
        """Test API server start and stop"""
        # Mock server components
        with patch('aiohttp.web.AppRunner') as mock_runner_class:
            mock_runner = AsyncMock()
            mock_runner_class.return_value = mock_runner
            
            with patch('aiohttp.web.TCPSite') as mock_site_class:
                mock_site = AsyncMock()
                mock_site_class.return_value = mock_site
                
                # Start server
                await api_system.start_server("localhost", 8080)
                
                mock_runner.setup.assert_called_once()
                mock_site.start.assert_called_once()
                
                # Stop server
                await api_system.stop_server()
                
                api_system.redis.close.assert_called_once()


class TestAPISystemErrorHandling:
    """Test error handling in API system"""
    
    @pytest.mark.asyncio
    async def test_redis_connection_error(self, mock_code_intelligence, mock_context_engine, 
                                        mock_agent_coordinator):
        """Test handling Redis connection errors"""
        # Mock Redis to raise connection error
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            api_system = APISystem(
                mock_code_intelligence, mock_context_engine, mock_agent_coordinator,
                "test_secret_key", "redis://localhost"
            )
            
            # Health check should return unhealthy status
            request = Mock()
            response = await api_system._health_check(request)
            
            assert response.status == 503
    
    @pytest.mark.asyncio
    async def test_code_analysis_error_handling(self, api_system):
        """Test error handling in code analysis endpoint"""
        # Mock code intelligence to raise exception
        api_system.code_intelligence.analyze_code_semantics.side_effect = Exception("Analysis failed")
        
        # Create mock request
        request = Mock()
        request.json = AsyncMock(return_value={"code": "test", "language": "python"})
        
        response = await api_system._analyze_code(request)
        
        assert response.status == 500
    
    @pytest.mark.asyncio
    async def test_webhook_delivery_failure(self, webhook_manager, sample_webhook):
        """Test webhook delivery failure handling"""
        # Register webhook
        webhook_manager.register_webhook(sample_webhook)
        
        # Mock aiohttp to raise exception
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post.side_effect = Exception("Network error")
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            event = WebhookEvent(
                event_id="event123",
                event_type="code_analysis",
                timestamp=datetime.now(),
                data={"result": "success"},
                source="api",
                webhook_endpoints=[]
            )
            
            # Should handle error gracefully
            await webhook_manager._send_webhook(event, sample_webhook)


class TestAPISystemPerformance:
    """Test performance aspects of API system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, api_system):
        """Test handling concurrent API requests"""
        # Create test API key
        key, api_key = api_system.create_api_key("Test Key", ["read", "write"])
        
        # Mock request processing
        async def mock_handler(request):
            request["api_key"] = api_key
            return web.json_response({"status": "success"})
        
        # Process multiple requests concurrently
        tasks = []
        for i in range(10):
            request = Mock()
            request.path = "/api/v1/test"
            request.method = "POST"
            request.remote = "127.0.0.1"
            request.headers = {"User-Agent": "TestClient"}
            request.__getitem__ = lambda self, key: api_key if key == "api_key" else None
            request.__contains__ = lambda self, key: key == "api_key"
            request.get = lambda key, default=None: api_key if key == "api_key" else default
            
            task = asyncio.create_task(api_system._analytics_middleware(request, mock_handler))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self, rate_limiter):
        """Test rate limiting performance under load"""
        # Mock Redis for fast responses
        rate_limiter.redis.pipeline.return_value.execute.return_value = [None, 5, None, None]
        
        # Test many rate limit checks
        tasks = []
        for i in range(100):
            task = rate_limiter.is_allowed(f"key_{i}", 1000)
            tasks.append(task)
        
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0  # 1 second max
        
        # All should be allowed
        for allowed, info in results:
            assert allowed is True
    
    @pytest.mark.asyncio
    async def test_webhook_delivery_performance(self, webhook_manager):
        """Test webhook delivery performance"""
        # Register multiple webhooks
        webhooks = []
        for i in range(10):
            webhook = WebhookEndpoint(
                id=f"webhook{i}",
                url=f"https://example{i}.com/webhook",
                events=["test_event"],
                secret=None,
                headers={},
                retry_count=1,
                timeout=5,
                is_active=True,
                created_at=datetime.now(),
                last_triggered=None
            )
            webhook_manager.register_webhook(webhook)
            webhooks.append(webhook)
        
        # Mock successful HTTP responses
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            event = WebhookEvent(
                event_id="event123",
                event_type="test_event",
                timestamp=datetime.now(),
                data={"test": "data"},
                source="test",
                webhook_endpoints=[]
            )
            
            start_time = asyncio.get_event_loop().time()
            await webhook_manager.trigger_event(event)
            
            # Process all queued events
            while not webhook_manager.event_queue.empty():
                event_data, webhook = await webhook_manager.event_queue.get()
                await webhook_manager._send_webhook(event_data, webhook)
                webhook_manager.event_queue.task_done()
            
            end_time = asyncio.get_event_loop().time()
            
            # Should complete within reasonable time
            assert end_time - start_time < 2.0  # 2 seconds max


if __name__ == "__main__":
    pytest.main([__file__])