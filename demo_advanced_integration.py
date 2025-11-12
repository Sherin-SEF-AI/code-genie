"""
Demo script showcasing advanced features integration in CodeGenie.
"""

import asyncio
from pathlib import Path
from rich.console import Console

from src.codegenie.ui.onboarding import OnboardingSystem, TutorialSystem
from src.codegenie.ui.themes import ThemeManager
from src.codegenie.core.permissions import PermissionManager, Permission
from src.codegenie.core.plugin_system import PluginManager


async def demo_onboarding():
    """Demo onboarding system."""
    console = Console()
    console.print("\n[bold blue]═══ Onboarding System Demo ═══[/bold blue]\n")
    
    onboarding = OnboardingSystem(console)
    
    console.print("✨ Onboarding system initialized")
    console.print("   - Collects user preferences")
    console.print("   - Configures features")
    console.print("   - Sets up project")
    console.print("   - Provides quick start guide")
    
    console.print("\n💡 Run: codegenie onboard")


async def demo_tutorials():
    """Demo tutorial system."""
    console = Console()
    console.print("\n[bold blue]═══ Tutorial System Demo ═══[/bold blue]\n")
    
    tutorial_system = TutorialSystem(console)
    
    console.print("📚 Available tutorials:")
    tutorial_system.list_tutorials()
    
    console.print("\n💡 Run: codegenie tutorial run basics")


async def demo_themes():
    """Demo theme system."""
    console = Console()
    console.print("\n[bold blue]═══ Theme System Demo ═══[/bold blue]\n")
    
    theme_manager = ThemeManager()
    
    console.print("🎨 Available themes:")
    for theme_name in theme_manager.list_themes():
        theme = theme_manager.get_theme(theme_name)
        console.print(f"   • {theme_name}: {theme.primary_color} / {theme.background_color}")
    
    console.print(f"\n✅ Current theme: {theme_manager.current_theme}")
    
    # Switch theme
    theme_manager.set_theme("monokai")
    console.print(f"🔄 Switched to: {theme_manager.current_theme}")


async def demo_permissions():
    """Demo permission system."""
    console = Console()
    console.print("\n[bold blue]═══ Permission System Demo ═══[/bold blue]\n")
    
    pm = PermissionManager()
    
    console.print("🔒 Permission checks:")
    
    # Check various permissions
    permissions_to_check = [
        (Permission.FILE_READ, "Read files"),
        (Permission.FILE_WRITE, "Write files"),
        (Permission.FILE_DELETE, "Delete files"),
        (Permission.COMMAND_SUDO, "Run sudo commands"),
        (Permission.GIT_PUSH, "Push to git")
    ]
    
    for permission, description in permissions_to_check:
        allowed = pm.check_permission(permission)
        status = "✅ Allowed" if allowed else "❌ Denied"
        console.print(f"   {status}: {description}")
    
    # Check commands
    console.print("\n🔍 Command checks:")
    commands = [
        "ls -la",
        "rm -rf /",
        "git push origin main"
    ]
    
    for cmd in commands:
        allowed = pm.check_command(cmd)
        status = "✅ Allowed" if allowed else "❌ Denied"
        console.print(f"   {status}: {cmd}")
    
    # Show policy summary
    console.print("\n📋 Policy Summary:")
    summary = pm.get_policy_summary()
    console.print(f"   Allowed permissions: {len(summary['allowed_permissions'])}")
    console.print(f"   Denied permissions: {len(summary['denied_permissions'])}")
    console.print(f"   Require approval: {len(summary['require_approval'])}")


async def demo_plugins():
    """Demo plugin system."""
    console = Console()
    console.print("\n[bold blue]═══ Plugin System Demo ═══[/bold blue]\n")
    
    plugins_dir = Path(".codegenie/plugins")
    plugins_dir.mkdir(parents=True, exist_ok=True)
    
    pm = PluginManager(plugins_dir)
    
    console.print(f"🔌 Plugin directory: {plugins_dir}")
    console.print(f"📦 Loaded plugins: {len(pm.plugins)}")
    
    console.print("\n💡 Plugin system features:")
    console.print("   • Load plugins from directory")
    console.print("   • Register hooks and commands")
    console.print("   • Manage dependencies")
    console.print("   • Enable/disable plugins")


async def demo_end_to_end_workflow():
    """Demo end-to-end workflow concept."""
    console = Console()
    console.print("\n[bold blue]═══ End-to-End Workflow Demo ═══[/bold blue]\n")
    
    console.print("🔄 Workflow Phases:")
    console.print("   1. Context Gathering - AgenticSearch finds relevant code")
    console.print("   2. Planning - WorkflowEngine creates execution plan")
    console.print("   3. Execution - ToolExecutor runs commands and edits files")
    console.print("   4. Verification - Tests, security, and performance checks")
    console.print("   5. Learning - LearningEngine records patterns")
    
    console.print("\n🤖 Integrated Components:")
    console.print("   • ToolExecutor - Command execution")
    console.print("   • AgenticSearch - Context gathering")
    console.print("   • ProactiveAssistant - Suggestions")
    console.print("   • WorkflowEngine - Planning")
    console.print("   • AgentCoordinator - Multi-agent tasks")
    console.print("   • LearningEngine - Adaptation")
    console.print("   • ContextEngine - Historical data")
    
    console.print("\n💡 Example workflow:")
    console.print('   codegenie workflow create "Build a REST API with authentication"')


async def main():
    """Run all demos."""
    console = Console()
    
    console.print("\n[bold green]╔═══════════════════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║   CodeGenie Advanced Features Integration Demo       ║[/bold green]")
    console.print("[bold green]╚═══════════════════════════════════════════════════════╝[/bold green]\n")
    
    # Run demos
    await demo_onboarding()
    await demo_tutorials()
    await demo_themes()
    await demo_permissions()
    await demo_plugins()
    await demo_end_to_end_workflow()
    
    console.print("\n[bold green]═══════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]Demo Complete! All advanced features are integrated.[/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════════════[/bold green]\n")
    
    console.print("📚 For more information:")
    console.print("   • Run: codegenie onboard")
    console.print("   • Run: codegenie tutorial list")
    console.print("   • Read: ADVANCED_INTEGRATION_SUMMARY.md")
    console.print("   • Tests: pytest tests/e2e/test_advanced_features_integration.py\n")


if __name__ == "__main__":
    asyncio.run(main())
