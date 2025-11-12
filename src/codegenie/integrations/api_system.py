"""
API and Webhook System

Provides REST API for external integrations, webhook system for event-driven workflows,
authentication and authorization systems, and rate limiting with usage analytics.
"""

import asyncio
import json
import logging
import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path
import jwt
import aiohttp
from aiohttp import web, web_middlewares
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import redis.asyncio as redis
from collections import defaultdict, deque

from ..core.code_intelligence import CodeIntelligence
from ..core.context_engine import ContextEngine
from ..agents.coordinator import AgentCoordinator


@dataclass
class APIKey:
    """API key information"""
    key_id: str
    key_hash: str
    name: str
    permissions: List[str]
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    is_active: bool


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    id: str
    url: str
    events: List[str]
    secret: Optional[str]
    headers: Dict[str, str]
    retry_count: int
    timeout: int
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime]


@dataclass
class APIRequest:
    """API request information"""
    request_id: str
    api_key_id: str
    endpoint: str
    method: str
    timestamp: datetime
    response_time: float
    status_code: int
    user_agent: Optional[str]
    ip_address: str


@dataclass
class WebhookEvent:
    """Webhook event data"""
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    webhook_endpoints: List[str]


class RateLimiter:
    """Rate limiting system with Redis backend"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def is_allowed(self, key: str, limit: int, window: int = 3600) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit"""
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use sliding window rate limiting
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(f"rate_limit:{key}", 0, window_start)
            
            # Count current requests
            pipe.zcard(f"rate_limit:{key}")
            
            # Add current request
            pipe.zadd(f"rate_limit:{key}", {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(f"rate_limit:{key}", window)
            
            results = await pipe.execute()
            current_count = results[1]
            
            if current_count >= limit:
                # Calculate reset time
                oldest_request = await self.redis.zrange(f"rate_limit:{key}", 0, 0, withscores=True)
                reset_time = int(oldest_request[0][1]) + window if oldest_request else current_time + window
                
                return False, {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": reset_time,
                    "retry_after": reset_time - current_time
                }
            
            return True, {
                "allowed": True,
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset_time": current_time + window,
                "retry_after": 0
            }
            
        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, {"allowed": True, "limit": limit, "remaining": limit - 1}


class AuthenticationManager:
    """Authentication and authorization system"""
    
    def __init__(self, secret_key: str, redis_client: redis.Redis):
        self.secret_key = secret_key
        self.redis = redis_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_keys: Dict[str, APIKey] = {}
    
    def generate_api_key(self, name: str, permissions: List[str], rate_limit: int = 1000,
                        expires_in_days: Optional[int] = None) -> tuple[str, APIKey]:
        """Generate new API key"""
        import secrets
        
        # Generate random API key
        key = f"cg_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Create API key object
        api_key = APIKey(
            key_id=key_hash[:16],
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            rate_limit=rate_limit,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
            last_used=None,
            usage_count=0,
            is_active=True
        )
        
        self.api_keys[key_hash] = api_key
        return key, api_key
    
    async def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate API key"""
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            api_key = self.api_keys.get(key_hash)
            
            if not api_key:
                return None
            
            if not api_key.is_active:
                return None
            
            if api_key.expires_at and datetime.now() > api_key.expires_at:
                return None
            
            # Update usage
            api_key.last_used = datetime.now()
            api_key.usage_count += 1
            
            return api_key
            
        except Exception as e:
            self.logger.error(f"API key validation error: {e}")
            return None
    
    def generate_jwt_token(self, user_id: str, permissions: List[str], expires_in: int = 3600) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    async def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def has_permission(self, permissions: List[str], required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in permissions or "admin" in permissions


class WebhookManager:
    """Webhook system for event-driven workflows"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self.webhooks: Dict[str, WebhookEndpoint] = {}
        self.event_queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
    
    async def start_workers(self, num_workers: int = 3):
        """Start webhook worker tasks"""
        for i in range(num_workers):
            task = asyncio.create_task(self._webhook_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        self.logger.info(f"Started {num_workers} webhook workers")
    
    async def stop_workers(self):
        """Stop webhook worker tasks"""
        for task in self.worker_tasks:
            task.cancel()
        
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        self.logger.info("Stopped webhook workers")
    
    def register_webhook(self, webhook: WebhookEndpoint):
        """Register webhook endpoint"""
        self.webhooks[webhook.id] = webhook
        self.logger.info(f"Registered webhook: {webhook.url} for events: {webhook.events}")
    
    def unregister_webhook(self, webhook_id: str):
        """Unregister webhook endpoint"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self.logger.info(f"Unregistered webhook: {webhook_id}")
    
    async def trigger_event(self, event: WebhookEvent):
        """Trigger webhook event"""
        try:
            # Find matching webhooks
            matching_webhooks = []
            for webhook in self.webhooks.values():
                if webhook.is_active and event.event_type in webhook.events:
                    matching_webhooks.append(webhook)
            
            if not matching_webhooks:
                self.logger.debug(f"No webhooks registered for event: {event.event_type}")
                return
            
            # Queue event for processing
            for webhook in matching_webhooks:
                await self.event_queue.put((event, webhook))
            
            self.logger.info(f"Queued event {event.event_type} for {len(matching_webhooks)} webhooks")
            
        except Exception as e:
            self.logger.error(f"Error triggering webhook event: {e}")
    
    async def _webhook_worker(self, worker_id: str):
        """Webhook worker to process events"""
        self.logger.info(f"Webhook worker {worker_id} started")
        
        while True:
            try:
                # Get event from queue
                event, webhook = await self.event_queue.get()
                
                # Process webhook
                await self._send_webhook(event, webhook)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Webhook worker {worker_id} error: {e}")
    
    async def _send_webhook(self, event: WebhookEvent, webhook: WebhookEndpoint):
        """Send webhook HTTP request"""
        try:
            # Prepare payload
            payload = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "source": event.source
            }
            
            # Prepare headers
            headers = webhook.headers.copy()
            headers["Content-Type"] = "application/json"
            headers["User-Agent"] = "CodeGenie-Webhook/1.0"
            
            # Add signature if secret is provided
            if webhook.secret:
                signature = self._generate_signature(json.dumps(payload), webhook.secret)
                headers["X-CodeGenie-Signature"] = signature
            
            # Send webhook with retries
            for attempt in range(webhook.retry_count + 1):
                try:
                    timeout = aiohttp.ClientTimeout(total=webhook.timeout)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(webhook.url, json=payload, headers=headers) as response:
                            if response.status < 400:
                                # Success
                                webhook.last_triggered = datetime.now()
                                self.logger.info(f"Webhook sent successfully: {webhook.url}")
                                return
                            else:
                                self.logger.warning(f"Webhook failed with status {response.status}: {webhook.url}")
                
                except asyncio.TimeoutError:
                    self.logger.warning(f"Webhook timeout (attempt {attempt + 1}): {webhook.url}")
                except Exception as e:
                    self.logger.warning(f"Webhook error (attempt {attempt + 1}): {webhook.url} - {e}")
                
                # Wait before retry (exponential backoff)
                if attempt < webhook.retry_count:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
            
            self.logger.error(f"Webhook failed after {webhook.retry_count + 1} attempts: {webhook.url}")
            
        except Exception as e:
            self.logger.error(f"Error sending webhook: {e}")
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook"""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"


class UsageAnalytics:
    """Usage analytics and monitoring system"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def record_api_request(self, request: APIRequest):
        """Record API request for analytics"""
        try:
            # Store request data
            request_data = asdict(request)
            request_data["timestamp"] = request.timestamp.isoformat()
            
            # Store in Redis with TTL (30 days)
            await self.redis.setex(
                f"api_request:{request.request_id}",
                30 * 24 * 3600,  # 30 days
                json.dumps(request_data)
            )
            
            # Update counters
            date_key = request.timestamp.strftime("%Y-%m-%d")
            hour_key = request.timestamp.strftime("%Y-%m-%d:%H")
            
            pipe = self.redis.pipeline()
            
            # Daily counters
            pipe.hincrby(f"api_stats:daily:{date_key}", "total_requests", 1)
            pipe.hincrby(f"api_stats:daily:{date_key}", f"status_{request.status_code}", 1)
            pipe.hincrby(f"api_stats:daily:{date_key}", f"endpoint_{request.endpoint}", 1)
            
            # Hourly counters
            pipe.hincrby(f"api_stats:hourly:{hour_key}", "total_requests", 1)
            pipe.hincrby(f"api_stats:hourly:{hour_key}", f"status_{request.status_code}", 1)
            
            # API key usage
            pipe.hincrby(f"api_key_stats:{request.api_key_id}", "total_requests", 1)
            pipe.hincrby(f"api_key_stats:{request.api_key_id}", f"status_{request.status_code}", 1)
            
            # Response time tracking
            pipe.lpush(f"response_times:{date_key}", request.response_time)
            pipe.ltrim(f"response_times:{date_key}", 0, 999)  # Keep last 1000 entries
            
            await pipe.execute()
            
        except Exception as e:
            self.logger.error(f"Error recording API request: {e}")
    
    async def get_usage_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get usage statistics for date range"""
        try:
            stats = {
                "total_requests": 0,
                "status_codes": defaultdict(int),
                "endpoints": defaultdict(int),
                "daily_breakdown": {},
                "average_response_time": 0.0
            }
            
            current_date = start_date
            response_times = []
            
            while current_date <= end_date:
                date_key = current_date.strftime("%Y-%m-%d")
                
                # Get daily stats
                daily_stats = await self.redis.hgetall(f"api_stats:daily:{date_key}")
                
                if daily_stats:
                    daily_total = int(daily_stats.get(b"total_requests", 0))
                    stats["total_requests"] += daily_total
                    stats["daily_breakdown"][date_key] = daily_total
                    
                    # Aggregate status codes and endpoints
                    for key, value in daily_stats.items():
                        key_str = key.decode()
                        if key_str.startswith("status_"):
                            status_code = key_str.replace("status_", "")
                            stats["status_codes"][status_code] += int(value)
                        elif key_str.startswith("endpoint_"):
                            endpoint = key_str.replace("endpoint_", "")
                            stats["endpoints"][endpoint] += int(value)
                
                # Get response times
                daily_response_times = await self.redis.lrange(f"response_times:{date_key}", 0, -1)
                response_times.extend([float(rt) for rt in daily_response_times])
                
                current_date += timedelta(days=1)
            
            # Calculate average response time
            if response_times:
                stats["average_response_time"] = sum(response_times) / len(response_times)
            
            return dict(stats)
            
        except Exception as e:
            self.logger.error(f"Error getting usage stats: {e}")
            return {}
    
    async def get_api_key_usage(self, api_key_id: str) -> Dict[str, Any]:
        """Get usage statistics for specific API key"""
        try:
            key_stats = await self.redis.hgetall(f"api_key_stats:{api_key_id}")
            
            if not key_stats:
                return {"total_requests": 0, "status_codes": {}}
            
            stats = {"total_requests": 0, "status_codes": {}}
            
            for key, value in key_stats.items():
                key_str = key.decode()
                if key_str == "total_requests":
                    stats["total_requests"] = int(value)
                elif key_str.startswith("status_"):
                    status_code = key_str.replace("status_", "")
                    stats["status_codes"][status_code] = int(value)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting API key usage: {e}")
            return {}


class APISystem:
    """Main API system with REST endpoints"""
    
    def __init__(self, code_intelligence: CodeIntelligence, context_engine: ContextEngine,
                 agent_coordinator: AgentCoordinator, secret_key: str, redis_url: str = "redis://localhost"):
        self.code_intelligence = code_intelligence
        self.context_engine = context_engine
        self.agent_coordinator = agent_coordinator
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.redis = redis.from_url(redis_url)
        self.auth_manager = AuthenticationManager(secret_key, self.redis)
        self.rate_limiter = RateLimiter(self.redis)
        self.webhook_manager = WebhookManager(self.redis)
        self.usage_analytics = UsageAnalytics(self.redis)
        
        # Web application
        self.app = web.Application(middlewares=[
            self._auth_middleware,
            self._rate_limit_middleware,
            self._analytics_middleware,
            self._cors_middleware
        ])
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        # Code Intelligence endpoints
        self.app.router.add_post("/api/v1/code/analyze", self._analyze_code)
        self.app.router.add_post("/api/v1/code/suggestions", self._get_code_suggestions)
        self.app.router.add_post("/api/v1/code/review", self._review_code)
        
        # Agent endpoints
        self.app.router.add_post("/api/v1/agents/execute", self._execute_agent_task)
        self.app.router.add_get("/api/v1/agents/status/{task_id}", self._get_task_status)
        
        # Context endpoints
        self.app.router.add_post("/api/v1/context/search", self._search_context)
        self.app.router.add_post("/api/v1/context/store", self._store_context)
        
        # Webhook endpoints
        self.app.router.add_post("/api/v1/webhooks", self._create_webhook)
        self.app.router.add_get("/api/v1/webhooks", self._list_webhooks)
        self.app.router.add_delete("/api/v1/webhooks/{webhook_id}", self._delete_webhook)
        
        # Analytics endpoints
        self.app.router.add_get("/api/v1/analytics/usage", self._get_usage_analytics)
        self.app.router.add_get("/api/v1/analytics/api-keys/{key_id}", self._get_api_key_analytics)
        
        # Health check
        self.app.router.add_get("/health", self._health_check)
        
        # API documentation
        self.app.router.add_get("/api/docs", self._api_docs)
    
    @web.middleware
    async def _auth_middleware(self, request: Request, handler: Callable) -> Response:
        """Authentication middleware"""
        # Skip auth for health check and docs
        if request.path in ["/health", "/api/docs"]:
            return await handler(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return web.json_response({"error": "Missing authorization header"}, status=401)
        
        # Parse authorization header
        try:
            auth_type, token = auth_header.split(" ", 1)
        except ValueError:
            return web.json_response({"error": "Invalid authorization header"}, status=401)
        
        # Validate token
        if auth_type.lower() == "bearer":
            # JWT token
            payload = await self.auth_manager.validate_jwt_token(token)
            if not payload:
                return web.json_response({"error": "Invalid JWT token"}, status=401)
            request["user"] = payload
        elif auth_type.lower() == "apikey":
            # API key
            api_key = await self.auth_manager.validate_api_key(token)
            if not api_key:
                return web.json_response({"error": "Invalid API key"}, status=401)
            request["api_key"] = api_key
        else:
            return web.json_response({"error": "Unsupported authorization type"}, status=401)
        
        return await handler(request)
    
    @web.middleware
    async def _rate_limit_middleware(self, request: Request, handler: Callable) -> Response:
        """Rate limiting middleware"""
        # Skip rate limiting for health check
        if request.path == "/health":
            return await handler(request)
        
        # Get rate limit key
        if "api_key" in request:
            rate_limit_key = f"api_key:{request['api_key'].key_id}"
            limit = request["api_key"].rate_limit
        elif "user" in request:
            rate_limit_key = f"user:{request['user']['user_id']}"
            limit = 1000  # Default limit for JWT users
        else:
            return web.json_response({"error": "No authentication found"}, status=401)
        
        # Check rate limit
        allowed, info = await self.rate_limiter.is_allowed(rate_limit_key, limit)
        
        if not allowed:
            response = web.json_response({
                "error": "Rate limit exceeded",
                "limit": info["limit"],
                "retry_after": info["retry_after"]
            }, status=429)
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset_time"])
            response.headers["Retry-After"] = str(info["retry_after"])
            return response
        
        # Add rate limit headers to response
        response = await handler(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset_time"])
        
        return response
    
    @web.middleware
    async def _analytics_middleware(self, request: Request, handler: Callable) -> Response:
        """Analytics middleware"""
        start_time = time.time()
        
        # Process request
        response = await handler(request)
        
        # Record analytics (skip for health check)
        if request.path != "/health":
            response_time = time.time() - start_time
            
            api_request = APIRequest(
                request_id=f"{int(time.time() * 1000000)}",  # Microsecond timestamp
                api_key_id=request.get("api_key", {}).get("key_id", "unknown"),
                endpoint=request.path,
                method=request.method,
                timestamp=datetime.now(),
                response_time=response_time,
                status_code=response.status,
                user_agent=request.headers.get("User-Agent"),
                ip_address=request.remote
            )
            
            # Record asynchronously
            asyncio.create_task(self.usage_analytics.record_api_request(api_request))
        
        return response
    
    @web.middleware
    async def _cors_middleware(self, request: Request, handler: Callable) -> Response:
        """CORS middleware"""
        if request.method == "OPTIONS":
            response = web.Response()
        else:
            response = await handler(request)
        
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response
    
    # API endpoint handlers
    async def _analyze_code(self, request: Request) -> Response:
        """Analyze code endpoint"""
        try:
            data = await request.json()
            code = data.get("code")
            language = data.get("language", "python")
            
            if not code:
                return web.json_response({"error": "Code is required"}, status=400)
            
            # Perform code analysis
            analysis = await self.code_intelligence.analyze_code_semantics(code, language)
            
            return web.json_response({
                "analysis": asdict(analysis),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Code analysis error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _get_code_suggestions(self, request: Request) -> Response:
        """Get code suggestions endpoint"""
        try:
            data = await request.json()
            code = data.get("code")
            cursor_position = data.get("cursor_position", 0)
            language = data.get("language", "python")
            
            if not code:
                return web.json_response({"error": "Code is required"}, status=400)
            
            # Get code suggestions
            suggestions = await self.code_intelligence.get_code_suggestions(
                code, cursor_position, language
            )
            
            return web.json_response({
                "suggestions": [asdict(s) for s in suggestions],
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Code suggestions error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _review_code(self, request: Request) -> Response:
        """Review code endpoint"""
        try:
            data = await request.json()
            code = data.get("code")
            language = data.get("language", "python")
            
            if not code:
                return web.json_response({"error": "Code is required"}, status=400)
            
            # Perform code review
            review = await self.code_intelligence.review_code(code, language)
            
            return web.json_response({
                "review": asdict(review),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Code review error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _execute_agent_task(self, request: Request) -> Response:
        """Execute agent task endpoint"""
        try:
            data = await request.json()
            agent_type = data.get("agent_type")
            task = data.get("task")
            
            if not agent_type or not task:
                return web.json_response({"error": "Agent type and task are required"}, status=400)
            
            # Execute agent task
            task_id = await self.agent_coordinator.execute_task(agent_type, task)
            
            return web.json_response({
                "task_id": task_id,
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Agent execution error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _get_task_status(self, request: Request) -> Response:
        """Get task status endpoint"""
        try:
            task_id = request.match_info["task_id"]
            
            # Get task status
            status = await self.agent_coordinator.get_task_status(task_id)
            
            return web.json_response({
                "task_id": task_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Task status error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _search_context(self, request: Request) -> Response:
        """Search context endpoint"""
        try:
            data = await request.json()
            query = data.get("query")
            
            if not query:
                return web.json_response({"error": "Query is required"}, status=400)
            
            # Search context
            results = await self.context_engine.retrieve_relevant_context(query)
            
            return web.json_response({
                "results": asdict(results),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Context search error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _store_context(self, request: Request) -> Response:
        """Store context endpoint"""
        try:
            data = await request.json()
            context_data = data.get("context")
            
            if not context_data:
                return web.json_response({"error": "Context data is required"}, status=400)
            
            # Store context
            context_id = await self.context_engine.store_context(context_data)
            
            return web.json_response({
                "context_id": context_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Context storage error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _create_webhook(self, request: Request) -> Response:
        """Create webhook endpoint"""
        try:
            data = await request.json()
            
            webhook = WebhookEndpoint(
                id=data.get("id", f"webhook_{int(time.time())}"),
                url=data["url"],
                events=data["events"],
                secret=data.get("secret"),
                headers=data.get("headers", {}),
                retry_count=data.get("retry_count", 3),
                timeout=data.get("timeout", 30),
                is_active=data.get("is_active", True),
                created_at=datetime.now(),
                last_triggered=None
            )
            
            self.webhook_manager.register_webhook(webhook)
            
            return web.json_response({
                "webhook_id": webhook.id,
                "status": "created",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Webhook creation error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _list_webhooks(self, request: Request) -> Response:
        """List webhooks endpoint"""
        try:
            webhooks = [asdict(webhook) for webhook in self.webhook_manager.webhooks.values()]
            
            return web.json_response({
                "webhooks": webhooks,
                "count": len(webhooks),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Webhook listing error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _delete_webhook(self, request: Request) -> Response:
        """Delete webhook endpoint"""
        try:
            webhook_id = request.match_info["webhook_id"]
            
            self.webhook_manager.unregister_webhook(webhook_id)
            
            return web.json_response({
                "webhook_id": webhook_id,
                "status": "deleted",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Webhook deletion error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _get_usage_analytics(self, request: Request) -> Response:
        """Get usage analytics endpoint"""
        try:
            # Parse query parameters
            start_date_str = request.query.get("start_date")
            end_date_str = request.query.get("end_date")
            
            if not start_date_str or not end_date_str:
                return web.json_response({"error": "start_date and end_date are required"}, status=400)
            
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
            
            # Get usage statistics
            stats = await self.usage_analytics.get_usage_stats(start_date, end_date)
            
            return web.json_response({
                "analytics": stats,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Usage analytics error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _get_api_key_analytics(self, request: Request) -> Response:
        """Get API key analytics endpoint"""
        try:
            key_id = request.match_info["key_id"]
            
            # Get API key usage statistics
            stats = await self.usage_analytics.get_api_key_usage(key_id)
            
            return web.json_response({
                "api_key_id": key_id,
                "analytics": stats,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"API key analytics error: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def _health_check(self, request: Request) -> Response:
        """Health check endpoint"""
        try:
            # Check Redis connection
            await self.redis.ping()
            
            return web.json_response({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            })
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return web.json_response({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=503)
    
    async def _api_docs(self, request: Request) -> Response:
        """API documentation endpoint"""
        docs = {
            "title": "CodeGenie API",
            "version": "1.0.0",
            "description": "REST API for CodeGenie AI coding assistant",
            "endpoints": {
                "POST /api/v1/code/analyze": "Analyze code for issues and improvements",
                "POST /api/v1/code/suggestions": "Get code completion suggestions",
                "POST /api/v1/code/review": "Perform automated code review",
                "POST /api/v1/agents/execute": "Execute agent task",
                "GET /api/v1/agents/status/{task_id}": "Get task execution status",
                "POST /api/v1/context/search": "Search context database",
                "POST /api/v1/context/store": "Store context data",
                "POST /api/v1/webhooks": "Create webhook endpoint",
                "GET /api/v1/webhooks": "List webhook endpoints",
                "DELETE /api/v1/webhooks/{webhook_id}": "Delete webhook endpoint",
                "GET /api/v1/analytics/usage": "Get usage analytics",
                "GET /api/v1/analytics/api-keys/{key_id}": "Get API key analytics",
                "GET /health": "Health check endpoint"
            },
            "authentication": {
                "api_key": "Use 'Authorization: ApiKey <your-api-key>' header",
                "jwt": "Use 'Authorization: Bearer <jwt-token>' header"
            }
        }
        
        return web.json_response(docs)
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start API server"""
        try:
            # Start webhook workers
            await self.webhook_manager.start_workers()
            
            # Start web server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, host, port)
            await site.start()
            
            self.logger.info(f"API server started on {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Error starting API server: {e}")
            raise
    
    async def stop_server(self):
        """Stop API server"""
        try:
            # Stop webhook workers
            await self.webhook_manager.stop_workers()
            
            # Close Redis connection
            await self.redis.close()
            
            self.logger.info("API server stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping API server: {e}")
    
    # Utility methods for API key management
    def create_api_key(self, name: str, permissions: List[str], rate_limit: int = 1000) -> tuple[str, APIKey]:
        """Create new API key"""
        return self.auth_manager.generate_api_key(name, permissions, rate_limit)
    
    def revoke_api_key(self, key_hash: str) -> bool:
        """Revoke API key"""
        if key_hash in self.auth_manager.api_keys:
            self.auth_manager.api_keys[key_hash].is_active = False
            return True
        return False
    
    async def trigger_webhook_event(self, event_type: str, data: Dict[str, Any], source: str = "api"):
        """Trigger webhook event"""
        event = WebhookEvent(
            event_id=f"event_{int(time.time() * 1000000)}",
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            source=source,
            webhook_endpoints=[]
        )
        
        await self.webhook_manager.trigger_event(event)