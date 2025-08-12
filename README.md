# Tapo Camera MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/tapo-camera-mcp)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A FastMCP 2.10-compliant MCP server for controlling TP-Link Tapo cameras. This project provides a unified interface to manage and control Tapo cameras through the MCP protocol, enabling seamless integration with other MCP-compliant systems.

## Features

- **Camera Control**: Power on/off, reboot, and manage camera settings
- **PTZ Control**: Pan, tilt, and zoom control for compatible cameras
- **Motion Detection**: Configure and monitor motion detection
- **Video Streaming**: Stream video in multiple formats (RTSP, RTMP, HLS)
- **Recording**: Local recording with configurable storage settings
- **Snapshot**: Capture still images from the camera feed
- **RESTful API**: Full-featured API for programmatic control
- **CLI**: Command-line interface for easy management
- **Plugin System**: Easy integration with FastMCP applications

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Using pip

```bash
pip install tapo-camera-mcp
```

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tapo-camera-mcp.git
   cd tapo-camera-mcp
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

## Configuration

Create a `.env` file in the project root with your camera details:

```ini
# Camera connection settings
TAPO_CAMERA_HOST=192.168.1.100
TAPO_CAMERA_PORT=443
TAPO_CAMERA_USERNAME=admin
TAPO_CAMERA_PASSWORD=yourpassword

# Optional settings
TAPO_CAMERA_USE_HTTPS=true
TAPO_CAMERA_VERIFY_SSL=false
TAPO_CAMERA_TIMEOUT=10

# Stream settings
TAPO_CAMERA_STREAM_TYPE=rtsp
TAPO_CAMERA_STREAM_QUALITY=high
TAPO_CAMERA_STREAM_AUDIO=true

# Storage settings
TAPO_CAMERA_STORAGE_PATH=./recordings
TAPO_CAMERA_MAX_STORAGE_GB=10

# Motion detection
TAPO_CAMERA_MOTION_DETECTION_ENABLED=true
TAPO_CAMERA_MOTION_SENSITIVITY=medium
```

## Usage

### Command Line Interface

```bash
# Start the MCP server
tapo-camera-mcp serve --bind 0.0.0.0 --port 8000

# Get camera info
tapo-camera-mcp camera info

# Get camera status
tapo-camera-mcp camera status

# Start streaming
tapo-camera-mcp camera stream start --type rtsp

# Move PTZ
tapo-camera-mcp camera ptz move --direction up --speed 0.5

# Take a snapshot
tapo-camera-mcp camera snapshot

# Start recording
tapo-camera-mcp camera record start --duration 60
```

### Python API

```python
from tapo_camera_mcp import TapoCameraMCP

# Create a camera instance
camera = TapoCameraMCP(config={
    "host": "192.168.1.100",
    "username": "admin",
    "password": "yourpassword"
})

# Connect to the camera
await camera.connect()

# Get camera info
info = await camera.handle_get_info(None)
print(f"Camera Model: {info.get('model')}")

# Start streaming
stream = await camera.handle_start_stream({
    "stream_type": "rtsp",
    "quality": "high"
})
print(f"Stream URL: {stream.get('stream_url')}")

# Disconnect
await camera.disconnect()
```

## API Reference

### Endpoints

- `GET /api/camera/info` - Get camera information
- `GET /api/camera/status` - Get camera status
- `POST /api/camera/reboot` - Reboot the camera
- `POST /api/stream/start` - Start a video stream
- `POST /api/stream/stop` - Stop a video stream
- `POST /api/ptz/move` - Move the PTZ camera
- `POST /api/ptz/preset` - Manage PTZ presets
- `POST /api/recording/start` - Start recording
- `POST /api/recording/stop` - Stop recording
- `GET /api/snapshot` - Take a snapshot

## Development

### Setting Up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tapo-camera-mcp.git
   cd tapo-camera-mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=tapo_camera_mcp --cov-report=term-missing
```

### Code Style

This project uses `black` for code formatting and `isort` for import sorting.

```bash
# Format code
black .

# Sort imports
isort .

# Check code style
pylint tapo_camera_mcp/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [TP-Link](https://www.tp-link.com/) for their Tapo camera products
- [FastMCP](https://github.com/yourusername/fastmcp) for the MCP protocol implementation
- [aiohttp](https://docs.aiohttp.org/) for the async HTTP client/server
- [ONVIF](https://www.onvif.org/) for the camera control protocol

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
