"""
IDE-Specific Features
Implements inline diff preview, quick actions, and code lens integration
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class QuickActionType(Enum):
    """Types of quick actions"""
    FIX_ERROR = "fix_error"
    REFACTOR = "refactor"
    GENERATE_CODE = "generate_code"
    ADD_IMPORT = "add_import"
    OPTIMIZE = "optimize"
    ADD_DOCUMENTATION = "add_documentation"
    RUN_TESTS = "run_tests"
    FORMAT_CODE = "format_code"


@dataclass
class Range:
    """Represents a range in a document"""
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'start': {'line': self.start_line, 'character': self.start_column},
            'end': {'line': self.end_line, 'character': self.end_column}
        }


@dataclass
class InlineDiff:
    """Represents an inline diff preview"""
    file_path: Path
    range: Range
    original_text: str
    modified_text: str
    description: str
    can_apply: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'file': str(self.file_path),
            'range': self.range.to_dict(),
            'original': self.original_text,
            'modified': self.modified_text,
            'description': self.description,
            'canApply': self.can_apply
        }


@dataclass
class QuickAction:
    """Represents a quick action/code action"""
    id: str
    title: str
    action_type: QuickActionType
    file_path: Path
    range: Range
    command: Optional[str] = None
    arguments: List[Any] = field(default_factory=list)
    is_preferred: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'id': self.id,
            'title': self.title,
            'kind': self.action_type.value,
            'file': str(self.file_path),
            'range': self.range.to_dict(),
            'command': self.command,
            'arguments': self.arguments,
            'isPreferred': self.is_preferred
        }


@dataclass
class CodeLens:
    """Represents a code lens"""
    file_path: Path
    range: Range
    command: str
    title: str
    arguments: List[Any] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'range': self.range.to_dict(),
            'command': {
                'title': self.title,
                'command': self.command,
                'arguments': self.arguments
            }
        }


class InlineDiffProvider:
    """
    Provides inline diff preview functionality
    Shows changes directly in the editor before applying
    """
    
    def __init__(self):
        self.active_diffs: Dict[str, InlineDiff] = {}
    
    def create_diff(
        self,
        file_path: Path,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        original_text: str,
        modified_text: str,
        description: str
    ) -> InlineDiff:
        """Create an inline diff"""
        range_obj = Range(start_line, start_column, end_line, end_column)
        diff = InlineDiff(
            file_path=file_path,
            range=range_obj,
            original_text=original_text,
            modified_text=modified_text,
            description=description
        )
        
        diff_id = f"{file_path}:{start_line}:{start_column}"
        self.active_diffs[diff_id] = diff
        
        return diff
    
    def get_diff(self, diff_id: str) -> Optional[InlineDiff]:
        """Get a diff by ID"""
        return self.active_diffs.get(diff_id)
    
    def remove_diff(self, diff_id: str):
        """Remove a diff"""
        if diff_id in self.active_diffs:
            del self.active_diffs[diff_id]
    
    def get_diffs_for_file(self, file_path: Path) -> List[InlineDiff]:
        """Get all diffs for a file"""
        return [
            diff for diff in self.active_diffs.values()
            if diff.file_path == file_path
        ]
    
    def clear_all_diffs(self):
        """Clear all diffs"""
        self.active_diffs.clear()
    
    def apply_diff(self, diff_id: str, content: str) -> str:
        """Apply a diff to content"""
        diff = self.get_diff(diff_id)
        if not diff:
            return content
        
        lines = content.split('\n')
        
        # Replace the lines in the range
        start_line = diff.range.start_line
        end_line = diff.range.end_line
        
        # Handle single line replacement
        if start_line == end_line:
            line = lines[start_line]
            before = line[:diff.range.start_column]
            after = line[diff.range.end_column:]
            lines[start_line] = before + diff.modified_text + after
        else:
            # Multi-line replacement
            first_line = lines[start_line][:diff.range.start_column]
            last_line = lines[end_line][diff.range.end_column:]
            
            new_lines = diff.modified_text.split('\n')
            new_lines[0] = first_line + new_lines[0]
            new_lines[-1] = new_lines[-1] + last_line
            
            lines[start_line:end_line + 1] = new_lines
        
        return '\n'.join(lines)


class QuickActionProvider:
    """
    Provides quick actions/code actions
    Suggests fixes and improvements at cursor position
    """
    
    def __init__(self):
        self.action_handlers: Dict[QuickActionType, Callable] = {}
        self.registered_actions: List[QuickAction] = []
    
    def register_handler(self, action_type: QuickActionType, handler: Callable):
        """Register a handler for an action type"""
        self.action_handlers[action_type] = handler
    
    def create_action(
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
        arguments: Optional[List[Any]] = None,
        is_preferred: bool = False
    ) -> QuickAction:
        """Create a quick action"""
        range_obj = Range(start_line, start_column, end_line, end_column)
        action = QuickAction(
            id=action_id,
            title=title,
            action_type=action_type,
            file_path=file_path,
            range=range_obj,
            command=command,
            arguments=arguments or [],
            is_preferred=is_preferred
        )
        
        self.registered_actions.append(action)
        return action
    
    def get_actions_for_range(
        self,
        file_path: Path,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int
    ) -> List[QuickAction]:
        """Get all actions applicable to a range"""
        actions = []
        
        for action in self.registered_actions:
            if action.file_path == file_path:
                # Check if ranges overlap
                if self._ranges_overlap(
                    action.range,
                    Range(start_line, start_column, end_line, end_column)
                ):
                    actions.append(action)
        
        return actions
    
    def _ranges_overlap(self, range1: Range, range2: Range) -> bool:
        """Check if two ranges overlap"""
        # Simple overlap check
        if range1.end_line < range2.start_line:
            return False
        if range2.end_line < range1.start_line:
            return False
        return True
    
    async def execute_action(self, action_id: str) -> bool:
        """Execute a quick action"""
        action = next(
            (a for a in self.registered_actions if a.id == action_id),
            None
        )
        
        if not action:
            return False
        
        handler = self.action_handlers.get(action.action_type)
        if handler:
            await handler(action)
            return True
        
        return False
    
    def clear_actions_for_file(self, file_path: Path):
        """Clear all actions for a file"""
        self.registered_actions = [
            a for a in self.registered_actions
            if a.file_path != file_path
        ]
    
    def create_fix_error_action(
        self,
        file_path: Path,
        line: int,
        column: int,
        error_message: str,
        fix_text: str
    ) -> QuickAction:
        """Create a quick action to fix an error"""
        return self.create_action(
            action_id=f"fix_error_{file_path}_{line}_{column}",
            title=f"Fix: {error_message}",
            action_type=QuickActionType.FIX_ERROR,
            file_path=file_path,
            start_line=line,
            start_column=column,
            end_line=line,
            end_column=column + len(error_message),
            command="codegenie.applyFix",
            arguments=[str(file_path), line, column, fix_text],
            is_preferred=True
        )
    
    def create_refactor_action(
        self,
        file_path: Path,
        start_line: int,
        start_column: int,
        end_line: int,
        end_column: int,
        refactor_type: str,
        title: str
    ) -> QuickAction:
        """Create a refactoring action"""
        return self.create_action(
            action_id=f"refactor_{refactor_type}_{file_path}_{start_line}",
            title=title,
            action_type=QuickActionType.REFACTOR,
            file_path=file_path,
            start_line=start_line,
            start_column=start_column,
            end_line=end_line,
            end_column=end_column,
            command="codegenie.refactor",
            arguments=[str(file_path), refactor_type, start_line, end_line]
        )
    
    def create_add_import_action(
        self,
        file_path: Path,
        line: int,
        symbol: str,
        import_statement: str
    ) -> QuickAction:
        """Create an action to add an import"""
        return self.create_action(
            action_id=f"add_import_{file_path}_{symbol}",
            title=f"Add import: {import_statement}",
            action_type=QuickActionType.ADD_IMPORT,
            file_path=file_path,
            start_line=line,
            start_column=0,
            end_line=line,
            end_column=0,
            command="codegenie.addImport",
            arguments=[str(file_path), import_statement],
            is_preferred=True
        )


class CodeLensProvider:
    """
    Provides code lens integration
    Shows actionable information above code elements
    """
    
    def __init__(self):
        self.lenses: Dict[Path, List[CodeLens]] = {}
    
    def add_lens(
        self,
        file_path: Path,
        line: int,
        column: int,
        command: str,
        title: str,
        arguments: Optional[List[Any]] = None
    ) -> CodeLens:
        """Add a code lens"""
        range_obj = Range(line, column, line, column)
        lens = CodeLens(
            file_path=file_path,
            range=range_obj,
            command=command,
            title=title,
            arguments=arguments or []
        )
        
        if file_path not in self.lenses:
            self.lenses[file_path] = []
        
        self.lenses[file_path].append(lens)
        return lens
    
    def get_lenses_for_file(self, file_path: Path) -> List[CodeLens]:
        """Get all code lenses for a file"""
        return self.lenses.get(file_path, [])
    
    def clear_lenses_for_file(self, file_path: Path):
        """Clear all lenses for a file"""
        if file_path in self.lenses:
            del self.lenses[file_path]
    
    def clear_all_lenses(self):
        """Clear all lenses"""
        self.lenses.clear()
    
    def add_run_test_lens(
        self,
        file_path: Path,
        line: int,
        test_name: str
    ) -> CodeLens:
        """Add a lens to run a test"""
        return self.add_lens(
            file_path=file_path,
            line=line,
            column=0,
            command="codegenie.runTest",
            title=f"▶ Run {test_name}",
            arguments=[str(file_path), test_name]
        )
    
    def add_debug_test_lens(
        self,
        file_path: Path,
        line: int,
        test_name: str
    ) -> CodeLens:
        """Add a lens to debug a test"""
        return self.add_lens(
            file_path=file_path,
            line=line,
            column=0,
            command="codegenie.debugTest",
            title=f"🐛 Debug {test_name}",
            arguments=[str(file_path), test_name]
        )
    
    def add_references_lens(
        self,
        file_path: Path,
        line: int,
        symbol: str,
        reference_count: int
    ) -> CodeLens:
        """Add a lens showing reference count"""
        return self.add_lens(
            file_path=file_path,
            line=line,
            column=0,
            command="codegenie.showReferences",
            title=f"{reference_count} references",
            arguments=[str(file_path), line, symbol]
        )
    
    def add_implementation_lens(
        self,
        file_path: Path,
        line: int,
        interface_name: str,
        implementation_count: int
    ) -> CodeLens:
        """Add a lens showing implementations"""
        return self.add_lens(
            file_path=file_path,
            line=line,
            column=0,
            command="codegenie.showImplementations",
            title=f"{implementation_count} implementations",
            arguments=[str(file_path), line, interface_name]
        )
    
    def add_complexity_lens(
        self,
        file_path: Path,
        line: int,
        function_name: str,
        complexity: int
    ) -> CodeLens:
        """Add a lens showing code complexity"""
        complexity_label = "Low" if complexity < 5 else "Medium" if complexity < 10 else "High"
        return self.add_lens(
            file_path=file_path,
            line=line,
            column=0,
            command="codegenie.showComplexity",
            title=f"Complexity: {complexity} ({complexity_label})",
            arguments=[str(file_path), function_name, complexity]
        )


class IDEFeatureManager:
    """
    Manages all IDE-specific features
    Coordinates inline diffs, quick actions, and code lenses
    """
    
    def __init__(self):
        self.diff_provider = InlineDiffProvider()
        self.action_provider = QuickActionProvider()
        self.lens_provider = CodeLensProvider()
    
    def get_diff_provider(self) -> InlineDiffProvider:
        """Get the inline diff provider"""
        return self.diff_provider
    
    def get_action_provider(self) -> QuickActionProvider:
        """Get the quick action provider"""
        return self.action_provider
    
    def get_lens_provider(self) -> CodeLensProvider:
        """Get the code lens provider"""
        return self.lens_provider
    
    def clear_all_features_for_file(self, file_path: Path):
        """Clear all features for a file"""
        self.diff_provider.get_diffs_for_file(file_path)
        for diff in self.diff_provider.get_diffs_for_file(file_path):
            diff_id = f"{file_path}:{diff.range.start_line}:{diff.range.start_column}"
            self.diff_provider.remove_diff(diff_id)
        
        self.action_provider.clear_actions_for_file(file_path)
        self.lens_provider.clear_lenses_for_file(file_path)
    
    def clear_all_features(self):
        """Clear all features"""
        self.diff_provider.clear_all_diffs()
        self.action_provider.registered_actions.clear()
        self.lens_provider.clear_all_lenses()
    
    async def suggest_improvements(
        self,
        file_path: Path,
        content: str,
        language: str
    ) -> Dict[str, List[Any]]:
        """Analyze code and suggest improvements via quick actions and lenses"""
        suggestions = {
            'diffs': [],
            'actions': [],
            'lenses': []
        }
        
        # Example: Detect missing imports
        if language == 'python':
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Simple heuristic: look for undefined names
                if 'NameError' in line or 'ImportError' in line:
                    action = self.action_provider.create_add_import_action(
                        file_path=file_path,
                        line=i,
                        symbol='unknown',
                        import_statement='from module import symbol'
                    )
                    suggestions['actions'].append(action.to_dict())
        
        # Example: Add test run lenses
        if 'test_' in file_path.name or '_test' in file_path.name:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('def test_') or line.strip().startswith('async def test_'):
                    # Extract test name
                    test_name = line.strip().split('(')[0].replace('def ', '').replace('async ', '').strip()
                    
                    lens = self.lens_provider.add_run_test_lens(
                        file_path=file_path,
                        line=i,
                        test_name=test_name
                    )
                    suggestions['lenses'].append(lens.to_dict())
        
        return suggestions
