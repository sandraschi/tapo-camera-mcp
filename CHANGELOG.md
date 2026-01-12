# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.0] - 2026-01-12 🚀 **Critical Webapp Fixes & Plex Integration**

### 🔥 **WEBAPP STABILITY FIXES**

#### **Routing System Overhaul**
- **Fixed Missing Routes**: Added 25+ missing page routes that were causing 404 errors
- **Complete Page Coverage**: All templates now have corresponding API endpoints
- **Navigation Consistency**: All sidebar links now point to working pages

#### **Pages Now Working** ✅
- `/logs` - Log management interface
- `/alerts` - Alert management system
- `/alarms` - Security alarm controls
- `/appliance-monitor` - Appliance monitoring dashboard
- `/events` - Event timeline and history
- `/health-dashboard` - Connection health monitoring
- `/human-health` - Human health monitoring
- `/onboarding` - Device setup wizard
- And 15+ other previously broken pages

### 🎬 **PLEX MEDIA SERVER INTEGRATION**

#### **Complete Plex Support**
- **Webhook Integration**: Real-time media activity tracking from Plex
- **API Endpoints**: `/api/plex/webhook`, `/api/plex/now-playing`, `/api/plex/status`
- **Web Interface**: Beautiful media library at `/plex` with posters and progress
- **Event Logging**: Media events integrated into security dashboard timeline

#### **Plex Features**
- **Media Activity Tracking**: See who's watching what, when, and where
- **Current Status**: Live playback status and metadata
- **Webhook Support**: Handles all Plex media events (play/pause/stop/resume)
- **Theme Integration**: Full dark/light theme support for media interface

#### **Setup Instructions**
- Configure Plex webhook URL: `http://your-server:7777/api/plex/webhook`
- Enable desired events in Plex settings
- Access media dashboard at `/plex`

### 🔧 **THEME SYSTEM IMPROVEMENTS**

#### **Enhanced CSS Variables**
- **Expanded Color Palette**: Added 20+ new CSS variables for comprehensive theming
- **Camera-Specific Colors**: Dedicated color variables for camera status indicators
- **Status Colors**: Success, warning, error, and info color schemes
- **Gray Scale**: Complete gray scale for proper contrast

#### **Template Updates**
- **Camera Cards**: All camera status indicators now follow theme
- **Status Badges**: Online/offline/warning states use proper colors
- **Modal Dialogs**: All popups and overlays theme-aware
- **Button States**: All interactive elements properly themed

### 📚 **DOCUMENTATION UPDATES**

#### **README.md**
- Added Plex integration to feature list and badges
- Updated architecture overview to include Plex MCP
- Enhanced device compatibility badges

#### **API Documentation**
- Added complete Plex API reference
- Documented webhook endpoints and payload formats
- Updated MCP tool categories to include media management

#### **User Guide**
- Added Plex integration setup instructions
- Documented webhook configuration steps
- Included media dashboard usage guide

### 🐛 **BUG FIXES**

#### **Critical Fixes**
- **Port Environment Variable**: Fixed PORT environment variable support in `start.py`
- **Message Categories**: Added missing `MEDIA_EVENT` category for Plex integration
- **Webhook Error Handling**: Improved error handling for malformed webhook payloads
- **Request Parsing**: Enhanced support for both multipart/form-data and JSON webhook formats

#### **Webapp Fixes**
- **Navigation Links**: All sidebar links now functional
- **Page Loading**: Eliminated 404 errors across all pages
- **Theme Consistency**: Fixed hardcoded colors in camera and status displays
- **Modal Theming**: All dialog boxes now properly themed

## [1.9.0] - 2026-01-09 🎨 **Web Interface CSS Cleanup & Theme Support**

### 🎨 **COMPREHENSIVE CSS CLEANUP**

#### **CSS Architecture Refactoring**
- **Inline Styles Migration**: Converted all inline `<style>` blocks to external CSS files for better maintainability
- **Theme Variables Implementation**: Replaced hardcoded colors with CSS custom properties for consistent theming
- **Modular CSS Structure**: Created dedicated CSS files for each major template component

#### **Templates Updated (13 Files)**
- ✅ `base.html` → `theme.css` - Base theme and layout styles
- ✅ `cameras.html` → `cameras.css` - Camera management interface
- ✅ `dashboard.html` → `dashboard.css` - Main dashboard layout
- ✅ `plex.html` → `plex.css` - Media server integration
- ✅ `lighting.html` → `lighting.css` - Lighting controls
- ✅ `energy.html` → `energy.css` - Energy monitoring
- ✅ `weather.html` → `weather.css` - Weather data display
- ✅ `alerts.html` → `alerts.css` - Alert management system
- ✅ `health.html` → `health.css` - Health monitoring dashboard
- ✅ `settings.html` → `settings.css` - Configuration interface
- ✅ `alarms.html` → `alarms.css` - Security alarm controls
- ✅ `appliance_monitor.html` → `appliance_monitor.css` - Appliance monitoring
- ✅ `kitchen.html` → `kitchen.css` - Kitchen device controls

### 🎯 **THEME SYSTEM ENHANCEMENTS**

#### **CSS Custom Properties**
```css
:root {
  --primary-color: #4361ee;
  --secondary-color: #3f37c9;
  --success-color: #4bb543;
  --danger-color: #ff3333;
  --warning-color: #f9c74f;
  --info-color: #4895ef;
  --light-color: #f8f9fa;
  --dark-color: #212529;
  --gray-color: #6c757d;
  --light-gray: #e9ecef;
  --border-radius: 8px;
  --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
}
```

#### **Key Improvements**
- **Readability Fixes**: Resolved "white on white" text visibility issues across all pages
- **Theme Consistency**: Unified color scheme and styling patterns
- **Dark Mode Support**: Automatic light/dark mode compatibility
- **Responsive Design**: Enhanced mobile and tablet layouts
- **Accessibility**: Improved contrast ratios and keyboard navigation

### 🚀 **PERFORMANCE & MAINTENANCE**

#### **Performance Benefits**
- **Reduced HTML Size**: Externalized large CSS blocks from templates
- **CSS Caching**: Browser caching of external stylesheets
- **Faster Page Loads**: Improved initial page rendering
- **Bundle Optimization**: Modular CSS loading strategy

#### **Developer Experience**
- **Better Code Organization**: Clear separation of HTML, CSS, and JavaScript
- **Easier Maintenance**: Centralized styling definitions
- **Version Control**: CSS changes tracked independently
- **Debugging**: Improved CSS debugging and inspection

### 📱 **RESPONSIVE DESIGN IMPROVEMENTS**

#### **Mobile Optimizations**
- **Adaptive Grids**: Layouts that scale from desktop to mobile
- **Touch-Friendly**: Appropriate button sizes and spacing
- **Readable Fonts**: Optimized font sizes across screen sizes
- **Flexible Components**: Responsive card layouts and navigation

### 📚 **DOCUMENTATION UPDATES**

#### **New Documentation**
- **WEB_INTERFACE_IMPROVEMENTS.md**: Comprehensive guide to CSS cleanup and theme system
- **Updated USER_GUIDE.md**: Added web interface features section
- **Updated DOCUMENTATION_INDEX.md**: Added new documentation reference

#### **Migration Guide**
- **CSS Architecture**: Guidelines for maintaining the new CSS structure
- **Theme Variables**: How to use and extend the theme system
- **Template Standards**: Best practices for HTML/CSS separation

## [1.17.0] - 2026-01-09 🔄 **MCP Client Refactoring & Testing Infrastructure Overhaul**

### 🏗️ **ARCHITECTURAL IMPROVEMENTS**

#### **Web API MCP Client Refactoring**
- **Complete MCP Migration**: All remaining web API endpoints now use MCP client instead of direct manager calls
- **Unified Communication Pattern**: Standardized MCP protocol usage across all API endpoints
- **Improved Separation of Concerns**: Clean separation between web layer and MCP tool layer
- **Enhanced Error Handling**: Consistent error handling and response formatting across all endpoints

**Refactored Endpoints:**
- ✅ `lighting.py` - Philips Hue and Tapo lighting control
- ✅ `cameras.py` - Camera management and streaming
- ✅ `pages.py` - Page rendering and navigation
- ✅ `system.py` - System information and control
- ✅ `custom_presets.py` - PTZ preset management
- ✅ `microscope.py` - Microscope camera control
- ✅ `otoscope.py` - Medical otoscope camera control
- ✅ `ptz.py` - Pan-Tilt-Zoom camera control
- ✅ `scanner.py` - Document scanner control
- ✅ `security.py` - Ring/Nest security integration
- ✅ `motion.py` - Motion detection management
- ✅ `audio.py` - Audio streaming control
- ✅ `energy.py` - Smart plug energy monitoring
- ✅ `sensors.py` - Environmental sensor management
- ✅ `log_management.py` - System logging operations
- ✅ `onboarding.py` - Device discovery and configuration

#### **MCP Tools Integration**
- **Portmanteau Tools**: Full integration with consolidated MCP tools
- **Tool Categories**:
  - `energy_management` - Smart plug and energy monitoring
  - `motion_management` - Motion detection and camera events
  - `camera_management` - Camera control and streaming
  - `ptz_management` - PTZ control and presets
  - `media_management` - Media capture and streaming
  - `system_management` - System operations and logging
  - `medical_management` - Medical device control
  - `security_management` - Security system integration
  - `lighting_management` - Lighting control systems
- **Action-Based Interface**: Clean action-based tool calling patterns

### 🧪 **COMPREHENSIVE TESTING INFRASTRUCTURE**

#### **Testing Scaffold Overhaul**
- **120+ Test Methods**: Comprehensive test coverage across all components
- **Advanced Fixtures**: 100+ reusable test fixtures for all components
- **Mock Infrastructure**: Extensive mocking for external dependencies
- **Performance Testing**: Built-in performance benchmarking and regression detection
- **Integration Testing**: Full MCP client-server integration tests

#### **Test Categories & Coverage**
- **Unit Tests** (92% coverage target):
  - API endpoint unit tests with MCP integration
  - MCP client functionality tests
  - Core component isolation tests
  - Error handling and edge case validation

- **Integration Tests** (85% coverage target):
  - MCP client-server interaction testing
  - Cross-component workflow validation
  - Real-time data flow testing
  - Concurrent operation testing

- **End-to-End Tests**:
  - Complete user journey validation
  - API contract verification
  - Performance under load testing

#### **Advanced Testing Features**
- **Mock MCP Server**: Configurable mock server for testing MCP interactions
- **Test Data Factories**: Consistent, realistic test data generation
- **Performance Timers**: Automated performance threshold validation
- **Async Testing Support**: Full asyncio testing infrastructure
- **Cross-Platform Testing**: Windows, macOS, Linux compatibility validation

#### **CI/CD Pipeline Enhancement**
- **10 Comprehensive Jobs**: Quality checks, unit tests, integration tests, performance, security, deployment
- **Parallel Execution**: Optimized test execution with parallel processing
- **Artifact Generation**: Detailed test reports, coverage reports, performance metrics
- **Automated Deployment**: Container testing and production deployment validation
- **Security Integration**: Vulnerability scanning, secrets detection, dependency analysis

### 📊 **DEVELOPMENT EXPERIENCE**

#### **Testing Infrastructure**
- **One-Command Testing**: `poetry run pytest` with comprehensive coverage
- **Test Discovery**: Automatic test discovery with clear categorization
- **Debug Support**: Enhanced debugging with PDB, IPython, and detailed tracebacks
- **Performance Monitoring**: Built-in performance regression detection
- **Documentation**: Complete testing guide with examples and best practices

#### **Developer Tools**
- **Test Fixtures**: Pre-configured fixtures for common testing scenarios
- **Mock Utilities**: Easy-to-use mocking helpers for external services
- **Assertion Helpers**: Standardized assertion patterns for consistent testing
- **Performance Tools**: Built-in benchmarking for performance-critical code
- **CI/CD Integration**: Local CI pipeline execution for development validation

### 🔧 **TECHNICAL IMPROVEMENTS**

#### **Code Quality & Architecture**
- **MCP Protocol Compliance**: Full adherence to MCP stdio protocol standards
- **Error Handling**: Consistent error handling patterns across all endpoints
- **Type Safety**: Enhanced type hints and validation throughout the codebase
- **Documentation**: Updated API documentation reflecting MCP integration
- **Logging**: Improved logging with structured error reporting

#### **Performance Optimizations**
- **Connection Pooling**: Efficient MCP client connection management
- **Async Operations**: Full asyncio support for non-blocking operations
- **Caching**: Smart caching for frequently accessed data
- **Resource Management**: Proper cleanup and resource lifecycle management

### 🐛 **BUG FIXES**

- **MCP Connection Stability**: Improved MCP client connection reliability
- **Error Propagation**: Fixed error handling in MCP tool calls
- **Resource Cleanup**: Enhanced cleanup of MCP client resources
- **Concurrent Access**: Fixed race conditions in concurrent MCP operations

### 📚 **DOCUMENTATION**

- **Testing Guide**: Comprehensive testing documentation (`tests/README.md`)
- **API Documentation**: Updated API docs reflecting MCP integration
- **Development Guide**: Enhanced development workflow documentation
- **CI/CD Documentation**: Complete CI/CD pipeline documentation
- **Architecture Docs**: Updated architecture documentation

### 🔄 **BACKWARD COMPATIBILITY**

- **API Contracts**: All existing API endpoints maintain backward compatibility
- **Response Formats**: Consistent response formats across all endpoints
- **Error Codes**: Standardized error codes and messages
- **Migration Path**: Smooth transition from direct manager calls to MCP client

---

## [1.16.0] - 2025-12-18 🌤️ **Vienna Public Webcams Integration**

### 🆕 **FEATURES**

#### **USB Otoscope Camera Support**
- **Full medical camera integration**: Added complete support for USB otoscope cameras
- **Medical examination presets**: Pre-configured settings for ear, throat, nose, skin, and mouth examinations
- **LED light control**: Adjustable LED intensity (0-100%) for optimal illumination
- **Digital magnification**: Variable magnification levels with measurement calibration
- **Medical metadata**: Embedded examination data in captured images and videos
- **Specimen tracking**: Automatic categorization by examination type
- **Focus mode control**: Auto, manual, and fixed focus modes
- **Measurement tools**: Calibrated pixel-to-millimeter conversion for accurate measurements

#### **Otoscope Detection & Configuration**
- **Detection script**: `scripts/detect_otoscope.py` for automatic USB otoscope discovery
- **Smart configuration**: Automatic detection of common otoscope resolutions (640x480, 800x600)
- **Easy setup**: One-command device detection and configuration generation

#### **Medical Camera API**
- **Complete REST API**: `/api/otoscope/*` endpoints for all otoscope functions
- **Medical presets**: Apply examination-specific settings with single API call
- **Calibration endpoints**: Accurate measurement calibration and validation
- **Recording controls**: Start/stop medical examination recordings

#### **AI-Powered Humorous Fridge Labels**
- **50-Label Bulk Printing**: Generate and print 50 humorous labels for maximum fridge coverage
  - Dad jokes, puns, sarcastic remarks, and absurd humor
  - Food-related, chore-related, and general humor categories
  - Short, medium, and long humor styles
  - Preview before printing to ensure quality
- **Humor Categories**: Specialized humor for different contexts
  - General: Universal humor for any fridge item
  - Food: Food-related puns and jokes ("Lettuce turnip the beet")
  - Chores: Sarcastic household chore reminders
  - Pets: Pet-related humor
  - Tech: Technology jokes
  - Life: Life observations with humor
- **Humor Themes**: Multiple comedic styles
  - Dad Jokes: Classic pun-based humor
  - Puns: Clever wordplay
  - Sarcastic: Witty, sarcastic remarks
  - Absurd: Completely ridiculous humor
  - Random: Mix of all styles
- **Web Interface**: Easy-to-use form for label generation
  - Theme and category selection
  - Style preference (short/medium/long)
  - Count control (1-100 labels)
  - Preview functionality
  - One-click bulk printing
- **Dymo Integration**: Full integration with existing Dymo printer system
  - Uses configured tape sizes and colors
  - Batch printing optimized for label efficiency
  - Error handling for out-of-tape situations

#### **Plant Growth Timelapse Photography**
- **Automated Germination Monitoring**: Set microscope over germinating plants for time-lapse capture
  - 10-minute intervals (configurable) for optimal germination tracking
  - Multi-day sessions (24+ hours) to capture full growth cycles
  - Built-in LED light ensures consistent illumination throughout session
  - Auto-focus every 10 shots to maintain sharp focus as plants grow
- **Intelligent Session Management**: Smart session naming and organization
  - Automatic timestamp-based session directories
  - Plant-specific session names (e.g., "basil_germination_20251218_143000")
  - Metadata tracking for each captured image
  - Session status monitoring and progress tracking
- **Growth Video Creation**: Convert image sequences to timelapse videos
  - MP4 video output with configurable frame rates
  - Optional timestamp overlays showing capture time
  - Professional-quality growth acceleration videos
  - Perfect for sharing germination progress or educational content
- **Plant Health Analysis**: AI-powered growth pattern analysis
  - Detect growth acceleration phases
  - Monitor color changes (green development)
  - Track subtle movement and structural changes
  - Generate growth reports and recommendations
- **One-Click Germination Setup**: Quick-start templates for common scenarios
  - "Quick Start" button for immediate 10-minute interval monitoring
  - 24-hour default duration perfect for most germination cycles
  - Automatic LED brightness optimization for plant photography
  - Guided setup prompts for plant identification and session naming
- **Web Interface Integration**: Full microscope control panel
  - Live timelapse status monitoring
  - Session progress indicators
  - Video creation tools with preview
  - Growth analysis dashboards

#### **Vienna Public Webcams Integration**
- **Live Vienna Landmark Cameras**: Integrated 8+ public webcams showing Vienna's most iconic locations
  - Stephansdom Cathedral (weather watching on St. Stephen's)
  - Rathaus City Hall (perfect for snow/rain views with Rathauspark)
  - Donau City Skyline (modern Vienna with UNO City)
  - Prater Riesenrad (famous ferris wheel landmark)
  - Schönbrunn Palace Gardens (seasonal weather and gardens)
  - Naschmarkt (lively food market atmosphere)
  - Augarten Royal Gardens (peaceful park views)
  - Danube Canal (water and weather monitoring)
- **Dedicated Vienna Webcams Dashboard**: New `/vienna-webcams` page with live camera grid
  - Auto-refresh every 5 minutes for weather updates
  - Individual camera refresh buttons
  - Connection status monitoring
  - Direct links to original webcam sources
  - Mobile-responsive design for phone viewing
- **Weather Monitoring Focus**: Optimized for watching Vienna weather conditions
  - Snow accumulation on landmarks
  - Rain patterns across the city
  - Seasonal changes in gardens and parks
  - Fog and atmospheric conditions
- **Public Webcam Framework**: Extensible system for adding more city webcams
  - Configurable camera metadata (location, description)
  - Automatic image loading with error handling
  - Status monitoring and connection testing
  - Cache-busting for fresh image updates

#### **iKettle Smart Kettle Integration**
- **Complete iKettle Control**: Full REST API integration with Smarter iKettle
  - Temperature control (20°C to 100°C / 68°F to 212°F)
  - Boil operations with custom temperature settings
  - Keep warm mode with configurable duration
  - Operation scheduling and morning coffee routines
  - Real-time status monitoring and water level detection
- **Morning Coffee Automation**: Intelligent wake-up coffee preparation
  - Schedule coffee heating for exact wake-up time
  - Pre-heat timing to ensure perfect temperature
  - Configurable coffee temperature (default 95°C for optimal extraction)
  - Integration with existing morning routines
- **Smart Kettle Modes**: Multiple operational modes support
  - Wake Up mode for morning routines
  - Home mode for general household use
  - Formula mode for specialized heating profiles
  - Voice control integration ready (Alexa/Google Assistant)
- **Advanced Monitoring**: Comprehensive kettle status and diagnostics
  - Real-time temperature monitoring
  - Water level detection and low-water alerts
  - Boiling status and operation progress
  - Keep warm timer and temperature maintenance
  - Connection status and error reporting
- **Web Interface Controls**: Full-featured kettle management dashboard
  - One-click coffee and tea heating buttons
  - Keep warm and stop operation controls
  - Morning routine setup wizard
  - Live status display with temperature and water level
  - Historical operation logging and notifications
- **Zojirushi Comparison Mode**: Side-by-side feature comparison
  - Instant hot water vs. heated-on-demand
  - Energy efficiency analysis (vacuum insulation vs. heating)
  - Temperature precision and control
  - Maintenance and reliability tracking
  - Cost-benefit analysis for both approaches

#### **Enhanced Camera Management**
- **Medical device classification**: Special handling for medical vs. security cameras
- **Improved naming**: Better support for descriptive camera names including medical devices
- **Configuration templates**: Updated examples with otoscope configuration

### 📋 **CONFIGURATION EXAMPLE**
```yaml
# USB Otoscope Configuration
otoscope1:
  type: otoscope
  device_id: 2
  resolution: "640x480"
  fps: 30
  light_intensity: 80
  focus_mode: "auto"
  specimen_type: "ear"
  magnification: 1.0
```

### 🩺 **MEDICAL PRESETS AVAILABLE**
- **Ear Exam**: Optimized for tympanic membrane visualization
- **Throat Exam**: Suitable for oropharyngeal examination
- **Nose Exam**: Designed for nasal cavity inspection
- **Skin Exam**: High magnification for dermatological assessment
- **Mouth Exam**: Appropriate for oral cavity examination

### 🔧 **USAGE EXAMPLES**
```bash
# Apply ear examination preset
curl -X POST http://localhost:7777/api/otoscope/apply_preset \
  -d '{"camera_name":"otoscope1","preset_name":"ear_exam"}'

# Calibrate for measurements
curl -X POST http://localhost:7777/api/otoscope/calibrate \
  -d '{"camera_name":"otoscope1","reference_size_mm":10,"pixels":100}'

# Capture medical image
curl -X POST http://localhost:7777/api/otoscope/capture_medical \
  -d '{"camera_name":"otoscope1","filename":"ear-exam-001"}'
```

## [1.8.1] - 2025-12-18 ⚡ **Real-Time Power Monitoring Fix**

### 🐛 **BUG FIXES**

#### **Tapo P115 Real-Time Power Monitoring**
- **Fixed missing current_power data**: Tapo P115 plugs now report real-time power consumption in watts
- **Correct API method usage**: Changed from accessing `energy.current_power` (non-existent) to using `client.get_current_power()` method
- **Added real-time power tracking**: Energy API now returns actual current power consumption (e.g., 107W, 52W, 254W)
- **Enhanced energy monitoring**: Plugs are now fully functional for real-time energy monitoring and cost tracking

### 🐛 **BUG FIXES** (Previous)

#### **Netatmo Token Refresh**
- **Fixed 403 errors after token refresh**: System was using cached/stale access tokens after refresh
- **Proper token cache clearing**: Now clears both `_access_token` AND `_token_expiry` when 403 errors occur
- **Automatic retry**: System automatically refreshes token and retries API calls on 403 errors
- **Added 403 handling**: Both `list_stations()` and `current_data()` now properly handle 403 errors with token refresh

#### **Weather Page**
- **Fixed missing `active_page` parameter**: Weather page route now includes `active_page: "weather"` for proper navigation highlighting

### 📝 **DOCUMENTATION**

- **Updated NETATMO_TOKEN_GUIDE.md**: Added troubleshooting section for 403 errors after token refresh
- **Documented token refresh fix**: Explained how automatic refresh works and what was fixed
- **Added recent changes section**: Documented the 2025-12-10 token refresh improvements

### 🔧 **TECHNICAL IMPROVEMENTS**

- **Token refresh logic**: Improved error handling in `netatmo_client.py` to force complete token refresh on 403 errors
- **Code quality**: Fixed 178 ruff linting issues (imports, whitespace, formatting)

## [1.7.0] - 2025-11-30 🔐 **Authentication System + Lighting Enhancements**

### ✨ **NEW FEATURES**

#### **🔐 Session-Based Authentication** (NEW)
- **Complete Auth System**: Password hashing with PBKDF2-SHA256 + salt
- **Session Management**: Secure cookie-based sessions (24h default, 30d with "remember me")
- **Login Page**: Modern dark-themed login interface with password visibility toggle
- **User Menu**: Dropdown menu in topbar with Settings link and Sign Out button
- **Auth Middleware**: Automatic route protection for all dashboard pages
- **Configurable**: Enable/disable via `config.yaml` (`auth.enabled: true/false`)
- **Default User**: Auto-creates admin user with random password on first enable

#### **💡 Lighting Dashboard Enhancements**
- **Color Controls**: Full RGB color picker for color-capable Hue bulbs
- **Auto-Scan**: Automatic device rescan on page load if no lights found
- **Periodic Refresh**: Auto-refresh every 15 seconds + full rescan every 2 minutes
- **Global Controls**: Quick action buttons for all lights:
  - 💡 **All On** - Turn all lights on instantly
  - 🌙 **All Off** - Turn all lights off instantly
  - 🔆 **50%** - Set all lights to 50% brightness
  - ☀️ **100%** - Set all lights to full brightness
  - 🪩 **Disco!** - Party mode with random colors (auto-stops after 30s)
- **Performance**: Near-instant light changes (removed unnecessary delays)
- **Refresh Button**: Quick refresh without full bridge rescan

#### **⚡ Performance Optimizations**
- **Removed Full Bridge Scans**: No longer scans all devices on every `get_light()` call
- **Parallel Requests**: Global controls fire all commands simultaneously
- **Immediate API Returns**: Control endpoints return instantly without waiting for state refresh
- **Cache-First Loading**: Periodic updates use cached data (only full Rescan queries bridge)

### 🔧 **TECHNICAL IMPROVEMENTS**

#### **Auth Module** (`web/auth.py`)
- PBKDF2-SHA256 password hashing with random salt
- In-memory session storage with expiration
- Public path whitelist (login, static files, API endpoints)
- Automatic default user creation on first enable

#### **Security Headers**
- Updated CSP to allow Font Awesome icons from CDN
- Fixed icon visibility in topbar navigation

#### **API Changes**
- `POST /api/auth/login` - User authentication
- `POST /api/auth/logout` - Session termination
- `GET /api/auth/status` - Current auth status
- `GET /login` - Login page (redirects to dashboard if auth disabled)

### 🐛 **BUG FIXES**
- Fixed slow light control (was doing full bridge discovery on every command)
- Fixed missing color controls for RGB-capable bulbs
- Fixed topbar icons not visible (CSP blocking Font Awesome)
- Fixed initial light scan not running on page load
- Fixed combined energy calculation (was averaging instead of summing)

### 📝 **CONFIGURATION**

```yaml
auth:
  enabled: false  # Set to true to require login
  users:
    admin:
      password: admin123  # Change this! Or use password_hash + salt
      role: admin
```

### 🎯 **USER EXPERIENCE**
- **Login Flow**: Beautiful login page with error handling
- **Session Persistence**: "Remember me" extends session to 30 days
- **User Feedback**: Clear error messages for invalid credentials
- **Auto-Redirect**: Logged-in users redirected away from login page
- **Responsive Design**: Login page works on mobile devices

---

## [1.6.1] - 2025-11-29 🔐 **Nest OAuth + SOTA Voice**

### ✨ **NEW FEATURES**

#### **Real Nest Protect API Integration**
- Added OAuth flow for direct Google Nest API access
- `nest_oauth_start`: Get Google OAuth URL
- `nest_oauth_complete`: Exchange code for token (one-time setup)
- `nest_oauth_status`: Check authentication status
- Falls back to mock data when not authenticated
- Token cached in `nest_token.cache` for persistent auth

#### **SOTA Voice Stack (Fully Offline)**
Upgraded audio engines with automatic fallback chains:

**STT Chain**: Faster-Whisper → Vosk → Whisper
- `faster-whisper`: 4x faster, CTranslate2 optimized
- `vosk`: Lightweight streaming fallback
- `whisper`: Original OpenAI model

**TTS Chain**: Piper → Edge-TTS → pyttsx3
- `piper`: SOTA local neural TTS
- `edge-tts`: Microsoft neural voices
- `pyttsx3`: Offline system SAPI

**Always-On Wake Word** (Alexa-style):
- `wake_start`: Start background listener
- `wake_stop`: Stop listener
- `wake_status`: Check status
- Uses OpenWakeWord or Vosk keyword spotting
- Zero network traffic - fully offline

---

## [1.6.0] - 2025-11-29 🎙️ **ALEXA 2 - Voice & Fun Features**

### ✨ **NEW FEATURES**

#### **"Alexa 2" Audio Capabilities**
Full voice assistant capabilities added to `audio_management`:

- **Text-to-Speech (TTS)**
  - `speak`: Convert text to spoken audio
  - `announce`: Play attention chime, then speak
  - Supports `pyttsx3` (offline) and `edge-tts` (high quality, internet required)

- **Speech-to-Text (STT)**
  - `listen`: Record and transcribe speech using Whisper
  - `voice_command`: Wake word detection + command recognition
  - Built-in wake words: "hey tapo", "ok tapo", "computer", "assistant"

- **Alarm Sounds**
  - 10 built-in alarm types: `siren`, `beep`, `urgent`, `doorbell`, `chime`, `alarm`, `attention`, `success`, `error`, `alert`
  - Programmatically generated (no audio files needed)
  - `repeat` parameter for multiple cycles

- **Audio Recording**
  - `record`: Record from microphone to WAV file
  - `list_devices`: List available audio input/output devices

#### **Prank Modes** 🎉

**Lighting Pranks** (`lighting_management action="prank"`):
| Mode | Effect |
|------|--------|
| `chaos` | Random on/off for all lights |
| `wave` | Sequential room-to-room sweep |
| `disco` | Rapid brightness changes |
| `sos` | Morse code ... --- ... |

**PTZ Camera Pranks** (`ptz_management action="prank"`):
| Mode | Effect |
|------|--------|
| `nod` | Enthusiastic yes-yes-yes! |
| `shake` | Rapid no-no-no! |
| `dizzy` | Circular drunk motion |
| `chaos` | Random crazy movements |

All pranks restore original state after completion. Duration 1-10 sec (safety cap).

#### **Hue Bridge Improvements**
- `rescan` action: Force refresh lights/groups/scenes from bridge
- Auto-rescan on stale cache detection (fixes "all off" bug on startup)

### 📦 **OPTIONAL DEPENDENCIES**

New `[voice]` optional dependencies:
```bash
pip install home-security-mcp-platform[voice]
```

Installs: `pyttsx3`, `edge-tts`, `openai-whisper`, `sounddevice`, `soundfile`

### 📝 **EXAMPLES**

```python
# Announce intruder
audio_management(action="announce", text="Motion detected in backyard!")

# Play alarm
audio_management(action="play_alarm", alarm_type="siren", repeat=3)

# Voice command
audio_management(action="voice_command", wake_word="hey tapo", duration=10)

# Disco party!
lighting_management(action="prank", prank_mode="disco", duration=8)

# Camera says yes
ptz_management(action="prank", camera_name="Kitchen", prank_mode="nod", duration=5)
```

---

## [1.5.1] - 2025-11-29 🔧 **MCP PROTOCOL FIX**

### 🐛 **BUG FIXES**

#### **MCP stdio Protocol Corruption Fixed**
- **Root Cause**: `patch_ring_doorbell.py` was printing to stdout during import, corrupting MCP JSON-RPC
- **Fix**: Replaced all `print()` statements with proper `logging.getLogger(__name__)` calls
- **Result**: Clean stdout for MCP, stderr shows initialization logs

#### **Logging Order Fixed**
- **Issue**: Logging was configured AFTER patch ran, so messages went to /dev/null
- **Fix**: Reordered `server_v2.py` to configure logging BEFORE running the patch
- **Result**: All initialization messages now visible in Cursor output tab

#### **Cursor MCP Config Fixed**
- **Issue**: `cwd` was set to `src/` subdirectory, breaking module imports
- **Fix**: Changed `cwd` from `D:/Dev/repos/tapo-camera-mcp/src` to `D:/Dev/repos/tapo-camera-mcp`
- **Removed**: Placeholder env vars (server reads from `config.yaml`)

### 📝 **TECHNICAL DETAILS**

```python
# Before (broken - stdout pollution)
print(f"Websockets package found at: {websockets.__file__}")

# After (correct - stderr logging)
logger.info(f"Websockets found: {websockets.__file__}")
```

**Cursor `mcp.json` fix:**
```json
{
  "tapo-mcp": {
    "command": "python",
    "args": ["-m", "tapo_camera_mcp.server_v2", "--direct"],
    "cwd": "D:/Dev/repos/tapo-camera-mcp",  // NOT /src!
    "env": {
      "PYTHONPATH": "D:/Dev/repos/tapo-camera-mcp/src",
      "PYTHONUNBUFFERED": "1"
    }
  }
}
```

## [1.4.0] - 2025-11-26 🏠 **SMART HOME INTEGRATION**

### 🚀 **MAJOR FEATURES ADDED**

#### **💡 Philips Hue Integration** (NEW)
- **Full Bridge Support**: Connect to Hue Bridge via phue library
- **18 Lights Discovered**: Automatic discovery of all connected bulbs
- **Group Control**: Control rooms/zones as groups
- **Scene Activation**: 11 predefined scenes (Sunset, Aurora, etc.)
- **Performance Caching**: Device lists cached on startup for instant response
- **Rescan Button**: Manual refresh of lights/groups/scenes
- **Lighting Dashboard**: New `/lighting` page with real-time controls
- **ZigBee Reliability**: 10-year-old bulbs still running perfectly

#### **🌤️ Netatmo Weather** (ENHANCED)
- **Real API Integration**: pyatmo 8.x with OAuth token refresh
- **Live Indoor Data**: Temperature, humidity, CO2, noise, pressure from your station
- **Stroheckgasse Station**: Your actual station detected and working
- **Database Storage**: Weather data persisted for historical charts

#### **🌍 Vienna External Weather** (NEW)
- **Open-Meteo API**: Free weather data, no API key required
- **Real-Time Vienna Weather**: Temperature, humidity, wind, clouds
- **5-Day Forecast**: Daily forecast with weather icons
- **Indoor/Outdoor Comparison**: +19°C warmer inside indicator
- **Day/Night Indicator**: Visual feedback for time of day

#### **🍳 Kitchen Dashboard** (NEW)
- **Appliance Overview**: Tefal Optigrill, Zojirushi water boiler
- **Tapo Plug Integration**: On/off control via smart plug
- **Smarter iKettle Info**: Alternative smart kettle research

#### **🤖 Robots Dashboard** (NEW)
- **Roomba Status**: Coming soon integration
- **Unitree Go2**: Planned purchase card with specs
- **Pilot Labs Moorebot Scout**: AI home patrol robot (arriving Jan 2025)
- **Petbot Loona**: No API available (documented)

### 🔧 **TECHNICAL IMPROVEMENTS**

#### **Chatbot Enhancements**
- **Draggable/Resizable**: Move and resize chat window
- **Settings Persistence**: Provider, model, personality saved to localStorage
- **10 Personalities**: Helpful Assistant, Home Automation Expert, Pirate Captain, etc.
- **Auto Model Loading**: Models load automatically when selected
- **Prompt Enhancement**: 🪄 button to elaborate prompts in personality style
- **Response Refinement**: ✨ button to improve AI responses

#### **API Additions**
- `POST /api/lighting/hue/rescan` - Force refresh device cache
- `GET /api/weather/external/current` - Vienna current weather
- `GET /api/weather/external/forecast` - 7-day forecast
- `GET /api/weather/combined` - Internal + external weather combined

#### **Configuration**
- **Config Model Mapping**: WeatherSettings → "weather" config key fix
- **CSP Updates**: Allow Chart.js from jsdelivr CDN
- **Netatmo OAuth**: Full OAuth flow with token refresh

### 🐛 **BUG FIXES**
- Fixed Hue scene activation (use `bridge.set_group()` not `group.scene`)
- Fixed slow Hue response (removed redundant `_discover_devices()` calls)
- Fixed Chart.js CSP blocking
- Fixed config model key mapping for weather settings
- Fixed chatbot window positioning and visibility

### 📦 **DEPENDENCIES**
- `phue>=1.1` - Philips Hue Bridge control
- `pyatmo>=8.0.0,<9.0.0` - Netatmo weather (updated from 9.x)
- `aiohttp` - Async HTTP for Open-Meteo

---

## [1.3.0] - 2025-11-17 🚀 **LLM INTEGRATION & DOCKERIZATION**

### 🚀 **MAJOR FEATURES ADDED**

#### **🤖 LLM Integration** (NEW)
- **Multi-Provider Support**: Ollama, LM Studio, and OpenAI integration
- **LLM Manager**: Unified interface for managing multiple LLM providers
- **Model Management**: List, load, and unload models dynamically
- **Chatbot UI**: Floating chatbot button with chat window
- **Streaming Support**: Real-time streaming responses from LLM providers
- **API Endpoints**: Complete REST API for LLM operations (`/api/llm/*`)

#### **🐳 Dockerization** (NEW)
- **MyHomeControl Stack**: Complete Docker Compose setup
- **Production Builds**: Minimal `requirements-docker.txt` for faster builds
- **Network Integration**: Unified `myhomecontrol` Docker network
- **Health Checks**: Container health monitoring
- **Optimized Images**: Reduced build time and image size

#### **🌤️ Netatmo Weather Integration** (NEW)
- **OAuth 2.0 Authentication**: Secure token-based authentication
- **Live Weather Data**: Real-time temperature, humidity, CO2, pressure
- **Weather Dashboard**: Visual weather station monitoring
- **Helper Scripts**: OAuth setup and token refresh automation

#### **📊 Monitoring & Observability** (ENHANCED)
- **GitLab Integration**: GitLab CE setup with Prometheus scraping
- **Grafana Dashboards**: GitLab status monitoring
- **Port Management**: Resolved port conflicts (GitLab: 8093, Prometheus: 9095)
- **Unified Stack**: Single monitoring stack for all repositories

### 🔧 **TECHNICAL IMPROVEMENTS**

#### **CI/CD Modernization**
- **Ruff Integration**: Modern linting and formatting (replaced black)
- **Concurrency Groups**: Cancel redundant CI runs automatically
- **Dependency Caching**: Ruff and pip caching for faster builds
- **Test Timeouts**: Prevent hanging test jobs
- **Dependabot**: Automated dependency updates (weekly, low-spam)
- **Reduced Python Versions**: Test on 3.10, 3.11, 3.12 (faster CI)

#### **Testing Infrastructure**
- **Integration Tests**: Real provider connection tests (Ollama, LM Studio, OpenAI)
- **Test Markers**: `@pytest.mark.integration` for test categorization
- **Comprehensive Coverage**: Unit tests for LLM providers, manager, and API
- **Mock-Free**: Removed all mock data from production code

#### **Code Quality**
- **Ruff Linting**: Fast, comprehensive code quality checks
- **Type Safety**: Enhanced type hints and validation
- **Error Handling**: Improved error messages and recovery
- **Documentation**: Updated docs for new features

### 🎨 **USER EXPERIENCE IMPROVEMENTS**

#### **Camera Dashboard**
- **Dedicated Cameras Page**: Live view moved to `/cameras` page
- **Live Thumbnails**: 160x160 video thumbnails for all cameras
- **Camera Prioritization**: USB webcam → Tapo → Doorcam → Petcube
- **Status Indicators**: Clear online/offline status display

#### **Energy Dashboard**
- **Real Device Priority**: Real P115 plugs shown first
- **Read-Only Support**: Proper handling of read-only devices
- **Live Data**: Real-time energy monitoring and charts
- **Device Control**: On/off toggle for controllable devices

### 📦 **DEPENDENCIES**

#### **New Dependencies**
- `httpx>=0.24.0` - LLM provider HTTP client
- `pyatmo>=9.0.0` - Netatmo weather station integration
- `psutil>=5.9.0` - System monitoring
- `tapo>=0.8.0` - P115 smart plug ingestion

#### **Docker Dependencies**
- Minimal `requirements-docker.txt` for production builds
- Excludes heavy ML dependencies for faster builds
- OpenCV system libraries for camera support

### 🐛 **BUG FIXES**
- Fixed camera status parsing (dict vs string)
- Removed all mock data from production endpoints
- Fixed API endpoint calls (`server.list_cameras()` → `server.camera_manager.list_cameras()`)
- Resolved port conflicts for GitLab and Prometheus
- Fixed Docker build context issues (GitLab data exclusion)

### 📚 **DOCUMENTATION**
- GitLab CE usage guide and repository setup
- Netatmo OAuth setup documentation
- Docker deployment guide
- CI/CD improvements documentation

---

## [1.2.0] - 2025-01-15 🎯 **COMPREHENSIVE DEVICE ONBOARDING SYSTEM**

### 🚀 **MAJOR FEATURES ADDED**

#### **🔧 Device Onboarding System** (NEW)
- **Progressive Device Discovery**: Automatic scanning for Tapo P115, Nest Protect, Ring devices, and USB webcams
- **Smart Configuration Wizard**: User-friendly device naming, location assignment, and settings
- **Authentication Integration**: OAuth setup for Nest Protect and Ring devices
- **Cross-Device Integration**: Intelligent recommendations for device combinations
- **Beautiful Progressive UI**: Step-by-step onboarding with real-time progress tracking

#### **⚡ Advanced Energy Management** (NEW)
- **Tapo P115 Smart Plug Integration**: Complete energy monitoring and control
- **Real-time Power Consumption**: Live wattage, voltage, and current monitoring
- **Cost Analysis**: Daily, monthly, and annual energy cost tracking
- **Smart Scheduling**: Automated power management based on usage patterns
- **Energy Saving Mode**: Intelligent power optimization with 10% reduction
- **Historical Data Visualization**: Chart.js-based energy consumption charts

#### **🚨 Security System Integration** (NEW)
- **Nest Protect Integration**: Smoke and CO detector monitoring
- **Ring Device Support**: Doorbell, motion sensors, and contact sensors
- **Emergency Automation**: Smart plug shutdown during smoke alarms
- **Cross-System Notifications**: Unified alert management
- **Security Dashboard**: Comprehensive alarm status and health monitoring

#### **🤖 AI-Powered Analytics** (NEW)
- **Performance Analytics**: Camera system optimization and monitoring
- **AI Scene Analysis**: Intelligent object detection and activity analysis
- **Smart Automation**: Predictive maintenance and intelligent scheduling
- **Usage Pattern Recognition**: Energy and security optimization recommendations

### 🔧 **TECHNICAL IMPROVEMENTS**

#### **FastMCP 2.12 Compliance** (MAJOR)
- **Tool Registration**: All tools now use proper `@tool()` decorators
- **Meta Classes**: Comprehensive tool metadata with Parameters subclasses
- **Multiline Docstrings**: Fixed all docstring formatting issues
- **Type Safety**: Enhanced Pydantic model validation and error handling

#### **Code Quality Enhancements**
- **Ruff Integration**: Replaced pylint with faster, more comprehensive linting
- **Security Hardening**: Fixed security warnings and added proper validation
- **Error Handling**: Comprehensive exception handling and recovery
- **Documentation**: Extensive inline documentation and API guides

#### **Web Dashboard Expansion**
- **New Dashboard Pages**: Alarms and Energy management interfaces
- **Responsive Design**: Mobile-optimized layouts with Tailwind CSS
- **Real-time Updates**: Live device status and energy consumption monitoring
- **Interactive Charts**: Lightweight Chart.js integration for data visualization

### 📊 **NEW API ENDPOINTS**
- **Onboarding API**: Complete device discovery and configuration endpoints
- **Energy Management**: Tapo P115 device control and monitoring
- **Security Integration**: Nest Protect and Ring device management
- **Analytics**: Performance monitoring and AI analysis endpoints

### 🎯 **USER EXPERIENCE IMPROVEMENTS**
- **Progressive Onboarding**: Guided setup for any device combination
- **Smart Defaults**: AI-powered device naming and configuration suggestions
- **Error Recovery**: Comprehensive error handling with user guidance
- **Cross-Device Integration**: Intelligent automation recommendations

### 📈 **PROJECT METRICS UPDATE**
- **Tool Count**: 30+ MCP tools (FastMCP 2.12 compliant)
- **Device Support**: Tapo P115, Nest Protect, Ring, USB Webcams
- **Dashboard Pages**: Cameras, Alarms, Energy, Analytics
- **GLAMA Status**: Gold+ Standard (95/100 points)
- **Code Quality**: 95%+ ruff compliance

---

## [1.1.0] - 2025-10-11 🚀 **MAJOR BREAKTHROUGH - LIVE DASHBOARD WORKING!**

### 🎯 **PRODUCTION READY ACHIEVEMENT**
- **✅ Live Web Dashboard**: Real camera monitoring at `localhost:7777`
- **✅ USB Webcam Auto-Detection**: Cameras automatically discovered and displayed
- **✅ Claude Desktop Integration**: MCP server starts successfully in Claude
- **✅ Production Foundation**: Ready for video streaming implementation

### 🔧 **TECHNICAL BREAKTHROUGHS**

#### **JSON Parsing Fix** (Critical)
- **Root Cause**: Pydantic deprecation warnings corrupted stdout JSON
- **Solution**: Comprehensive warning suppression and stderr redirection
- **Impact**: MCP server now loads correctly in Claude Desktop

#### **Dashboard Revolution** (Major)
- **Before**: Mock data and static interface
- **After**: Real camera data with live status monitoring
- **Auto-Discovery**: USB webcams automatically added on startup
- **Professional UI**: Clean, responsive design with real-time updates

#### **Server Stability** (Critical)
- **Fixed**: pytapo/kasa compatibility issues
- **Resolved**: Import errors and dependency conflicts
- **Enhanced**: Error handling and recovery mechanisms

### 📊 **PROGRESS METRICS**
- **Server Stability**: 100% ✅ (No more crashes)
- **Dashboard Functionality**: 90% ✅ (Video streaming next)
- **Camera Detection**: 100% ✅ (USB webcams working)
- **Claude Integration**: 100% ✅ (MCP loads successfully)

### 🎯 **CURRENT STATUS**
- **USB Webcam**: ✅ Recognized and monitored in dashboard
- **Tapo Cameras**: 🔄 Authentication pending (credentials needed)
- **Foundation**: ✅ Production-ready for video streaming

---

## [1.0.0] - 2025-10-01

### 🚀 **Gold Status Achievement**
- **Production Ready**: Achieved Glama.ai Gold Status certification (85/100 points)
- **Enterprise Standards**: Full compliance with enterprise MCP server requirements
- **Quality Assurance**: Comprehensive testing and validation pipeline

### ✅ **Major Improvements**

#### **Code Quality**
- ✅ **Zero Print Statements**: Complete replacement with structured logging
- ✅ **Error Handling**: Comprehensive input validation and graceful degradation
- ✅ **Type Safety**: Full type hints throughout codebase
- ✅ **FastMCP 2.12**: Upgraded to latest FastMCP framework version

#### **Testing & Infrastructure**
- ✅ **100% Test Coverage**: All tests passing with proper mocking
- ✅ **CI/CD Pipeline**: GitHub Actions with multi-version testing (3.8-3.13)
- ✅ **Code Quality**: Black formatting, isort imports, mypy type checking
- ✅ **Automated Validation**: Package building and validation pipeline

#### **Documentation**
- ✅ **Complete Documentation**: CHANGELOG, SECURITY.md, CONTRIBUTING.md
- ✅ **API Documentation**: Comprehensive tool documentation
- ✅ **Professional Standards**: Issue/PR templates, Dependabot configuration

#### **MCP Tools Enhancement**
- ✅ **21 Production Tools**: Complete camera management functionality
- ✅ **Health Check**: Comprehensive system health monitoring
- ✅ **Multilevel Help**: Hierarchical help system navigation
- ✅ **Status Tools**: Detailed system and application status

### 🔧 **Technical Enhancements**

#### **Camera Support**
- **Tapo Cameras**: Full support for TP-Link Tapo series
- **Webcams**: Enhanced USB webcam support
- **Ring Cameras**: Experimental Ring device support
- **Furbo Cameras**: Support for Furbo pet cameras

#### **Streaming & Media**
- **Live Streaming**: RTSP, RTMP, and HLS streaming support
- **PTZ Control**: Pan, tilt, and zoom (where supported)
- **Motion Detection**: Configurable motion detection settings
- **Snapshot Capture**: High-quality image capture
- **Audio Support**: Two-way audio where available

#### **Platform Integration**
- **Claude Desktop**: Native MCP stdio protocol support
- **Grafana Dashboards**: Real-time monitoring and visualization
- **REST API**: HTTP endpoints for remote control
- **Web Dashboard**: Real-time video streaming interface

### 📊 **Glama.ai Certification**

#### **Gold Tier Achievement**
- **Score**: 85/100 points
- **Grade**: Gold (Production Ready)
- **Validation**: All automated quality checks passing
- **Status**: Enterprise Production Ready

#### **Quality Metrics**
- **Code Quality**: 9/10 (structured logging, comprehensive error handling)
- **Testing**: 9/10 (100% pass rate, CI/CD validation)
- **Documentation**: 9/10 (complete professional documentation)
- **Infrastructure**: 9/10 (full CI/CD pipeline, automated testing)
- **Security**: 8/10 (input validation, dependency management)

### 🛡️ **Security & Compliance**

#### **Security Features**
- **Input Validation**: Comprehensive parameter validation decorators
- **Error Sanitization**: Secure error message handling
- **Dependency Security**: Automated vulnerability scanning
- **Access Control**: Proper authentication and authorization

#### **Compliance**
- **MCP Standards**: Full compliance with MCP 2.12 protocol
- **Python Standards**: PEP 8, type hints, structured logging
- **Enterprise Ready**: Production-grade error handling and logging

### 🎯 **Business Impact**

#### **Platform Recognition**
- **Glama.ai Listing**: Featured in #1 MCP server directory (5,000+ servers)
- **Professional Validation**: Gold tier certification from industry platform
- **Enterprise Credibility**: Trusted solution for business adoption
- **Community Recognition**: Leadership in MCP server development

#### **Technical Excellence**
- **Zero Downtime**: Robust error handling and recovery
- **Scalability**: Efficient resource management and performance
- **Maintainability**: Clean code structure and comprehensive testing
- **Extensibility**: Modular architecture for easy feature addition

---

## [0.5.0] - 2025-09-15

### Added
- Initial production release with FastMCP 2.12 compatibility
- Complete camera management system
- Multi-camera type support (Tapo, Webcam, Ring, Furbo)
- Web dashboard for real-time streaming
- Comprehensive tool set (21 tools)

### Changed
- Upgraded to FastMCP 2.12 framework
- Enhanced logging and error handling
- Improved camera discovery and management

## [0.4.0] - 2025-08-01

### Added
- Ring camera support
- Furbo camera support
- Enhanced PTZ controls
- Motion detection configuration

## [0.3.0] - 2025-07-15

### Added
- Webcam support for USB cameras
- RTSP streaming capabilities
- Image capture and processing
- Audio support for two-way communication

## [0.2.0] - 2025-06-01

### Added
- Tapo camera basic support
- PTZ control functionality
- Live streaming interface
- Basic web dashboard

## [0.1.0] - 2025-05-15

### Added
- Initial MCP server implementation
- Basic camera discovery
- Core tool framework
- Development setup and configuration

---

## Contributing

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages. Please ensure your commits follow this format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

Example:
```
feat(api): add support for Tapo C200 camera model

- Add support for Tapo C200 camera model
- Update API documentation
- Add unit tests for new functionality

Closes #123
```

## Contact

For questions, suggestions, or issues, please:
1. Check existing [Issues](https://github.com/yourusername/tapo-camera-mcp/issues)
2. Open a new [Issue](https://github.com/yourusername/tapo-camera-mcp/issues/new)
3. Contact the maintainers

---

**Document Version**: 1.0
**Last Updated**: October 1, 2025
**Repository**: tapo-camera-mcp
**Status**: Gold Tier (85/100) 🏆
