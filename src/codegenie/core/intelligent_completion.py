"""
Intelligent Code Completion - Claude Code-like suggestions
Provides context-aware code completions and suggestions
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CompletionType(Enum):
    """Types of completions"""
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    IMPORT = "import"
    METHOD = "method"
    PARAMETER = "parameter"
    SNIPPET = "snippet"


@dataclass
class Completion:
    """Represents a code completion suggestion"""
    text: str
    completion_type: CompletionType
    description: str
    confidence: float  # 0.0 to 1.0
    context: Optional[str] = None
    documentation: Optional[str] = None


class IntelligentCompletion:
    """
    Provides intelligent code completions like Claude Code
    Context-aware suggestions based on current code and project
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.completion_cache: Dict[str, List[Completion]] = {}
    
    def get_completions(
        self,
        file_path: Path,
        line: int,
        column: int,
        context_lines: List[str]
    ) -> List[Completion]:
        """
        Get code completions for a specific position
        Like Claude Code's inline suggestions
        """
        current_line = context_lines[line - 1] if line <= len(context_lines) else ""
        prefix = current_line[:column]
        
        completions = []
        
        # Detect what kind of completion is needed
        if self._is_import_context(prefix, context_lines):
            completions.extend(self._get_import_completions(prefix))
        
        elif self._is_function_call_context(prefix):
            completions.extend(self._get_function_completions(prefix, context_lines))
        
        elif self._is_class_context(prefix, context_lines):
            completions.extend(self._get_class_completions(prefix))
        
        elif self._is_method_context(prefix, context_lines):
            completions.extend(self._get_method_completions(prefix, context_lines))
        
        else:
            # General completions
            completions.extend(self._get_general_completions(prefix, context_lines))
        
        # Sort by confidence
        completions.sort(key=lambda c: c.confidence, reverse=True)
        
        return completions[:10]  # Return top 10
    
    def _is_import_context(self, prefix: str, context_lines: List[str]) -> bool:
        """Check if we're in an import statement"""
        return 'import' in prefix or 'from' in prefix
    
    def _is_function_call_context(self, prefix: str) -> bool:
        """Check if we're calling a function"""
        return bool(re.search(r'\w+\($', prefix))
    
    def _is_class_context(self, prefix: str, context_lines: List[str]) -> bool:
        """Check if we're defining or using a class"""
        return 'class ' in prefix or any('class ' in line for line in context_lines[-5:])
    
    def _is_method_context(self, prefix: str, context_lines: List[str]) -> bool:
        """Check if we're in a method definition"""
        return bool(re.search(r'def \w+\(', prefix))
    
    def _get_import_completions(self, prefix: str) -> List[Completion]:
        """Get import suggestions"""
        completions = []
        
        # Common Python imports
        common_imports = [
            ("import os", "Operating system interface"),
            ("import sys", "System-specific parameters"),
            ("import json", "JSON encoder and decoder"),
            ("import re", "Regular expressions"),
            ("from pathlib import Path", "Object-oriented filesystem paths"),
            ("from typing import List, Dict, Any", "Type hints"),
            ("import asyncio", "Asynchronous I/O"),
            ("import logging", "Logging facility"),
        ]
        
        for import_stmt, description in common_imports:
            if import_stmt.startswith(prefix.strip()):
                completions.append(Completion(
                    text=import_stmt,
                    completion_type=CompletionType.IMPORT,
                    description=description,
                    confidence=0.8
                ))
        
        return completions
    
    def _get_function_completions(
        self,
        prefix: str,
        context_lines: List[str]
    ) -> List[Completion]:
        """Get function call completions"""
        completions = []
        
        # Extract function name
        match = re.search(r'(\w+)\($', prefix)
        if not match:
            return completions
        
        func_name = match.group(1)
        
        # Common function patterns
        if func_name == 'print':
            completions.append(Completion(
                text='print(f"")',
                completion_type=CompletionType.FUNCTION,
                description="Print formatted string",
                confidence=0.9
            ))
        
        elif func_name == 'open':
            completions.append(Completion(
                text='open("", "r")',
                completion_type=CompletionType.FUNCTION,
                description="Open file for reading",
                confidence=0.9
            ))
        
        elif func_name == 'range':
            completions.append(Completion(
                text='range(10)',
                completion_type=CompletionType.FUNCTION,
                description="Create range of numbers",
                confidence=0.9
            ))
        
        return completions
    
    def _get_class_completions(self, prefix: str) -> List[Completion]:
        """Get class-related completions"""
        completions = []
        
        if 'class ' in prefix:
            # Suggest class template
            completions.append(Completion(
                text='''class ClassName:
    """Class description"""
    
    def __init__(self):
        pass
''',
                completion_type=CompletionType.CLASS,
                description="Basic class template",
                confidence=0.9
            ))
        
        return completions
    
    def _get_method_completions(
        self,
        prefix: str,
        context_lines: List[str]
    ) -> List[Completion]:
        """Get method definition completions"""
        completions = []
        
        # Check if we're in a class
        in_class = any('class ' in line for line in context_lines[-10:])
        
        if in_class:
            # Suggest common methods
            if 'def __init__' in prefix:
                completions.append(Completion(
                    text='def __init__(self):',
                    completion_type=CompletionType.METHOD,
                    description="Constructor method",
                    confidence=0.95
                ))
            
            elif 'def __str__' in prefix:
                completions.append(Completion(
                    text='def __str__(self):\n    return ""',
                    completion_type=CompletionType.METHOD,
                    description="String representation",
                    confidence=0.9
                ))
        
        return completions
    
    def _get_general_completions(
        self,
        prefix: str,
        context_lines: List[str]
    ) -> List[Completion]:
        """Get general code completions"""
        completions = []
        
        # Detect patterns and suggest completions
        
        # If/else blocks
        if prefix.strip().startswith('if '):
            completions.append(Completion(
                text='if condition:\n    pass',
                completion_type=CompletionType.SNIPPET,
                description="If statement",
                confidence=0.8
            ))
        
        # For loops
        elif prefix.strip().startswith('for '):
            completions.append(Completion(
                text='for item in items:\n    pass',
                completion_type=CompletionType.SNIPPET,
                description="For loop",
                confidence=0.8
            ))
        
        # Try/except
        elif prefix.strip().startswith('try'):
            completions.append(Completion(
                text='try:\n    pass\nexcept Exception as e:\n    pass',
                completion_type=CompletionType.SNIPPET,
                description="Try/except block",
                confidence=0.8
            ))
        
        # With statement
        elif prefix.strip().startswith('with '):
            completions.append(Completion(
                text='with open("", "r") as f:\n    pass',
                completion_type=CompletionType.SNIPPET,
                description="With statement",
                confidence=0.8
            ))
        
        return completions
    
    def suggest_next_line(
        self,
        file_path: Path,
        context_lines: List[str]
    ) -> Optional[str]:
        """
        Suggest the next line of code (like Claude Code's multi-line suggestions)
        """
        if not context_lines:
            return None
        
        last_line = context_lines[-1].strip()
        
        # Function definition -> suggest docstring
        if last_line.startswith('def ') and last_line.endswith(':'):
            return '    """Function description"""'
        
        # Class definition -> suggest docstring
        elif last_line.startswith('class ') and last_line.endswith(':'):
            return '    """Class description"""'
        
        # If statement -> suggest pass or implementation
        elif last_line.startswith('if ') and last_line.endswith(':'):
            return '    pass'
        
        # For loop -> suggest pass or implementation
        elif last_line.startswith('for ') and last_line.endswith(':'):
            return '    pass'
        
        # Try block -> suggest except
        elif last_line.startswith('try:'):
            return 'except Exception as e:'
        
        # Import statement -> suggest another import
        elif last_line.startswith('import ') or last_line.startswith('from '):
            return None  # Don't auto-suggest more imports
        
        return None
    
    def suggest_refactoring(
        self,
        file_path: Path,
        code: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest code refactorings (like Claude Code's improvement suggestions)
        """
        suggestions = []
        
        lines = code.split('\n')
        
        # Check for long functions
        in_function = False
        function_start = 0
        function_lines = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                if in_function and function_lines > 50:
                    suggestions.append({
                        'type': 'refactor',
                        'severity': 'warning',
                        'line': function_start,
                        'message': f'Function is too long ({function_lines} lines). Consider breaking it into smaller functions.',
                        'suggestion': 'Extract methods for better readability'
                    })
                in_function = True
                function_start = i + 1
                function_lines = 0
            elif in_function:
                function_lines += 1
        
        # Check for missing docstrings
        for i, line in enumerate(lines):
            if line.strip().startswith('def ') or line.strip().startswith('class '):
                # Check if next line is a docstring
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not next_line.startswith('"""') and not next_line.startswith("'''"):
                        suggestions.append({
                            'type': 'documentation',
                            'severity': 'info',
                            'line': i + 1,
                            'message': 'Missing docstring',
                            'suggestion': 'Add a docstring to document this function/class'
                        })
        
        # Check for bare except clauses
        for i, line in enumerate(lines):
            if 'except:' in line and 'except Exception' not in line:
                suggestions.append({
                    'type': 'best_practice',
                    'severity': 'warning',
                    'line': i + 1,
                    'message': 'Bare except clause',
                    'suggestion': 'Specify exception type: except Exception as e:'
                })
        
        return suggestions
