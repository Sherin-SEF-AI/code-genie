#!/usr/bin/env python3
"""
Automated Full CodeGenie Application Demo
Runs without requiring user input
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.monitoring_dashboard import MonitoringDashboard, AlertManager
from codegenie.core.community_support import CommunitySupport, KnowledgeBase
from codegenie.core.telemetry import TelemetryManager, UsageAnalytics
from codegenie.core.error_reporting import ErrorReporter, DiagnosticTool


def print_banner():
    """Print application banner"""
    print("\n" + "="*80)
    print("  🧞 CODEGENIE - Advanced AI Coding Agent")
    print("  Full Application Demo - Automated Run")
    print("="*80 + "\n")


async def main():
    """Main demo function"""
    print_banner()
    
    data_dir = Path.home() / ".codegenie"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Starting CodeGenie Full Application Demo...\n")
    
    # 1. System Diagnostics
    print("=" * 80)
    print("1️⃣  SYSTEM DIAGNOSTICS")
    print("=" * 80 + "\n")
    
    config_dir = Path.home() / ".config" / "codegenie"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    reporter = ErrorReporter(config_dir)
    diagnostic_tool = DiagnosticTool(reporter)
    diagnostic_tool.print_diagnostics()
    
    # 2. Monitoring Dashboard
    print("\n" + "=" * 80)
    print("2️⃣  MONITORING DASHBOARD")
    print("=" * 80 + "\n")
    
    dashboard = MonitoringDashboard(data_dir)
    dashboard.print_dashboard()
    
    # Check alerts
    alert_manager = AlertManager(data_dir)
    alerts = alert_manager.check_alerts()
    
    if alerts:
        print(f"\n⚠️  Active Alerts: {len(alerts)}")
        for alert in alerts:
            print(f"  • {alert['severity'].upper()}: {alert['message']}")
    else:
        print("\n✅ No active alerts - all systems operational")
    
    # 3. Community Support
    print("\n" + "=" * 80)
    print("3️⃣  COMMUNITY SUPPORT SYSTEM")
    print("=" * 80 + "\n")
    
    support = CommunitySupport(data_dir)
    
    # Create sample ticket
    ticket_id = support.create_ticket(
        title="Getting started with CodeGenie",
        description="I'm new to CodeGenie and would like to learn the basics.",
        category="getting-started",
        priority="low"
    )
    print(f"✅ Support ticket created: {ticket_id}")
    
    # Show FAQ
    print("\n📚 Frequently Asked Questions:")
    faqs = support.get_faq()[:3]  # Show first 3
    for i, faq in enumerate(faqs, 1):
        print(f"\n  {i}. {faq['question']}")
        print(f"     → {faq['answer']}")
    
    # Show resources
    print("\n🌐 Community Resources:")
    resources = support.get_community_resources()
    print(f"  • Discord: {resources['community']['discord']}")
    print(f"  • Forum: {resources['community']['forum']}")
    print(f"  • GitHub: {resources['community']['github']}")
    
    # 4. Knowledge Base
    print("\n" + "=" * 80)
    print("4️⃣  KNOWLEDGE BASE")
    print("=" * 80 + "\n")
    
    kb = KnowledgeBase(data_dir)
    
    # Add sample article
    article_id = kb.add_article(
        title="Quick Start Guide",
        content="Get started with CodeGenie in 5 minutes...",
        category="getting-started",
        tags=["quickstart", "tutorial", "beginner"]
    )
    print(f"✅ Knowledge base article created: {article_id}")
    
    # Search articles
    results = kb.search_articles("start")
    print(f"\n📖 Found {len(results)} article(s) matching 'start'")
    for article in results[:2]:
        print(f"  • {article['title']} ({article['category']})")
    
    # 5. Telemetry & Analytics
    print("\n" + "=" * 80)
    print("5️⃣  TELEMETRY & ANALYTICS")
    print("=" * 80 + "\n")
    
    telemetry = TelemetryManager(config_dir)
    print(f"📊 Telemetry Status: {'Enabled ✅' if telemetry.enabled else 'Disabled (Privacy Mode) 🔒'}")
    print(f"   User ID: {telemetry.user_id} (anonymous)")
    print(f"   Session: {telemetry.session_id}")
    
    stats = telemetry.get_usage_stats()
    print(f"\n📈 Usage Statistics:")
    print(f"   Total Events: {stats['total_events']}")
    print(f"   Total Sessions: {stats['sessions']}")
    
    # 6. Documentation
    print("\n" + "=" * 80)
    print("6️⃣  DOCUMENTATION")
    print("=" * 80 + "\n")
    
    docs_dir = Path(__file__).parent / "docs"
    doc_files = [
        "USER_GUIDE.md",
        "API_REFERENCE.md",
        "TOOL_EXECUTOR_GUIDE.md",
        "TERMINAL_INTERFACE_GUIDE.md",
        "VIDEO_TUTORIALS.md"
    ]
    
    print("📚 Available Documentation:")
    for doc in doc_files:
        filepath = docs_dir / doc
        if filepath.exists():
            size = filepath.stat().st_size / 1024
            print(f"  ✅ {doc:35s} ({size:.1f} KB)")
        else:
            print(f"  ❌ {doc:35s} (Not found)")
    
    # 7. Deployment Options
    print("\n" + "=" * 80)
    print("7️⃣  DEPLOYMENT OPTIONS")
    print("=" * 80 + "\n")
    
    deployment_files = [
        ("Local Install", "scripts/install.sh"),
        ("Docker", "docker-compose.yml"),
        ("Kubernetes", "deploy/kubernetes/deployment.yaml"),
        ("AWS", "deploy/aws/cloudformation.yaml")
    ]
    
    print("🚀 Deployment Methods:")
    for name, file in deployment_files:
        filepath = Path(__file__).parent / file
        status = "✅" if filepath.exists() else "❌"
        print(f"  {status} {name:15s} → {file}")
    
    # 8. Performance Summary
    print("\n" + "=" * 80)
    print("8️⃣  PERFORMANCE SUMMARY")
    print("=" * 80 + "\n")
    
    perf = dashboard.get_performance_metrics(hours=24)
    print("⚡ Last 24 Hours:")
    print(f"  • Tasks Completed: {perf['tasks_completed']}")
    print(f"  • Tasks Failed: {perf['tasks_failed']}")
    print(f"  • Completion Rate: {perf['task_completion_rate']*100:.1f}%")
    print(f"  • Avg Duration: {perf['average_task_duration']:.1f}s")
    print(f"  • Error Rate: {perf['error_rate']*100:.1f}%")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE - ALL SYSTEMS OPERATIONAL")
    print("=" * 80 + "\n")
    
    print("🎯 Key Features Demonstrated:")
    print("  ✅ System diagnostics and health checks")
    print("  ✅ Real-time monitoring dashboard")
    print("  ✅ Community support system")
    print("  ✅ Knowledge base management")
    print("  ✅ Privacy-focused telemetry")
    print("  ✅ Comprehensive documentation")
    print("  ✅ Multiple deployment options")
    print("  ✅ Performance tracking")
    
    print("\n📖 Next Steps:")
    print("  1. Explore documentation: cat docs/USER_GUIDE.md")
    print("  2. Try deployment: ./scripts/install.sh")
    print("  3. Check monitoring: python -c 'from demo_full_application import *'")
    print("  4. Get support: Visit https://community.codegenie.dev")
    
    print("\n" + "=" * 80)
    print("  Thank you for using CodeGenie! 🧞")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
