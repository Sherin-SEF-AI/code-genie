"""
IDE Bridge - Seamless integration with IDEs like Claude Code
Provides real-time communication with IDEs via LSP and custom protocols
"""

import json
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime

from .ide_features import (
    IDEFeatureManager,
    InlineDiffProvider,
    QuickActionProvider,
    CodeLensProvider,
    QuickActionType
)


class IDEEventType(Enum):
    """Types of IDE events"""
    FILE_OPENED = "file_opened"
    FILE_CLOSED = "file_closed"
    FILE_CHANGED = "file_changed"
    FILE_SAVED = "file_saved"
    CURSOR_MOVED = "cursor_moved"
    SELECTION_CHANGED = "selection_changed"
    COMPLETION_REQUESTED = "completion_requested"
    HOVER_REQUESTED = "hover_requested"
    DEFINITION_REQUESTED = "definition_requested"
    CODE_ACTION_REQUESTED = "code_action_requested"
    REFACTOR_REQUESTED = "refactor_requested"


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


@dataclass
class FileState:
    """Represents the state of a file in the IDE"""
    path: Path
    content: str
    checksum: str
    version: int
    last_modified: datetime
    is_dirty: bool = False
    
    @classmethod
    def from_file(cls, path: Path, content: str, version: int = 1):
        """Create FileState from file content"""
        checksum = hashlib.md5(content.encode()).hexdigest()
        return cls(
            path=path,
            content=content,
            checksum=checksum,
            version=version,
            last_modified=datetime.now(),
            is_dirty=False
        )


@dataclass
class SyncStatus:
    """File synchronization status"""
    in_sync: bool
    local_version: int
    remote_version: int
    conflicts: List[str] = field(default_factory=list)


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
        
        # File sync mechanism
        self.file_states: Dict[Path, FileState] = {}
        self.sync_enabled = True
        self.auto_sync_interval = 5  # seconds
        
        # IDE-specific features
        self.feature_manager = IDEFeatureManager()
        
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
    
    # File Sync Mechanism
    
    async def sync_file(self, file_path: Path) -> SyncStatus:
        """Synchronize a file between IDE and CodeGenie"""
        try:
            # Get current file content from IDE
            ide_content = await self.request_file_content(file_path)
            if ide_content is None:
                return SyncStatus(
                    in_sync=False,
                    local_version=0,
                    remote_version=0,
                    conflicts=["File not found in IDE"]
                )
            
            # Check if we have a cached state
            if file_path in self.file_states:
                cached_state = self.file_states[file_path]
                ide_checksum = hashlib.md5(ide_content.encode()).hexdigest()
                
                if cached_state.checksum == ide_checksum:
                    # Files are in sync
                    return SyncStatus(
                        in_sync=True,
                        local_version=cached_state.version,
                        remote_version=cached_state.version
                    )
                else:
                    # Files differ - update cache
                    new_state = FileState.from_file(
                        file_path,
                        ide_content,
                        cached_state.version + 1
                    )
                    self.file_states[file_path] = new_state
                    
                    return SyncStatus(
                        in_sync=False,
                        local_version=cached_state.version,
                        remote_version=new_state.version,
                        conflicts=["File modified in IDE"]
                    )
            else:
                # First time seeing this file
                new_state = FileState.from_file(file_path, ide_content)
                self.file_states[file_path] = new_state
                
                return SyncStatus(
                    in_sync=True,
                    local_version=new_state.version,
                    remote_version=new_state.version
                )
                
        except Exception as e:
            return SyncStatus(
                in_sync=False,
                local_version=0,
                remote_version=0,
                conflicts=[f"Sync error: {str(e)}"]
            )
    
    async def sync_all_files(self) -> Dict[Path, SyncStatus]:
        """Synchronize all active files"""
        results = {}
        for file_path in self.get_active_files():
            results[file_path] = await self.sync_file(file_path)
        return results
    
    async def watch_file_changes(self, callback: Callable[[Path, str], None]):
        """Watch for file changes and trigger callback"""
        while self.sync_enabled:
            sync_results = await self.sync_all_files()
            
            for file_path, status in sync_results.items():
                if not status.in_sync and file_path in self.file_states:
                    await callback(file_path, self.file_states[file_path].content)
            
            await asyncio.sleep(self.auto_sync_interval)
    
    def get_file_state(self, file_path: Path) -> Optional[FileState]:
        """Get the current state of a file"""
        return self.file_states.get(file_path)
    
    def mark_file_dirty(self, file_path: Path):
        """Mark a file as having unsaved changes"""
        if file_path in self.file_states:
            self.file_states[file_path].is_dirty = True
    
    def mark_file_clean(self, file_path: Path):
        """Mark a file as saved"""
        if file_path in self.file_states:
            self.file_states[file_path].is_dirty = False
    
    # IDE Feature Integration
    
    def get_feature_manager(self) -> IDEFeatureManager:
        """Get the IDE feature manager"""
        return self.feature_manager
    
    async def show_inline_diff(
        self,
        file_path: Path,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        original_text: str,
        modified_text: str,
        description: str
    ):
        """Show an inline diff in the IDE"""
        diff = self.feature_manager.diff_provider.create_diff(
            file_path=file_path,
            start_line=start_line,
            start_column=start_column,
            end_line=end_line,
            end_column=end_column,
            original_text=original_text,
            modified_text=modified_text,
            description=description
        )
        
        await self.send_notification('show_inline_diff', diff.to_dict())
    
    async def register_quick_action(
        self,
        action_id: str,
        title: str,
        action_type: QuickActionType,
        file_path: Path,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        command: Optional[str] = None,
        arguments: Optional[List[Any]] = None
    ):
        """Register a quick action in the IDE"""
        action = self.feature_manager.action_provider.create_action(
            action_id=action_id,
            title=title,
            action_type=action_type,
            file_path=file_path,
            start_line=start_line,
            start_column=start_column,
            end_line=end_line,
            end_column=end_column,
            command=command,
            arguments=arguments
        )
        
        await self.send_notification('register_quick_action', action.to_dict())
    
    async def add_code_lens(
        self,
        file_path: Path,
        line: int,
        column: int,
        command: str,
        title: str,
        arguments: Optional[List[Any]] = None
    ):
        """Add a code lens in the IDE"""
        lens = self.feature_manager.lens_provider.add_lens(
            file_path=file_path,
            line=line,
            column=column,
            command=command,
            title=title,
            arguments=arguments
        )
        
        await self.send_notification('add_code_lens', lens.to_dict())
    
    async def analyze_and_suggest(self, file_path: Path, content: str, language: str):
        """Analyze code and provide suggestions"""
        suggestions = await self.feature_manager.suggest_improvements(
            file_path=file_path,
            content=content,
            language=language
        )
        
        await self.send_notification('code_suggestions', {
            'file': str(file_path),
            'suggestions': suggestions
        })


class VSCodeBridge(IDEBridge):
    """
    Specific bridge for VS Code
    Implements VS Code Extension API interface
    """
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.extension_version = "1.0.0"
        self.extension_id = "codegenie.vscode"
        self.capabilities = {
            'textDocument': {
                'completion': True,
                'hover': True,
                'definition': True,
                'codeAction': True,
                'formatting': True
            },
            'workspace': {
                'fileOperations': True,
                'workspaceFolders': True
            }
        }
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize VS Code extension"""
        return {
            'capabilities': self.capabilities,
            'serverInfo': {
                'name': 'CodeGenie Language Server',
                'version': self.extension_version
            }
        }
    
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
    
    async def show_quick_pick(self, items: List[str], title: str = "") -> Optional[str]:
        """Show VS Code quick pick menu"""
        response = await self.send_notification('show_quick_pick', {
            'items': items,
            'title': title
        })
        return response
    
    async def show_input_box(self, prompt: str, default: str = "") -> Optional[str]:
        """Show VS Code input box"""
        response = await self.send_notification('show_input_box', {
            'prompt': prompt,
            'default': default
        })
        return response
    
    async def create_terminal(self, name: str, cwd: Optional[Path] = None) -> str:
        """Create a new terminal in VS Code"""
        terminal_id = f"codegenie-{name}"
        await self.send_notification('create_terminal', {
            'id': terminal_id,
            'name': name,
            'cwd': str(cwd) if cwd else str(self.project_root)
        })
        return terminal_id
    
    async def send_terminal_text(self, terminal_id: str, text: str):
        """Send text to a terminal"""
        await self.send_notification('terminal_send_text', {
            'terminal_id': terminal_id,
            'text': text
        })
    
    async def show_webview(self, title: str, html: str, view_column: int = 1):
        """Show a webview panel in VS Code"""
        await self.send_notification('show_webview', {
            'title': title,
            'html': html,
            'viewColumn': view_column
        })
    
    async def register_code_lens(self, file_path: Path, lenses: List[Dict[str, Any]]):
        """Register code lenses for a file"""
        await self.send_notification('register_code_lens', {
            'file': str(file_path),
            'lenses': lenses
        })
    
    async def register_code_action(
        self,
        file_path: Path,
        range: Dict[str, Any],
        action: Dict[str, Any]
    ):
        """Register a code action"""
        await self.send_notification('register_code_action', {
            'file': str(file_path),
            'range': range,
            'action': action
        })
    
    async def show_inline_diff(
        self,
        file_path: Path,
        line: int,
        original: str,
        modified: str
    ):
        """Show inline diff decoration"""
        await self.send_notification('show_inline_diff', {
            'file': str(file_path),
            'line': line,
            'original': original,
            'modified': modified
        })
    
    async def apply_workspace_edit(self, edits: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Apply workspace edit (multiple files)"""
        await self.send_notification('apply_workspace_edit', {
            'edits': edits
        })
        return True


class JetBrainsBridge(IDEBridge):
    """
    Specific bridge for JetBrains IDEs (IntelliJ IDEA, PyCharm, WebStorm, etc.)
    Implements JetBrains Plugin API interface
    """
    
    def __init__(self, project_root: Path, ide_type: str = "IntelliJ IDEA"):
        super().__init__(project_root)
        self.plugin_version = "1.0.0"
        self.plugin_id = "com.codegenie.jetbrains"
        self.ide_type = ide_type
        self.capabilities = {
            'codeCompletion': True,
            'codeInspection': True,
            'refactoring': True,
            'intentions': True,
            'quickFixes': True
        }
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize JetBrains plugin"""
        return {
            'capabilities': self.capabilities,
            'pluginInfo': {
                'name': 'CodeGenie Plugin',
                'version': self.plugin_version,
                'ide': self.ide_type
            }
        }
    
    async def run_configuration(self, config_name: str):
        """Run a configuration in JetBrains IDE"""
        await self.send_notification('run_configuration', {
            'name': config_name
        })
    
    async def open_file(self, file_path: Path, line: Optional[int] = None, column: Optional[int] = None):
        """Open a file in JetBrains IDE"""
        await self.send_notification('open_file', {
            'file': str(file_path),
            'line': line,
            'column': column
        })
    
    async def show_diff(self, file_path: Path, original: str, modified: str):
        """Show diff view in JetBrains IDE"""
        await self.send_notification('show_diff', {
            'file': str(file_path),
            'original': original,
            'modified': modified,
            'title': f"CodeGenie: {file_path.name}"
        })
    
    async def show_balloon(self, message: str, message_type: str = "info"):
        """Show balloon notification"""
        await self.send_notification('show_balloon', {
            'message': message,
            'type': message_type
        })
    
    async def create_intention_action(
        self,
        file_path: Path,
        range: Dict[str, Any],
        text: str,
        action_id: str
    ):
        """Create an intention action (quick fix)"""
        await self.send_notification('create_intention', {
            'file': str(file_path),
            'range': range,
            'text': text,
            'actionId': action_id
        })
    
    async def create_inspection(
        self,
        file_path: Path,
        range: Dict[str, Any],
        message: str,
        severity: str = "WARNING"
    ):
        """Create a code inspection"""
        await self.send_notification('create_inspection', {
            'file': str(file_path),
            'range': range,
            'message': message,
            'severity': severity
        })
    
    async def run_refactoring(
        self,
        refactoring_type: str,
        file_path: Path,
        params: Dict[str, Any]
    ):
        """Trigger a refactoring operation"""
        await self.send_notification('run_refactoring', {
            'type': refactoring_type,
            'file': str(file_path),
            'params': params
        })
    
    async def show_tool_window(self, window_id: str, content: str):
        """Show content in a tool window"""
        await self.send_notification('show_tool_window', {
            'windowId': window_id,
            'content': content
        })
    
    async def execute_action(self, action_id: str, context: Optional[Dict[str, Any]] = None):
        """Execute an IDE action"""
        await self.send_notification('execute_action', {
            'actionId': action_id,
            'context': context or {}
        })
    
    async def create_gutter_icon(
        self,
        file_path: Path,
        line: int,
        icon: str,
        tooltip: str
    ):
        """Create a gutter icon"""
        await self.send_notification('create_gutter_icon', {
            'file': str(file_path),
            'line': line,
            'icon': icon,
            'tooltip': tooltip
        })
    
    async def show_popup_menu(
        self,
        items: List[Dict[str, Any]],
        x: int,
        y: int
    ) -> Optional[str]:
        """Show popup menu"""
        response = await self.send_notification('show_popup_menu', {
            'items': items,
            'x': x,
            'y': y
        })
        return response


# Alias for backward compatibility
IntelliJBridge = JetBrainsBridge


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
