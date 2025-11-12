#!/usr/bin/env python3
"""
Full CodeGenie Application Demo
Demonstrates all implemented features including documentation, deployment, and monitoring
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.monitoring_dashboard import MonitoringDashboard, AlertManager
from codegenie.core.community_support import CommunitySupport, KnowledgeBase
from codegenie.core.telemetry import TelemetryManager, UsageAnalytics
from codegenie.core.error_reporting import ErrorReporter, DiagnosticTool


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}\n")


async def demo_monitoring_dashboard():
    """Demonstrate monitoring dashboard features"""
    print_header("MONITORING DASHBOARD DEMO")
    
    # Initialize dashboard
    data_dir = Path.home() / ".codegenie"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    dashboard = MonitoringDashboard(data_dir)
    
    print_section("Real-time Metrics")
    metrics = dashboard.get_realtime_metrics()
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"Active Sessions: {metrics['active_sessions']}")
    print(f"Tasks in Progress: {metrics['tasks_in_progress']}")
    print(f"System Health: {metrics['system_health']['overall']}")
    
    if metrics['model_usage']:
        print("\nModel Usage:")
        for model, count in metrics['model_usage'].items():
            print(f"  {model}: {count} requests")
    
    print_section("Performance Metrics (Last 24 Hours)")
    perf = dashboard.get_performance_metrics(hours=24)
    print(f"Tasks Completed: {perf['tasks_completed']}")
    print(f"Tasks Failed: {perf['tasks_failed']}")
    print(f"Completion Rate: {perf['task_completion_rate']*100:.1f}%")
    print(f"Average Duration: {perf['average_task_duration']:.1f}s")
    print(f"Error Rate: {perf['error_rate']*100:.1f}%")
    
    print_section("Usage Trends (Last 7 Days)")
    trends = dashboard.get_usage_trends(days=7)
    
    if trends['daily_usage']:
        print("Daily Usage:")
        for day_data in trends['daily_usage'][-7:]:
            print(f"  {day_data['date']}: {day_data['count']} events")
    
    if trends['feature_usage']:
        print("\nTop Features:")
        sorted_features = sorted(
            trends['feature_usage'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for feature, count in sorted_features:
            print(f"  {feature}: {count} uses")
    
    if trends['agent_usage']:
        print("\nAgent Usage:")
        for agent, count in sorted(trends['agent_usage'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {agent}: {count} tasks")
    
    print_section("Alert Management")
    alert_manager = AlertManager(data_dir)
    alerts = alert_manager.check_alerts()
    
    if alerts:
        print(f"Found {len(alerts)} alert(s):")
        for alert in alerts:
            severity_icon = "🔴" if alert['severity'] == 'critical' else "🟡"
            print(f"\n{severity_icon} {alert['severity'].upper()}: {alert['type']}")
            print(f"   Message: {alert['message']}")
            print(f"   Action: {alert['action']}")
    else:
        print("✓ No alerts - all systems operational")
    
    print_section("Full Dashboard Display")
    dashboard.print_dashboard()
    
    print("✓ Monitoring dashboard demo complete\n")


async def demo_community_support():
    """Demonstrate community support features"""
    print_header("COMMUNITY SUPPORT DEMO")
    
    # Initialize support system
    data_dir = Path.home() / ".codegenie"
    support = CommunitySupport(data_dir)
    
    print_section("Creating Support Ticket")
    ticket_id = support.create_ticket(
        title="Need help with autonomous mode",
        description="I'm trying to use autonomous mode but it's not working as expected. "
                   "The agent stops after a few steps.",
        category="features",
        priority="medium"
    )
    print(f"✓ Created ticket: {ticket_id}")
    
    print_section("Adding Response to Ticket")
    support.add_response(
        ticket_id,
        "Have you enabled intervention points? Try: /autonomous on with intervention_points: true",
        author="support"
    )
    print("✓ Response added")
    
    print_section("Viewing Ticket")
    ticket = support.get_ticket(ticket_id)
    if ticket:
        print(f"Ticket ID: {ticket.ticket_id}")
        print(f"Title: {ticket.title}")
        print(f"Status: {ticket.status}")
        print(f"Priority: {ticket.priority}")
        print(f"Category: {ticket.category}")
        print(f"Created: {ticket.created_at}")
        print(f"\nDescription:\n{ticket.description}")
        
        if ticket.responses:
            print(f"\nResponses ({len(ticket.responses)}):")
            for i, response in enumerate(ticket.responses, 1):
                print(f"\n  [{i}] {response['author']} - {response['timestamp']}")
                print(f"      {response['message']}")
    
    print_section("Searching FAQ")
    faq_results = support.search_faq("autonomous")
    print(f"Found {len(faq_results)} FAQ result(s):")
    for faq in faq_results:
        print(f"\nQ: {faq['question']}")
        print(f"A: {faq['answer']}")
        print(f"Category: {faq['category']}")
    
    print_section("Community Resources")
    resources = support.get_community_resources()
    
    print("Documentation:")
    for name, path in resources['documentation'].items():
        print(f"  {name}: {path}")
    
    print("\nCommunity:")
    for name, url in resources['community'].items():
        print(f"  {name}: {url}")
    
    print("\nSupport:")
    for name, contact in resources['support'].items():
        print(f"  {name}: {contact}")
    
    print_section("Support Statistics")
    stats = support.generate_support_report()
    print(f"Total Tickets: {stats['total_tickets']}")
    print(f"Open Tickets: {stats['open_tickets']}")
    print(f"Closed Tickets: {stats['closed_tickets']}")
    
    if stats['by_category']:
        print("\nTickets by Category:")
        for category, count in stats['by_category'].items():
            print(f"  {category}: {count}")
    
    print("\n✓ Community support demo complete\n")


async def demo_knowledge_base():
    """Demonstrate knowledge base features"""
    print_header("KNOWLEDGE BASE DEMO")
    
    data_dir = Path.home() / ".codegenie"
    kb = KnowledgeBase(data_dir)
    
    print_section("Adding Article to Knowledge Base")
    article_id = kb.add_article(
        title="How to Use Autonomous Mode Effectively",
        content="""
Autonomous mode allows CodeGenie to execute complex multi-step tasks with minimal supervision.

Best Practices:
1. Enable intervention points for review opportunities
2. Start with well-defined tasks
3. Use for repetitive or standard implementations
4. Monitor progress and interrupt if needed

Example:
  You: /autonomous on
  You: Build a complete REST API with authentication

CodeGenie will create an execution plan and execute it step by step.
        """,
        category="tutorials",
        tags=["autonomous", "features", "best-practices"]
    )
    print(f"✓ Created article: {article_id}")
    
    print_section("Searching Knowledge Base")
    results = kb.search_articles("autonomous")
    print(f"Found {len(results)} article(s):")
    for article in results:
        print(f"\nTitle: {article['title']}")
        print(f"Category: {article['category']}")
        print(f"Tags: {', '.join(article['tags'])}")
        print(f"Views: {article['views']}")
        print(f"Helpful: {article['helpful_count']}")
    
    print("\n✓ Knowledge base demo complete\n")


async def demo_telemetry_analytics():
    """Demonstrate telemetry and analytics features"""
    print_header("TELEMETRY & ANALYTICS DEMO")
    
    config_dir = Path.home() / ".config" / "codegenie"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Note: Telemetry is opt-in and disabled by default
    print_section("Telemetry System (Opt-in)")
    print("Telemetry is disabled by default to protect privacy.")
    print("To enable: Set telemetry.enabled: true in config.yaml")
    print("\nTelemetry features:")
    print("  • Anonymous usage tracking")
    print("  • Performance metrics")
    print("  • Feature adoption insights")
    print("  • Error pattern analysis")
    print("  • All data sanitized (no sensitive info)")
    
    telemetry = TelemetryManager(config_dir)
    print(f"\nTelemetry Status: {'Enabled' if telemetry.enabled else 'Disabled'}")
    print(f"User ID: {telemetry.user_id} (anonymous hash)")
    print(f"Session ID: {telemetry.session_id}")
    
    print_section("Usage Analytics")
    analytics = UsageAnalytics(telemetry)
    
    # Simulate some events (only if enabled)
    if telemetry.enabled:
        print("Tracking sample events...")
        analytics.track_task_execution("code_generation", 5.2, True)
        analytics.track_agent_usage("architect", "design_system")
        analytics.track_feature_usage("autonomous_mode")
        print("✓ Events tracked")
    
    # Get insights
    print("\nGetting usage insights...")
    stats = telemetry.get_usage_stats()
    print(f"Total Events: {stats['total_events']}")
    print(f"Total Sessions: {stats['sessions']}")
    
    if stats['events_by_type']:
        print("\nEvents by Type:")
        for event_type, count in sorted(stats['events_by_type'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {event_type}: {count}")
    
    print("\n✓ Telemetry & analytics demo complete\n")


async def demo_error_reporting():
    """Demonstrate error reporting and diagnostics"""
    print_header("ERROR REPORTING & DIAGNOSTICS DEMO")
    
    config_dir = Path.home() / ".config" / "codegenie"
    reporter = ErrorReporter(config_dir)
    
    print_section("System Diagnostics")
    diagnostic_tool = DiagnosticTool(reporter)
    diagnostic_tool.print_diagnostics()
    
    print_section("Error Reporting")
    print("Error reporting features:")
    print("  • Automatic error capture")
    print("  • System information collection")
    print("  • Context sanitization (no sensitive data)")
    print("  • Error ID for tracking")
    print("  • Diagnostic information")
    
    # Simulate an error report
    try:
        # This will fail intentionally
        raise ValueError("Demo error for testing")
    except Exception as e:
        error_id = reporter.report_error(
            e,
            context={
                "operation": "demo",
                "component": "error_reporting",
                "timestamp": datetime.now().isoformat()
            },
            user_description="This is a demo error for testing purposes"
        )
        print(f"\n✓ Error reported with ID: {error_id}")
    
    print_section("Recent Error Reports")
    recent_reports = reporter.list_reports(limit=5)
    print(f"Found {len(recent_reports)} recent error report(s):")
    for report in recent_reports:
        print(f"\nError ID: {report.error_id}")
        print(f"Type: {report.error_type}")
        print(f"Message: {report.error_message}")
        print(f"Timestamp: {report.timestamp}")
    
    print("\n✓ Error reporting demo complete\n")


async def demo_documentation_access():
    """Demonstrate documentation access"""
    print_header("DOCUMENTATION ACCESS DEMO")
    
    docs_dir = Path(__file__).parent / "docs"
    
    print_section("Available Documentation")
    
    doc_files = [
        ("User Guide", "USER_GUIDE.md"),
        ("API Reference", "API_REFERENCE.md"),
        ("Tutorials", "TUTORIALS.md"),
        ("ToolExecutor Guide", "TOOL_EXECUTOR_GUIDE.md"),
        ("Terminal Interface Guide", "TERMINAL_INTERFACE_GUIDE.md"),
        ("Video Tutorials", "VIDEO_TUTORIALS.md"),
        ("Troubleshooting", "TROUBLESHOOTING.md"),
        ("FAQ", "FAQ.md"),
        ("Deployment Guide", "DEPLOYMENT.md"),
        ("Support", "SUPPORT.md")
    ]
    
    print("Documentation Files:")
    for name, filename in doc_files:
        filepath = docs_dir / filename
        exists = "✓" if filepath.exists() else "✗"
        size = f"{filepath.stat().st_size / 1024:.1f} KB" if filepath.exists() else "N/A"
        print(f"  {exists} {name:30s} ({filename:30s}) - {size}")
    
    print_section("Quick Documentation Access")
    print("To view documentation:")
    print("  • User Guide:           cat docs/USER_GUIDE.md")
    print("  • ToolExecutor Guide:   cat docs/TOOL_EXECUTOR_GUIDE.md")
    print("  • Terminal Guide:       cat docs/TERMINAL_INTERFACE_GUIDE.md")
    print("  • Video Tutorials:      cat docs/VIDEO_TUTORIALS.md")
    print("  • API Reference:        cat docs/API_REFERENCE.md")
    
    print("\n✓ Documentation access demo complete\n")


async def demo_deployment_info():
    """Demonstrate deployment information"""
    print_header("DEPLOYMENT INFORMATION DEMO")
    
    print_section("Available Deployment Methods")
    
    deployment_methods = [
        ("Local Installation", "scripts/install.sh", "Automated local setup"),
        ("Docker", "docker-compose.yml", "Containerized deployment"),
        ("Kubernetes", "deploy/kubernetes/deployment.yaml", "Production K8s deployment"),
        ("AWS CloudFormation", "deploy/aws/cloudformation.yaml", "AWS cloud deployment")
    ]
    
    print("Deployment Options:")
    for name, file, description in deployment_methods:
        filepath = Path(__file__).parent / file
        exists = "✓" if filepath.exists() else "✗"
        print(f"  {exists} {name:20s} - {description}")
        print(f"      File: {file}")
    
    print_section("Deployment Commands")
    print("Local Installation:")
    print("  ./scripts/install.sh")
    
    print("\nDocker Deployment:")
    print("  docker-compose up -d")
    
    print("\nKubernetes Deployment:")
    print("  kubectl apply -f deploy/kubernetes/deployment.yaml")
    
    print("\nAWS Deployment:")
    print("  aws cloudformation create-stack --stack-name codegenie \\")
    print("    --template-body file://deploy/aws/cloudformation.yaml")
    
    print_section("Update & Migration")
    print("Update CodeGenie:")
    print("  ./scripts/update.sh")
    
    print("\nRun Migrations:")
    print("  python scripts/migrate.py run")
    
    print("\nCheck Migration Status:")
    print("  python scripts/migrate.py status")
    
    print("\n✓ Deployment information demo complete\n")


async def main():
    """Main demo function"""
    print("\n" + "=" * 80)
    print("  CODEGENIE FULL APPLICATION DEMO")
    print("  Comprehensive demonstration of all features")
    print("=" * 80)
    
    print("\nThis demo showcases:")
    print("  1. Monitoring Dashboard - Real-time metrics and analytics")
    print("  2. Community Support - Tickets, FAQ, and resources")
    print("  3. Knowledge Base - Articles and documentation")
    print("  4. Telemetry & Analytics - Usage insights (opt-in)")
    print("  5. Error Reporting - Diagnostics and error tracking")
    print("  6. Documentation Access - All available guides")
    print("  7. Deployment Information - Setup and deployment options")
    
    print("\nPress Enter to start the demo...")
    input()
    
    try:
        # Run all demos
        await demo_monitoring_dashboard()
        await demo_community_support()
        await demo_knowledge_base()
        await demo_telemetry_analytics()
        await demo_error_reporting()
        await demo_documentation_access()
        await demo_deployment_info()
        
        # Final summary
        print_header("DEMO COMPLETE")
        print("✓ All features demonstrated successfully!")
        print("\nKey Takeaways:")
        print("  • Comprehensive monitoring with real-time metrics")
        print("  • Strong community support infrastructure")
        print("  • Extensive documentation and guides")
        print("  • Privacy-focused telemetry (opt-in)")
        print("  • Robust error reporting and diagnostics")
        print("  • Multiple deployment options")
        print("  • Production-ready system")
        
        print("\nNext Steps:")
        print("  1. Explore the documentation in docs/")
        print("  2. Try the deployment scripts")
        print("  3. Check the monitoring dashboard")
        print("  4. Review the support resources")
        
        print("\nFor more information:")
        print("  • Documentation: docs/USER_GUIDE.md")
        print("  • Support: docs/SUPPORT.md")
        print("  • Deployment: docs/DEPLOYMENT.md")
        
        print("\n" + "=" * 80)
        print("  Thank you for using CodeGenie!")
        print("=" * 80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
