"""
Test script to verify our updated imports.
"""

import sys
from pathlib import Path


def test_import(module_name):
    """Test importing a module and print the result."""
    try:
        __import__(module_name)
        print(f"✅ Successfully imported: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error importing {module_name}: {e}")
        return False


def main():
    """Main function to test imports."""
    # Add the src directory to the Python path
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    print(f"Python path: {sys.path}\n")

    # List of modules to test
    modules_to_test = [
        "tapo_camera_mcp.tools.camera",
        "tapo_camera_mcp.tools.system",
        "tapo_camera_mcp.tools.ptz",
        "tapo_camera_mcp.tools.media",
        "tapo_camera_mcp.tools.grafana",
    ]

    # Test each module
    results = {}
    for module in modules_to_test:
        results[module] = test_import(module)

    # Print summary
    print("\n=== Import Test Summary ===")
    for module, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {module}")

    # Return non-zero exit code if any import failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
