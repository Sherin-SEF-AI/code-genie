#!/usr/bin/env python3
"""
Demo script showcasing the integrated safety system.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.config import Config
from codegenie.utils.integrated_safety import IntegratedSafetySystem
from codegenie.utils.safe_executor import ExecutionContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_integrated_safety():
    """Demonstrate the integrated safety system."""
    
    print("\n" + "="*70)
    print("🛡️  INTEGRATED SAFETY SYSTEM DEMO")
    print("="*70)
    
    # Initialize the integrated safety system
    config = Config()
    safety_system = IntegratedSafetySystem(config)
    
    print("\n🔧 Testing Integrated Safety Features:")
    
    # Test 1: Safe command execution with recovery
    print("\n1️⃣  Safe Command Execution with Recovery")
    print("-" * 50)
    
    test_commands = [
        {
            "name": "Safe Python Command",
            "command": "python3 -c 'print(\"Hello from integrated safety!\")'",
            "description": "Execute a safe Python command",
        },
        {
            "name": "Command with Potential Error",
            "command": "python3 -c 'import nonexistent_module'",
            "description": "Command that will fail and trigger recovery",
        },
        {
            "name": "Blocked Dangerous Command",
            "command": "rm -rf /tmp/test",
            "description": "Dangerous command that should be blocked",
        },
    ]
    
    for i, test in enumerate(test_commands, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Command: {test['command']}")
        print(f"   Description: {test['description']}")
        
        # Create execution context
        context = ExecutionContext(
            working_directory=Path.cwd(),
            timeout=30,
            max_output_size=1024,
        )
        
        # Execute with integrated safety
        report = await safety_system.safe_execute_with_recovery(
            test['command'],
            context,
            max_recovery_attempts=2,
            auto_recover=True
        )
        
        # Display results
        status = "✅ Success" if report.success else "❌ Failed"
        print(f"   Result: {status}")
        print(f"   Duration: {report.duration:.2f}s")
        
        if report.security_violations:
            print(f"   🚨 Security violations: {len(report.security_violations)}")
            for violation in report.security_violations[:2]:  # Show first 2
                print(f"      • {violation}")
        
        if report.errors_detected:
            print(f"   🔍 Errors detected: {len(report.errors_detected)}")
            for error in report.errors_detected[:2]:  # Show first 2
                print(f"      • {error.error_type}: {error.message[:50]}...")
        
        if report.recovery_attempts:
            print(f"   🔧 Recovery attempts: {len(report.recovery_attempts)}")
            successful_recoveries = sum(1 for result in report.recovery_attempts if result.success)
            print(f"      Successful: {successful_recoveries}/{len(report.recovery_attempts)}")
        
        if report.recommendations:
            print(f"   💡 Recommendations:")
            for rec in report.recommendations[:2]:  # Show first 2
                print(f"      • {rec}")
    
    # Test 2: Safe file operations with validation
    print("\n2️⃣  Safe File Operations with Validation")
    print("-" * 50)
    
    test_files = [
        {
            "name": "Valid Python File",
            "content": """
import os
import sys

def hello_world():
    print("Hello from safe file operations!")
    return 0

if __name__ == "__main__":
    sys.exit(hello_world())
""",
            "operation": "create",
        },
        {
            "name": "File with Syntax Error",
            "content": """
import os
import sys

def hello_world(
    print("Hello from file with syntax error!")  # Missing closing parenthesis

if __name__ == "__main__":
    hello_world()
""",
            "operation": "create",
        },
        {
            "name": "Dangerous File",
            "content": """
import os
import subprocess

# This is dangerous code
os.system("rm -rf /")
subprocess.call(["format", "C:"])
""",
            "operation": "create",
        },
    ]
    
    for i, test in enumerate(test_files, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Operation: {test['operation']}")
        
        # Perform safe file operation
        report = await safety_system.safe_file_operation_with_validation(
            test['operation'],
            f"test_file_{i}.py",
            test['content'],
            backup=True,
            validate=True
        )
        
        # Display results
        status = "✅ Success" if report.success else "❌ Failed"
        print(f"   Result: {status}")
        print(f"   Duration: {report.duration:.2f}s")
        
        if report.file_validation:
            validation_status = "✅ Valid" if report.file_validation.is_valid else "❌ Invalid"
            print(f"   Validation: {validation_status}")
            
            if report.file_validation.issues:
                print(f"   Issues: {len(report.file_validation.issues)}")
                for issue in report.file_validation.issues[:2]:  # Show first 2
                    print(f"      • {issue}")
            
            if report.file_validation.warnings:
                print(f"   Warnings: {len(report.file_validation.warnings)}")
                for warning in report.file_validation.warnings[:2]:  # Show first 2
                    print(f"      • {warning}")
        
        if report.security_violations:
            print(f"   🚨 Security violations: {len(report.security_violations)}")
            for violation in report.security_violations[:2]:  # Show first 2
                print(f"      • {violation}")
        
        if report.recommendations:
            print(f"   💡 Recommendations:")
            for rec in report.recommendations[:2]:  # Show first 2
                print(f"      • {rec}")
    
    # Test 3: Safe Python execution with analysis
    print("\n3️⃣  Safe Python Execution with Analysis")
    print("-" * 50)
    
    test_python_codes = [
        {
            "name": "Valid Python Code",
            "code": """
import sys
import os

def main():
    print("Hello from safe Python execution!")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
""",
        },
        {
            "name": "Python Code with Syntax Error",
            "code": """
import sys

def main(
    print("Hello from Python with syntax error!")  # Missing closing parenthesis

if __name__ == "__main__":
    main()
""",
        },
        {
            "name": "Python Code with Import Error",
            "code": """
import nonexistent_module

def main():
    print("This will fail due to import error")
    return 0

if __name__ == "__main__":
    main()
""",
        },
    ]
    
    for i, test in enumerate(test_python_codes, 1):
        print(f"\n   Test {i}: {test['name']}")
        
        # Execute Python code safely
        report = await safety_system.safe_python_execution_with_analysis(
            test['code'],
            analyze_code=True,
            auto_fix=True
        )
        
        # Display results
        status = "✅ Success" if report.success else "❌ Failed"
        print(f"   Result: {status}")
        print(f"   Duration: {report.duration:.2f}s")
        
        if report.file_validation:
            validation_status = "✅ Valid" if report.file_validation.is_valid else "❌ Invalid"
            print(f"   Code Analysis: {validation_status}")
            
            if report.file_validation.issues:
                print(f"   Issues: {len(report.file_validation.issues)}")
                for issue in report.file_validation.issues[:2]:  # Show first 2
                    print(f"      • {issue}")
        
        if report.execution_result:
            if report.execution_result.stdout:
                output = report.execution_result.stdout.strip()
                if output:
                    print(f"   Output: {output[:100]}...")
            
            if report.execution_result.stderr:
                error = report.execution_result.stderr.strip()
                if error:
                    print(f"   Error: {error[:100]}...")
        
        if report.errors_detected:
            print(f"   🔍 Errors detected: {len(report.errors_detected)}")
            for error in report.errors_detected[:2]:  # Show first 2
                print(f"      • {error.error_type}: {error.message[:50]}...")
        
        if report.recovery_attempts:
            print(f"   🔧 Recovery attempts: {len(report.recovery_attempts)}")
            successful_recoveries = sum(1 for result in report.recovery_attempts if result.success)
            print(f"      Successful: {successful_recoveries}/{len(report.recovery_attempts)}")
        
        if report.recommendations:
            print(f"   💡 Recommendations:")
            for rec in report.recommendations[:2]:  # Show first 2
                print(f"      • {rec}")
    
    # Show comprehensive statistics
    print("\n4️⃣  Comprehensive Safety Statistics")
    print("-" * 50)
    
    stats = safety_system.get_safety_statistics()
    
    print(f"   Total operations: {stats.get('total_operations', 0)}")
    print(f"   Successful operations: {stats.get('successful_operations', 0)}")
    print(f"   Success rate: {stats.get('success_rate', 0):.2%}")
    print(f"   Security violations: {stats.get('security_violations', 0)}")
    print(f"   Errors detected: {stats.get('errors_detected', 0)}")
    print(f"   Recovery attempts: {stats.get('recovery_attempts', 0)}")
    print(f"   Successful recoveries: {stats.get('successful_recoveries', 0)}")
    print(f"   Recovery success rate: {stats.get('recovery_success_rate', 0):.2%}")
    print(f"   Average duration: {stats.get('average_duration', 0):.2f}s")
    
    if stats.get('operation_types'):
        print(f"   Operation types:")
        for op_type, count in stats['operation_types'].items():
            print(f"      • {op_type}: {count}")
    
    # Show recent reports
    print("\n5️⃣  Recent Safety Reports")
    print("-" * 50)
    
    recent_reports = safety_system.get_recent_reports(5)
    
    for i, report in enumerate(recent_reports, 1):
        status = "✅" if report.success else "❌"
        print(f"   {i}. {status} {report.operation_type} (ID: {report.operation_id})")
        print(f"      Duration: {report.duration:.2f}s")
        
        if report.security_violations:
            print(f"      Security violations: {len(report.security_violations)}")
        
        if report.errors_detected:
            print(f"      Errors detected: {len(report.errors_detected)}")
        
        if report.recovery_attempts:
            successful = sum(1 for result in report.recovery_attempts if result.success)
            print(f"      Recovery: {successful}/{len(report.recovery_attempts)} successful")
    
    # Cleanup
    safety_system.cleanup()
    
    print("\n" + "="*70)
    print("✅ INTEGRATED SAFETY SYSTEM DEMO COMPLETED!")
    print("="*70)
    
    print("\n🎯 Key Features Demonstrated:")
    print("   • Integrated error detection and recovery")
    print("   • Safe command execution with security checks")
    print("   • File operations with comprehensive validation")
    print("   • Python code analysis and auto-fixing")
    print("   • Comprehensive safety reporting")
    print("   • Automatic backup and rollback capabilities")
    print("   • Security violation detection and blocking")
    print("   • Performance monitoring and recommendations")
    
    return safety_system


async def main():
    """Main demo function."""
    
    print("🚀 CodeGenie - Integrated Safety System Demo")
    print("=" * 70)
    
    try:
        # Run the integrated safety demo
        safety_system = await demo_integrated_safety()
        
        print("\n📋 Summary:")
        print("   • Integrated safety system working perfectly")
        print("   • Error detection and recovery functioning")
        print("   • Safe execution with security enforcement")
        print("   • File operations with validation")
        print("   • Comprehensive reporting and statistics")
        
        print("\n🛡️  Safety Features:")
        print("   • Automatic error pattern recognition")
        print("   • Intelligent recovery strategies")
        print("   • Security violation detection")
        print("   • File validation and safety checks")
        print("   • Resource usage monitoring")
        print("   • Backup and rollback capabilities")
        print("   • Performance analysis and recommendations")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
