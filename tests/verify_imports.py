"""
Verify imports for Tapo Camera MCP tools.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.absolute() / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# List of modules to test
modules_to_test = [
    "tapo_camera_mcp.tools.camera",
    "tapo_camera_mcp.tools.system",
    "tapo_camera_mcp.tools.ptz",
    "tapo_camera_mcp.tools.media",
    "tapo_camera_mcp.tools.grafana",
]

# Test each module
for module_name in modules_to_test:
    try:
        print(f"Testing import: {module_name}")
        __import__(module_name, fromlist=["*"])
        print(f"✅ Successfully imported {module_name}")
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        import traceback

        traceback.print_exc()
    except Exception as e:
        print(f"⚠️ Error importing {module_name}: {e}")
        import traceback

        traceback.print_exc()
    print("-" * 80)
