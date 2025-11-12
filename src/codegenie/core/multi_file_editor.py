"""
Multi-File Editor - Claude Code-like multi-file editing capabilities
Handles coordinated edits across multiple files with change planning,
cross-file refactoring, and atomic operations.
"""

import ast
import difflib
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EditType(Enum):
    """Types of edits"""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    CREATE_FILE = "create_file"
    DELETE_FILE = "delete_file"


@dataclass
class FileEdit:
    """Represents a single file edit"""
    file_path: Path
    edit_type: EditType
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    description: str = ""


@dataclass
class MultiFileEdit:
    """Represents a coordinated edit across multiple files"""
    description: str
    edits: List[FileEdit] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    is_atomic: bool = True  # All or nothing execution
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class ChangeSet:
    """Represents a planned set of changes across multiple files"""
    intent: str  # Description of what the change set accomplishes
    file_edits: List[FileEdit] = field(default_factory=list)
    affected_files: Set[Path] = field(default_factory=set)
    dependencies: Dict[Path, List[Path]] = field(default_factory=dict)
    is_validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    estimated_impact: str = "low"  # low, medium, high


@dataclass
class ChangeResult:
    """Result of applying a change set"""
    success: bool
    changes_applied: int
    changes_failed: int
    errors: List[str] = field(default_factory=list)
    rollback_performed: bool = False
    affected_files: List[Path] = field(default_factory=list)


class MultiFileEditor:
    """
    Handles multi-file editing like Claude Code with advanced features:
    - Change planning and coordination
    - Cross-file refactoring
    - Atomic operations (all or nothing)
    - Import management
    - Symbol refactoring
    - Change validation
    """
    
    def __init__(self, project_root: Path, context_analyzer=None, diff_engine=None):
        """
        Initialize the multi-file editor.
        
        Args:
            project_root: Root directory of the project
            context_analyzer: Optional ContextAnalyzer for project understanding
            diff_engine: Optional DiffEngine for diff generation
        """
        self.project_root = Path(project_root)
        self.pending_edits: List[MultiFileEdit] = []
        self.edit_history: List[MultiFileEdit] = []
        self.context_analyzer = context_analyzer
        self.diff_engine = diff_engine
        self._backups: Dict[Path, str] = {}  # For atomic rollback
        
        logger.info(f"MultiFileEditor initialized for project: {project_root}")
    
    def create_file(self, file_path: Path, content: str, description: str = "") -> FileEdit:
        """Create a new file"""
        return FileEdit(
            file_path=file_path,
            edit_type=EditType.CREATE_FILE,
            new_content=content,
            description=description or f"Create {file_path.name}"
        )
    
    def delete_file(self, file_path: Path, description: str = "") -> FileEdit:
        """Delete a file"""
        return FileEdit(
            file_path=file_path,
            edit_type=EditType.DELETE_FILE,
            description=description or f"Delete {file_path.name}"
        )
    
    def insert_lines(
        self,
        file_path: Path,
        line_number: int,
        content: str,
        description: str = ""
    ) -> FileEdit:
        """Insert lines at a specific position"""
        return FileEdit(
            file_path=file_path,
            edit_type=EditType.INSERT,
            line_start=line_number,
            new_content=content,
            description=description or f"Insert at line {line_number}"
        )
    
    def delete_lines(
        self,
        file_path: Path,
        line_start: int,
        line_end: int,
        description: str = ""
    ) -> FileEdit:
        """Delete lines from a file"""
        # Read current content
        if file_path.exists():
            with open(file_path) as f:
                lines = f.readlines()
            old_content = ''.join(lines[line_start-1:line_end])
        else:
            old_content = ""
        
        return FileEdit(
            file_path=file_path,
            edit_type=EditType.DELETE,
            line_start=line_start,
            line_end=line_end,
            old_content=old_content,
            description=description or f"Delete lines {line_start}-{line_end}"
        )
    
    def replace_lines(
        self,
        file_path: Path,
        line_start: int,
        line_end: int,
        new_content: str,
        description: str = ""
    ) -> FileEdit:
        """Replace lines in a file"""
        # Read current content
        if file_path.exists():
            with open(file_path) as f:
                lines = f.readlines()
            old_content = ''.join(lines[line_start-1:line_end])
        else:
            old_content = ""
        
        return FileEdit(
            file_path=file_path,
            edit_type=EditType.REPLACE,
            line_start=line_start,
            line_end=line_end,
            old_content=old_content,
            new_content=new_content,
            description=description or f"Replace lines {line_start}-{line_end}"
        )
    
    def replace_content(
        self,
        file_path: Path,
        old_text: str,
        new_text: str,
        description: str = ""
    ) -> FileEdit:
        """Replace specific text in a file (search and replace)"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path) as f:
            content = f.read()
        
        if old_text not in content:
            raise ValueError(f"Text not found in {file_path}: {old_text[:50]}...")
        
        # Find line numbers
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if old_text in '\n'.join(lines[i:]):
                line_start = i + 1
                # Find end line
                remaining = '\n'.join(lines[i:])
                old_lines = old_text.count('\n') + 1
                line_end = line_start + old_lines - 1
                break
        else:
            line_start = 1
            line_end = len(lines)
        
        return FileEdit(
            file_path=file_path,
            edit_type=EditType.REPLACE,
            line_start=line_start,
            line_end=line_end,
            old_content=old_text,
            new_content=new_text,
            description=description or "Replace content"
        )
    
    def create_multi_file_edit(
        self,
        description: str,
        edits: List[FileEdit]
    ) -> MultiFileEdit:
        """Create a coordinated multi-file edit"""
        return MultiFileEdit(
            description=description,
            edits=edits
        )
    
    def apply_edit(self, edit: FileEdit, dry_run: bool = False) -> bool:
        """Apply a single file edit"""
        try:
            if edit.edit_type == EditType.CREATE_FILE:
                if dry_run:
                    return True
                edit.file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(edit.file_path, 'w') as f:
                    f.write(edit.new_content or '')
                return True
            
            elif edit.edit_type == EditType.DELETE_FILE:
                if dry_run:
                    return edit.file_path.exists()
                if edit.file_path.exists():
                    edit.file_path.unlink()
                return True
            
            elif edit.edit_type in [EditType.INSERT, EditType.DELETE, EditType.REPLACE]:
                if not edit.file_path.exists():
                    return False
                
                with open(edit.file_path) as f:
                    lines = f.readlines()
                
                if edit.edit_type == EditType.INSERT:
                    if dry_run:
                        return True
                    insert_pos = (edit.line_start or 1) - 1
                    new_lines = (edit.new_content or '').split('\n')
                    lines[insert_pos:insert_pos] = [l + '\n' for l in new_lines]
                
                elif edit.edit_type == EditType.DELETE:
                    if dry_run:
                        return True
                    start = (edit.line_start or 1) - 1
                    end = edit.line_end or len(lines)
                    del lines[start:end]
                
                elif edit.edit_type == EditType.REPLACE:
                    if dry_run:
                        return True
                    
                    # Handle content-based replacement
                    if edit.old_content:
                        content = ''.join(lines)
                        if edit.old_content in content:
                            content = content.replace(edit.old_content, edit.new_content or '', 1)
                            lines = content.split('\n')
                            lines = [l + '\n' if i < len(lines) - 1 else l for i, l in enumerate(lines)]
                        else:
                            return False
                    # Handle line-based replacement
                    else:
                        start = (edit.line_start or 1) - 1
                        end = edit.line_end or len(lines)
                        new_lines = (edit.new_content or '').split('\n')
                        lines[start:end] = [l + '\n' for l in new_lines]
                
                if not dry_run:
                    with open(edit.file_path, 'w') as f:
                        f.writelines(lines)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error applying edit to {edit.file_path}: {e}")
            return False
    
    def apply_multi_file_edit(
        self,
        multi_edit: MultiFileEdit,
        dry_run: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Apply a multi-file edit
        Returns (success, list of error messages)
        """
        errors = []
        
        # Validate all edits first
        for edit in multi_edit.edits:
            if not self.apply_edit(edit, dry_run=True):
                errors.append(f"Validation failed for {edit.file_path}: {edit.description}")
        
        if errors and not dry_run:
            return False, errors
        
        if dry_run:
            return len(errors) == 0, errors
        
        # Apply all edits
        for edit in multi_edit.edits:
            if not self.apply_edit(edit, dry_run=False):
                errors.append(f"Failed to apply edit to {edit.file_path}: {edit.description}")
        
        if not errors:
            self.edit_history.append(multi_edit)
        
        return len(errors) == 0, errors
    
    def preview_edit(self, edit: FileEdit) -> str:
        """Generate a preview of an edit (like Claude Code's diff view)"""
        if edit.edit_type == EditType.CREATE_FILE:
            return f"Create file: {edit.file_path}\n\n{edit.new_content or ''}"
        
        elif edit.edit_type == EditType.DELETE_FILE:
            return f"Delete file: {edit.file_path}"
        
        elif edit.edit_type in [EditType.INSERT, EditType.DELETE, EditType.REPLACE]:
            if not edit.file_path.exists():
                return f"File not found: {edit.file_path}"
            
            with open(edit.file_path) as f:
                lines = f.readlines()
            
            if edit.edit_type == EditType.INSERT:
                preview_lines = []
                insert_pos = (edit.line_start or 1) - 1
                
                # Show context before
                start_context = max(0, insert_pos - 2)
                for i in range(start_context, insert_pos):
                    preview_lines.append(f"  {i+1} | {lines[i]}")
                
                # Show inserted lines
                new_lines = (edit.new_content or '').split('\n')
                for i, line in enumerate(new_lines):
                    preview_lines.append(f"+ {insert_pos+i+1} | {line}")
                
                # Show context after
                end_context = min(len(lines), insert_pos + 2)
                for i in range(insert_pos, end_context):
                    preview_lines.append(f"  {i+1} | {lines[i]}")
                
                return '\n'.join(preview_lines)
            
            elif edit.edit_type == EditType.DELETE:
                preview_lines = []
                start = (edit.line_start or 1) - 1
                end = edit.line_end or len(lines)
                
                # Show context before
                start_context = max(0, start - 2)
                for i in range(start_context, start):
                    preview_lines.append(f"  {i+1} | {lines[i]}")
                
                # Show deleted lines
                for i in range(start, end):
                    preview_lines.append(f"- {i+1} | {lines[i]}")
                
                # Show context after
                end_context = min(len(lines), end + 2)
                for i in range(end, end_context):
                    preview_lines.append(f"  {i+1} | {lines[i]}")
                
                return '\n'.join(preview_lines)
            
            elif edit.edit_type == EditType.REPLACE:
                # Generate unified diff
                if edit.old_content and edit.new_content:
                    old_lines = edit.old_content.split('\n')
                    new_lines = edit.new_content.split('\n')
                    
                    diff = difflib.unified_diff(
                        old_lines,
                        new_lines,
                        fromfile=str(edit.file_path),
                        tofile=str(edit.file_path),
                        lineterm=''
                    )
                    
                    return '\n'.join(diff)
                else:
                    return f"Replace lines {edit.line_start}-{edit.line_end} in {edit.file_path}"
        
        return "Unknown edit type"
    
    def preview_multi_file_edit(self, multi_edit: MultiFileEdit) -> str:
        """Generate a preview of a multi-file edit"""
        preview_parts = [f"# {multi_edit.description}\n"]
        
        for i, edit in enumerate(multi_edit.edits, 1):
            preview_parts.append(f"\n## Edit {i}: {edit.description}")
            preview_parts.append(self.preview_edit(edit))
        
        return '\n'.join(preview_parts)
    
    def get_edit_summary(self, multi_edit: MultiFileEdit) -> Dict[str, Any]:
        """Get a summary of a multi-file edit"""
        files_affected = set()
        edit_types = {}
        
        for edit in multi_edit.edits:
            files_affected.add(edit.file_path)
            edit_type = edit.edit_type.value
            edit_types[edit_type] = edit_types.get(edit_type, 0) + 1
        
        return {
            'description': multi_edit.description,
            'files_affected': len(files_affected),
            'total_edits': len(multi_edit.edits),
            'edit_types': edit_types,
            'files': [str(f) for f in files_affected]
        }
    
    # ========== Task 10.1: Change Planning and Atomic Operations ==========
    
    def plan_changes(self, intent: str, files: Optional[List[Path]] = None) -> ChangeSet:
        """
        Plan a set of coordinated changes across multiple files.
        
        This method analyzes the intent and creates a comprehensive plan
        for changes that need to be made across multiple files.
        
        Args:
            intent: Description of what needs to be changed
            files: Optional list of files to consider (analyzes all if None)
            
        Returns:
            ChangeSet with planned changes
        """
        logger.info(f"Planning changes: {intent}")
        
        change_set = ChangeSet(intent=intent)
        
        # If no files specified, analyze project to find relevant files
        if files is None:
            files = self._find_relevant_files(intent)
        
        # Analyze dependencies between files
        change_set.dependencies = self._analyze_file_dependencies(files)
        
        # Estimate impact
        change_set.estimated_impact = self._estimate_impact(files, intent)
        
        # Store affected files
        change_set.affected_files = set(files)
        
        logger.info(f"Change plan created: {len(files)} files affected, impact: {change_set.estimated_impact}")
        
        return change_set
    
    def apply_changes(
        self,
        change_set: ChangeSet,
        atomic: bool = True,
        validate: bool = True
    ) -> ChangeResult:
        """
        Apply a planned change set to files.
        
        Args:
            change_set: ChangeSet to apply
            atomic: If True, rollback all changes if any fail
            validate: If True, validate changes before applying
            
        Returns:
            ChangeResult with application results
        """
        logger.info(f"Applying change set: {change_set.intent} (atomic={atomic})")
        
        result = ChangeResult(
            success=False,
            changes_applied=0,
            changes_failed=0
        )
        
        # Validate if requested
        if validate:
            validation_result = self.validate_changes(change_set)
            if not validation_result['valid']:
                result.errors = validation_result['errors']
                logger.error(f"Validation failed: {result.errors}")
                return result
        
        # Create backups for atomic operation
        if atomic:
            self._create_backups(change_set.affected_files)
        
        # Apply each edit
        for edit in change_set.file_edits:
            try:
                success = self.apply_edit(edit, dry_run=False)
                if success:
                    result.changes_applied += 1
                    result.affected_files.append(edit.file_path)
                else:
                    result.changes_failed += 1
                    result.errors.append(f"Failed to apply edit to {edit.file_path}")
                    
                    # Rollback if atomic
                    if atomic:
                        logger.warning("Atomic operation failed, rolling back changes")
                        self._rollback_changes()
                        result.rollback_performed = True
                        return result
                        
            except Exception as e:
                result.changes_failed += 1
                result.errors.append(f"Error applying edit to {edit.file_path}: {e}")
                
                # Rollback if atomic
                if atomic:
                    logger.error(f"Atomic operation failed with exception: {e}")
                    self._rollback_changes()
                    result.rollback_performed = True
                    return result
        
        # Success if all changes applied
        result.success = result.changes_failed == 0
        
        # Clear backups if successful
        if result.success and atomic:
            self._clear_backups()
        
        logger.info(f"Change set applied: {result.changes_applied} succeeded, {result.changes_failed} failed")
        
        return result
    
    def refactor_across_files(
        self,
        refactoring_type: str,
        target: str,
        replacement: str,
        files: Optional[List[Path]] = None
    ) -> ChangeSet:
        """
        Perform cross-file refactoring operations.
        
        Args:
            refactoring_type: Type of refactoring (rename, move, extract, etc.)
            target: Target to refactor (symbol name, file path, etc.)
            replacement: Replacement value
            files: Optional list of files to refactor (analyzes all if None)
            
        Returns:
            ChangeSet with refactoring changes
        """
        logger.info(f"Cross-file refactoring: {refactoring_type} {target} -> {replacement}")
        
        if refactoring_type == "rename_symbol":
            return self._refactor_rename_symbol(target, replacement, files)
        elif refactoring_type == "move_file":
            return self._refactor_move_file(Path(target), Path(replacement))
        elif refactoring_type == "extract_function":
            return self._refactor_extract_function(target, replacement, files)
        else:
            logger.warning(f"Unknown refactoring type: {refactoring_type}")
            return ChangeSet(intent=f"Unknown refactoring: {refactoring_type}")
    
    def validate_changes(self, change_set: ChangeSet) -> Dict[str, Any]:
        """
        Validate a change set before applying.
        
        Args:
            change_set: ChangeSet to validate
            
        Returns:
            Dictionary with validation results
        """
        logger.debug(f"Validating change set: {change_set.intent}")
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if all files exist
        for file_path in change_set.affected_files:
            if not file_path.exists() and not any(
                edit.edit_type == EditType.CREATE_FILE and edit.file_path == file_path
                for edit in change_set.file_edits
            ):
                result['errors'].append(f"File does not exist: {file_path}")
                result['valid'] = False
        
        # Validate each edit
        for edit in change_set.file_edits:
            if edit.edit_type in [EditType.INSERT, EditType.DELETE, EditType.REPLACE]:
                if edit.file_path.exists():
                    # Check if file is readable
                    try:
                        with open(edit.file_path, 'r') as f:
                            f.read()
                    except Exception as e:
                        result['errors'].append(f"Cannot read file {edit.file_path}: {e}")
                        result['valid'] = False
        
        # Check for circular dependencies
        if self._has_circular_dependencies(change_set.dependencies):
            result['errors'].append("Circular dependencies detected in change set")
            result['valid'] = False
        
        change_set.is_validated = result['valid']
        change_set.validation_errors = result['errors']
        
        return result
    
    # ========== Private Helper Methods ==========
    
    def _find_relevant_files(self, intent: str) -> List[Path]:
        """Find files relevant to the given intent."""
        # Simple implementation - can be enhanced with AI/context analysis
        relevant_files = []
        
        # Search for Python files in project
        for file_path in self.project_root.rglob('*.py'):
            # Skip common ignore patterns
            if any(part.startswith('.') or part in ['__pycache__', 'venv', 'env'] 
                   for part in file_path.parts):
                continue
            relevant_files.append(file_path)
        
        return relevant_files[:50]  # Limit to avoid processing too many files
    
    def _analyze_file_dependencies(self, files: List[Path]) -> Dict[Path, List[Path]]:
        """Analyze dependencies between files."""
        dependencies = {}
        
        for file_path in files:
            if not file_path.exists() or file_path.suffix != '.py':
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Parse imports
                tree = ast.parse(content)
                file_deps = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Try to resolve to file path
                            module_path = self._resolve_module_path(node.module, file_path)
                            if module_path and module_path in files:
                                file_deps.append(module_path)
                
                dependencies[file_path] = file_deps
                
            except Exception as e:
                logger.debug(f"Error analyzing dependencies for {file_path}: {e}")
                dependencies[file_path] = []
        
        return dependencies
    
    def _resolve_module_path(self, module_name: str, from_file: Path) -> Optional[Path]:
        """Resolve a module name to a file path."""
        # Simple resolution - can be enhanced
        parts = module_name.split('.')
        
        # Try relative to project root
        potential_path = self.project_root / '/'.join(parts)
        if potential_path.with_suffix('.py').exists():
            return potential_path.with_suffix('.py')
        
        # Try as package
        potential_init = potential_path / '__init__.py'
        if potential_init.exists():
            return potential_init
        
        return None
    
    def _estimate_impact(self, files: List[Path], intent: str) -> str:
        """Estimate the impact of changes."""
        num_files = len(files)
        
        # Simple heuristic
        if num_files <= 2:
            return "low"
        elif num_files <= 10:
            return "medium"
        else:
            return "high"
    
    def _create_backups(self, files: Set[Path]) -> None:
        """Create backups of files for atomic rollback."""
        self._backups.clear()
        
        for file_path in files:
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        self._backups[file_path] = f.read()
                    logger.debug(f"Created backup for {file_path}")
                except Exception as e:
                    logger.warning(f"Could not backup {file_path}: {e}")
    
    def _rollback_changes(self) -> None:
        """Rollback changes using backups."""
        logger.info(f"Rolling back {len(self._backups)} files")
        
        for file_path, content in self._backups.items():
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.debug(f"Rolled back {file_path}")
            except Exception as e:
                logger.error(f"Error rolling back {file_path}: {e}")
        
        self._backups.clear()
    
    def _clear_backups(self) -> None:
        """Clear backup storage."""
        self._backups.clear()
        logger.debug("Cleared backups")
    
    def _has_circular_dependencies(self, dependencies: Dict[Path, List[Path]]) -> bool:
        """Check for circular dependencies."""
        def has_cycle(node: Path, visited: Set[Path], rec_stack: Set[Path]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for node in dependencies:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    return True
        
        return False
    
    def _refactor_rename_symbol(
        self,
        old_name: str,
        new_name: str,
        files: Optional[List[Path]]
    ) -> ChangeSet:
        """Refactor by renaming a symbol across files."""
        change_set = ChangeSet(intent=f"Rename symbol {old_name} to {new_name}")
        
        if files is None:
            files = self._find_relevant_files(old_name)
        
        for file_path in files:
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Simple regex-based replacement (can be enhanced with AST)
                pattern = r'\b' + re.escape(old_name) + r'\b'
                if re.search(pattern, content):
                    new_content = re.sub(pattern, new_name, content)
                    
                    edit = self.replace_content(
                        file_path,
                        content,
                        new_content,
                        f"Rename {old_name} to {new_name}"
                    )
                    change_set.file_edits.append(edit)
                    change_set.affected_files.add(file_path)
                    
            except Exception as e:
                logger.warning(f"Error processing {file_path} for rename: {e}")
        
        return change_set
    
    def _refactor_move_file(self, old_path: Path, new_path: Path) -> ChangeSet:
        """Refactor by moving a file and updating references."""
        change_set = ChangeSet(intent=f"Move file {old_path} to {new_path}")
        
        # Find all files that import the moved file
        all_files = list(self.project_root.rglob('*.py'))
        
        for file_path in all_files:
            if file_path == old_path:
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check if file imports the moved file
                old_module = self._path_to_module(old_path)
                new_module = self._path_to_module(new_path)
                
                if old_module in content:
                    new_content = content.replace(old_module, new_module)
                    
                    edit = self.replace_content(
                        file_path,
                        content,
                        new_content,
                        f"Update import from {old_module} to {new_module}"
                    )
                    change_set.file_edits.append(edit)
                    change_set.affected_files.add(file_path)
                    
            except Exception as e:
                logger.warning(f"Error processing {file_path} for move: {e}")
        
        return change_set
    
    def _refactor_extract_function(
        self,
        code_snippet: str,
        function_name: str,
        files: Optional[List[Path]]
    ) -> ChangeSet:
        """Refactor by extracting code into a function."""
        change_set = ChangeSet(intent=f"Extract function {function_name}")
        
        # This is a placeholder - full implementation would require
        # sophisticated code analysis
        logger.info(f"Extract function refactoring: {function_name}")
        
        return change_set
    
    def _path_to_module(self, file_path: Path) -> str:
        """Convert a file path to a module name."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            return '.'.join(parts)
        except ValueError:
            return str(file_path.stem)
    
    # ========== Task 10.2: Import Management ==========
    
    def update_imports(
        self,
        moved_file: Path,
        new_path: Path,
        files: Optional[List[Path]] = None
    ) -> List[FileEdit]:
        """
        Update imports when a file is moved or renamed.
        
        Args:
            moved_file: Original file path
            new_path: New file path
            files: Optional list of files to update (analyzes all if None)
            
        Returns:
            List of FileEdit objects for import updates
        """
        logger.info(f"Updating imports: {moved_file} -> {new_path}")
        
        edits = []
        
        if files is None:
            files = list(self.project_root.rglob('*.py'))
        
        old_module = self._path_to_module(moved_file)
        new_module = self._path_to_module(new_path)
        
        for file_path in files:
            if file_path == moved_file or not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check if file imports the moved module
                if old_module not in content:
                    continue
                
                # Parse and update imports
                tree = ast.parse(content)
                lines = content.splitlines()
                changes_made = False
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == old_module or alias.name.startswith(old_module + '.'):
                                # Update import
                                new_import = alias.name.replace(old_module, new_module, 1)
                                line_idx = node.lineno - 1
                                old_line = lines[line_idx]
                                new_line = old_line.replace(alias.name, new_import)
                                lines[line_idx] = new_line
                                changes_made = True
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and (node.module == old_module or 
                                          node.module.startswith(old_module + '.')):
                            # Update from import
                            new_import = node.module.replace(old_module, new_module, 1)
                            line_idx = node.lineno - 1
                            old_line = lines[line_idx]
                            new_line = old_line.replace(node.module, new_import)
                            lines[line_idx] = new_line
                            changes_made = True
                
                if changes_made:
                    new_content = '\n'.join(lines)
                    edit = self.replace_content(
                        file_path,
                        content,
                        new_content,
                        f"Update imports from {old_module} to {new_module}"
                    )
                    edits.append(edit)
                    
            except Exception as e:
                logger.warning(f"Error updating imports in {file_path}: {e}")
        
        logger.info(f"Updated imports in {len(edits)} files")
        return edits
    
    def remove_unused_imports(
        self,
        file_path: Path,
        dry_run: bool = False
    ) -> Optional[FileEdit]:
        """
        Remove unused imports from a file.
        
        Args:
            file_path: Path to the file
            dry_run: If True, return edit without applying
            
        Returns:
            FileEdit if changes were made, None otherwise
        """
        logger.info(f"Removing unused imports from {file_path}")
        
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the file
            tree = ast.parse(content)
            
            # Find all imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'name': alias.asname or alias.name,
                            'module': alias.name,
                            'lineno': node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append({
                            'type': 'from',
                            'name': alias.asname or alias.name,
                            'module': node.module,
                            'lineno': node.lineno
                        })
            
            # Find all name references
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Get the base name
                    base = node
                    while isinstance(base, ast.Attribute):
                        base = base.value
                    if isinstance(base, ast.Name):
                        used_names.add(base.id)
            
            # Find unused imports
            unused_lines = set()
            for imp in imports:
                if imp['name'] not in used_names:
                    unused_lines.add(imp['lineno'])
            
            if not unused_lines:
                logger.info("No unused imports found")
                return None
            
            # Remove unused import lines
            lines = content.splitlines()
            new_lines = [line for i, line in enumerate(lines, 1) if i not in unused_lines]
            new_content = '\n'.join(new_lines)
            
            # Create edit
            edit = self.replace_content(
                file_path,
                content,
                new_content,
                f"Remove {len(unused_lines)} unused imports"
            )
            
            if not dry_run:
                self.apply_edit(edit, dry_run=False)
            
            logger.info(f"Removed {len(unused_lines)} unused imports")
            return edit
            
        except Exception as e:
            logger.error(f"Error removing unused imports: {e}")
            return None
    
    def organize_imports(
        self,
        file_path: Path,
        style: str = "pep8",
        dry_run: bool = False
    ) -> Optional[FileEdit]:
        """
        Organize and sort imports in a file.
        
        Args:
            file_path: Path to the file
            style: Import organization style (pep8, google, etc.)
            dry_run: If True, return edit without applying
            
        Returns:
            FileEdit if changes were made, None otherwise
        """
        logger.info(f"Organizing imports in {file_path} (style: {style})")
        
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the file
            tree = ast.parse(content)
            lines = content.splitlines()
            
            # Collect imports
            stdlib_imports = []
            third_party_imports = []
            local_imports = []
            
            import_end_line = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_end_line = max(import_end_line, node.lineno)
                    line = lines[node.lineno - 1]
                    
                    # Categorize import
                    if isinstance(node, ast.Import):
                        module = node.names[0].name
                    else:
                        module = node.module or ''
                    
                    if self._is_stdlib_module(module):
                        stdlib_imports.append(line)
                    elif module.startswith('.'):
                        local_imports.append(line)
                    else:
                        third_party_imports.append(line)
            
            if not (stdlib_imports or third_party_imports or local_imports):
                logger.info("No imports to organize")
                return None
            
            # Sort imports within each group
            stdlib_imports.sort()
            third_party_imports.sort()
            local_imports.sort()
            
            # Build organized imports
            organized = []
            if stdlib_imports:
                organized.extend(stdlib_imports)
                organized.append('')
            if third_party_imports:
                organized.extend(third_party_imports)
                organized.append('')
            if local_imports:
                organized.extend(local_imports)
                organized.append('')
            
            # Replace import section
            new_lines = organized + lines[import_end_line:]
            new_content = '\n'.join(new_lines)
            
            # Create edit
            edit = self.replace_content(
                file_path,
                content,
                new_content,
                "Organize imports"
            )
            
            if not dry_run:
                self.apply_edit(edit, dry_run=False)
            
            logger.info("Imports organized successfully")
            return edit
            
        except Exception as e:
            logger.error(f"Error organizing imports: {e}")
            return None
    
    def add_missing_import(
        self,
        file_path: Path,
        symbol: str,
        module: str,
        dry_run: bool = False
    ) -> Optional[FileEdit]:
        """
        Add a missing import to a file.
        
        Args:
            file_path: Path to the file
            symbol: Symbol to import
            module: Module to import from
            dry_run: If True, return edit without applying
            
        Returns:
            FileEdit if successful, None otherwise
        """
        logger.info(f"Adding import: from {module} import {symbol} to {file_path}")
        
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if import already exists
            if f"from {module} import" in content and symbol in content:
                logger.info("Import already exists")
                return None
            
            # Find where to insert the import
            lines = content.splitlines()
            insert_line = 0
            
            # Find last import line
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_line = max(insert_line, node.lineno)
            
            # Insert the import
            new_import = f"from {module} import {symbol}"
            lines.insert(insert_line, new_import)
            new_content = '\n'.join(lines)
            
            # Create edit
            edit = self.insert_lines(
                file_path,
                insert_line + 1,
                new_import,
                f"Add import: from {module} import {symbol}"
            )
            
            if not dry_run:
                self.apply_edit(edit, dry_run=False)
            
            logger.info("Import added successfully")
            return edit
            
        except Exception as e:
            logger.error(f"Error adding import: {e}")
            return None
    
    def _is_stdlib_module(self, module_name: str) -> bool:
        """Check if a module is from Python standard library."""
        # Common stdlib modules
        stdlib_modules = {
            'os', 'sys', 'json', 'ast', 're', 'pathlib', 'typing',
            'collections', 'itertools', 'functools', 'datetime',
            'logging', 'unittest', 'argparse', 'subprocess', 'shutil',
            'tempfile', 'io', 'csv', 'xml', 'html', 'http', 'urllib',
            'email', 'base64', 'hashlib', 'hmac', 'secrets', 'random',
            'math', 'statistics', 'decimal', 'fractions', 'time',
            'threading', 'multiprocessing', 'asyncio', 'queue',
            'socket', 'ssl', 'select', 'signal', 'errno', 'ctypes'
        }
        
        base_module = module_name.split('.')[0]
        return base_module in stdlib_modules
    
    # ========== Task 10.3: Symbol Refactoring ==========
    
    def refactor_symbol(
        self,
        symbol: str,
        new_name: str,
        scope: str = "project",
        files: Optional[List[Path]] = None
    ) -> List[FileEdit]:
        """
        Rename a symbol across multiple files.
        
        Args:
            symbol: Symbol name to rename
            new_name: New symbol name
            scope: Scope of refactoring (file, module, project)
            files: Optional list of files to refactor
            
        Returns:
            List of FileEdit objects
        """
        logger.info(f"Refactoring symbol: {symbol} -> {new_name} (scope: {scope})")
        
        edits = []
        
        if files is None:
            if scope == "project":
                files = list(self.project_root.rglob('*.py'))
            else:
                files = []
        
        for file_path in files:
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Use word boundary regex to avoid partial matches
                pattern = r'\b' + re.escape(symbol) + r'\b'
                
                if re.search(pattern, content):
                    new_content = re.sub(pattern, new_name, content)
                    
                    edit = self.replace_content(
                        file_path,
                        content,
                        new_content,
                        f"Rename symbol {symbol} to {new_name}"
                    )
                    edits.append(edit)
                    
            except Exception as e:
                logger.warning(f"Error refactoring symbol in {file_path}: {e}")
        
        logger.info(f"Symbol refactored in {len(edits)} files")
        return edits
    
    def move_rename_file(
        self,
        old_path: Path,
        new_path: Path,
        update_references: bool = True
    ) -> ChangeSet:
        """
        Move or rename a file and update all references.
        
        Args:
            old_path: Current file path
            new_path: New file path
            update_references: Whether to update imports in other files
            
        Returns:
            ChangeSet with all necessary changes
        """
        logger.info(f"Moving/renaming file: {old_path} -> {new_path}")
        
        change_set = ChangeSet(intent=f"Move/rename {old_path.name} to {new_path.name}")
        
        # Add file move operation
        move_edit = FileEdit(
            file_path=old_path,
            edit_type=EditType.DELETE_FILE,
            description=f"Move {old_path} to {new_path}"
        )
        change_set.file_edits.append(move_edit)
        
        # Read content and create new file
        if old_path.exists():
            try:
                with open(old_path, 'r') as f:
                    content = f.read()
                
                create_edit = FileEdit(
                    file_path=new_path,
                    edit_type=EditType.CREATE_FILE,
                    new_content=content,
                    description=f"Create {new_path}"
                )
                change_set.file_edits.append(create_edit)
                change_set.affected_files.add(old_path)
                change_set.affected_files.add(new_path)
                
            except Exception as e:
                logger.error(f"Error reading file {old_path}: {e}")
                return change_set
        
        # Update references if requested
        if update_references:
            import_edits = self.update_imports(old_path, new_path)
            change_set.file_edits.extend(import_edits)
            for edit in import_edits:
                change_set.affected_files.add(edit.file_path)
        
        logger.info(f"File move/rename planned: {len(change_set.file_edits)} edits")
        return change_set
    
    def update_references(
        self,
        symbol: str,
        new_symbol: str,
        file_path: Optional[Path] = None
    ) -> List[FileEdit]:
        """
        Update all references to a symbol.
        
        Args:
            symbol: Original symbol name
            new_symbol: New symbol name
            file_path: Optional specific file (updates all if None)
            
        Returns:
            List of FileEdit objects
        """
        logger.info(f"Updating references: {symbol} -> {new_symbol}")
        
        if file_path:
            files = [file_path]
        else:
            files = list(self.project_root.rglob('*.py'))
        
        edits = []
        
        for fp in files:
            if not fp.exists():
                continue
            
            try:
                with open(fp, 'r') as f:
                    content = f.read()
                
                # Parse AST to find references
                tree = ast.parse(content)
                has_reference = False
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == symbol:
                        has_reference = True
                        break
                    elif isinstance(node, ast.Attribute) and node.attr == symbol:
                        has_reference = True
                        break
                
                if has_reference:
                    # Use word boundary regex for replacement
                    pattern = r'\b' + re.escape(symbol) + r'\b'
                    new_content = re.sub(pattern, new_symbol, content)
                    
                    edit = self.replace_content(
                        fp,
                        content,
                        new_content,
                        f"Update references from {symbol} to {new_symbol}"
                    )
                    edits.append(edit)
                    
            except Exception as e:
                logger.warning(f"Error updating references in {fp}: {e}")
        
        logger.info(f"Updated references in {len(edits)} files")
        return edits
    
    def extract_method(
        self,
        file_path: Path,
        start_line: int,
        end_line: int,
        method_name: str,
        dry_run: bool = False
    ) -> Optional[FileEdit]:
        """
        Extract a block of code into a new method.
        
        Args:
            file_path: Path to the file
            start_line: Start line of code to extract
            end_line: End line of code to extract
            method_name: Name for the new method
            dry_run: If True, return edit without applying
            
        Returns:
            FileEdit if successful, None otherwise
        """
        logger.info(f"Extracting method {method_name} from {file_path} lines {start_line}-{end_line}")
        
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = content.splitlines()
            
            # Extract the code block
            extracted_lines = lines[start_line-1:end_line]
            extracted_code = '\n'.join(extracted_lines)
            
            # Determine indentation
            indent = len(extracted_lines[0]) - len(extracted_lines[0].lstrip())
            base_indent = ' ' * indent
            
            # Create new method
            new_method = f"\n{base_indent}def {method_name}(self):\n"
            for line in extracted_lines:
                new_method += f"{base_indent}    {line.lstrip()}\n"
            
            # Replace extracted code with method call
            method_call = f"{base_indent}self.{method_name}()"
            
            # Build new content
            new_lines = (
                lines[:start_line-1] +
                [method_call] +
                lines[end_line:] +
                [new_method]
            )
            new_content = '\n'.join(new_lines)
            
            # Create edit
            edit = self.replace_content(
                file_path,
                content,
                new_content,
                f"Extract method {method_name}"
            )
            
            if not dry_run:
                self.apply_edit(edit, dry_run=False)
            
            logger.info(f"Method {method_name} extracted successfully")
            return edit
            
        except Exception as e:
            logger.error(f"Error extracting method: {e}")
            return None
    
    def inline_method(
        self,
        file_path: Path,
        method_name: str,
        dry_run: bool = False
    ) -> Optional[FileEdit]:
        """
        Inline a method by replacing calls with method body.
        
        Args:
            file_path: Path to the file
            method_name: Name of method to inline
            dry_run: If True, return edit without applying
            
        Returns:
            FileEdit if successful, None otherwise
        """
        logger.info(f"Inlining method {method_name} in {file_path}")
        
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse to find method definition
            tree = ast.parse(content)
            method_body = None
            method_node = None
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == method_name:
                    method_node = node
                    # Get method body lines
                    lines = content.splitlines()
                    method_body = '\n'.join(lines[node.lineno:node.end_lineno])
                    break
            
            if not method_body:
                logger.warning(f"Method {method_name} not found")
                return None
            
            # Find and replace method calls
            # This is a simplified implementation
            pattern = rf'\bself\.{re.escape(method_name)}\(\)'
            new_content = re.sub(pattern, f'# Inlined {method_name}\n{method_body}', content)
            
            # Create edit
            edit = self.replace_content(
                file_path,
                content,
                new_content,
                f"Inline method {method_name}"
            )
            
            if not dry_run:
                self.apply_edit(edit, dry_run=False)
            
            logger.info(f"Method {method_name} inlined successfully")
            return edit
            
        except Exception as e:
            logger.error(f"Error inlining method: {e}")
            return None
    
    # ========== Task 10.4: Change Validation ==========
    
    def validate_syntax(
        self,
        file_path: Path,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate syntax of a file or content.
        
        Args:
            file_path: Path to the file
            content: Optional content to validate (reads file if None)
            
        Returns:
            Dictionary with validation results
        """
        logger.debug(f"Validating syntax for {file_path}")
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_path': str(file_path)
        }
        
        # Get content
        if content is None:
            if not file_path.exists():
                result['valid'] = False
                result['errors'].append(f"File does not exist: {file_path}")
                return result
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
            except Exception as e:
                result['valid'] = False
                result['errors'].append(f"Error reading file: {e}")
                return result
        
        # Validate based on file type
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.py':
            result.update(self._validate_python_syntax(content))
        elif file_ext in ['.js', '.jsx']:
            result.update(self._validate_javascript_syntax(content))
        elif file_ext == '.json':
            result.update(self._validate_json_syntax(content))
        else:
            result['warnings'].append(f"No syntax validation available for {file_ext}")
        
        return result
    
    def validate_semantics(
        self,
        file_path: Path,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate semantic correctness of code.
        
        Args:
            file_path: Path to the file
            content: Optional content to validate
            
        Returns:
            Dictionary with validation results
        """
        logger.debug(f"Validating semantics for {file_path}")
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_path': str(file_path)
        }
        
        # Get content
        if content is None:
            if not file_path.exists():
                result['valid'] = False
                result['errors'].append(f"File does not exist: {file_path}")
                return result
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
            except Exception as e:
                result['valid'] = False
                result['errors'].append(f"Error reading file: {e}")
                return result
        
        # Validate based on file type
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.py':
            result.update(self._validate_python_semantics(content))
        
        return result
    
    def run_tests(
        self,
        test_files: Optional[List[Path]] = None,
        test_command: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run tests to validate changes.
        
        Args:
            test_files: Optional list of test files to run
            test_command: Optional custom test command
            
        Returns:
            Dictionary with test results
        """
        logger.info("Running tests to validate changes")
        
        import subprocess
        
        result = {
            'success': False,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'output': '',
            'errors': []
        }
        
        # Determine test command
        if test_command is None:
            # Try to detect test framework
            if (self.project_root / 'pytest.ini').exists() or \
               (self.project_root / 'setup.cfg').exists():
                test_command = 'pytest'
            elif (self.project_root / 'unittest').exists():
                test_command = 'python -m unittest discover'
            else:
                result['errors'].append("No test framework detected")
                return result
        
        # Add specific test files if provided
        if test_files:
            test_command += ' ' + ' '.join(str(f) for f in test_files)
        
        # Run tests
        try:
            proc = subprocess.run(
                test_command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            result['output'] = proc.stdout
            result['success'] = proc.returncode == 0
            
            # Parse output for test counts (pytest format)
            if 'pytest' in test_command:
                output = proc.stdout
                # Look for patterns like "5 passed" or "3 failed"
                passed_match = re.search(r'(\d+) passed', output)
                failed_match = re.search(r'(\d+) failed', output)
                
                if passed_match:
                    result['tests_passed'] = int(passed_match.group(1))
                if failed_match:
                    result['tests_failed'] = int(failed_match.group(1))
                
                result['tests_run'] = result['tests_passed'] + result['tests_failed']
            
            if not result['success']:
                result['errors'].append(f"Tests failed with exit code {proc.returncode}")
                if proc.stderr:
                    result['errors'].append(proc.stderr)
            
        except subprocess.TimeoutExpired:
            result['errors'].append("Test execution timed out")
        except Exception as e:
            result['errors'].append(f"Error running tests: {e}")
        
        logger.info(f"Tests completed: {result['tests_passed']} passed, {result['tests_failed']} failed")
        return result
    
    def validate_change_set_complete(
        self,
        change_set: ChangeSet,
        run_tests: bool = False
    ) -> Dict[str, Any]:
        """
        Perform complete validation of a change set.
        
        Args:
            change_set: ChangeSet to validate
            run_tests: Whether to run tests
            
        Returns:
            Dictionary with comprehensive validation results
        """
        logger.info(f"Performing complete validation of change set: {change_set.intent}")
        
        result = {
            'valid': True,
            'syntax_errors': [],
            'semantic_errors': [],
            'test_errors': [],
            'warnings': [],
            'files_validated': 0
        }
        
        # Validate syntax for all affected files
        for file_path in change_set.affected_files:
            # Find the edit for this file
            file_content = None
            for edit in change_set.file_edits:
                if edit.file_path == file_path and edit.new_content:
                    file_content = edit.new_content
                    break
            
            # Validate syntax
            syntax_result = self.validate_syntax(file_path, file_content)
            if not syntax_result['valid']:
                result['valid'] = False
                result['syntax_errors'].extend(syntax_result['errors'])
            result['warnings'].extend(syntax_result.get('warnings', []))
            
            # Validate semantics
            semantic_result = self.validate_semantics(file_path, file_content)
            if not semantic_result['valid']:
                result['valid'] = False
                result['semantic_errors'].extend(semantic_result['errors'])
            result['warnings'].extend(semantic_result.get('warnings', []))
            
            result['files_validated'] += 1
        
        # Run tests if requested
        if run_tests and result['valid']:
            test_result = self.run_tests()
            if not test_result['success']:
                result['valid'] = False
                result['test_errors'] = test_result['errors']
        
        logger.info(f"Validation complete: valid={result['valid']}, files={result['files_validated']}")
        return result
    
    def _validate_python_syntax(self, content: str) -> Dict[str, Any]:
        """Validate Python syntax."""
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        try:
            compile(content, '<string>', 'exec')
        except SyntaxError as e:
            result['valid'] = False
            result['errors'].append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Compilation error: {e}")
        
        return result
    
    def _validate_python_semantics(self, content: str) -> Dict[str, Any]:
        """Validate Python semantic correctness."""
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        try:
            tree = ast.parse(content)
            
            # Check for undefined variables (basic check)
            defined_names = set()
            used_names = set()
            
            for node in ast.walk(tree):
                # Track definitions
                if isinstance(node, ast.FunctionDef):
                    defined_names.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    defined_names.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined_names.add(target.id)
                
                # Track usage
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
            
            # Check for potentially undefined names (excluding builtins)
            builtins = {'print', 'len', 'str', 'int', 'float', 'list', 'dict', 
                       'set', 'tuple', 'range', 'enumerate', 'zip', 'map', 'filter',
                       'True', 'False', 'None', 'Exception', 'ValueError', 'TypeError'}
            
            undefined = used_names - defined_names - builtins
            if undefined:
                result['warnings'].append(f"Potentially undefined names: {', '.join(undefined)}")
            
        except Exception as e:
            result['warnings'].append(f"Semantic analysis error: {e}")
        
        return result
    
    def _validate_javascript_syntax(self, content: str) -> Dict[str, Any]:
        """Validate JavaScript syntax (basic checks)."""
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        # Basic bracket matching
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(content):
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    result['valid'] = False
                    result['errors'].append(f"Unmatched closing bracket at position {i}")
                    break
                open_bracket, _ = stack.pop()
                if brackets[open_bracket] != char:
                    result['valid'] = False
                    result['errors'].append(f"Mismatched brackets at position {i}")
                    break
        
        if stack:
            result['warnings'].append(f"Unclosed brackets: {len(stack)}")
        
        return result
    
    def _validate_json_syntax(self, content: str) -> Dict[str, Any]:
        """Validate JSON syntax."""
        import json
        
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            result['valid'] = False
            result['errors'].append(f"JSON error at line {e.lineno}: {e.msg}")
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"JSON validation error: {e}")
        
        return result
