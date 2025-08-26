#!/usr/bin/env python3
"""
Test camera connections and capture sample images.

This script helps verify that your camera configurations are correct
and that the server can connect to all configured cameras.
"""
import asyncio
import argparse
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List

from tapo_camera_mcp.camera.manager import camera_manager
from tapo_camera_mcp.camera.base import CameraConfig, CameraType

# Create output directories
TEST_OUTPUT_DIR = Path("test_output")
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

async def test_camera_connection(camera_name: str, config: Dict[str, Any]) -> bool:
    """Test connection to a single camera and capture a test image."""
    print(f"\nTesting camera: {camera_name} ({config['type']})")
    print("-" * 50)
    
    try:
        # Create camera config
        camera_config = CameraConfig(
            name=camera_name,
            type=CameraType(config["type"]),
            params=config.get("params", {}),
            enabled=config.get("enabled", True)
        )
        
        # Add camera to manager
        success = await camera_manager.add_camera(camera_config)
        if not success:
            print(f"❌ Failed to add camera {camera_name}")
            return False
            
        # Get camera instance
        camera = await camera_manager.get_camera(camera_name)
        if not camera:
            print(f"❌ Camera {camera_name} not found after adding")
            return False
            
        # Test connection
        print("🔌 Testing connection...")
        connected = await camera.connect()
        if not connected:
            print(f"❌ Failed to connect to {camera_name}")
            return False
            
        # Get status
        status = await camera.get_status()
        print(f"✅ Connected to {camera_name}")
        print(f"   Status: {status}")
        
        # Capture test image
        output_path = TEST_OUTPUT_DIR / f"{camera_name}_test.jpg"
        print(f"📸 Capturing test image to {output_path}...")
        try:
            await camera.capture_still(str(output_path))
            print(f"✅ Successfully captured image to {output_path}")
        except Exception as e:
            print(f"⚠️  Failed to capture image: {e}")
            
        # Test stream URL
        print("🌐 Testing stream URL...")
        try:
            stream_url = await camera.get_stream_url()
            if stream_url:
                print(f"✅ Stream URL: {stream_url}")
            else:
                print("ℹ️  No stream URL available")
        except Exception as e:
            print(f"⚠️  Failed to get stream URL: {e}")
            
        # Disconnect
        await camera.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Error testing camera {camera_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main(config_path: str):
    """Main function to test all cameras in the config."""
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    cameras = config.get('cameras', [])
    if not cameras:
        print("No cameras found in config")
        return
    
    print(f"\n🔍 Found {len(cameras)} cameras in config")
    print("=" * 50)
    
    # Test each camera
    results = {}
    for cam_config in cameras:
        if not cam_config.get('enabled', True):
            print(f"\n⏩ Skipping disabled camera: {cam_config['name']}")
            continue
            
        success = await test_camera_connection(cam_config['name'], cam_config)
        results[cam_config['name']] = success
    
    # Print summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary")
    print("=" * 50)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\nTest images saved to:", TEST_OUTPUT_DIR.absolute())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test camera connections")
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        print("Please create a config.yaml file or specify a different config file with --config")
        exit(1)
    
    asyncio.run(main(args.config))
