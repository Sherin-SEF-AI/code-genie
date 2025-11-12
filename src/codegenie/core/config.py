"""
Configuration management for Claude Code Agent.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """Configuration for Ollama models."""
    
    default: str = "llama3.1:8b"
    code_generation: str = "codellama:7b"
    reasoning: str = "llama3.1:70b"
    fallback: List[str] = ["llama3.1:8b", "codellama:7b"]
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    timeout: int = Field(default=300, ge=1)  # 5 minutes


class UIConfig(BaseModel):
    """Configuration for user interface."""
    
    theme: str = "dark"
    show_reasoning: bool = True
    show_progress: bool = True
    auto_approve_safe: bool = True
    confirm_destructive: bool = True
    max_output_lines: int = Field(default=100, ge=10)
    refresh_rate: float = Field(default=0.1, ge=0.01, le=1.0)


class ExecutionConfig(BaseModel):
    """Configuration for code execution."""
    
    sandbox_mode: bool = True
    auto_backup: bool = True
    max_file_size: str = "10MB"
    allowed_commands: List[str] = [
        "git", "npm", "pip", "python", "node", "go", "cargo", "rustc",
        "gcc", "g++", "make", "cmake", "docker", "kubectl"
    ]
    blocked_commands: List[str] = [
        "rm", "del", "format", "fdisk", "mkfs", "dd", "shutdown", "reboot"
    ]
    timeout: int = Field(default=300, ge=1)  # 5 minutes


class LearningConfig(BaseModel):
    """Configuration for learning and adaptation."""
    
    save_corrections: bool = True
    adapt_style: bool = True
    remember_patterns: bool = True
    max_memory_size: str = "100MB"
    learning_rate: float = Field(default=0.1, ge=0.0, le=1.0)


class SecurityConfig(BaseModel):
    """Configuration for security features."""
    
    detect_secrets: bool = True
    mask_output: bool = True
    require_confirmation: bool = True
    allowed_file_extensions: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c",
        ".h", ".hpp", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".conf",
        ".md", ".txt", ".sql", ".html", ".css", ".scss", ".sass", ".less"
    ]
    blocked_file_extensions: List[str] = [
        ".exe", ".dll", ".so", ".dylib", ".bin", ".app", ".deb", ".rpm", ".msi"
    ]


class Config(BaseModel):
    """Main configuration for Claude Code Agent."""
    
    models: ModelConfig = Field(default_factory=ModelConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Advanced features
    autonomous_workflows: bool = True
    multi_agent_coordination: bool = True
    adaptive_learning: bool = True
    
    # Global settings
    debug: bool = False
    verbose: bool = False
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "codegenie")
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".config" / "codegenie")
    
    @field_validator('cache_dir', 'config_dir', mode='after')
    @classmethod
    def ensure_directories_exist(cls, v):
        """Ensure configuration directories exist."""
        if isinstance(v, Path):
            v.mkdir(parents=True, exist_ok=True)
        return v
    
    @classmethod
    def create_default(cls) -> "Config":
        """Create a default configuration."""
        return cls()
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file or environment."""
        
        # Try to load from specified path
        if config_path and isinstance(config_path, Path) and config_path.exists():
            return cls._load_from_file(config_path)
        
        # Try to load from project directory
        project_config = Path.cwd() / ".codegenie.yaml"
        if project_config.exists():
            return cls._load_from_file(project_config)
        
        # Try to load from global config directory
        global_config = cls().config_dir / "config.yaml"
        if global_config.exists():
            return cls._load_from_file(global_config)
        
        # Load from environment variables
        config = cls._load_from_env()
        
        # Create default config file if none exists
        if not global_config.exists():
            config.save(global_config)
        
        return config
    
    @classmethod
    def _load_from_file(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Handle environment variable substitution
            data = cls._substitute_env_vars(data)
            
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")
    
    @classmethod
    def _load_from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        config_data = {}
        
        # Map environment variables to config structure
        env_mappings = {
            "CLAUDE_CODE_MODEL": ("models", "default"),
            "CLAUDE_CODE_THEME": ("ui", "theme"),
            "CLAUDE_CODE_DEBUG": ("debug",),
            "CLAUDE_CODE_VERBOSE": ("verbose",),
            "CLAUDE_CODE_LOG_LEVEL": ("log_level",),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the correct nested location
                current = config_data
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Set the final value with type conversion
                final_key = config_path[-1]
                if final_key in ["debug", "verbose"]:
                    current[final_key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    current[final_key] = value
        
        return cls(**config_data)
    
    @classmethod
    def _substitute_env_vars(cls, data: Any) -> Any:
        """Substitute environment variables in configuration data."""
        if isinstance(data, dict):
            return {k: cls._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls._substitute_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1]
            return os.getenv(env_var, data)
        else:
            return data
    
    def save(self, config_path: Path) -> None:
        """Save configuration to file."""
        try:
            # Convert to dict and remove None values
            data = self.model_dump(exclude_none=True)
            
            # Convert Path objects to strings for YAML serialization
            def convert_paths(obj):
                if isinstance(obj, Path):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_paths(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_paths(item) for item in obj]
                return obj
            
            data = convert_paths(data)
            
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            raise ValueError(f"Failed to save configuration to {config_path}: {e}")
    
    def get_model_for_task(self, task_type: str) -> str:
        """Get the appropriate model for a specific task type."""
        model_mapping = {
            "code_generation": self.models.code_generation,
            "reasoning": self.models.reasoning,
            "debugging": self.models.reasoning,
            "planning": self.models.reasoning,
            "documentation": self.models.default,
            "testing": self.models.code_generation,
        }
        
        return model_mapping.get(task_type, self.models.default)
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to execute."""
        cmd_name = command.split()[0] if command else ""
        
        # Check blocked commands first
        if any(cmd_name.startswith(blocked) for blocked in self.execution.blocked_commands):
            return False
        
        # Check allowed commands
        if any(cmd_name.startswith(allowed) for allowed in self.execution.allowed_commands):
            return True
        
        # If no explicit allow/block, default to blocked for safety
        return False
    
    def is_file_allowed(self, file_path: Path) -> bool:
        """Check if a file extension is allowed."""
        suffix = file_path.suffix.lower()
        
        # Check blocked extensions first
        if suffix in self.security.blocked_file_extensions:
            return False
        
        # Check allowed extensions
        if suffix in self.security.allowed_file_extensions:
            return True
        
        # If no explicit allow/block, default to allowed
        return True
