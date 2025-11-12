"""
Unit tests for File Creator.

Tests file creation, modification, deletion, diff generation,
and content generation capabilities.
"""

import pytest
import tempfile
from pathlib import Path

from src.codegenie.core.file_creator import (
    FileCreator, FileOperation, OperationType, OperationStatus,
    Diff, Change
)
from src.codegenie.utils.file_operations import FileOperations


class TestFileCreator:
    """Test suite for File Creator."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def file_creator(self):
        """Create a file creator instance."""
        return FileCreator(preview_by_default=False)
    
    @pytest.fixture
    def file_creator_with_preview(self):
        """Create a file creator with preview enabled."""
        return FileCreator(preview_by_default=True)
    
    def test_initialization(self, file_creator):
        """Test file creator initialization."""
        assert file_creator is not None
        assert file_creator.auto_backup is True
        assert file_creator.preview_by_default is False
        assert len(file_creator.pending_operations) == 0
    
    def test_create_file_new(self, file_creator, temp_dir):
        """Test creating a new file."""
        file_path = temp_dir / "test.txt"
        content = "Hello, World!"
        
        operation = file_creator.create_file(file_path, content)
        
        assert isinstance(operation, FileOperation)
        assert operation.operation_type == OperationType.CREATE
        assert operation.file_path == file_path
        assert operation.content == content
        assert operation.status == OperationStatus.COMPLETED
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_create_file_existing_without_force(self, file_creator, temp_dir):
        """Test creating a file that already exists without force."""
        file_path = temp_dir / "existing.txt"
        file_path.write_text("Original content")
        
        operation = file_creator.create_file(file_path, "New content")
        
        assert operation.status == OperationStatus.FAILED
        assert "already exists" in operation.error_message.lower()
        assert file_path.read_text() == "Original content"
    
    def test_create_file_existing_with_force(self, file_creator, temp_dir):
        """Test creating a file that already exists with force."""
        file_path = temp_dir / "existing.txt"
        file_path.write_text("Original content")
        
        operation = file_creator.create_file(file_path, "New content", force=True)
        
        assert operation.status == OperationStatus.COMPLETED
        assert file_path.read_text() == "New content"
    
    def test_create_file_with_preview(self, file_creator_with_preview, temp_dir):
        """Test creating a file with preview enabled."""
        file_path = temp_dir / "test.txt"
        content = "Test content"
        
        operation = file_creator_with_preview.create_file(file_path, content)
        
        assert operation.status == OperationStatus.PREVIEWED
        assert operation in file_creator_with_preview.pending_operations
        assert not file_path.exists()
    
    def test_modify_file_success(self, file_creator, temp_dir):
        """Test modifying an existing file."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Original content")
        
        new_content = "Modified content"
        operation = file_creator.modify_file(file_path, new_content)
        
        assert operation.status == OperationStatus.COMPLETED
        assert operation.diff is not None
        assert file_path.read_text() == new_content
    
    def test_modify_file_nonexistent(self, file_creator, temp_dir):
        """Test modifying a file that doesn't exist."""
        file_path = temp_dir / "nonexistent.txt"
        
        operation = file_creator.modify_file(file_path, "Content")
        
        assert operation.status == OperationStatus.FAILED
        assert "does not exist" in operation.error_message.lower()
    
    def test_delete_file_success(self, file_creator, temp_dir):
        """Test deleting a file."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Content to delete")
        
        operation = file_creator.delete_file(file_path, safe=False)
        
        assert operation.status == OperationStatus.COMPLETED
        assert not file_path.exists()
    
    def test_delete_file_nonexistent(self, file_creator, temp_dir):
        """Test deleting a file that doesn't exist."""
        file_path = temp_dir / "nonexistent.txt"
        
        operation = file_creator.delete_file(file_path)
        
        assert operation.status == OperationStatus.FAILED
        assert "does not exist" in operation.error_message.lower()
    
    def test_generate_diff(self, file_creator):
        """Test diff generation."""
        original = "Line 1\nLine 2\nLine 3\n"
        modified = "Line 1\nLine 2 modified\nLine 3\nLine 4\n"
        
        diff = file_creator.generate_diff(original, modified, "test.txt")
        
        assert isinstance(diff, Diff)
        assert diff.additions > 0
        assert diff.deletions > 0
        assert "Line 2 modified" in diff.unified_diff
    
    def test_show_diff_plain(self, file_creator):
        """Test showing diff without colors."""
        diff = Diff(
            original="old",
            modified="new",
            unified_diff="--- a/test\n+++ b/test\n-old\n+new",
            additions=1,
            deletions=1
        )
        
        output = file_creator.show_diff(diff, colored=False)
        
        assert "old" in output
        assert "new" in output
    
    def test_detect_file_type(self, file_creator):
        """Test file type detection."""
        assert "python" in file_creator.detect_file_type(Path("test.py")).lower()
        assert "javascript" in file_creator.detect_file_type(Path("test.js")).lower()
        assert "json" in file_creator.detect_file_type(Path("test.json")).lower()
    
    def test_create_directory_structure(self, file_creator, temp_dir):
        """Test creating directory structure."""
        structure = {
            'src': {
                'main.py': 'print("Hello")',
                'utils.py': 'def helper(): pass'
            },
            'tests': {
                'test_main.py': 'def test_main(): pass'
            },
            'README.md': '# Project'
        }
        
        operations = file_creator.create_directory_structure(structure, temp_dir)
        
        assert len(operations) == 4
        assert (temp_dir / 'src' / 'main.py').exists()
        assert (temp_dir / 'tests' / 'test_main.py').exists()
        assert (temp_dir / 'README.md').exists()
    
    def test_approve_operation(self, file_creator_with_preview, temp_dir):
        """Test approving a pending operation."""
        file_path = temp_dir / "test.txt"
        operation = file_creator_with_preview.create_file(file_path, "Content")
        
        assert operation.status == OperationStatus.PREVIEWED
        
        success = file_creator_with_preview.approve_operation(operation)
        
        assert success
        assert operation.status == OperationStatus.COMPLETED
        assert file_path.exists()
    
    def test_cancel_operation(self, file_creator_with_preview, temp_dir):
        """Test cancelling a pending operation."""
        file_path = temp_dir / "test.txt"
        operation = file_creator_with_preview.create_file(file_path, "Content")
        
        success = file_creator_with_preview.cancel_operation(operation)
        
        assert success
        assert operation.status == OperationStatus.CANCELLED
        assert not file_path.exists()
    
    def test_approve_all_pending(self, file_creator_with_preview, temp_dir):
        """Test approving all pending operations."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file_creator_with_preview.create_file(file1, "Content 1")
        file_creator_with_preview.create_file(file2, "Content 2")
        
        assert len(file_creator_with_preview.pending_operations) == 2
        
        results = file_creator_with_preview.approve_all_pending()
        
        assert results['successful'] == 2
        assert file1.exists()
        assert file2.exists()
    
    def test_get_pending_operations(self, file_creator_with_preview, temp_dir):
        """Test getting pending operations."""
        file_path = temp_dir / "test.txt"
        operation = file_creator_with_preview.create_file(file_path, "Content")
        
        pending = file_creator_with_preview.get_pending_operations()
        
        assert len(pending) == 1
        assert pending[0].file_path == file_path
    
    def test_get_completed_operations(self, file_creator, temp_dir):
        """Test getting completed operations."""
        file_path = temp_dir / "test.txt"
        file_creator.create_file(file_path, "Content")
        
        completed = file_creator.get_completed_operations()
        
        assert len(completed) == 1
        assert completed[0].status == OperationStatus.COMPLETED
    
    def test_operation_to_dict(self):
        """Test FileOperation serialization."""
        operation = FileOperation(
            operation_type=OperationType.CREATE,
            file_path=Path("test.txt"),
            content="Test content",
            status=OperationStatus.COMPLETED
        )
        
        op_dict = operation.to_dict()
        
        assert op_dict['operation_type'] == "create"
        assert op_dict['file_path'] == "test.txt"
        assert op_dict['status'] == "completed"
    
    def test_diff_to_dict(self):
        """Test Diff serialization."""
        diff = Diff(
            original="old",
            modified="new",
            unified_diff="diff content",
            additions=1,
            deletions=1
        )
        
        diff_dict = diff.to_dict()
        
        assert diff_dict['additions'] == 1
        assert diff_dict['deletions'] == 1
    
    def test_change_to_dict(self):
        """Test Change serialization."""
        change = Change(
            line_number=5,
            old_content="old line",
            new_content="new line",
            change_type="modify"
        )
        
        change_dict = change.to_dict()
        
        assert change_dict['line_number'] == 5
        assert change_dict['change_type'] == "modify"
