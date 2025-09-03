# Tapo Camera MCP DXT Package

This document provides instructions for building, installing, and using the Tapo Camera MCP DXT package.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- TP-Link Tapo camera (C100, C110, C200, C210, or C310)
- Camera connected to the same network as the MCP server
- Administrator credentials for the Tapo camera

## Building the DXT Package

1. **Clone the repository** (if you haven't already):

   ```bash
   git clone https://github.com/sandraschi/tapo-camera-mcp.git
   cd tapo-camera-mcp
   ```

## Grafana Plugin Setup

---

### Prerequisites

- Node.js 14.x or later
- Grafana 9.5.x or later
- Yarn or npm

### Installation

1. **Navigate to the plugin directory**:

   ```bash
   cd grafana/plugins/tapo-camera-stream
   ```

2. **Install dependencies**:

   ```bash
   npm install
   # or
   yarn install
   ```

3. **Build the plugin**:

   ```bash
   npm run build
   # or
   yarn build
   ```

4. **Start the development server**:

   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Add the plugin to Grafana**:
   - Copy the `tapo-camera-stream` directory to your Grafana plugins directory
   - Or create a symlink from the Grafana plugins directory to this directory
   - Restart Grafana

6. **Enable the plugin**:
   - Log in to Grafana as an administrator
   - Go to Configuration -> Plugins
   - Find "Tapo Camera Stream" and click "Enable"

### Development

- `npm run build` — Build the plugin in production mode
- `npm run dev` — Start development server with hot reload
- `npm run test` — Run tests
- `npm run sign` — Sign the plugin for distribution

2. **Build the DXT package** using the provided build script:
   ```powershell
   # Windows (PowerShell)
   .\build_dxt.ps1
   
   # Linux/macOS
   chmod +x build_dxt.ps1
   pwsh -File build_dxt.ps1
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Run tests (can be skipped with `-NoTests`)
   - Generate the DXT package in the `dist` directory

3. **Verify the DXT package** was created:
   ```
   dist/tapo-camera-mcp-{version}.dxt
   ```

## Installing the DXT Package

1. **Copy the DXT file** to your Claude Desktop packages directory:
   - Windows: `%APPDATA%\Claude\packages\`
   - macOS: `~/Library/Application Support/Claude/packages/`
   - Linux: `~/.config/claude/packages/`

2. **Create a configuration file** at `~/.tapo/config.json` with your camera details:
   ```json
   {
     "camera_ip": "192.168.1.100",
     "username": "admin@example.com",
     "password": "your_password"
   }
   ```

3. **Restart Claude Desktop** to load the new package

4. **Verify installation** by checking the Claude Desktop logs or using the MCP client to list available services

## Using the Tapo Camera MCP Service

Once installed, you can interact with the Tapo Camera MCP service using the Claude Desktop MCP client or any HTTP client.

### Example: Viewing Camera Stream

```python
# Using Python requests
import requests

# Start RTSP stream
response = requests.post(
    "http://localhost:8080/stream/start",
    json={
        "stream_type": "rtsp",
        "quality": "high",
        "with_audio": true
    }
)
stream_url = response.json()["stream_url"]
print(f"Stream URL: {stream_url}")

# Use VLC or another media player to open the stream
# vlc rtsp://username:password@camera-ip:554/stream1
```

### Example: Controlling PTZ

```python
# Move camera up for 2 seconds
response = requests.post(
    "http://localhost:8080/ptz/move",
    json={
        "direction": "up",
        "speed": 50,  # 0-100
        "duration": 2  # seconds
    }
)
print("PTZ response:", response.json())
```

## Available Prompts

The following prompts are available for natural language interaction:

- **Camera Status**: "What is the current status of the {camera_name} camera? Show me {details_level} information."
- **Start Stream**: "Start a {stream_type} stream from the {camera_name} camera with {quality} quality and {with_audio}audio."
- **Stop Stream**: "Stop the {stream_type} stream from the {camera_name} camera."
- **PTZ Control**: "Move the {camera_name} camera {direction} at {speed} speed for {duration} seconds."
- **Motion Detection**: "{enable_disable} motion detection on the {camera_name} camera with {sensitivity} sensitivity."
- **Privacy Mode**: "{enable_disable} privacy mode on the {camera_name} camera."
- **Take Snapshot**: "Take a snapshot from the {camera_name} camera and save it as {filename}."
- **Camera Reboot**: "Reboot the {camera_name} camera {force_option}."
- **Recording Control**: "{start_stop} {recording_type} recording on the {camera_name} camera."
- **Night Vision**: "{enable_disable} night vision on the {camera_name} camera with {mode} mode."

## Troubleshooting

### Common Issues

1. **Connection Issues**:
   - Ensure the camera is powered on and connected to the network
   - Verify the camera's IP address in the configuration
   - Check that the username and password are correct

2. **Streaming Issues**:
   - Make sure the camera supports the requested stream type
   - Check that the required ports are open in your firewall
   - Verify that the camera's firmware is up to date

3. **Authentication Errors**:
   - Double-check the username and password in the configuration
   - Some cameras may require an email address as the username
   - The account may be locked after multiple failed attempts

### Viewing Logs

Logs can be found in the standard Claude Desktop log location:
- Windows: `%APPDATA%\Claude\logs\`
- macOS: `~/Library/Logs/Claude/`
- Linux: `~/.local/share/claude/logs/`

## Development

### Testing Changes

1. Make your changes to the code
2. Run tests:
   ```bash
   pytest -v
   ```
3. Rebuild the DXT package
4. Copy to Claude Desktop packages directory and restart

### Directory Structure

```
tapo-camera-mcp/
├── config/                    # Configuration files
│   └── default.toml          # Default configuration
├── src/
│   └── tapo_camera_mcp/      # Main package
│       ├── __init__.py       # Package initialization
│       ├── server.py         # Main server implementation
│       ├── models.py         # Data models
│       ├── exceptions.py     # Custom exceptions
│       └── cli.py           # Command-line interface
├── tests/                    # Test files
├── dxt_build.py              # DXT package builder
├── build_dxt.ps1             # Build script (PowerShell)
├── dxt_manifest.json         # DXT package manifest
└── pyproject.toml            # Project configuration
```

## License

MIT License - See [LICENSE](LICENSE) for details.
