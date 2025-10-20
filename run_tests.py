#!/usr/bin/env python3
"""
Test runner script for the notification bot
Usage: python run_tests.py [test_type]
Test types: unit, integration, all (default)
"""
import subprocess
import sys
import os

def run_tests(test_type="all"):
    """Run tests based on type"""
    
    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install test dependencies if needed
    print("Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                  check=True, capture_output=True)
    
    print(f"Running {test_type} tests...")
    
    if test_type == "unit":
        cmd = ["python", "-m", "pytest", "tests/test_binance_api.py", "tests/test_telegram.py", 
               "tests/test_message_processing.py", "-v"]
    elif test_type == "integration": 
        cmd = ["python", "-m", "pytest", "tests/test_integration.py", "-v"]
    else:  # all
        cmd = ["python", "-m", "pytest", "tests/", "-v"]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def main():
    """Main test runner"""
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if test_type not in ["unit", "integration", "all"]:
        print("Invalid test type. Use: unit, integration, or all")
        sys.exit(1)
    
    print("Notification Bot Test Suite")
    print("=" * 40)
    
    success = run_tests(test_type)
    
    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()