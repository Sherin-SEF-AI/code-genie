"""
Shell Integration for bash, zsh, and fish shells.

This module provides shell-specific integrations including:
- Environment variable access and management
- Working directory awareness
- Shell command aliasing
- Shell-specific features and optimizations
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class ShellType(Enum):
    """Supported shell types."""
    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    SH = "sh"
    UNKNOWN = "unknown"


@dataclass
class ShellConfig:
    """Shell configuration."""
    shell_type: ShellType
    config_file: Path
    rc_file: Path
    profile_file: Optional[Path]
    aliases_file: Optional[Path]
    functions_file: Optional[Path]


@dataclass
class ShellEnvironment:
    """Shell environment information."""
    shell_type: ShellType
    shell_path: Path
    working_directory: Path
    environment_variables: Dict[str, str]
    aliases: Dict[str, str]
    functions: Dict[str, str]
    path_dirs: List[Path]



class BaseShellIntegration(ABC):
    """Base class for shell integrations."""
    
    def __init__(self, shell_type: ShellType):
        """
        Initialize shell integration.
        
        Args:
            shell_type: Type of shell
        """
        self.shell_type = shell_type
        self.config = self._get_shell_config()
    
    @abstractmethod
    def _get_shell_config(self) -> ShellConfig:
        """Get shell-specific configuration."""
        pass
    
    @abstractmethod
    def get_alias_syntax(self, name: str, command: str) -> str:
        """
        Get shell-specific alias syntax.
        
        Args:
            name: Alias name
            command: Command to alias
            
        Returns:
            Shell-specific alias definition
        """
        pass
    
    @abstractmethod
    def get_function_syntax(self, name: str, body: str) -> str:
        """
        Get shell-specific function syntax.
        
        Args:
            name: Function name
            body: Function body
            
        Returns:
            Shell-specific function definition
        """
        pass
    
    def get_environment(self) -> ShellEnvironment:
        """
        Get current shell environment.
        
        Returns:
            ShellEnvironment with current state
        """
        return ShellEnvironment(
            shell_type=self.shell_type,
            shell_path=Path(os.getenv('SHELL', '/bin/sh')),
            working_directory=Path.cwd(),
            environment_variables=dict(os.environ),
            aliases=self._get_aliases(),
            functions=self._get_functions(),
            path_dirs=self._get_path_dirs()
        )
    
    def _get_aliases(self) -> Dict[str, str]:
        """Get current shell aliases."""
        try:
            result = subprocess.run(
                ['alias'],
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            aliases = {}
            for line in result.stdout.splitlines():
                if '=' in line:
                    # Parse alias definition
                    parts = line.split('=', 1)
                    name = parts[0].replace('alias', '').strip()
                    value = parts[1].strip().strip("'\"")
                    aliases[name] = value
            
            return aliases
        except Exception:
            return {}
    
    def _get_functions(self) -> Dict[str, str]:
        """Get current shell functions."""
        # This is shell-specific and would need to be implemented per shell
        return {}
    
    def _get_path_dirs(self) -> List[Path]:
        """Get directories in PATH."""
        path = os.getenv('PATH', '')
        return [Path(d) for d in path.split(':') if d]
    
    def set_environment_variable(self, name: str, value: str) -> bool:
        """
        Set environment variable.
        
        Args:
            name: Variable name
            value: Variable value
            
        Returns:
            True if successful
        """
        try:
            os.environ[name] = value
            return True
        except Exception:
            return False
    
    def get_environment_variable(self, name: str) -> Optional[str]:
        """
        Get environment variable.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value or None
        """
        return os.getenv(name)
    
    def add_alias(self, name: str, command: str) -> bool:
        """
        Add alias to shell configuration.
        
        Args:
            name: Alias name
            command: Command to alias
            
        Returns:
            True if successful
        """
        try:
            alias_def = self.get_alias_syntax(name, command)
            
            # Append to rc file
            if self.config.rc_file.exists():
                with open(self.config.rc_file, 'a') as f:
                    f.write(f"\n# Added by CodeGenie\n{alias_def}\n")
                return True
            
            return False
        except Exception:
            return False
    
    def add_function(self, name: str, body: str) -> bool:
        """
        Add function to shell configuration.
        
        Args:
            name: Function name
            body: Function body
            
        Returns:
            True if successful
        """
        try:
            func_def = self.get_function_syntax(name, body)
            
            # Append to rc file or functions file
            target_file = self.config.functions_file or self.config.rc_file
            
            if target_file and target_file.exists():
                with open(target_file, 'a') as f:
                    f.write(f"\n# Added by CodeGenie\n{func_def}\n")
                return True
            
            return False
        except Exception:
            return False


class BashIntegration(BaseShellIntegration):
    """Bash shell integration."""
    
    def __init__(self):
        """Initialize Bash integration."""
        super().__init__(ShellType.BASH)
    
    def _get_shell_config(self) -> ShellConfig:
        """Get Bash configuration."""
        home = Path.home()
        return ShellConfig(
            shell_type=ShellType.BASH,
            config_file=home / '.bashrc',
            rc_file=home / '.bashrc',
            profile_file=home / '.bash_profile',
            aliases_file=home / '.bash_aliases',
            functions_file=None
        )
    
    def get_alias_syntax(self, name: str, command: str) -> str:
        """Get Bash alias syntax."""
        return f"alias {name}='{command}'"
    
    def get_function_syntax(self, name: str, body: str) -> str:
        """Get Bash function syntax."""
        return f"""{name}() {{
    {body}
}}"""
    
    def source_file(self, file_path: Path) -> bool:
        """
        Source a file in Bash.
        
        Args:
            file_path: File to source
            
        Returns:
            True if successful
        """
        try:
            subprocess.run(
                ['bash', '-c', f'source {file_path}'],
                check=True,
                timeout=5
            )
            return True
        except Exception:
            return False


class ZshIntegration(BaseShellIntegration):
    """Zsh shell integration."""
    
    def __init__(self):
        """Initialize Zsh integration."""
        super().__init__(ShellType.ZSH)
    
    def _get_shell_config(self) -> ShellConfig:
        """Get Zsh configuration."""
        home = Path.home()
        return ShellConfig(
            shell_type=ShellType.ZSH,
            config_file=home / '.zshrc',
            rc_file=home / '.zshrc',
            profile_file=home / '.zprofile',
            aliases_file=None,
            functions_file=None
        )
    
    def get_alias_syntax(self, name: str, command: str) -> str:
        """Get Zsh alias syntax."""
        return f"alias {name}='{command}'"
    
    def get_function_syntax(self, name: str, body: str) -> str:
        """Get Zsh function syntax."""
        return f"""{name}() {{
    {body}
}}"""
    
    def enable_oh_my_zsh_plugin(self, plugin: str) -> bool:
        """
        Enable Oh My Zsh plugin.
        
        Args:
            plugin: Plugin name
            
        Returns:
            True if successful
        """
        try:
            zshrc = self.config.rc_file
            if not zshrc.exists():
                return False
            
            content = zshrc.read_text()
            
            # Find plugins line
            import re
            match = re.search(r'plugins=\((.*?)\)', content, re.DOTALL)
            if match:
                current_plugins = match.group(1).strip().split()
                if plugin not in current_plugins:
                    current_plugins.append(plugin)
                    new_plugins = ' '.join(current_plugins)
                    new_content = content.replace(match.group(0), f'plugins=({new_plugins})')
                    zshrc.write_text(new_content)
                    return True
            
            return False
        except Exception:
            return False


class FishIntegration(BaseShellIntegration):
    """Fish shell integration."""
    
    def __init__(self):
        """Initialize Fish integration."""
        super().__init__(ShellType.FISH)
    
    def _get_shell_config(self) -> ShellConfig:
        """Get Fish configuration."""
        home = Path.home()
        config_dir = home / '.config' / 'fish'
        return ShellConfig(
            shell_type=ShellType.FISH,
            config_file=config_dir / 'config.fish',
            rc_file=config_dir / 'config.fish',
            profile_file=None,
            aliases_file=config_dir / 'functions',
            functions_file=config_dir / 'functions'
        )
    
    def get_alias_syntax(self, name: str, command: str) -> str:
        """Get Fish alias syntax."""
        return f"alias {name} '{command}'"
    
    def get_function_syntax(self, name: str, body: str) -> str:
        """Get Fish function syntax."""
        return f"""function {name}
    {body}
end"""
    
    def add_function(self, name: str, body: str) -> bool:
        """
        Add function to Fish configuration.
        
        Fish stores functions in separate files.
        
        Args:
            name: Function name
            body: Function body
            
        Returns:
            True if successful
        """
        try:
            func_def = self.get_function_syntax(name, body)
            
            # Create functions directory if it doesn't exist
            if self.config.functions_file:
                self.config.functions_file.mkdir(parents=True, exist_ok=True)
                
                # Write function to its own file
                func_file = self.config.functions_file / f"{name}.fish"
                func_file.write_text(f"# Added by CodeGenie\n{func_def}\n")
                return True
            
            return False
        except Exception:
            return False



class ShellIntegrationManager:
    """
    Manages shell integrations across different shell types.
    
    Provides unified interface for:
    - Environment variable access
    - Working directory awareness
    - Shell command aliasing
    - Shell-specific features
    """
    
    def __init__(self, shell_type: Optional[ShellType] = None):
        """
        Initialize shell integration manager.
        
        Args:
            shell_type: Optional shell type (auto-detected if not provided)
        """
        self.shell_type = shell_type or self._detect_shell()
        self.integration = self._create_integration()
    
    def _detect_shell(self) -> ShellType:
        """
        Detect current shell type.
        
        Returns:
            Detected ShellType
        """
        shell = os.getenv('SHELL', '')
        
        if 'bash' in shell:
            return ShellType.BASH
        elif 'zsh' in shell:
            return ShellType.ZSH
        elif 'fish' in shell:
            return ShellType.FISH
        elif 'sh' in shell:
            return ShellType.SH
        else:
            return ShellType.UNKNOWN
    
    def _create_integration(self) -> BaseShellIntegration:
        """
        Create shell-specific integration.
        
        Returns:
            Shell integration instance
        """
        if self.shell_type == ShellType.BASH:
            return BashIntegration()
        elif self.shell_type == ShellType.ZSH:
            return ZshIntegration()
        elif self.shell_type == ShellType.FISH:
            return FishIntegration()
        else:
            # Default to Bash for unknown shells
            return BashIntegration()
    
    def get_environment(self) -> ShellEnvironment:
        """
        Get current shell environment.
        
        Returns:
            ShellEnvironment with current state
        """
        return self.integration.get_environment()
    
    def get_environment_variable(self, name: str) -> Optional[str]:
        """
        Get environment variable value.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value or None
        """
        return self.integration.get_environment_variable(name)
    
    def set_environment_variable(self, name: str, value: str) -> bool:
        """
        Set environment variable.
        
        Args:
            name: Variable name
            value: Variable value
            
        Returns:
            True if successful
        """
        return self.integration.set_environment_variable(name, value)
    
    def get_working_directory(self) -> Path:
        """
        Get current working directory.
        
        Returns:
            Current working directory path
        """
        return Path.cwd()
    
    def change_directory(self, path: Path) -> bool:
        """
        Change working directory.
        
        Args:
            path: New directory path
            
        Returns:
            True if successful
        """
        try:
            os.chdir(path)
            return True
        except Exception:
            return False
    
    def add_alias(self, name: str, command: str) -> bool:
        """
        Add command alias.
        
        Args:
            name: Alias name
            command: Command to alias
            
        Returns:
            True if successful
        """
        return self.integration.add_alias(name, command)
    
    def add_function(self, name: str, body: str) -> bool:
        """
        Add shell function.
        
        Args:
            name: Function name
            body: Function body
            
        Returns:
            True if successful
        """
        return self.integration.add_function(name, body)
    
    def get_path_dirs(self) -> List[Path]:
        """
        Get directories in PATH.
        
        Returns:
            List of PATH directories
        """
        return self.integration._get_path_dirs()
    
    def add_to_path(self, directory: Path) -> bool:
        """
        Add directory to PATH.
        
        Args:
            directory: Directory to add
            
        Returns:
            True if successful
        """
        try:
            current_path = os.getenv('PATH', '')
            dir_str = str(directory)
            
            if dir_str not in current_path:
                new_path = f"{dir_str}:{current_path}"
                os.environ['PATH'] = new_path
                return True
            
            return True
        except Exception:
            return False
    
    def get_shell_info(self) -> Dict[str, Any]:
        """
        Get shell information.
        
        Returns:
            Dictionary with shell details
        """
        env = self.get_environment()
        
        return {
            'shell_type': self.shell_type.value,
            'shell_path': str(env.shell_path),
            'working_directory': str(env.working_directory),
            'config_file': str(self.integration.config.config_file),
            'rc_file': str(self.integration.config.rc_file),
            'num_aliases': len(env.aliases),
            'num_functions': len(env.functions),
            'path_dirs': len(env.path_dirs)
        }
    
    def create_codegenie_alias(self) -> bool:
        """
        Create convenient alias for CodeGenie.
        
        Returns:
            True if successful
        """
        # Create alias for launching CodeGenie terminal
        return self.add_alias('cg', 'python -m codegenie.integrations.terminal_integration')
    
    def create_codegenie_functions(self) -> bool:
        """
        Create helpful CodeGenie functions.
        
        Returns:
            True if successful
        """
        success = True
        
        # Function to quickly analyze a file
        analyze_func = """
    if [ -z "$1" ]; then
        echo "Usage: cg-analyze <file>"
        return 1
    fi
    python -m codegenie.cli analyze "$1"
"""
        success &= self.add_function('cg-analyze', analyze_func)
        
        # Function to generate code
        generate_func = """
    if [ -z "$1" ]; then
        echo "Usage: cg-generate <description>"
        return 1
    fi
    python -m codegenie.cli generate "$@"
"""
        success &= self.add_function('cg-generate', generate_func)
        
        # Function to run tests
        test_func = """
    python -m codegenie.cli test "$@"
"""
        success &= self.add_function('cg-test', test_func)
        
        return success
    
    def setup_codegenie_integration(self) -> Dict[str, bool]:
        """
        Set up complete CodeGenie shell integration.
        
        Returns:
            Dictionary with setup results
        """
        results = {
            'alias_created': self.create_codegenie_alias(),
            'functions_created': self.create_codegenie_functions(),
        }
        
        # Add CodeGenie to PATH if not already there
        try:
            import codegenie
            codegenie_path = Path(codegenie.__file__).parent.parent
            results['path_updated'] = self.add_to_path(codegenie_path)
        except Exception:
            results['path_updated'] = False
        
        return results
    
    def get_shell_config_path(self) -> Path:
        """
        Get path to shell configuration file.
        
        Returns:
            Path to shell config file
        """
        return self.integration.config.rc_file
    
    def backup_shell_config(self) -> Optional[Path]:
        """
        Create backup of shell configuration.
        
        Returns:
            Path to backup file or None
        """
        try:
            config_file = self.integration.config.rc_file
            if config_file.exists():
                backup_file = config_file.with_suffix(f'{config_file.suffix}.backup')
                import shutil
                shutil.copy2(config_file, backup_file)
                return backup_file
            return None
        except Exception:
            return None
