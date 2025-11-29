"""Tests for Ring client integration."""

import asyncio
from unittest.mock import MagicMock

import pytest


class TestRingClientInit:
    """Tests for RingClient initialization."""

    def test_client_creation(self):
        """Test creating a RingClient instance."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com", password="testpass")
        assert client._initialized is False
        assert client._2fa_pending is False
        assert client._ring is None
        assert client.email == "test@test.com"

    def test_client_creation_no_password(self):
        """Test creating a RingClient without password."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")
        assert client.password is None

    def test_client_token_file_default(self):
        """Test default token file path."""
        from pathlib import Path

        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")
        assert client.token_file == Path("ring_token.cache")


class TestRingClient2FA:
    """Tests for Ring 2FA handling."""

    def test_2fa_pending_property(self):
        """Test 2FA pending state tracking."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")
        assert client.is_2fa_pending is False

        client._2fa_pending = True
        assert client.is_2fa_pending is True

    def test_submit_2fa_not_pending(self):
        """Test submitting 2FA when not pending."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")
        client._2fa_pending = False

        async def run_test():
            return await client.submit_2fa_code("123456")

        result = asyncio.run(run_test())
        assert result is False


class TestRingClientSummary:
    """Tests for Ring summary data."""

    def test_get_summary_not_initialized(self):
        """Test getting summary when not initialized."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")

        async def run_test():
            return await client.get_summary()

        result = asyncio.run(run_test())
        assert result["initialized"] is False

    def test_get_summary_2fa_pending(self):
        """Test getting summary when 2FA pending."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")
        client._2fa_pending = True

        async def run_test():
            return await client.get_summary()

        result = asyncio.run(run_test())
        assert result["2fa_pending"] is True


class TestRingClientEvents:
    """Tests for Ring events retrieval."""

    def test_get_events_not_initialized(self):
        """Test getting events when not initialized."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")

        async def run_test():
            return await client.get_recent_events()

        result = asyncio.run(run_test())
        assert result == []

    def test_get_events_structure(self):
        """Test events return structure when initialized."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")
        client._initialized = True
        client._ring = MagicMock()

        # Mock video_devices to return empty list (simpler test)
        client._ring.video_devices.return_value = []

        async def run_test():
            return await client.get_recent_events(limit=5)

        result = asyncio.run(run_test())
        # With no devices, should return empty list
        assert isinstance(result, list)


class TestRingClientAlarm:
    """Tests for Ring alarm functions."""

    def test_get_alarm_not_initialized(self):
        """Test getting alarm when not initialized."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")

        async def run_test():
            return await client.get_alarm_status()

        result = asyncio.run(run_test())
        assert result is None

    def test_set_alarm_mode_not_initialized(self):
        """Test setting alarm mode when not initialized."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")

        async def run_test():
            return await client.set_alarm_mode("home")

        result = asyncio.run(run_test())
        assert result is False


class TestRingClientDoorbells:
    """Tests for Ring doorbell retrieval."""

    def test_get_doorbells_not_initialized(self):
        """Test getting doorbells when not initialized."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")

        async def run_test():
            return await client.get_doorbells()

        result = asyncio.run(run_test())
        assert result == []


class TestRingClientProperties:
    """Tests for Ring client properties."""

    def test_is_initialized_property(self):
        """Test is_initialized property."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")
        assert client.is_initialized is False

        client._initialized = True
        assert client.is_initialized is True

    def test_email_stored(self):
        """Test email is stored correctly."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="user@example.com", password="secret")
        assert client.email == "user@example.com"
        assert client.password == "secret"


class TestRingClientDataUpdate:
    """Tests for Ring data update functionality."""

    def test_update_data_not_initialized(self):
        """Test updating data when not initialized."""
        from tapo_camera_mcp.integrations.ring_client import RingClient

        client = RingClient(email="test@test.com")

        async def run_test():
            await client._update_data()

        # Should not raise
        asyncio.run(run_test())


class TestRingAlarmStatus:
    """Tests for Ring alarm status dataclass."""

    def test_alarm_status_creation(self):
        """Test creating RingAlarmStatus."""
        from tapo_camera_mcp.integrations.ring_client import RingAlarmMode, RingAlarmStatus

        status = RingAlarmStatus(
            mode=RingAlarmMode.HOME,
            is_armed=True,
            sensors=[]
        )
        assert status.mode == RingAlarmMode.HOME
        assert status.is_armed is True

    def test_alarm_status_to_dict(self):
        """Test RingAlarmStatus.to_dict()."""
        from tapo_camera_mcp.integrations.ring_client import RingAlarmMode, RingAlarmStatus

        status = RingAlarmStatus(
            mode=RingAlarmMode.DISARMED,
            is_armed=False,
            sensors=[]
        )
        result = status.to_dict()
        assert result["mode"] == "none"
        assert result["is_armed"] is False


class TestRingDevice:
    """Tests for Ring device dataclass."""

    def test_device_creation(self):
        """Test creating RingDevice."""
        from tapo_camera_mcp.integrations.ring_client import RingDevice, RingDeviceType

        device = RingDevice(
            id="123",
            name="Front Door",
            device_type=RingDeviceType.DOORBELL,
            battery_level=100
        )
        assert device.name == "Front Door"
        assert device.battery_level == 100

    def test_device_to_dict(self):
        """Test RingDevice.to_dict()."""
        from tapo_camera_mcp.integrations.ring_client import RingDevice, RingDeviceType

        device = RingDevice(
            id="123",
            name="Test Camera",
            device_type=RingDeviceType.CAMERA
        )
        result = device.to_dict()
        assert result["id"] == "123"
        assert result["device_type"] == "camera"


class TestRingSensor:
    """Tests for Ring sensor dataclass."""

    def test_sensor_creation(self):
        """Test creating RingSensor."""
        from tapo_camera_mcp.integrations.ring_client import RingSensor

        sensor = RingSensor(
            id="456",
            name="Kitchen Door",
            sensor_type="contact",
            is_open=False
        )
        assert sensor.name == "Kitchen Door"
        assert sensor.is_open is False

    def test_sensor_to_dict(self):
        """Test RingSensor.to_dict()."""
        from tapo_camera_mcp.integrations.ring_client import RingSensor

        sensor = RingSensor(
            id="789",
            name="Hallway Motion",
            sensor_type="motion",
            motion_detected=True
        )
        result = sensor.to_dict()
        assert result["sensor_type"] == "motion"
        assert result["motion_detected"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
