#!/usr/bin/env python3
"""
Demo script for DependencyManager.

This demonstrates the dependency management capabilities including:
- Detecting missing dependencies from imports
- Resolving package versions
- Detecting conflicts
- Managing package files (package.json, requirements.txt, etc.)
- Supporting multiple package managers
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.dependency_manager import (
    DependencyManager,
    Language,
    PackageManager,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_basic_usage():
    """Demonstrate basic dependency manager usage."""
    print_section("Basic Dependency Manager Usage")
    
    # Initialize with current project
    dm = DependencyManager(Path.cwd())
    
    print("\n1. Discovered Package Files:")
    for pm, package_file in dm.package_files.items():
        print(f"   - {pm.value}: {package_file.path}")
        print(f"     Dependencies: {len(package_file.dependencies)}")
        print(f"     Dev Dependencies: {len(package_file.dev_dependencies)}")
    
    print("\n2. All Dependencies:")
    all_deps = dm.get_all_dependencies()
    for dep in all_deps[:10]:  # Show first 10
        dev_marker = " (dev)" if dep.is_dev else ""
        print(f"   - {dep.name} {dep.version or 'latest'}{dev_marker} [{dep.package_manager.value}]")
    if len(all_deps) > 10:
        print(f"   ... and {len(all_deps) - 10} more")


def demo_missing_dependencies():
    """Demonstrate missing dependency detection."""
    print_section("Missing Dependency Detection")
    
    dm = DependencyManager(Path.cwd())
    
    print("\n1. Scanning for missing dependencies...")
    missing = dm.detect_missing_dependencies()
    
    if missing:
        print(f"\n   Found {len(missing)} missing dependencies:")
        for dep in missing[:5]:  # Show first 5
            print(f"   - {dep.name} (from {dep.source})")
        if len(missing) > 5:
            print(f"   ... and {len(missing) - 5} more")
    else:
        print("   ✓ No missing dependencies found!")


def demo_version_resolution():
    """Demonstrate version resolution."""
    print_section("Version Resolution")
    
    dm = DependencyManager(Path.cwd())
    
    packages_to_check = [
        ("requests", Language.PYTHON),
        ("flask", Language.PYTHON),
        ("express", Language.JAVASCRIPT),
    ]
    
    print("\n1. Resolving package versions:")
    for package, language in packages_to_check:
        print(f"\n   {package} ({language.value}):")
        version = dm.resolve_version(package, language)
        if version:
            print(f"   Latest version: {version}")
        else:
            print(f"   Could not resolve version (package manager may not be available)")



def demo_conflict_detection():
    """Demonstrate conflict detection."""
    print_section("Conflict Detection")
    
    dm = DependencyManager(Path.cwd())
    
    print("\n1. Checking for version conflicts...")
    conflicts = dm.detect_conflicts()
    
    if conflicts:
        print(f"\n   Found {len(conflicts)} conflicts:")
        for conflict in conflicts:
            print(f"\n   Package: {conflict.package_name}")
            print(f"   Conflicting versions: {', '.join(conflict.required_versions)}")
            print(f"   Sources: {', '.join(conflict.sources)}")
            if conflict.suggested_resolution:
                print(f"   Suggested: {conflict.suggested_resolution}")
    else:
        print("   ✓ No conflicts detected!")


def demo_package_manager_support():
    """Demonstrate multiple package manager support."""
    print_section("Package Manager Support")
    
    dm = DependencyManager(Path.cwd())
    
    package_managers = [
        PackageManager.NPM,
        PackageManager.YARN,
        PackageManager.PIP,
        PackageManager.POETRY,
        PackageManager.CARGO,
        PackageManager.GO_MODULES,
    ]
    
    print("\n1. Available Package Managers:")
    for pm in package_managers:
        info = dm.get_package_manager_info(pm)
        status = "✓" if info['available'] else "✗"
        print(f"   {status} {pm.value}")
        if info['available'] and info['version']:
            print(f"      Version: {info['version']}")
        if info['package_file']:
            print(f"      Package file: {info['package_file']}")


def demo_dependency_info():
    """Demonstrate getting detailed dependency info."""
    print_section("Dependency Information")
    
    dm = DependencyManager(Path.cwd())
    
    # Check some common packages
    packages = [
        ("anthropic", Language.PYTHON),
        ("requests", Language.PYTHON),
    ]
    
    print("\n1. Detailed Dependency Information:")
    for package, language in packages:
        print(f"\n   {package}:")
        info = dm.get_dependency_info(package, language)
        print(f"   - Language: {info['language']}")
        print(f"   - Installed: {info['installed']}")
        if info['version']:
            print(f"   - Current version: {info['version']}")
        if info['latest_version']:
            print(f"   - Latest version: {info['latest_version']}")


def demo_add_dependency():
    """Demonstrate adding a dependency (dry run)."""
    print_section("Adding Dependencies (Demo)")
    
    dm = DependencyManager(Path.cwd())
    
    print("\n1. Example: Adding a new dependency")
    print("   (This is a demonstration - no actual changes will be made)")
    print("\n   To add a dependency:")
    print("   dm.add_dependency('requests', '2.31.0', Language.PYTHON)")
    print("\n   To install a dependency:")
    print("   dm.install_dependency('requests', '2.31.0', Language.PYTHON)")
    print("\n   To remove a dependency:")
    print("   dm.remove_dependency('requests', Language.PYTHON)")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  CodeGenie Dependency Manager Demo")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_missing_dependencies()
        demo_version_resolution()
        demo_conflict_detection()
        demo_package_manager_support()
        demo_dependency_info()
        demo_add_dependency()
        
        print("\n" + "=" * 60)
        print("  Demo Complete!")
        print("=" * 60)
        print("\nThe DependencyManager provides:")
        print("  ✓ Automatic dependency detection from imports")
        print("  ✓ Version resolution from package registries")
        print("  ✓ Conflict detection and resolution")
        print("  ✓ Support for multiple package managers")
        print("  ✓ Package file management (add/remove/update)")
        print("  ✓ Cross-language support (Python, JS/TS, Rust, Go)")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
