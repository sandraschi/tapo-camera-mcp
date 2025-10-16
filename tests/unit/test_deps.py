#!/usr/bin/env python3
"""
Test script to identify dependency installation issues
"""

import subprocess
import sys
import tempfile


def test_dependency(dep_name, dep_spec):
    """Test if a dependency can be installed."""
    print(f"\n🧪 Testing {dep_name} ({dep_spec})...")

    # First check if it's already installed
    check_cmd = [sys.executable, "-m", "pip", "show", dep_name]
    result = subprocess.run(check_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {dep_name} is already installed")
        lines = result.stdout.split("\n")
        for line in lines:
            if line.startswith("Version:"):
                print(f"   Current version: {line.split(':')[1].strip()}")
                break
    else:
        print(f"❌ {dep_name} is not installed")

    # Test installation to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        install_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            temp_dir,
            dep_spec,
        ]

        print(f"   Testing installation: {' '.join(install_cmd)}")
        result = subprocess.run(install_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {dep_spec} can be installed successfully")
            return True
        else:
            print(f"❌ {dep_spec} installation failed")
            print(f"   Error: {result.stderr}")
            if result.stdout:
                print(f"   Output: {result.stdout}")
            return False


def main():
    """Test all dependencies."""
    print("🔧 Testing tapo-camera-mcp dependencies...")

    dependencies = [
        ("pytapo", "pytapo>=3.3.0"),
        ("fastmcp", "fastmcp>=2.10.0"),
        ("aiohttp", "aiohttp>=3.8.0"),
        ("python-dotenv", "python-dotenv>=0.19.0"),
        ("pydantic", "pydantic>=1.9.0"),
    ]

    failed_deps = []

    for dep_name, dep_spec in dependencies:
        success = test_dependency(dep_name, dep_spec)
        if not success:
            failed_deps.append(dep_spec)

    print("\n📊 Results:")
    print(f"✅ Successful: {len(dependencies) - len(failed_deps)}/{len(dependencies)}")
    print(f"❌ Failed: {len(failed_deps)}/{len(dependencies)}")

    if failed_deps:
        print("\n💥 Failed dependencies:")
        for dep in failed_deps:
            print(f"   - {dep}")
        return 1
    else:
        print("\n🎯 All dependencies can be installed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
