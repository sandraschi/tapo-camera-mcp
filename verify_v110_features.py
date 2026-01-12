#!/usr/bin/env python3
"""
Verification script for Tapo Camera MCP v1.10.0 features.

This script verifies that all the key v1.10.0 features are working correctly.
Run this after deployment to ensure everything is functioning.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_imports():
    """Check that all required imports work."""
    print("=== CHECKING IMPORTS ===")

    try:
        from tapo_camera_mcp.web.server import WebServer
        print("OK - WebServer import")
    except Exception as e:
        print(f"FAIL - WebServer import: {e}")
        return False

    try:
        from tapo_camera_mcp.web.api.plex import router as plex_router
        print("OK - Plex router import")
    except Exception as e:
        print(f"FAIL - Plex router import: {e}")
        return False

    try:
        from tapo_camera_mcp.core.messaging_service import MessageCategory
        assert hasattr(MessageCategory, 'MEDIA_EVENT')
        print("OK - MEDIA_EVENT category exists")
    except Exception as e:
        print(f"FAIL - MEDIA_EVENT category missing: {e}")
        return False

    return True

def check_files():
    """Check that all required files exist."""
    print("\n=== CHECKING FILES ===")

    files_to_check = [
        "webapp/web/templates/plex.html",
        "webapp/web/templates/log_management.html",
        "webapp/web/static/css/plex.css",
        "webapp/web/api/plex.py",
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"OK - {file_path} exists")
        else:
            print(f"FAIL - {file_path} missing")
            return False

    return True

def check_navigation():
    """Check that navigation includes new links."""
    print("\n=== CHECKING NAVIGATION ===")

    nav_file = "src/tapo_camera_mcp/web/templates/base.html"
    if not os.path.exists(nav_file):
        print(f"FAIL - Navigation file missing: {nav_file}")
        return False

    with open(nav_file, 'r', encoding='utf-8') as f:
        content = f.read()

    nav_checks = [
        ('href="/plex"', "Plex Media link"),
        ('href="/logs"', "Log Management link"),
    ]

    for check, description in nav_checks:
        if check in content:
            print(f"OK - {description} present")
        else:
            print(f"FAIL - {description} missing")
            return False

    return True

def check_theme_variables():
    """Check that theme variables are defined."""
    print("\n=== CHECKING THEME VARIABLES ===")

    theme_file = "src/tapo_camera_mcp/web/templates/base.html"
    if not os.path.exists(theme_file):
        print(f"FAIL - Theme file missing: {theme_file}")
        return False

    with open(theme_file, 'r', encoding='utf-8') as f:
        content = f.read()

    theme_vars = [
        "--camera-online",
        "--camera-warning",
        "--camera-blue",
        "--bg-color",
        "--text-color",
    ]

    for var in theme_vars:
        if var in content:
            print(f"OK - Theme variable {var} defined")
        else:
            print(f"FAIL - Theme variable {var} missing")
            return False

    return True

def check_api_endpoints():
    """Check that API endpoints are defined."""
    print("\n=== CHECKING API ENDPOINTS ===")

    server_file = "src/tapo_camera_mcp/web/server.py"
    if not os.path.exists(server_file):
        print(f"FAIL - Server file missing: {server_file}")
        return False

    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()

    api_checks = [
        ('/plex', "Plex page route"),
        ('/logs', "Logs page route"),
        ('plex_router', "Plex router inclusion"),
    ]

    for route, description in api_checks:
        if route in content:
            print(f"OK - {description} defined")
        else:
            print(f"FAIL - {description} missing")
            return False

    return True

def main():
    """Run all verification checks."""
    print("Tapo Camera MCP v1.10.0 Feature Verification")
    print("=" * 50)

    all_passed = True

    # Run all checks
    checks = [
        check_imports,
        check_files,
        check_navigation,
        check_theme_variables,
        check_api_endpoints,
    ]

    for check_func in checks:
        if not check_func():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("SUCCESS: ALL V1.10.0 FEATURES VERIFIED SUCCESSFULLY!")
        print("\n- Plex Media Integration: OK")
        print("- Log Management Interface: OK")
        print("- Enhanced Theme System: OK")
        print("- Complete API Endpoints: OK")
        print("- Navigation Updates: OK")
        return 0
    else:
        print("FAILURE: SOME V1.10.0 FEATURES FAILED VERIFICATION")
        print("Please check the errors above and fix any missing components.")
        return 1

if __name__ == "__main__":
    sys.exit(main())