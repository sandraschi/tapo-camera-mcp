#!/usr/bin/env python3
"""
Test script for security system integrations

This script tests the integration between Tapo Camera MCP dashboard
and external security MCP servers (Nest Protect, Ring MCP).
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tapo_camera_mcp.security import security_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_nest_protect_integration():
    """Test Nest Protect MCP integration"""
    print("🔥 Testing Nest Protect MCP Integration")
    print("=" * 50)

    # Configure for Nest Protect
    config = {
        "nest_protect": {"enabled": True, "server_url": "http://localhost:8123"},
        "ring_mcp": {"enabled": False},
    }

    try:
        # Initialize the security manager
        await security_manager.initialize(config)
        print("✅ Security manager initialized")

        # Test getting devices
        print("\n📊 Testing device retrieval...")
        devices = await security_manager.get_all_devices()
        print(f"Found {len(devices)} security devices")

        for device in devices:
            print(f"  - {device.name} ({device.type}): {device.status}")

        # Test getting alerts
        print("\n🚨 Testing alert retrieval...")
        alerts = await security_manager.get_all_alerts()
        print(f"Found {len(alerts)} active alerts")

        for alert in alerts:
            print(f"  - {alert.device_name}: {alert.message} ({alert.severity})")

        # Test system overview
        print("\n📈 Testing system overview...")
        overview = await security_manager.get_system_overview()
        print(f"Total devices: {overview.get('total_devices', 0)}")
        print(f"Online devices: {overview.get('online_devices', 0)}")
        print(f"Active alerts: {overview.get('active_alerts', 0)}")

        if overview.get("systems"):
            for system_name, system_data in overview["systems"].items():
                print(f"  - {system_name}: {system_data}")

        print("\n✅ Nest Protect integration test completed successfully!")

    except Exception as e:
        print(f"❌ Nest Protect integration test failed: {e}")
        import traceback

        traceback.print_exc()


async def test_ring_mcp_integration():
    """Test Ring MCP integration (when ready)"""
    print("\n🚨 Testing Ring MCP Integration")
    print("=" * 50)

    # Configure for Ring MCP
    config = {
        "nest_protect": {"enabled": False},
        "ring_mcp": {"enabled": True, "server_path": "D:\\Dev\\repos\\ring-mcp"},
    }

    try:
        # Initialize the security manager
        await security_manager.initialize(config)
        print("✅ Security manager initialized for Ring MCP")

        # Test getting devices (will likely fail until Ring MCP is working)
        print("\n📊 Testing Ring device retrieval...")
        devices = await security_manager.get_all_devices()
        print(f"Found {len(devices)} Ring devices")

        print("\n⚠️  Ring MCP integration not yet implemented (waiting for server fix)")

    except Exception as e:
        print(f"❌ Ring MCP integration test failed (expected): {e}")


async def main():
    """Run all integration tests"""
    print("🏠 Tapo Camera MCP - Security Integration Tests")
    print("=" * 60)

    # Test Nest Protect integration
    await test_nest_protect_integration()

    # Test Ring MCP integration
    await test_ring_mcp_integration()

    # Cleanup
    await security_manager.cleanup()

    print("\n" + "=" * 60)
    print("🏁 All security integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
