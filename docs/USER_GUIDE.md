# Tapo Camera MCP - User Guide

## Table of Contents
- [1. Introduction](#1-introduction)
- [2. Getting Started](#2-getting-started)
  - [2.1 Prerequisites](#21-prerequisites)
  - [2.2 Installation](#22-installation)
  - [2.3 Configuration](#23-configuration)
- [3. Web Interface](#3-web-interface)
- [4. Camera Management](#4-camera-management)
  - [4.1 Adding Cameras](#41-adding-cameras)
  - [4.2 Camera Groups](#42-camera-groups)
  - [4.3 Multiple Camera Types](#43-multiple-camera-types)
- [5. Streaming](#5-streaming)
  - [5.1 Web Streaming](#51-web-streaming)
  - [5.2 VLC Streaming](#52-vlc-streaming)
  - [5.3 Multi-View Layouts](#53-multi-view-layouts)
- [6. Advanced Features](#6-advanced-features)
  - [6.1 Motion Detection](#61-motion-detection)
  - [6.2 PTZ Controls](#62-ptz-controls)
  - [6.3 Recording](#63-recording)
- [7. Troubleshooting](#7-troubleshooting)

## 1. Introduction

Tapo Camera MCP is a powerful server for managing multiple IP cameras with support for various brands including TP-Link Tapo, Ring, and Furbo. This guide covers all aspects of setting up and using the server.

## 2. Getting Started

### 2.1 Prerequisites
- Python 3.8+
- pip package manager
- Network access to your cameras
- Camera credentials

### 2.2 Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/tapo-camera-mcp.git
cd tapo-camera-mcp

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e .
```

### 2.3 Configuration
Edit `config.yaml` to set up your cameras and server settings. See the example configuration below:

```yaml
# Server settings
web_enabled: true
web_host: "0.0.0.0"
web_port: 7777
web_username: "admin"
web_password: "change_me"

# Camera configurations
cameras:
  - name: "living_room"
    type: "tapo"
    params:
      host: "192.168.1.100"
      username: "your_email@example.com"
      password: "your_secure_password"
    stream_quality: "hd"
    enabled: true
    motion_detection: true
    recording: false

# More configurations...
```

## 3. Web Interface

Access the web interface at `http://localhost:7777` (or your server's IP address).

![Web Interface](docs/images/web-interface.png)

## 4. Camera Management

### 4.1 Adding Cameras
Add cameras through the web interface or config file. Supported parameters:
- `name`: Unique identifier
- `type`: Camera type (tapo, ring, furbo)
- `params`: Connection parameters
- `stream_quality`: hd or sd
- `enabled`: true/false

### 4.2 Camera Groups
Group cameras for batch operations:
```yaml
camera_groups:
  outdoor: ["front_door", "backyard"]
  all: ["living_room", "front_door", "backyard"]
```

### 4.3 Multiple Camera Types
Supported camera types and their requirements:

| Type  | Required Parameters           | Notes                          |
|-------|------------------------------|--------------------------------|
| Tapo  | host, username, password     | Uses Tapo API                  |
| Ring  | email, password, 2FA token   | Requires Ring account          |
| Furbo | email, password              | Uses Furbo API                 |
| RTSP  | rtsp_url                     | Generic RTSP camera support    |

## 5. Streaming

### 5.1 Web Streaming
Access live streams through the web interface. Supports:
- Individual camera views
- Multi-view layouts (1x1, 2x2, 3x3)
- Fullscreen mode

### 5.2 VLC Streaming
To view streams in VLC:
1. Get the RTSP URL from the web interface
2. Open VLC
3. Media > Open Network Stream
4. Enter URL: `rtsp://your-server:8554/stream/camera_name`

### 5.3 Multi-View Layouts
Create custom layouts in the web interface:
1. Go to Settings > Layouts
2. Create a new layout
3. Drag and drop camera streams
4. Save the layout

## 6. Advanced Features

### 6.1 Motion Detection
Configure motion detection per camera:
```yaml
motion_detection:
  enabled: true
  sensitivity: 0.7  # 0.1 to 1.0
  zones:             # Optional motion zones
    - name: "front_door"
      coordinates: [0,0, 100,0, 100,100, 0,100]  # x1,y1,x2,y2,...
  notifications: true
  snapshot: true
```

### 6.2 PTZ Controls
For PTZ-enabled cameras:
- Pan/Tilt: Click and drag the video
- Zoom: Mouse wheel or +/- buttons
- Presets: Save/recall camera positions

### 6.3 Recording
Configure automatic recording:
```yaml
recording:
  enabled: true
  mode: "motion"  # or "continuous"
  pre_buffer: 5   # seconds before motion
  post_buffer: 10  # seconds after motion
  path: "/path/to/recordings"
  retention_days: 30
```

## 7. Troubleshooting

### Common Issues
1. **Can't connect to camera**
   - Verify network connectivity
   - Check camera credentials
   - Ensure the camera is online

2. **Stream is laggy**
   - Reduce stream quality in settings
   - Check network bandwidth
   - Increase buffer size in config

3. **Web interface is slow**
   - Reduce number of concurrent streams
   - Enable hardware acceleration
   - Check server resources

### Viewing Logs
Server logs are stored in `logs/tapo_camera_mcp.log` by default. Enable debug logging for more detailed information:

```yaml
log_level: "DEBUG"
log_file: "/path/to/logs/tapo_camera_mcp.log"
```

## Support
For additional help, please open an issue on [GitHub](https://github.com/yourusername/tapo-camera-mcp/issues).
