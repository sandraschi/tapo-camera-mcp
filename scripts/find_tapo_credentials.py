"""Helper script to find Tapo camera credentials.

This script tries common credential combinations to help identify
what credentials your Tapo camera uses after reset.
"""

import sys

from pytapo import Tapo


def try_credentials(ip, username, password):
    """Try to connect with given credentials."""
    try:
        print(f"  Trying {username}/{password}...", end=" ")
        camera = Tapo(ip, username, password)
        info = camera.getBasicInfo()
        print("[SUCCESS!]")
        return True
    except Exception as e:
        error_msg = str(e)
        if "Temporary Suspension" in error_msg:
            print("[LOCKED OUT - Wait 30 min]")
            return "locked"
        if "Invalid authentication" in error_msg:
            print("[FAILED]")
            return False
        print(f"[ERROR: {error_msg[:50]}]")
        return False


def find_credentials(ip):
    """Try common credential combinations."""
    print(f"\nSearching for credentials for camera at {ip}...")
    print("=" * 60)

    # Common combinations to try
    combinations = [
        # Default after reset (most common)
        ("admin", "admin"),
        # Cloud account
        ("sandraschipal@hotmail.com", "Sec0860ta#"),
        # Variations
        ("admin", ""),
        ("", "admin"),
    ]

    for username, password in combinations:
        result = try_credentials(ip, username, password)
        if result is True:
            print("\n[SUCCESS] Found working credentials!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print("\nUpdate your config.yaml with these credentials.")
            return (username, password)
        if result == "locked":
            print("\n[STOPPED] Camera is locked out. Wait 30 minutes or power cycle camera.")
            return None

    print("\n" + "=" * 60)
    print("[FAILED] None of the common credentials worked.")
    print("\nTry manually:")
    print("1. Check the camera label/sticker for default credentials")
    print("2. Check device manual for default username/password")
    print("3. In Tapo app: Camera -> Advanced -> Local Device Settings")
    print("4. Password might be in TPL[numbers] format from label")
    print("=" * 60)
    return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = "192.168.0.164"  # Kitchen camera

    print("Tapo Camera Credential Finder")
    print(f"Testing camera at {ip}")
    print("\nWARNING: Too many failed attempts will lock the camera!")
    print("This script tries common combinations carefully.\n")

    result = find_credentials(ip)

    if result:
        print(f"\nWorking credentials found: {result[0]}/{result[1]}")
        sys.exit(0)
    else:
        print("\nManual credential lookup required.")
        sys.exit(1)

