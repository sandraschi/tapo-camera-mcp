import sys
import os

print(f"Current Working Directory: {os.getcwd()}")
print(f"Python Path: {sys.path}")

try:
    import tapo_camera_mcp

    print("Successfully imported tapo_camera_mcp")
    print(f"Package location: {tapo_camera_mcp.__file__}")
except ImportError as e:
    print(f"Failed to import tapo_camera_mcp: {e}")

try:
    from tapo_camera_mcp.integrations.vbot_client import VbotClient

    print("Successfully imported VbotClient")
except ImportError as e:
    print(f"Failed to import VbotClient: {e}")
