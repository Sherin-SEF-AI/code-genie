"""
Context Manager - Claude Code-like context awareness
Maintains deep understanding of codebase and conversation context
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class CodeContext:
    """Represents code context for a file or symbol"""
    file_path: Path
    symbol_name: str
    symbol_type: str  # function, class, variable, import
    line_start: int
    line_end: int
    code: str
    dependencies: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ConversationContext:
    """Maintains conversation context like Claude Code"""
    current_files: Set[Path] = field(default_factory=set)
    mentioned_symbols: Set[str] = field(default_factory=set)
    recent_edits: List[Dict[str, Any]] = field(default_factory=list)
    user_intent: Optional[str] = None
    task_history: List[str] = field(default_factory=list)


class ContextManager:
    """
    Manages context like Claude Code - understands what files are relevant,
    what the user is working on, and maintains conversation continuity
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.conversation_context = ConversationContext()
        self.code_contexts: Dict[Path, List[CodeContext]] = {}
        self.file_dependencies: Dict[Path, Set[Path]] = defaultdict(set)
        self.symbol_index: Dict[str, List[CodeContext]] = defaultdict(list)
        
    def add_file_to_context(self, file_path: Path):
        """Add a file to the current context (like opening a file in Claude Code)"""
        if not file_path.exists():
            return
        
        self.conversation_context.current_files.add(file_path)
        
        # Parse and index the file
        if file_path.suffix == '.py':
            self._parse_python_file(file_path)
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            self._parse_javascript_file(file_path)
    
    def _parse_python_file(self, file_path: Path):
        """Parse Python file and extract context"""
        try:
            with open(file_path) as f:
                content = f.read()
            
            tree = ast.parse(content)
            contexts = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    context = CodeContext(
                        file_path=file_path,
                        symbol_name=node.name,
                        symbol_type='function',
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        code=ast.get_source_segment(content, node) or '',
                        docstring=ast.get_docstring(node)
                    )
                    contexts.append(context)
                    self.symbol_index[node.name].append(context)
                    
                elif isinstance(node, ast.ClassDef):
                    context = CodeContext(
                        file_path=file_path,
                        symbol_name=node.name,
                        symbol_type='class',
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        code=ast.get_source_segment(content, node) or '',
                        docstring=ast.get_docstring(node)
                    )
                    contexts.append(context)
                    self.symbol_index[node.name].append(context)
            
            self.code_contexts[file_path] = contexts
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _parse_javascript_file(self, file_path: Path):
        """Parse JavaScript/TypeScript file (basic parsing)"""
        try:
            with open(file_path) as f:
                content = f.read()
            
            contexts = []
            
            # Simple regex-based parsing for functions and classes
            function_pattern = r'(?:function|const|let|var)\s+(\w+)\s*=?\s*(?:async\s*)?\([^)]*\)\s*(?:=>)?\s*\{'
            class_pattern = r'class\s+(\w+)\s*(?:extends\s+\w+)?\s*\{'
            
            for match in re.finditer(function_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                context = CodeContext(
                    file_path=file_path,
                    symbol_name=match.group(1),
                    symbol_type='function',
                    line_start=line_num,
                    line_end=line_num,  # Approximate
                    code=match.group(0)
                )
                contexts.append(context)
                self.symbol_index[match.group(1)].append(context)
            
            for match in re.finditer(class_pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                context = CodeContext(
                    file_path=file_path,
                    symbol_name=match.group(1),
                    symbol_type='class',
                    line_start=line_num,
                    line_end=line_num,  # Approximate
                    code=match.group(0)
                )
                contexts.append(context)
                self.symbol_index[match.group(1)].append(context)
            
            self.code_contexts[file_path] = contexts
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def find_symbol(self, symbol_name: str) -> List[CodeContext]:
        """Find all occurrences of a symbol across the codebase"""
        return self.symbol_index.get(symbol_name, [])
    
    def get_relevant_context(self, query: str, max_files: int = 5) -> List[Path]:
        """
        Get relevant files for a query (like Claude Code's context selection)
        Uses current files, mentioned symbols, and semantic relevance
        """
        relevant_files = set()
        
        # 1. Include currently open files
        relevant_files.update(self.conversation_context.current_files)
        
        # 2. Find files containing mentioned symbols
        words = re.findall(r'\b\w+\b', query.lower())
        for word in words:
            if word in self.symbol_index:
                for context in self.symbol_index[word]:
                    relevant_files.add(context.file_path)
        
        # 3. Include recently edited files
        for edit in self.conversation_context.recent_edits[-5:]:
            if 'file_path' in edit:
                relevant_files.add(Path(edit['file_path']))
        
        # 4. Limit to max_files
        return list(relevant_files)[:max_files]
    
    def track_edit(self, file_path: Path, edit_type: str, details: Dict[str, Any]):
        """Track an edit for context continuity"""
        self.conversation_context.recent_edits.append({
            'file_path': str(file_path),
            'edit_type': edit_type,
            'details': details,
            'timestamp': None  # Add timestamp if needed
        })
        
        # Keep only recent edits
        if len(self.conversation_context.recent_edits) > 20:
            self.conversation_context.recent_edits = \
                self.conversation_context.recent_edits[-20:]
    
    def infer_user_intent(self, user_input: str) -> str:
        """Infer user intent from input (like Claude Code's understanding)"""
        user_input_lower = user_input.lower()
        
        # Code generation
        if any(word in user_input_lower for word in ['create', 'write', 'generate', 'add', 'implement']):
            return 'code_generation'
        
        # Code modification
        elif any(word in user_input_lower for word in ['change', 'modify', 'update', 'refactor', 'fix']):
            return 'code_modification'
        
        # Code explanation
        elif any(word in user_input_lower for word in ['explain', 'what does', 'how does', 'why']):
            return 'code_explanation'
        
        # Debugging
        elif any(word in user_input_lower for word in ['debug', 'error', 'bug', 'issue', 'problem']):
            return 'debugging'
        
        # Code review
        elif any(word in user_input_lower for word in ['review', 'check', 'analyze', 'improve']):
            return 'code_review'
        
        # Testing
        elif any(word in user_input_lower for word in ['test', 'unit test', 'integration test']):
            return 'testing'
        
        else:
            return 'general_query'
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context (for display or debugging)"""
        return {
            'current_files': [str(f) for f in self.conversation_context.current_files],
            'total_symbols_indexed': len(self.symbol_index),
            'recent_edits_count': len(self.conversation_context.recent_edits),
            'user_intent': self.conversation_context.user_intent,
            'task_history': self.conversation_context.task_history[-5:]
        }
    
    def build_context_prompt(self, user_query: str) -> str:
        """
        Build a context-aware prompt like Claude Code
        Includes relevant code, recent edits, and conversation history
        """
        relevant_files = self.get_relevant_context(user_query)
        
        prompt_parts = []
        
        # Add project context
        prompt_parts.append("# Project Context")
        prompt_parts.append(f"Working directory: {self.project_root}")
        
        # Add current files
        if self.conversation_context.current_files:
            prompt_parts.append("\n# Currently Open Files:")
            for file in self.conversation_context.current_files:
                try:
                    rel_path = file.relative_to(self.project_root)
                    prompt_parts.append(f"- {rel_path}")
                except ValueError:
                    # File is outside project root
                    prompt_parts.append(f"- {file}")
        
        # Add relevant code context
        if relevant_files:
            prompt_parts.append("\n# Relevant Code:")
            for file in relevant_files[:3]:  # Limit to 3 files
                if file in self.code_contexts:
                    try:
                        rel_path = file.relative_to(self.project_root)
                        prompt_parts.append(f"\n## {rel_path}")
                    except ValueError:
                        prompt_parts.append(f"\n## {file.name}")
                    for context in self.code_contexts[file][:5]:  # Limit symbols per file
                        prompt_parts.append(f"- {context.symbol_type} {context.symbol_name} (line {context.line_start})")
        
        # Add recent edits
        if self.conversation_context.recent_edits:
            prompt_parts.append("\n# Recent Edits:")
            for edit in self.conversation_context.recent_edits[-3:]:
                prompt_parts.append(f"- {edit['edit_type']} in {edit['file_path']}")
        
        # Add user query
        prompt_parts.append(f"\n# User Query:\n{user_query}")
        
        return '\n'.join(prompt_parts)
    
    def clear_context(self):
        """Clear current context (like closing all files)"""
        self.conversation_context = ConversationContext()
    
    def get_file_context(self, file_path: Path) -> Optional[List[CodeContext]]:
        """Get all code contexts for a specific file"""
        return self.code_contexts.get(file_path)
