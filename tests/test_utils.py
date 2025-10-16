"""
Test utilities for Tapo Camera MCP tests.
"""

from unittest.mock import MagicMock


class MockMcpMessage:
    """Mock for McpMessage class."""

    def __init__(self, content=None, **kwargs):
        self.content = content or {}
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockFastMCP:
    """Mock for FastMCP class."""

    def __init__(self):
        self.tools = {}
        self.message_handlers = {}

    def tool(self, name=None, **kwargs):
        """Mock for the @tool decorator."""

        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = {"func": func, "name": tool_name, **kwargs}
            return func

        return decorator

    def on_message(self, message_type):
        """Mock for the on_message decorator."""

        def decorator(func):
            self.message_handlers[message_type] = func
            return func

        return decorator

    async def call_tool(self, name, params):
        """Call a tool by name with the given parameters."""
        if name not in self.tools:
            raise ValueError(f"No such tool: {name}")

        tool = self.tools[name]
        return await tool["func"](params)


def create_mock_camera():
    """Create a mock Tapo camera for testing."""
    mock_camera = MagicMock()
    mock_camera.host = "192.168.1.100"

    # Mock basic info
    mock_camera.getBasicInfo = MagicMock(
        return_value={
            "device_info": {"device_model": "Tapo C200"},
            "firmware_version": "1.0.0",
            "mac": "00:11:22:33:44:55",
        }
    )

    # Mock PTZ methods
    mock_camera.moveRight = MagicMock()
    mock_camera.moveLeft = MagicMock()
    mock_camera.moveUp = MagicMock()
    mock_camera.moveDown = MagicMock()
    mock_camera.moveStop = MagicMock()

    # Mock other methods
    mock_camera.setMotionDetection = MagicMock()
    mock_camera.setLED = MagicMock()
    mock_camera.setPrivacyMode = MagicMock()
    mock_camera.reboot = MagicMock()

    return mock_camera
