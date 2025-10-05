"""
Safe file operations for Claude Code Agent.
"""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class FileOperations:
    """Safe file operations with backup and rollback capabilities."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path(tempfile.gettempdir()) / "claude-code-backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.operation_log: List[Dict[str, Any]] = []
    
    def create_file(
        self,
        file_path: Union[str, Path],
        content: str,
        backup: bool = True,
    ) -> Dict[str, Any]:
        """Create a new file with content."""
        
        file_path = Path(file_path)
        
        try:
            # Check if file already exists
            if file_path.exists():
                if backup:
                    self._backup_file(file_path)
                else:
                    return {"success": False, "error": "File already exists and backup is disabled"}
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Log operation
            operation = {
                "type": "create_file",
                "file_path": str(file_path),
                "content": content,
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Created file: {file_path}")
            return {"success": True, "file_path": str(file_path)}
            
        except Exception as e:
            logger.error(f"Error creating file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def modify_file(
        self,
        file_path: Union[str, Path],
        content: str,
        backup: bool = True,
    ) -> Dict[str, Any]:
        """Modify an existing file with new content."""
        
        file_path = Path(file_path)
        
        try:
            if not file_path.exists():
                return {"success": False, "error": "File does not exist"}
            
            # Backup original content
            if backup:
                self._backup_file(file_path)
            
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Log operation
            operation = {
                "type": "modify_file",
                "file_path": str(file_path),
                "original_content": original_content,
                "new_content": content,
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Modified file: {file_path}")
            return {"success": True, "file_path": str(file_path)}
            
        except Exception as e:
            logger.error(f"Error modifying file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def append_to_file(
        self,
        file_path: Union[str, Path],
        content: str,
        backup: bool = True,
    ) -> Dict[str, Any]:
        """Append content to an existing file."""
        
        file_path = Path(file_path)
        
        try:
            if not file_path.exists():
                return {"success": False, "error": "File does not exist"}
            
            # Backup original content
            if backup:
                self._backup_file(file_path)
            
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Append new content
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            # Log operation
            operation = {
                "type": "append_to_file",
                "file_path": str(file_path),
                "original_content": original_content,
                "appended_content": content,
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Appended to file: {file_path}")
            return {"success": True, "file_path": str(file_path)}
            
        except Exception as e:
            logger.error(f"Error appending to file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_file(
        self,
        file_path: Union[str, Path],
        backup: bool = True,
    ) -> Dict[str, Any]:
        """Delete a file with optional backup."""
        
        file_path = Path(file_path)
        
        try:
            if not file_path.exists():
                return {"success": False, "error": "File does not exist"}
            
            # Backup file before deletion
            if backup:
                self._backup_file(file_path)
            
            # Read content for logging
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Delete file
            file_path.unlink()
            
            # Log operation
            operation = {
                "type": "delete_file",
                "file_path": str(file_path),
                "content": content,
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Deleted file: {file_path}")
            return {"success": True, "file_path": str(file_path)}
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def move_file(
        self,
        source_path: Union[str, Path],
        destination_path: Union[str, Path],
        backup: bool = True,
    ) -> Dict[str, Any]:
        """Move a file to a new location."""
        
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        
        try:
            if not source_path.exists():
                return {"success": False, "error": "Source file does not exist"}
            
            if destination_path.exists():
                return {"success": False, "error": "Destination file already exists"}
            
            # Backup source file
            if backup:
                self._backup_file(source_path)
            
            # Ensure destination directory exists
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source_path), str(destination_path))
            
            # Log operation
            operation = {
                "type": "move_file",
                "source_path": str(source_path),
                "destination_path": str(destination_path),
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Moved file from {source_path} to {destination_path}")
            return {"success": True, "source_path": str(source_path), "destination_path": str(destination_path)}
            
        except Exception as e:
            logger.error(f"Error moving file from {source_path} to {destination_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def copy_file(
        self,
        source_path: Union[str, Path],
        destination_path: Union[str, Path],
        backup: bool = True,
    ) -> Dict[str, Any]:
        """Copy a file to a new location."""
        
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        
        try:
            if not source_path.exists():
                return {"success": False, "error": "Source file does not exist"}
            
            if destination_path.exists() and backup:
                self._backup_file(destination_path)
            
            # Ensure destination directory exists
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(str(source_path), str(destination_path))
            
            # Log operation
            operation = {
                "type": "copy_file",
                "source_path": str(source_path),
                "destination_path": str(destination_path),
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Copied file from {source_path} to {destination_path}")
            return {"success": True, "source_path": str(source_path), "destination_path": str(destination_path)}
            
        except Exception as e:
            logger.error(f"Error copying file from {source_path} to {destination_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def create_directory(
        self,
        dir_path: Union[str, Path],
        parents: bool = True,
    ) -> Dict[str, Any]:
        """Create a directory."""
        
        dir_path = Path(dir_path)
        
        try:
            if dir_path.exists():
                return {"success": False, "error": "Directory already exists"}
            
            dir_path.mkdir(parents=parents, exist_ok=False)
            
            # Log operation
            operation = {
                "type": "create_directory",
                "dir_path": str(dir_path),
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Created directory: {dir_path}")
            return {"success": True, "dir_path": str(dir_path)}
            
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_directory(
        self,
        dir_path: Union[str, Path],
        recursive: bool = False,
        backup: bool = True,
    ) -> Dict[str, Any]:
        """Delete a directory."""
        
        dir_path = Path(dir_path)
        
        try:
            if not dir_path.exists():
                return {"success": False, "error": "Directory does not exist"}
            
            if not dir_path.is_dir():
                return {"success": False, "error": "Path is not a directory"}
            
            # Backup directory if requested
            if backup:
                self._backup_directory(dir_path)
            
            # Delete directory
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()
            
            # Log operation
            operation = {
                "type": "delete_directory",
                "dir_path": str(dir_path),
                "recursive": recursive,
                "timestamp": self._get_timestamp(),
                "success": True,
            }
            self.operation_log.append(operation)
            
            logger.info(f"Deleted directory: {dir_path}")
            return {"success": True, "dir_path": str(dir_path)}
            
        except Exception as e:
            logger.error(f"Error deleting directory {dir_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _backup_file(self, file_path: Path) -> Path:
        """Create a backup of a file."""
        
        import time
        
        timestamp = int(time.time())
        backup_name = f"{file_path.name}.backup.{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy file to backup location
        shutil.copy2(file_path, backup_path)
        
        logger.debug(f"Created backup: {backup_path}")
        return backup_path
    
    def _backup_directory(self, dir_path: Path) -> Path:
        """Create a backup of a directory."""
        
        import time
        
        timestamp = int(time.time())
        backup_name = f"{dir_path.name}.backup.{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy directory to backup location
        shutil.copytree(dir_path, backup_path)
        
        logger.debug(f"Created directory backup: {backup_path}")
        return backup_path
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def rollback_operation(self, operation_index: int) -> Dict[str, Any]:
        """Rollback a specific operation."""
        
        if operation_index >= len(self.operation_log):
            return {"success": False, "error": "Invalid operation index"}
        
        operation = self.operation_log[operation_index]
        
        try:
            if operation["type"] == "create_file":
                # Delete the created file
                file_path = Path(operation["file_path"])
                if file_path.exists():
                    file_path.unlink()
            
            elif operation["type"] == "modify_file":
                # Restore original content
                file_path = Path(operation["file_path"])
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(operation["original_content"])
            
            elif operation["type"] == "append_to_file":
                # Remove appended content
                file_path = Path(operation["file_path"])
                original_content = operation["original_content"]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
            
            elif operation["type"] == "delete_file":
                # Restore deleted file
                file_path = Path(operation["file_path"])
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(operation["content"])
            
            elif operation["type"] == "move_file":
                # Move file back
                source_path = Path(operation["destination_path"])
                destination_path = Path(operation["source_path"])
                shutil.move(str(source_path), str(destination_path))
            
            elif operation["type"] == "copy_file":
                # Delete copied file
                destination_path = Path(operation["destination_path"])
                if destination_path.exists():
                    destination_path.unlink()
            
            elif operation["type"] == "create_directory":
                # Delete created directory
                dir_path = Path(operation["dir_path"])
                if dir_path.exists():
                    dir_path.rmdir()
            
            elif operation["type"] == "delete_directory":
                # Restore deleted directory (this is complex and may not be fully possible)
                return {"success": False, "error": "Directory restoration not fully supported"}
            
            # Mark operation as rolled back
            operation["rolled_back"] = True
            operation["rollback_timestamp"] = self._get_timestamp()
            
            logger.info(f"Rolled back operation: {operation['type']}")
            return {"success": True, "operation": operation}
            
        except Exception as e:
            logger.error(f"Error rolling back operation: {e}")
            return {"success": False, "error": str(e)}
    
    def get_operation_log(self) -> List[Dict[str, Any]]:
        """Get the operation log."""
        return self.operation_log.copy()
    
    def clear_operation_log(self) -> None:
        """Clear the operation log."""
        self.operation_log.clear()
        logger.info("Cleared operation log")
    
    def get_backup_files(self) -> List[Path]:
        """Get list of backup files."""
        if not self.backup_dir.exists():
            return []
        
        return list(self.backup_dir.glob("*.backup.*"))
    
    def cleanup_old_backups(self, max_age_days: int = 7) -> int:
        """Clean up old backup files."""
        
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        cleaned_count = 0
        
        for backup_file in self.get_backup_files():
            try:
                file_age = current_time - backup_file.stat().st_mtime
                if file_age > max_age_seconds:
                    backup_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Error cleaning up backup {backup_file}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old backup files")
        
        return cleaned_count
