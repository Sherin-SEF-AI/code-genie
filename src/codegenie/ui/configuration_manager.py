"""
Advanced configuration management system for CodeGenie.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Advanced configuration management with templates and validation."""
    
    def __init__(self):
        self.templates = {
            'default': self._get_default_template(),
            'minimal': self._get_minimal_template(),
            'full': self._get_full_template(),
            'team': self._get_team_template(),
            'enterprise': self._get_enterprise_template()
        }
        
        self.config_schema = self._get_config_schema()
    
    def initialize_project_config(self, project_path: Path, template: str = 'default') -> None:
        """Initialize project configuration with specified template."""
        
        config_dir = project_path / '.codegenie'
        config_dir.mkdir(exist_ok=True)
        
        # Create main config file
        config_file = config_dir / 'config.yaml'
        
        if template in self.templates:
            config_content = self.templates[template]
        else:
            logger.warning(f"Unknown template '{template}', using default")
            config_content = self.templates['default']
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Create additional configuration files
        self._create_agent_configs(config_dir)
        self._create_workflow_configs(config_dir)
        self._create_learning_configs(config_dir)
        
        logger.info(f"Configuration initialized in {config_dir}")
    
    def load_project_config(self, project_path: Path) -> Dict[str, Any]:
        """Load project configuration."""
        
        config_file = project_path / '.codegenie' / 'config.yaml'
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate configuration
            self._validate_config(config)
            
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    def save_project_config(self, project_path: Path, config: Dict[str, Any]) -> None:
        """Save project configuration."""
        
        # Validate before saving
        self._validate_config(config)
        
        config_file = project_path / '.codegenie' / 'config.yaml'
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_file}")
    
    def set_config_value(self, project_path: Path, key: str, value: Any) -> None:
        """Set a specific configuration value."""
        
        try:
            config = self.load_project_config(project_path)
        except FileNotFoundError:
            # Create default config if none exists
            self.initialize_project_config(project_path)
            config = self.load_project_config(project_path)
        
        # Handle nested keys (e.g., "models.default")
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Convert string values to appropriate types
        current[keys[-1]] = self._convert_value(value)
        
        self.save_project_config(project_path, config)
    
    def get_config_value(self, project_path: Path, key: str, default: Any = None) -> Any:
        """Get a specific configuration value."""
        
        try:
            config = self.load_project_config(project_path)
        except FileNotFoundError:
            return default
        
        # Handle nested keys
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def list_templates(self) -> List[str]:
        """List available configuration templates."""
        return list(self.templates.keys())
    
    def get_template_description(self, template: str) -> str:
        """Get description of a configuration template."""
        descriptions = {
            'default': 'Balanced configuration with core features enabled',
            'minimal': 'Lightweight configuration with basic features only',
            'full': 'Complete configuration with all advanced features',
            'team': 'Team-oriented configuration with collaboration features',
            'enterprise': 'Enterprise configuration with security and compliance'
        }
        return descriptions.get(template, 'Unknown template')
    
    def validate_config_file(self, config_file: Path) -> List[str]:
        """Validate a configuration file and return any errors."""
        
        errors = []
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            errors.extend(self._validate_config(config, return_errors=True))
            
        except FileNotFoundError:
            errors.append(f"Configuration file not found: {config_file}")
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {e}")
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
        
        return errors
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries."""
        
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_agent_configs(self, config_dir: Path) -> None:
        """Create agent-specific configuration files."""
        
        agents_dir = config_dir / 'agents'
        agents_dir.mkdir(exist_ok=True)
        
        agent_configs = {
            'architect.yaml': """
# Architect Agent Configuration
specialization: "system_design"
capabilities:
  - architecture_analysis
  - technology_selection
  - design_patterns
  - scalability_planning

models:
  primary: "llama3.1:8b"
  fallback: "codellama:7b"

parameters:
  creativity: 0.7
  analysis_depth: "deep"
  recommendation_count: 3
            """,
            
            'security.yaml': """
# Security Agent Configuration
specialization: "security_analysis"
capabilities:
  - vulnerability_scanning
  - threat_modeling
  - security_best_practices
  - compliance_checking

models:
  primary: "codellama:7b"
  security_focused: true

parameters:
  scan_depth: "comprehensive"
  risk_tolerance: "low"
  compliance_standards: ["OWASP", "CWE"]
            """,
            
            'performance.yaml': """
# Performance Agent Configuration
specialization: "performance_optimization"
capabilities:
  - bottleneck_detection
  - optimization_suggestions
  - profiling_analysis
  - resource_monitoring

models:
  primary: "llama3.1:8b"
  
parameters:
  optimization_level: "aggressive"
  profiling_enabled: true
  metrics_collection: true
            """
        }
        
        for filename, content in agent_configs.items():
            config_file = agents_dir / filename
            with open(config_file, 'w') as f:
                f.write(content.strip())
    
    def _create_workflow_configs(self, config_dir: Path) -> None:
        """Create workflow configuration files."""
        
        workflows_dir = config_dir / 'workflows'
        workflows_dir.mkdir(exist_ok=True)
        
        workflow_config = """
# Workflow Engine Configuration
execution:
  timeout: 3600  # 1 hour
  max_parallel_tasks: 4
  checkpoint_interval: 300  # 5 minutes
  rollback_enabled: true

planning:
  decomposition_depth: 3
  dependency_analysis: true
  risk_assessment: true
  effort_estimation: true

monitoring:
  progress_tracking: true
  real_time_updates: true
  performance_metrics: true
  error_reporting: true

recovery:
  auto_retry: true
  max_retries: 3
  fallback_strategies: true
  user_intervention: true
        """
        
        config_file = workflows_dir / 'engine.yaml'
        with open(config_file, 'w') as f:
            f.write(workflow_config.strip())
    
    def _create_learning_configs(self, config_dir: Path) -> None:
        """Create learning engine configuration files."""
        
        learning_dir = config_dir / 'learning'
        learning_dir.mkdir(exist_ok=True)
        
        learning_config = """
# Learning Engine Configuration
adaptation:
  learning_rate: 0.1
  feedback_weight: 0.8
  adaptation_threshold: 0.7
  pattern_recognition: true

personalization:
  user_profiling: true
  preference_modeling: true
  style_adaptation: true
  skill_assessment: true

feedback:
  collection_enabled: true
  rating_system: true
  comment_analysis: true
  improvement_tracking: true

privacy:
  data_encryption: true
  local_storage: true
  anonymization: true
  retention_policy: "30_days"
        """
        
        config_file = learning_dir / 'engine.yaml'
        with open(config_file, 'w') as f:
            f.write(learning_config.strip())
    
    def _validate_config(self, config: Dict[str, Any], return_errors: bool = False) -> Union[bool, List[str]]:
        """Validate configuration against schema."""
        
        errors = []
        
        # Check required fields
        required_fields = ['models']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate models section
        if 'models' in config:
            models = config['models']
            if not isinstance(models, dict):
                errors.append("'models' must be a dictionary")
            elif 'default' not in models:
                errors.append("'models.default' is required")
        
        # Validate boolean fields
        boolean_fields = [
            'autonomous_workflows', 'multi_agent_coordination', 'adaptive_learning',
            'safe_mode', 'cache_enabled', 'parallel_processing'
        ]
        
        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                errors.append(f"'{field}' must be a boolean value")
        
        # Validate numeric fields
        numeric_fields = {
            'max_context_length': (1024, 32768),
            'code_execution_timeout': (1, 3600),
            'learning_rate': (0.0, 1.0),
            'feedback_weight': (0.0, 1.0)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in config:
                value = config[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"'{field}' must be a number")
                elif not (min_val <= value <= max_val):
                    errors.append(f"'{field}' must be between {min_val} and {max_val}")
        
        if return_errors:
            return errors
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        
        # Try boolean
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for validation."""
        
        return {
            'type': 'object',
            'required': ['models'],
            'properties': {
                'models': {
                    'type': 'object',
                    'required': ['default'],
                    'properties': {
                        'default': {'type': 'string'},
                        'fallback': {'type': 'string'}
                    }
                },
                'autonomous_workflows': {'type': 'boolean'},
                'multi_agent_coordination': {'type': 'boolean'},
                'adaptive_learning': {'type': 'boolean'},
                'max_context_length': {
                    'type': 'integer',
                    'minimum': 1024,
                    'maximum': 32768
                },
                'safe_mode': {'type': 'boolean'},
                'learning_rate': {
                    'type': 'number',
                    'minimum': 0.0,
                    'maximum': 1.0
                }
            }
        }
    
    def _get_default_template(self) -> str:
        """Get default configuration template."""
        return """
# CodeGenie Advanced Configuration

# Core Settings
models:
  default: "llama3.1:8b"
  fallback: "codellama:7b"

# Advanced Features
autonomous_workflows: true
multi_agent_coordination: true
adaptive_learning: true

# Performance Settings
max_context_length: 8192
cache_enabled: true
parallel_processing: true

# Security Settings
sandbox_enabled: true
code_execution_timeout: 30
safe_mode: true

# Learning Settings
learning_rate: 0.1
feedback_weight: 0.8
adaptation_threshold: 0.7

# UI Settings
interface_theme: "dark"
show_progress: true
verbose_output: false

# Integration Settings
git_integration: true
ide_plugins: true
webhook_enabled: false
        """
    
    def _get_minimal_template(self) -> str:
        """Get minimal configuration template."""
        return """
# CodeGenie Minimal Configuration

models:
  default: "llama3.1:8b"

autonomous_workflows: false
multi_agent_coordination: false
adaptive_learning: true

safe_mode: true
        """
    
    def _get_full_template(self) -> str:
        """Get full configuration template."""
        return """
# CodeGenie Full Configuration

# Core Settings
models:
  default: "llama3.1:8b"
  fallback: "codellama:7b"
  specialized:
    architect: "llama3.1:8b"
    security: "codellama:7b"
    performance: "llama3.1:8b"

# Advanced Features
autonomous_workflows: true
multi_agent_coordination: true
adaptive_learning: true
predictive_assistance: true
natural_language_programming: true

# Performance Settings
max_context_length: 16384
cache_enabled: true
cache_size: "1GB"
parallel_processing: true
max_parallel_tasks: 4

# Security Settings
sandbox_enabled: true
code_execution_timeout: 60
safe_mode: true
vulnerability_scanning: true
security_audit_enabled: true

# Learning Settings
learning_rate: 0.1
feedback_weight: 0.8
adaptation_threshold: 0.7
personalization_enabled: true
pattern_recognition: true

# Multi-Agent Settings
agent_coordination_timeout: 300
conflict_resolution_strategy: "priority_based"
agent_communication_protocol: "async"

# Workflow Settings
workflow_timeout: 3600
rollback_enabled: true
checkpoint_interval: 300
progress_tracking: true

# UI Settings
interface_theme: "dark"
show_progress: true
verbose_output: true
real_time_updates: true

# Integration Settings
git_integration: true
ide_plugins: true
webhook_enabled: true
ci_cd_integration: true
team_collaboration: true

# Monitoring Settings
performance_monitoring: true
usage_analytics: true
error_reporting: true
telemetry_enabled: true
        """
    
    def _get_team_template(self) -> str:
        """Get team configuration template."""
        return """
# CodeGenie Team Configuration

# Core Settings
models:
  default: "llama3.1:8b"
  fallback: "codellama:7b"

# Team Features
autonomous_workflows: true
multi_agent_coordination: true
adaptive_learning: true
team_collaboration: true

# Collaboration Settings
shared_knowledge_base: true
collaborative_planning: true
team_analytics: true
communication_integration: true

# Workflow Settings
workflow_sharing: true
template_library: true
best_practices_enforcement: true

# Security Settings
role_based_access: true
audit_logging: true
safe_mode: true

# Integration Settings
git_integration: true
ci_cd_integration: true
project_management_integration: true
        """
    
    def _get_enterprise_template(self) -> str:
        """Get enterprise configuration template."""
        return """
# CodeGenie Enterprise Configuration

# Core Settings
models:
  default: "llama3.1:8b"
  fallback: "codellama:7b"
  enterprise_model: "custom-enterprise-model"

# Enterprise Features
autonomous_workflows: true
multi_agent_coordination: true
adaptive_learning: true
enterprise_security: true
compliance_monitoring: true

# Security & Compliance
role_based_access_control: true
multi_factor_authentication: true
data_encryption: true
audit_logging: true
compliance_reporting: true
vulnerability_scanning: true

# Governance
policy_enforcement: true
approval_workflows: true
change_management: true
risk_assessment: true

# Monitoring & Analytics
comprehensive_monitoring: true
performance_analytics: true
usage_analytics: true
security_monitoring: true
compliance_tracking: true

# Integration
enterprise_sso: true
ldap_integration: true
api_management: true
webhook_security: true

# Scalability
load_balancing: true
horizontal_scaling: true
resource_management: true
performance_optimization: true
        """