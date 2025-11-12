"""
Web interface for CodeGenie with advanced workflow management.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from datetime import datetime
import aiohttp
from aiohttp import web, WSMsgType
import aiohttp_cors
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import weakref

from ..core.agent import CodeGenieAgent
from ..core.config import Config
from .web_components import (
    WebComponentsManager, ExecutionPlan, PlanStep, FileDiff,
    ApprovalRequest, ProgressMetrics
)
from .realtime_updates import (
    RealtimeUpdateManager, ProgressTracker, CommandOutputStreamer,
    PlanProgressTracker, ProgressUpdate, CommandOutput
)

logger = logging.getLogger(__name__)


class WebInterface:
    """Advanced web interface for CodeGenie."""
    
    def __init__(self, agent: CodeGenieAgent, config: Config):
        self.agent = agent
        self.config = config
        self.app = None
        self.websockets = weakref.WeakSet()
        self.active_workflows = {}
        self.components_manager = WebComponentsManager()
        self.approval_requests = {}
        self.progress_metrics = {}
        self.recent_activities = []
        
        # Real-time updates
        self.realtime_manager = RealtimeUpdateManager()
        self.progress_tracker = ProgressTracker(self.realtime_manager)
        self.command_streamer = CommandOutputStreamer(self.realtime_manager)
        self.plan_tracker = PlanProgressTracker(self.realtime_manager)
        
    async def start_server(self, host: str = "localhost", port: int = 8080) -> None:
        """Start the web server."""
        
        # Start real-time update manager
        await self.realtime_manager.start()
        
        # Create aiohttp application
        self.app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Setup session storage
        # Generate a proper Fernet key (32 url-safe base64-encoded bytes)
        from cryptography.fernet import Fernet
        import os
        
        # Try to load key from environment or generate a new one
        secret_key_str = os.getenv('CODEGENIE_SECRET_KEY')
        if secret_key_str:
            secret_key = secret_key_str.encode()
        else:
            # Generate a new Fernet key
            secret_key = Fernet.generate_key()
            logger.warning("Using generated secret key. Set CODEGENIE_SECRET_KEY environment variable for production.")
        
        setup_session(self.app, EncryptedCookieStorage(secret_key))
        
        # Setup routes
        self._setup_routes(cors)
        
        # Setup static files
        self._setup_static_files()
        
        # Start server
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"Web interface started on http://{host}:{port}")
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down web interface...")
        finally:
            await self.realtime_manager.stop()
            await runner.cleanup()
    
    def _setup_routes(self, cors) -> None:
        """Setup web routes."""
        
        # API routes
        cors.add(self.app.router.add_get('/api/status', self.get_status))
        cors.add(self.app.router.add_post('/api/chat', self.handle_chat))
        cors.add(self.app.router.add_get('/api/workflows', self.get_workflows))
        cors.add(self.app.router.add_post('/api/workflows', self.create_workflow))
        cors.add(self.app.router.add_post('/api/workflows/{workflow_id}/execute', self.execute_workflow))
        cors.add(self.app.router.add_get('/api/agents', self.get_agents))
        cors.add(self.app.router.add_post('/api/agents/coordinate', self.coordinate_agents))
        cors.add(self.app.router.add_get('/api/learning/profile', self.get_learning_profile))
        cors.add(self.app.router.add_post('/api/learning/feedback', self.provide_feedback))
        cors.add(self.app.router.add_get('/api/config', self.get_config))
        cors.add(self.app.router.add_post('/api/config', self.update_config))
        
        # New component routes
        cors.add(self.app.router.add_get('/api/plans/{plan_id}', self.get_plan))
        cors.add(self.app.router.add_get('/api/diffs/{diff_id}', self.get_diff))
        cors.add(self.app.router.add_get('/api/approvals', self.get_approvals))
        cors.add(self.app.router.add_post('/api/approvals/{request_id}/approve', self.approve_request))
        cors.add(self.app.router.add_post('/api/approvals/{request_id}/reject', self.reject_request))
        cors.add(self.app.router.add_get('/api/progress', self.get_progress))
        
        # WebSocket route
        cors.add(self.app.router.add_get('/ws', self.websocket_handler))
        
        # Main page
        cors.add(self.app.router.add_get('/', self.serve_index))
        cors.add(self.app.router.add_get('/{path:.*}', self.serve_static))
    
    def _setup_static_files(self) -> None:
        """Setup static file serving."""
        
        # Create basic HTML interface
        html_content = self._generate_html_interface()
        
        # Store in memory for now (in production, use proper static files)
        self.static_files = {
            'index.html': html_content,
            'style.css': self._generate_css(),
            'script.js': self._generate_javascript()
        }
    
    async def serve_index(self, request) -> web.Response:
        """Serve the main index page."""
        return web.Response(
            text=self.static_files['index.html'],
            content_type='text/html'
        )
    
    async def serve_static(self, request) -> web.Response:
        """Serve static files."""
        path = request.match_info['path']
        
        if path in self.static_files:
            if path.endswith('.css'):
                content_type = 'text/css'
            elif path.endswith('.js'):
                content_type = 'application/javascript'
            else:
                content_type = 'text/plain'
            
            return web.Response(
                text=self.static_files[path],
                content_type=content_type
            )
        
        return web.Response(status=404, text="File not found")
    
    async def websocket_handler(self, request) -> web.WebSocketResponse:
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        
        # Get subscription channels from query params
        channels = request.rel_url.query.get('channels', 'global').split(',')
        self.realtime_manager.register_websocket(ws, channels)
        
        try:
            # Send initial connection message
            await ws.send_str(json.dumps({
                'type': 'connected',
                'message': 'WebSocket connected',
                'channels': channels,
                'timestamp': datetime.now().isoformat()
            }))
            
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_websocket_message(ws, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON'
                        }))
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            logger.error(f'WebSocket handler error: {e}')
        finally:
            self.websockets.discard(ws)
            self.realtime_manager.unregister_websocket(ws)
        
        return ws
    
    async def _handle_websocket_message(self, ws: web.WebSocketResponse, data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket messages."""
        
        message_type = data.get('type')
        
        if message_type == 'chat':
            # Handle chat message
            user_input = data.get('message', '')
            response = await self.agent.process_user_input(user_input)
            
            await ws.send_str(json.dumps({
                'type': 'chat_response',
                'message': response,
                'timestamp': asyncio.get_event_loop().time()
            }))
        
        elif message_type == 'workflow_progress':
            # Request workflow progress updates
            workflow_id = data.get('workflow_id')
            if workflow_id in self.active_workflows:
                progress = self.active_workflows[workflow_id]
                await ws.send_str(json.dumps({
                    'type': 'workflow_progress',
                    'workflow_id': workflow_id,
                    'progress': progress
                }))
    
    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected WebSocket clients."""
        if self.websockets:
            message_str = json.dumps(message)
            for ws in list(self.websockets):
                try:
                    await ws.send_str(message_str)
                except Exception as e:
                    logger.error(f'Error broadcasting to WebSocket: {e}')
                    self.websockets.discard(ws)
    
    # API Handlers
    
    async def get_status(self, request) -> web.Response:
        """Get agent status."""
        try:
            status = await self.agent.get_status()
            return web.json_response(status)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_chat(self, request) -> web.Response:
        """Handle chat messages."""
        try:
            data = await request.json()
            user_input = data.get('message', '')
            
            response = await self.agent.process_user_input(user_input)
            
            return web.json_response({
                'response': response,
                'timestamp': asyncio.get_event_loop().time()
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_workflows(self, request) -> web.Response:
        """Get available workflows."""
        try:
            # In a real implementation, this would fetch from workflow engine
            workflows = [
                {
                    'id': 'workflow_1',
                    'name': 'Create REST API',
                    'description': 'Create a complete REST API with authentication',
                    'status': 'completed',
                    'steps': 5,
                    'progress': 100
                },
                {
                    'id': 'workflow_2',
                    'name': 'Add Unit Tests',
                    'description': 'Add comprehensive unit tests to the project',
                    'status': 'in_progress',
                    'steps': 3,
                    'progress': 60
                }
            ]
            
            return web.json_response({'workflows': workflows})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def create_workflow(self, request) -> web.Response:
        """Create a new workflow."""
        try:
            data = await request.json()
            goal = data.get('goal', '')
            
            if not goal:
                return web.json_response({'error': 'Goal is required'}, status=400)
            
            # Create workflow using workflow engine
            if hasattr(self.agent, 'workflow_engine') and self.agent.workflow_engine:
                plan = await self.agent.workflow_engine.create_execution_plan(goal)
                
                workflow_data = {
                    'id': f'workflow_{len(self.active_workflows) + 1}',
                    'goal': goal,
                    'plan': plan.to_dict() if hasattr(plan, 'to_dict') else str(plan),
                    'status': 'created',
                    'created_at': asyncio.get_event_loop().time()
                }
                
                self.active_workflows[workflow_data['id']] = workflow_data
                
                return web.json_response(workflow_data)
            else:
                return web.json_response({'error': 'Workflow engine not available'}, status=503)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def execute_workflow(self, request) -> web.Response:
        """Execute a workflow."""
        try:
            workflow_id = request.match_info['workflow_id']
            
            if workflow_id not in self.active_workflows:
                return web.json_response({'error': 'Workflow not found'}, status=404)
            
            workflow = self.active_workflows[workflow_id]
            
            # Execute workflow using workflow engine
            if hasattr(self.agent, 'workflow_engine') and self.agent.workflow_engine:
                # Start execution in background
                asyncio.create_task(self._execute_workflow_background(workflow_id, workflow))
                
                return web.json_response({
                    'message': 'Workflow execution started',
                    'workflow_id': workflow_id
                })
            else:
                return web.json_response({'error': 'Workflow engine not available'}, status=503)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def _execute_workflow_background(self, workflow_id: str, workflow: Dict[str, Any]) -> None:
        """Execute workflow in background and broadcast progress."""
        try:
            goal = workflow['goal']
            
            # Update status
            workflow['status'] = 'executing'
            await self.broadcast_message({
                'type': 'workflow_status',
                'workflow_id': workflow_id,
                'status': 'executing'
            })
            
            # Execute workflow
            result = await self.agent.workflow_engine.execute_autonomous_workflow(goal, {})
            
            # Update final status
            workflow['status'] = 'completed' if result.success else 'failed'
            workflow['result'] = result.to_dict() if hasattr(result, 'to_dict') else str(result)
            
            await self.broadcast_message({
                'type': 'workflow_completed',
                'workflow_id': workflow_id,
                'status': workflow['status'],
                'result': workflow.get('result')
            })
            
        except Exception as e:
            logger.error(f'Error executing workflow {workflow_id}: {e}')
            workflow['status'] = 'failed'
            workflow['error'] = str(e)
            
            await self.broadcast_message({
                'type': 'workflow_error',
                'workflow_id': workflow_id,
                'error': str(e)
            })
    
    async def get_agents(self, request) -> web.Response:
        """Get available agents."""
        try:
            agents = [
                {'name': 'architect', 'status': 'active', 'specialization': 'System design'},
                {'name': 'developer', 'status': 'active', 'specialization': 'Code implementation'},
                {'name': 'tester', 'status': 'active', 'specialization': 'Quality assurance'},
                {'name': 'security', 'status': 'active', 'specialization': 'Security analysis'},
                {'name': 'performance', 'status': 'active', 'specialization': 'Performance optimization'},
                {'name': 'documentation', 'status': 'active', 'specialization': 'Documentation'},
                {'name': 'refactoring', 'status': 'active', 'specialization': 'Code improvement'}
            ]
            
            return web.json_response({'agents': agents})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def coordinate_agents(self, request) -> web.Response:
        """Coordinate multiple agents."""
        try:
            data = await request.json()
            task = data.get('task', '')
            agents = data.get('agents', [])
            
            if not task:
                return web.json_response({'error': 'Task is required'}, status=400)
            
            # Coordinate agents using agent coordinator
            if hasattr(self.agent, 'agent_coordinator') and self.agent.agent_coordinator:
                assignments = await self.agent.agent_coordinator.delegate_task({
                    'description': task,
                    'requested_agents': agents
                })
                
                result = await self.agent.agent_coordinator.coordinate_execution(assignments)
                
                return web.json_response({
                    'success': result.success,
                    'assignments': [a.to_dict() if hasattr(a, 'to_dict') else str(a) for a in assignments],
                    'result': result.to_dict() if hasattr(result, 'to_dict') else str(result)
                })
            else:
                return web.json_response({'error': 'Agent coordinator not available'}, status=503)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_learning_profile(self, request) -> web.Response:
        """Get learning profile."""
        try:
            if hasattr(self.agent, 'learning_engine') and self.agent.learning_engine:
                profile = await self.agent.learning_engine.get_user_profile()
                return web.json_response(profile)
            else:
                return web.json_response({'error': 'Learning engine not available'}, status=503)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def provide_feedback(self, request) -> web.Response:
        """Provide feedback on suggestions."""
        try:
            data = await request.json()
            
            if hasattr(self.agent, 'learning_engine') and self.agent.learning_engine:
                await self.agent.learning_engine.process_feedback(data)
                return web.json_response({'message': 'Feedback recorded'})
            else:
                return web.json_response({'error': 'Learning engine not available'}, status=503)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_config(self, request) -> web.Response:
        """Get current configuration."""
        try:
            config_dict = {
                'autonomous_workflows': getattr(self.config, 'autonomous_workflows', False),
                'multi_agent_coordination': getattr(self.config, 'multi_agent_coordination', False),
                'adaptive_learning': getattr(self.config, 'adaptive_learning', True),
                'debug': getattr(self.config, 'debug', False),
                'verbose': getattr(self.config, 'verbose', False)
            }
            
            return web.json_response(config_dict)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def update_config(self, request) -> web.Response:
        """Update configuration."""
        try:
            data = await request.json()
            
            # Update configuration
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            return web.json_response({'message': 'Configuration updated'})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_plan(self, request) -> web.Response:
        """Get execution plan visualization."""
        try:
            plan_id = request.match_info['plan_id']
            
            # Get plan from planning agent
            if hasattr(self.agent, 'planning_agent') and self.agent.planning_agent:
                # Create sample plan for demonstration
                plan = ExecutionPlan(
                    id=plan_id,
                    name="Create REST API",
                    description="Build a complete REST API with authentication",
                    steps=[
                        PlanStep(
                            id="step1",
                            description="Create project structure",
                            status="completed",
                            progress=100,
                            dependencies=[],
                            estimated_duration=30
                        ),
                        PlanStep(
                            id="step2",
                            description="Implement authentication",
                            status="in_progress",
                            progress=60,
                            dependencies=["step1"],
                            estimated_duration=120
                        ),
                        PlanStep(
                            id="step3",
                            description="Create API endpoints",
                            status="pending",
                            progress=0,
                            dependencies=["step2"],
                            estimated_duration=180
                        )
                    ],
                    status="in_progress",
                    created_at=datetime.now().isoformat(),
                    started_at=datetime.now().isoformat()
                )
                
                html = self.components_manager.render_plan(plan)
                return web.json_response({
                    'html': html,
                    'plan': plan.to_dict()
                })
            else:
                return web.json_response({'error': 'Planning agent not available'}, status=503)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_diff(self, request) -> web.Response:
        """Get file diff visualization."""
        try:
            diff_id = request.match_info['diff_id']
            
            # Create sample diff for demonstration
            diff = FileDiff(
                file_path="src/api/auth.py",
                old_content="",
                new_content="",
                diff_lines=[
                    {'type': 'context', 'old_line': 1, 'new_line': 1, 'content': 'from flask import Flask, request'},
                    {'type': 'addition', 'old_line': '', 'new_line': 2, 'content': 'from flask_jwt_extended import JWTManager'},
                    {'type': 'context', 'old_line': 2, 'new_line': 3, 'content': ''},
                    {'type': 'context', 'old_line': 3, 'new_line': 4, 'content': 'app = Flask(__name__)'},
                    {'type': 'addition', 'old_line': '', 'new_line': 5, 'content': 'jwt = JWTManager(app)'},
                    {'type': 'deletion', 'old_line': 4, 'new_line': '', 'content': '# TODO: Add authentication'},
                    {'type': 'addition', 'old_line': '', 'new_line': 6, 'content': '@app.route("/login", methods=["POST"])'},
                    {'type': 'addition', 'old_line': '', 'new_line': 7, 'content': 'def login():'},
                    {'type': 'addition', 'old_line': '', 'new_line': 8, 'content': '    return {"token": "jwt_token"}'}
                ],
                additions=5,
                deletions=1
            )
            
            html = self.components_manager.render_diff(diff)
            return web.json_response({
                'html': html,
                'diff': {
                    'file_path': diff.file_path,
                    'additions': diff.additions,
                    'deletions': diff.deletions
                }
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_approvals(self, request) -> web.Response:
        """Get pending approval requests."""
        try:
            # Create sample approval requests
            requests = [
                ApprovalRequest(
                    id="approval1",
                    title="Create new file: auth.py",
                    description="Create authentication module with JWT support",
                    operation_type="file_create",
                    risk_level="safe",
                    details={
                        'file_path': 'src/api/auth.py',
                        'size': '2.5 KB',
                        'lines': 85
                    },
                    status="pending",
                    timestamp=datetime.now().isoformat()
                ),
                ApprovalRequest(
                    id="approval2",
                    title="Execute command: npm install",
                    description="Install required dependencies for the project",
                    operation_type="command_execute",
                    risk_level="risky",
                    details={
                        'command': 'npm install express jsonwebtoken',
                        'working_directory': '/project/root'
                    },
                    status="pending",
                    timestamp=datetime.now().isoformat()
                )
            ]
            
            html_list = [self.components_manager.render_approval(req) for req in requests]
            
            return web.json_response({
                'html': html_list,
                'requests': [asdict(req) for req in requests]
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def approve_request(self, request) -> web.Response:
        """Approve an approval request."""
        try:
            request_id = request.match_info['request_id']
            
            # Update request status
            if request_id in self.approval_requests:
                self.approval_requests[request_id]['status'] = 'approved'
                
                # Broadcast update
                await self.broadcast_message({
                    'type': 'approval_updated',
                    'request_id': request_id,
                    'status': 'approved'
                })
                
                return web.json_response({'message': 'Request approved'})
            else:
                return web.json_response({'error': 'Request not found'}, status=404)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def reject_request(self, request) -> web.Response:
        """Reject an approval request."""
        try:
            request_id = request.match_info['request_id']
            
            # Update request status
            if request_id in self.approval_requests:
                self.approval_requests[request_id]['status'] = 'rejected'
                
                # Broadcast update
                await self.broadcast_message({
                    'type': 'approval_updated',
                    'request_id': request_id,
                    'status': 'rejected'
                })
                
                return web.json_response({'message': 'Request rejected'})
            else:
                return web.json_response({'error': 'Request not found'}, status=404)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_progress(self, request) -> web.Response:
        """Get progress dashboard data."""
        try:
            # Create sample progress metrics
            metrics = ProgressMetrics(
                total_tasks=10,
                completed_tasks=6,
                failed_tasks=1,
                in_progress_tasks=2,
                estimated_time_remaining=300,
                elapsed_time=450
            )
            
            activities = [
                {'icon': '✅', 'text': 'Completed: Create project structure', 'time': '2m ago'},
                {'icon': '✅', 'text': 'Completed: Install dependencies', 'time': '5m ago'},
                {'icon': '🔄', 'text': 'In progress: Implement authentication', 'time': 'now'},
                {'icon': '⏳', 'text': 'Pending: Create API endpoints', 'time': 'queued'},
                {'icon': '❌', 'text': 'Failed: Run tests (retrying)', 'time': '1m ago'}
            ]
            
            html = self.components_manager.render_dashboard(metrics, activities)
            
            return web.json_response({
                'html': html,
                'metrics': asdict(metrics),
                'activities': activities
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    def _generate_html_interface(self) -> str:
        """Generate the main HTML interface."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeGenie - Advanced AI Coding Agent</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>🧞 CodeGenie</h1>
            <p>Advanced AI Coding Agent</p>
        </header>
        
        <nav>
            <button onclick="showTab('chat')" class="tab-button active">💬 Chat</button>
            <button onclick="showTab('workflows')" class="tab-button">🔄 Workflows</button>
            <button onclick="showTab('plans')" class="tab-button">📋 Plans</button>
            <button onclick="showTab('approvals')" class="tab-button">✓ Approvals</button>
            <button onclick="showTab('progress')" class="tab-button">📊 Progress</button>
            <button onclick="showTab('agents')" class="tab-button">👥 Agents</button>
            <button onclick="showTab('learning')" class="tab-button">🎓 Learning</button>
            <button onclick="showTab('config')" class="tab-button">⚙️ Config</button>
        </nav>
        
        <main>
            <!-- Chat Tab -->
            <div id="chat-tab" class="tab-content active">
                <div id="chat-messages"></div>
                <div class="chat-input">
                    <input type="text" id="chat-input" placeholder="Ask me anything about your code...">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <!-- Workflows Tab -->
            <div id="workflows-tab" class="tab-content">
                <div class="section">
                    <h2>Create New Workflow</h2>
                    <input type="text" id="workflow-goal" placeholder="Describe your goal...">
                    <button onclick="createWorkflow()">Create Workflow</button>
                </div>
                
                <div class="section">
                    <h2>Active Workflows</h2>
                    <div id="workflows-list"></div>
                </div>
            </div>
            
            <!-- Plans Tab -->
            <div id="plans-tab" class="tab-content">
                <div class="section">
                    <h2>Execution Plans</h2>
                    <div id="plans-list"></div>
                </div>
            </div>
            
            <!-- Approvals Tab -->
            <div id="approvals-tab" class="tab-content">
                <div class="section">
                    <h2>Pending Approvals</h2>
                    <div id="approvals-list"></div>
                </div>
            </div>
            
            <!-- Progress Tab -->
            <div id="progress-tab" class="tab-content">
                <div id="progress-dashboard"></div>
            </div>
            
            <!-- Agents Tab -->
            <div id="agents-tab" class="tab-content">
                <div class="section">
                    <h2>Available Agents</h2>
                    <div id="agents-list"></div>
                </div>
                
                <div class="section">
                    <h2>Coordinate Agents</h2>
                    <input type="text" id="coordination-task" placeholder="Describe the task...">
                    <div id="agent-selection"></div>
                    <button onclick="coordinateAgents()">Coordinate</button>
                </div>
            </div>
            
            <!-- Learning Tab -->
            <div id="learning-tab" class="tab-content">
                <div class="section">
                    <h2>Learning Profile</h2>
                    <div id="learning-profile"></div>
                </div>
                
                <div class="section">
                    <h2>Provide Feedback</h2>
                    <input type="text" id="feedback-id" placeholder="Suggestion ID">
                    <select id="feedback-rating">
                        <option value="1">1 - Poor</option>
                        <option value="2">2 - Fair</option>
                        <option value="3">3 - Good</option>
                        <option value="4">4 - Very Good</option>
                        <option value="5">5 - Excellent</option>
                    </select>
                    <input type="text" id="feedback-comment" placeholder="Optional comment">
                    <button onclick="provideFeedback()">Submit Feedback</button>
                </div>
            </div>
            
            <!-- Config Tab -->
            <div id="config-tab" class="tab-content">
                <div class="section">
                    <h2>Configuration</h2>
                    <div id="config-form"></div>
                    <button onclick="updateConfig()">Update Configuration</button>
                </div>
            </div>
        </main>
    </div>
    
    <script src="script.js"></script>
</body>
</html>
        """
    
    def _generate_css(self) -> str:
        """Generate CSS styles."""
        # Include component CSS
        component_css = self.components_manager.get_all_css()
        
        return component_css + """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

#app {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    min-height: 100vh;
    box-shadow: 0 0 20px rgba(0,0,0,0.1);
}

header {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    padding: 2rem;
    text-align: center;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

nav {
    background: #f8f9fa;
    padding: 1rem;
    display: flex;
    gap: 1rem;
    border-bottom: 1px solid #dee2e6;
}

.tab-button {
    padding: 0.75rem 1.5rem;
    border: none;
    background: white;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
}

.tab-button:hover {
    background: #e9ecef;
}

.tab-button.active {
    background: #007bff;
    color: white;
}

main {
    padding: 2rem;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.section {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
}

.section h2 {
    margin-bottom: 1rem;
    color: #495057;
}

#chat-messages {
    height: 400px;
    overflow-y: auto;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    background: white;
}

.chat-input {
    display: flex;
    gap: 1rem;
}

.chat-input input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    font-size: 1rem;
}

button {
    padding: 0.75rem 1.5rem;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.3s ease;
}

button:hover {
    background: #0056b3;
}

input, select {
    padding: 0.75rem;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    font-size: 1rem;
    margin-bottom: 1rem;
    width: 100%;
}

.message {
    margin-bottom: 1rem;
    padding: 1rem;
    border-radius: 8px;
}

.message.user {
    background: #e3f2fd;
    margin-left: 2rem;
}

.message.agent {
    background: #f3e5f5;
    margin-right: 2rem;
}

.workflow-item, .agent-item {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border: 1px solid #dee2e6;
}

.status {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}

.status.active {
    background: #d4edda;
    color: #155724;
}

.status.completed {
    background: #d1ecf1;
    color: #0c5460;
}

.status.in-progress {
    background: #fff3cd;
    color: #856404;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 0.5rem;
}

.progress-fill {
    height: 100%;
    background: #28a745;
    transition: width 0.3s ease;
}

#notifications {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: 400px;
}

.notification {
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-weight: 500;
    animation: slideIn 0.3s ease;
    transition: opacity 0.3s ease;
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.notification-success {
    background: #d1e7dd;
    color: #0f5132;
    border-left: 4px solid #198754;
}

.notification-error {
    background: #f8d7da;
    color: #842029;
    border-left: 4px solid #dc3545;
}

.notification-warning {
    background: #fff3cd;
    color: #856404;
    border-left: 4px solid #ffc107;
}

.notification-info {
    background: #cfe2ff;
    color: #084298;
    border-left: 4px solid #0d6efd;
}

.command-output {
    background: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 0.875rem;
    padding: 1rem;
    border-radius: 8px;
    max-height: 400px;
    overflow-y: auto;
    margin-top: 1rem;
}

.command-line {
    padding: 0.25rem 0;
    white-space: pre-wrap;
    word-break: break-all;
}

.command-line.stdout {
    color: #d4d4d4;
}

.command-line.stderr {
    color: #f48771;
}

.command-line.completion {
    color: #4ec9b0;
    font-weight: 600;
}
        """
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for the interface."""
        return """
let ws = null;
let currentTab = 'chat';

// Initialize WebSocket connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const channels = 'global,progress,commands,plans,approvals';
    const wsUrl = `${protocol}//${window.location.host}/ws?channels=${channels}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        showNotification('Connected to server', 'success');
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
        showNotification('Disconnected from server. Reconnecting...', 'warning');
        // Attempt to reconnect after 3 seconds
        setTimeout(initWebSocket, 3000);
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        showNotification('Connection error', 'error');
    };
}

function handleWebSocketMessage(data) {
    switch(data.type) {
        case 'connected':
            console.log('Connected to channels:', data.channels);
            break;
        case 'chat_response':
            addChatMessage(data.message, 'agent');
            break;
        case 'workflow_status':
            updateWorkflowStatus(data.workflow_id, data.status);
            break;
        case 'workflow_completed':
            updateWorkflowStatus(data.workflow_id, data.status);
            loadWorkflows();
            break;
        case 'workflow_error':
            console.error('Workflow error:', data.error);
            showNotification('Workflow error: ' + data.error, 'error');
            break;
        case 'progress_update':
            handleProgressUpdate(data.data);
            break;
        case 'command_output':
            handleCommandOutput(data.data);
            break;
        case 'plan_update':
            handlePlanUpdate(data.data);
            break;
        case 'approval_request':
            handleApprovalRequest(data.data);
            break;
        case 'approval_updated':
            if (currentTab === 'approvals') {
                loadApprovals();
            }
            break;
        case 'notification':
            showNotification(data.data.message, data.data.level);
            break;
    }
}

function handleProgressUpdate(data) {
    console.log('Progress update:', data);
    
    // Update progress dashboard if visible
    if (currentTab === 'progress') {
        loadProgress();
    }
    
    // Show notification for important updates
    if (data.type === 'task_completed') {
        showNotification(data.message, 'success');
    } else if (data.type === 'task_failed') {
        showNotification(data.message, 'error');
    }
}

function handleCommandOutput(data) {
    console.log('Command output:', data);
    
    // Add to command output display if exists
    const outputElement = document.getElementById('command-output-' + data.command_id);
    if (outputElement) {
        const line = document.createElement('div');
        line.className = 'command-line ' + data.output_type;
        line.textContent = data.content;
        outputElement.appendChild(line);
        outputElement.scrollTop = outputElement.scrollHeight;
    }
}

function handlePlanUpdate(data) {
    console.log('Plan update:', data);
    
    // Update plan visualization if visible
    if (currentTab === 'plans') {
        loadPlans();
    }
    
    // Update step status in UI
    const stepElement = document.querySelector(`[data-step-id="${data.step_id}"]`);
    if (stepElement) {
        stepElement.className = `plan-step step-${data.status}`;
        const progressFill = stepElement.querySelector('.step-progress-fill');
        if (progressFill) {
            progressFill.style.width = data.progress + '%';
        }
    }
}

function handleApprovalRequest(data) {
    console.log('Approval request:', data);
    
    // Reload approvals if on that tab
    if (currentTab === 'approvals') {
        loadApprovals();
    }
    
    // Show notification
    showNotification('New approval request: ' + data.title, 'info');
}

function showNotification(message, level = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${level}`;
    notification.textContent = message;
    
    // Add to page
    let container = document.getElementById('notifications');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notifications';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Tab management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
    
    currentTab = tabName;
    
    // Load tab-specific data
    switch(tabName) {
        case 'workflows':
            loadWorkflows();
            break;
        case 'plans':
            loadPlans();
            break;
        case 'approvals':
            loadApprovals();
            break;
        case 'progress':
            loadProgress();
            break;
        case 'agents':
            loadAgents();
            break;
        case 'learning':
            loadLearningProfile();
            break;
        case 'config':
            loadConfig();
            break;
    }
}

// Chat functionality
function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addChatMessage(message, 'user');
    input.value = '';
    
    // Send via WebSocket if available, otherwise use HTTP
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'chat',
            message: message
        }));
    } else {
        // Fallback to HTTP
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                addChatMessage(data.response, 'agent');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addChatMessage('Error: Could not get response', 'agent');
        });
    }
}

function addChatMessage(message, sender) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'CodeGenie'}:</strong> ${message}`;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Workflow functionality
function loadWorkflows() {
    fetch('/api/workflows')
        .then(response => response.json())
        .then(data => {
            const workflowsList = document.getElementById('workflows-list');
            workflowsList.innerHTML = '';
            
            data.workflows.forEach(workflow => {
                const workflowDiv = document.createElement('div');
                workflowDiv.className = 'workflow-item';
                workflowDiv.innerHTML = `
                    <h3>${workflow.name}</h3>
                    <p>${workflow.description}</p>
                    <div class="status ${workflow.status}">${workflow.status}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${workflow.progress}%"></div>
                    </div>
                    <p>Steps: ${workflow.steps} | Progress: ${workflow.progress}%</p>
                    ${workflow.status === 'created' ? `<button onclick="executeWorkflow('${workflow.id}')">Execute</button>` : ''}
                `;
                workflowsList.appendChild(workflowDiv);
            });
        })
        .catch(error => console.error('Error loading workflows:', error));
}

function createWorkflow() {
    const goal = document.getElementById('workflow-goal').value.trim();
    
    if (!goal) {
        alert('Please enter a goal for the workflow');
        return;
    }
    
    fetch('/api/workflows', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ goal: goal })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            document.getElementById('workflow-goal').value = '';
            loadWorkflows();
        }
    })
    .catch(error => {
        console.error('Error creating workflow:', error);
        alert('Error creating workflow');
    });
}

function executeWorkflow(workflowId) {
    fetch(`/api/workflows/${workflowId}/execute`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            loadWorkflows();
        }
    })
    .catch(error => {
        console.error('Error executing workflow:', error);
        alert('Error executing workflow');
    });
}

function updateWorkflowStatus(workflowId, status) {
    // Update workflow status in the UI
    const workflowItems = document.querySelectorAll('.workflow-item');
    workflowItems.forEach(item => {
        if (item.dataset.workflowId === workflowId) {
            const statusElement = item.querySelector('.status');
            if (statusElement) {
                statusElement.textContent = status;
                statusElement.className = `status ${status}`;
            }
        }
    });
}

// Plan visualization functionality
function loadPlans() {
    // Load sample plan
    fetch('/api/plans/plan_1')
        .then(response => response.json())
        .then(data => {
            const plansList = document.getElementById('plans-list');
            plansList.innerHTML = data.html || '<p>No plans available</p>';
        })
        .catch(error => console.error('Error loading plans:', error));
}

// Approval interface functionality
function loadApprovals() {
    fetch('/api/approvals')
        .then(response => response.json())
        .then(data => {
            const approvalsList = document.getElementById('approvals-list');
            if (data.html && data.html.length > 0) {
                approvalsList.innerHTML = data.html.join('');
            } else {
                approvalsList.innerHTML = '<p>No pending approvals</p>';
            }
        })
        .catch(error => console.error('Error loading approvals:', error));
}

function approveRequest(requestId) {
    fetch(`/api/approvals/${requestId}/approve`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            loadApprovals();
        }
    })
    .catch(error => {
        console.error('Error approving request:', error);
        alert('Error approving request');
    });
}

function rejectRequest(requestId) {
    fetch(`/api/approvals/${requestId}/reject`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            loadApprovals();
        }
    })
    .catch(error => {
        console.error('Error rejecting request:', error);
        alert('Error rejecting request');
    });
}

// Progress dashboard functionality
function loadProgress() {
    fetch('/api/progress')
        .then(response => response.json())
        .then(data => {
            const progressDashboard = document.getElementById('progress-dashboard');
            progressDashboard.innerHTML = data.html || '<p>No progress data available</p>';
        })
        .catch(error => console.error('Error loading progress:', error));
}

// Agent functionality
function loadAgents() {
    fetch('/api/agents')
        .then(response => response.json())
        .then(data => {
            const agentsList = document.getElementById('agents-list');
            const agentSelection = document.getElementById('agent-selection');
            
            agentsList.innerHTML = '';
            agentSelection.innerHTML = '';
            
            data.agents.forEach(agent => {
                // Add to agents list
                const agentDiv = document.createElement('div');
                agentDiv.className = 'agent-item';
                agentDiv.innerHTML = `
                    <h3>${agent.name}</h3>
                    <p>${agent.specialization}</p>
                    <div class="status ${agent.status}">${agent.status}</div>
                `;
                agentsList.appendChild(agentDiv);
                
                // Add to selection
                const checkbox = document.createElement('label');
                checkbox.innerHTML = `
                    <input type="checkbox" value="${agent.name}"> ${agent.name} (${agent.specialization})
                `;
                agentSelection.appendChild(checkbox);
            });
        })
        .catch(error => console.error('Error loading agents:', error));
}

function coordinateAgents() {
    const task = document.getElementById('coordination-task').value.trim();
    const selectedAgents = Array.from(document.querySelectorAll('#agent-selection input:checked'))
        .map(checkbox => checkbox.value);
    
    if (!task) {
        alert('Please enter a task description');
        return;
    }
    
    fetch('/api/agents/coordinate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task: task,
            agents: selectedAgents
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Agent coordination completed successfully!');
            document.getElementById('coordination-task').value = '';
            document.querySelectorAll('#agent-selection input').forEach(cb => cb.checked = false);
        }
    })
    .catch(error => {
        console.error('Error coordinating agents:', error);
        alert('Error coordinating agents');
    });
}

// Learning functionality
function loadLearningProfile() {
    fetch('/api/learning/profile')
        .then(response => response.json())
        .then(data => {
            const profileDiv = document.getElementById('learning-profile');
            profileDiv.innerHTML = `
                <p><strong>Coding Style:</strong> ${data.coding_style || 'Unknown'}</p>
                <p><strong>Skill Level:</strong> ${data.skill_level || 'Unknown'}</p>
                <p><strong>Languages:</strong> ${(data.languages || []).join(', ')}</p>
                <p><strong>Learning Goals:</strong> ${(data.learning_goals || []).join(', ')}</p>
            `;
        })
        .catch(error => console.error('Error loading learning profile:', error));
}

function provideFeedback() {
    const suggestionId = document.getElementById('feedback-id').value.trim();
    const rating = document.getElementById('feedback-rating').value;
    const comment = document.getElementById('feedback-comment').value.trim();
    
    if (!suggestionId) {
        alert('Please enter a suggestion ID');
        return;
    }
    
    fetch('/api/learning/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            suggestion_id: suggestionId,
            rating: parseInt(rating),
            comment: comment
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Feedback submitted successfully!');
            document.getElementById('feedback-id').value = '';
            document.getElementById('feedback-comment').value = '';
        }
    })
    .catch(error => {
        console.error('Error submitting feedback:', error);
        alert('Error submitting feedback');
    });
}

// Configuration functionality
function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            const configForm = document.getElementById('config-form');
            configForm.innerHTML = '';
            
            Object.entries(data).forEach(([key, value]) => {
                const label = document.createElement('label');
                label.innerHTML = `
                    <input type="checkbox" id="config-${key}" ${value ? 'checked' : ''}> 
                    ${key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}
                `;
                configForm.appendChild(label);
            });
        })
        .catch(error => console.error('Error loading config:', error));
}

function updateConfig() {
    const config = {};
    document.querySelectorAll('#config-form input[type="checkbox"]').forEach(checkbox => {
        const key = checkbox.id.replace('config-', '');
        config[key] = checkbox.checked;
    });
    
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Configuration updated successfully!');
        }
    })
    .catch(error => {
        console.error('Error updating config:', error);
        alert('Error updating configuration');
    });
}

// Event listeners
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initWebSocket();
    loadWorkflows();
});
        """


class ConfigurationManager:
    """Advanced configuration management system."""
    
    def __init__(self):
        self.templates = {
            'default': self._get_default_template(),
            'minimal': self._get_minimal_template(),
            'full': self._get_full_template()
        }
    
    def initialize_project_config(self, project_path: Path, template: str = 'default') -> None:
        """Initialize project configuration."""
        
        config_dir = project_path / '.codegenie'
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'config.yaml'
        
        if template in self.templates:
            config_content = self.templates[template]
        else:
            config_content = self.templates['default']
        
        with open(config_file, 'w') as f:
            f.write(config_content)
    
    def set_config_value(self, project_path: Path, key: str, value: str) -> None:
        """Set a configuration value."""
        
        config_file = project_path / '.codegenie' / 'config.yaml'
        
        if not config_file.exists():
            raise FileNotFoundError("Configuration file not found. Run 'codegenie config init' first.")
        
        # In a real implementation, this would parse and update YAML
        # For now, we'll just append the setting
        with open(config_file, 'a') as f:
            f.write(f"\n{key}: {value}\n")
    
    def _get_default_template(self) -> str:
        """Get default configuration template."""
        return """
# CodeGenie Advanced Configuration

# Core Settings
models:
  default: "llama3.1:8b"
  fallback: "codellama:7b"

# Advanced Features
autonomous_workflows: true
multi_agent_coordination: true
adaptive_learning: true

# Performance Settings
max_context_length: 8192
cache_enabled: true
parallel_processing: true

# Security Settings
sandbox_enabled: true
code_execution_timeout: 30
safe_mode: true

# Learning Settings
learning_rate: 0.1
feedback_weight: 0.8
adaptation_threshold: 0.7

# UI Settings
interface_theme: "dark"
show_progress: true
verbose_output: false

# Integration Settings
git_integration: true
ide_plugins: true
webhook_enabled: false
        """
    
    def _get_minimal_template(self) -> str:
        """Get minimal configuration template."""
        return """
# CodeGenie Minimal Configuration

models:
  default: "llama3.1:8b"

autonomous_workflows: false
multi_agent_coordination: false
adaptive_learning: true

safe_mode: true
        """
    
    def _get_full_template(self) -> str:
        """Get full configuration template."""
        return """
# CodeGenie Full Configuration

# Core Settings
models:
  default: "llama3.1:8b"
  fallback: "codellama:7b"
  specialized:
    architect: "llama3.1:8b"
    security: "codellama:7b"
    performance: "llama3.1:8b"

# Advanced Features
autonomous_workflows: true
multi_agent_coordination: true
adaptive_learning: true
predictive_assistance: true
natural_language_programming: true

# Performance Settings
max_context_length: 16384
cache_enabled: true
cache_size: "1GB"
parallel_processing: true
max_parallel_tasks: 4

# Security Settings
sandbox_enabled: true
code_execution_timeout: 60
safe_mode: true
vulnerability_scanning: true
security_audit_enabled: true

# Learning Settings
learning_rate: 0.1
feedback_weight: 0.8
adaptation_threshold: 0.7
personalization_enabled: true
pattern_recognition: true

# Multi-Agent Settings
agent_coordination_timeout: 300
conflict_resolution_strategy: "priority_based"
agent_communication_protocol: "async"

# Workflow Settings
workflow_timeout: 3600
rollback_enabled: true
checkpoint_interval: 300
progress_tracking: true

# UI Settings
interface_theme: "dark"
show_progress: true
verbose_output: true
real_time_updates: true

# Integration Settings
git_integration: true
ide_plugins: true
webhook_enabled: true
ci_cd_integration: true
team_collaboration: true

# Monitoring Settings
performance_monitoring: true
usage_analytics: true
error_reporting: true
telemetry_enabled: true
        """