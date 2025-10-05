#!/usr/bin/env python3
"""
Demo script showcasing error detection and recovery capabilities.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.config import Config
from codegenie.utils.error_detector import ErrorDetector, DetectedError
from codegenie.utils.error_recovery import ErrorRecovery
from codegenie.utils.safe_executor import SafeExecutor, ExecutionContext
from codegenie.utils.enhanced_file_ops import EnhancedFileOperations

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_error_detection():
    """Demonstrate error detection capabilities."""
    
    print("\n" + "="*60)
    print("🔍 ERROR DETECTION DEMO")
    print("="*60)
    
    # Initialize error detector
    error_detector = ErrorDetector()
    
    # Test various error outputs
    test_errors = [
        "ImportError: No module named 'nonexistent_module'",
        "SyntaxError: invalid syntax (<unknown>, line 1)",
        "NameError: name 'undefined_variable' is not defined",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "FileNotFoundError: [Errno 2] No such file or directory: 'missing_file.py'",
        "PermissionError: [Errno 13] Permission denied: 'protected_file.txt'",
        "IndentationError: expected an indented block (<unknown>, line 2)",
        "AttributeError: 'str' object has no attribute 'append'",
        "ValueError: invalid literal for int() with base 10: 'abc'",
        "KeyError: 'missing_key'",
    ]
    
    print("\n📋 Testing Error Detection:")
    for i, error_output in enumerate(test_errors, 1):
        print(f"\n{i}. Testing: {error_output}")
        
        detected_errors = error_detector.detect_errors(error_output)
        
        if detected_errors:
            for error in detected_errors:
                print(f"   ✅ Detected: {error.error_type}")
                print(f"   📊 Severity: {error.severity}")
                print(f"   🏷️  Category: {error.category}")
                print(f"   🎯 Confidence: {error.confidence:.2f}")
                if error.suggested_fixes:
                    print(f"   💡 Suggested fixes: {', '.join(error.suggested_fixes)}")
        else:
            print("   ❌ No errors detected")
    
    # Show error analysis
    print("\n📈 Error Analysis:")
    trends = error_detector.analyze_error_trends()
    print(f"   Total errors detected: {trends.get('total_errors', 0)}")
    print(f"   Category distribution: {trends.get('category_distribution', {})}")
    print(f"   Most common errors: {trends.get('most_common_errors', [])}")
    
    # Show recommendations
    print("\n💡 Recommendations:")
    recommendations = error_detector.get_error_recommendations()
    for rec in recommendations:
        print(f"   • {rec}")
    
    return error_detector


async def demo_error_recovery():
    """Demonstrate error recovery capabilities."""
    
    print("\n" + "="*60)
    print("🔧 ERROR RECOVERY DEMO")
    print("="*60)
    
    # Initialize error recovery
    config = Config()
    error_recovery = ErrorRecovery(config)
    
    # Test recovery scenarios
    test_scenarios = [
        {
            "name": "Python Import Error",
            "error": DetectedError(
                error_type="python_import_error",
                message="ImportError: No module named 'requests'",
                severity="error",
                category="import",
                confidence=0.9,
                suggested_fixes=["Install missing package: pip install requests"],
            ),
            "context": {"package_name": "requests"},
        },
        {
            "name": "Python Syntax Error",
            "error": DetectedError(
                error_type="python_syntax_error",
                message="SyntaxError: invalid syntax",
                file_path="test.py",
                line_number=5,
                severity="error",
                category="syntax",
                confidence=0.8,
            ),
            "context": {"file_path": "test.py"},
        },
        {
            "name": "Python Name Error",
            "error": DetectedError(
                error_type="python_name_error",
                message="NameError: name 'undefined_var' is not defined",
                file_path="test.py",
                line_number=10,
                severity="error",
                category="runtime",
                confidence=0.9,
            ),
            "context": {"file_path": "test.py"},
        },
        {
            "name": "Command Not Found",
            "error": DetectedError(
                error_type="command_not_found",
                message="command not found: git",
                severity="error",
                category="runtime",
                confidence=0.9,
            ),
            "context": {"command_name": "git"},
        },
    ]
    
    print("\n🔄 Testing Error Recovery:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Scenario: {scenario['name']}")
        print(f"   Error: {scenario['error'].message}")
        
        # Attempt recovery
        recovery_results = await error_recovery.recover_from_error(
            scenario['error'],
            scenario['context']
        )
        
        if recovery_results:
            for result in recovery_results:
                status = "✅ Success" if result.success else "❌ Failed"
                print(f"   {status}: {result.action.description}")
                if result.output:
                    print(f"   Output: {result.output[:100]}...")
                if result.error_message:
                    print(f"   Error: {result.error_message}")
        else:
            print("   ⚠️  No recovery strategies available")
    
    # Show recovery statistics
    print("\n📊 Recovery Statistics:")
    stats = error_recovery.get_recovery_statistics()
    print(f"   Total attempts: {stats.get('total_attempts', 0)}")
    print(f"   Successful recoveries: {stats.get('successful_recoveries', 0)}")
    print(f"   Success rate: {stats.get('success_rate', 0):.2%}")
    print(f"   Action type distribution: {stats.get('action_type_distribution', {})}")
    
    return error_recovery


async def demo_safe_execution():
    """Demonstrate safe execution capabilities."""
    
    print("\n" + "="*60)
    print("🛡️  SAFE EXECUTION DEMO")
    print("="*60)
    
    # Initialize safe executor
    config = Config()
    safe_executor = SafeExecutor(config)
    
    # Test safe execution scenarios
    test_commands = [
        {
            "name": "Safe Python Command",
            "command": "python -c 'print(\"Hello, Safe World!\")'",
            "description": "Execute a safe Python command",
        },
        {
            "name": "Safe File Operation",
            "command": "echo 'Test content' > test_file.txt",
            "description": "Create a test file safely",
        },
        {
            "name": "Safe Directory Listing",
            "command": "ls -la",
            "description": "List directory contents safely",
        },
        {
            "name": "Blocked Dangerous Command",
            "command": "rm -rf /",
            "description": "Attempt to execute a dangerous command (should be blocked)",
        },
        {
            "name": "Blocked System Command",
            "command": "sudo shutdown -h now",
            "description": "Attempt to execute a system command (should be blocked)",
        },
    ]
    
    print("\n🔒 Testing Safe Execution:")
    for i, test in enumerate(test_commands, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Command: {test['command']}")
        print(f"   Description: {test['description']}")
        
        # Create execution context
        context = ExecutionContext(
            working_directory=Path.cwd(),
            timeout=30,
            max_output_size=1024,
        )
        
        # Execute command safely
        result = await safe_executor.execute_safe(test['command'], context)
        
        status = "✅ Success" if result.success else "❌ Failed"
        print(f"   Result: {status}")
        print(f"   Exit code: {result.exit_code}")
        
        if result.security_violations:
            print(f"   🚨 Security violations: {', '.join(result.security_violations)}")
        
        if result.stdout:
            print(f"   Output: {result.stdout[:200]}...")
        
        if result.stderr:
            print(f"   Error: {result.stderr[:200]}...")
    
    # Test Python code execution
    print("\n🐍 Testing Python Code Execution:")
    python_code = """
import sys
print(f"Python version: {sys.version}")
print("Safe Python execution working!")
"""
    
    result = await safe_executor.execute_python_code(python_code)
    status = "✅ Success" if result.success else "❌ Failed"
    print(f"   Result: {status}")
    if result.stdout:
        print(f"   Output: {result.stdout}")
    
    # Show execution statistics
    print("\n📊 Execution Statistics:")
    stats = safe_executor.get_execution_statistics()
    print(f"   Total executions: {stats.get('total_executions', 0)}")
    print(f"   Successful executions: {stats.get('successful_executions', 0)}")
    print(f"   Failed executions: {stats.get('failed_executions', 0)}")
    print(f"   Success rate: {stats.get('success_rate', 0):.2%}")
    print(f"   Security violations: {stats.get('security_violations', 0)}")
    
    return safe_executor


async def demo_enhanced_file_operations():
    """Demonstrate enhanced file operations."""
    
    print("\n" + "="*60)
    print("📁 ENHANCED FILE OPERATIONS DEMO")
    print("="*60)
    
    # Initialize enhanced file operations
    config = Config()
    file_ops = EnhancedFileOperations(config)
    
    # Test file validation
    print("\n🔍 Testing File Validation:")
    
    # Create test files
    test_files = {
        "valid_python.py": """
import os
import sys

def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""",
        "invalid_python.py": """
import os
import sys

def hello_world(
    print("Hello, World!")  # Missing closing parenthesis

if __name__ == "__main__":
    hello_world()
""",
        "dangerous_script.py": """
import os
import subprocess

# This is dangerous code
os.system("rm -rf /")
subprocess.call(["format", "C:"])
""",
        "config.json": """
{
    "name": "test-project",
    "version": "1.0.0",
    "dependencies": {
        "requests": "^2.25.0"
    }
}
""",
        "invalid_json.json": """
{
    "name": "test-project",
    "version": "1.0.0",
    "dependencies": {
        "requests": "^2.25.0"
    }  // Missing closing brace
}
""",
    }
    
    for filename, content in test_files.items():
        print(f"\n📄 Testing file: {filename}")
        
        # Create temporary file
        temp_file = Path(f"temp_{filename}")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Validate file
        validation_result = file_ops.validate_file(temp_file)
        
        status = "✅ Valid" if validation_result.is_valid else "❌ Invalid"
        print(f"   Status: {status}")
        print(f"   File type: {validation_result.file_type}")
        print(f"   Size: {validation_result.size} bytes")
        print(f"   Checksum: {validation_result.checksum[:16]}...")
        
        if validation_result.issues:
            print(f"   Issues: {', '.join(validation_result.issues)}")
        
        if validation_result.warnings:
            print(f"   Warnings: {', '.join(validation_result.warnings)}")
        
        # Clean up
        temp_file.unlink()
    
    # Test safe file operations
    print("\n🔒 Testing Safe File Operations:")
    
    # Test safe file creation
    test_content = """
# This is a test Python file
import os
import sys

def main():
    print("Hello from safe file creation!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
    
    success, message, validation = file_ops.safe_create_file(
        "test_safe_file.py",
        test_content,
        backup=True,
        validate=True
    )
    
    status = "✅ Success" if success else "❌ Failed"
    print(f"   Safe file creation: {status}")
    print(f"   Message: {message}")
    if validation:
        print(f"   Validation: {'Valid' if validation.is_valid else 'Invalid'}")
    
    # Test safe file modification
    if success:
        modified_content = test_content.replace("Hello from safe file creation!", "Hello from safe file modification!")
        
        success, message, validation = file_ops.safe_modify_file(
            "test_safe_file.py",
            modified_content,
            backup=True,
            validate=True
        )
        
        status = "✅ Success" if success else "❌ Failed"
        print(f"   Safe file modification: {status}")
        print(f"   Message: {message}")
    
    # Test safe file deletion
    if success:
        success, message = file_ops.safe_delete_file("test_safe_file.py", backup=True)
        
        status = "✅ Success" if success else "❌ Failed"
        print(f"   Safe file deletion: {status}")
        print(f"   Message: {message}")
    
    # Show file operations statistics
    print("\n📊 File Operations Statistics:")
    stats = file_ops.get_statistics()
    print(f"   Total operations: {stats.get('total_operations', 0)}")
    print(f"   Operation counts: {stats.get('operation_counts', {})}")
    print(f"   Backup files: {stats.get('backup_files', 0)}")
    
    return file_ops


async def main():
    """Main demo function."""
    
    print("🚀 CodeGenie - Error Detection & Recovery Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        error_detector = await demo_error_detection()
        error_recovery = await demo_error_recovery()
        safe_executor = await demo_safe_execution()
        file_ops = await demo_enhanced_file_operations()
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print("\n📋 Summary:")
        print("   • Error detection system working")
        print("   • Error recovery system working")
        print("   • Safe execution system working")
        print("   • Enhanced file operations working")
        
        print("\n🎯 Key Features Demonstrated:")
        print("   • Automatic error pattern recognition")
        print("   • Intelligent error recovery strategies")
        print("   • Safe command execution with security checks")
        print("   • File validation and safe operations")
        print("   • Backup and rollback capabilities")
        print("   • Resource usage monitoring")
        print("   • Security violation detection")
        
        # Cleanup
        error_recovery.cleanup()
        safe_executor.cleanup()
        file_ops.cleanup()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
