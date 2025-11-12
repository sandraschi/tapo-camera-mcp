import logging
import sys
from pathlib import Path

# Add src to path
src_dir = str(Path(__file__).parent.absolute() / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# Test importing base_tool
try:
    from tapo_camera_mcp.tools.base_tool import register_tool  # noqa: F401

except ImportError:
    import traceback

    traceback.print_exc()

# Test importing tools/__init__.py
try:
    from tapo_camera_mcp.tools import get_all_tools

except ImportError:
    import traceback

    traceback.print_exc()

# Test importing tool modules
modules = [
    "tapo_camera_mcp.tools.camera",
    "tapo_camera_mcp.tools.system",
    "tapo_camera_mcp.tools.ptz",
    "tapo_camera_mcp.tools.media",
    "tapo_camera_mcp.tools.grafana",
]

for module_name in modules:
    try:
        __import__(module_name)
    except ImportError:
        import traceback

        traceback.print_exc()

# Test tool registration
try:
    from tapo_camera_mcp.tools import get_all_tools

    tools = get_all_tools()
    for _tool in tools:
        pass
except Exception:
    import traceback

    traceback.print_exc()
