#!/usr/bin/env python3
"""
Test runner script for SearchFace backend
"""
import subprocess
import sys
import os

def run_tests():
    """Run pytest with coverage"""
    print("Starting pytest test execution...")
    
    # Change to project root directory
    os.chdir('/home/shsk/git/SearchFace')
    
    # Run pytest with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        '-v',
        '--cov=src',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-fail-under=80',
        'tests/'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed or coverage threshold not met")
        
        return result.returncode
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)