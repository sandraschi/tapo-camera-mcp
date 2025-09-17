#!/usr/bin/env python3
"""
Minimal test to identify the exact pip install issue
"""
import subprocess
import sys
import tempfile
from pathlib import Path

def test_basic_pip_install():
    """Test basic pip install functionality."""
    print("🔧 Testing basic pip install functionality...")
    
    # Test 1: Check pip version
    print("\n1. Checking pip version...")
    result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Pip version: {result.stdout.strip()}")
    else:
        print(f"❌ Pip check failed: {result.stderr}")
        return False
    
    # Test 2: Try installing a simple package to temp directory
    print("\n2. Testing install to temp directory...")
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [sys.executable, "-m", "pip", "install", "--target", temp_dir, "requests"]
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Basic pip install --target works")
            # Check what was installed
            temp_path = Path(temp_dir)
            installed = list(temp_path.iterdir())
            print(f"   Installed {len(installed)} items: {[p.name for p in installed[:5]]}")
        else:
            print("❌ Basic pip install --target failed")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
    
    # Test 3: Try installing our specific dependencies one by one
    print("\n3. Testing our specific dependencies...")
    dependencies = [
        "python-dotenv>=0.19.0",  # Start with simple ones
        "pydantic>=1.9.0",
        "aiohttp>=3.8.0", 
        "fastmcp>=2.10.0",
        "pytapo>=3.3.0"
    ]
    
    for dep in dependencies:
        print(f"\n   Testing {dep}...")
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = [sys.executable, "-m", "pip", "install", "--target", temp_dir, dep]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {dep} - SUCCESS")
            else:
                print(f"   ❌ {dep} - FAILED")
                print(f"      stdout: {result.stdout}")
                print(f"      stderr: {result.stderr}")
                return False
    
    print("\n🎯 All tests passed! Pip install should work fine.")
    return True

if __name__ == "__main__":
    success = test_basic_pip_install()
    if not success:
        print("\n💥 Found the issue! Check the error messages above.")
        sys.exit(1)
    else:
        print("\n✅ All pip tests passed - the issue is elsewhere.")
        sys.exit(0)
