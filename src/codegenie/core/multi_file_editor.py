"""
Multi-File Editor - Claude Code-like multi-file editing capabilities
Handles coordinated edits across multiple files
"""

import difflib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


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


class MultiFileEditor:
    """
    Handles multi-file editing like Claude Code
    Can make coordinated changes across multiple files
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pending_edits: List[MultiFileEdit] = []
        self.edit_history: List[MultiFileEdit] = []
    
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
