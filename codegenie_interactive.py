#!/usr/bin/env python3
"""
CodeGenie Interactive Testing Application
Manual testing interface for all features
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.monitoring_dashboard import MonitoringDashboard, AlertManager
from codegenie.core.community_support import CommunitySupport, KnowledgeBase
from codegenie.core.telemetry import TelemetryManager, UsageAnalytics
from codegenie.core.error_reporting import ErrorReporter, DiagnosticTool


def print_menu():
    """Print main menu"""
    print("\n" + "="*80)
    print("  🧞 CODEGENIE - Interactive Testing Application")
    print("="*80)
    print("\n📋 Available Features:\n")
    print("  1. System Diagnostics")
    print("  2. Monitoring Dashboard")
    print("  3. Community Support")
    print("  4. Knowledge Base")
    print("  5. Telemetry & Analytics")
    print("  6. Error Reporting")
    print("  7. View Documentation")
    print("  8. Deployment Info")
    print("  9. Run All Tests")
    print("  0. Exit")
    print("\n" + "="*80)


def main():
    """Main interactive loop"""
    data_dir = Path.home() / ".codegenie"
    data_dir.mkdir(parents=True, exist_ok=True)
    config_dir = Path.home() / ".config" / "codegenie"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    dashboard = MonitoringDashboard(data_dir)
    support = CommunitySupport(data_dir)
    kb = KnowledgeBase(data_dir)
    telemetry = TelemetryManager(config_dir)
    reporter = ErrorReporter(config_dir)
    diagnostic_tool = DiagnosticTool(reporter)
    
    print("\n🚀 CodeGenie Interactive Application Started!")
    print("   All components initialized successfully.")
    
    while True:
        print_menu()
        choice = input("\n👉 Select option (0-9): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye! Thank you for testing CodeGenie.")
            break
        elif choice == "1":
            diagnostic_tool.print_diagnostics()
        elif choice == "2":
            dashboard.print_dashboard()
        elif choice == "3":
            test_support(support)
        elif choice == "4":
            test_knowledge_base(kb)
        elif choice == "5":
            test_telemetry(telemetry)
        elif choice == "6":
            test_error_reporting(reporter)
        elif choice == "7":
            show_documentation()
        elif choice == "8":
            show_deployment_info()
        elif choice == "9":
            run_all_tests(dashboard, support, kb, telemetry, reporter, diagnostic_tool)
        else:
            print("\n❌ Invalid option. Please try again.")
        
        input("\n⏸️  Press Enter to continue...")


def test_support(support):
    """Test community support features"""
    print("\n" + "="*80)
    print("  COMMUNITY SUPPORT TESTING")
    print("="*80 + "\n")
    
    print("1. Create Ticket")
    print("2. View Tickets")
    print("3. Search FAQ")
    print("4. View Resources")
    print("5. Back")
    
    choice = input("\nSelect: ").strip()
    
    if choice == "1":
        title = input("Ticket title: ")
        desc = input("Description: ")
        category = input("Category (features/bug/question): ")
        ticket_id = support.create_ticket(title, desc, category)
        print(f"\n✅ Ticket created: {ticket_id}")
    elif choice == "2":
        tickets = support.list_tickets()
        print(f"\n📋 Total tickets: {len(tickets)}")
        for t in tickets[:5]:
            print(f"  • [{t.ticket_id}] {t.title} ({t.status})")
    elif choice == "3":
        query = input("Search FAQ: ")
        results = support.search_faq(query)
        print(f"\n📚 Found {len(results)} result(s):")
        for faq in results:
            print(f"\nQ: {faq['question']}")
            print(f"A: {faq['answer']}")
    elif choice == "4":
        resources = support.get_community_resources()
        print("\n🌐 Community Resources:")
        for category, items in resources.items():
            print(f"\n{category.upper()}:")
            for name, value in items.items():
                print(f"  • {name}: {value}")


def test_knowledge_base(kb):
    """Test knowledge base features"""
    print("\n" + "="*80)
    print("  KNOWLEDGE BASE TESTING")
    print("="*80 + "\n")
    
    print("1. Add Article")
    print("2. Search Articles")
    print("3. Back")
    
    choice = input("\nSelect: ").strip()
    
    if choice == "1":
        title = input("Article title: ")
        content = input("Content: ")
        category = input("Category: ")
        tags = input("Tags (comma-separated): ").split(",")
        article_id = kb.add_article(title, content, category, [t.strip() for t in tags])
        print(f"\n✅ Article created: {article_id}")
    elif choice == "2":
        query = input("Search: ")
        results = kb.search_articles(query)
        print(f"\n📖 Found {len(results)} article(s):")
        for article in results[:5]:
            print(f"\n• {article['title']}")
            print(f"  Category: {article['category']}")
            print(f"  Tags: {', '.join(article['tags'])}")
            print(f"  Views: {article['views']}")


def test_telemetry(telemetry):
    """Test telemetry features"""
    print("\n" + "="*80)
    print("  TELEMETRY & ANALYTICS TESTING")
    print("="*80 + "\n")
    
    print(f"Status: {'Enabled' if telemetry.enabled else 'Disabled'}")
    print(f"User ID: {telemetry.user_id}")
    print(f"Session: {telemetry.session_id}")
    
    stats = telemetry.get_usage_stats()
    print(f"\nTotal Events: {stats['total_events']}")
    print(f"Total Sessions: {stats['sessions']}")
    
    if stats['events_by_type']:
        print("\nEvents by Type:")
        for event_type, count in list(stats['events_by_type'].items())[:5]:
            print(f"  • {event_type}: {count}")


def test_error_reporting(reporter):
    """Test error reporting features"""
    print("\n" + "="*80)
    print("  ERROR REPORTING TESTING")
    print("="*80 + "\n")
    
    print("1. View Recent Errors")
    print("2. Generate Test Error")
    print("3. Back")
    
    choice = input("\nSelect: ").strip()
    
    if choice == "1":
        reports = reporter.list_reports(limit=5)
        print(f"\n📋 Recent errors: {len(reports)}")
        for report in reports:
            print(f"\n• Error ID: {report.error_id}")
            print(f"  Type: {report.error_type}")
            print(f"  Message: {report.error_message}")
            print(f"  Time: {report.timestamp}")
    elif choice == "2":
        try:
            raise ValueError("Test error for demonstration")
        except Exception as e:
            error_id = reporter.report_error(e, {"test": True})
            print(f"\n✅ Error reported: {error_id}")


def show_documentation():
    """Show available documentation"""
    print("\n" + "="*80)
    print("  DOCUMENTATION")
    print("="*80 + "\n")
    
    docs_dir = Path(__file__).parent / "docs"
    docs = [
        "USER_GUIDE.md",
        "API_REFERENCE.md",
        "TOOL_EXECUTOR_GUIDE.md",
        "TERMINAL_INTERFACE_GUIDE.md",
        "VIDEO_TUTORIALS.md",
        "TUTORIALS.md",
        "FAQ.md",
        "TROUBLESHOOTING.md",
        "DEPLOYMENT.md",
        "SUPPORT.md"
    ]
    
    print("📚 Available Documentation:\n")
    for doc in docs:
        filepath = docs_dir / doc
        if filepath.exists():
            size = filepath.stat().st_size / 1024
            print(f"  ✅ {doc:35s} ({size:.1f} KB)")
        else:
            print(f"  ❌ {doc:35s} (Not found)")
    
    print("\n💡 To view: cat docs/<filename>")


def show_deployment_info():
    """Show deployment information"""
    print("\n" + "="*80)
    print("  DEPLOYMENT OPTIONS")
    print("="*80 + "\n")
    
    deployments = [
        ("Local Install", "scripts/install.sh", "./scripts/install.sh"),
        ("Docker", "docker-compose.yml", "docker-compose up -d"),
        ("Kubernetes", "deploy/kubernetes/deployment.yaml", "kubectl apply -f deploy/kubernetes/deployment.yaml"),
        ("AWS", "deploy/aws/cloudformation.yaml", "aws cloudformation create-stack...")
    ]
    
    print("🚀 Deployment Methods:\n")
    for name, file, command in deployments:
        filepath = Path(__file__).parent / file
        status = "✅" if filepath.exists() else "❌"
        print(f"{status} {name:15s}")
        print(f"   File: {file}")
        print(f"   Command: {command}\n")


def run_all_tests(dashboard, support, kb, telemetry, reporter, diagnostic_tool):
    """Run all tests"""
    print("\n" + "="*80)
    print("  RUNNING ALL TESTS")
    print("="*80 + "\n")
    
    print("1️⃣  System Diagnostics...")
    diagnostic_tool.print_diagnostics()
    
    print("\n2️⃣  Monitoring Dashboard...")
    dashboard.print_dashboard()
    
    print("\n3️⃣  Community Support...")
    tickets = support.list_tickets()
    print(f"   Total tickets: {len(tickets)}")
    
    print("\n4️⃣  Knowledge Base...")
    results = kb.search_articles("")
    print(f"   Total articles: {len(results)}")
    
    print("\n5️⃣  Telemetry...")
    stats = telemetry.get_usage_stats()
    print(f"   Total events: {stats['total_events']}")
    
    print("\n6️⃣  Error Reporting...")
    reports = reporter.list_reports()
    print(f"   Total errors: {len(reports)}")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
