"""
CodeGenie Integration Module

This module provides integrations with external development tools including:
- IDE integrations (VS Code, IntelliJ)
- CI/CD pipeline integrations (GitHub Actions, Jenkins, GitLab CI)
- Team collaboration tools (Slack, Teams)
- Webhook and API systems
"""

# Optional imports - some may require additional dependencies
try:
    from .ide_integration import IDEIntegrationManager, VSCodeExtension, IntelliJPlugin
    _IDE_AVAILABLE = True
except ImportError:
    _IDE_AVAILABLE = False

try:
    from .cicd_integration import CICDIntegrationManager, GitHubActionsIntegration, JenkinsIntegration, GitLabCIIntegration
    _CICD_AVAILABLE = True
except ImportError:
    _CICD_AVAILABLE = False

try:
    from .team_collaboration import TeamCollaborationManager, SlackIntegration, TeamsIntegration
    _TEAM_AVAILABLE = True
except ImportError:
    _TEAM_AVAILABLE = False

try:
    from .api_system import APISystem, WebhookManager, AuthenticationManager
    _API_AVAILABLE = True
except ImportError:
    _API_AVAILABLE = False

__all__ = [
    'IDEIntegrationManager',
    'VSCodeExtension', 
    'IntelliJPlugin',
    'CICDIntegrationManager',
    'GitHubActionsIntegration',
    'JenkinsIntegration', 
    'GitLabCIIntegration',
    'TeamCollaborationManager',
    'SlackIntegration',
    'TeamsIntegration',
    'APISystem',
    'WebhookManager',
    'AuthenticationManager'
]