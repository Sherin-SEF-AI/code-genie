"""
Real-time updates system for CodeGenie web interface.
Provides WebSocket support, live progress updates, and real-time command output.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from aiohttp import web
import weakref

logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """Represents a progress update."""
    type: str  # task_started, task_progress, task_completed, task_failed
    task_id: str
    task_name: str
    progress: int  # 0-100
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class CommandOutput:
    """Represents command output."""
    command_id: str
    command: str
    output_type: str  # stdout, stderr
    content: str
    timestamp: str
    exit_code: Optional[int] = None


@dataclass
class PlanUpdate:
    """Represents a plan update."""
    plan_id: str
    step_id: str
    status: str  # pending, in_progress, completed, failed
    progress: int
    message: str
    timestamp: str


class RealtimeUpdateManager:
    """Manages real-time updates via WebSocket."""
    
    def __init__(self):
        self.websockets: Set[web.WebSocketResponse] = weakref.WeakSet()
        self.subscriptions: Dict[str, Set[web.WebSocketResponse]] = {}
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
    
    async def start(self):
        """Start the update manager."""
        self.running = True
        asyncio.create_task(self._process_updates())
        logger.info("Real-time update manager started")
    
    async def stop(self):
        """Stop the update manager."""
        self.running = False
        logger.info("Real-time update manager stopped")
    
    async def _process_updates(self):
        """Process updates from the queue and broadcast them."""
        while self.running:
            try:
                update = await asyncio.wait_for(self.update_queue.get(), timeout=1.0)
                await self._broadcast_update(update)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing update: {e}")
    
    async def _broadcast_update(self, update: Dict[str, Any]):
        """Broadcast update to subscribed clients."""
        update_type = update.get('type')
        channel = update.get('channel', 'global')
        
        # Get subscribers for this channel
        subscribers = self.subscriptions.get(channel, set())
        
        # Also send to global subscribers
        subscribers = subscribers.union(self.subscriptions.get('global', set()))
        
        if subscribers:
            message = json.dumps(update)
            for ws in list(subscribers):
                try:
                    await ws.send_str(message)
                except Exception as e:
                    logger.error(f"Error sending update to WebSocket: {e}")
                    subscribers.discard(ws)
    
    def register_websocket(self, ws: web.WebSocketResponse, channels: List[str] = None):
        """Register a WebSocket connection."""
        self.websockets.add(ws)
        
        if channels is None:
            channels = ['global']
        
        for channel in channels:
            if channel not in self.subscriptions:
                self.subscriptions[channel] = weakref.WeakSet()
            self.subscriptions[channel].add(ws)
        
        logger.info(f"WebSocket registered for channels: {channels}")
    
    def unregister_websocket(self, ws: web.WebSocketResponse):
        """Unregister a WebSocket connection."""
        self.websockets.discard(ws)
        
        for channel_subs in self.subscriptions.values():
            channel_subs.discard(ws)
        
        logger.info("WebSocket unregistered")
    
    async def send_progress_update(self, update: ProgressUpdate):
        """Send a progress update."""
        await self.update_queue.put({
            'type': 'progress_update',
            'channel': 'progress',
            'data': asdict(update)
        })
    
    async def send_command_output(self, output: CommandOutput):
        """Send command output."""
        await self.update_queue.put({
            'type': 'command_output',
            'channel': 'commands',
            'data': asdict(output)
        })
    
    async def send_plan_update(self, update: PlanUpdate):
        """Send a plan update."""
        await self.update_queue.put({
            'type': 'plan_update',
            'channel': 'plans',
            'data': asdict(update)
        })
    
    async def send_approval_request(self, request_data: Dict[str, Any]):
        """Send an approval request."""
        await self.update_queue.put({
            'type': 'approval_request',
            'channel': 'approvals',
            'data': request_data
        })
    
    async def send_notification(self, message: str, level: str = 'info'):
        """Send a notification."""
        await self.update_queue.put({
            'type': 'notification',
            'channel': 'global',
            'data': {
                'message': message,
                'level': level,
                'timestamp': datetime.now().isoformat()
            }
        })


class ProgressTracker:
    """Tracks progress of tasks and operations."""
    
    def __init__(self, update_manager: RealtimeUpdateManager):
        self.update_manager = update_manager
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
    
    async def start_task(self, task_id: str, task_name: str, total_steps: int = 100):
        """Start tracking a task."""
        self.active_tasks[task_id] = {
            'name': task_name,
            'total_steps': total_steps,
            'current_step': 0,
            'status': 'in_progress',
            'started_at': datetime.now().isoformat()
        }
        
        update = ProgressUpdate(
            type='task_started',
            task_id=task_id,
            task_name=task_name,
            progress=0,
            message=f"Started: {task_name}",
            timestamp=datetime.now().isoformat()
        )
        
        await self.update_manager.send_progress_update(update)
    
    async def update_progress(self, task_id: str, current_step: int, message: str = ""):
        """Update task progress."""
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found")
            return
        
        task = self.active_tasks[task_id]
        task['current_step'] = current_step
        
        progress = int((current_step / task['total_steps']) * 100)
        
        update = ProgressUpdate(
            type='task_progress',
            task_id=task_id,
            task_name=task['name'],
            progress=progress,
            message=message or f"Progress: {progress}%",
            timestamp=datetime.now().isoformat()
        )
        
        await self.update_manager.send_progress_update(update)
    
    async def complete_task(self, task_id: str, message: str = ""):
        """Mark task as completed."""
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found")
            return
        
        task = self.active_tasks[task_id]
        task['status'] = 'completed'
        task['completed_at'] = datetime.now().isoformat()
        
        update = ProgressUpdate(
            type='task_completed',
            task_id=task_id,
            task_name=task['name'],
            progress=100,
            message=message or f"Completed: {task['name']}",
            timestamp=datetime.now().isoformat()
        )
        
        await self.update_manager.send_progress_update(update)
    
    async def fail_task(self, task_id: str, error_message: str):
        """Mark task as failed."""
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found")
            return
        
        task = self.active_tasks[task_id]
        task['status'] = 'failed'
        task['failed_at'] = datetime.now().isoformat()
        task['error'] = error_message
        
        update = ProgressUpdate(
            type='task_failed',
            task_id=task_id,
            task_name=task['name'],
            progress=task['current_step'] / task['total_steps'] * 100,
            message=f"Failed: {error_message}",
            timestamp=datetime.now().isoformat(),
            details={'error': error_message}
        )
        
        await self.update_manager.send_progress_update(update)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task."""
        return self.active_tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active tasks."""
        return self.active_tasks.copy()


class CommandOutputStreamer:
    """Streams command output in real-time."""
    
    def __init__(self, update_manager: RealtimeUpdateManager):
        self.update_manager = update_manager
        self.active_commands: Dict[str, Dict[str, Any]] = {}
    
    async def start_command(self, command_id: str, command: str):
        """Start streaming a command."""
        self.active_commands[command_id] = {
            'command': command,
            'started_at': datetime.now().isoformat(),
            'output_lines': []
        }
        
        await self.update_manager.send_notification(
            f"Executing command: {command}",
            level='info'
        )
    
    async def stream_output(self, command_id: str, content: str, output_type: str = 'stdout'):
        """Stream command output."""
        if command_id not in self.active_commands:
            logger.warning(f"Command {command_id} not found")
            return
        
        self.active_commands[command_id]['output_lines'].append({
            'type': output_type,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        output = CommandOutput(
            command_id=command_id,
            command=self.active_commands[command_id]['command'],
            output_type=output_type,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        
        await self.update_manager.send_command_output(output)
    
    async def complete_command(self, command_id: str, exit_code: int):
        """Mark command as completed."""
        if command_id not in self.active_commands:
            logger.warning(f"Command {command_id} not found")
            return
        
        cmd = self.active_commands[command_id]
        cmd['completed_at'] = datetime.now().isoformat()
        cmd['exit_code'] = exit_code
        
        output = CommandOutput(
            command_id=command_id,
            command=cmd['command'],
            output_type='completion',
            content=f"Command completed with exit code {exit_code}",
            timestamp=datetime.now().isoformat(),
            exit_code=exit_code
        )
        
        await self.update_manager.send_command_output(output)
        
        level = 'success' if exit_code == 0 else 'error'
        await self.update_manager.send_notification(
            f"Command {'succeeded' if exit_code == 0 else 'failed'}: {cmd['command']}",
            level=level
        )
    
    def get_command_output(self, command_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all output for a command."""
        if command_id in self.active_commands:
            return self.active_commands[command_id]['output_lines']
        return None


class PlanProgressTracker:
    """Tracks progress of execution plans."""
    
    def __init__(self, update_manager: RealtimeUpdateManager):
        self.update_manager = update_manager
        self.active_plans: Dict[str, Dict[str, Any]] = {}
    
    async def start_plan(self, plan_id: str, plan_name: str, steps: List[str]):
        """Start tracking a plan."""
        self.active_plans[plan_id] = {
            'name': plan_name,
            'steps': {step_id: {'status': 'pending', 'progress': 0} for step_id in steps},
            'started_at': datetime.now().isoformat()
        }
        
        await self.update_manager.send_notification(
            f"Started execution plan: {plan_name}",
            level='info'
        )
    
    async def update_step(self, plan_id: str, step_id: str, status: str, progress: int, message: str = ""):
        """Update a plan step."""
        if plan_id not in self.active_plans:
            logger.warning(f"Plan {plan_id} not found")
            return
        
        plan = self.active_plans[plan_id]
        if step_id not in plan['steps']:
            logger.warning(f"Step {step_id} not found in plan {plan_id}")
            return
        
        plan['steps'][step_id] = {
            'status': status,
            'progress': progress,
            'updated_at': datetime.now().isoformat()
        }
        
        update = PlanUpdate(
            plan_id=plan_id,
            step_id=step_id,
            status=status,
            progress=progress,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
        await self.update_manager.send_plan_update(update)
    
    async def complete_plan(self, plan_id: str):
        """Mark plan as completed."""
        if plan_id not in self.active_plans:
            logger.warning(f"Plan {plan_id} not found")
            return
        
        plan = self.active_plans[plan_id]
        plan['completed_at'] = datetime.now().isoformat()
        
        await self.update_manager.send_notification(
            f"Completed execution plan: {plan['name']}",
            level='success'
        )
    
    def get_plan_progress(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress of a plan."""
        return self.active_plans.get(plan_id)
