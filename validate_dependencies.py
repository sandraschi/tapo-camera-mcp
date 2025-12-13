#!/usr/bin/env python3
"""
Dependency Validator - Checks all required libraries before server starts.

Prevents the frustrating "it worked yesterday" scenario by validating
all dependencies on startup and providing clear error messages.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_dependencies():
    """Check all required dependencies and provide actionable errors."""
    print("\n" + "=" * 70)
    print("🔍 DEPENDENCY VALIDATION - Smart Home Dashboard")
    print("=" * 70 + "\n")

    missing = []
    issues = []

    # Core dependencies
    checks = [
        ("fastmcp", "FastMCP (MCP server)", "pip install fastmcp"),
        ("pydantic", "Pydantic (data validation)", "pip install pydantic"),
        ("fastapi", "FastAPI (web framework)", "pip install fastapi"),
        ("uvicorn", "Uvicorn (ASGI server)", "pip install uvicorn"),
        ("jinja2", "Jinja2 (templates)", "pip install jinja2"),
    ]

    # Hardware-specific dependencies
    hardware_checks = [
        ("pytapo", "PyTapo (Tapo C200 cameras)", "pip install pytapo", "Tapo Cameras"),
        ("tapo", "Tapo Library (P115 plugs)", "pip install tapo", "Tapo P115 Smart Plugs"),
        ("cv2", "OpenCV (USB webcams)", "pip install opencv-python", "USB Webcams"),
        ("phue", "phue (Philips Hue)", "pip install phue", "Philips Hue Lights"),
        ("pyatmo", "pyatmo (Netatmo weather)", "pip install pyatmo", "Netatmo Weather"),
        ("ring_doorbell", "Ring Library (Ring doorbell)", "pip install ring-doorbell", "Ring Doorbell"),
        ("onvif", "ONVIF (camera protocol)", "pip install onvif-zeep", "ONVIF Cameras"),
    ]

    # System dependencies
    system_checks = [
        ("psycopg2", "psycopg2 (database)", "pip install psycopg2-binary", "Database"),
        ("psutil", "psutil (system monitoring)", "pip install psutil", "System Monitoring"),
        ("aiohttp", "aiohttp (async HTTP)", "pip install aiohttp", "HTTP Client"),
        ("PIL", "Pillow (image processing)", "pip install pillow", "Image Processing"),
    ]

    print("📦 CORE DEPENDENCIES:")
    print("-" * 70)
    for module, name, install_cmd in checks:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - MISSING!")
            missing.append((name, install_cmd))

    print("\n🔌 HARDWARE DEPENDENCIES:")
    print("-" * 70)
    for module, name, install_cmd, hardware in hardware_checks:
        try:
            __import__(module)
            print(f"   ✅ {name} ({hardware})")
        except ImportError:
            print(f"   ⚠️  {name} - MISSING (affects: {hardware})")
            issues.append((name, install_cmd, hardware))

    print("\n⚙️ SYSTEM DEPENDENCIES:")
    print("-" * 70)
    for module, name, install_cmd, feature in system_checks:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - MISSING!")
            missing.append((name, install_cmd))

    print("\n" + "=" * 70)

    if missing:
        print("\n❌ CRITICAL MISSING DEPENDENCIES:")
        print("-" * 70)
        for name, install_cmd in missing:
            print(f"   {name}")
            print(f"      Fix: {install_cmd}")
        print("\n🚨 Server may not start! Install critical dependencies first.")
        return False

    if issues:
        print("\n⚠️  OPTIONAL HARDWARE DEPENDENCIES MISSING:")
        print("-" * 70)
        for name, install_cmd, hardware in issues:
            print(f"   {name} - {hardware} won't work")
            print(f"      Fix: {install_cmd}")
        print("\n✅ Server will start, but some hardware won't be available.")
        print("   Install missing dependencies to enable full functionality.")
        return True  # Can still start

    print("\n🎉 ALL DEPENDENCIES SATISFIED!")
    print("   Server is ready for full operation.")
    print("=" * 70 + "\n")
    return True


if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)

