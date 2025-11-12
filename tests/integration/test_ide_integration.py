"""
Integration tests for IDE integration functionality.

Tests VS Code extension, IntelliJ plugin, and Language Server Protocol support.
"""

import pytest
import asyncio
import json
import websockets
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.codegenie.integrations.ide_integration import (
    IDEIntegrationManager, VSCodeExtension, IntelliJPlugin, 
    LanguageServerProtocol, IDEContext, CodeSuggestion
)
from src.codegenie.core.code_intelligence import CodeIntelligence
from src.codegenie.core.context_engine import ContextEngine


@pytest.fixture
async def mock_code_intelligence():
    """Mock code intelligence for testing"""
    mock = AsyncMock(spec=CodeIntelligence)
    
    # Mock analyze_code_context
    mock.analyze_code_context.return_value = Mock(
        completion_context={"type": "function_call", "context": "test"},
        refactoring_opportunities=[
            Mock(
                suggested_code="optimized_code",
                start_position=10,
                end_position=20,
                confidence=0.9,
                reasoning="Performance improvement"
            )
        ]
    )
    
    # Mock analyze_code_semantics
    mock.analyze_code_semantics.return_value = Mock(
        issues=[
            Mock(
                severity="warning",
                message="Unused variable",
                line=5,
                column=10,
                end_line=5,
                end_column=15
            )
        ],
        suggested_fixes=[
            Mock(
                title="Remove unused variable",
                range={"start": {"line": 5, "character": 10}, "end": {"line": 5, "character": 15}},
                new_text=""
            )
        ],
        refactoring_options=[
            Mock(
                title="Extract method",
                description="Extract this code into a separate method",
                kind="refactor.extract.method"
            )
        ]
    )
    
    return mock


@pytest.fixture
async def mock_context_engine():
    """Mock context engine for testing"""
    mock = AsyncMock(spec=ContextEngine)
    
    mock.retrieve_relevant_context.return_value = Mock(
        conversation_history=[],
        project_state=Mock(),
        user_goals=[],
        recent_changes=[],
        relevant_knowledge=[]
    )
    
    return mock


@pytest.fixture
async def ide_integration_manager(mock_code_intelligence, mock_context_engine):
    """Create IDE integration manager for testing"""
    return IDEIntegrationManager(mock_code_intelligence, mock_context_engine)


@pytest.fixture
async def vscode_extension(mock_code_intelligence, mock_context_engine):
    """Create VS Code extension for testing"""
    return VSCodeExtension(mock_code_intelligence, mock_context_engine)


@pytest.fixture
async def intellij_plugin(mock_code_intelligence, mock_context_engine):
    """Create IntelliJ plugin for testing"""
    return IntelliJPlugin(mock_code_intelligence, mock_context_engine)


@pytest.fixture
def sample_ide_context():
    """Sample IDE context for testing"""
    return IDEContext(
        file_path="/test/file.py",
        cursor_position=100,
        selected_text="test_code",
        project_root="/test",
        language="python",
        workspace_files=["/test/file.py", "/test/other.py"]
    )


class TestVSCodeExtension:
    """Test VS Code extension functionality"""
    
    @pytest.mark.asyncio
    async def test_provide_code_suggestions(self, vscode_extension, sample_ide_context):
        """Test code suggestion generation for VS Code"""
        suggestions = await vscode_extension.provide_code_suggestions(sample_ide_context)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        suggestion = suggestions[0]
        assert isinstance(suggestion, CodeSuggestion)
        assert suggestion.confidence > 0
        assert suggestion.category in ["completion", "refactor", "fix"]
    
    @pytest.mark.asyncio
    async def test_analyze_code_in_editor(self, vscode_extension, sample_ide_context):
        """Test code analysis in VS Code editor"""
        code = "def test_function():\n    unused_var = 42\n    return True"
        
        analysis = await vscode_extension.analyze_code_in_editor(code, sample_ide_context)
        
        assert analysis.diagnostics is not None
        assert analysis.quick_fixes is not None
        assert analysis.refactoring_options is not None
        
        # Check diagnostic format
        if analysis.diagnostics:
            diagnostic = analysis.diagnostics[0]
            assert "severity" in diagnostic
            assert "message" in diagnostic
            assert "range" in diagnostic
            assert "source" in diagnostic
    
    @pytest.mark.asyncio
    async def test_websocket_server_startup(self, vscode_extension):
        """Test VS Code WebSocket server startup"""
        # Mock websockets.serve
        with patch('websockets.serve') as mock_serve:
            mock_server = AsyncMock()
            mock_serve.return_value = mock_server
            
            await vscode_extension.start_websocket_server("localhost", 8765)
            
            mock_serve.assert_called_once()
            assert vscode_extension.websocket_server == mock_server
    
    @pytest.mark.asyncio
    async def test_handle_vscode_message(self, vscode_extension, sample_ide_context):
        """Test VS Code message handling"""
        # Mock WebSocket client
        mock_websocket = AsyncMock()
        client_id = "test_client"
        vscode_extension.connected_clients[client_id] = mock_websocket
        
        # Test code completion message
        message = {
            "type": "code_completion",
            "context": {
                "file_path": sample_ide_context.file_path,
                "cursor_position": sample_ide_context.cursor_position,
                "selected_text": sample_ide_context.selected_text,
                "project_root": sample_ide_context.project_root,
                "language": sample_ide_context.language,
                "workspace_files": sample_ide_context.workspace_files
            }
        }
        
        await vscode_extension._handle_vscode_message(client_id, message)
        
        # Verify response was sent
        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["type"] == "code_completion_response"
        assert "suggestions" in sent_data
    
    @pytest.mark.asyncio
    async def test_real_time_collaboration(self, vscode_extension):
        """Test real-time collaboration features"""
        session_id = "test_session"
        event = {
            "type": "cursor_move",
            "user": "test_user",
            "position": {"line": 10, "character": 5},
            "file": "/test/file.py"
        }
        
        # Mock session clients
        vscode_extension.active_sessions[session_id] = {"clients": ["client1", "client2"]}
        vscode_extension.connected_clients["client1"] = AsyncMock()
        vscode_extension.connected_clients["client2"] = AsyncMock()
        
        await vscode_extension.handle_real_time_collaboration(session_id, event)
        
        # Verify broadcast to all clients
        for client_id in ["client1", "client2"]:
            vscode_extension.connected_clients[client_id].send.assert_called_once()


class TestIntelliJPlugin:
    """Test IntelliJ plugin functionality"""
    
    @pytest.mark.asyncio
    async def test_provide_code_suggestions(self, intellij_plugin, sample_ide_context):
        """Test code suggestion generation for IntelliJ"""
        suggestions = await intellij_plugin.provide_code_suggestions(sample_ide_context)
        
        assert isinstance(suggestions, list)
        # IntelliJ might have different suggestion logic
    
    @pytest.mark.asyncio
    async def test_analyze_code_in_editor(self, intellij_plugin, sample_ide_context):
        """Test code analysis in IntelliJ editor"""
        code = "public class Test { private int unused; }"
        
        analysis = await intellij_plugin.analyze_code_in_editor(code, sample_ide_context)
        
        assert analysis.diagnostics is not None
        
        # Check IntelliJ-specific diagnostic format
        if analysis.diagnostics:
            diagnostic = analysis.diagnostics[0]
            assert "severity" in diagnostic
            assert "startOffset" in diagnostic or "message" in diagnostic
    
    @pytest.mark.asyncio
    async def test_http_server_startup(self, intellij_plugin):
        """Test IntelliJ HTTP server startup"""
        with patch('aiohttp.web_runner.AppRunner') as mock_runner_class:
            mock_runner = AsyncMock()
            mock_runner_class.return_value = mock_runner
            
            with patch('aiohttp.web_runner.TCPSite') as mock_site_class:
                mock_site = AsyncMock()
                mock_site_class.return_value = mock_site
                
                await intellij_plugin.start_http_server("localhost", 8766)
                
                mock_runner.setup.assert_called_once()
                mock_site.start.assert_called_once()


class TestLanguageServerProtocol:
    """Test Language Server Protocol implementation"""
    
    @pytest.fixture
    def lsp_server(self, mock_code_intelligence):
        """Create LSP server for testing"""
        return LanguageServerProtocol(mock_code_intelligence)
    
    @pytest.mark.asyncio
    async def test_initialize(self, lsp_server):
        """Test LSP server initialization"""
        params = {
            "processId": 1234,
            "clientInfo": {"name": "test-client"},
            "capabilities": {}
        }
        
        result = await lsp_server.initialize(params)
        
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "CodeGenie Language Server"
    
    @pytest.mark.asyncio
    async def test_text_document_completion(self, lsp_server):
        """Test LSP completion requests"""
        # Mock code intelligence completions
        mock_completions = [
            Mock(
                label="test_function",
                kind=3,  # Function
                detail="def test_function()",
                documentation="Test function",
                insert_text="test_function()"
            )
        ]
        lsp_server.code_intelligence.get_completions.return_value = mock_completions
        
        params = {
            "textDocument": {"uri": "file:///test.py"},
            "position": {"line": 10, "character": 5}
        }
        
        result = await lsp_server.text_document_completion(params)
        
        assert "items" in result
        assert len(result["items"]) > 0
        
        item = result["items"][0]
        assert "label" in item
        assert "kind" in item
    
    @pytest.mark.asyncio
    async def test_text_document_hover(self, lsp_server):
        """Test LSP hover requests"""
        # Mock hover info
        mock_hover = Mock(
            content="Test function documentation",
            range={"start": {"line": 10, "character": 0}, "end": {"line": 10, "character": 10}}
        )
        lsp_server.code_intelligence.get_hover_info.return_value = mock_hover
        
        params = {
            "textDocument": {"uri": "file:///test.py"},
            "position": {"line": 10, "character": 5}
        }
        
        result = await lsp_server.text_document_hover(params)
        
        assert result is not None
        assert "contents" in result
        assert result["contents"]["kind"] == "markdown"


class TestIDEIntegrationManager:
    """Test IDE integration manager"""
    
    @pytest.mark.asyncio
    async def test_start_all_integrations(self, ide_integration_manager):
        """Test starting all IDE integrations"""
        with patch.object(ide_integration_manager.vscode_extension, 'start_websocket_server') as mock_vscode:
            with patch.object(ide_integration_manager.intellij_plugin, 'start_http_server') as mock_intellij:
                await ide_integration_manager.start_all_integrations()
                
                mock_vscode.assert_called_once()
                mock_intellij.assert_called_once()
                
                assert "vscode" in ide_integration_manager.active_integrations
                assert "intellij" in ide_integration_manager.active_integrations
    
    @pytest.mark.asyncio
    async def test_handle_ide_request(self, ide_integration_manager, sample_ide_context):
        """Test generic IDE request handling"""
        # Start integrations first
        ide_integration_manager.active_integrations["vscode"] = ide_integration_manager.vscode_extension
        
        # Test code suggestions request
        params = {
            "context": {
                "file_path": sample_ide_context.file_path,
                "cursor_position": sample_ide_context.cursor_position,
                "selected_text": sample_ide_context.selected_text,
                "project_root": sample_ide_context.project_root,
                "language": sample_ide_context.language,
                "workspace_files": sample_ide_context.workspace_files
            }
        }
        
        result = await ide_integration_manager.handle_ide_request("vscode", "code_suggestions", params)
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_stop_all_integrations(self, ide_integration_manager):
        """Test stopping all IDE integrations"""
        # Mock active integrations
        mock_vscode_server = AsyncMock()
        mock_intellij_server = AsyncMock()
        
        ide_integration_manager.vscode_extension.websocket_server = mock_vscode_server
        ide_integration_manager.intellij_plugin.http_server = mock_intellij_server
        
        ide_integration_manager.active_integrations["vscode"] = ide_integration_manager.vscode_extension
        ide_integration_manager.active_integrations["intellij"] = ide_integration_manager.intellij_plugin
        
        await ide_integration_manager.stop_all_integrations()
        
        mock_vscode_server.close.assert_called_once()
        mock_vscode_server.wait_closed.assert_called_once()
        mock_intellij_server.cleanup.assert_called_once()
        
        assert len(ide_integration_manager.active_integrations) == 0


class TestIDEIntegrationErrorHandling:
    """Test error handling in IDE integrations"""
    
    @pytest.mark.asyncio
    async def test_code_analysis_error_handling(self, vscode_extension, sample_ide_context):
        """Test error handling in code analysis"""
        # Mock code intelligence to raise exception
        vscode_extension.code_intelligence.analyze_code_semantics.side_effect = Exception("Analysis failed")
        
        code = "invalid code"
        analysis = await vscode_extension.analyze_code_in_editor(code, sample_ide_context)
        
        # Should return empty analysis on error
        assert analysis.diagnostics == []
        assert analysis.suggestions == []
        assert analysis.quick_fixes == []
        assert analysis.refactoring_options == []
    
    @pytest.mark.asyncio
    async def test_suggestion_error_handling(self, vscode_extension, sample_ide_context):
        """Test error handling in code suggestions"""
        # Mock code intelligence to raise exception
        vscode_extension.code_intelligence.analyze_code_context.side_effect = Exception("Suggestion failed")
        
        suggestions = await vscode_extension.provide_code_suggestions(sample_ide_context)
        
        # Should return empty list on error
        assert suggestions == []
    
    @pytest.mark.asyncio
    async def test_websocket_connection_error(self, vscode_extension):
        """Test WebSocket connection error handling"""
        # Mock WebSocket that raises exception
        mock_websocket = AsyncMock()
        mock_websocket.send.side_effect = Exception("Connection lost")
        
        client_id = "test_client"
        vscode_extension.connected_clients[client_id] = mock_websocket
        
        message = {"type": "test", "data": "test"}
        await vscode_extension._send_to_client(client_id, message)
        
        # Client should be removed from connected clients
        assert client_id not in vscode_extension.connected_clients


class TestIDEIntegrationPerformance:
    """Test performance aspects of IDE integrations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, vscode_extension, sample_ide_context):
        """Test handling concurrent requests"""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                vscode_extension.provide_code_suggestions(sample_ide_context)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_large_code_analysis(self, vscode_extension, sample_ide_context):
        """Test analysis of large code files"""
        # Create large code sample
        large_code = "def function_{}():\n    pass\n" * 1000
        
        start_time = asyncio.get_event_loop().time()
        analysis = await vscode_extension.analyze_code_in_editor(large_code, sample_ide_context)
        end_time = asyncio.get_event_loop().time()
        
        # Analysis should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds max
        assert analysis is not None


if __name__ == "__main__":
    pytest.main([__file__])