# Tapo Camera MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/tapo-camera-mcp)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A FastMCP 2.10.1-compliant MCP server for TP-Link Tapo cameras, communicating via stdio as per the MCP 2.10.1 standard.

> **Note:** This project includes FastAPI-based test endpoints for development and testing purposes only. The primary communication channel is via stdio as required by the MCP 2.10.1 specification.

## Features

### Supported Camera Types
- **Tapo Cameras**: Full support for TP-Link Tapo series
- *Note: Other camera types shown in examples are for demonstration purposes only. Current implementation focuses on Tapo cameras.*

### Core Features
- **Unified Interface**: Single API for all camera types
- **Camera Groups**: Organize cameras into logical groups
- **Multi-Stream Support**: Handle multiple camera streams simultaneously
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Camera Control
- **Power Management**: Power on/off, reboot
- **PTZ Control**: Pan, tilt, and zoom (where supported)
- **Motion Detection**: Configure and monitor motion events
- **Video Streaming**: RTSP, RTMP, and HLS streaming
- **Snapshot**: Capture still images
- **Status Monitoring**: Real-time status and health checks

### Integration
- **MCP 2.10.1 Compliant**: Seamless integration with MCP ecosystem via stdio
- **CLI**: Command-line interface for administration

### Development & Testing
- **Test Server**: Includes a FastAPI-based test server (for development only)
- **Mock Implementations**: For testing without physical hardware

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

## Quick Start

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tapo-camera-mcp.git
   cd tapo-camera-mcp
   ```

2. Install with development dependencies:
   ```bash
   # Install package in development mode with test dependencies
   pip install -e ".[dev]"
   
   # For testing the MCP server (optional)
   pip install fastapi uvicorn
   ```

> **Note:** FastAPI and Uvicorn are only required for testing the MCP server. The main application communicates via stdio as per the MCP 2.10.1 specification.

### Configuration

Create a `config.yaml` file in the project root with your camera configurations:

```yaml
# Server configuration
server:
  host: 0.0.0.0
  port: 8000
  web_port: 7777
  log_level: INFO

# Camera configurations
cameras:
  - name: living_room
    type: tapo
    enabled: true
    params:
      host: 192.168.1.100
      username: your_username
      password: your_password
      
  - name: front_door
    type: ring
    enabled: true
    params:
      email: your@email.com
      password: your_password
      
  - name: pet_cam
    type: furbo
    enabled: true
    params:
      email: your@email.com
      password: your_password
      
  - name: webcam1
    type: webcam
    enabled: true
    params:
      device_id: 0  # Usually 0 for default webcam

# Camera groups
groups:
  indoor:
    - living_room
    - pet_cam
  outdoor:
    - front_door

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

### MCP 2.10.1 Integration

This MCP server communicates via stdio as per the MCP 2.10.1 specification. It's designed to be used with MCP-compatible clients.

### Command Line Interface (Development Only)

For development and testing purposes, you can use the CLI:

```bash
# Start the MCP server (stdio mode, MCP 2.10.1 compliant)
tapo-camera-mcp serve

# For testing with FastAPI (development only)
tapo-camera-mcp serve --test-api --port 8000

# Get camera info (development only)
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

### MCP 2.10.1 Protocol

This server implements the MCP 2.10.1 specification, communicating via stdio. For integration with MCP clients:

1. The server reads JSON-RPC 2.0 requests from stdin
2. Processes the requests
3. Writes JSON-RPC 2.0 responses to stdout

### Python API (Testing Only)

For testing purposes, you can use the Python API:

```python
from tapo_camera_mcp.server import TapoCameraMCPServer

# Create and run the MCP server
server = TapoCameraMCPServer()
server.run()  # Runs in stdio mode for MCP 2.10.1 compatibility
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
# Run unit tests
pytest tests/

# Run MCP protocol tests
pytest tests/test_mcp_protocol.py
```

### Code Style

This project uses `black` for code formatting and `isort` for import sorting. Before committing, run:

```bash
black .
isort .
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
