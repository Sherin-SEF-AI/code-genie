"""
Claude Code Features Integration
Combines all Claude Code-like features into a unified interface
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .context_manager import ContextManager, ConversationContext
from .multi_file_editor import MultiFileEditor, MultiFileEdit, FileEdit
from .intelligent_completion import IntelligentCompletion, Completion
from ..integrations.ide_bridge import IDEBridge, IDEEvent, IDEEventType


@dataclass
class ClaudeCodeSession:
    """Represents a Claude Code-like session"""
    session_id: str
    context_manager: ContextManager
    multi_file_editor: MultiFileEditor
    completion_engine: IntelligentCompletion
    ide_bridge: Optional[IDEBridge] = None


class ClaudeCodeFeatures:
    """
    Main interface for Claude Code-like features
    Provides seamless, context-aware coding assistance
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.context_manager = ContextManager(project_root)
        self.multi_file_editor = MultiFileEditor(project_root)
        self.completion_engine = IntelligentCompletion(project_root)
        self.ide_bridge: Optional[IDEBridge] = None
        
    def enable_ide_integration(self, ide_type: str = "vscode"):
        """Enable IDE integration"""
        if ide_type == "vscode":
            from ..integrations.ide_bridge import VSCodeBridge
            self.ide_bridge = VSCodeBridge(self.project_root)
        elif ide_type == "intellij":
            from ..integrations.ide_bridge import IntelliJBridge
            self.ide_bridge = IntelliJBridge(self.project_root)
        else:
            self.ide_bridge = IDEBridge(self.project_root)
        
        # Register event handlers
        self._setup_ide_handlers()
    
    def _setup_ide_handlers(self):
        """Setup IDE event handlers"""
        if not self.ide_bridge:
            return
        
        # Handle file opened
        async def on_file_opened(event: IDEEvent):
            if event.file_path:
                self.context_manager.add_file_to_context(event.file_path)
        
        # Handle file changed
        async def on_file_changed(event: IDEEvent):
            if event.file_path:
                self.context_manager.track_edit(
                    event.file_path,
                    'modified',
                    {'text': event.text}
                )
        
        self.ide_bridge.register_handler(IDEEventType.FILE_OPENED, on_file_opened)
        self.ide_bridge.register_handler(IDEEventType.FILE_CHANGED, on_file_changed)
    
    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user request with full context awareness
        Like Claude Code's intelligent request handling
        """
        # Infer user intent
        intent = self.context_manager.infer_user_intent(user_input)
        
        # Get relevant context
        relevant_files = self.context_manager.get_relevant_context(user_input)
        
        # Build context-aware prompt
        context_prompt = self.context_manager.build_context_prompt(user_input)
        
        # Process based on intent
        if intent == 'code_generation':
            return await self._handle_code_generation(user_input, context_prompt)
        
        elif intent == 'code_modification':
            return await self._handle_code_modification(user_input, context_prompt)
        
        elif intent == 'code_explanation':
            return await self._handle_code_explanation(user_input, context_prompt)
        
        elif intent == 'debugging':
            return await self._handle_debugging(user_input, context_prompt)
        
        elif intent == 'code_review':
            return await self._handle_code_review(user_input, context_prompt)
        
        else:
            return await self._handle_general_query(user_input, context_prompt)
    
    async def _handle_code_generation(
        self,
        user_input: str,
        context_prompt: str
    ) -> Dict[str, Any]:
        """Handle code generation request"""
        # This would integrate with the AI model
        return {
            'intent': 'code_generation',
            'context': context_prompt,
            'action': 'generate_code',
            'message': 'Code generation request processed'
        }
    
    async def _handle_code_modification(
        self,
        user_input: str,
        context_prompt: str
    ) -> Dict[str, Any]:
        """Handle code modification request"""
        return {
            'intent': 'code_modification',
            'context': context_prompt,
            'action': 'modify_code',
            'message': 'Code modification request processed'
        }
    
    async def _handle_code_explanation(
        self,
        user_input: str,
        context_prompt: str
    ) -> Dict[str, Any]:
        """Handle code explanation request"""
        return {
            'intent': 'code_explanation',
            'context': context_prompt,
            'action': 'explain_code',
            'message': 'Code explanation request processed'
        }
    
    async def _handle_debugging(
        self,
        user_input: str,
        context_prompt: str
    ) -> Dict[str, Any]:
        """Handle debugging request"""
        return {
            'intent': 'debugging',
            'context': context_prompt,
            'action': 'debug_code',
            'message': 'Debugging request processed'
        }
    
    async def _handle_code_review(
        self,
        user_input: str,
        context_prompt: str
    ) -> Dict[str, Any]:
        """Handle code review request"""
        # Get refactoring suggestions
        relevant_files = self.context_manager.get_relevant_context(user_input)
        suggestions = []
        
        for file_path in relevant_files:
            if file_path.exists():
                with open(file_path) as f:
                    code = f.read()
                file_suggestions = self.completion_engine.suggest_refactoring(
                    file_path,
                    code
                )
                suggestions.extend(file_suggestions)
        
        return {
            'intent': 'code_review',
            'context': context_prompt,
            'action': 'review_code',
            'suggestions': suggestions,
            'message': f'Found {len(suggestions)} suggestions'
        }
    
    async def _handle_general_query(
        self,
        user_input: str,
        context_prompt: str
    ) -> Dict[str, Any]:
        """Handle general query"""
        return {
            'intent': 'general_query',
            'context': context_prompt,
            'action': 'answer_query',
            'message': 'General query processed'
        }
    
    async def apply_multi_file_edit(
        self,
        description: str,
        edits: List[FileEdit],
        preview: bool = True
    ) -> Dict[str, Any]:
        """
        Apply a multi-file edit with preview
        Like Claude Code's edit application
        """
        multi_edit = self.multi_file_editor.create_multi_file_edit(
            description,
            edits
        )
        
        if preview:
            preview_text = self.multi_file_editor.preview_multi_file_edit(multi_edit)
            return {
                'action': 'preview',
                'preview': preview_text,
                'summary': self.multi_file_editor.get_edit_summary(multi_edit)
            }
        
        # Apply the edit
        success, errors = self.multi_file_editor.apply_multi_file_edit(multi_edit)
        
        # Track edits in context
        for edit in edits:
            self.context_manager.track_edit(
                edit.file_path,
                edit.edit_type.value,
                {'description': edit.description}
            )
        
        # Notify IDE if connected
        if self.ide_bridge and success:
            for edit in edits:
                await self.ide_bridge.send_notification('file_changed', {
                    'file': str(edit.file_path)
                })
        
        return {
            'action': 'applied',
            'success': success,
            'errors': errors,
            'summary': self.multi_file_editor.get_edit_summary(multi_edit)
        }
    
    async def get_completions(
        self,
        file_path: Path,
        line: int,
        column: int
    ) -> List[Completion]:
        """
        Get code completions for a position
        Like Claude Code's inline suggestions
        """
        if not file_path.exists():
            return []
        
        with open(file_path) as f:
            context_lines = f.readlines()
        
        return self.completion_engine.get_completions(
            file_path,
            line,
            column,
            context_lines
        )
    
    async def suggest_next_line(self, file_path: Path) -> Optional[str]:
        """
        Suggest the next line of code
        Like Claude Code's multi-line suggestions
        """
        if not file_path.exists():
            return None
        
        with open(file_path) as f:
            context_lines = f.readlines()
        
        return self.completion_engine.suggest_next_line(file_path, context_lines)
    
    def add_file_to_context(self, file_path: Path):
        """Add a file to the current context"""
        self.context_manager.add_file_to_context(file_path)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context"""
        return self.context_manager.get_context_summary()
    
    async def explain_code(self, file_path: Path, line_start: int, line_end: int) -> str:
        """
        Explain a code snippet
        Like Claude Code's code explanation
        """
        if not file_path.exists():
            return "File not found"
        
        with open(file_path) as f:
            lines = f.readlines()
        
        code_snippet = ''.join(lines[line_start-1:line_end])
        
        # This would integrate with AI model for actual explanation
        return f"Explanation for lines {line_start}-{line_end} in {file_path.name}:\n{code_snippet}"
    
    async def find_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        Find all references to a symbol
        Like Claude Code's find references
        """
        contexts = self.context_manager.find_symbol(symbol_name)
        
        return [
            {
                'file': str(ctx.file_path),
                'line': ctx.line_start,
                'symbol': ctx.symbol_name,
                'type': ctx.symbol_type
            }
            for ctx in contexts
        ]
    
    async def refactor_symbol(
        self,
        old_name: str,
        new_name: str
    ) -> Dict[str, Any]:
        """
        Refactor a symbol across the codebase
        Like Claude Code's rename refactoring
        """
        contexts = self.context_manager.find_symbol(old_name)
        
        edits = []
        for ctx in contexts:
            # Create edit to rename symbol
            if ctx.file_path.exists():
                with open(ctx.file_path) as f:
                    content = f.read()
                
                # Simple replacement (in real implementation, use AST)
                new_content = content.replace(old_name, new_name)
                
                edit = self.multi_file_editor.replace_content(
                    ctx.file_path,
                    old_name,
                    new_name,
                    f"Rename {old_name} to {new_name}"
                )
                edits.append(edit)
        
        return await self.apply_multi_file_edit(
            f"Rename {old_name} to {new_name}",
            edits,
            preview=True
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'files_in_context': len(self.context_manager.conversation_context.current_files),
            'symbols_indexed': len(self.context_manager.symbol_index),
            'recent_edits': len(self.context_manager.conversation_context.recent_edits),
            'edit_history': len(self.multi_file_editor.edit_history),
            'ide_connected': self.ide_bridge is not None
        }
