"""
Diff Engine for advanced diff generation, visualization, and application.

Provides unified diff, side-by-side diff, syntax highlighting, patch application,
and multi-file diff capabilities.
"""

import difflib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class DiffFormat(Enum):
    """Diff output formats."""
    UNIFIED = "unified"
    SIDE_BY_SIDE = "side_by_side"
    CONTEXT = "context"
    INLINE = "inline"


class ChangeType(Enum):
    """Types of changes in a diff."""
    ADDITION = "addition"
    DELETION = "deletion"
    MODIFICATION = "modification"
    UNCHANGED = "unchanged"


@dataclass
class DiffLine:
    """Represents a single line in a diff."""
    line_number_old: Optional[int]
    line_number_new: Optional[int]
    content: str
    change_type: ChangeType
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'line_number_old': self.line_number_old,
            'line_number_new': self.line_number_new,
            'content': self.content,
            'change_type': self.change_type.value,
        }


@dataclass
class DiffHunk:
    """Represents a hunk (section) of changes in a diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine] = field(default_factory=list)
    header: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'old_start': self.old_start,
            'old_count': self.old_count,
            'new_start': self.new_start,
            'new_count': self.new_count,
            'header': self.header,
            'lines': [line.to_dict() for line in self.lines],
        }


@dataclass
class Diff:
    """Represents a complete diff between two versions."""
    original_file: str
    modified_file: str
    hunks: List[DiffHunk] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    modifications: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'original_file': self.original_file,
            'modified_file': self.modified_file,
            'hunks': [hunk.to_dict() for hunk in self.hunks],
            'additions': self.additions,
            'deletions': self.deletions,
            'modifications': self.modifications,
        }


@dataclass
class FileDiff:
    """Represents a diff for a single file."""
    file_path: Path
    original_content: str
    modified_content: str
    diff: Diff
    file_status: str  # 'modified', 'added', 'deleted'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': str(self.file_path),
            'file_status': self.file_status,
            'diff': self.diff.to_dict(),
        }


@dataclass
class Patch:
    """Represents a patch that can be applied to files."""
    file_diffs: List[FileDiff] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'description': self.description,
            'file_diffs': [fd.to_dict() for fd in self.file_diffs],
        }


class DiffEngine:
    """
    Advanced diff engine for generating, visualizing, and applying diffs.
    
    Supports multiple diff formats, syntax highlighting, patch application,
    and multi-file diff operations.
    """
    
    def __init__(
        self,
        context_lines: int = 3,
        syntax_highlighting: bool = True,
        colored_output: bool = True
    ):
        """
        Initialize the diff engine.
        
        Args:
            context_lines: Number of context lines around changes
            syntax_highlighting: Whether to enable syntax highlighting
            colored_output: Whether to use colored output
        """
        self.context_lines = context_lines
        self.syntax_highlighting = syntax_highlighting
        self.colored_output = colored_output
        
        logger.info("DiffEngine initialized")
    
    def generate_diff(
        self,
        original: str,
        modified: str,
        filename: str = "file",
        format: DiffFormat = DiffFormat.UNIFIED
    ) -> Diff:
        """
        Generate a diff between two versions of content.
        
        Args:
            original: Original content
            modified: Modified content
            filename: Filename for diff header
            format: Diff format to use
            
        Returns:
            Diff object with structured diff information
        """
        logger.debug(f"Generating diff for {filename}")
        
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            n=self.context_lines,
            lineterm=''
        ))
        
        # Parse diff into structured format
        diff = self._parse_unified_diff(diff_lines, filename, filename)
        
        return diff
    
    def show_unified_diff(self, diff: Diff) -> str:
        """
        Format a diff as unified diff output.
        
        Args:
            diff: Diff object to format
            
        Returns:
            Formatted unified diff string
        """
        lines = []
        
        # Add file headers
        lines.append(f"--- a/{diff.original_file}")
        lines.append(f"+++ b/{diff.modified_file}")
        
        # Add hunks
        for hunk in diff.hunks:
            # Add hunk header
            lines.append(f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@")
            
            # Add hunk lines
            for line in hunk.lines:
                if line.change_type == ChangeType.ADDITION:
                    lines.append(f"+{line.content}")
                elif line.change_type == ChangeType.DELETION:
                    lines.append(f"-{line.content}")
                else:
                    lines.append(f" {line.content}")
        
        unified_diff = '\n'.join(lines)
        
        # Apply coloring if enabled
        if self.colored_output:
            unified_diff = self._colorize_unified_diff(unified_diff)
        
        return unified_diff
    
    def show_side_by_side_diff(
        self,
        diff: Diff,
        width: int = 80,
        separator: str = " | "
    ) -> str:
        """
        Format a diff as side-by-side comparison.
        
        Args:
            diff: Diff object to format
            width: Total width of output
            separator: Separator between columns
            
        Returns:
            Formatted side-by-side diff string
        """
        lines = []
        
        # Calculate column widths
        line_num_width = 4
        separator_width = len(separator)
        content_width = (width - separator_width - 2 * line_num_width) // 2
        
        # Add header
        header = f"{'Original':<{content_width + line_num_width}}{separator}{'Modified':<{content_width + line_num_width}}"
        lines.append(header)
        lines.append("=" * width)
        
        # Process each hunk
        for hunk in diff.hunks:
            # Add hunk header
            hunk_header = f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@"
            lines.append(hunk_header)
            lines.append("-" * width)
            
            # Group lines for side-by-side display
            i = 0
            while i < len(hunk.lines):
                line = hunk.lines[i]
                
                if line.change_type == ChangeType.UNCHANGED:
                    # Show unchanged line on both sides
                    left = self._format_side_by_side_line(
                        line.line_number_old, line.content, content_width, ' '
                    )
                    right = self._format_side_by_side_line(
                        line.line_number_new, line.content, content_width, ' '
                    )
                    lines.append(f"{left}{separator}{right}")
                    i += 1
                
                elif line.change_type == ChangeType.DELETION:
                    # Check if next line is an addition (modification)
                    if i + 1 < len(hunk.lines) and hunk.lines[i + 1].change_type == ChangeType.ADDITION:
                        # Show as modification
                        next_line = hunk.lines[i + 1]
                        left = self._format_side_by_side_line(
                            line.line_number_old, line.content, content_width, '-'
                        )
                        right = self._format_side_by_side_line(
                            next_line.line_number_new, next_line.content, content_width, '+'
                        )
                        
                        if self.colored_output:
                            left = f"\033[31m{left}\033[0m"
                            right = f"\033[32m{right}\033[0m"
                        
                        lines.append(f"{left}{separator}{right}")
                        i += 2
                    else:
                        # Pure deletion
                        left = self._format_side_by_side_line(
                            line.line_number_old, line.content, content_width, '-'
                        )
                        right = " " * (content_width + line_num_width)
                        
                        if self.colored_output:
                            left = f"\033[31m{left}\033[0m"
                        
                        lines.append(f"{left}{separator}{right}")
                        i += 1
                
                elif line.change_type == ChangeType.ADDITION:
                    # Pure addition
                    left = " " * (content_width + line_num_width)
                    right = self._format_side_by_side_line(
                        line.line_number_new, line.content, content_width, '+'
                    )
                    
                    if self.colored_output:
                        right = f"\033[32m{right}\033[0m"
                    
                    lines.append(f"{left}{separator}{right}")
                    i += 1
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def apply_diff(
        self,
        file_path: Union[str, Path],
        diff: Diff,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply a diff to a file.
        
        Args:
            file_path: Path to the file to patch
            diff: Diff to apply
            dry_run: If True, don't actually modify the file
            
        Returns:
            Dictionary with result information
        """
        file_path = Path(file_path)
        
        logger.info(f"Applying diff to {file_path} (dry_run={dry_run})")
        
        # Read current file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"File not found: {file_path}",
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error reading file: {e}",
            }
        
        # Apply the diff
        try:
            new_content = self._apply_diff_to_content(current_content, diff)
        except Exception as e:
            return {
                'success': False,
                'error': f"Error applying diff: {e}",
            }
        
        # Write the new content if not dry run
        if not dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Error writing file: {e}",
                }
        
        return {
            'success': True,
            'file_path': str(file_path),
            'dry_run': dry_run,
            'changes_applied': len(diff.hunks),
        }
    
    def apply_selective_changes(
        self,
        file_path: Union[str, Path],
        diff: Diff,
        selected_hunks: List[int],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply only selected hunks from a diff.
        
        Args:
            file_path: Path to the file to patch
            diff: Diff containing changes
            selected_hunks: List of hunk indices to apply
            dry_run: If True, don't actually modify the file
            
        Returns:
            Dictionary with result information
        """
        logger.info(f"Applying selective changes to {file_path}")
        
        # Create a new diff with only selected hunks
        selective_diff = Diff(
            original_file=diff.original_file,
            modified_file=diff.modified_file,
            hunks=[diff.hunks[i] for i in selected_hunks if i < len(diff.hunks)]
        )
        
        # Recalculate statistics
        for hunk in selective_diff.hunks:
            for line in hunk.lines:
                if line.change_type == ChangeType.ADDITION:
                    selective_diff.additions += 1
                elif line.change_type == ChangeType.DELETION:
                    selective_diff.deletions += 1
        
        # Apply the selective diff
        return self.apply_diff(file_path, selective_diff, dry_run)
    
    def validate_changes(
        self,
        original: str,
        modified: str,
        file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate that changes are syntactically correct.
        
        Args:
            original: Original content
            modified: Modified content
            file_type: Optional file type for syntax checking
            
        Returns:
            Dictionary with validation results
        """
        logger.debug("Validating changes")
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
        }
        
        # Basic validation
        if not modified:
            result['warnings'].append("Modified content is empty")
        
        # File type specific validation
        if file_type:
            if file_type in ['python', '.py', 'text/x-python']:
                result.update(self._validate_python(modified))
            elif file_type in ['javascript', '.js', 'text/javascript']:
                result.update(self._validate_javascript(modified))
            elif file_type in ['json', '.json', 'application/json']:
                result.update(self._validate_json(modified))
        
        return result
    
    def create_patch(
        self,
        file_diffs: List[FileDiff],
        description: str = ""
    ) -> Patch:
        """
        Create a patch from multiple file diffs.
        
        Args:
            file_diffs: List of FileDiff objects
            description: Optional patch description
            
        Returns:
            Patch object
        """
        logger.info(f"Creating patch with {len(file_diffs)} file diffs")
        
        return Patch(
            file_diffs=file_diffs,
            description=description
        )
    
    def generate_batch_diff(
        self,
        file_changes: Dict[Path, Tuple[str, str]]
    ) -> List[FileDiff]:
        """
        Generate diffs for multiple files.
        
        Args:
            file_changes: Dictionary mapping file paths to (original, modified) tuples
            
        Returns:
            List of FileDiff objects
        """
        logger.info(f"Generating batch diff for {len(file_changes)} files")
        
        file_diffs = []
        
        for file_path, (original, modified) in file_changes.items():
            # Determine file status
            if not original and modified:
                file_status = 'added'
            elif original and not modified:
                file_status = 'deleted'
            else:
                file_status = 'modified'
            
            # Generate diff
            diff = self.generate_diff(original, modified, str(file_path))
            
            # Create FileDiff
            file_diff = FileDiff(
                file_path=file_path,
                original_content=original,
                modified_content=modified,
                diff=diff,
                file_status=file_status
            )
            
            file_diffs.append(file_diff)
        
        return file_diffs
    
    def show_diff_summary(self, file_diffs: List[FileDiff]) -> str:
        """
        Generate a summary view of multiple file diffs.
        
        Args:
            file_diffs: List of FileDiff objects
            
        Returns:
            Formatted summary string
        """
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"Diff Summary: {len(file_diffs)} files changed")
        lines.append("=" * 60)
        lines.append("")
        
        # Statistics
        total_additions = sum(fd.diff.additions for fd in file_diffs)
        total_deletions = sum(fd.diff.deletions for fd in file_diffs)
        
        lines.append(f"Total changes: +{total_additions} -{total_deletions}")
        lines.append("")
        
        # File list
        lines.append("Files:")
        for fd in file_diffs:
            status_symbol = {
                'added': '+',
                'deleted': '-',
                'modified': 'M'
            }.get(fd.file_status, '?')
            
            change_summary = f"+{fd.diff.additions} -{fd.diff.deletions}"
            
            line = f"  [{status_symbol}] {fd.file_path} ({change_summary})"
            
            if self.colored_output:
                if fd.file_status == 'added':
                    line = f"\033[32m{line}\033[0m"
                elif fd.file_status == 'deleted':
                    line = f"\033[31m{line}\033[0m"
                elif fd.file_status == 'modified':
                    line = f"\033[33m{line}\033[0m"
            
            lines.append(line)
        
        lines.append("")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def navigate_file_diffs(
        self,
        file_diffs: List[FileDiff],
        format: DiffFormat = DiffFormat.UNIFIED
    ) -> str:
        """
        Generate navigable output for multiple file diffs.
        
        Args:
            file_diffs: List of FileDiff objects
            format: Diff format to use
            
        Returns:
            Formatted output with file-by-file navigation markers
        """
        lines = []
        
        # Add summary
        lines.append(self.show_diff_summary(file_diffs))
        lines.append("")
        
        # Add each file diff
        for i, fd in enumerate(file_diffs, 1):
            # File header
            lines.append("")
            lines.append("=" * 60)
            lines.append(f"File {i}/{len(file_diffs)}: {fd.file_path}")
            lines.append(f"Status: {fd.file_status}")
            lines.append("=" * 60)
            lines.append("")
            
            # Show diff based on format
            if format == DiffFormat.UNIFIED:
                lines.append(self.show_unified_diff(fd.diff))
            elif format == DiffFormat.SIDE_BY_SIDE:
                lines.append(self.show_side_by_side_diff(fd.diff))
            
            lines.append("")
        
        return '\n'.join(lines)
    
    # Private helper methods
    
    def _parse_unified_diff(
        self,
        diff_lines: List[str],
        original_file: str,
        modified_file: str
    ) -> Diff:
        """Parse unified diff output into structured Diff object."""
        diff = Diff(
            original_file=original_file,
            modified_file=modified_file
        )
        
        current_hunk = None
        old_line_num = 0
        new_line_num = 0
        
        for line in diff_lines:
            # Skip file headers
            if line.startswith('---') or line.startswith('+++'):
                continue
            
            # Parse hunk header
            if line.startswith('@@'):
                if current_hunk:
                    diff.hunks.append(current_hunk)
                
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1
                    
                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        header=line
                    )
                    
                    old_line_num = old_start
                    new_line_num = new_start
                
                continue
            
            if not current_hunk:
                continue
            
            # Parse diff lines
            if line.startswith('+'):
                # Addition
                content = line[1:] if len(line) > 1 else ''
                diff_line = DiffLine(
                    line_number_old=None,
                    line_number_new=new_line_num,
                    content=content,
                    change_type=ChangeType.ADDITION
                )
                current_hunk.lines.append(diff_line)
                diff.additions += 1
                new_line_num += 1
            
            elif line.startswith('-'):
                # Deletion
                content = line[1:] if len(line) > 1 else ''
                diff_line = DiffLine(
                    line_number_old=old_line_num,
                    line_number_new=None,
                    content=content,
                    change_type=ChangeType.DELETION
                )
                current_hunk.lines.append(diff_line)
                diff.deletions += 1
                old_line_num += 1
            
            else:
                # Unchanged context line
                content = line[1:] if len(line) > 1 else line
                diff_line = DiffLine(
                    line_number_old=old_line_num,
                    line_number_new=new_line_num,
                    content=content,
                    change_type=ChangeType.UNCHANGED
                )
                current_hunk.lines.append(diff_line)
                old_line_num += 1
                new_line_num += 1
        
        # Add last hunk
        if current_hunk:
            diff.hunks.append(current_hunk)
        
        return diff
    
    def _apply_diff_to_content(self, content: str, diff: Diff) -> str:
        """Apply a diff to content and return the result."""
        lines = content.splitlines(keepends=True)
        
        # Apply each hunk
        for hunk in diff.hunks:
            # Find the starting position
            start_idx = hunk.old_start - 1
            
            # Build the new lines for this hunk
            new_lines = []
            for diff_line in hunk.lines:
                if diff_line.change_type == ChangeType.ADDITION:
                    new_lines.append(diff_line.content + '\n')
                elif diff_line.change_type == ChangeType.UNCHANGED:
                    new_lines.append(diff_line.content + '\n')
                # Skip deletions
            
            # Replace the old lines with new lines
            end_idx = start_idx + hunk.old_count
            lines[start_idx:end_idx] = new_lines
        
        return ''.join(lines)
    
    def _format_side_by_side_line(
        self,
        line_num: Optional[int],
        content: str,
        width: int,
        marker: str
    ) -> str:
        """Format a line for side-by-side display."""
        line_num_str = f"{line_num:4d}" if line_num is not None else "    "
        
        # Truncate content if too long
        if len(content) > width - 2:
            content = content[:width - 5] + "..."
        
        return f"{line_num_str} {marker} {content:<{width}}"
    
    def _colorize_unified_diff(self, diff: str) -> str:
        """Add ANSI color codes to unified diff."""
        lines = diff.split('\n')
        colored_lines = []
        
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                # File headers in bold
                colored_lines.append(f"\033[1m{line}\033[0m")
            elif line.startswith('+'):
                # Additions in green
                colored_lines.append(f"\033[32m{line}\033[0m")
            elif line.startswith('-'):
                # Deletions in red
                colored_lines.append(f"\033[31m{line}\033[0m")
            elif line.startswith('@@'):
                # Hunk headers in cyan
                colored_lines.append(f"\033[36m{line}\033[0m")
            else:
                colored_lines.append(line)
        
        return '\n'.join(colored_lines)
    
    def _validate_python(self, content: str) -> Dict[str, Any]:
        """Validate Python syntax."""
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        try:
            compile(content, '<string>', 'exec')
        except SyntaxError as e:
            result['valid'] = False
            result['errors'].append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validation error: {e}")
        
        return result
    
    def _validate_javascript(self, content: str) -> Dict[str, Any]:
        """Validate JavaScript syntax (basic checks)."""
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        # Basic bracket matching
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in content:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack.pop()] != char:
                    result['valid'] = False
                    result['errors'].append("Mismatched brackets")
                    break
        
        if stack:
            result['warnings'].append("Unclosed brackets detected")
        
        return result
    
    def _validate_json(self, content: str) -> Dict[str, Any]:
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
            result['errors'].append(f"Validation error: {e}")
        
        return result
