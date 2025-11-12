#!/usr/bin/env python3
"""
CodeGenie Interactive Testing - Standalone Version
Manual testing interface without package dependencies
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def print_banner():
    print("\n" + "="*80)
    print("  🧞 CODEGENIE - Interactive Testing Application")
    print("  Standalone Version - Manual Testing Interface")
    print("="*80)


def print_menu():
    print("\n📋 Available Tests:\n")
    print("  1. System Diagnostics")
    print("  2. View Documentation")
    print("  3. Check Deployment Files")
    print("  4. Test Monitoring Components")
    print("  5. Test Support System")
    print("  6. View All Features")
    print("  7. Run Quick Health Check")
    print("  0. Exit")
    print("\n" + "="*80)


def test_diagnostics():
    print("\n" + "="*80)
    print("  SYSTEM DIAGNOSTICS")
    print("="*80 + "\n")
    
    import platform
    import subprocess
    
    print("📊 System Information:")
    print(f"  Platform: {platform.system()}")
    print(f"  Release: {platform.release()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  Architecture: {platform.machine()}")
    
    print("\n🔧 Ollama Status:")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✅ Ollama is running")
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"  ✅ Models installed: {len(lines)-1}")
                for line in lines[1:]:
                    model_name = line.split()[0]
                    print(f"     • {model_name}")
        else:
            print("  ❌ Ollama not responding")
    except:
        print("  ❌ Ollama not found")
    
    print("\n💾 Disk Space:")
    import shutil
    try:
        usage = shutil.disk_usage(str(Path.home()))
        total_gb = usage.total / (1024**3)
        free_gb = usage.free / (1024**3)
        used_percent = (usage.used / usage.total) * 100
        print(f"  Total: {total_gb:.1f} GB")
        print(f"  Free: {free_gb:.1f} GB")
        print(f"  Used: {used_percent:.1f}%")
    except:
        print("  ❌ Could not check disk space")


def view_documentation():
    print("\n" + "="*80)
    print("  DOCUMENTATION")
    print("="*80 + "\n")
    
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("❌ Documentation directory not found")
        return
    
    docs = list(docs_dir.glob("*.md"))
    print(f"📚 Found {len(docs)} documentation file(s):\n")
    
    for doc in sorted(docs):
        size = doc.stat().st_size / 1024
        print(f"  ✅ {doc.name:35s} ({size:.1f} KB)")
    
    print("\n💡 Commands to view:")
    print("  • cat docs/USER_GUIDE.md")
    print("  • cat docs/API_REFERENCE.md")
    print("  • cat docs/TOOL_EXECUTOR_GUIDE.md")


def check_deployment():
    print("\n" + "="*80)
    print("  DEPLOYMENT FILES")
    print("="*80 + "\n")
    
    files = [
        ("Installation Script", "scripts/install.sh"),
        ("Update Script", "scripts/update.sh"),
        ("Migration Script", "scripts/migrate.py"),
        ("Dockerfile", "Dockerfile"),
        ("Docker Compose", "docker-compose.yml"),
        ("Kubernetes Deploy", "deploy/kubernetes/deployment.yaml"),
        ("AWS CloudFormation", "deploy/aws/cloudformation.yaml"),
    ]
    
    print("🚀 Deployment Files:\n")
    for name, filepath in files:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"  ✅ {name:20s} → {filepath:40s} ({size:.1f} KB)")
        else:
            print(f"  ❌ {name:20s} → {filepath:40s} (Not found)")


def test_monitoring():
    print("\n" + "="*80)
    print("  MONITORING COMPONENTS")
    print("="*80 + "\n")
    
    components = [
        ("Monitoring Dashboard", "src/codegenie/core/monitoring_dashboard.py"),
        ("Community Support", "src/codegenie/core/community_support.py"),
        ("Telemetry System", "src/codegenie/core/telemetry.py"),
        ("Error Reporting", "src/codegenie/core/error_reporting.py"),
    ]
    
    print("📊 Monitoring Components:\n")
    for name, filepath in components:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size / 1024
            lines = len(path.read_text().split('\n'))
            print(f"  ✅ {name:25s} ({size:.1f} KB, {lines} lines)")
        else:
            print(f"  ❌ {name:25s} (Not found)")


def test_support():
    print("\n" + "="*80)
    print("  SUPPORT SYSTEM")
    print("="*80 + "\n")
    
    data_dir = Path.home() / ".codegenie" / "support"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("📋 Support System Status:")
    print(f"  Data Directory: {data_dir}")
    print(f"  Exists: {'✅' if data_dir.exists() else '❌'}")
    
    tickets_dir = data_dir / "tickets"
    if tickets_dir.exists():
        tickets = list(tickets_dir.glob("*.json"))
        print(f"  Tickets: {len(tickets)}")
    else:
        print(f"  Tickets: 0 (directory not created yet)")
    
    print("\n💡 Support Features:")
    print("  • Create support tickets")
    print("  • FAQ system")
    print("  • Knowledge base")
    print("  • Community resources")


def view_all_features():
    print("\n" + "="*80)
    print("  ALL CODEGENIE FEATURES")
    print("="*80 + "\n")
    
    features = {
        "Core Features": [
            "Multi-agent system (Architect, Developer, Security, Performance, Testing, Documentation)",
            "Autonomous workflow execution",
            "Code intelligence and analysis",
            "Natural language programming",
            "Terminal integration",
        ],
        "Advanced Features": [
            "Predictive assistance",
            "Proactive monitoring",
            "Impact analysis",
            "Knowledge graph",
            "Tool executor with sandboxing",
        ],
        "Integration": [
            "IDE integration (VS Code, IntelliJ)",
            "CI/CD integration (GitHub Actions, Jenkins)",
            "Shell integration (Bash, Zsh, Fish)",
            "Git operations",
        ],
        "Monitoring & Support": [
            "Real-time monitoring dashboard",
            "Community support system",
            "Knowledge base",
            "Error reporting and diagnostics",
            "Telemetry and analytics (opt-in)",
        ],
        "Documentation": [
            "User Guide",
            "API Reference",
            "ToolExecutor Guide",
            "Terminal Interface Guide",
            "Video Tutorials",
            "Troubleshooting Guide",
            "FAQ",
        ],
        "Deployment": [
            "Local installation",
            "Docker deployment",
            "Kubernetes deployment",
            "AWS CloudFormation",
            "Update and migration system",
        ]
    }
    
    for category, items in features.items():
        print(f"📦 {category}:")
        for item in items:
            print(f"  • {item}")
        print()


def quick_health_check():
    print("\n" + "="*80)
    print("  QUICK HEALTH CHECK")
    print("="*80 + "\n")
    
    checks = []
    
    # Check Python
    import platform
    python_version = platform.python_version()
    python_ok = python_version >= "3.9"
    checks.append(("Python 3.9+", python_ok, f"v{python_version}"))
    
    # Check Ollama
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
        ollama_ok = result.returncode == 0
        checks.append(("Ollama Running", ollama_ok, "Active"))
    except:
        checks.append(("Ollama Running", False, "Not found"))
    
    # Check documentation
    docs_exist = Path("docs").exists()
    checks.append(("Documentation", docs_exist, "Available"))
    
    # Check deployment files
    docker_exists = Path("docker-compose.yml").exists()
    checks.append(("Deployment Files", docker_exists, "Present"))
    
    # Check source code
    src_exists = Path("src/codegenie").exists()
    checks.append(("Source Code", src_exists, "Present"))
    
    # Check monitoring components
    monitoring_exists = Path("src/codegenie/core/monitoring_dashboard.py").exists()
    checks.append(("Monitoring System", monitoring_exists, "Implemented"))
    
    print("🏥 Health Check Results:\n")
    all_ok = True
    for name, status, detail in checks:
        icon = "✅" if status else "❌"
        print(f"  {icon} {name:25s} {detail}")
        if not status:
            all_ok = False
    
    print("\n" + "="*80)
    if all_ok:
        print("  ✅ ALL SYSTEMS OPERATIONAL")
    else:
        print("  ⚠️  SOME ISSUES DETECTED")
    print("="*80)


def main():
    print_banner()
    print("\n🚀 CodeGenie Interactive Testing Application")
    print("   Manual testing interface for all features\n")
    
    while True:
        print_menu()
        choice = input("\n👉 Select option (0-7): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye! Thank you for testing CodeGenie.")
            break
        elif choice == "1":
            test_diagnostics()
        elif choice == "2":
            view_documentation()
        elif choice == "3":
            check_deployment()
        elif choice == "4":
            test_monitoring()
        elif choice == "5":
            test_support()
        elif choice == "6":
            view_all_features()
        elif choice == "7":
            quick_health_check()
        else:
            print("\n❌ Invalid option. Please try again.")
        
        input("\n⏸️  Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
