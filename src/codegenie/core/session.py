"""
Session management for maintaining context across interactions.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .config import Config
from .memory import Memory

logger = logging.getLogger(__name__)


class ProjectContext(BaseModel):
    """Context information about the current project."""
    
    project_path: Path
    project_type: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    file_count: int = 0
    project_size: str = "small"  # small, medium, large
    git_repo: bool = False
    has_tests: bool = False
    has_docs: bool = False
    last_analyzed: Optional[float] = None


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    
    timestamp: float
    user_input: str
    agent_response: str
    reasoning_trace: Optional[Dict[str, Any]] = None
    actions_taken: List[Dict[str, Any]] = []
    errors_encountered: List[str] = []
    success: bool = True


class Session(BaseModel):
    """Session state for the agent."""
    
    session_id: str
    start_time: float
    project_context: ProjectContext
    conversation_history: List[ConversationTurn] = []
    current_goal: Optional[str] = None
    active_plan: Optional[Dict[str, Any]] = None
    context_variables: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True


class SessionManager:
    """Manages agent sessions and context."""
    
    def __init__(self, project_path: Path, config: Config):
        self.project_path = project_path
        self.config = config
        self.session: Optional[Session] = None
        self.memory = Memory(config, config.cache_dir)
        self.session_file = config.cache_dir / "current_session.json"
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self) -> None:
        """Initialize or load existing session."""
        
        # Try to load existing session
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert project_path back to Path object
                data['project_context']['project_path'] = Path(data['project_context']['project_path'])
                
                self.session = Session(**data)
                logger.info(f"Loaded existing session: {self.session.session_id}")
                
            except Exception as e:
                logger.warning(f"Failed to load session: {e}, creating new session")
                self._create_new_session()
        else:
            self._create_new_session()
    
    def _create_new_session(self) -> None:
        """Create a new session."""
        
        session_id = f"session_{int(time.time())}"
        
        # Analyze project context
        project_context = self._analyze_project_context()
        
        self.session = Session(
            session_id=session_id,
            start_time=time.time(),
            project_context=project_context,
        )
        
        logger.info(f"Created new session: {session_id}")
        self._save_session()
    
    def _analyze_project_context(self) -> ProjectContext:
        """Analyze the project to understand its context."""
        
        logger.info("Analyzing project context...")
        
        # Basic project info
        project_context = ProjectContext(project_path=self.project_path)
        
        # Count files and analyze structure
        file_count = 0
        languages = set()
        frameworks = set()
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                file_count += 1
                
                # Detect language from extension
                suffix = file_path.suffix.lower()
                if suffix in ['.py']:
                    languages.add('python')
                elif suffix in ['.js', '.jsx']:
                    languages.add('javascript')
                elif suffix in ['.ts', '.tsx']:
                    languages.add('typescript')
                elif suffix in ['.go']:
                    languages.add('go')
                elif suffix in ['.rs']:
                    languages.add('rust')
                elif suffix in ['.java']:
                    languages.add('java')
                elif suffix in ['.cpp', '.c', '.h', '.hpp']:
                    languages.add('cpp')
        
        project_context.file_count = file_count
        project_context.languages = list(languages)
        
        # Detect project type and frameworks
        project_context.project_type = self._detect_project_type()
        project_context.frameworks = self._detect_frameworks()
        
        # Check for git repository
        project_context.git_repo = (self.project_path / '.git').exists()
        
        # Check for tests and docs
        project_context.has_tests = self._has_test_directory()
        project_context.has_docs = self._has_documentation()
        
        # Determine project size
        if file_count > 100:
            project_context.project_size = "large"
        elif file_count > 20:
            project_context.project_size = "medium"
        else:
            project_context.project_size = "small"
        
        project_context.last_analyzed = time.time()
        
        logger.info(f"Project analysis complete: {project_context.project_type} project with {len(languages)} languages")
        return project_context
    
    def _detect_project_type(self) -> str:
        """Detect the type of project."""
        
        # Check for common project indicators
        if (self.project_path / 'package.json').exists():
            return "nodejs"
        elif (self.project_path / 'requirements.txt').exists() or (self.project_path / 'pyproject.toml').exists():
            return "python"
        elif (self.project_path / 'go.mod').exists():
            return "go"
        elif (self.project_path / 'Cargo.toml').exists():
            return "rust"
        elif (self.project_path / 'pom.xml').exists():
            return "java"
        elif (self.project_path / 'CMakeLists.txt').exists():
            return "cpp"
        elif (self.project_path / 'Dockerfile').exists():
            return "docker"
        elif (self.project_path / 'docker-compose.yml').exists():
            return "docker-compose"
        else:
            return "unknown"
    
    def _detect_frameworks(self) -> List[str]:
        """Detect frameworks used in the project."""
        
        frameworks = []
        
        # Check package.json for Node.js frameworks
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                dependencies = data.get('dependencies', {})
                dev_dependencies = data.get('devDependencies', {})
                all_deps = {**dependencies, **dev_dependencies}
                
                # Check for common frameworks
                if 'react' in all_deps:
                    frameworks.append('react')
                if 'vue' in all_deps:
                    frameworks.append('vue')
                if 'angular' in all_deps:
                    frameworks.append('angular')
                if 'express' in all_deps:
                    frameworks.append('express')
                if 'next' in all_deps:
                    frameworks.append('nextjs')
                if 'nuxt' in all_deps:
                    frameworks.append('nuxt')
                    
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
        
        # Check requirements.txt for Python frameworks
        requirements_txt = self.project_path / 'requirements.txt'
        if requirements_txt.exists():
            try:
                with open(requirements_txt, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                if 'django' in content:
                    frameworks.append('django')
                if 'flask' in content:
                    frameworks.append('flask')
                if 'fastapi' in content:
                    frameworks.append('fastapi')
                if 'pytest' in content:
                    frameworks.append('pytest')
                    
            except Exception as e:
                logger.warning(f"Failed to parse requirements.txt: {e}")
        
        return frameworks
    
    def _has_test_directory(self) -> bool:
        """Check if project has test directories."""
        
        test_dirs = ['tests', 'test', '__tests__', 'spec']
        for test_dir in test_dirs:
            if (self.project_path / test_dir).exists():
                return True
        return False
    
    def _has_documentation(self) -> bool:
        """Check if project has documentation."""
        
        doc_files = ['README.md', 'README.rst', 'docs', 'documentation']
        for doc_file in doc_files:
            if (self.project_path / doc_file).exists():
                return True
        return False
    
    def add_conversation_turn(
        self,
        user_input: str,
        agent_response: str,
        reasoning_trace: Optional[Dict[str, Any]] = None,
        actions_taken: Optional[List[Dict[str, Any]]] = None,
        errors_encountered: Optional[List[str]] = None,
        success: bool = True,
    ) -> None:
        """Add a conversation turn to the session."""
        
        if not self.session:
            raise RuntimeError("No active session")
        
        turn = ConversationTurn(
            timestamp=time.time(),
            user_input=user_input,
            agent_response=agent_response,
            reasoning_trace=reasoning_trace,
            actions_taken=actions_taken or [],
            errors_encountered=errors_encountered or [],
            success=success,
        )
        
        self.session.conversation_history.append(turn)
        
        # Add to memory
        self.memory.add_conversation_memory(
            user_input=user_input,
            agent_response=agent_response,
            context=self.get_context(),
        )
        
        # Save session
        self._save_session()
        
        logger.debug(f"Added conversation turn to session {self.session.session_id}")
    
    def set_current_goal(self, goal: str) -> None:
        """Set the current goal for the session."""
        
        if not self.session:
            raise RuntimeError("No active session")
        
        self.session.current_goal = goal
        self._save_session()
        
        logger.info(f"Set current goal: {goal}")
    
    def set_active_plan(self, plan: Dict[str, Any]) -> None:
        """Set the active plan for the session."""
        
        if not self.session:
            raise RuntimeError("No active session")
        
        self.session.active_plan = plan
        self._save_session()
        
        logger.info("Set active plan")
    
    def get_context(self) -> Dict[str, Any]:
        """Get current session context."""
        
        if not self.session:
            return {}
        
        context = {
            "session_id": self.session.session_id,
            "project_type": self.session.project_context.project_type,
            "languages": self.session.project_context.languages,
            "frameworks": self.session.project_context.frameworks,
            "file_count": self.session.project_context.file_count,
            "project_size": self.session.project_context.project_size,
            "git_repo": self.session.project_context.git_repo,
            "has_tests": self.session.project_context.has_tests,
            "has_docs": self.session.project_context.has_docs,
            "current_goal": self.session.current_goal,
            "conversation_turns": len(self.session.conversation_history),
            "context_variables": self.session.context_variables,
        }
        
        return context
    
    def get_recent_context(self, turns: int = 5) -> Dict[str, Any]:
        """Get context from recent conversation turns."""
        
        if not self.session:
            return {}
        
        recent_turns = self.session.conversation_history[-turns:]
        
        context = {
            "recent_conversations": [
                {
                    "user_input": turn.user_input,
                    "agent_response": turn.agent_response[:200] + "..." if len(turn.agent_response) > 200 else turn.agent_response,
                    "success": turn.success,
                    "errors": turn.errors_encountered,
                }
                for turn in recent_turns
            ],
            "recent_errors": [
                error
                for turn in recent_turns
                for error in turn.errors_encountered
            ],
            "recent_actions": [
                action
                for turn in recent_turns
                for action in turn.actions_taken
            ],
        }
        
        return context
    
    def _save_session(self) -> None:
        """Save session to disk."""
        
        if not self.session:
            return
        
        try:
            # Ensure cache directory exists
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict and handle Path objects
            session_data = self.session.dict()
            session_data['project_context']['project_path'] = str(session_data['project_context']['project_path'])
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            logger.debug(f"Saved session {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        
        if not self.session:
            return {}
        
        stats = {
            "session_id": self.session.session_id,
            "duration": time.time() - self.session.start_time,
            "conversation_turns": len(self.session.conversation_history),
            "successful_turns": sum(1 for turn in self.session.conversation_history if turn.success),
            "failed_turns": sum(1 for turn in self.session.conversation_history if not turn.success),
            "total_errors": sum(len(turn.errors_encountered) for turn in self.session.conversation_history),
            "total_actions": sum(len(turn.actions_taken) for turn in self.session.conversation_history),
            "project_info": {
                "type": self.session.project_context.project_type,
                "languages": self.session.project_context.languages,
                "frameworks": self.session.project_context.frameworks,
                "file_count": self.session.project_context.file_count,
                "size": self.session.project_context.project_size,
            },
            "memory_stats": self.memory.get_memory_stats(),
        }
        
        return stats
