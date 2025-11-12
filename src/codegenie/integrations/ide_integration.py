"""
IDE Integration System

Provides integrations with popular IDEs including VS Code and IntelliJ,
implementing Language Server Protocol (LSP) support and real-time collaboration features.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import websockets
from websockets.server import WebSocketServerProtocol

from ..core.code_intelligence import CodeIntelligence
from ..core.context_engine import ContextEngine
from ..core.tool_executor import ToolExecutor
from ..agents.base_agent import BaseAgent


@dataclass
class IDEContext:
    """Context information from IDE"""
    file_path: str
    cursor_position: int
    selected_text: Optional[str]
    project_root: str
    language: str
    workspace_files: List[str]


@dataclass
class CodeSuggestion:
    """Code suggestion for IDE"""
    text: str
    range_start: int
    range_end: int
    confidence: float
    reasoning: str
    category: str  # completion, refactor, fix, etc.


@dataclass
class IDEAnalysis:
    """Analysis result for IDE display"""
    diagnostics: List[Dict[str, Any]]
    suggestions: List[CodeSuggestion]
    quick_fixes: List[Dict[str, Any]]
    refactoring_options: List[Dict[str, Any]]


class IDEIntegrationBase(ABC):
    """Base class for IDE integrations"""
    
    def __init__(self, code_intelligence: CodeIntelligence, context_engine: ContextEngine, tool_executor: Optional[ToolExecutor] = None):
        self.code_intelligence = code_intelligence
        self.context_engine = context_engine
        self.tool_executor = tool_executor or ToolExecutor()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_sessions: Dict[str, Dict] = {}
    
    @abstractmethod
    async def provide_code_suggestions(self, context: IDEContext) -> List[CodeSuggestion]:
        """Provide code suggestions based on IDE context"""
        pass
    
    @abstractmethod
    async def analyze_code_in_editor(self, code: str, context: IDEContext) -> IDEAnalysis:
        """Analyze code in the editor and provide diagnostics"""
        pass
    
    @abstractmethod
    async def handle_real_time_collaboration(self, session_id: str, event: Dict[str, Any]) -> None:
        """Handle real-time collaboration events"""
        pass


class VSCodeExtension(IDEIntegrationBase):
    """VS Code extension integration with real-time assistance"""
    
    def __init__(self, code_intelligence: CodeIntelligence, context_engine: ContextEngine, tool_executor: Optional[ToolExecutor] = None):
        super().__init__(code_intelligence, context_engine, tool_executor)
        self.websocket_server = None
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
    
    async def start_websocket_server(self, host: str = "localhost", port: int = 8765):
        """Start WebSocket server for VS Code communication"""
        async def handle_client(websocket: WebSocketServerProtocol, path: str):
            client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            self.connected_clients[client_id] = websocket
            self.logger.info(f"VS Code client connected: {client_id}")
            
            try:
                async for message in websocket:
                    await self._handle_vscode_message(client_id, json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                self.logger.info(f"VS Code client disconnected: {client_id}")
            finally:
                self.connected_clients.pop(client_id, None)
        
        self.websocket_server = await websockets.serve(handle_client, host, port)
        self.logger.info(f"VS Code WebSocket server started on {host}:{port}")
    
    async def _handle_vscode_message(self, client_id: str, message: Dict[str, Any]):
        """Handle incoming messages from VS Code"""
        message_type = message.get("type")
        
        if message_type == "code_completion":
            context = IDEContext(**message["context"])
            suggestions = await self.provide_code_suggestions(context)
            await self._send_to_client(client_id, {
                "type": "code_completion_response",
                "suggestions": [asdict(s) for s in suggestions]
            })
        
        elif message_type == "code_analysis":
            context = IDEContext(**message["context"])
            analysis = await self.analyze_code_in_editor(message["code"], context)
            await self._send_to_client(client_id, {
                "type": "code_analysis_response",
                "analysis": asdict(analysis)
            })
        
        elif message_type == "collaboration_event":
            await self.handle_real_time_collaboration(message["session_id"], message["event"])
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific VS Code client"""
        if client_id in self.connected_clients:
            try:
                await self.connected_clients[client_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                self.connected_clients.pop(client_id, None)
    
    async def provide_code_suggestions(self, context: IDEContext) -> List[CodeSuggestion]:
        """Provide intelligent code suggestions for VS Code"""
        try:
            # Analyze current code context
            code_analysis = await self.code_intelligence.analyze_code_context(
                context.file_path, context.cursor_position
            )
            
            # Get relevant context from conversation history
            relevant_context = await self.context_engine.retrieve_relevant_context(
                f"code completion at {context.file_path}:{context.cursor_position}"
            )
            
            suggestions = []
            
            # Generate completion suggestions
            if code_analysis.completion_context:
                completion_text = await self._generate_completion(
                    code_analysis.completion_context, relevant_context
                )
                suggestions.append(CodeSuggestion(
                    text=completion_text,
                    range_start=context.cursor_position,
                    range_end=context.cursor_position,
                    confidence=0.85,
                    reasoning="AI-generated code completion based on context analysis",
                    category="completion"
                ))
            
            # Generate refactoring suggestions
            if code_analysis.refactoring_opportunities:
                for opportunity in code_analysis.refactoring_opportunities:
                    suggestions.append(CodeSuggestion(
                        text=opportunity.suggested_code,
                        range_start=opportunity.start_position,
                        range_end=opportunity.end_position,
                        confidence=opportunity.confidence,
                        reasoning=opportunity.reasoning,
                        category="refactor"
                    ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error providing code suggestions: {e}")
            return []
    
    async def analyze_code_in_editor(self, code: str, context: IDEContext) -> IDEAnalysis:
        """Analyze code in VS Code editor"""
        try:
            # Perform semantic analysis
            semantic_analysis = await self.code_intelligence.analyze_code_semantics(
                code, context.language
            )
            
            # Generate diagnostics
            diagnostics = []
            for issue in semantic_analysis.issues:
                diagnostics.append({
                    "severity": issue.severity,
                    "message": issue.message,
                    "range": {
                        "start": {"line": issue.line, "character": issue.column},
                        "end": {"line": issue.end_line, "character": issue.end_column}
                    },
                    "source": "CodeGenie"
                })
            
            # Generate quick fixes
            quick_fixes = []
            for fix in semantic_analysis.suggested_fixes:
                quick_fixes.append({
                    "title": fix.title,
                    "edit": {
                        "range": fix.range,
                        "newText": fix.new_text
                    },
                    "kind": "quickfix"
                })
            
            # Generate refactoring options
            refactoring_options = []
            for refactor in semantic_analysis.refactoring_options:
                refactoring_options.append({
                    "title": refactor.title,
                    "description": refactor.description,
                    "kind": refactor.kind
                })
            
            return IDEAnalysis(
                diagnostics=diagnostics,
                suggestions=[],  # Handled separately
                quick_fixes=quick_fixes,
                refactoring_options=refactoring_options
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing code: {e}")
            return IDEAnalysis(diagnostics=[], suggestions=[], quick_fixes=[], refactoring_options=[])
    
    async def handle_real_time_collaboration(self, session_id: str, event: Dict[str, Any]) -> None:
        """Handle real-time collaboration in VS Code"""
        try:
            event_type = event.get("type")
            
            if event_type == "cursor_move":
                # Broadcast cursor position to other collaborators
                await self._broadcast_to_session(session_id, {
                    "type": "collaborator_cursor",
                    "user": event["user"],
                    "position": event["position"],
                    "file": event["file"]
                })
            
            elif event_type == "text_change":
                # Broadcast text changes to other collaborators
                await self._broadcast_to_session(session_id, {
                    "type": "collaborator_edit",
                    "user": event["user"],
                    "changes": event["changes"],
                    "file": event["file"]
                })
            
            elif event_type == "selection_change":
                # Broadcast selection changes
                await self._broadcast_to_session(session_id, {
                    "type": "collaborator_selection",
                    "user": event["user"],
                    "selection": event["selection"],
                    "file": event["file"]
                })
                
        except Exception as e:
            self.logger.error(f"Error handling collaboration event: {e}")
    
    async def _broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to all clients in a collaboration session"""
        session_clients = self.active_sessions.get(session_id, {}).get("clients", [])
        for client_id in session_clients:
            await self._send_to_client(client_id, message)
    
    async def _generate_completion(self, context: Dict[str, Any], relevant_context: Any) -> str:
        """Generate code completion using AI"""
        # This would integrate with the AI model to generate completions
        # For now, return a placeholder
        return "// AI-generated completion"


class IntelliJPlugin(IDEIntegrationBase):
    """IntelliJ plugin integration with advanced code intelligence"""
    
    def __init__(self, code_intelligence: CodeIntelligence, context_engine: ContextEngine, tool_executor: Optional[ToolExecutor] = None):
        super().__init__(code_intelligence, context_engine, tool_executor)
        self.http_server = None
        self.plugin_sessions: Dict[str, Dict] = {}
    
    async def start_http_server(self, host: str = "localhost", port: int = 8766):
        """Start HTTP server for IntelliJ plugin communication"""
        from aiohttp import web, web_runner
        
        app = web.Application()
        app.router.add_post('/code-suggestions', self._handle_code_suggestions)
        app.router.add_post('/code-analysis', self._handle_code_analysis)
        app.router.add_post('/collaboration', self._handle_collaboration)
        
        runner = web_runner.AppRunner(app)
        await runner.setup()
        site = web_runner.TCPSite(runner, host, port)
        await site.start()
        
        self.logger.info(f"IntelliJ HTTP server started on {host}:{port}")
    
    async def _handle_code_suggestions(self, request):
        """Handle code suggestion requests from IntelliJ"""
        from aiohttp import web
        
        try:
            data = await request.json()
            context = IDEContext(**data["context"])
            suggestions = await self.provide_code_suggestions(context)
            
            return web.json_response({
                "suggestions": [asdict(s) for s in suggestions]
            })
        except Exception as e:
            self.logger.error(f"Error handling code suggestions: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_code_analysis(self, request):
        """Handle code analysis requests from IntelliJ"""
        from aiohttp import web
        
        try:
            data = await request.json()
            context = IDEContext(**data["context"])
            analysis = await self.analyze_code_in_editor(data["code"], context)
            
            return web.json_response(asdict(analysis))
        except Exception as e:
            self.logger.error(f"Error handling code analysis: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_collaboration(self, request):
        """Handle collaboration requests from IntelliJ"""
        from aiohttp import web
        
        try:
            data = await request.json()
            await self.handle_real_time_collaboration(data["session_id"], data["event"])
            
            return web.json_response({"status": "success"})
        except Exception as e:
            self.logger.error(f"Error handling collaboration: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def provide_code_suggestions(self, context: IDEContext) -> List[CodeSuggestion]:
        """Provide intelligent code suggestions for IntelliJ"""
        try:
            # Similar to VS Code but optimized for IntelliJ's capabilities
            code_analysis = await self.code_intelligence.analyze_code_context(
                context.file_path, context.cursor_position
            )
            
            suggestions = []
            
            # IntelliJ-specific suggestions (e.g., leveraging its refactoring capabilities)
            if code_analysis.intellij_specific_opportunities:
                for opportunity in code_analysis.intellij_specific_opportunities:
                    suggestions.append(CodeSuggestion(
                        text=opportunity.suggested_code,
                        range_start=opportunity.start_position,
                        range_end=opportunity.end_position,
                        confidence=opportunity.confidence,
                        reasoning=f"IntelliJ-optimized: {opportunity.reasoning}",
                        category=opportunity.category
                    ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error providing IntelliJ code suggestions: {e}")
            return []
    
    async def analyze_code_in_editor(self, code: str, context: IDEContext) -> IDEAnalysis:
        """Analyze code in IntelliJ editor"""
        try:
            # Leverage IntelliJ's advanced static analysis capabilities
            semantic_analysis = await self.code_intelligence.analyze_code_semantics(
                code, context.language
            )
            
            # Generate IntelliJ-compatible diagnostics
            diagnostics = []
            for issue in semantic_analysis.issues:
                diagnostics.append({
                    "severity": self._map_severity_to_intellij(issue.severity),
                    "message": issue.message,
                    "startOffset": issue.start_offset,
                    "endOffset": issue.end_offset,
                    "inspectionClass": issue.inspection_class,
                    "source": "CodeGenie"
                })
            
            return IDEAnalysis(
                diagnostics=diagnostics,
                suggestions=[],
                quick_fixes=[],
                refactoring_options=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing IntelliJ code: {e}")
            return IDEAnalysis(diagnostics=[], suggestions=[], quick_fixes=[], refactoring_options=[])
    
    async def handle_real_time_collaboration(self, session_id: str, event: Dict[str, Any]) -> None:
        """Handle real-time collaboration in IntelliJ"""
        try:
            # IntelliJ collaboration handling
            event_type = event.get("type")
            
            if event_type == "code_with_me_event":
                # Handle IntelliJ Code With Me integration
                await self._handle_code_with_me(session_id, event)
            
            elif event_type == "shared_index_update":
                # Handle shared index updates
                await self._handle_shared_index_update(session_id, event)
                
        except Exception as e:
            self.logger.error(f"Error handling IntelliJ collaboration: {e}")
    
    def _map_severity_to_intellij(self, severity: str) -> str:
        """Map generic severity to IntelliJ severity levels"""
        mapping = {
            "error": "ERROR",
            "warning": "WARNING", 
            "info": "INFO",
            "hint": "WEAK_WARNING"
        }
        return mapping.get(severity, "INFO")
    
    async def _handle_code_with_me(self, session_id: str, event: Dict[str, Any]):
        """Handle IntelliJ Code With Me events"""
        # Implementation for Code With Me integration
        pass
    
    async def _handle_shared_index_update(self, session_id: str, event: Dict[str, Any]):
        """Handle shared index updates in IntelliJ"""
        # Implementation for shared index updates
        pass


class LanguageServerProtocol:
    """Language Server Protocol implementation for IDE integrations"""
    
    def __init__(self, code_intelligence: CodeIntelligence):
        self.code_intelligence = code_intelligence
        self.logger = logging.getLogger(self.__class__.__name__)
        self.capabilities = {
            "textDocumentSync": 1,  # Full document sync
            "completionProvider": {"triggerCharacters": [".", "(", "["]},
            "hoverProvider": True,
            "definitionProvider": True,
            "referencesProvider": True,
            "documentSymbolProvider": True,
            "workspaceSymbolProvider": True,
            "codeActionProvider": True,
            "documentFormattingProvider": True,
            "documentRangeFormattingProvider": True,
            "renameProvider": True,
            "foldingRangeProvider": True,
            "semanticTokensProvider": {
                "legend": {
                    "tokenTypes": ["class", "function", "variable", "parameter"],
                    "tokenModifiers": ["declaration", "definition", "readonly"]
                },
                "range": True,
                "full": True
            }
        }
    
    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize LSP server"""
        return {
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": "CodeGenie Language Server",
                "version": "1.0.0"
            }
        }
    
    async def text_document_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle completion requests"""
        try:
            document_uri = params["textDocument"]["uri"]
            position = params["position"]
            
            # Convert LSP position to our format
            cursor_position = position["line"] * 1000 + position["character"]  # Simplified
            
            # Get completions from code intelligence
            completions = await self.code_intelligence.get_completions(
                document_uri, cursor_position
            )
            
            completion_items = []
            for completion in completions:
                completion_items.append({
                    "label": completion.label,
                    "kind": completion.kind,
                    "detail": completion.detail,
                    "documentation": completion.documentation,
                    "insertText": completion.insert_text
                })
            
            return {"items": completion_items}
            
        except Exception as e:
            self.logger.error(f"Error in text_document_completion: {e}")
            return {"items": []}
    
    async def text_document_hover(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle hover requests"""
        try:
            document_uri = params["textDocument"]["uri"]
            position = params["position"]
            
            hover_info = await self.code_intelligence.get_hover_info(
                document_uri, position
            )
            
            if hover_info:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": hover_info.content
                    },
                    "range": hover_info.range
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in text_document_hover: {e}")
            return None


class IDEIntegrationManager:
    """Manager for all IDE integrations"""
    
    def __init__(self, code_intelligence: CodeIntelligence, context_engine: ContextEngine, tool_executor: Optional[ToolExecutor] = None):
        self.code_intelligence = code_intelligence
        self.context_engine = context_engine
        self.tool_executor = tool_executor or ToolExecutor()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize IDE integrations
        self.vscode_extension = VSCodeExtension(code_intelligence, context_engine, self.tool_executor)
        self.intellij_plugin = IntelliJPlugin(code_intelligence, context_engine, self.tool_executor)
        self.lsp_server = LanguageServerProtocol(code_intelligence)
        
        self.active_integrations: Dict[str, IDEIntegrationBase] = {}
    
    async def start_all_integrations(self):
        """Start all IDE integration servers"""
        try:
            # Start VS Code WebSocket server
            await self.vscode_extension.start_websocket_server()
            self.active_integrations["vscode"] = self.vscode_extension
            
            # Start IntelliJ HTTP server
            await self.intellij_plugin.start_http_server()
            self.active_integrations["intellij"] = self.intellij_plugin
            
            self.logger.info("All IDE integrations started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting IDE integrations: {e}")
            raise
    
    async def stop_all_integrations(self):
        """Stop all IDE integration servers"""
        try:
            # Stop VS Code WebSocket server
            if self.vscode_extension.websocket_server:
                self.vscode_extension.websocket_server.close()
                await self.vscode_extension.websocket_server.wait_closed()
            
            # Stop IntelliJ HTTP server
            if self.intellij_plugin.http_server:
                await self.intellij_plugin.http_server.cleanup()
            
            self.active_integrations.clear()
            self.logger.info("All IDE integrations stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping IDE integrations: {e}")
    
    def get_integration(self, ide_type: str) -> Optional[IDEIntegrationBase]:
        """Get specific IDE integration"""
        return self.active_integrations.get(ide_type)
    
    async def handle_ide_request(self, ide_type: str, request_type: str, params: Dict[str, Any]) -> Any:
        """Handle generic IDE requests"""
        integration = self.get_integration(ide_type)
        if not integration:
            raise ValueError(f"IDE integration not found: {ide_type}")
        
        if request_type == "code_suggestions":
            context = IDEContext(**params["context"])
            return await integration.provide_code_suggestions(context)
        
        elif request_type == "code_analysis":
            context = IDEContext(**params["context"])
            return await integration.analyze_code_in_editor(params["code"], context)
        
        elif request_type == "collaboration":
            return await integration.handle_real_time_collaboration(
                params["session_id"], params["event"]
            )
        
        else:
            raise ValueError(f"Unknown request type: {request_type}")