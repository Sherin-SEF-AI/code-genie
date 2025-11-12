"""
Demo script for Proactive Assistant Implementation.

This demonstrates the new proactive monitoring, related code finding,
convention enforcement, and security/performance scanning capabilities.
"""

import asyncio
from pathlib import Path
from src.codegenie.core.proactive_monitoring import ProactiveAssistant
from src.codegenie.core.related_code_finder import RelatedCodeFinder
from src.codegenie.core.convention_enforcer import ConventionEnforcer
from src.codegenie.core.security_performance_scanner import SecurityPerformanceScanner


async def demo_proactive_monitoring():
    """Demonstrate proactive monitoring capabilities."""
    print("\n" + "="*60)
    print("PROACTIVE MONITORING DEMO")
    print("="*60)
    
    project_root = Path("demo_advanced_project")
    assistant = ProactiveAssistant(project_root)
    
    # Start monitoring
    print("\n1. Starting proactive assistant...")
    await assistant.start()
    print(f"   ✓ Monitoring active: {assistant.monitoring_active}")
    
    # Scan codebase
    print("\n2. Scanning entire codebase...")
    result = await assistant.scan_entire_codebase()
    print(f"   ✓ Files monitored: {result.files_monitored}")
    print(f"   ✓ Issues detected: {len(result.issues)}")
    print(f"   ✓ Suggestions generated: {len(result.suggestions)}")
    
    # Show some issues
    if result.issues:
        print("\n3. Sample detected issues:")
        for issue in result.issues[:3]:
            print(f"   - {issue.issue_type.value}: {issue.description}")
    
    # Show some suggestions
    if result.suggestions:
        print("\n4. Sample proactive suggestions:")
        for suggestion in result.suggestions[:3]:
            print(f"   - {suggestion.type.value}: {suggestion.title}")
    
    # Get summary
    summary = assistant.get_summary()
    print("\n5. Monitoring summary:")
    print(f"   - Files tracked: {summary['files_tracked']}")
    print(f"   - Total issues: {summary['total_issues']}")
    print(f"   - Total suggestions: {summary['total_suggestions']}")


async def demo_related_code_finder():
    """Demonstrate related code finding capabilities."""
    print("\n" + "="*60)
    print("RELATED CODE FINDER DEMO")
    print("="*60)
    
    project_root = Path("demo_advanced_project")
    finder = RelatedCodeFinder(project_root)
    
    # Initialize
    print("\n1. Initializing dependency analyzer...")
    await finder.initialize()
    print("   ✓ Dependency graph built")
    
    # Find related code for a file
    test_file = project_root / "src" / "calculator.py"
    if test_file.exists():
        print(f"\n2. Finding related code for {test_file.name}...")
        related = await finder.find_related_code(test_file)
        print(f"   ✓ Found {len(related)} related items")
        
        for item in related[:5]:
            print(f"   - {item.relationship_type}: {item.file_path.name}")
            print(f"     Reason: {item.reason}")
    
    # Get test coverage report
    print("\n3. Test coverage report:")
    coverage_report = finder.get_test_coverage_report()
    print(f"   - Total files: {coverage_report['total_files']}")
    print(f"   - Files with tests: {coverage_report['files_with_tests']}")
    print(f"   - Coverage: {coverage_report['coverage_percentage']:.1f}%")


async def demo_convention_enforcer():
    """Demonstrate convention enforcement capabilities."""
    print("\n" + "="*60)
    print("CONVENTION ENFORCER DEMO")
    print("="*60)
    
    project_root = Path("demo_advanced_project")
    enforcer = ConventionEnforcer(project_root)
    
    # Learn conventions
    print("\n1. Learning project conventions...")
    conventions = await enforcer.learn_conventions()
    print(f"   ✓ Learned {len(conventions)} conventions")
    
    for convention in conventions:
        print(f"   - {convention.name}: {convention.description}")
        print(f"     Confidence: {convention.confidence:.2f}")
    
    # Check codebase
    print("\n2. Checking codebase for violations...")
    report = await enforcer.check_codebase()
    print(f"   ✓ Files checked: {report['files_checked']}")
    print(f"   ✓ Total violations: {report['total_violations']}")
    print(f"   ✓ Auto-fixable: {report['auto_fixable']}")
    
    if report['by_severity']:
        print("\n3. Violations by severity:")
        for severity, count in report['by_severity'].items():
            print(f"   - {severity}: {count}")


async def demo_security_performance_scanner():
    """Demonstrate security and performance scanning capabilities."""
    print("\n" + "="*60)
    print("SECURITY & PERFORMANCE SCANNER DEMO")
    print("="*60)
    
    project_root = Path("demo_advanced_project")
    scanner = SecurityPerformanceScanner()
    
    # Scan codebase
    print("\n1. Scanning codebase for security and performance issues...")
    result = await scanner.scan_codebase(project_root)
    print(f"   ✓ Files scanned: {result['files_scanned']}")
    
    # Security issues
    print("\n2. Security issues:")
    sec_issues = result['security_issues']
    print(f"   - Total: {sec_issues['total']}")
    print(f"   - Critical: {sec_issues['critical']}")
    print(f"   - High: {sec_issues['high']}")
    print(f"   - Medium: {sec_issues['medium']}")
    
    # Performance issues
    print("\n3. Performance issues:")
    perf_issues = result['performance_issues']
    print(f"   - Total: {perf_issues['total']}")
    print(f"   - High impact: {perf_issues['high_impact']}")
    
    # Alerts
    if result['alerts']:
        print("\n4. Proactive alerts:")
        for alert in result['alerts'][:3]:
            print(f"   - [{alert.severity.value}] {alert.title}")
    
    # Suggested fixes
    print(f"\n5. Suggested fixes: {len(result['suggested_fixes'])}")
    print(f"   - Auto-fixable: {result['auto_fixable_count']}")


async def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("PROACTIVE ASSISTANT IMPLEMENTATION DEMO")
    print("Task 2: Proactive Assistant Implementation")
    print("="*60)
    
    try:
        # Demo 1: Proactive Monitoring
        await demo_proactive_monitoring()
        
        # Demo 2: Related Code Finder
        await demo_related_code_finder()
        
        # Demo 3: Convention Enforcer
        await demo_convention_enforcer()
        
        # Demo 4: Security & Performance Scanner
        await demo_security_performance_scanner()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nImplemented features:")
        print("✓ Proactive monitoring with continuous change tracking")
        print("✓ Issue detection for code smells and inconsistencies")
        print("✓ Intelligent suggestion engine")
        print("✓ Workflow prediction for next steps")
        print("✓ Related code identification with dependency analysis")
        print("✓ Test suggestion system")
        print("✓ Documentation update detection")
        print("✓ Convention learning and enforcement")
        print("✓ Automatic violation detection")
        print("✓ Security vulnerability scanning")
        print("✓ Performance bottleneck identification")
        print("✓ Proactive alerting system")
        print("✓ Automatic fix generation")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
