#!/usr/bin/env python3
"""
Test models and core data structures.
"""

import sys
import os

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_core_models():
    """Test core model definitions."""
    try:
        from tapo_camera_mcp.core.models import CameraModel, StreamType, VideoQuality

        # Test enums
        camera_models = [CameraModel.C200, CameraModel.C310, CameraModel.L530]
        stream_types = [StreamType.RTSP, StreamType.RTMP, StreamType.HLS]
        video_qualities = [VideoQuality.LOW, VideoQuality.MEDIUM, VideoQuality.HIGH]

        print(f"✅ Camera models: {[cm.value for cm in camera_models]}")
        print(f"✅ Stream types: {[st.value for st in stream_types]}")
        print(f"✅ Video qualities: {[vq.value for vq in video_qualities]}")

        return True
    except Exception as e:
        print(f"❌ Core models test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ptz_models():
    """Test PTZ model definitions."""
    try:
        from tapo_camera_mcp.core.models import PTZDirection, PTZPosition

        # Test PTZ directions
        directions = [
            PTZDirection.UP,
            PTZDirection.DOWN,
            PTZDirection.LEFT,
            PTZDirection.RIGHT,
            PTZDirection.UP_LEFT,
            PTZDirection.UP_RIGHT,
            PTZDirection.DOWN_LEFT,
            PTZDirection.DOWN_RIGHT,
        ]
        print(f"✅ PTZ directions: {[d.value for d in directions]}")

        # Test PTZ position
        position = PTZPosition(pan=45.0, tilt=30.0, zoom=1.5)
        print(
            f"✅ PTZ position: pan={position.pan}, tilt={position.tilt}, zoom={position.zoom}"
        )

        return True
    except Exception as e:
        print(f"❌ PTZ models test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_motion_models():
    """Test motion detection models."""
    try:
        from tapo_camera_mcp.core.models import MotionDetectionSensitivity, MotionEvent

        # Test sensitivity levels
        sensitivities = [
            MotionDetectionSensitivity.LOW,
            MotionDetectionSensitivity.MEDIUM,
            MotionDetectionSensitivity.HIGH,
        ]
        print(f"✅ Motion sensitivities: {[s.value for s in sensitivities]}")

        # Test motion event
        event = MotionEvent(
            camera_id="test-camera",
            timestamp="2023-01-01T12:00:00Z",
            regions=[[0, 0, 100, 100]],
            confidence=0.85,
        )
        print(
            f"✅ Motion event: camera={event.camera_id}, confidence={event.confidence}"
        )

        return True
    except Exception as e:
        print(f"❌ Motion models test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    tests = [
        test_core_models,
        test_ptz_models,
        test_motion_models,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All model tests passed!")
        sys.exit(0)
    else:
        print("❌ Some model tests failed")
        sys.exit(1)
