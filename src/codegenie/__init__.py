"""
CodeGenie - Local AI Coding Agent

A powerful local AI coding agent that rivals Claude Code, built with Ollama
for complete privacy and offline operation.
"""

__version__ = "0.1.0"
__author__ = "Sherin Joseph Roy"
__email__ = "sherin.joseph2217@gmail.com"

from .core.agent import CodeGenieAgent
from .core.config import Config
from .core.session import Session

__all__ = [
    "CodeGenieAgent",
    "Config", 
    "Session",
]
