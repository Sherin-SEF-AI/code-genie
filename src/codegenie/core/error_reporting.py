"""
Error Reporting and Diagnostics System
Helps users report errors and provides diagnostic information
"""

import sys
import traceback
import platform
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ErrorReport:
    """Represents an error report"""
    error_id: str
    timestamp: str
    error_type: str
    error_message: str
    traceback: str
    system_info: Dict[str, Any]
    context: Dict[str, Any]
    user_description: Optional[str] = None


class ErrorReporter:
    """Handles error reporting and diagnostics"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.reports_dir = config_dir.parent.parent / ".codegenie" / "error_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def report_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        user_description: Optional[str] = None
    ) -> str:
        """Report an error and return error ID"""
        import uuid
        
        error_id = str(uuid.uuid4())[:8]
        
        report = ErrorReport(
            error_id=error_id,
            timestamp=datetime.now().isoformat(),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=self._get_traceback(),
            system_info=self._get_system_info(),
            context=self._sanitize_context(context),
            user_description=user_description
        )
        
        self._save_report(report)
        return error_id
    
    def _get_traceback(self) -> str:
        """Get formatted traceback"""
        return traceback.format_exc()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "codegenie_version": self._get_codegenie_version()
        }
    
    def _get_codegenie_version(self) -> str:
        """Get CodeGenie version"""
        try:
            from codegenie import __version__
            return __version__
        except:
            return "unknown"
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from context"""
        sanitized = {}
        
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'api_key',
            'auth', 'credential', 'private'
        }
        
        for key, value in context.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "<redacted>"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_context(value)
            elif isinstance(value, (str, Path)) and ('/' in str(value) or '\\' in str(value)):
                sanitized[key] = "<path>"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _save_report(self, report: ErrorReport):
        """Save error report to file"""
        report_file = self.reports_dir / f"error_{report.error_id}.json"
        
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)
    
    def get_report(self, error_id: str) -> Optional[ErrorReport]:
        """Get error report by ID"""
        report_file = self.reports_dir / f"error_{error_id}.json"
        
        if not report_file.exists():
            return None
        
        with open(report_file) as f:
            data = json.load(f)
            return ErrorReport(**data)
    
    def list_reports(self, limit: int = 10) -> list:
        """List recent error reports"""
        reports = []
        
        for report_file in sorted(self.reports_dir.glob("error_*.json"), reverse=True)[:limit]:
            with open(report_file) as f:
                data = json.load(f)
                reports.append(ErrorReport(**data))
        
        return reports
    
    def generate_diagnostic_info(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic information"""
        return {
            "system": self._get_system_info(),
            "ollama": self._check_ollama(),
            "models": self._check_models(),
            "configuration": self._check_configuration(),
            "disk_space": self._check_disk_space(),
            "recent_errors": len(list(self.reports_dir.glob("error_*.json")))
        }
    
    def _check_ollama(self) -> Dict[str, Any]:
        """Check Ollama status"""
        import subprocess
        
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "installed": True,
                "running": result.returncode == 0,
                "version": self._get_ollama_version()
            }
        except:
            return {
                "installed": False,
                "running": False,
                "version": None
            }
    
    def _get_ollama_version(self) -> Optional[str]:
        """Get Ollama version"""
        import subprocess
        
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except:
            return None
    
    def _check_models(self) -> Dict[str, Any]:
        """Check installed models"""
        import subprocess
        
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = [line.split()[0] for line in lines if line.strip()]
                return {
                    "count": len(models),
                    "models": models
                }
        except:
            pass
        
        return {
            "count": 0,
            "models": []
        }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration status"""
        config_file = self.config_dir / "config.yaml"
        
        return {
            "exists": config_file.exists(),
            "path": str(config_file),
            "valid": self._validate_config(config_file) if config_file.exists() else False
        }
    
    def _validate_config(self, config_file: Path) -> bool:
        """Validate configuration file"""
        try:
            import yaml
            with open(config_file) as f:
                yaml.safe_load(f)
            return True
        except:
            return False
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        import shutil
        
        try:
            usage = shutil.disk_usage(str(self.config_dir))
            return {
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "percent_used": (usage.used / usage.total) * 100
            }
        except:
            return {}


class DiagnosticTool:
    """Provides diagnostic tools for troubleshooting"""
    
    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter
    
    def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive diagnostics"""
        print("Running diagnostics...")
        
        diagnostics = self.error_reporter.generate_diagnostic_info()
        
        # Add health checks
        diagnostics["health_checks"] = {
            "ollama_running": diagnostics["ollama"]["running"],
            "models_installed": diagnostics["models"]["count"] > 0,
            "config_valid": diagnostics["configuration"]["valid"],
            "disk_space_ok": diagnostics["disk_space"].get("free_gb", 0) > 10
        }
        
        # Overall health
        diagnostics["overall_health"] = all(diagnostics["health_checks"].values())
        
        return diagnostics
    
    def print_diagnostics(self):
        """Print diagnostics in human-readable format"""
        diagnostics = self.run_diagnostics()
        
        print("\n" + "="*60)
        print("CodeGenie Diagnostics")
        print("="*60)
        
        print("\n📊 System Information:")
        for key, value in diagnostics["system"].items():
            print(f"  {key}: {value}")
        
        print("\n🔧 Ollama Status:")
        ollama = diagnostics["ollama"]
        print(f"  Installed: {'✓' if ollama['installed'] else '✗'}")
        print(f"  Running: {'✓' if ollama['running'] else '✗'}")
        print(f"  Version: {ollama['version'] or 'N/A'}")
        
        print("\n🤖 Models:")
        models = diagnostics["models"]
        print(f"  Installed: {models['count']}")
        for model in models["models"]:
            print(f"    - {model}")
        
        print("\n⚙️  Configuration:")
        config = diagnostics["configuration"]
        print(f"  Exists: {'✓' if config['exists'] else '✗'}")
        print(f"  Valid: {'✓' if config['valid'] else '✗'}")
        print(f"  Path: {config['path']}")
        
        print("\n💾 Disk Space:")
        disk = diagnostics["disk_space"]
        if disk:
            print(f"  Total: {disk['total_gb']:.1f} GB")
            print(f"  Used: {disk['used_gb']:.1f} GB ({disk['percent_used']:.1f}%)")
            print(f"  Free: {disk['free_gb']:.1f} GB")
        
        print("\n🏥 Health Checks:")
        for check, status in diagnostics["health_checks"].items():
            status_icon = "✓" if status else "✗"
            print(f"  {status_icon} {check.replace('_', ' ').title()}")
        
        print("\n" + "="*60)
        overall = "✓ All systems operational" if diagnostics["overall_health"] else "✗ Issues detected"
        print(f"Overall Health: {overall}")
        print("="*60 + "\n")
        
        if not diagnostics["overall_health"]:
            print("💡 Recommendations:")
            if not diagnostics["ollama"]["running"]:
                print("  - Start Ollama: ollama serve")
            if diagnostics["models"]["count"] == 0:
                print("  - Install models: ollama pull llama3.1:8b")
            if not diagnostics["configuration"]["valid"]:
                print("  - Fix configuration: codegenie init")
            if diagnostics["disk_space"].get("free_gb", 100) < 10:
                print("  - Free up disk space (need at least 10GB)")
    
    def export_diagnostics(self, output_file: Path):
        """Export diagnostics to file"""
        diagnostics = self.run_diagnostics()
        
        with open(output_file, 'w') as f:
            json.dump(diagnostics, f, indent=2)
        
        print(f"Diagnostics exported to: {output_file}")
