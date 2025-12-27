"""Detect and configure USB microscopes."""

import cv2
import sys
from pathlib import Path

def detect_usb_devices():
    """Detect all available USB camera devices."""
    print("USB Camera Device Detection")
    print("=" * 50)

    devices_found = []

    # Test device IDs from 0 to 9 (typical range)
    for device_id in range(10):
        cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)  # Use DirectShow on Windows

        if cap.isOpened():
            # Get device info
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]

                # Try to get device name (limited info available)
                device_info = {
                    'device_id': device_id,
                    'resolution': f"{width}x{height}",
                    'type': 'unknown'
                }

                # Basic heuristics for microscope detection
                if width >= 1280 and height >= 720:  # HD resolution common for microscopes
                    device_info['type'] = 'potential_microscope'
                    device_info['suggested_config'] = 'microscope'
                else:
                    device_info['type'] = 'webcam'
                    device_info['suggested_config'] = 'webcam'

                devices_found.append(device_info)

                print(f"[CAMERA] Device {device_id}: {width}x{height} - {device_info['type']}")

            cap.release()
        else:
            print(f"[NOT FOUND] Device {device_id}: Not available")

    print("\n" + "=" * 50)
    print("Configuration Suggestions:")
    print("=" * 50)

    for device in devices_found:
        if device['suggested_config'] == 'microscope':
            print(f"""
# USB Microscope Configuration (Device {device['device_id']})
microscope_{device['device_id']}:
  type: microscope
  device_id: {device['device_id']}
  resolution: "{device['resolution']}"
  fps: 15  # Lower FPS for better quality
  magnification: 50.0  # Starting magnification
  focus_mode: "auto"
  led_brightness: 75
  calibration_factor: 0.01  # Calibrate for accurate measurements
""")
        else:
            print(f"""
# Webcam Configuration (Device {device['device_id']})
webcam_{device['device_id']}:
  type: webcam
  device_id: {device['device_id']}
  resolution: "{device['resolution']}"
  fps: 30
""")

    return devices_found

def main():
    """Main detection function."""
    print("USB Microscope Detection Tool")
    print("This tool helps you find and configure USB microscopes.")
    print()

    devices = detect_usb_devices()

    if not devices:
        print("\n[ERROR] No camera devices found!")
        print("Make sure your USB microscope is connected and powered on.")
        return 1

    microscopes = [d for d in devices if d['suggested_config'] == 'microscope']
    if microscopes:
        print(f"\n[SUCCESS] Found {len(microscopes)} potential microscope(s)!")
        print("Add the configuration above to your config.yaml file.")
        print("Then restart the Tapo Camera MCP server.")
    else:
        print("\n[WARNING] No microscopes detected, but found other cameras.")
        print("Your microscope might use a different device ID or require special drivers.")

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Detection cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
