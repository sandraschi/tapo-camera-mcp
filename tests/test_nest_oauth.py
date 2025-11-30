"""
Tests for Nest Protect OAuth Integration

Tests the real Google Nest API integration:
- OAuth flow (start, complete, status)
- Real API vs mock data fallback
- Device operations
"""

import pytest


class TestNestOAuthActions:
    """Test Nest OAuth action definitions."""

    def test_oauth_actions_in_security_management(self):
        """Test that OAuth actions are defined in SECURITY_ACTIONS."""
        from tapo_camera_mcp.tools.portmanteau.security_management import (
            SECURITY_ACTIONS,
        )

        expected_oauth_actions = [
            "nest_oauth_start",
            "nest_oauth_complete",
            "nest_oauth_status",
        ]
        for action in expected_oauth_actions:
            assert action in SECURITY_ACTIONS, f"Missing OAuth action: {action}"

        print("\nOAuth actions defined:")
        for action in expected_oauth_actions:
            print(f"  {action}: {SECURITY_ACTIONS[action]}")


class TestNestClient:
    """Test NestClient functionality."""

    def test_nest_client_import(self):
        """Test that NestClient can be imported."""
        from tapo_camera_mcp.integrations.nest_client import (
            NestClient,
            get_nest_client,
        )

        assert NestClient is not None
        assert get_nest_client is not None

    def test_get_oauth_url(self):
        """Test OAuth URL generation."""
        from tapo_camera_mcp.integrations.nest_client import NestClient

        url = NestClient.get_oauth_url()

        assert url is not None
        assert "accounts.google.com" in url
        assert "oauth2" in url
        assert "client_id" in url

        print("\nOAuth URL generated (first 100 chars):")
        print(f"  {url[:100]}...")


class TestSecurityManagementNestIntegration:
    """Test Nest operations via security_management tool."""

    @pytest.mark.asyncio
    async def test_nest_oauth_start(self):
        """Test nest_oauth_start action."""
        from fastmcp import FastMCP

        from tapo_camera_mcp.tools.portmanteau.security_management import (
            register_security_management_tool,
        )

        mcp = FastMCP("test")
        register_security_management_tool(mcp)

        tool = mcp._tool_manager._tools["security_management"]
        result = await tool.fn(action="nest_oauth_start")

        assert result["success"] is True
        assert "data" in result

        data = result["data"]
        assert "oauth_url" in data
        assert "instructions" in data
        assert len(data["instructions"]) >= 4

        print("\nOAuth Start Response:")
        print(f"  URL present: {bool(data['oauth_url'])}")
        print(f"  Instructions: {len(data['instructions'])} steps")

    @pytest.mark.asyncio
    async def test_nest_oauth_status_unauthenticated(self):
        """Test nest_oauth_status when not authenticated."""
        from fastmcp import FastMCP

        from tapo_camera_mcp.tools.portmanteau.security_management import (
            register_security_management_tool,
        )

        mcp = FastMCP("test")
        register_security_management_tool(mcp)

        tool = mcp._tool_manager._tools["security_management"]
        result = await tool.fn(action="nest_oauth_status")

        assert result["success"] is True
        assert "data" in result

        data = result["data"]
        # When no token cached, should show as not authenticated
        assert "authenticated" in data

        print("\nOAuth Status Response:")
        print(f"  Authenticated: {data['authenticated']}")
        print(f"  Using Real API: {data.get('using_real_api', False)}")

    @pytest.mark.asyncio
    async def test_nest_status_fallback_to_mock(self):
        """Test nest_status falls back to mock when not authenticated."""
        from fastmcp import FastMCP

        from tapo_camera_mcp.tools.portmanteau.security_management import (
            register_security_management_tool,
        )

        mcp = FastMCP("test")
        register_security_management_tool(mcp)

        tool = mcp._tool_manager._tools["security_management"]
        result = await tool.fn(action="nest_status")

        assert result["success"] is True
        assert "data" in result

        data = result["data"]
        # Should indicate mock data when not authenticated
        if not data.get("using_real_api", False):
            assert "note" in data
            assert "mock" in data["note"].lower() or "oauth" in data["note"].lower()

        print("\nNest Status Response:")
        print(f"  Using Real API: {data.get('using_real_api', False)}")
        print(f"  Has devices: {'devices' in data}")


class TestNestOAuthComplete:
    """Test OAuth completion (requires manual code)."""

    @pytest.mark.asyncio
    async def test_oauth_complete_requires_code(self):
        """Test that oauth_complete fails without code."""
        from fastmcp import FastMCP

        from tapo_camera_mcp.tools.portmanteau.security_management import (
            register_security_management_tool,
        )

        mcp = FastMCP("test")
        register_security_management_tool(mcp)

        tool = mcp._tool_manager._tools["security_management"]
        result = await tool.fn(action="nest_oauth_complete")

        assert result["success"] is False
        assert "error" in result
        assert "oauth_code" in result["error"].lower()

        print("\nOAuth Complete without code:")
        print(f"  Error (expected): {result['error']}")


if __name__ == "__main__":
    import asyncio

    print("=" * 60)
    print("NEST OAUTH INTEGRATION - TEST HARNESS")
    print("=" * 60)

    # Sync tests
    test1 = TestNestOAuthActions()
    test1.test_oauth_actions_in_security_management()

    test2 = TestNestClient()
    test2.test_nest_client_import()
    test2.test_get_oauth_url()

    # Async tests
    print("\n" + "-" * 60)
    print("ASYNC TESTS")
    print("-" * 60)

    async def run_async_tests():
        test3 = TestSecurityManagementNestIntegration()
        await test3.test_nest_oauth_start()
        await test3.test_nest_oauth_status_unauthenticated()
        await test3.test_nest_status_fallback_to_mock()

        test4 = TestNestOAuthComplete()
        await test4.test_oauth_complete_requires_code()

    asyncio.run(run_async_tests())

    print("\n" + "=" * 60)
    print("✅ All Nest OAuth tests passed!")
    print("=" * 60)

