#!/usr/bin/env python3
"""USB Otoscope Detection and Configuration Tool."""

import cv2
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def detect_usb_cameras(max_devices=10):
    """Detect all available USB camera devices."""
    print("USB Camera Device Detection")
    print("=" * 50)
    detected_devices = []
    for i in range(max_devices):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            backend = cap.getBackendName()

            # Try to read a frame to confirm it's a working camera
            ret, frame = cap.read()
            if ret:
                device_info = {
                    "device_id": i,
                    "resolution": f"{width}x{height}",
                    "backend": backend,
                    "is_working": True
                }
                detected_devices.append(device_info)
                print(f"[CAMERA] Device {i}: {width}x{height} - {backend} (Working)")
            else:
                print(f"[CAMERA] Device {i}: {width}x{height} - {backend} (Not working, possibly in use or no stream)")
            cap.release()
        else:
            print(f"[NOT FOUND] Device {i}: Not available")
    return detected_devices

def suggest_otoscope_config(detected_devices):
    """Suggests configuration for detected otoscopes."""
    print("\nConfiguration Suggestions:")
    print("=" * 50)

    otoscope_configs = []
    for device in detected_devices:
        # Heuristic: Otoscopes often have specific resolutions or are lower-res cameras
        # This can be refined based on common otoscope characteristics
        if device["is_working"] and device["resolution"] in ["640x480", "800x600", "1024x768"]:
            config_entry = f"""
# USB Otoscope Configuration (Device {device['device_id']})
otoscope{device['device_id']}:
  type: otoscope
  device_id: {device['device_id']}
  resolution: "{device['resolution']}"
  fps: 30
  light_intensity: 80  # LED brightness (0-100)
  focus_mode: "auto"   # auto, manual, or fixed
  specimen_type: "ear" # ear, throat, nose, mouth, skin, other
  magnification: 1.0   # Digital magnification
  # calibration_data: {{}}  # Will be set during first use
"""
            otoscope_configs.append(config_entry)
            print(config_entry)

    if not otoscope_configs:
        print("No potential otoscope devices detected based on common resolutions.")
        print("Otoscope cameras typically use 640x480 or 800x600 resolution.")
        print("If your otoscope uses a different resolution, you can manually configure it as type: otoscope")

def main():
    """Main detection function."""
    print("USB Otoscope Detection Tool")
    print("This tool helps you find and configure USB otoscope cameras.")
    print()

    detected_devices = detect_usb_cameras()
    suggest_otoscope_config(detected_devices)

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
