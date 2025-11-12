"""
Theme and customization system for CodeGenie UI.
"""

from typing import Dict, Any
from dataclasses import dataclass
from rich.theme import Theme as RichTheme


@dataclass
class UITheme:
    """UI theme configuration."""
    
    name: str
    primary_color: str
    secondary_color: str
    success_color: str
    warning_color: str
    error_color: str
    info_color: str
    background_color: str
    text_color: str
    border_style: str
    
    def to_rich_theme(self) -> RichTheme:
        """Convert to Rich theme."""
        return RichTheme({
            "primary": self.primary_color,
            "secondary": self.secondary_color,
            "success": self.success_color,
            "warning": self.warning_color,
            "error": self.error_color,
            "info": self.info_color,
            "background": self.background_color,
            "text": self.text_color
        })


class ThemeManager:
    """Manages UI themes."""
    
    def __init__(self):
        self.themes = {
            "dark": self._get_dark_theme(),
            "light": self._get_light_theme(),
            "monokai": self._get_monokai_theme(),
            "solarized": self._get_solarized_theme(),
            "dracula": self._get_dracula_theme()
        }
        self.current_theme = "dark"
    
    def _get_dark_theme(self) -> UITheme:
        """Get dark theme."""
        return UITheme(
            name="dark",
            primary_color="blue",
            secondary_color="cyan",
            success_color="green",
            warning_color="yellow",
            error_color="red",
            info_color="blue",
            background_color="black",
            text_color="white",
            border_style="blue"
        )
    
    def _get_light_theme(self) -> UITheme:
        """Get light theme."""
        return UITheme(
            name="light",
            primary_color="blue",
            secondary_color="cyan",
            success_color="green",
            warning_color="yellow",
            error_color="red",
            info_color="blue",
            background_color="white",
            text_color="black",
            border_style="blue"
        )
    
    def _get_monokai_theme(self) -> UITheme:
        """Get Monokai theme."""
        return UITheme(
            name="monokai",
            primary_color="#66D9EF",
            secondary_color="#A6E22E",
            success_color="#A6E22E",
            warning_color="#E6DB74",
            error_color="#F92672",
            info_color="#66D9EF",
            background_color="#272822",
            text_color="#F8F8F2",
            border_style="#66D9EF"
        )
    
    def _get_solarized_theme(self) -> UITheme:
        """Get Solarized theme."""
        return UITheme(
            name="solarized",
            primary_color="#268BD2",
            secondary_color="#2AA198",
            success_color="#859900",
            warning_color="#B58900",
            error_color="#DC322F",
            info_color="#268BD2",
            background_color="#002B36",
            text_color="#839496",
            border_style="#268BD2"
        )
    
    def _get_dracula_theme(self) -> UITheme:
        """Get Dracula theme."""
        return UITheme(
            name="dracula",
            primary_color="#BD93F9",
            secondary_color="#8BE9FD",
            success_color="#50FA7B",
            warning_color="#F1FA8C",
            error_color="#FF5555",
            info_color="#8BE9FD",
            background_color="#282A36",
            text_color="#F8F8F2",
            border_style="#BD93F9"
        )
    
    def get_theme(self, name: str) -> UITheme:
        """Get theme by name."""
        return self.themes.get(name, self.themes["dark"])
    
    def set_theme(self, name: str) -> None:
        """Set current theme."""
        if name in self.themes:
            self.current_theme = name
    
    def get_current_theme(self) -> UITheme:
        """Get current theme."""
        return self.themes[self.current_theme]
    
    def list_themes(self) -> list:
        """List available themes."""
        return list(self.themes.keys())
    
    def add_custom_theme(self, theme: UITheme) -> None:
        """Add a custom theme."""
        self.themes[theme.name] = theme
