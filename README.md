# Tapo Camera MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/tapo-camera-mcp)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![MCP Version](https://img.shields.io/badge/MCP-2.12.0-blue)](https://mcp-standard.org)

A FastMCP 2.12.0-compliant MCP server for TP-Link Tapo cameras, providing a unified interface for camera control and monitoring through the MCP protocol.

## 🚀 Features

### 📷 Supported Camera Types
- **Tapo Cameras**: Full support for TP-Link Tapo series
- **Webcams**: Basic support for local webcams
- **Ring Cameras**: Experimental support for Ring devices
- **Furbo Cameras**: Support for Furbo pet cameras

### 🎯 Core Features
- **Unified Camera Interface**: Consistent API across different camera types
- **Modular Architecture**: Easy to extend with new camera types and features
- **Asynchronous I/O**: Built on asyncio for high performance
- **Type Annotations**: Full type hints for better development experience

### 🎥 Camera Controls
- **Live Streaming**: RTSP, RTMP, and HLS streaming support
- **PTZ Control**: Pan, tilt, and zoom (where supported)
- **Motion Detection**: Configurable motion detection settings
- **Snapshot Capture**: Capture still images from video streams
- **Audio Support**: Two-way audio where available

### 🔌 Integrations
- **Grafana Dashboards**: Real-time monitoring and visualization
- **MCP 2.12.0 Protocol**: Seamless integration with MCP ecosystem
- **REST API**: HTTP endpoints for remote control and monitoring
- **Web Interface**: Built-in web UI for camera management

### 🛠 Development Tools
- **CLI Interface**: Command-line tools for administration
- **Mock Camera**: Simulated camera for testing
- **Comprehensive Logging**: Detailed logs for debugging
- **Unit Tests**: Test suite for core functionality

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- FFmpeg (for video processing)
- TP-Link Tapo camera(s) or compatible device

### Installation

1. **Install from PyPI (recommended):**
   ```bash
   pip install tapo-camera-mcp
   ```

2. **Install from source:**
   ```bash
   git clone https://github.com/yourusername/tapo-camera-mcp.git
   cd tapo-camera-mcp
   pip install -e .
   ```

### Configuration

1. Copy the example configuration file:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. Edit `config.yaml` with your camera details:
   ```yaml
   cameras:
     living_room:
       type: tapo
       host: 192.168.1.100
       username: your_username
       password: your_password
   ```

3. Set up environment variables (optional):
   ```bash
   export TAPO_USERNAME=your_username
   export TAPO_PASSWORD=your_password
   ```

## 🚀 Usage

### Starting the Server

```bash
# Start in development mode with debug logging
tapo-camera-mcp --debug

# Start with a specific config file
tapo-camera-mcp --config /path/to/config.yaml

# Start in production mode
tapo-camera-mcp --production
```

### Using the CLI

```bash
# List all available commands
tapo-camera-mcp --help

# Camera Management
tapo-camera-mcp camera list                   # List all cameras
tapo-camera-mcp camera status <camera_name>   # Get camera status
tapo-camera-mcp camera info <camera_name>     # Get detailed camera info

# PTZ Controls
tapo-camera-mcp camera ptz move --direction up --speed 0.5
tapo-camera-mcp camera ptz preset save --name "Home"
tapo-camera-mcp camera ptz preset goto --name "Home"

# Media Controls
tapo-camera-mcp camera snapshot               # Take a snapshot
tapo-camera-mcp camera record start           # Start recording
tapo-camera-mcp camera record stop            # Stop recording

# System Management
tapo-camera-mcp system status                # Check system status
tapo-camera-mcp system restart               # Restart the server
tapo-camera-mcp system update                # Update to the latest version
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

## 🛠 Development

### Project Structure

```
src/tapo_camera_mcp/
├── core/               # Core server implementation
├── camera/             # Camera implementations
│   ├── base.py         # Base camera class
│   ├── tapo.py         # Tapo camera implementation
│   └── ...
├── api/                # API endpoints
│   └── v1/             # API version 1
├── tools/              # MCP tools
│   ├── camera/         # Camera-related tools
│   ├── ptz/            # PTZ controls
│   └── system/         # System tools
├── web/                # Web interface
└── cli_v2.py           # Command-line interface
```

### Setting Up Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/yourusername/tapo-camera-mcp.git
   cd tapo-camera-mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   pre-commit install
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
