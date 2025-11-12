"""
Plugin and extension system for CodeGenie.
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    enabled: bool = True


class Plugin(ABC):
    """Base class for CodeGenie plugins."""
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass
    
    def register_hooks(self) -> Dict[str, Callable]:
        """Register plugin hooks."""
        return {}
    
    def register_commands(self) -> Dict[str, Callable]:
        """Register plugin commands."""
        return {}


class PluginManager:
    """Manages plugins and extensions."""
    
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.commands: Dict[str, Callable] = {}
    
    async def load_plugins(self) -> None:
        """Load all plugins from plugins directory."""
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return
        
        for plugin_path in self.plugins_dir.glob("*.py"):
            if plugin_path.stem.startswith("_"):
                continue
            
            try:
                await self._load_plugin(plugin_path)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_path}: {e}")
    
    async def _load_plugin(self, plugin_path: Path) -> None:
        """Load a single plugin."""
        
        module_name = plugin_path.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin class
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                plugin = obj()
                metadata = plugin.get_metadata()
                
                if metadata.enabled:
                    await plugin.initialize({})
                    self.plugins[metadata.name] = plugin
                    
                    # Register hooks
                    for hook_name, hook_func in plugin.register_hooks().items():
                        self.hooks.setdefault(hook_name, []).append(hook_func)
                    
                    # Register commands
                    for cmd_name, cmd_func in plugin.register_commands().items():
                        self.commands[cmd_name] = cmd_func
                    
                    logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
    
    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all hooks for a given hook name."""
        
        results = []
        
        for hook_func in self.hooks.get(hook_name, []):
            try:
                result = await hook_func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing hook {hook_name}: {e}")
        
        return results
    
    async def execute_command(self, command_name: str, *args, **kwargs) -> Any:
        """Execute a plugin command."""
        
        if command_name not in self.commands:
            raise ValueError(f"Unknown command: {command_name}")
        
        return await self.commands[command_name](*args, **kwargs)
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all loaded plugins."""
        return [plugin.get_metadata() for plugin in self.plugins.values()]
    
    async def shutdown_all(self) -> None:
        """Shutdown all plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin: {e}")
