# 🏠 Home Security MCP Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.18.0-blue.svg)](https://github.com/sandraschi/tapo-camera-mcp/releases)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![MCP Version](https://img.shields.io/badge/MCP-2.12.0-blue)](https://mcp-standard.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13.0-green.svg)](https://github.com/jlowin/fastmcp)
[![Status](https://img.shields.io/badge/status-Beta-yellow.svg)](https://github.com/sandraschi/tapo-camera-mcp)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](https://github.com/sandraschi/tapo-camera-mcp/actions)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-green.svg)](http://localhost:7777)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Energy Dashboard](https://img.shields.io/badge/Energy%20Dashboard-Operational-success.svg)](http://localhost:7777/energy)
[![Lighting Dashboard](https://img.shields.io/badge/Lighting%20Dashboard-Operational-success.svg)](http://localhost:7777/lighting)
[![Multi-Device](https://img.shields.io/badge/Devices-Tapo%20%7C%20Ring%20%7C%20Nest%20%7C%20Plex%20%7C%20USB-blue.svg)](https://github.com/sandraschi/tapo-camera-mcp)
[![LLM Integration](https://img.shields.io/badge/LLM-Multi--Provider-orange.svg)](https://github.com/sandraschi/tapo-camera-mcp)

⚠️ **BETA**: Comprehensive home security platform in active development. Unified surveillance dashboard with multi-device MCP architecture - serving as both individual device MCP servers AND a complete security monitoring ecosystem. **Status: Beta - Active Development**

> **⚠️ Beta Status Notice**: This project is in active beta development. Features are working but may have bugs, APIs may change between versions, and some integrations are experimental. Not recommended for critical production use. Active development - contributions welcome.

## 🏗️ **DUAL ARCHITECTURE OVERVIEW**

**This repository has evolved into a comprehensive home security platform with dual-role architecture:**

### **🎯 Role 1: Individual Security Device MCP Servers**
**Standalone MCP servers** for specific security device types that can run independently:
- **Tapo Camera MCP**: TP-Link camera control and monitoring
- **USB Webcam MCP**: Direct webcam management
- **Ring MCP**: Doorbell and security camera integration
- **Nest Protect MCP**: Smoke/CO detector monitoring
- **Plex MCP**: Media server integration and webhook handling

### **🎯 Role 2: Unified Security Dashboard**
**Multi-MCP orchestration platform** that coordinates multiple MCP servers:
- **Single Interface**: Monitor all cameras + sensors + alarms + media in one dashboard
- **Cross-System Integration**: Correlate events across different security systems
- **Real-time Monitoring**: Live status updates from all integrated devices
- **Media Integration**: Plex media server webhook support for activity tracking
- **Remote Access**: Mobile monitoring via Tailscale VPN

**The platform serves as the "conductor" that brings together multiple specialized security devices (MCP servers) into a cohesive home surveillance ecosystem.**

## 🏆 **v1.10.0 RELEASE - WEBAPP STABILITY & PLEX INTEGRATION** (January 2026)

**⚠️ BETA STATUS - Active Development:**
- **🔍 Dependency Validator**: Checks all libraries on EVERY startup - no more "it worked yesterday"!
- **👁️ Connection Supervisor**: Polls ALL devices every 60s with auto-reconnect
- **🚨 3-Level Messaging**: Info/Warning/Alarm system with acknowledgement tracking
- **🏥 Health Dashboard**: Real-time device status at `/health-dashboard`
- **📢 Alerts Dashboard**: Message center at `/alerts`
- **📊 Prometheus Integration**: Metrics endpoint for Grafana monitoring
- **📝 Loki-Compatible Logs**: Structured JSON logging for Promtail/Loki
- **📈 Dual-Line Weather Graphs**: Compare main station + bathroom + outdoor modules
- **🔌 Tapo P115 Fixed**: Smart plugs now showing real-time power data
- **🎬 Plex Integration**: Media server webhook support with activity tracking
- **🔗 Complete Routing**: All 25+ webapp pages now functional (no more 404s!)
- **🎨 Enhanced Theming**: Camera cards and status indicators fully theme-aware

**v1.7.0:**
- **🔐 Session-Based Auth**: Complete authentication system with secure password hashing
- **💡 Global Lighting Controls**: All On/Off, 50%, 100%, Disco mode buttons
- **🎨 Color Controls**: Full RGB color picker for color-capable Hue bulbs
- **⚡ Performance**: Near-instant light changes (optimized API calls)
- **🔄 Auto-Refresh**: Periodic device rescan to catch wall switch/remote changes
- **🎯 User Menu**: Dropdown with Settings and Sign Out in topbar

**v1.6.1:**
- **🎙️ SOTA Voice Stack**: Faster-Whisper → Vosk → Whisper (STT), Piper → Edge-TTS → pyttsx3 (TTS)
- **👂 Always-On Wake Word**: OpenWakeWord/Vosk background listener ("hey tapo")
- **🔐 Real Nest OAuth**: Direct Google Nest API integration (no Home Assistant needed!)
- **🎉 Prank Modes**: Hue light chaos/wave/disco/sos + PTZ camera nod/shake/dizzy
- **🔇 Fully Offline**: Zero network traffic for voice - all local processing

**v1.6.0:**
- **📢 TTS/STT**: speak, announce, listen, voice_command actions
- **🎵 Alarm Sounds**: 10 built-in types (siren, beep, doorbell, etc.)
- **📹 PTZ Pranks**: Camera movement fun modes

## 🏆 **v1.5.0 RELEASE - RING & NEST INTEGRATION**

**✅ PREVIOUS:
- **🔔 Ring Doorbell WebRTC**: Live video streaming + push-to-talk (NO subscription required!)
- **🚨 Ring Alerts**: Full-screen DING popup + motion toast notifications on dashboard
- **🎬 Plex Media Server**: Webhook integration for media activity tracking
- **🔥 Nest Protect Setup**: Home Assistant bridge for smoke/CO detector integration
- **📹 Two-Way Talk**: WebRTC audio for speaking to visitors at door
- **🧪 Ring Tests**: Comprehensive pytest suite for Ring client and API
- **📚 Ring Docs**: Full integration guide with subscription comparison
- **🎨 Enhanced UI**: Modern gradient status cards, setup instructions, one-click initialization
- **📱 Ring Dashboard**: Dedicated `/ring` page with device cards, alarm controls, event timeline
- **🔥 Nest Dashboard**: Dedicated `/nest` page with device status, alerts, and Home Assistant integration

**Previous v1.4.0:**
- **💡 Philips Hue Lighting**: 18 lights, 6 groups, 11 predefined scenes, cached device lists
- **🌤️ Netatmo Weather**: Live indoor weather from your station (pyatmo 8.x OAuth)
- **🌍 Vienna External Weather**: Open-Meteo API (free, no key) with 5-day forecast
- **🍳 Kitchen Dashboard**: Tefal Optigrill, Zojirushi water boiler integration
- **🤖 Robots Dashboard**: Roomba, Unitree Go2 planned integrations

**🎯 Current Status**: Beta - Full smart home platform with Ring doorbell, lighting, weather, kitchen, and robots dashboards. **Active development - features may change.**

## 🚀 **DUAL ARCHITECTURE CAPABILITIES** (November 2025)

### **🎯 ASPECT 1: INDIVIDUAL MCP SERVERS**

#### ✅ **WORKING NOW**
- **🎥 Tapo Camera MCP**: TP-Link Tapo camera control and monitoring
- **📹 USB Webcam MCP**: Auto-detection and management
- **🤖 Claude Desktop Integration**: MCP protocol compliance for AI assistants
- **🔧 Camera Management Tools**: Add, configure, and control cameras
- **📊 Real-time Status**: Camera connection health and diagnostics

#### 🎯 **CORE MCP FEATURES**
- **MCP 2.12.0 Protocol**: Full Model Context Protocol compliance
- **Modular Camera Types**: Extensible architecture for new camera brands
- **Asynchronous Operations**: High-performance async I/O
- **Type-Safe APIs**: Full type hints and Pydantic validation

### **🎯 ASPECT 2: UNIFIED SECURITY DASHBOARD**

#### ✅ **WORKING NOW**
- **🏠 Live Security Dashboard**: Single interface at `localhost:7777`
- **🔗 Multi-MCP Integration**: Connect multiple security MCP servers
- **📊 Real-time Monitoring**: Cameras + sensors + alarms in one view
- **🚨 Alert Aggregation**: Unified security event display
- **📱 Mobile Access**: Works on iPad/iPhone via Tailscale

#### 🎯 **CORE DASHBOARD FEATURES**
- **Multi-Server Coordination**: Nest Protect, Ring, and other MCPs
- **Security Event Correlation**: Cross-system alert analysis
- **Professional UI/UX**: Responsive design with real-time updates
- **Remote Monitoring**: Access anywhere via secure VPN

### 📷 **SUPPORTED CAMERA TYPES**
- **✅ USB Webcams**: Auto-detected with live thumbnails (WORKING)
- **✅ Tapo Cameras**: TP-Link Tapo series with full control
- **✅ Ring Cameras**: Ring doorbell and security cameras
- **🐱 Petcube Cameras**: Petcube pet cameras with full API access (READY)

### 🤖 **LLM INTEGRATION** (NEW in v1.3.0)
- **Ollama**: Local LLM support with model management
- **LM Studio**: Desktop LLM integration
- **OpenAI**: Cloud-based AI capabilities
- **Chatbot UI**: Floating chat interface with streaming support
- **API Access**: Complete REST API for LLM operations

### 🐳 **DOCKER DEPLOYMENT** (NEW in v1.3.0)
- **MyHomeControl Stack**: Complete Docker Compose setup
- **Production Builds**: Optimized images with minimal dependencies
- **Health Monitoring**: Container health checks and monitoring
- **Network Integration**: Unified Docker network for all services

## 🔄 **MCP CLIENT ARCHITECTURE** (v1.17.0)

### **🏗️ Unified Communication Layer**

**All web API endpoints now use MCP client architecture** instead of direct manager calls, providing:

- **🔗 Standardized Protocol**: Consistent MCP stdio communication across all APIs
- **🧪 Enhanced Testability**: Comprehensive mocking and integration testing
- **⚡ Better Performance**: Async connection pooling and optimized tool calls
- **🔧 Improved Maintainability**: Clean separation between web and business logic
- **🚀 Future-Proof**: Extensible architecture for new MCP integrations

### **🛠️ MCP Tool Integration**

#### **Portmanteau Tools** - Consolidated Operations
- `energy_management` - Smart plug and energy monitoring
- `motion_management` - Motion detection and camera events
- `camera_management` - Camera control and streaming
- `ptz_management` - Pan-Tilt-Zoom operations
- `media_management` - Media capture and streaming
- `system_management` - System operations and logging
- `medical_management` - Medical device control
- `security_management` - Security system integration
- `lighting_management` - Lighting control systems

#### **Migration Benefits**
```python
# Before (Direct Manager Calls)
from ...tools.energy.tapo_plug_tools import tapo_plug_manager
devices = await tapo_plug_manager.get_all_devices()

# After (MCP Client)
result = await call_mcp_tool("energy_management", {"action": "status"})
devices = result.get("data", {}).get("devices", [])
```

### **🧪 Enterprise Testing Infrastructure**

#### **Comprehensive Test Coverage** (120+ test methods)
- **Unit Tests**: 92% coverage with isolated component testing
- **Integration Tests**: Full MCP client-server interaction validation
- **Performance Tests**: Automated benchmarking and regression detection
- **API Contract Tests**: OpenAPI specification validation
- **Cross-Platform Tests**: Windows, macOS, Linux compatibility

#### **Advanced Testing Features**
- **Mock MCP Server**: Configurable mock server for realistic testing
- **Test Data Factories**: Consistent, realistic test data generation
- **Performance Timers**: Built-in response time validation
- **Async Testing Support**: Comprehensive asyncio testing utilities
- **CI/CD Integration**: Automated testing pipeline with artifact generation

### **📊 Production-Ready CI/CD**

#### **10 Comprehensive Pipeline Jobs**
1. **Quality Checks**: Linting, type checking, security scanning
2. **Unit Tests**: Multi-version Python testing with coverage
3. **Integration Tests**: MCP protocol and component interaction testing
4. **API Contract Tests**: Live server API validation
5. **Performance Tests**: Benchmarking and load testing
6. **Security Tests**: Vulnerability scanning and dependency analysis
7. **Cross-Platform Tests**: Windows, macOS, Linux compatibility validation
8. **Container Tests**: Docker image validation and health checks
9. **Deployment Tests**: Production deployment validation
10. **Test Reporting**: Comprehensive results and artifact generation

### ⚠️ **UNSUPPORTED CAMERAS**
- **🚫 Furbo Cameras**: **NOT SUPPORTED** - Furbo intentionally blocks third-party API access. Use official Furbo app only.

### 🐾 **PETCUBE INTEGRATION** ⭐

**Petcube Bites 2 Lite** is now fully supported as an excellent Furbo replacement!

#### **🎥 Camera Features:**
- **1080p Full HD** video with night vision
- **160° wide-angle** lens
- **Two-way audio** with noise cancellation
- **Motion detection** with smart alerts
- **Cloud storage** (30 days free)

#### **🍖 Smart Features:**
- **Dual treat compartments** (vs Furbo's single)
- **Laser pointer** for interactive play
- **Auto-play** mode with built-in toys
- **Custom feeding schedules**
- **Medication dispensing** capability

#### **🔋 Battery & Connectivity:**
- **12-hour battery life** (rechargeable)
- **WiFi + Bluetooth** connectivity
- **Mobile app** for iOS/Android
- **Alexa/Google Home** integration

#### **💰 Pricing & Value:**
- **Price:** $199-249 (vs Furbo's $249-349)
- **Better value:** More features, lower price
- **API access:** Full third-party integration
- **Where to buy:** Amazon, Petcube website, pet stores

#### **🔧 MCP Configuration:**
```yaml
cameras:
  my_petcube:
    type: petcube
    params:
      email: "your_petcube_account@example.com"
      password: "your_password"
      device_id: "optional_device_id"  # Auto-detected if not specified
```

#### **🎮 MCP Features:**
- ✅ **Live video streaming**
- ✅ **Remote treat dispensing**
- ✅ **Motion/sound alerts**
- ✅ **Battery monitoring**
- ✅ **Status tracking**
- ✅ **Automated pet care**

#### **🚀 Why Petcube Over Furbo:**
| Feature | Furbo ❌ | Petcube ✅ |
|---------|----------|------------|
| **API Access** | Blocked | ✅ Official API |
| **Treat Compartments** | 1 | 2 |
| **Interactive Toys** | Limited | Laser + Auto-play |
| **Third-party Apps** | Forbidden | ✅ Allowed |
| **Price** | $249-349 | $199-249 |
| **MCP Integration** | ❌ Impossible | ✅ Full support |

**Petcube is the clear winner for API-accessible pet cameras!** 🐱✨

### 🎥 **CAMERA CONTROLS** (Next Phase)
- **Live Streaming**: RTSP, RTMP, and HLS streaming support
- **PTZ Control**: Pan, tilt, and zoom (where supported)
- **Motion Detection**: Configurable motion detection settings
- **Snapshot Capture**: Capture still images from video streams
- **Audio Support**: Two-way audio where available

### 🔌 **INTEGRATIONS**

#### **🔗 MCP SERVER ECOSYSTEM** (Dual Role)
**This repository serves dual purposes:**
1. **🎥 Individual MCP Servers**: Standalone camera control (Tapo, USB, Ring)
2. **🏠 Unified Security Dashboard**: Multi-MCP orchestration platform

#### **🔗 Multi-MCP Coordination** (Dashboard Role)
- **Nest Protect MCP**: Real-time smoke/CO detector monitoring
- **Ring MCP**: Doorbell and security camera integration
- **Unified Dashboard**: Single interface for all security devices
- **Cross-System Alerts**: Correlated security events and notifications
- **Health Monitoring**: Real-time status of all integrated MCP servers

#### **🤖 Claude Desktop Integration** (MCP Server Role)
- **✅ MCP 2.12.0 Protocol**: Seamless Claude Desktop integration (WORKING)
- **🔧 Camera Management Tools**: Add, configure, and control cameras
- **📊 Real-time Status**: Camera connection health and diagnostics
- **🎯 AI Assistant Ready**: Full MCP compliance for intelligent camera control

#### **🌐 Web & API Interfaces** (Dashboard Role)
- **🏠 Live Security Dashboard**: Real-time monitoring at `localhost:7777`
- **🔌 REST API**: HTTP endpoints for remote control and monitoring
- **📊 Grafana Dashboards**: Real-time monitoring and visualization (planned)
- **📱 Mobile Access**: Works on iPad/iPhone via Tailscale

### 📺 **VIDEO STREAMING DASHBOARD** (Next Phase)
- **Live Video Streams**: Real-time MJPEG streaming from USB webcams
- **RTSP Integration**: Direct streaming from Tapo cameras
- **Dynamic Camera Management**: Add/remove cameras on the fly

### 🎯 **DEVICE ONBOARDING SYSTEM** (NEW - January 2025)
- **Progressive Discovery**: Automatic scanning for Tapo P115, Nest Protect, Ring devices, and USB webcams
- **Smart Configuration**: User-friendly device naming, location assignment, and settings
- **Authentication Integration**: OAuth setup for Nest Protect and Ring devices
- **Cross-Device Integration**: Intelligent recommendations for device combinations
- **Beautiful Progressive UI**: Step-by-step onboarding with real-time progress tracking
- **Error Recovery**: Comprehensive error handling with user guidance
- **API-First Design**: Full programmatic access to onboarding functionality

### 💪 **STABILITY & MONITORING SYSTEM** (NEW - December 2025)

#### 🔍 **Beta Reliability Features**
- **Dependency Validator**: Checks all 20+ libraries on every startup - prevents "it worked yesterday" failures
- **Connection Supervisor**: Polls ALL devices every 60s with automatic reconnection
- **3-Level Alerting**: Info (💬) / Warning (⚠️) / Alarm (🚨) system with escalation
- **Health Dashboard**: Real-time device status at `/health-dashboard`
- **Alerts Dashboard**: Message center with acknowledgement at `/alerts`
- **Demo-Proof**: No silent failures during demonstrations!

#### 📊 **Monitoring Stack Integration**
- **Prometheus Metrics**: `/api/messages/prometheus` endpoint ready for scraping
- **Loki Logs**: Structured JSON logging compatible with Promtail ingestion
- **Grafana Ready**: Dashboards for device uptime, alert timelines, power consumption
- **Alert Escalation**: 1 failure → WARNING, 3 failures (180s) → ALARM
- **Auto-Recovery**: Supervisor attempts reconnection on device failures

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'tapo_home'
    static_configs:
      - targets: ['localhost:7777']
    metrics_path: '/api/messages/prometheus'
    scrape_interval: 30s
```

### ⚡ **ADVANCED FEATURES** (NEW - January 2025)

#### 🔋 **Energy Management Dashboard**
- **Tapo P115 Smart Plugs**: Energy monitoring and control (REAL DATA!)
- **Real-time Power Consumption**: Live wattage, voltage, and current monitoring
- **Cost Analysis**: Daily, monthly, and annual energy cost tracking
- **Smart Scheduling**: Automated power management based on usage patterns
- **Energy Saving Mode**: Intelligent power optimization
- **Historical Data**: Limited to current day (P115 limitation) with Home Assistant integration recommended

#### 💡 **Lighting Control Dashboard** (ENHANCED in v1.7.0)
- **Philips Hue Integration**: Full support for Hue Bridge and lights
- **Light Discovery**: Automatic discovery (18 lights, 6 groups detected)
- **Light Control**: On/off toggle and brightness adjustment (instant response)
- **Color Controls**: Full RGB color picker for color-capable bulbs
- **Global Controls**: Quick action buttons (All On/Off, 50%, 100%, Disco mode)
- **Group Management**: Support for Hue groups/rooms with bulk control
- **Scene Activation**: 11 predefined scenes (Sunset, Aurora, Energize, etc.)
- **Performance Caching**: Device lists cached on startup for instant page loads
- **Auto-Refresh**: Periodic rescan every 2 minutes to catch wall switch changes
- **Rescan Button**: Manual refresh of lights/groups/scenes with last scan timestamp
- **Settings Integration**: Bridge IP and username configuration via settings page

#### 🌤️ **Weather Dashboard** (ENHANCED v1.8.0)
- **Multi-Module Netatmo**: Main station + bathroom module (NAModule4 support)
- **Dual-Line Graphs**: Compare main (red) vs bathroom (orange) vs outdoor (teal)
- **Real-Time Data**: 26.8°C main, 26.6°C bathroom - see room differences!
- **Vienna External Weather**: Open-Meteo API (5.5°C, slight rain)
- **Dynamic Station Cards**: Auto-loads YOUR real devices (70:ee:50:3a:0e:dc @ Stroheckgasse)
- **5-Day Forecast**: Daily forecast with weather icons
- **Historical Charts**: 4 metrics × 3 time ranges, auto-refresh every 30s
- **CO2 Monitoring**: Threshold warnings (800 ppm yellow, 1000 ppm red)
- **Battery Indicators**: Shows battery level for wireless modules (🔋 60%)
- **Outdoor Sensor Ready**: Automatic detection when NAModule1 installed

#### 🍳 **Kitchen Dashboard** (NEW in v1.4.0)
- **Tefal Optigrill**: Smart grill status and control
- **Zojirushi Water Boiler**: On/off via Tapo P115 smart plug
- **Smarter iKettle**: Alternative smart kettle research

#### 🤖 **Robots Dashboard** (NEW in v1.4.0)
- **Roomba**: Coming soon integration
- **Unitree Go2**: Planned purchase with specs
- **Pilot Labs Moorebot Scout**: AI home patrol robot (arriving Jan 2025)

#### 🚨 **Alarm System Integration**
- **Nest Protect**: Smoke and CO detector monitoring
- **Ring Alarms**: Door/window sensors and motion detectors
- **Alert Correlation**: Cross-system event analysis with camera feeds
- **Battery Monitoring**: Device health and maintenance alerts
- **Test Scheduling**: Automated device testing and validation

#### 📊 **AI-Powered Analytics**
- **Scene Analysis**: Computer vision-based scene understanding
- **Object Detection**: People, vehicles, and activity recognition
- **Performance Analytics**: System health and optimization recommendations
- **Smart Automation**: Intelligent scheduling and predictive maintenance
- **Pattern Recognition**: Usage pattern analysis and optimization

#### 📈 **Advanced Dashboard Components**
- **Energy Charts**: Lightweight Chart.js-based energy consumption visualization
- **Real-time Updates**: Live data refresh every minute
- **Interactive Controls**: Device management and automation configuration
- **Mobile Responsive**: Optimized for tablet and smartphone access
- **Export Capabilities**: Chart and data export functionality

## 🚀 **QUICK START** (What Works Now)

### **1. Start the Web Dashboard**
```bash
# Start dashboard with auto-USB webcam detection
python start.py dashboard
```
**Result**: Dashboard at `http://localhost:7777` with USB webcam monitoring

### **2. Check Claude Desktop Integration**
```bash
# MCP server should load automatically in Claude Desktop
# Look for Tapo Camera tools in Claude
```

### **3. Current Working Features**
- ✅ **USB Webcam Detection**: Auto-discovered on dashboard load
- ✅ **Real-time Status**: Camera connection monitoring
- ✅ **Professional UI**: Clean, responsive dashboard interface
- ✅ **MCP Tools**: 30+ tools available in Claude Desktop (FastMCP 2.12 compliant)
  - **Device Onboarding**: Progressive discovery and configuration tools
  - **Energy Management**: Tapo P115 smart plug control and monitoring
  - **Lighting Control**: Philips Hue Bridge integration (18 lights, 11 scenes)
  - **Weather Integration**: Netatmo indoor + Vienna external weather
  - **Security Integration**: Nest Protect and Ring device management
  - **AI Analytics**: Performance monitoring and intelligent automation

### **4. Next Steps** (Tapo Camera Integration)
```bash
# Once we resolve authentication:
# Add your C200 cameras with correct credentials
# Enable live video streaming in dashboard
# Full camera control through Claude
```
- **Stream Controls**: Start/stop streaming per camera
- **Responsive Design**: Works on desktop and mobile browsers
- **Real-time Status**: Live camera status and health monitoring
- **Snapshot Capture**: Instant image capture from any camera
- **Multi-camera View**: Grid layout for multiple camera feeds

### 🛠 Development Tools
- **CLI Interface**: Command-line tools for administration
- **Mock Camera**: Simulated camera for testing
- **Comprehensive Logging**: Structured logging throughout codebase
- **Unit Tests**: Complete test suite with 100% pass rate
- **CI/CD Pipeline**: GitHub Actions with modern ruff linting, caching, and Python 3.10-3.12 testing
- **Security Scanning**: Automated vulnerability and dependency scanning
- **Code Quality**: Ruff linting and formatting, mypy type checking, pylint linting

## 🚀 Getting Started

### 🎯 **Device Onboarding** (NEW!)

**Progressive device setup for any combination of devices:**

```bash
# Start the server
python -m tapo_camera_mcp.web.server

# Open the onboarding dashboard
open http://localhost:7777/onboarding
```

**Supported Device Types:**
- **Tapo P115 Smart Plugs**: Energy monitoring and control
- **Nest Protect Devices**: Smoke and CO detector monitoring  
- **Ring Devices**: Doorbell, motion sensors, and contact sensors
- **USB Webcams**: Video streaming and capture

**Features:**
- **Automatic Discovery**: Network scanning for all supported devices
- **Smart Configuration**: User-friendly naming and location assignment
- **Cross-Device Integration**: Intelligent automation recommendations
- **Progressive UI**: Step-by-step guided setup process

### Installation Options

This MCP server supports multiple installation methods:

1. **MCPB Package** (Recommended) - One-click installation for Claude Desktop
2. **Manual Installation** - Clone repository and install via pip/uv
3. **JSON Config File** - Add to Claude Desktop or Cursor IDE config files

---

#### Option 1: MCPB Package (Recommended for Claude Desktop)

**One-click installation** for Claude Desktop users:

1. Download the latest `.mcpb` package from [GitHub Releases](https://github.com/sandraschi/tapo-camera-mcp/releases)
2. Drag the `.mcpb` file to Claude Desktop
3. Configure camera settings when prompted:
   - Tapo Camera IP Address (optional)
   - Tapo Camera Username (optional)
   - Tapo Camera Password (optional)
   - Web Dashboard Port (default: 7777)
4. Restart Claude Desktop
5. All 26+ tools are now available!

**Quick Start with MCPB:**
```
"Connect to my USB webcam using add_camera tool"
"Start the dashboard and show me the camera feed"
```

**See [MCPB Quick Start Guide](docs/MCPB_QUICKSTART.md) for detailed instructions.**

---

#### Option 2: Manual Installation (Clone & Install)

**For developers or users who prefer manual setup:**

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- OpenCV (for webcam support)
- TP-Link Tapo camera(s), Ring doorbell, or USB webcam

### Version Manager Installation (Recommended)

Using version managers ensures you have the correct Python and Node.js versions without conflicts.

#### Python Version Management with uv (or pyenv)

**uv** is a fast Python package installer and resolver (similar to nvm for Node.js). Alternatively, you can use **pyenv** for Python version management:

```powershell
# Windows (PowerShell)
# Install uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install Python 3.11 (or 3.10, 3.12)
uv python install 3.11

# Create virtual environment with specific Python version
uv venv --python 3.11

# Activate virtual environment
.\venv\Scripts\activate

# Install project dependencies
uv pip install -e ".[dev]"
```

```bash
# macOS/Linux
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.11 (or 3.10, 3.12)
uv python install 3.11

# Create virtual environment with specific Python version
uv venv --python 3.11

# Activate virtual environment
source .venv/bin/activate

# Install project dependencies
uv pip install -e ".[dev]"
```

**Alternative: Using pyenv for Python version management:**

```bash
# macOS/Linux
# Install pyenv
curl https://pyenv.run | bash

# Add to shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install project dependencies
pip install -e ".[dev]"
```

#### Node.js Version Management with nvm or nvx (Optional)

If you need Node.js for Grafana plugins or other frontend components:

**Option 1: Using nvm (Node Version Manager)**

```powershell
# Windows (PowerShell)
# Install nvm-windows from: https://github.com/coreybutler/nvm-windows/releases
# Or use Chocolatey:
choco install nvm

# Install Node.js 20 LTS
nvm install 20
nvm use 20

# Verify installation
node --version
npm --version
```

```bash
# macOS/Linux
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc

# Install Node.js 20 LTS
nvm install 20
nvm use 20

# Verify installation
node --version
npm --version
```

**Option 2: Using nvx (Universal NVM - Cross-platform)**

nvx is a universal Node.js version manager that works on both Unix and Windows:

```bash
# Install nvx via npm (requires npm 5.2.0+)
npm install -g nvx

# Run commands with specific Node.js version
nvx 20 node --version

# Or install and use a specific version
nvx install 20
nvx use 20

# Verify installation
node --version
npm --version
```

### Installation

1. **Install from source (recommended):**
   ```bash
   git clone https://github.com/yourusername/tapo-camera-mcp.git
   cd tapo-camera-mcp
   pip install -e .
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
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
     webcam:
       type: webcam
       device_id: 0
   
   # Authentication (optional - disabled by default)
   auth:
     enabled: false  # Set to true to require login
     users:
       admin:
         password: admin123  # Change this!
         role: admin
   ```

### 🔐 **Authentication** (NEW in v1.7.0)

The dashboard supports optional session-based authentication:

**Enable Authentication:**
1. Edit `config.yaml` and set `auth.enabled: true`
2. Configure users with passwords
3. Restart the server
4. Access dashboard at `http://localhost:7777` - you'll be redirected to login

**Features:**
- **Secure Password Hashing**: PBKDF2-SHA256 with salt
- **Session Management**: 24-hour sessions (30 days with "remember me")
- **User Menu**: Dropdown in topbar with Settings and Sign Out
- **Auto-Redirect**: Logged-in users can't access login page
- **Public Paths**: Login, static files, and API endpoints remain accessible

**Default User:**
When auth is first enabled, a default admin user is created with a random password (printed to console). Change it immediately in `config.yaml`!

---

#### Option 3: JSON Config File Installation (Claude Desktop / Cursor IDE)

**For users who prefer manual JSON configuration:**

After cloning and installing the repository, add the server to your MCP client configuration file.

**Claude Desktop Configuration:**

Edit `~/.config/claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "tapo-camera-mcp": {
      "command": "python",
      "args": ["-m", "tapo_camera_mcp.server_v2", "--direct"],
      "cwd": "D:/Dev/repos/tapo-camera-mcp",
      "env": {
        "PYTHONPATH": "D:/Dev/repos/tapo-camera-mcp",
        "TAPO_MCP_SKIP_HARDWARE_INIT": "true"
      }
    }
  }
}
```

**Fast Startup Option:**

If the server takes too long to start (>1 minute), add `TAPO_MCP_SKIP_HARDWARE_INIT=true` to the `env` section. This skips hardware initialization during startup - hardware will initialize automatically on first use. This reduces startup time from 30-60 seconds to <5 seconds.

**Without fast startup:** Server initializes all hardware (cameras, Hue, Netatmo, Ring, etc.) during startup (10s timeout)
**With fast startup:** Server starts immediately, hardware initializes on-demand when tools are used

**Cursor IDE Configuration:**

Edit Cursor settings (Cmd+, on Mac or Ctrl+, on Windows) → MCP tab, or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "tapo-camera-mcp": {
      "command": "python",
      "args": ["-m", "tapo_camera_mcp.server_v2", "--direct"],
      "cwd": "D:/Dev/repos/tapo-camera-mcp",
      "env": {
        "PYTHONPATH": "D:/Dev/repos/tapo-camera-mcp"
      }
    }
  }
}
```

**Important Notes:**
- Replace `D:/Dev/repos/tapo-camera-mcp` with your actual repository path
- Use absolute paths (not relative)
- Ensure Python 3.10+ is in your PATH
- Restart Claude Desktop or Cursor after configuration
- Verify installation by asking Claude/Cursor: "List available camera tools"

**Troubleshooting JSON Config:**
- Check Python path: `python --version` or `python3 --version`
- Verify module exists: `python -m tapo_camera_mcp.server_v2 --help`
- Check logs: `%APPDATA%\Claude\logs\` (Windows) or `~/.config/claude/logs/` (macOS/Linux)

**Fast Startup (Skip Hardware Init):**

If the server takes more than 1 minute to start, add `TAPO_MCP_SKIP_HARDWARE_INIT=true` to the `env` section:

```json
{
  "mcpServers": {
    "tapo-camera-mcp": {
      "command": "python",
      "args": ["-m", "tapo_camera_mcp.server_v2", "--direct"],
      "cwd": "D:/Dev/repos/tapo-camera-mcp",
      "env": {
        "PYTHONPATH": "D:/Dev/repos/tapo-camera-mcp",
        "TAPO_MCP_SKIP_HARDWARE_INIT": "true"
      }
    }
  }
}
```

This skips hardware initialization during startup (reduces startup from 30-60s to <5s). Hardware will initialize automatically when tools are first used.

---

## 🚀 Usage

### Starting the MCP Server

```bash
# Start MCP server for Claude Desktop integration
python -m tapo_camera_mcp.server_v2 --direct

# Start with debug logging
python -m tapo_camera_mcp.server_v2 --direct --debug
```

### Starting the Web Dashboard

```bash
# Start the web dashboard (separate terminal)
python -m tapo_camera_mcp.web.server

# Dashboard will be available at: http://localhost:7777
```

### Quick Start Script

```bash
# Check dependencies
python start.py check

# Test webcam
python start.py test

# Start MCP server only
python start.py mcp

# Start dual interface server (MCP + REST API)
python start.py dual

# Start web dashboard only
python start.py dashboard

# Start both services
python start.py both

# Test webcam and start dashboard
python start.py webcam
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

### Web Dashboard Endpoints

- `GET /` - Main dashboard page
- `GET /api/cameras` - Get list of all cameras
- `GET /api/cameras/{camera_id}/stream` - Get video stream (MJPEG/RTSP)
- `GET /api/cameras/{camera_id}/snapshot` - Get camera snapshot
- `GET /api/status` - Get server status

### MCP Tools

#### Camera Management
- `list_cameras` - List all registered cameras
- `add_camera` - Add a new camera to the system
- `connect_camera` - Connect to a specific camera
- `disconnect_camera` - Disconnect from camera
- `get_camera_info` - Get detailed camera information
- `get_camera_status` - Get camera status and health

#### PTZ Controls
- `move_ptz` - Move PTZ camera (pan, tilt, zoom)
- `get_ptz_position` - Get current PTZ position
- `save_ptz_preset` - Save current position as preset
- `recall_ptz_preset` - Move to saved preset position
- `go_to_home_ptz` - Return to home position
- `stop_ptz` - Stop PTZ movement

#### Media Operations
- `capture_image` - Capture still image from camera
- `start_recording` - Start video recording
- `stop_recording` - Stop video recording
- `get_recording_status` - Get recording status

#### System Management
- `get_system_info` - Get camera system information
- `reboot_camera` - Reboot the camera
- `get_logs` - Get system logs
- `set_motion_detection` - Configure motion detection
- `set_led_enabled` - Control LED status
- `set_privacy_mode` - Enable/disable privacy mode

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

### Building MCPB Package

To build an MCPB package for distribution:

```powershell
# Windows (PowerShell)
.\scripts\build-mcpb-package.ps1 -NoSign

# Or build manually
mcpb pack . dist/tapo-camera-mcp.mcpb
```

The package will be created in `dist/tapo-camera-mcp.mcpb` (approximately 280KB).

**For automated builds**: Push a version tag to trigger GitHub Actions:
```bash
git tag v1.0.0
git push origin v1.0.0
```

### Running Tests

```bash
# Run unit tests with coverage
pytest tests/unit/ --cov=tapo_camera_mcp --cov-report=html

# Run all tests
pytest tests/ -v

# Run MCP protocol tests
pytest tests/test_mcp_protocol.py

# Run with specific Python version (in CI/CD)
python -m pytest --cov=tapo_camera_mcp --cov-report=xml
```

### Code Style

This project uses `ruff` for code linting and formatting. Before committing, run:

```bash
ruff check src/ tests/
ruff format src/ tests/
pylint tapo_camera_mcp/
```

## 📦 MCPB Packaging

This project supports **MCPB (MCP Bundle)** packaging for one-click installation in Claude Desktop.

**For Users:**
- Download `.mcpb` file from [Releases](https://github.com/sandraschi/tapo-camera-mcp/releases)
- Drag to Claude Desktop
- Configure and enjoy!

**For Developers:**
- See [MCPB Quick Start](docs/MCPB_QUICKSTART.md)
- Build with `.\scripts\build-mcpb-package.ps1 -NoSign`
- Full guide in [docs/mcpb-packaging/](docs/mcpb-packaging/)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [TP-Link](https://www.tp-link.com/) for their Tapo camera products
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Anthropic](https://www.anthropic.com/) for Claude Desktop and MCPB toolkit
- [Ring](https://ring.com/) for Ring doorbell integration

**Note:** Furbo cameras are not supported due to their intentional API restrictions. Use the official Furbo app for Furbo camera access.
- [aiohttp](https://docs.aiohttp.org/) for the async HTTP client/server
- [ONVIF](https://www.onvif.org/) for the camera control protocol

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
# Trigger workflow test
# Trigger CI
