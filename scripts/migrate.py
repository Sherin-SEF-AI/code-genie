#!/usr/bin/env python3
"""
CodeGenie Migration Script
Handles data migrations between versions
"""

import os
import sys
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class MigrationManager:
    """Manages CodeGenie data migrations"""
    
    def __init__(self):
        self.home = Path.home()
        self.config_dir = self.home / ".config" / "codegenie"
        self.data_dir = self.home / ".codegenie"
        self.cache_dir = self.home / ".cache" / "codegenie"
        self.migrations_dir = self.data_dir / "migrations"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
    def get_current_version(self) -> str:
        """Get current CodeGenie version"""
        version_file = self.data_dir / "version"
        if version_file.exists():
            return version_file.read_text().strip()
        return "0.0.0"
    
    def set_version(self, version: str):
        """Set current version"""
        version_file = self.data_dir / "version"
        version_file.write_text(version)
    
    def get_migration_history(self) -> List[str]:
        """Get list of applied migrations"""
        history_file = self.migrations_dir / "history.json"
        if history_file.exists():
            with open(history_file) as f:
                return json.load(f)
        return []
    
    def add_to_history(self, migration: str):
        """Add migration to history"""
        history = self.get_migration_history()
        history.append({
            "migration": migration,
            "applied_at": datetime.now().isoformat()
        })
        history_file = self.migrations_dir / "history.json"
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def backup_data(self) -> Path:
        """Create backup before migration"""
        backup_dir = self.data_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup config
        if self.config_dir.exists():
            shutil.copytree(self.config_dir, backup_dir / "config")
        
        # Backup sessions
        sessions_dir = self.data_dir / "sessions"
        if sessions_dir.exists():
            shutil.copytree(sessions_dir, backup_dir / "sessions")
        
        print(f"✓ Backup created: {backup_dir}")
        return backup_dir
    
    def migrate_0_1_to_0_2(self):
        """Migration from v0.1.x to v0.2.x"""
        print("Running migration: 0.1.x -> 0.2.x")
        
        # Migrate config format
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            # Add new fields
            if "autonomous" not in config:
                config["autonomous"] = {
                    "enabled": True,
                    "intervention_points": True,
                    "max_steps": 50
                }
            
            if "cache" not in config:
                config["cache"] = {
                    "enabled": True,
                    "ttl": 3600,
                    "max_size": "1GB"
                }
            
            # Write updated config
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print("  ✓ Config migrated")
        
        # Migrate session format
        sessions_dir = self.data_dir / "sessions"
        if sessions_dir.exists():
            for session_file in sessions_dir.glob("*.json"):
                with open(session_file) as f:
                    session = json.load(f)
                
                # Add new fields
                if "context" not in session:
                    session["context"] = {
                        "project_path": session.get("project_path", ""),
                        "files": []
                    }
                
                with open(session_file, 'w') as f:
                    json.dump(session, f, indent=2)
            
            print("  ✓ Sessions migrated")
    
    def migrate_0_2_to_0_3(self):
        """Migration from v0.2.x to v0.3.x"""
        print("Running migration: 0.2.x -> 0.3.x")
        
        # Migrate to new agent system
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            # Add agent configuration
            if "agents" not in config:
                config["agents"] = {
                    "architect": {"enabled": True},
                    "developer": {"enabled": True},
                    "security": {"enabled": True},
                    "performance": {"enabled": True},
                    "tester": {"enabled": True},
                    "documentation": {"enabled": True}
                }
            
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print("  ✓ Agent configuration added")
        
        # Create knowledge graph directory
        kg_dir = self.data_dir / "knowledge_graph"
        kg_dir.mkdir(exist_ok=True)
        print("  ✓ Knowledge graph directory created")
    
    def run_migrations(self):
        """Run all pending migrations"""
        current_version = self.get_current_version()
        history = self.get_migration_history()
        
        print(f"Current version: {current_version}")
        print(f"Applied migrations: {len(history)}")
        
        # Create backup
        backup_dir = self.backup_data()
        
        try:
            # Define migrations
            migrations = [
                ("0.1_to_0.2", self.migrate_0_1_to_0_2),
                ("0.2_to_0.3", self.migrate_0_2_to_0_3),
            ]
            
            # Run pending migrations
            applied_migrations = [m["migration"] for m in history]
            for name, migration_func in migrations:
                if name not in applied_migrations:
                    migration_func()
                    self.add_to_history(name)
                    print(f"✓ Migration {name} completed")
            
            # Update version
            self.set_version("0.3.0")
            print("\n✓ All migrations completed successfully")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            print(f"Backup available at: {backup_dir}")
            sys.exit(1)
    
    def rollback_migration(self, backup_dir: Path):
        """Rollback to a previous backup"""
        print(f"Rolling back to: {backup_dir}")
        
        # Restore config
        if (backup_dir / "config").exists():
            if self.config_dir.exists():
                shutil.rmtree(self.config_dir)
            shutil.copytree(backup_dir / "config", self.config_dir)
        
        # Restore sessions
        if (backup_dir / "sessions").exists():
            sessions_dir = self.data_dir / "sessions"
            if sessions_dir.exists():
                shutil.rmtree(sessions_dir)
            shutil.copytree(backup_dir / "sessions", sessions_dir)
        
        print("✓ Rollback completed")

def main():
    """Main migration entry point"""
    manager = MigrationManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "run":
            manager.run_migrations()
        elif command == "rollback":
            if len(sys.argv) > 2:
                backup_dir = Path(sys.argv[2])
                manager.rollback_migration(backup_dir)
            else:
                print("Usage: migrate.py rollback <backup_dir>")
        elif command == "status":
            print(f"Current version: {manager.get_current_version()}")
            history = manager.get_migration_history()
            print(f"Applied migrations: {len(history)}")
            for migration in history:
                print(f"  - {migration['migration']} ({migration['applied_at']})")
        else:
            print(f"Unknown command: {command}")
            print("Usage: migrate.py [run|rollback|status]")
    else:
        manager.run_migrations()

if __name__ == "__main__":
    main()
