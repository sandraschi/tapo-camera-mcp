"""
Test module imports for the Tapo Camera MCP server.
"""

import os
import sys

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        # Test core imports
        from tapo_camera_mcp import TapoCameraMCP
        from tapo_camera_mcp.core.models import TapoCameraConfig
        from tapo_camera_mcp.core.server import TapoCameraServer
        from tapo_camera_mcp.exceptions import TapoCameraError

        print("✅ SUCCESS: All core modules imported successfully")
        return True

    except ImportError as e:
        print(f"❌ ERROR: Import failed - {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error - {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    if not success:
        sys.exit(1)
