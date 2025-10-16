#!/usr/bin/env python3
"""
Tests for tools discovery and registration system.
"""

import sys
import os

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_tools_discovery():
    """Test tools discovery functionality."""
    try:
        from tapo_camera_mcp.tools.discovery import discover_tools

        # Test discovering tools from the tools package
        tools = discover_tools("tapo_camera_mcp.tools")

        # Should find multiple tools
        assert len(tools) > 0, "Should discover at least one tool"

        # Check that discovered tools are classes
        for tool_cls in tools:
            assert hasattr(tool_cls, "__name__"), f"Tool {tool_cls} should be a class"
            assert "Tool" in tool_cls.__name__, "Tool class name should contain 'Tool'"

        print(f"✅ Tools discovery found {len(tools)} tools")
        return True
    except Exception as e:
        print(f"❌ Tools discovery test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_registry():
    """Test tool registration system."""
    try:
        from tapo_camera_mcp.tools.base_tool import (
            register_tool,
            get_all_tools,
            get_tool,
        )

        # Test initial state (should be empty)
        all_tools = get_all_tools()
        assert len(all_tools) == 0, "Registry should start empty"

        # Test registering a mock tool
        class MockTool:
            class Meta:
                name = "mock_tool"

        register_tool(MockTool)

        # Test that tool is registered
        all_tools = get_all_tools()
        assert len(all_tools) == 1, "Should have one registered tool"

        # Test getting tool by name
        tool = get_tool("mock_tool")
        assert tool is not None, "Should be able to get tool by name"

        print("✅ Tool registry test passed")
        return True
    except Exception as e:
        print(f"❌ Tool registry test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_base_tool_structure():
    """Test base tool class structure."""
    try:
        from tapo_camera_mcp.tools.base_tool import ToolResult, ToolCategory

        # Test ToolCategory enum
        categories = list(ToolCategory)
        expected_categories = [
            "Camera",
            "System",
            "Media",
            "PTZ",
            "Configuration",
            "Utility",
            "Analysis",
            "Security",
        ]

        for category in categories:
            assert category.value in expected_categories, (
                f"Unexpected category: {category.value}"
            )

        print(f"✅ Tool categories: {[c.value for c in categories]}")

        # Test ToolResult creation
        result = ToolResult(content="test", is_error=False)
        assert result.content == "test"
        assert result.is_error is False

        print("✅ Base tool structure test passed")
        return True
    except Exception as e:
        print(f"❌ Base tool structure test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_decorator():
    """Test tool decorator functionality."""
    try:
        from tapo_camera_mcp.tools.base_tool import tool

        # Test decorator creation
        @tool(name="test_decorator_tool")
        class TestDecoratorTool:
            class Meta:
                pass

            async def execute(self):
                return {"result": "test"}

        # Check that decorator added metadata
        assert hasattr(TestDecoratorTool, "Meta"), "Tool should have Meta class"
        assert hasattr(TestDecoratorTool.Meta, "name"), "Meta should have name"
        assert TestDecoratorTool.Meta.name == "test_decorator_tool", (
            "Name should be set correctly"
        )

        print("✅ Tool decorator test passed")
        return True
    except Exception as e:
        print(f"❌ Tool decorator test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_definition():
    """Test tool definition generation."""
    try:
        from tapo_camera_mcp.tools.base_tool import BaseTool

        # Create a test tool class
        class TestTool(BaseTool):
            class Meta:
                name = "test_tool"
                description = "Test tool description"
                category = "Utility"

            async def execute(self):
                return {"result": "test"}

        # Test get_definition method
        definition = TestTool.get_definition()
        assert definition.name == "test_tool"
        assert definition.description == "Test tool description"
        assert definition.category.value == "Utility"

        print("✅ Tool definition test passed")
        return True
    except Exception as e:
        print(f"❌ Tool definition test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_discovery_error_handling():
    """Test error handling in tool discovery."""
    try:
        from tapo_camera_mcp.tools.discovery import discover_tools

        # Test discovery with non-existent package
        tools = discover_tools("non.existent.package")
        assert tools == [], "Should return empty list for non-existent package"

        # Test discovery with invalid package name
        tools = discover_tools("")
        assert tools == [], "Should return empty list for empty package"

        print("✅ Tool discovery error handling test passed")
        return True
    except Exception as e:
        print(f"❌ Tool discovery error handling test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_validation_function():
    """Test the is_tool_class validation function."""
    try:
        from tapo_camera_mcp.tools.discovery import is_tool_class
        from tapo_camera_mcp.tools.base_tool import BaseTool

        # Test valid tool class
        class ValidTool(BaseTool):
            class Meta:
                name = "valid_tool"
                category = "Utility"

            async def execute(self, **kwargs):
                return {"result": "valid"}

        assert is_tool_class(ValidTool), (
            "ValidTool should be recognized as a tool class"
        )

        # Test invalid cases
        class NotATool:
            pass

        assert not is_tool_class(NotATool), (
            "NotATool should not be recognized as a tool class"
        )
        assert not is_tool_class(BaseTool), (
            "BaseTool itself should not be recognized as a tool class"
        )
        assert not is_tool_class("not a class"), (
            "String should not be recognized as a tool class"
        )

        print("✅ Tool validation function test passed")
        return True
    except Exception as e:
        print(f"❌ Tool validation function test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_metadata_completeness():
    """Test that discovered tools have complete metadata."""
    try:
        from tapo_camera_mcp.tools.discovery import discover_tools

        # Discover all tools
        all_tools = discover_tools("tapo_camera_mcp.tools")

        # Test that tools have required metadata
        for tool_cls in all_tools:
            assert hasattr(tool_cls, "Meta"), (
                f"Tool {tool_cls.__name__} missing Meta class"
            )
            meta = tool_cls.Meta

            # Required metadata fields
            required_fields = ["name", "category"]
            for field in required_fields:
                assert hasattr(meta, field), (
                    f"Tool {tool_cls.__name__} missing {field} in Meta"
                )
                value = getattr(meta, field)
                assert value is not None, f"Tool {tool_cls.__name__} {field} is None"
                if field == "name":
                    assert isinstance(value, str), (
                        f"Tool {tool_cls.__name__} name should be string"
                    )
                    assert len(value) > 0, (
                        f"Tool {tool_cls.__name__} name should not be empty"
                    )

        print(
            f"✅ Tool metadata completeness test passed - validated {len(all_tools)} tools"
        )
        return True
    except Exception as e:
        print(f"❌ Tool metadata completeness test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_system_tools_structure():
    """Test system tools structure and metadata."""
    try:
        from tapo_camera_mcp.tools.discovery import discover_tools

        # Discover system tools
        all_tools = discover_tools("tapo_camera_mcp.tools")

        # Find system tools (those with 'system' in their module name or category)
        system_tools = [
            tool for tool in all_tools if "system" in tool.__module__.lower()
        ]

        # We should have at least a few system tools
        assert len(system_tools) > 0, "Should find at least some system tools"

        # Test that system tools have proper metadata
        for tool_cls in system_tools[:3]:  # Test first 3
            assert hasattr(tool_cls, "Meta"), (
                f"Tool {tool_cls.__name__} missing Meta class"
            )
            meta = tool_cls.Meta
            assert hasattr(meta, "name"), (
                f"Tool {tool_cls.__name__} missing name in Meta"
            )
            assert hasattr(meta, "category"), (
                f"Tool {tool_cls.__name__} missing category in Meta"
            )

        print(
            f"✅ System tools structure test passed - found {len(system_tools)} system tools"
        )
        return True
    except Exception as e:
        print(f"❌ System tools structure test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_tools_discovery,
        test_tool_registry,
        test_base_tool_structure,
        test_tool_decorator,
        test_tool_definition,
        test_tool_categories,
        test_tool_discovery_error_handling,
        test_tool_validation_function,
        test_tool_metadata_completeness,
        test_system_tools_structure,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tools discovery tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tools discovery tests failed")
        sys.exit(1)
