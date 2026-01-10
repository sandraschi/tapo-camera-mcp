"""Tests for Ring API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_ring_client():
    """Create a mock Ring client."""
    client = MagicMock()
    client.is_initialized = True
    client.is_2fa_pending = False
    client._ring = MagicMock()
    return client


@pytest.fixture
def mock_doorbell():
    """Create a mock Ring doorbell."""
    doorbell = MagicMock()
    doorbell.id = "52772421"
    doorbell.name = "Front Door"
    doorbell.kind = "doorbell_portal"
    doorbell.battery_life = 100
    doorbell.has_subscription = False
    doorbell.model = "Peephole Cam"
    doorbell.wifi_signal_strength = -50
    doorbell.firmware = "Up to Date"
    return doorbell


class TestRingStatus:
    """Tests for Ring status endpoint."""

    def test_ring_not_configured(self):
        """Test response when Ring client not configured."""
        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=None):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_ring_status

            result = asyncio.run(get_ring_status())
            assert result["connected"] is False
            assert result["initialized"] is False
            assert "not configured" in result["message"].lower()

    def test_ring_2fa_pending(self, mock_ring_client):
        """Test response when 2FA is pending."""
        mock_ring_client.is_initialized = False
        mock_ring_client.is_2fa_pending = True

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_ring_status

            result = asyncio.run(get_ring_status())
            assert result["connected"] is True
            assert result["two_fa_pending"] is True
            assert "2fa" in result["message"].lower()

    def test_ring_initialized(self, mock_ring_client):
        """Test response when Ring is fully initialized."""
        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_ring_status

            result = asyncio.run(get_ring_status())
            assert result["connected"] is True
            assert result["initialized"] is True
            assert result["two_fa_pending"] is False


class TestRingSummary:
    """Tests for Ring summary endpoint."""

    def test_summary_not_initialized(self):
        """Test summary when Ring not initialized."""
        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=None):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_ring_summary

            result = asyncio.run(get_ring_summary())
            assert result.initialized is False

    def test_summary_with_doorbells(self, mock_ring_client, mock_doorbell):
        """Test summary with doorbell data."""
        mock_ring_client.get_summary = AsyncMock(
            return_value={
                "initialized": True,
                "2fa_pending": False,
                "doorbells": [{"id": "52772421", "name": "Front Door"}],
                "doorbell_count": 1,
                "alarm": None,
                "recent_events": [],
                "last_event": None,
            }
        )

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_ring_summary

            result = asyncio.run(get_ring_summary())
            assert result.initialized is True
            assert result.doorbell_count == 1


class TestRingEvents:
    """Tests for Ring events endpoint."""

    def test_events_not_initialized(self):
        """Test events when Ring not initialized."""
        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=None):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_recent_events

            with pytest.raises(HTTPException):
                asyncio.run(get_recent_events())

    def test_events_with_data(self, mock_ring_client):
        """Test events with motion/ding data."""
        mock_ring_client.get_recent_events = AsyncMock(
            return_value=[
                {
                    "device_id": "52772421",
                    "device_name": "Front Door",
                    "event_type": "motion",
                    "timestamp": "2025-11-28T20:00:00+01:00",
                    "answered": False,
                    "recording_id": "12345",
                    "duration": 30,
                },
                {
                    "device_id": "52772421",
                    "device_name": "Front Door",
                    "event_type": "ding",
                    "timestamp": "2025-11-28T19:00:00+01:00",
                    "answered": True,
                    "recording_id": "12344",
                    "duration": 15,
                },
            ]
        )

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_recent_events

            result = asyncio.run(get_recent_events(limit=10))
            assert result["summary"]["total"] == 2
            assert result["summary"]["motion"] == 1
            assert result["summary"]["dings"] == 1
            assert result["latest_motion"] is not None
            assert result["latest_ding"] is not None


class TestRingCapabilities:
    """Tests for Ring capabilities endpoint."""

    def test_capabilities_no_subscription(self, mock_ring_client, mock_doorbell):
        """Test capabilities without Ring Protect."""
        mock_ring_client._ring.video_devices.return_value = [mock_doorbell]
        mock_ring_client._update_data = AsyncMock()

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_doorbell_capabilities

            result = asyncio.run(get_doorbell_capabilities("52772421"))
            assert result["has_subscription"] is False
            assert result["features"]["live_view"] is False
            assert result["features"]["recordings"] is True

    def test_capabilities_with_subscription(self, mock_ring_client, mock_doorbell):
        """Test capabilities with Ring Protect."""
        mock_doorbell.has_subscription = True
        mock_ring_client._ring.video_devices.return_value = [mock_doorbell]
        mock_ring_client._update_data = AsyncMock()

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_doorbell_capabilities

            result = asyncio.run(get_doorbell_capabilities("52772421"))
            assert result["has_subscription"] is True
            assert result["features"]["live_view"] is True


class TestRingAlarm:
    """Tests for Ring alarm endpoints."""

    def test_alarm_status(self, mock_ring_client):
        """Test getting alarm status."""
        mock_ring_client.get_alarm_status = AsyncMock(
            return_value=MagicMock(
                mode=MagicMock(value="none"),
                is_armed=False,
                sensors=[],
                to_dict=lambda: {"mode": "none", "is_armed": False, "sensors": []},
            )
        )

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_alarm_status

            result = asyncio.run(get_alarm_status())
            assert "alarm" in result


class TestRing2FA:
    """Tests for Ring 2FA endpoints."""

    def test_2fa_no_pending(self, mock_ring_client):
        """Test 2FA submission when none pending."""
        mock_ring_client.is_2fa_pending = False

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import Ring2FARequest, submit_2fa_code

            with pytest.raises(HTTPException):
                asyncio.run(submit_2fa_code(Ring2FARequest(code="123456")))

    def test_2fa_success(self, mock_ring_client):
        """Test successful 2FA submission."""
        mock_ring_client.is_2fa_pending = True
        mock_ring_client.submit_2fa_code = AsyncMock(return_value=True)

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import Ring2FARequest, submit_2fa_code

            result = asyncio.run(submit_2fa_code(Ring2FARequest(code="123456")))
            assert result["success"] is True


class TestRingWebRTC:
    """Tests for Ring WebRTC endpoints."""

    def test_webrtc_offer_not_initialized(self):
        """Test WebRTC offer when Ring not initialized."""
        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=None):
            import asyncio

            from tapo_camera_mcp.web.api.ring import WebRTCOfferRequest, create_webrtc_stream

            with pytest.raises(HTTPException):
                asyncio.run(
                    create_webrtc_stream(
                        WebRTCOfferRequest(device_id="52772421", sdp_offer="v=0...")
                    )
                )

    def test_webrtc_offer_device_not_found(self, mock_ring_client):
        """Test WebRTC offer with unknown device."""
        mock_ring_client._ring.video_devices.return_value = []

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import WebRTCOfferRequest, create_webrtc_stream

            with pytest.raises(HTTPException):
                asyncio.run(
                    create_webrtc_stream(
                        WebRTCOfferRequest(device_id="99999999", sdp_offer="v=0...")
                    )
                )

    def test_ice_servers(self, mock_ring_client, mock_doorbell):
        """Test getting ICE servers."""
        mock_doorbell.get_ice_servers = MagicMock(return_value=[{"urls": "stun:stun.ring.com:443"}])
        mock_ring_client._ring.video_devices.return_value = [mock_doorbell]

        with patch("tapo_camera_mcp.web.api.ring.get_ring_client", return_value=mock_ring_client):
            import asyncio

            from tapo_camera_mcp.web.api.ring import get_ice_servers

            result = asyncio.run(get_ice_servers())
            assert "ice_servers" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
