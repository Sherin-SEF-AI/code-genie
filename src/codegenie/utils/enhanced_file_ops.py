"""
Enhanced file operations with safety, validation, and recovery capabilities.
"""

import hashlib
import logging
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FileOperation(BaseModel):
    """A file operation with metadata and safety checks."""
    
    operation_type: str  # "create", "modify", "delete", "move", "copy"
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    content: Optional[str] = None
    backup_path: Optional[str] = None
    checksum: Optional[str] = None
    timestamp: float
    user_id: Optional[str] = None
    operation_id: str


class FileValidationResult(BaseModel):
    """Result of file validation."""
    
    is_valid: bool
    file_path: str
    file_type: str
    size: int
    checksum: str
    permissions: str
    last_modified: float
    issues: List[str] = []
    warnings: List[str] = []


class EnhancedFileOperations:
    """Enhanced file operations with safety, validation, and recovery."""
    
    def __init__(self, config):
        self.config = config
        self.operation_history: List[FileOperation] = []
        self.backup_dir = Path(tempfile.mkdtemp(prefix="claude-code-backups-"))
        self.validation_rules = self._initialize_validation_rules()
        self.safety_checks = self._initialize_safety_checks()
        
        # Create backup directory structure
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        (self.backup_dir / "files").mkdir(exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
    
    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize file validation rules."""
        
        return {
            "python": {
                "extensions": [".py", ".pyi"],
                "max_size": 10 * 1024 * 1024,  # 10MB
                "check_syntax": True,
                "check_imports": True,
                "allowed_imports": ["os", "sys", "pathlib", "json", "yaml", "requests"],
                "blocked_imports": ["subprocess", "os.system", "eval", "exec"],
            },
            "javascript": {
                "extensions": [".js", ".jsx", ".ts", ".tsx"],
                "max_size": 5 * 1024 * 1024,  # 5MB
                "check_syntax": True,
                "check_imports": True,
                "allowed_imports": ["fs", "path", "util", "crypto"],
                "blocked_imports": ["child_process", "eval", "Function"],
            },
            "config": {
                "extensions": [".json", ".yaml", ".yml", ".toml", ".ini"],
                "max_size": 1 * 1024 * 1024,  # 1MB
                "check_syntax": True,
                "check_imports": False,
            },
            "documentation": {
                "extensions": [".md", ".rst", ".txt"],
                "max_size": 2 * 1024 * 1024,  # 2MB
                "check_syntax": False,
                "check_imports": False,
            },
            "binary": {
                "extensions": [".exe", ".dll", ".so", ".dylib", ".bin"],
                "max_size": 100 * 1024 * 1024,  # 100MB
                "check_syntax": False,
                "check_imports": False,
                "blocked": True,  # Binary files are blocked by default
            }
        }
    
    def _initialize_safety_checks(self) -> Dict[str, List[str]]:
        """Initialize safety check patterns."""
        
        return {
            "dangerous_patterns": [
                r"rm\s+-rf", r"del\s+/[sq]", r"format\s+[c-z]:",
                r"fdisk\s+/dev/", r"mkfs\s+/dev/", r"dd\s+if=.*of=/dev/",
                r">\s*/dev/", r">>\s*/dev/", r"curl\s+.*\|\s*sh",
                r"wget\s+.*\|\s*sh", r"python\s+-c\s+.*exec",
                r"eval\s+", r"exec\s+", r"system\s+", r"shell_exec\s+"
            ],
            "sensitive_paths": [
                "/etc/", "/root/", "/home/", "/usr/bin/", "/usr/sbin/",
                "/bin/", "/sbin/", "/var/", "/opt/", "/boot/"
            ],
            "dangerous_extensions": [
                ".exe", ".dll", ".so", ".dylib", ".bin", ".app", ".deb", ".rpm", ".msi"
            ],
            "sensitive_keywords": [
                "password", "secret", "key", "token", "credential", "auth",
                "private", "confidential", "api_key", "access_token"
            ]
        }
    
    def validate_file(self, file_path: Union[str, Path]) -> FileValidationResult:
        """Validate a file for safety and compliance."""
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            return FileValidationResult(
                is_valid=False,
                file_path=str(file_path),
                file_type="unknown",
                size=0,
                checksum="",
                permissions="",
                last_modified=0,
                issues=["File does not exist"],
            )
        
        try:
            # Get file information
            stat = file_path.stat()
            file_type = self._determine_file_type(file_path)
            checksum = self._calculate_checksum(file_path)
            
            result = FileValidationResult(
                is_valid=True,
                file_path=str(file_path),
                file_type=file_type,
                size=stat.st_size,
                checksum=checksum,
                permissions=oct(stat.st_mode)[-3:],
                last_modified=stat.st_mtime,
            )
            
            # Run validation checks
            self._check_file_size(result)
            self._check_file_type(result)
            self._check_dangerous_content(result)
            self._check_sensitive_paths(result)
            self._check_syntax(result)
            self._check_imports(result)
            
            return result
            
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                file_path=str(file_path),
                file_type="unknown",
                size=0,
                checksum="",
                permissions="",
                last_modified=0,
                issues=[f"Validation error: {str(e)}"],
            )
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension and content."""
        
        suffix = file_path.suffix.lower()
        
        # Check extension-based types
        for file_type, rules in self.validation_rules.items():
            if suffix in rules.get("extensions", []):
                return file_type
        
        # Check content-based types
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Read first 1KB
                
                if content.startswith("#!/"):
                    return "script"
                elif content.startswith("<?xml"):
                    return "xml"
                elif content.startswith("<!DOCTYPE") or content.startswith("<html"):
                    return "html"
                elif "import " in content or "from " in content:
                    return "python"
                elif "require(" in content or "import " in content:
                    return "javascript"
                elif "{" in content and "}" in content:
                    return "json"
                elif "---" in content:
                    return "yaml"
        
        except Exception:
            pass
        
        return "unknown"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _check_file_size(self, result: FileValidationResult) -> None:
        """Check file size against limits."""
        
        file_type = result.file_type
        if file_type in self.validation_rules:
            max_size = self.validation_rules[file_type].get("max_size", 0)
            if max_size > 0 and result.size > max_size:
                result.issues.append(f"File size {result.size} exceeds limit {max_size}")
                result.is_valid = False
    
    def _check_file_type(self, result: FileValidationResult) -> None:
        """Check if file type is allowed."""
        
        file_type = result.file_type
        if file_type in self.validation_rules:
            if self.validation_rules[file_type].get("blocked", False):
                result.issues.append(f"File type {file_type} is blocked")
                result.is_valid = False
    
    def _check_dangerous_content(self, result: FileValidationResult) -> None:
        """Check for dangerous content patterns."""
        
        try:
            with open(result.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for dangerous patterns
            for pattern in self.safety_checks["dangerous_patterns"]:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    result.issues.append(f"Dangerous pattern detected: {pattern}")
                    result.is_valid = False
            
            # Check for sensitive keywords
            for keyword in self.safety_checks["sensitive_keywords"]:
                if keyword.lower() in content.lower():
                    result.warnings.append(f"Potentially sensitive content: {keyword}")
        
        except Exception:
            pass
    
    def _check_sensitive_paths(self, result: FileValidationResult) -> None:
        """Check if file is in a sensitive path."""
        
        file_path = Path(result.file_path)
        
        for sensitive_path in self.safety_checks["sensitive_paths"]:
            try:
                file_path.resolve().relative_to(Path(sensitive_path).resolve())
                result.issues.append(f"File in sensitive path: {sensitive_path}")
                result.is_valid = False
                break
            except ValueError:
                continue
    
    def _check_syntax(self, result: FileValidationResult) -> None:
        """Check file syntax if applicable."""
        
        file_type = result.file_type
        
        if file_type in self.validation_rules:
            rules = self.validation_rules[file_type]
            if rules.get("check_syntax", False):
                try:
                    if file_type == "python":
                        self._check_python_syntax(result)
                    elif file_type == "javascript":
                        self._check_javascript_syntax(result)
                    elif file_type == "config":
                        self._check_config_syntax(result)
                except Exception as e:
                    result.issues.append(f"Syntax check failed: {str(e)}")
                    result.is_valid = False
    
    def _check_python_syntax(self, result: FileValidationResult) -> None:
        """Check Python syntax."""
        
        try:
            import ast
            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            result.issues.append(f"Python syntax error: {str(e)}")
            result.is_valid = False
    
    def _check_javascript_syntax(self, result: FileValidationResult) -> None:
        """Check JavaScript syntax."""
        
        try:
            import json
            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Simple check - in a real implementation, you'd use a proper JS parser
            if content.count('{') != content.count('}'):
                result.issues.append("JavaScript syntax error: Unmatched braces")
                result.is_valid = False
        except Exception as e:
            result.issues.append(f"JavaScript syntax check failed: {str(e)}")
            result.is_valid = False
    
    def _check_config_syntax(self, result: FileValidationResult) -> None:
        """Check configuration file syntax."""
        
        try:
            if result.file_path.endswith('.json'):
                import json
                with open(result.file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            elif result.file_path.endswith(('.yaml', '.yml')):
                import yaml
                with open(result.file_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
        except Exception as e:
            result.issues.append(f"Config syntax error: {str(e)}")
            result.is_valid = False
    
    def _check_imports(self, result: FileValidationResult) -> None:
        """Check imports for safety."""
        
        file_type = result.file_type
        
        if file_type in self.validation_rules:
            rules = self.validation_rules[file_type]
            if rules.get("check_imports", False):
                try:
                    with open(result.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for blocked imports
                    blocked_imports = rules.get("blocked_imports", [])
                    for blocked_import in blocked_imports:
                        if blocked_import in content:
                            result.issues.append(f"Blocked import: {blocked_import}")
                            result.is_valid = False
                    
                    # Check for allowed imports (if specified)
                    allowed_imports = rules.get("allowed_imports", [])
                    if allowed_imports:
                        import re
                        import_pattern = r"(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
                        imports = re.findall(import_pattern, content)
                        
                        for import_name in imports:
                            if import_name not in allowed_imports:
                                result.warnings.append(f"Unusual import: {import_name}")
                
                except Exception as e:
                    result.issues.append(f"Import check failed: {str(e)}")
                    result.is_valid = False
    
    def safe_create_file(
        self,
        file_path: Union[str, Path],
        content: str,
        backup: bool = True,
        validate: bool = True,
    ) -> Tuple[bool, str, Optional[FileValidationResult]]:
        """Safely create a file with validation and backup."""
        
        file_path = Path(file_path)
        
        try:
            # Validate content before creating file
            if validate:
                # Create temporary file for validation
                temp_file = self.backup_dir / "temp" / f"validation_{file_path.name}"
                temp_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                validation_result = self.validate_file(temp_file)
                
                if not validation_result.is_valid:
                    temp_file.unlink()  # Clean up temp file
                    return False, f"Validation failed: {', '.join(validation_result.issues)}", validation_result
                
                # Clean up temp file
                temp_file.unlink()
            else:
                validation_result = None
            
            # Create backup if file exists
            backup_path = None
            if file_path.exists() and backup:
                backup_path = self._create_backup(file_path)
                if not backup_path:
                    return False, "Failed to create backup", validation_result
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Record operation
            operation = FileOperation(
                operation_type="create",
                target_path=str(file_path),
                content=content,
                backup_path=str(backup_path) if backup and file_path.exists() else None,
                checksum=self._calculate_checksum(file_path),
                timestamp=time.time(),
                operation_id=f"create_{int(time.time())}",
            )
            self.operation_history.append(operation)
            
            logger.info(f"Successfully created file: {file_path}")
            return True, "File created successfully", validation_result
            
        except Exception as e:
            logger.error(f"Failed to create file {file_path}: {e}")
            return False, str(e), None
    
    def safe_modify_file(
        self,
        file_path: Union[str, Path],
        content: str,
        backup: bool = True,
        validate: bool = True,
    ) -> Tuple[bool, str, Optional[FileValidationResult]]:
        """Safely modify a file with validation and backup."""
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, "File does not exist", None
        
        try:
            # Create backup
            backup_path = None
            if backup:
                backup_path = self._create_backup(file_path)
                if not backup_path:
                    return False, "Failed to create backup", None
            
            # Validate new content
            if validate:
                # Create temporary file for validation
                temp_file = self.backup_dir / "temp" / f"validation_{file_path.name}"
                temp_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                validation_result = self.validate_file(temp_file)
                
                if not validation_result.is_valid:
                    temp_file.unlink()  # Clean up temp file
                    return False, f"Validation failed: {', '.join(validation_result.issues)}", validation_result
                
                # Clean up temp file
                temp_file.unlink()
            else:
                validation_result = None
            
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Modify the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Record operation
            operation = FileOperation(
                operation_type="modify",
                target_path=str(file_path),
                content=content,
                backup_path=str(backup_path) if backup else None,
                checksum=self._calculate_checksum(file_path),
                timestamp=time.time(),
                operation_id=f"modify_{int(time.time())}",
            )
            self.operation_history.append(operation)
            
            logger.info(f"Successfully modified file: {file_path}")
            return True, "File modified successfully", validation_result
            
        except Exception as e:
            logger.error(f"Failed to modify file {file_path}: {e}")
            return False, str(e), None
    
    def safe_delete_file(
        self,
        file_path: Union[str, Path],
        backup: bool = True,
    ) -> Tuple[bool, str]:
        """Safely delete a file with backup."""
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, "File does not exist"
        
        try:
            # Create backup
            backup_path = None
            if backup:
                backup_path = self._create_backup(file_path)
                if not backup_path:
                    return False, "Failed to create backup"
            
            # Read content for operation record
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Delete the file
            file_path.unlink()
            
            # Record operation
            operation = FileOperation(
                operation_type="delete",
                target_path=str(file_path),
                content=content,
                backup_path=str(backup_path) if backup else None,
                checksum="",
                timestamp=time.time(),
                operation_id=f"delete_{int(time.time())}",
            )
            self.operation_history.append(operation)
            
            logger.info(f"Successfully deleted file: {file_path}")
            return True, "File deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False, str(e)
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a file."""
        
        try:
            timestamp = int(time.time())
            backup_name = f"{file_path.name}.backup.{timestamp}"
            backup_path = self.backup_dir / "files" / backup_name
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to backup location
            shutil.copy2(file_path, backup_path)
            
            # Save metadata
            metadata = {
                "original_path": str(file_path),
                "backup_path": str(backup_path),
                "timestamp": timestamp,
                "checksum": self._calculate_checksum(file_path),
                "size": file_path.stat().st_size,
            }
            
            metadata_file = self.backup_dir / "metadata" / f"{backup_name}.json"
            import json
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def restore_from_backup(self, backup_path: Union[str, Path], target_path: Optional[Union[str, Path]] = None) -> bool:
        """Restore a file from backup."""
        
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            logger.error(f"Backup file does not exist: {backup_path}")
            return False
        
        try:
            # Read metadata
            metadata_file = self.backup_dir / "metadata" / f"{backup_path.name}.json"
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                original_path = Path(metadata["original_path"])
                if target_path is None:
                    target_path = original_path
                else:
                    target_path = Path(target_path)
                
                # Restore the file
                shutil.copy2(backup_path, target_path)
                
                logger.info(f"Restored file from backup: {backup_path} -> {target_path}")
                return True
            else:
                logger.error(f"Metadata file not found: {metadata_file}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore from backup {backup_path}: {e}")
            return False
    
    def get_operation_history(self) -> List[FileOperation]:
        """Get file operation history."""
        return self.operation_history.copy()
    
    def get_backup_files(self) -> List[Path]:
        """Get list of backup files."""
        backup_dir = self.backup_dir / "files"
        if backup_dir.exists():
            return list(backup_dir.glob("*.backup.*"))
        return []
    
    def cleanup_old_backups(self, max_age_days: int = 7) -> int:
        """Clean up old backup files."""
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        cleaned_count = 0
        
        for backup_file in self.get_backup_files():
            try:
                file_age = current_time - backup_file.stat().st_mtime
                if file_age > max_age_seconds:
                    backup_file.unlink()
                    
                    # Also remove metadata file
                    metadata_file = self.backup_dir / "metadata" / f"{backup_file.name}.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Error cleaning up backup {backup_file}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old backup files")
        
        return cleaned_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get file operations statistics."""
        
        if not self.operation_history:
            return {"message": "No operations yet"}
        
        # Count operations by type
        operation_counts = {}
        for operation in self.operation_history:
            op_type = operation.operation_type
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        # Count backup files
        backup_count = len(self.get_backup_files())
        
        return {
            "total_operations": len(self.operation_history),
            "operation_counts": operation_counts,
            "backup_files": backup_count,
            "backup_directory": str(self.backup_dir),
        }
    
    def cleanup(self) -> None:
        """Clean up temporary resources."""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            logger.info("Cleaned up file operations resources")
        except Exception as e:
            logger.warning(f"Failed to cleanup file operations: {e}")
