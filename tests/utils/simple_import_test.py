import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Python path:", sys.path)

# Add src to path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
    print("\nAdded to path:", src_dir)

print("\nAttempting to import base_tool...")
try:
    from tapo_camera_mcp.tools import base_tool

    print("✅ Successfully imported base_tool")
    print("base_tool location:", base_tool.__file__)

    # Check if register_tool exists
    if hasattr(base_tool, "register_tool"):
        print("✅ register_tool found in base_tool")
    else:
        print("❌ register_tool NOT found in base_tool")

    # Check if tools_registry exists
    if hasattr(base_tool, "tools_registry"):
        print(f"✅ tools_registry found with {len(base_tool.tools_registry)} tools")
    else:
        print("❌ tools_registry NOT found in base_tool")

except ImportError as e:
    print("❌ Failed to import base_tool:", e)
    import traceback

    traceback.print_exc()
