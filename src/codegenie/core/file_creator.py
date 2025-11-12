"""
File Creator for intelligent file operations with diff preview and content generation.
"""

import difflib
import logging
import mimetypes
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.file_operations import FileOperations

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of file operations."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"


class OperationStatus(Enum):
    """Status of file operations."""
    PENDING = "pending"
    PREVIEWED = "previewed"
    APPROVED = "approved"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Diff:
    """Represents a diff between two file versions."""
    original: str
    modified: str
    unified_diff: str
    additions: int = 0
    deletions: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'original': self.original,
            'modified': self.modified,
            'unified_diff': self.unified_diff,
            'additions': self.additions,
            'deletions': self.deletions,
        }


@dataclass
class Change:
    """Represents a change to be made to a file."""
    line_number: int
    old_content: str
    new_content: str
    change_type: str  # 'add', 'delete', 'modify'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'line_number': self.line_number,
            'old_content': self.old_content,
            'new_content': self.new_content,
            'change_type': self.change_type,
        }


@dataclass
class FileOperation:
    """Represents a file operation with metadata."""
    operation_type: OperationType
    file_path: Path
    content: Optional[str] = None
    diff: Optional[Diff] = None
    backup_path: Optional[Path] = None
    requires_approval: bool = True
    status: OperationStatus = OperationStatus.PENDING
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_type': self.operation_type.value,
            'file_path': str(self.file_path),
            'content': self.content,
            'diff': self.diff.to_dict() if self.diff else None,
            'backup_path': str(self.backup_path) if self.backup_path else None,
            'requires_approval': self.requires_approval,
            'status': self.status.value,
            'error_message': self.error_message,
            'metadata': self.metadata,
        }


class FileCreator:
    """
    Intelligent file creator with diff preview and content generation.
    
    Provides automatic file creation, modification, and deletion with
    diff preview, approval workflows, and intelligent content generation.
    """
    
    def __init__(
        self,
        file_ops: Optional[FileOperations] = None,
        auto_backup: bool = True,
        preview_by_default: bool = True,
        model_client=None,
        colored_output: bool = True
    ):
        """
        Initialize the file creator.
        
        Args:
            file_ops: Optional FileOperations instance
            auto_backup: Whether to automatically backup files
            preview_by_default: Whether to show preview by default
            model_client: Optional AI model client for content generation
            colored_output: Whether to use colored output for diffs
        """
        self.file_ops = file_ops or FileOperations()
        self.auto_backup = auto_backup
        self.preview_by_default = preview_by_default
        self.content_generator = ContentGenerator(model_client)
        self.diff_preview = DiffPreview(colored_output)
        self.pending_operations: List[FileOperation] = []
        self.completed_operations: List[FileOperation] = []
        
        logger.info("FileCreator initialized")

    
    def create_file(
        self,
        path: Union[str, Path],
        content: str,
        preview: bool = None,
        force: bool = False
    ) -> FileOperation:
        """
        Create a new file with content.
        
        Args:
            path: Path to the file to create
            content: Content to write to the file
            preview: Whether to show preview (uses default if None)
            force: Whether to overwrite if file exists
            
        Returns:
            FileOperation with operation details
        """
        path = Path(path)
        preview = preview if preview is not None else self.preview_by_default
        
        logger.info(f"Creating file: {path}")
        
        # Check if file already exists
        if path.exists() and not force:
            logger.warning(f"File already exists: {path}")
            operation = FileOperation(
                operation_type=OperationType.CREATE,
                file_path=path,
                content=content,
                status=OperationStatus.FAILED,
                error_message="File already exists. Use force=True to overwrite.",
            )
            return operation
        
        # Create operation
        operation = FileOperation(
            operation_type=OperationType.CREATE,
            file_path=path,
            content=content,
            requires_approval=preview,
        )
        
        # Generate diff if file exists
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                operation.diff = self.generate_diff(original_content, content, str(path))
            except Exception as e:
                logger.warning(f"Could not read existing file for diff: {e}")
        
        # Add metadata
        operation.metadata = {
            'file_size': len(content),
            'file_type': self.detect_file_type(path),
            'lines': content.count('\n') + 1,
        }
        
        if preview:
            operation.status = OperationStatus.PREVIEWED
            self.pending_operations.append(operation)
            logger.info(f"File creation pending approval: {path}")
        else:
            # Execute immediately
            result = self._execute_create(operation)
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                self.completed_operations.append(operation)
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Unknown error')
        
        return operation
    
    def modify_file(
        self,
        path: Union[str, Path],
        changes: Union[str, List[Change]],
        preview: bool = None
    ) -> FileOperation:
        """
        Modify an existing file.
        
        Args:
            path: Path to the file to modify
            changes: Either new content as string or list of Change objects
            preview: Whether to show preview (uses default if None)
            
        Returns:
            FileOperation with operation details
        """
        path = Path(path)
        preview = preview if preview is not None else self.preview_by_default
        
        logger.info(f"Modifying file: {path}")
        
        # Check if file exists
        if not path.exists():
            logger.error(f"File does not exist: {path}")
            operation = FileOperation(
                operation_type=OperationType.MODIFY,
                file_path=path,
                status=OperationStatus.FAILED,
                error_message="File does not exist",
            )
            return operation
        
        # Read original content
        try:
            with open(path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            logger.error(f"Could not read file {path}: {e}")
            operation = FileOperation(
                operation_type=OperationType.MODIFY,
                file_path=path,
                status=OperationStatus.FAILED,
                error_message=f"Could not read file: {e}",
            )
            return operation
        
        # Determine new content
        if isinstance(changes, str):
            new_content = changes
        else:
            # Apply changes to original content
            new_content = self._apply_changes(original_content, changes)
        
        # Generate diff
        diff = self.generate_diff(original_content, new_content, str(path))
        
        # Create operation
        operation = FileOperation(
            operation_type=OperationType.MODIFY,
            file_path=path,
            content=new_content,
            diff=diff,
            requires_approval=preview,
        )
        
        # Add metadata
        operation.metadata = {
            'original_size': len(original_content),
            'new_size': len(new_content),
            'file_type': self.detect_file_type(path),
            'additions': diff.additions,
            'deletions': diff.deletions,
        }
        
        if preview:
            operation.status = OperationStatus.PREVIEWED
            self.pending_operations.append(operation)
            logger.info(f"File modification pending approval: {path}")
        else:
            # Execute immediately
            result = self._execute_modify(operation)
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                self.completed_operations.append(operation)
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Unknown error')
        
        return operation
    
    def delete_file(
        self,
        path: Union[str, Path],
        safe: bool = True,
        preview: bool = None
    ) -> FileOperation:
        """
        Delete a file.
        
        Args:
            path: Path to the file to delete
            safe: Whether to backup before deletion
            preview: Whether to show preview (uses default if None)
            
        Returns:
            FileOperation with operation details
        """
        path = Path(path)
        preview = preview if preview is not None else self.preview_by_default
        
        logger.info(f"Deleting file: {path}")
        
        # Check if file exists
        if not path.exists():
            logger.error(f"File does not exist: {path}")
            operation = FileOperation(
                operation_type=OperationType.DELETE,
                file_path=path,
                status=OperationStatus.FAILED,
                error_message="File does not exist",
            )
            return operation
        
        # Read content for backup/preview
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read file content: {e}")
            content = None
        
        # Create operation
        operation = FileOperation(
            operation_type=OperationType.DELETE,
            file_path=path,
            content=content,
            requires_approval=preview or safe,
        )
        
        # Add metadata
        operation.metadata = {
            'file_size': len(content) if content else 0,
            'file_type': self.detect_file_type(path),
            'safe_delete': safe,
        }
        
        if preview:
            operation.status = OperationStatus.PREVIEWED
            self.pending_operations.append(operation)
            logger.info(f"File deletion pending approval: {path}")
        else:
            # Execute immediately
            result = self._execute_delete(operation, safe)
            if result['success']:
                operation.status = OperationStatus.COMPLETED
                operation.backup_path = Path(result.get('backup_path')) if 'backup_path' in result else None
                self.completed_operations.append(operation)
            else:
                operation.status = OperationStatus.FAILED
                operation.error_message = result.get('error', 'Unknown error')
        
        return operation
    
    def create_directory_structure(
        self,
        structure: Dict[str, Any],
        base_path: Union[str, Path] = ".",
        preview: bool = None
    ) -> List[FileOperation]:
        """
        Create a directory structure from a nested dictionary.
        
        Args:
            structure: Dictionary representing directory structure
                      Keys are names, values are either:
                      - None/empty dict for directories
                      - String for file content
                      - Dict for nested structure
            base_path: Base path for the structure
            preview: Whether to show preview (uses default if None)
            
        Returns:
            List of FileOperation objects
        """
        base_path = Path(base_path)
        preview = preview if preview is not None else self.preview_by_default
        
        logger.info(f"Creating directory structure at: {base_path}")
        
        operations = []
        
        def process_structure(struct: Dict[str, Any], current_path: Path):
            """Recursively process structure."""
            for name, value in struct.items():
                item_path = current_path / name
                
                if value is None or (isinstance(value, dict) and not value):
                    # Create directory
                    if not item_path.exists():
                        item_path.mkdir(parents=True, exist_ok=True)
                        logger.debug(f"Created directory: {item_path}")
                
                elif isinstance(value, str):
                    # Create file with content
                    operation = self.create_file(item_path, value, preview=False)
                    operations.append(operation)
                
                elif isinstance(value, dict):
                    # Create directory and recurse
                    if not item_path.exists():
                        item_path.mkdir(parents=True, exist_ok=True)
                        logger.debug(f"Created directory: {item_path}")
                    process_structure(value, item_path)
        
        try:
            process_structure(structure, base_path)
            logger.info(f"Created {len(operations)} files in directory structure")
        except Exception as e:
            logger.error(f"Error creating directory structure: {e}")
        
        return operations

    
    def generate_diff(
        self,
        original: str,
        modified: str,
        filename: str = "file"
    ) -> Diff:
        """
        Generate a diff between two versions of content.
        
        Args:
            original: Original content
            modified: Modified content
            filename: Filename for diff header
            
        Returns:
            Diff object with unified diff and statistics
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        ))
        
        unified_diff = ''.join(diff_lines)
        
        # Count additions and deletions
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        
        return Diff(
            original=original,
            modified=modified,
            unified_diff=unified_diff,
            additions=additions,
            deletions=deletions,
        )
    
    def show_diff(self, diff: Diff, colored: bool = True) -> str:
        """
        Format a diff for display.
        
        Args:
            diff: Diff object to display
            colored: Whether to add color codes (for terminal)
            
        Returns:
            Formatted diff string
        """
        if not colored:
            return diff.unified_diff
        
        # Add ANSI color codes
        lines = diff.unified_diff.split('\n')
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
    
    def detect_file_type(self, path: Union[str, Path]) -> str:
        """
        Detect the type of a file based on extension.
        
        Args:
            path: Path to the file
            
        Returns:
            File type string
        """
        path = Path(path)
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        
        if mime_type:
            return mime_type
        
        # Fallback to extension-based detection
        ext = path.suffix.lower()
        
        type_map = {
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.ts': 'text/typescript',
            '.jsx': 'text/jsx',
            '.tsx': 'text/tsx',
            '.java': 'text/x-java',
            '.c': 'text/x-c',
            '.cpp': 'text/x-c++',
            '.h': 'text/x-c-header',
            '.go': 'text/x-go',
            '.rs': 'text/x-rust',
            '.rb': 'text/x-ruby',
            '.php': 'text/x-php',
            '.html': 'text/html',
            '.css': 'text/css',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.yaml': 'text/yaml',
            '.yml': 'text/yaml',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.sh': 'text/x-shellscript',
            '.bash': 'text/x-shellscript',
        }
        
        return type_map.get(ext, 'application/octet-stream')
    
    def approve_operation(self, operation: FileOperation) -> bool:
        """
        Approve a pending operation and execute it.
        
        Args:
            operation: Operation to approve
            
        Returns:
            True if successful, False otherwise
        """
        if operation not in self.pending_operations:
            logger.error("Operation not in pending list")
            return False
        
        logger.info(f"Approving operation: {operation.operation_type.value} {operation.file_path}")
        
        operation.status = OperationStatus.APPROVED
        
        # Execute based on operation type
        if operation.operation_type == OperationType.CREATE:
            result = self._execute_create(operation)
        elif operation.operation_type == OperationType.MODIFY:
            result = self._execute_modify(operation)
        elif operation.operation_type == OperationType.DELETE:
            result = self._execute_delete(operation, operation.metadata.get('safe_delete', True))
        else:
            result = {'success': False, 'error': 'Unsupported operation type'}
        
        # Update status
        if result['success']:
            operation.status = OperationStatus.COMPLETED
            if 'backup_path' in result:
                operation.backup_path = Path(result['backup_path'])
            self.completed_operations.append(operation)
        else:
            operation.status = OperationStatus.FAILED
            operation.error_message = result.get('error', 'Unknown error')
        
        # Remove from pending
        self.pending_operations.remove(operation)
        
        return result['success']
    
    def cancel_operation(self, operation: FileOperation) -> bool:
        """
        Cancel a pending operation.
        
        Args:
            operation: Operation to cancel
            
        Returns:
            True if successful, False otherwise
        """
        if operation not in self.pending_operations:
            logger.error("Operation not in pending list")
            return False
        
        logger.info(f"Cancelling operation: {operation.operation_type.value} {operation.file_path}")
        
        operation.status = OperationStatus.CANCELLED
        self.pending_operations.remove(operation)
        
        return True
    
    def approve_all_pending(self) -> Dict[str, Any]:
        """
        Approve and execute all pending operations.
        
        Returns:
            Dictionary with results
        """
        logger.info(f"Approving {len(self.pending_operations)} pending operations")
        
        results = {
            'total': len(self.pending_operations),
            'successful': 0,
            'failed': 0,
            'operations': []
        }
        
        # Process all pending operations
        pending_copy = self.pending_operations.copy()
        for operation in pending_copy:
            success = self.approve_operation(operation)
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['operations'].append({
                'operation': operation.to_dict(),
                'success': success,
            })
        
        return results
    
    def get_pending_operations(self) -> List[FileOperation]:
        """Get list of pending operations."""
        return self.pending_operations.copy()
    
    def get_completed_operations(self) -> List[FileOperation]:
        """Get list of completed operations."""
        return self.completed_operations.copy()
    
    def generate_content(
        self,
        file_type: str,
        context: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None
    ) -> str:
        """
        Generate content for a file.
        
        Args:
            file_type: Type of file to generate
            context: Context for generation
            template_name: Optional template name
            
        Returns:
            Generated content
        """
        return self.content_generator.generate_content(file_type, context, template_name)
    
    def create_file_with_generation(
        self,
        path: Union[str, Path],
        file_type: str,
        context: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None,
        preview: bool = None
    ) -> FileOperation:
        """
        Create a file with automatically generated content.
        
        Args:
            path: Path to the file
            file_type: Type of file to generate
            context: Context for generation
            template_name: Optional template name
            preview: Whether to show preview
            
        Returns:
            FileOperation with operation details
        """
        # Generate content
        content = self.generate_content(file_type, context, template_name)
        
        # Create file with generated content
        return self.create_file(path, content, preview)
    
    def add_template(self, name: str, template: str) -> None:
        """Add a custom template."""
        self.content_generator.add_template(name, template)
    
    def get_template(self, name: str) -> Optional[str]:
        """Get a template by name."""
        return self.content_generator.get_template(name)
    
    def list_templates(self) -> List[str]:
        """List available templates."""
        return self.content_generator.list_templates()
    
    def preview_operation(self, operation: FileOperation) -> str:
        """
        Generate a preview string for an operation.
        
        Args:
            operation: Operation to preview
            
        Returns:
            Formatted preview string
        """
        return self.diff_preview.preview_operation(operation)
    
    def preview_pending_operations(self) -> str:
        """
        Generate a preview for all pending operations.
        
        Returns:
            Formatted preview string
        """
        return self.diff_preview.preview_multiple_operations(self.pending_operations)
    
    def confirm_and_execute_operation(
        self,
        operation: FileOperation,
        auto_approve: bool = False
    ) -> bool:
        """
        Show preview and request confirmation before executing an operation.
        
        Args:
            operation: Operation to execute
            auto_approve: Whether to auto-approve
            
        Returns:
            True if successful, False otherwise
        """
        # Request confirmation
        approved = self.diff_preview.confirm_operation(operation, auto_approve)
        
        if not approved:
            logger.info(f"Operation cancelled by user: {operation.file_path}")
            self.cancel_operation(operation)
            return False
        
        # Execute the operation
        return self.approve_operation(operation)
    
    def confirm_and_execute_all_pending(
        self,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Show preview and request confirmation for all pending operations.
        
        Args:
            auto_approve: Whether to auto-approve all
            
        Returns:
            Dictionary with execution results
        """
        if not self.pending_operations:
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'cancelled': 0,
                'operations': []
            }
        
        # Request confirmation
        approvals = self.diff_preview.confirm_multiple_operations(
            self.pending_operations,
            auto_approve
        )
        
        results = {
            'total': len(self.pending_operations),
            'successful': 0,
            'failed': 0,
            'cancelled': 0,
            'operations': []
        }
        
        # Process operations based on approvals
        pending_copy = self.pending_operations.copy()
        for i, operation in enumerate(pending_copy):
            if approvals.get(i, False):
                success = self.approve_operation(operation)
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['operations'].append({
                    'operation': operation.to_dict(),
                    'success': success,
                })
            else:
                self.cancel_operation(operation)
                results['cancelled'] += 1
                results['operations'].append({
                    'operation': operation.to_dict(),
                    'cancelled': True,
                })
        
        return results
    
    def _execute_create(self, operation: FileOperation) -> Dict[str, Any]:
        """Execute a create operation."""
        try:
            result = self.file_ops.create_file(
                operation.file_path,
                operation.content,
                backup=self.auto_backup
            )
            return result
        except Exception as e:
            logger.error(f"Error executing create operation: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_modify(self, operation: FileOperation) -> Dict[str, Any]:
        """Execute a modify operation."""
        try:
            result = self.file_ops.modify_file(
                operation.file_path,
                operation.content,
                backup=self.auto_backup
            )
            return result
        except Exception as e:
            logger.error(f"Error executing modify operation: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_delete(self, operation: FileOperation, safe: bool) -> Dict[str, Any]:
        """Execute a delete operation."""
        try:
            result = self.file_ops.delete_file(
                operation.file_path,
                backup=safe
            )
            return result
        except Exception as e:
            logger.error(f"Error executing delete operation: {e}")
            return {'success': False, 'error': str(e)}
    
    def _apply_changes(self, original: str, changes: List[Change]) -> str:
        """
        Apply a list of changes to original content.
        
        Args:
            original: Original content
            changes: List of Change objects
            
        Returns:
            Modified content
        """
        lines = original.splitlines(keepends=True)
        
        # Sort changes by line number (descending) to avoid index issues
        sorted_changes = sorted(changes, key=lambda c: c.line_number, reverse=True)
        
        for change in sorted_changes:
            line_idx = change.line_number - 1  # Convert to 0-based index
            
            if change.change_type == 'add':
                lines.insert(line_idx, change.new_content + '\n')
            elif change.change_type == 'delete':
                if 0 <= line_idx < len(lines):
                    del lines[line_idx]
            elif change.change_type == 'modify':
                if 0 <= line_idx < len(lines):
                    lines[line_idx] = change.new_content + '\n'
        
        return ''.join(lines)



class ContentGenerator:
    """
    Generates file content based on templates and context.
    """
    
    def __init__(self, model_client=None):
        """
        Initialize content generator.
        
        Args:
            model_client: Optional AI model client for intelligent generation
        """
        self.model_client = model_client
        self.templates = self._load_default_templates()
        
        logger.info("ContentGenerator initialized")
    
    def generate_content(
        self,
        file_type: str,
        context: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None
    ) -> str:
        """
        Generate content for a file based on type and context.
        
        Args:
            file_type: Type of file (e.g., 'python', 'javascript', 'html')
            context: Context information for generation
            template_name: Optional specific template to use
            
        Returns:
            Generated content as string
        """
        context = context or {}
        
        logger.info(f"Generating content for file type: {file_type}")
        
        # Use template if specified
        if template_name and template_name in self.templates:
            return self._apply_template(template_name, context)
        
        # Generate based on file type
        if file_type in ['text/x-python', 'python', '.py']:
            return self._generate_python_content(context)
        elif file_type in ['text/javascript', 'javascript', '.js']:
            return self._generate_javascript_content(context)
        elif file_type in ['text/typescript', 'typescript', '.ts']:
            return self._generate_typescript_content(context)
        elif file_type in ['text/html', 'html', '.html']:
            return self._generate_html_content(context)
        elif file_type in ['text/css', 'css', '.css']:
            return self._generate_css_content(context)
        elif file_type in ['text/markdown', 'markdown', '.md']:
            return self._generate_markdown_content(context)
        elif file_type in ['application/json', 'json', '.json']:
            return self._generate_json_content(context)
        elif file_type in ['text/yaml', 'yaml', '.yaml', '.yml']:
            return self._generate_yaml_content(context)
        else:
            return self._generate_generic_content(context)
    
    def _generate_python_content(self, context: Dict[str, Any]) -> str:
        """Generate Python file content."""
        module_name = context.get('module_name', 'module')
        description = context.get('description', 'Python module')
        author = context.get('author', '')
        include_main = context.get('include_main', False)
        class_name = context.get('class_name')
        functions = context.get('functions', [])
        
        lines = [
            '"""',
            description,
            '"""',
            '',
        ]
        
        if author:
            lines.insert(1, f'Author: {author}')
        
        # Add imports
        imports = context.get('imports', [])
        if imports:
            for imp in imports:
                lines.append(imp)
            lines.append('')
        
        # Add class if specified
        if class_name:
            lines.extend([
                '',
                f'class {class_name}:',
                f'    """',
                f'    {class_name} class.',
                f'    """',
                f'    ',
                f'    def __init__(self):',
                f'        """Initialize {class_name}."""',
                f'        pass',
                '',
            ])
        
        # Add functions
        for func in functions:
            func_name = func.get('name', 'function')
            func_desc = func.get('description', f'{func_name} function')
            params = func.get('parameters', [])
            
            param_str = ', '.join(params) if params else ''
            
            lines.extend([
                '',
                f'def {func_name}({param_str}):',
                f'    """',
                f'    {func_desc}',
                f'    """',
                f'    pass',
                '',
            ])
        
        # Add main block if requested
        if include_main:
            lines.extend([
                '',
                'if __name__ == "__main__":',
                '    pass',
                '',
            ])
        
        return '\n'.join(lines)
    
    def _generate_javascript_content(self, context: Dict[str, Any]) -> str:
        """Generate JavaScript file content."""
        description = context.get('description', 'JavaScript module')
        author = context.get('author', '')
        use_strict = context.get('use_strict', True)
        class_name = context.get('class_name')
        functions = context.get('functions', [])
        
        lines = [
            '/**',
            f' * {description}',
        ]
        
        if author:
            lines.append(f' * @author {author}')
        
        lines.extend([
            ' */',
            '',
        ])
        
        if use_strict:
            lines.extend([
                "'use strict';",
                '',
            ])
        
        # Add imports
        imports = context.get('imports', [])
        if imports:
            for imp in imports:
                lines.append(imp)
            lines.append('')
        
        # Add class if specified
        if class_name:
            lines.extend([
                f'class {class_name} {{',
                f'  constructor() {{',
                f'    // Initialize {class_name}',
                f'  }}',
                f'}}',
                '',
            ])
        
        # Add functions
        for func in functions:
            func_name = func.get('name', 'function')
            func_desc = func.get('description', f'{func_name} function')
            params = func.get('parameters', [])
            
            param_str = ', '.join(params) if params else ''
            
            lines.extend([
                f'/**',
                f' * {func_desc}',
                f' */',
                f'function {func_name}({param_str}) {{',
                f'  // TODO: Implement',
                f'}}',
                '',
            ])
        
        # Add exports
        exports = context.get('exports', [])
        if exports:
            export_str = ', '.join(exports)
            lines.append(f'module.exports = {{ {export_str} }};')
        
        return '\n'.join(lines)
    
    def _generate_typescript_content(self, context: Dict[str, Any]) -> str:
        """Generate TypeScript file content."""
        description = context.get('description', 'TypeScript module')
        interface_name = context.get('interface_name')
        class_name = context.get('class_name')
        
        lines = [
            '/**',
            f' * {description}',
            ' */',
            '',
        ]
        
        # Add imports
        imports = context.get('imports', [])
        if imports:
            for imp in imports:
                lines.append(imp)
            lines.append('')
        
        # Add interface if specified
        if interface_name:
            properties = context.get('properties', [])
            lines.extend([
                f'interface {interface_name} {{',
            ])
            for prop in properties:
                prop_name = prop.get('name', 'property')
                prop_type = prop.get('type', 'any')
                optional = '?' if prop.get('optional', False) else ''
                lines.append(f'  {prop_name}{optional}: {prop_type};')
            lines.extend([
                '}',
                '',
            ])
        
        # Add class if specified
        if class_name:
            implements = f' implements {interface_name}' if interface_name else ''
            lines.extend([
                f'export class {class_name}{implements} {{',
                f'  constructor() {{',
                f'    // Initialize {class_name}',
                f'  }}',
                f'}}',
                '',
            ])
        
        return '\n'.join(lines)
    
    def _generate_html_content(self, context: Dict[str, Any]) -> str:
        """Generate HTML file content."""
        title = context.get('title', 'Page')
        description = context.get('description', '')
        include_css = context.get('include_css', True)
        include_js = context.get('include_js', True)
        
        lines = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '  <meta charset="UTF-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        ]
        
        if description:
            lines.append(f'  <meta name="description" content="{description}">')
        
        lines.append(f'  <title>{title}</title>')
        
        if include_css:
            lines.append('  <link rel="stylesheet" href="styles.css">')
        
        lines.extend([
            '</head>',
            '<body>',
            f'  <h1>{title}</h1>',
            '  ',
            '</body>',
        ])
        
        if include_js:
            lines.append('<script src="script.js"></script>')
        
        lines.append('</html>')
        
        return '\n'.join(lines)
    
    def _generate_css_content(self, context: Dict[str, Any]) -> str:
        """Generate CSS file content."""
        description = context.get('description', 'Stylesheet')
        
        lines = [
            '/**',
            f' * {description}',
            ' */',
            '',
            '* {',
            '  margin: 0;',
            '  padding: 0;',
            '  box-sizing: border-box;',
            '}',
            '',
            'body {',
            '  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;',
            '  line-height: 1.6;',
            '  color: #333;',
            '}',
            '',
        ]
        
        return '\n'.join(lines)
    
    def _generate_markdown_content(self, context: Dict[str, Any]) -> str:
        """Generate Markdown file content."""
        title = context.get('title', 'Document')
        description = context.get('description', '')
        sections = context.get('sections', [])
        
        lines = [
            f'# {title}',
            '',
        ]
        
        if description:
            lines.extend([
                description,
                '',
            ])
        
        for section in sections:
            section_title = section.get('title', 'Section')
            section_content = section.get('content', '')
            level = section.get('level', 2)
            
            lines.extend([
                f'{"#" * level} {section_title}',
                '',
                section_content,
                '',
            ])
        
        return '\n'.join(lines)
    
    def _generate_json_content(self, context: Dict[str, Any]) -> str:
        """Generate JSON file content."""
        import json
        
        data = context.get('data', {})
        indent = context.get('indent', 2)
        
        return json.dumps(data, indent=indent, sort_keys=False)
    
    def _generate_yaml_content(self, context: Dict[str, Any]) -> str:
        """Generate YAML file content."""
        # Simple YAML generation without external dependencies
        data = context.get('data', {})
        
        def dict_to_yaml(d: Dict, indent: int = 0) -> List[str]:
            """Convert dict to YAML lines."""
            lines = []
            for key, value in d.items():
                if isinstance(value, dict):
                    lines.append(f'{" " * indent}{key}:')
                    lines.extend(dict_to_yaml(value, indent + 2))
                elif isinstance(value, list):
                    lines.append(f'{" " * indent}{key}:')
                    for item in value:
                        if isinstance(item, dict):
                            lines.append(f'{" " * (indent + 2)}-')
                            lines.extend(dict_to_yaml(item, indent + 4))
                        else:
                            lines.append(f'{" " * (indent + 2)}- {item}')
                else:
                    lines.append(f'{" " * indent}{key}: {value}')
            return lines
        
        return '\n'.join(dict_to_yaml(data))
    
    def _generate_generic_content(self, context: Dict[str, Any]) -> str:
        """Generate generic file content."""
        description = context.get('description', 'File content')
        content = context.get('content', '')
        
        if content:
            return content
        
        return f'# {description}\n\n'
    
    def _load_default_templates(self) -> Dict[str, str]:
        """Load default file templates."""
        return {
            'python_module': '''"""
{description}
"""

def main():
    """Main function."""
    pass


if __name__ == "__main__":
    main()
''',
            'python_class': '''"""
{description}
"""


class {class_name}:
    """
    {class_name} class.
    """
    
    def __init__(self):
        """Initialize {class_name}."""
        pass
''',
            'javascript_module': '''/**
 * {description}
 */

'use strict';

module.exports = {{}};
''',
            'readme': '''# {title}

{description}

## Installation

```bash
# Installation instructions
```

## Usage

```bash
# Usage examples
```

## License

{license}
''',
        }
    
    def _apply_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Apply a template with context."""
        template = self.templates.get(template_name, '')
        
        # Simple template variable substitution
        for key, value in context.items():
            placeholder = f'{{{key}}}'
            template = template.replace(placeholder, str(value))
        
        return template
    
    def add_template(self, name: str, template: str) -> None:
        """
        Add a custom template.
        
        Args:
            name: Template name
            template: Template content with {variable} placeholders
        """
        self.templates[name] = template
        logger.info(f"Added template: {name}")
    
    def get_template(self, name: str) -> Optional[str]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List available template names."""
        return list(self.templates.keys())



class DiffPreview:
    """
    Handles diff preview and user confirmation for file operations.
    """
    
    def __init__(self, colored_output: bool = True):
        """
        Initialize diff preview.
        
        Args:
            colored_output: Whether to use colored output
        """
        self.colored_output = colored_output
        
        logger.info("DiffPreview initialized")
    
    def preview_operation(self, operation: FileOperation) -> str:
        """
        Generate a preview string for an operation.
        
        Args:
            operation: Operation to preview
            
        Returns:
            Formatted preview string
        """
        lines = []
        
        # Header
        lines.append(self._format_header(operation))
        lines.append('')
        
        # Operation details
        lines.append(f"Operation: {operation.operation_type.value.upper()}")
        lines.append(f"File: {operation.file_path}")
        
        if operation.metadata:
            lines.append('')
            lines.append("Metadata:")
            for key, value in operation.metadata.items():
                lines.append(f"  {key}: {value}")
        
        # Show diff if available
        if operation.diff:
            lines.append('')
            lines.append(self._format_section_header("Changes"))
            lines.append('')
            
            if self.colored_output:
                lines.append(self._colorize_diff(operation.diff.unified_diff))
            else:
                lines.append(operation.diff.unified_diff)
            
            lines.append('')
            lines.append(f"Summary: +{operation.diff.additions} -{operation.diff.deletions}")
        
        # Show content preview for create/delete operations
        elif operation.content and operation.operation_type in [OperationType.CREATE, OperationType.DELETE]:
            lines.append('')
            lines.append(self._format_section_header("Content Preview"))
            lines.append('')
            
            # Show first 20 lines
            content_lines = operation.content.splitlines()
            preview_lines = content_lines[:20]
            lines.extend(preview_lines)
            
            if len(content_lines) > 20:
                lines.append(f"... ({len(content_lines) - 20} more lines)")
        
        lines.append('')
        lines.append(self._format_footer())
        
        return '\n'.join(lines)
    
    def preview_multiple_operations(self, operations: List[FileOperation]) -> str:
        """
        Generate a preview for multiple operations.
        
        Args:
            operations: List of operations to preview
            
        Returns:
            Formatted preview string
        """
        lines = []
        
        lines.append(self._format_header_text(f"Preview: {len(operations)} Operations"))
        lines.append('')
        
        # Summary
        lines.append("Summary:")
        op_counts = {}
        for op in operations:
            op_type = op.operation_type.value
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
        
        for op_type, count in op_counts.items():
            lines.append(f"  {op_type}: {count}")
        
        lines.append('')
        lines.append(self._format_section_header("Operations"))
        lines.append('')
        
        # List operations
        for i, op in enumerate(operations, 1):
            lines.append(f"{i}. {op.operation_type.value.upper()}: {op.file_path}")
            if op.diff:
                lines.append(f"   Changes: +{op.diff.additions} -{op.diff.deletions}")
        
        lines.append('')
        lines.append(self._format_footer())
        
        return '\n'.join(lines)
    
    def confirm_operation(
        self,
        operation: FileOperation,
        auto_approve: bool = False
    ) -> bool:
        """
        Request confirmation for an operation.
        
        Args:
            operation: Operation to confirm
            auto_approve: Whether to auto-approve
            
        Returns:
            True if approved, False otherwise
        """
        if auto_approve:
            return True
        
        # Show preview
        preview = self.preview_operation(operation)
        print(preview)
        
        # Request confirmation
        while True:
            response = input("\nApprove this operation? [y/n/d(etails)]: ").lower().strip()
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            elif response in ['d', 'details']:
                # Show more details
                print("\nOperation Details:")
                print(f"  Type: {operation.operation_type.value}")
                print(f"  File: {operation.file_path}")
                print(f"  Status: {operation.status.value}")
                print(f"  Requires Approval: {operation.requires_approval}")
                if operation.metadata:
                    print("  Metadata:")
                    for key, value in operation.metadata.items():
                        print(f"    {key}: {value}")
            else:
                print("Invalid response. Please enter 'y', 'n', or 'd'.")
    
    def confirm_multiple_operations(
        self,
        operations: List[FileOperation],
        auto_approve: bool = False
    ) -> Dict[str, bool]:
        """
        Request confirmation for multiple operations.
        
        Args:
            operations: List of operations to confirm
            auto_approve: Whether to auto-approve all
            
        Returns:
            Dictionary mapping operation index to approval status
        """
        if auto_approve:
            return {i: True for i in range(len(operations))}
        
        # Show preview
        preview = self.preview_multiple_operations(operations)
        print(preview)
        
        # Request confirmation
        while True:
            response = input("\nApprove all operations? [y/n/s(elective)]: ").lower().strip()
            
            if response in ['y', 'yes']:
                return {i: True for i in range(len(operations))}
            elif response in ['n', 'no']:
                return {i: False for i in range(len(operations))}
            elif response in ['s', 'selective']:
                # Selective approval
                approvals = {}
                for i, op in enumerate(operations):
                    print(f"\n--- Operation {i+1}/{len(operations)} ---")
                    approved = self.confirm_operation(op, auto_approve=False)
                    approvals[i] = approved
                return approvals
            else:
                print("Invalid response. Please enter 'y', 'n', or 's'.")
    
    def _format_header(self, operation: FileOperation) -> str:
        """Format operation header."""
        return self._format_header_text(f"{operation.operation_type.value.upper()} Operation")
    
    def _format_header_text(self, text: str) -> str:
        """Format header text."""
        if self.colored_output:
            return f"\033[1m{'=' * 60}\033[0m\n\033[1m{text}\033[0m\n\033[1m{'=' * 60}\033[0m"
        return f"{'=' * 60}\n{text}\n{'=' * 60}"
    
    def _format_section_header(self, text: str) -> str:
        """Format section header."""
        if self.colored_output:
            return f"\033[1m{text}\033[0m\n{'-' * len(text)}"
        return f"{text}\n{'-' * len(text)}"
    
    def _format_footer(self) -> str:
        """Format footer."""
        if self.colored_output:
            return f"\033[1m{'=' * 60}\033[0m"
        return '=' * 60
    
    def _colorize_diff(self, diff: str) -> str:
        """Add color codes to diff."""
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
