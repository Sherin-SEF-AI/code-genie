"""
IDE Bridge - Seamless integration with IDEs like Claude Code
Provides real-time communication with IDEs via LSP and custom protocols
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class IDEEventType(Enum):
    """Types of IDE events"""
    FILE_OPENED = "file_opened"
    FILE_CLOSED = "file_closed"
    FILE_CHANGED = "file_changed"
    CURSOR_MOVED = "cursor_moved"
    SELECTION_CHANGED = "selection_changed"
    COMPLETION_REQUESTED = "completion_requested"
    HOVER_REQUESTED = "hover_requested"
    DEFINITION_REQUESTED = "definition_requested"


@dataclass
class IDEEvent:
    """Represents an IDE event"""
    event_type: IDEEventType
    file_path: Optional[Path] = None
    line: Optional[int] = None
    column: Optional[int] = None
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class IDEResponse:
    """Response to IDE"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class IDEBridge:
    """
    Bridge between CodeGenie and IDEs
    Provides real-time integration like Claude Code
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.event_handlers: Dict[IDEEventType, List[Callable]] = {}
        self.active_files: Dict[Path, Dict[str, Any]] = {}
        self.cursor_position: Optional[Dict[str, Any]] = None
        
    def register_handler(self, event_type: IDEEventType, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def handle_event(self, event: IDEEvent) -> IDEResponse:
        """Handle an IDE event"""
        try:
            # Update internal state
            self._update_state(event)
            
            # Call registered handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    await handler(event)
            
            # Generate response based on event type
            response_data = await self._generate_response(event)
            
            return IDEResponse(success=True, data=response_data)
            
        except Exception as e:
            return IDEResponse(success=False, error=str(e))
    
    def _update_state(self, event: IDEEvent):
        """Update internal state based on event"""
        if event.event_type == IDEEventType.FILE_OPENED:
            if event.file_path:
                self.active_files[event.file_path] = {
                    'opened_at': None,  # Add timestamp if needed
                    'modified': False
                }
        
        elif event.event_type == IDEEventType.FILE_CLOSED:
            if event.file_path and event.file_path in self.active_files:
                del self.active_files[event.file_path]
        
        elif event.event_type == IDEEventType.FILE_CHANGED:
            if event.file_path and event.file_path in self.active_files:
                self.active_files[event.file_path]['modified'] = True
        
        elif event.event_type == IDEEventType.CURSOR_MOVED:
            self.cursor_position = {
                'file': event.file_path,
                'line': event.line,
                'column': event.column
            }
    
    async def _generate_response(self, event: IDEEvent) -> Optional[Any]:
        """Generate response data for an event"""
        if event.event_type == IDEEventType.COMPLETION_REQUESTED:
            return await self._get_completions(event)
        
        elif event.event_type == IDEEventType.HOVER_REQUESTED:
            return await self._get_hover_info(event)
        
        elif event.event_type == IDEEventType.DEFINITION_REQUESTED:
            return await self._get_definition(event)
        
        return None
    
    async def _get_completions(self, event: IDEEvent) -> List[Dict[str, Any]]:
        """Get code completions"""
        # This would integrate with IntelligentCompletion
        return [
            {
                'label': 'example_function',
                'kind': 'function',
                'detail': 'Example function',
                'documentation': 'This is an example function'
            }
        ]
    
    async def _get_hover_info(self, event: IDEEvent) -> Optional[Dict[str, str]]:
        """Get hover information"""
        return {
            'contents': 'Hover information would go here',
            'range': {
                'start': {'line': event.line or 0, 'character': event.column or 0},
                'end': {'line': event.line or 0, 'character': (event.column or 0) + 10}
            }
        }
    
    async def _get_definition(self, event: IDEEvent) -> Optional[Dict[str, Any]]:
        """Get symbol definition location"""
        return {
            'uri': str(event.file_path),
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 0, 'character': 10}
            }
        }
    
    def get_active_files(self) -> List[Path]:
        """Get list of currently active files"""
        return list(self.active_files.keys())
    
    def get_cursor_context(self) -> Optional[Dict[str, Any]]:
        """Get current cursor context"""
        return self.cursor_position
    
    async def send_notification(self, notification_type: str, data: Dict[str, Any]):
        """Send notification to IDE"""
        # This would send notifications back to the IDE
        notification = {
            'type': notification_type,
            'data': data
        }
        # In a real implementation, this would send via WebSocket or similar
        print(f"Notification: {json.dumps(notification)}")
    
    async def request_file_content(self, file_path: Path) -> Optional[str]:
        """Request file content from IDE"""
        # In a real implementation, this would request from IDE
        if file_path.exists():
            with open(file_path) as f:
                return f.read()
        return None
    
    async def apply_edit(
        self,
        file_path: Path,
        edits: List[Dict[str, Any]]
    ) -> bool:
        """Apply edits to a file in the IDE"""
        # This would send edit commands to the IDE
        edit_request = {
            'file': str(file_path),
            'edits': edits
        }
        await self.send_notification('apply_edits', edit_request)
        return True
    
    async def show_message(self, message: str, message_type: str = "info"):
        """Show a message in the IDE"""
        await self.send_notification('show_message', {
            'message': message,
            'type': message_type
        })
    
    async def show_progress(
        self,
        title: str,
        message: str,
        percentage: Optional[int] = None
    ):
        """Show progress indicator in IDE"""
        await self.send_notification('show_progress', {
            'title': title,
            'message': message,
            'percentage': percentage
        })


class VSCodeBridge(IDEBridge):
    """Specific bridge for VS Code"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.extension_version = "1.0.0"
    
    async def open_file(self, file_path: Path, line: Optional[int] = None):
        """Open a file in VS Code"""
        await self.send_notification('open_file', {
            'file': str(file_path),
            'line': line
        })
    
    async def show_diff(self, file_path: Path, original: str, modified: str):
        """Show diff view in VS Code"""
        await self.send_notification('show_diff', {
            'file': str(file_path),
            'original': original,
            'modified': modified
        })


class IntelliJBridge(IDEBridge):
    """Specific bridge for IntelliJ IDEA"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.plugin_version = "1.0.0"
    
    async def run_configuration(self, config_name: str):
        """Run a configuration in IntelliJ"""
        await self.send_notification('run_configuration', {
            'name': config_name
        })


class WebSocketIDEServer:
    """
    WebSocket server for IDE communication
    Allows real-time bidirectional communication like Claude Code
    """
    
    def __init__(self, bridge: IDEBridge, host: str = "localhost", port: int = 8765):
        self.bridge = bridge
        self.host = host
        self.port = port
        self.clients = set()
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                # Parse message
                data = json.loads(message)
                event_type = IDEEventType(data.get('type'))
                
                # Create event
                event = IDEEvent(
                    event_type=event_type,
                    file_path=Path(data['file']) if 'file' in data else None,
                    line=data.get('line'),
                    column=data.get('column'),
                    text=data.get('text'),
                    data=data.get('data')
                )
                
                # Handle event
                response = await self.bridge.handle_event(event)
                
                # Send response
                await websocket.send(json.dumps(asdict(response)))
                
        finally:
            self.clients.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients]
            )
    
    async def start(self):
        """Start the WebSocket server"""
        # In a real implementation, this would use websockets library
        print(f"IDE Bridge server starting on {self.host}:{self.port}")
        # await websockets.serve(self.handle_client, self.host, self.port)
