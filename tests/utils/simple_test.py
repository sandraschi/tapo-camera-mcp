import sys
import os
import logging
from pathlib import Path

# Add src to path
src_dir = str(Path(__file__).parent.absolute() / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("=== Testing Imports ===")

# Test importing base_tool
try:
    from tapo_camera_mcp.tools.base_tool import register_tool, Tool, ToolCategory
    print("✅ Successfully imported from base_tool")
except ImportError as e:
    print(f"❌ Failed to import from base_tool: {e}")
    import traceback
    traceback.print_exc()

# Test importing tools/__init__.py
try:
    from tapo_camera_mcp.tools import register_tool, get_tool, get_all_tools, tools_registry
    print("✅ Successfully imported from tools/__init__.py")
    print(f"Number of registered tools: {len(tools_registry)}")
except ImportError as e:
    print(f"❌ Failed to import from tools/__init__.py: {e}")
    import traceback
    traceback.print_exc()

# Test importing tool modules
modules = [
    "tapo_camera_mcp.tools.camera",
    "tapo_camera_mcp.tools.system",
    "tapo_camera_mcp.tools.ptz",
    "tapo_camera_mcp.tools.media",
    "tapo_camera_mcp.tools.grafana"
]

print("\n=== Testing Tool Imports ===")
for module_name in modules:
    try:
        __import__(module_name)
        print(f"✅ Successfully imported {module_name}")
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        import traceback
        traceback.print_exc()

# Test tool registration
try:
    from tapo_camera_mcp.tools import get_all_tools, tools_registry
    tools = get_all_tools()
    print("\n=== Registered Tools ===")
    for tool in tools:
        print(f"- {tool.name}: {tool.__module__}.{tool.__name__}")
    print(f"Total tools registered: {len(tools)}")
except Exception as e:
    print(f"\n❌ Error getting registered tools: {e}")
    import traceback
    traceback.print_exc()
