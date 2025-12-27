#!/usr/bin/env python3
"""Universal USB Device Detection and Configuration Tool."""

import cv2
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def detect_usb_cameras(max_devices=10):
    """Detect all available USB camera/scanner devices."""
    print("Universal USB Device Detection")
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
                    "is_working": True,
                    "suggested_type": suggest_device_type(width, height, i)
                }
                detected_devices.append(device_info)
                device_type = device_info["suggested_type"].upper()
                print(f"[{device_type}] Device {i}: {width}x{height} - {backend} (Working)")
            else:
                print(f"[UNKNOWN] Device {i}: {width}x{height} - {backend} (Not working, possibly in use)")
            cap.release()
        else:
            print(f"[NOT FOUND] Device {i}: Not available")
    return detected_devices

def suggest_device_type(width, height, device_id):
    """Suggest device type based on resolution and characteristics."""
    resolution = f"{width}x{height}"

    # Camera/microscope/otoscope resolutions
    if resolution in ["640x480", "800x600", "1024x768", "1280x720", "1920x1080"]:
        if resolution in ["640x480", "800x600"]:
            return "otoscope"  # Common otoscope resolutions
        elif resolution == "1280x720":
            return "microscope"  # Common microscope resolution
        else:
            return "webcam"  # General webcam - could also be digicam or iPhone

    # High resolution (likely scanners or professional cameras)
    elif width > 2000 or height > 1500:
        return "scanner"

    # Unknown/default - provide templates for manual configuration
    else:
        return "webcam"

def generate_device_configs(detected_devices):
    """Generate configuration for all detected devices."""
    print("\nConfiguration Suggestions:")
    print("=" * 50)

    configs = []

    for device in detected_devices:
        device_type = device["suggested_type"]
        device_id = device["device_id"]
        resolution = device["resolution"]

        if device_type == "webcam":
            config = f"""
# Webcam Configuration (Device {device_id})
webcam{device_id}:
  type: webcam
  device_id: {device_id}
  resolution: "{resolution}"
  fps: 30"""

        elif device_type == "microscope":
            config = f"""
# USB Microscope Configuration (Device {device_id})
microscope{device_id}:
  type: microscope
  device_id: {device_id}
  resolution: "{resolution}"
  fps: 15 # Lower FPS for better image quality
  magnification: 50.0 # Starting magnification
  focus_mode: "auto"
  led_brightness: 75 # Example LED brightness
  calibration_factor: 0.01 # Example: mm per pixel (needs actual calibration)"""

        elif device_type == "otoscope":
            config = f"""
# USB Otoscope Configuration (Device {device_id})
otoscope{device_id}:
  type: otoscope
  device_id: {device_id}
  resolution: "{resolution}"
  fps: 30
  light_intensity: 80 # LED brightness (0-100)
  focus_mode: "auto" # auto, manual, or fixed
  specimen_type: "ear" # ear, throat, nose, mouth, skin, other
  magnification: 1.0 # Digital magnification
  # calibration_data: {{}} # Will be set during calibration"""

        elif device_type == "scanner":
            config = f"""
# USB Scanner Configuration (Device {device_id})
scanner{device_id}:
  type: scanner
  device_id: {device_id}
  resolution: "{resolution}"
  scanner_type: "flatbed" # flatbed, slide, or auto
  color_mode: "color" # color, grayscale, or monochrome
  dpi: 300 # Default DPI setting"""

        elif device_type == "digicam":
            config = f"""
# USB Digicam Configuration (Device {device_id})
digicam{device_id}:
  type: digicam
  device_id: {device_id}
  resolution: "{resolution}"
  fps: 30
  camera_model: "Unknown Digicam" # e.g., Canon EOS Rebel, Nikon D3300
  connection_type: "usb" # usb, hdmi, wifi
  driver_software: "generic" # generic, canon, nikon, sony, etc.
  original_megapixels: 12 # Camera's original megapixel rating
  has_optical_zoom: false # true if camera has optical zoom lens
  max_optical_zoom: 1.0 # Maximum optical zoom level
  focus_mode: "auto" # auto, manual, macro, infinity
  image_stabilization: false
  night_mode: false"""

        elif device_type == "iphone":
            config = f"""
# iPhone Webcam Configuration (Device {device_id})
iphone{device_id}:
  type: iphone
  device_id: {device_id}
  resolution: "{resolution}"
  fps: 30
  iphone_model: "iPhone X" # e.g., iPhone 12 Pro, iPhone 13
  ios_version: "16.0" # iOS version
  connection_method: "wifi" # wifi, usb, continuity
  webcam_app: "continuity" # continuity, epoccam, manycam, etc.
  camera_lens: "wide" # wide, ultra_wide, telephoto
  hdr_mode: false
  portrait_mode: false
  live_photos: false
  stabilization: true"""

        else:
            config = f"""
# Unknown USB Device Configuration (Device {device_id})
unknown{device_id}:
  type: webcam  # Default to webcam, change as needed
  device_id: {device_id}
  resolution: "{resolution}"
  fps: 30"""

        configs.append(config)
        print(config)

    return configs

def main():
    """Main detection function."""
    print("Universal USB Device Detection Tool")
    print("Finds cameras, microscopes, otoscopes, scanners, digicams, iPhones, and other USB imaging devices.")
    print()

    detected_devices = detect_usb_cameras()
    configs = generate_device_configs(detected_devices)

    print(f"\n[SUCCESS] Found {len(detected_devices)} USB imaging device(s)")
    print("Add the configuration above to your config.yaml file.")
    print("Then restart the Tapo Camera MCP server.")
    print("\nDevice Types Detected:")
    for device in detected_devices:
        print(f"  - Device {device['device_id']}: {device['suggested_type'].upper()} ({device['resolution']})")

    print("\n[INFO] Additional Device Types Available:")
    print("  - DIGICAM: For old digital cameras (Canon, Nikon, Sony, etc.)")
    print("  - IPHONE: For repurposed iPhones as webcams")
    print("  - MICROSCOPE: For USB digital microscopes")
    print("  - OTOSCOPE: For USB medical otoscopes")
    print("  - SCANNER: For document/slide scanners")
    print("Configure manually if your device type isn't auto-detected.")

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
