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

    # Test 1: Check pip version
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"], check=False, capture_output=True, text=True
    )
    if result.returncode == 0:
        pass
    else:
        return False

    # Test 2: Try installing a simple package to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [sys.executable, "-m", "pip", "install", "--target", temp_dir, "requests"]

        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        if result.returncode == 0:
            # Check what was installed
            temp_path = Path(temp_dir)
            list(temp_path.iterdir())
        else:
            return False

    # Test 3: Try installing our specific dependencies one by one
    dependencies = [
        "python-dotenv>=0.19.0",  # Start with simple ones
        "pydantic>=1.9.0",
        "aiohttp>=3.8.0",
        "fastmcp>=2.10.0",
        "pytapo>=3.3.0",
    ]

    for dep in dependencies:
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = [sys.executable, "-m", "pip", "install", "--target", temp_dir, dep]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)

            if result.returncode == 0:
                pass
            else:
                return False

    return True


if __name__ == "__main__":
    success = test_basic_pip_install()
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)
