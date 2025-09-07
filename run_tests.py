#!/usr/bin/env python3
"""
Test runner for oxidize-xml.

This script helps run different types of tests and provides clear output.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FAILED (exit code {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"\n❌ {description} - FAILED (command not found)")
        return False


def check_package_installed():
    """Check if the package is properly installed."""
    try:
        import oxidize_xml
        print("✅ Package import successful")
        return True
    except ImportError as e:
        print(f"❌ Package import failed: {e}")
        print("💡 Run './build.sh' to build and install the package")
        return False


def check_basic_functionality():
    """Check if basic XML parsing functionality works."""
    try:
        import oxidize_xml
        # Test basic XML parsing
        xml_content = '<?xml version="1.0"?><root><item id="1">test</item></root>'
        result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
        if result and "test" in result:
            print("✅ Basic XML parsing functionality working")
            return True
        else:
            print("❌ Basic XML parsing failed")
            return False
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for oxidize-xml")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--check", action="store_true", help="Check setup without running tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    
    args = parser.parse_args()
    
    # Default to all tests if no specific type specified
    if not (args.unit or args.integration or args.performance or args.benchmark or args.check):
        args.all = True
    
    print("🧪 oxidize-xml Test Runner")
    print("=" * 60)
    
    # Check package installation
    print("\n📦 Checking package installation...")
    if not check_package_installed():
        print("\n❌ Package not properly installed. Please run './build.sh' first.")
        return 1
    
    # Check basic functionality
    print("\n🔧 Checking basic functionality...")
    if not check_basic_functionality():
        print("\n❌ Basic functionality check failed. Package may not be working correctly.")
        return 1
    
    if args.check:
        print("\n✅ Setup check complete!")
        return 0
    
    # Build pytest command
    pytest_args = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")
    
    # Add coverage if requested
    if args.coverage:
        pytest_args.extend(["--cov=oxidize_xml", "--cov-report=html", "--cov-report=term"])
    
    # Add test discovery and reporting
    pytest_args.extend(["--tb=short", "--no-header"])
    
    success = True
    
    # Run unit tests
    if args.unit or args.all:
        unit_cmd = pytest_args + ["tests/unit/"]
        if not run_command(unit_cmd, "Unit Tests"):
            success = False
    
    # Run integration tests
    if args.integration or args.all:
        integration_cmd = pytest_args + ["tests/integration/"]
        if not run_command(integration_cmd, "Integration Tests"):
            success = False
    
    # Run performance tests
    if args.performance or args.all:
        performance_cmd = pytest_args + ["tests/performance/", "-m", "not benchmark"]
        if not run_command(performance_cmd, "Performance Tests"):
            success = False
    
    # Run benchmark tests
    if args.benchmark:
        benchmark_cmd = pytest_args + ["tests/performance/", "-m", "benchmark", "--benchmark-only"]
        if not run_command(benchmark_cmd, "Benchmark Tests"):
            success = False
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
        print(f"{'='*60}")
        return 0
    else:
        print("💥 Some tests failed!")
        print(f"{'='*60}")
        print("💡 Tips:")
        print("   - Run with --verbose for more details")
        print("   - Check specific test categories: --unit, --integration, --performance")
        print("   - Run './build.sh' if you see import errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
