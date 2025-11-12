"""
Advanced configuration system with user preferences, team settings, and plugin management.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import importlib
import inspect

logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    """Configuration scope levels."""
    GLOBAL = "global"
    USER = "user"
    TEAM = "team"
    PROJECT = "project"
    SESSION = "session"


class ConfigType(Enum):
    """Configuration types."""
    CORE = "core"
    AGENT = "agent"
    WORKFLOW = "workflow"
    LEARNING = "learning"
    INTEGRATION = "integration"
    PLUGIN = "plugin"
    THEME = "theme"


@dataclass
class ConfigValue:
    """Configuration value with metadata."""
    value: Any
    type: str
    scope: ConfigScope
    description: str = ""
    default: Any = None
    validation: Optional[Callable] = None
    sensitive: bool = False
    readonly: bool = False
    deprecated: bool = False
    
    def validate(self) -> bool:
        """Validate the configuration value."""
        if self.validation:
            try:
                return self.validation(self.value)
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                return False
        return True


@dataclass
class UserPreferences:
    """User-specific preferences."""
    coding_style: str = "pep8"
    preferred_languages: List[str] = field(default_factory=lambda: ["python"])
    skill_level: str = "intermediate"
    interface_theme: str = "dark"
    auto_save: bool = True
    show_suggestions: bool = True
    suggestion_frequency: str = "normal"  # low, normal, high
    learning_enabled: bool = True
    telemetry_enabled: bool = True
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "workflow_completion": True,
        "error_alerts": True,
        "learning_updates": False,
        "performance_tips": True
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TeamConfiguration:
    """Team-specific configuration."""
    team_id: str
    team_name: str
    coding_standards: Dict[str, Any] = field(default_factory=dict)
    shared_templates: List[str] = field(default_factory=list)
    collaboration_settings: Dict[str, Any] = field(default_factory=dict)
    security_policies: Dict[str, Any] = field(default_factory=dict)
    workflow_templates: List[str] = field(default_factory=list)
    agent_permissions: Dict[str, List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamConfiguration':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PluginConfiguration:
    """Plugin configuration."""
    plugin_id: str
    name: str
    version: str
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginConfiguration':
        """Create from dictionary."""
        return cls(**data)


class AdvancedConfigurationManager:
    """Advanced configuration management system."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / ".codegenie"
        self.config_cache: Dict[str, Any] = {}
        self.watchers: Dict[str, List[Callable]] = {}
        self.validators: Dict[str, Callable] = {}
        self.plugins: Dict[str, Any] = {}
        
        # Configuration hierarchy (higher priority first)
        self.config_hierarchy = [
            ConfigScope.SESSION,
            ConfigScope.PROJECT,
            ConfigScope.TEAM,
            ConfigScope.USER,
            ConfigScope.GLOBAL
        ]
        
        self._initialize_config_structure()
        self._register_default_validators()
    
    def _initialize_config_structure(self) -> None:
        """Initialize configuration directory structure."""
        
        directories = [
            self.base_path,
            self.base_path / "global",
            self.base_path / "user",
            self.base_path / "teams",
            self.base_path / "projects",
            self.base_path / "plugins",
            self.base_path / "themes",
            self.base_path / "templates",
            self.base_path / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _register_default_validators(self) -> None:
        """Register default configuration validators."""
        
        self.validators.update({
            'models.default': lambda x: isinstance(x, str) and len(x) > 0,
            'learning_rate': lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            'max_context_length': lambda x: isinstance(x, int) and x > 0,
            'timeout': lambda x: isinstance(x, int) and x > 0,
            'skill_level': lambda x: x in ['beginner', 'intermediate', 'advanced', 'expert'],
            'interface_theme': lambda x: x in ['light', 'dark', 'auto'],
            'suggestion_frequency': lambda x: x in ['low', 'normal', 'high']
        })
    
    # Core Configuration Management
    
    def get_config(
        self,
        key: str,
        scope: Optional[ConfigScope] = None,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """Get configuration value with scope resolution."""
        
        # Check cache first
        cache_key = f"{scope.value if scope else 'auto'}:{key}"
        if cache_key in self.config_cache:
            return self.config_cache[cache_key]
        
        # Resolve value through hierarchy
        if scope:
            value = self._get_config_from_scope(key, scope, project_path, team_id)
        else:
            value = self._resolve_config_hierarchy(key, project_path, team_id)
        
        # Use default if not found
        if value is None:
            value = default
        
        # Cache the result
        self.config_cache[cache_key] = value
        
        return value
    
    def set_config(
        self,
        key: str,
        value: Any,
        scope: ConfigScope,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None,
        validate: bool = True
    ) -> None:
        """Set configuration value in specified scope."""
        
        # Validate value
        if validate and not self._validate_config_value(key, value):
            raise ValueError(f"Invalid value for configuration key '{key}': {value}")
        
        # Get config file path
        config_file = self._get_config_file_path(scope, project_path, team_id)
        
        # Load existing config
        config = self._load_config_file(config_file)
        
        # Set nested value
        self._set_nested_value(config, key, value)
        
        # Save config
        self._save_config_file(config_file, config)
        
        # Clear cache
        self._clear_cache_for_key(key)
        
        # Notify watchers
        self._notify_watchers(key, value, scope)
        
        logger.info(f"Set config {key} = {value} in scope {scope.value}")
    
    def delete_config(
        self,
        key: str,
        scope: ConfigScope,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None
    ) -> bool:
        """Delete configuration value from specified scope."""
        
        config_file = self._get_config_file_path(scope, project_path, team_id)
        config = self._load_config_file(config_file)
        
        if self._delete_nested_value(config, key):
            self._save_config_file(config_file, config)
            self._clear_cache_for_key(key)
            self._notify_watchers(key, None, scope)
            logger.info(f"Deleted config {key} from scope {scope.value}")
            return True
        
        return False
    
    def _resolve_config_hierarchy(
        self,
        key: str,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None
    ) -> Any:
        """Resolve configuration value through hierarchy."""
        
        for scope in self.config_hierarchy:
            value = self._get_config_from_scope(key, scope, project_path, team_id)
            if value is not None:
                return value
        
        return None
    
    def _get_config_from_scope(
        self,
        key: str,
        scope: ConfigScope,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None
    ) -> Any:
        """Get configuration value from specific scope."""
        
        config_file = self._get_config_file_path(scope, project_path, team_id)
        
        if not config_file.exists():
            return None
        
        config = self._load_config_file(config_file)
        return self._get_nested_value(config, key)
    
    def _get_config_file_path(
        self,
        scope: ConfigScope,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None
    ) -> Path:
        """Get configuration file path for scope."""
        
        if scope == ConfigScope.GLOBAL:
            return self.base_path / "global" / "config.yaml"
        elif scope == ConfigScope.USER:
            return self.base_path / "user" / "config.yaml"
        elif scope == ConfigScope.TEAM:
            if not team_id:
                raise ValueError("Team ID required for team scope")
            return self.base_path / "teams" / f"{team_id}.yaml"
        elif scope == ConfigScope.PROJECT:
            if not project_path:
                raise ValueError("Project path required for project scope")
            return project_path / ".codegenie" / "config.yaml"
        elif scope == ConfigScope.SESSION:
            return self.base_path / "session" / "config.yaml"
        else:
            raise ValueError(f"Unknown configuration scope: {scope}")
    
    # User Preferences Management
    
    def get_user_preferences(self, user_id: Optional[str] = None) -> UserPreferences:
        """Get user preferences."""
        
        config_file = self.base_path / "user" / "preferences.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                return UserPreferences.from_dict(data)
            except Exception as e:
                logger.error(f"Error loading user preferences: {e}")
        
        return UserPreferences()
    
    def save_user_preferences(
        self,
        preferences: UserPreferences,
        user_id: Optional[str] = None
    ) -> None:
        """Save user preferences."""
        
        config_file = self.base_path / "user" / "preferences.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(preferences.to_dict(), f, default_flow_style=False)
            
            logger.info("User preferences saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
            raise
    
    def update_user_preference(
        self,
        key: str,
        value: Any,
        user_id: Optional[str] = None
    ) -> None:
        """Update a specific user preference."""
        
        preferences = self.get_user_preferences(user_id)
        
        # Update preference using dot notation
        if hasattr(preferences, key):
            setattr(preferences, key, value)
        else:
            # Handle nested preferences
            parts = key.split('.')
            current = preferences
            for part in parts[:-1]:
                if hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return  # Invalid key path
            
            if hasattr(current, parts[-1]):
                setattr(current, parts[-1], value)
        
        self.save_user_preferences(preferences, user_id)
    
    # Team Configuration Management
    
    def get_team_configuration(self, team_id: str) -> Optional[TeamConfiguration]:
        """Get team configuration."""
        
        config_file = self.base_path / "teams" / f"{team_id}.yaml"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            return TeamConfiguration.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading team configuration: {e}")
            return None
    
    def save_team_configuration(self, team_config: TeamConfiguration) -> None:
        """Save team configuration."""
        
        config_file = self.base_path / "teams" / f"{team_config.team_id}.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(team_config.to_dict(), f, default_flow_style=False)
            
            logger.info(f"Team configuration saved for team {team_config.team_id}")
            
        except Exception as e:
            logger.error(f"Error saving team configuration: {e}")
            raise
    
    def create_team_configuration(
        self,
        team_id: str,
        team_name: str,
        **kwargs
    ) -> TeamConfiguration:
        """Create new team configuration."""
        
        team_config = TeamConfiguration(
            team_id=team_id,
            team_name=team_name,
            **kwargs
        )
        
        self.save_team_configuration(team_config)
        return team_config
    
    # Plugin Management
    
    def register_plugin(self, plugin_config: PluginConfiguration) -> None:
        """Register a plugin."""
        
        config_file = self.base_path / "plugins" / f"{plugin_config.plugin_id}.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(plugin_config.to_dict(), f, default_flow_style=False)
            
            # Load plugin if enabled
            if plugin_config.enabled:
                self._load_plugin(plugin_config)
            
            logger.info(f"Plugin {plugin_config.plugin_id} registered successfully")
            
        except Exception as e:
            logger.error(f"Error registering plugin: {e}")
            raise
    
    def get_plugin_configuration(self, plugin_id: str) -> Optional[PluginConfiguration]:
        """Get plugin configuration."""
        
        config_file = self.base_path / "plugins" / f"{plugin_id}.yaml"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            return PluginConfiguration.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading plugin configuration: {e}")
            return None
    
    def list_plugins(self, enabled_only: bool = False) -> List[PluginConfiguration]:
        """List all plugins."""
        
        plugins = []
        plugin_dir = self.base_path / "plugins"
        
        if not plugin_dir.exists():
            return plugins
        
        for config_file in plugin_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                plugin_config = PluginConfiguration.from_dict(data)
                
                if not enabled_only or plugin_config.enabled:
                    plugins.append(plugin_config)
                    
            except Exception as e:
                logger.error(f"Error loading plugin config {config_file}: {e}")
        
        return plugins
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin."""
        
        plugin_config = self.get_plugin_configuration(plugin_id)
        if not plugin_config:
            return False
        
        plugin_config.enabled = True
        
        try:
            self.register_plugin(plugin_config)
            return True
        except Exception as e:
            logger.error(f"Error enabling plugin {plugin_id}: {e}")
            return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        
        plugin_config = self.get_plugin_configuration(plugin_id)
        if not plugin_config:
            return False
        
        plugin_config.enabled = False
        
        try:
            # Unload plugin
            if plugin_id in self.plugins:
                self._unload_plugin(plugin_id)
            
            # Save configuration
            config_file = self.base_path / "plugins" / f"{plugin_id}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(plugin_config.to_dict(), f, default_flow_style=False)
            
            return True
        except Exception as e:
            logger.error(f"Error disabling plugin {plugin_id}: {e}")
            return False
    
    def _load_plugin(self, plugin_config: PluginConfiguration) -> None:
        """Load a plugin."""
        
        try:
            # This would implement actual plugin loading
            # For now, just store the configuration
            self.plugins[plugin_config.plugin_id] = plugin_config
            
            logger.info(f"Plugin {plugin_config.plugin_id} loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_config.plugin_id}: {e}")
            raise
    
    def _unload_plugin(self, plugin_id: str) -> None:
        """Unload a plugin."""
        
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            logger.info(f"Plugin {plugin_id} unloaded")
    
    # Theme Management
    
    def get_available_themes(self) -> List[str]:
        """Get list of available themes."""
        
        themes = ['light', 'dark']  # Built-in themes
        
        theme_dir = self.base_path / "themes"
        if theme_dir.exists():
            for theme_file in theme_dir.glob("*.yaml"):
                themes.append(theme_file.stem)
        
        return themes
    
    def get_theme_configuration(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Get theme configuration."""
        
        # Check for built-in themes
        if theme_name in ['light', 'dark']:
            return self._get_builtin_theme(theme_name)
        
        # Check for custom themes
        theme_file = self.base_path / "themes" / f"{theme_name}.yaml"
        if theme_file.exists():
            try:
                with open(theme_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Error loading theme {theme_name}: {e}")
        
        return None
    
    def save_theme_configuration(
        self,
        theme_name: str,
        theme_config: Dict[str, Any]
    ) -> None:
        """Save custom theme configuration."""
        
        theme_file = self.base_path / "themes" / f"{theme_name}.yaml"
        theme_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(theme_file, 'w') as f:
                yaml.dump(theme_config, f, default_flow_style=False)
            
            logger.info(f"Theme {theme_name} saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving theme {theme_name}: {e}")
            raise
    
    def _get_builtin_theme(self, theme_name: str) -> Dict[str, Any]:
        """Get built-in theme configuration."""
        
        if theme_name == 'light':
            return {
                'name': 'Light Theme',
                'colors': {
                    'primary': '#007bff',
                    'secondary': '#6c757d',
                    'success': '#28a745',
                    'warning': '#ffc107',
                    'danger': '#dc3545',
                    'background': '#ffffff',
                    'text': '#212529'
                }
            }
        elif theme_name == 'dark':
            return {
                'name': 'Dark Theme',
                'colors': {
                    'primary': '#0d6efd',
                    'secondary': '#6c757d',
                    'success': '#198754',
                    'warning': '#ffc107',
                    'danger': '#dc3545',
                    'background': '#212529',
                    'text': '#ffffff'
                }
            }
        
        return {}
    
    # Configuration Watching and Validation
    
    def watch_config(self, key: str, callback: Callable[[str, Any, ConfigScope], None]) -> None:
        """Watch for configuration changes."""
        
        if key not in self.watchers:
            self.watchers[key] = []
        
        self.watchers[key].append(callback)
    
    def unwatch_config(self, key: str, callback: Callable) -> None:
        """Stop watching configuration changes."""
        
        if key in self.watchers and callback in self.watchers[key]:
            self.watchers[key].remove(callback)
    
    def _notify_watchers(self, key: str, value: Any, scope: ConfigScope) -> None:
        """Notify configuration watchers."""
        
        if key in self.watchers:
            for callback in self.watchers[key]:
                try:
                    callback(key, value, scope)
                except Exception as e:
                    logger.error(f"Error in config watcher callback: {e}")
    
    def register_validator(self, key: str, validator: Callable[[Any], bool]) -> None:
        """Register configuration validator."""
        
        self.validators[key] = validator
    
    def _validate_config_value(self, key: str, value: Any) -> bool:
        """Validate configuration value."""
        
        if key in self.validators:
            try:
                return self.validators[key](value)
            except Exception as e:
                logger.error(f"Validation error for {key}: {e}")
                return False
        
        return True
    
    # Utility Methods
    
    def _load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration file."""
        
        if not config_file.exists():
            return {}
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix == '.json':
                    return json.load(f)
                else:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}")
            return {}
    
    def _save_config_file(self, config_file: Path, config: Dict[str, Any]) -> None:
        """Save configuration file."""
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                if config_file.suffix == '.json':
                    json.dump(config, f, indent=2)
                else:
                    yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving config file {config_file}: {e}")
            raise
    
    def _get_nested_value(self, config: Dict[str, Any], key: str) -> Any:
        """Get nested configuration value using dot notation."""
        
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _delete_nested_value(self, config: Dict[str, Any], key: str) -> bool:
        """Delete nested configuration value using dot notation."""
        
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False
        
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            return True
        
        return False
    
    def _clear_cache_for_key(self, key: str) -> None:
        """Clear cache entries for a specific key."""
        
        keys_to_remove = [cache_key for cache_key in self.config_cache.keys() if cache_key.endswith(f":{key}")]
        
        for cache_key in keys_to_remove:
            del self.config_cache[cache_key]
    
    # Import/Export and Backup
    
    def export_configuration(
        self,
        scope: ConfigScope,
        output_file: Path,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None
    ) -> None:
        """Export configuration to file."""
        
        config_file = self._get_config_file_path(scope, project_path, team_id)
        config = self._load_config_file(config_file)
        
        # Add metadata
        export_data = {
            'metadata': {
                'scope': scope.value,
                'exported_at': str(time.time()),
                'version': '1.0'
            },
            'configuration': config
        }
        
        self._save_config_file(output_file, export_data)
        logger.info(f"Configuration exported to {output_file}")
    
    def import_configuration(
        self,
        input_file: Path,
        scope: ConfigScope,
        project_path: Optional[Path] = None,
        team_id: Optional[str] = None,
        merge: bool = True
    ) -> None:
        """Import configuration from file."""
        
        import_data = self._load_config_file(input_file)
        
        if 'configuration' not in import_data:
            raise ValueError("Invalid configuration file format")
        
        config_file = self._get_config_file_path(scope, project_path, team_id)
        
        if merge and config_file.exists():
            existing_config = self._load_config_file(config_file)
            # Merge configurations (imported takes precedence)
            merged_config = {**existing_config, **import_data['configuration']}
            self._save_config_file(config_file, merged_config)
        else:
            self._save_config_file(config_file, import_data['configuration'])
        
        # Clear cache
        self.config_cache.clear()
        
        logger.info(f"Configuration imported from {input_file}")
    
    def backup_configuration(self, backup_name: Optional[str] = None) -> Path:
        """Create backup of all configurations."""
        
        import time
        
        if not backup_name:
            backup_name = f"backup_{int(time.time())}"
        
        backup_dir = self.base_path / "backups" / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup all configuration directories
        import shutil
        
        for source_dir in ['global', 'user', 'teams', 'plugins', 'themes']:
            source_path = self.base_path / source_dir
            if source_path.exists():
                dest_path = backup_dir / source_dir
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        
        logger.info(f"Configuration backup created: {backup_dir}")
        return backup_dir
    
    def restore_configuration(self, backup_name: str) -> None:
        """Restore configuration from backup."""
        
        backup_dir = self.base_path / "backups" / backup_name
        
        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")
        
        import shutil
        
        # Restore configuration directories
        for backup_subdir in backup_dir.iterdir():
            if backup_subdir.is_dir():
                dest_path = self.base_path / backup_subdir.name
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(backup_subdir, dest_path)
        
        # Clear cache
        self.config_cache.clear()
        
        logger.info(f"Configuration restored from backup: {backup_name}")
    
    def list_backups(self) -> List[str]:
        """List available configuration backups."""
        
        backup_dir = self.base_path / "backups"
        
        if not backup_dir.exists():
            return []
        
        return [backup.name for backup in backup_dir.iterdir() if backup.is_dir()]


# Configuration validation functions
def validate_model_name(value: str) -> bool:
    """Validate model name format."""
    return isinstance(value, str) and len(value) > 0 and ':' in value


def validate_learning_rate(value: Union[int, float]) -> bool:
    """Validate learning rate value."""
    return isinstance(value, (int, float)) and 0 <= value <= 1


def validate_timeout(value: int) -> bool:
    """Validate timeout value."""
    return isinstance(value, int) and value > 0


def validate_skill_level(value: str) -> bool:
    """Validate skill level."""
    return value in ['beginner', 'intermediate', 'advanced', 'expert']


def validate_theme_name(value: str) -> bool:
    """Validate theme name."""
    return isinstance(value, str) and len(value) > 0 and value.replace('_', '').replace('-', '').isalnum()


# Configuration migration utilities
class ConfigurationMigrator:
    """Handles configuration migration between versions."""
    
    def __init__(self, config_manager: AdvancedConfigurationManager):
        self.config_manager = config_manager
        self.migrations = {}
    
    def register_migration(self, from_version: str, to_version: str, migration_func: Callable) -> None:
        """Register a configuration migration."""
        
        key = f"{from_version}->{to_version}"
        self.migrations[key] = migration_func
    
    def migrate_configuration(self, from_version: str, to_version: str) -> None:
        """Migrate configuration from one version to another."""
        
        migration_key = f"{from_version}->{to_version}"
        
        if migration_key not in self.migrations:
            raise ValueError(f"No migration available from {from_version} to {to_version}")
        
        # Create backup before migration
        backup_name = f"pre_migration_{from_version}_to_{to_version}_{int(time.time())}"
        self.config_manager.backup_configuration(backup_name)
        
        try:
            # Run migration
            self.migrations[migration_key]()
            logger.info(f"Configuration migrated from {from_version} to {to_version}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            # Restore from backup
            self.config_manager.restore_configuration(backup_name)
            raise