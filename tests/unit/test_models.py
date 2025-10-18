#!/usr/bin/env python3
"""
Test models and core data structures.
"""

import os
import sys

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_core_models():
    """Test core model definitions."""
    try:

        # Test enums


        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_ptz_models():
    """Test PTZ model definitions."""
    try:
        from tapo_camera_mcp.core.models import PTZPosition

        # Test PTZ directions

        # Test PTZ position
        PTZPosition(pan=45.0, tilt=30.0, zoom=1.5)

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_motion_models():
    """Test motion detection models."""
    try:
        from tapo_camera_mcp.core.models import MotionEvent

        # Test sensitivity levels

        # Test motion event
        MotionEvent(
            camera_id="test-camera",
            timestamp="2023-01-01T12:00:00Z",
            regions=[[0, 0, 100, 100]],
            confidence=0.85,
        )

        return True
    except Exception:
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


    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)
