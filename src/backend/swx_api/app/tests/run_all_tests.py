#!/usr/bin/env python3
"""
Run All Async Tests
------------------
Script to run all async tests with proper configuration.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run all async tests."""
    backend_dir = Path(__file__).parent.parent.parent.parent
    tests_dir = backend_dir / "swx_api" / "app" / "tests"
    
    print("🧪 Running All Async Tests for ŠKODA Skill Coach")
    print("=" * 60)
    
    # Run pytest with async support
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--asyncio-mode=auto",
        "--tb=short",
        "-x",  # Stop on first failure
        "--cov=swx_api",  # Coverage if pytest-cov is installed
        "--cov-report=term-missing",
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=backend_dir)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()

