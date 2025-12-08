# Smart Kitchen & Robotics Integration Plan

**Timestamp**: 2025-12-02  
**Status**: PLANNING - Moorebot Scout Added (XMas 2025)  
**Tags**: smart-kitchen, robotics, roomba, unitree, butlerbot, zojirushi, samsung-fridge

## Overview

This document outlines the plan for integrating smart kitchen appliances and robotics platforms into the Home Security MCP system. This includes connected kitchen devices (water boilers, fridges, grills) and robotics platforms (Roomba, Unitree dogbot, butlerbot).

## Part 1: Smart Kitchen Appliances

### 1. Zojirushi Water Boiler

#### Current Situation
- User has Zojirushi water boiler
- Problem: Empty in morning when coffee needed
- Need: Smart connected version with scheduling/refill alerts

#### Research Findings

**Zojirushi Smart Water Boilers (2024-2025):**

**Research Result**: **Zojirushi does not currently offer Bluetooth/Wi-Fi connected water boilers** as of 2024-2025. However, there are alternatives and workarounds:

**Note**: CO2 detection is already covered by Netatmo, CO detection by Nest Protect. This plan focuses on gas leak detection (natural gas, propane) which is different from CO/CO2.

**Option 1: Smart Plug Integration**
- Use existing Zojirushi with **Tapo P115 smart plug** (already integrated!)
- Schedule: Turn on 30 minutes before wake time
- Monitor: Track power consumption to detect when empty
- Alert: Notify when power drops (indicates empty)

**Option 2: Alternative Smart Water Boilers**
- **Breville Smart Kettle**: Wi-Fi enabled, app control, scheduling
- **Smarter iKettle**: Wi-Fi, app control, temperature presets
- **Cosori Smart Kettle**: Wi-Fi, Alexa/Google integration

**Option 3: DIY Smart Integration**
- **ESP32 + Temperature Sensor**: Monitor water temperature
- **Smart Plug**: Control power and schedule
- **Water Level Sensor**: Detect when empty (advanced)

#### Recommended Solution: Tapo P115 Integration

**Implementation:**
```yaml
kitchen:
  zojirushi_water_boiler:
    enabled: true
    smart_plug_id: "tapo_p115_kitchen"  # Use existing Tapo plug
    schedule:
      morning_refill:
        enabled: true
        time: "06:00"  # 30 min before wake time
        duration_minutes: 15  # Time to heat water
      evening_refill:
        enabled: true
        time: "21:00"  # Evening refill
        duration_minutes: 15
    
    monitoring:
      power_threshold_watts: 50  # Below this = likely empty
      alert_on_empty: true
      check_interval_minutes: 15
```

**Features:**
- Schedule automatic refill before wake time
- Monitor power consumption to detect empty state
- Alert when boiler is empty
- Energy usage tracking

### 2. Samsung Smart Refrigerator

#### Available Models (2024-2025)

**Samsung Family Hub Refrigerators:**
- **Internal Cameras**: 3-4 cameras inside fridge
- **Food Recognition**: AI identifies items, tracks inventory
- **Bixby Integration**: Voice control and queries
- **SmartThings Integration**: Full home automation
- **Screen**: 21.5" or 32" touchscreen display
- **API Access**: SmartThings API (limited, requires developer account)

**Key Features:**
- **Food Inventory Tracking**: Camera-based item recognition
- **Expiration Alerts**: Track food expiration dates
- **Shopping Lists**: Auto-generate from inventory
- **Recipe Suggestions**: Based on available ingredients
- **Energy Monitoring**: Track power consumption
- **Temperature Monitoring**: Multiple zones

#### Integration Options

**Option 1: SmartThings API**
- **Access**: Requires Samsung SmartThings developer account
- **API**: RESTful API for device control
- **Limitations**: Limited food inventory API access
- **Status**: Food recognition data may not be fully accessible via API

**Option 2: Screen Scraping / Reverse Engineering**
- **Method**: Intercept SmartThings app traffic
- **Complexity**: High, may violate ToS
- **Reliability**: Low, breaks with app updates

**Option 3: MQTT Bridge (If Available)**
- **Method**: Use MQTT bridge if Samsung supports it
- **Status**: Check if available in 2025

**Option 4: Focus on Available Data**
- **Temperature Monitoring**: Via SmartThings API
- **Energy Usage**: Via SmartThings API
- **Door Open/Close**: Via SmartThings API
- **Food Inventory**: Limited or not available via API

#### Recommended Integration

```yaml
kitchen:
  samsung_fridge:
    enabled: false  # Enable when available
    integration_type: "smartthings"
    smartthings:
      api_key: ""  # SmartThings API key
      device_id: ""  # Fridge device ID
      poll_interval_seconds: 60
    
    features:
      temperature_monitoring: true
      energy_monitoring: true
      door_status: true
      food_inventory: false  # Not available via API
```

### 3. Tefal Smart Grill

#### Current Device
- User has Tefal intelligent connected grill
- **Integration**: Check Tefal app for API access
- **Protocol**: Likely Wi-Fi, may use Tuya or proprietary

#### Integration Research

**Tefal Smart Appliances:**
- **Tefal ActiFry**: Some models have app control
- **Tefal Cook4me**: Smart cooking with app
- **Integration**: May use Tuya platform (common for smart appliances)

**Integration Options:**
1. **Tuya Integration**: If Tefal uses Tuya platform
2. **Tefal App API**: Reverse engineer app (if available)
3. **MQTT**: If device supports MQTT

**Recommended Approach:**
- Investigate Tefal app for API endpoints
- Check if device appears in Tuya ecosystem
- Create integration service based on findings

### 4. Other Smart Kitchen Devices

#### Potential Integrations
- **Smart Ovens**: Samsung, LG, GE (Wi-Fi, app control)
- **Smart Dishwashers**: Samsung, LG (cycle monitoring, alerts)
- **Smart Coffee Makers**: Breville, Keurig (scheduling, remote start)
- **Smart Sous Vide**: Anova, Joule (temperature control, timers)

## Part 2: Robotics Integration

### 1. iRobot Roomba (Current)

#### Available Models
- **Roomba j7+**: Advanced obstacle avoidance, self-emptying
- **Roomba s9+**: Premium model, advanced mapping
- **Roomba i7+**: Mid-range, self-emptying
- **Roomba 980/960**: Older models with Wi-Fi

#### Integration Options

**Option 1: iRobot API (Official)**
- **Status**: iRobot provides REST API for developers
- **Access**: Requires developer account
- **Features**:
  - Start/stop/pause cleaning
  - Get robot status
  - Get cleaning history
  - Get map data
  - Schedule cleaning
- **Limitations**: Some features require iRobot account

**Option 2: Home Assistant Integration**
- **Status**: Official Home Assistant integration available
- **Features**: Full Roomba control via Home Assistant
- **Integration**: Can bridge to MCP via Home Assistant API

**Option 3: Valetudo (Open Source)**
- **Status**: Open-source firmware replacement
- **Features**: Full local control, no cloud required
- **Complexity**: Requires firmware flashing
- **Benefits**: Privacy, full control, MQTT support

#### Recommended Integration

```yaml
robotics:
  roomba:
    enabled: true
    integration_type: "irobot_api"  # or "home_assistant", "valetudo"
    irobot_api:
      username: ""  # iRobot account
      password: ""  # iRobot account
      endpoint: "https://api.irobot.com"
    
    features:
      start_cleaning: true
      stop_cleaning: true
      get_status: true
      get_map: true
      schedule_cleaning: true
      get_history: true
    
    automation:
      auto_clean_on_absence: false
      clean_after_events: false  # Clean after parties, etc.
      schedule:
        enabled: true
        times: ["09:00", "15:00"]  # Daily cleaning times
```

### 2. Moorebot Scout (Planned XMas 2025)

#### Specifications

**Moorebot Scout (Original - Mecanum Wheels):**
- **Type**: Mobile indoor security robot
- **Dimensions**: 11.5cm × 10cm × 8cm (4.53" × 3.94" × 3.15")
- **Weight**: 350g (0.77 lbs) - travel kit friendly!
- **Mobility**: 4× Mecanum wheels (omnidirectional)
- **Max Speed**: 2 km/h (1.2 mph)
- **Battery**: Over 2 hours (1 hour with night vision)
- **Charging**: 3 hours, auto-dock (sometimes wonky)
- **Connectivity**: Wi-Fi 2.4/5GHz (802.11 a/b/g/n)
- **Price**: ~€200-300

**Camera:**
- 2MP CMOS sensor, 1080p @ 30fps
- 120° wide-angle lens
- Infrared night vision (3-5m range)
- 2-way audio (1W speaker + mic)

**Processing:**
- Quad-Core ARM A7 @ 1.2 GHz
- 512MB LPDDR III RAM
- 16GB eMMC storage
- Linux + ROS 1.4

**Sensors:**
- 6DoF IMU (gyro + accelerometer)
- Time-of-Flight (ToF) sensor
- Light sensor

**Surface Compatibility:**
- ✅ Wood floors (excellent)
- ✅ Short carpet (good)
- ❌ Shag carpet (gets stuck)
- ❌ Stairs (cannot climb)

**Two Models Available:**
- **Scout (Original)**: Mecanum wheels, indoor only, ~€200 👈 RECOMMENDED for apartment
- **Scout E**: Tracks, indoor+outdoor, IPX4 water-resistant, ~€400

#### Integration Capabilities

**Potential Use Cases:**
1. **Benny Cam**: Follow/monitor German Shepherd when out
2. **Japan Trip Monitor**: Scheduled patrols during October trips
3. **Room Patrol**: Autonomous security rounds
4. **Mobile Camera**: Remote-controlled surveillance
5. **Package Detection**: Monitor deliveries at door
6. **Partner Check-In**: Two-way audio communication

**Integration Options:**

**Option 1: Official SDK (RECOMMENDED!)**
- **GitHub**: https://github.com/Pilot-Labs-Dev/Scout-open-source
- **Language**: Python, C++, ROS
- **Features**: 
  - Video/audio streaming
  - Sensor data access
  - Movement control
  - Custom automation
- **Complexity**: Moderate (ROS knowledge helpful)
- **Status**: Active, maintained by Pilot Labs

**Option 2: ROS Integration**
- **Framework**: ROS 1.4 (Melodic)
- **Benefits**: Standard robotics framework, extensive packages
- **Integration**: Bridge ROS to MCP via rosbridge_suite
- **Topics**: /camera/image_raw, /cmd_vel, /odom, /imu, /tof
- **Services**: /start_patrol, /return_home, /get_status

**Option 3: MQTT Bridge**
- **Method**: Create MQTT bridge from ROS topics
- **Benefits**: Easy integration with Home Assistant/Node-RED
- **Topics**: 
  - moorebot/scout/status
  - moorebot/scout/camera/stream
  - moorebot/scout/control/move
  - moorebot/scout/battery
  - moorebot/scout/location
- **Complexity**: Low-Medium

**Option 4: REST API Wrapper**
- **Method**: Build REST API over SDK
- **Endpoints**: 
  - GET /api/moorebot/status
  - POST /api/moorebot/move
  - GET /api/moorebot/camera/snapshot
  - POST /api/moorebot/patrol/start
- **Benefits**: HTTP integration, easy dashboard control

#### Recommended Integration

```yaml
robotics:
  moorebot_scout:
    enabled: false  # Enable when purchased (XMas 2025)
    integration_type: "sdk_ros"  # Official SDK + ROS bridge
    model: "scout_original"  # mecanum wheels version
    
    connection:
      wifi_ssid: "HomeNetwork5G"
      wifi_password: ""  # From secrets
      ip_address: ""  # Auto-discovered or static
      port: 8080  # SDK default
    
    sdk:
      github_repo: "https://github.com/Pilot-Labs-Dev/Scout-open-source"
      ros_version: "1.4"  # Melodic
      rosbridge_port: 9090
      video_stream_port: 8554  # RTSP
    
    features:
      camera:
        resolution: "1080p"
        fps: 30
        night_vision: true
        two_way_audio: true
        stream_url: "rtsp://{ip}:8554/stream"
      
      navigation:
        mecanum_wheels: true
        max_speed: 2.0  # km/h
        obstacle_avoidance: true  # ToF sensor
        auto_dock: true  # charging station
      
      monitoring:
        battery_alerts: true
        wifi_status: true
        position_tracking: true
        sensor_data: true
    
    automation:
      # Benny monitoring
      benny_follow:
        enabled: false
        trigger: "motion_detected"
        follow_distance: 1.0  # meters
      
      # Japan trip patrols
      security_patrol:
        enabled: false  # Enable before Oct trip
        schedule: 
          - "08:00"  # Morning check
          - "14:00"  # Afternoon check
          - "20:00"  # Evening check
          - "02:00"  # Night patrol
        route: "apartment_perimeter"
        duration_minutes: 15
        return_to_dock: true
      
      # Low battery handling
      battery_management:
        auto_return_threshold: 20  # % battery
        charging_notification: true
        manual_override: false
      
      # Alerts
      alerts:
        motion_detected: true
        door_activity: true
        bark_detected: true  # For Benny
        low_battery: true
        offline: true
    
    # Stroheckgasse apartment map
    location:
      home_base: {x: 0.0, y: 0.0}  # Charging dock location
      rooms:
        - name: "living_room"
          bounds: {x_min: 0, x_max: 5, y_min: 0, y_max: 4}
        - name: "bedroom"
          bounds: {x_min: 5, x_max: 8, y_min: 0, y_max: 3}
        - name: "kitchen"
          bounds: {x_min: 0, x_max: 3, y_min: 4, y_max: 7}
      
      patrol_waypoints:
        - {x: 2.0, y: 2.0, room: "living_room"}
        - {x: 1.0, y: 5.0, room: "kitchen"}
        - {x: 6.0, y: 1.5, room: "bedroom"}
        - {x: 0.5, y: 0.5, room: "home_base"}
```

#### API Integration Example

```python
from moorebot_scout import ScoutSDK
import rospy
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist

class MoorebotScoutIntegration:
    """MCP integration for Moorebot Scout"""
    
    def __init__(self, ip_address: str):
        self.sdk = ScoutSDK(ip_address)
        self.ros_node = None
        
    async def initialize(self):
        """Initialize SDK and ROS node"""
        await self.sdk.connect()
        self.ros_node = rospy.init_node('moorebot_scout_mcp')
        
    async def get_status(self) -> Dict:
        """Get robot status"""
        return {
            "battery": await self.sdk.get_battery_level(),
            "position": await self.sdk.get_position(),
            "wifi_signal": await self.sdk.get_wifi_strength(),
            "charging": await self.sdk.is_charging(),
            "sensors": {
                "tof_distance": await self.sdk.get_tof_reading(),
                "imu": await self.sdk.get_imu_data(),
                "light_level": await self.sdk.get_light_sensor()
            }
        }
    
    async def start_patrol(self, route: str):
        """Start security patrol"""
        waypoints = self.get_patrol_waypoints(route)
        for wp in waypoints:
            await self.sdk.navigate_to(wp['x'], wp['y'])
            await self.sdk.rotate(360)  # Scan area
            await asyncio.sleep(5)  # Wait at waypoint
        await self.sdk.return_to_dock()
    
    async def get_camera_snapshot(self) -> bytes:
        """Get current camera frame"""
        return await self.sdk.get_snapshot()
    
    async def get_video_stream(self) -> str:
        """Get RTSP stream URL"""
        return f"rtsp://{self.sdk.ip_address}:8554/stream"
    
    async def move(self, linear: float, angular: float):
        """Move robot (mecanum wheels)"""
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        await self.sdk.publish_twist(twist)
```

### 3. Unitree Go2 Dogbot (Planned 2025)

#### Specifications

**Unitree Go2:**
- **Type**: Quadruped robot (robotic dog)
- **Dimensions**: 70cm x 31cm x 40cm (standing)
- **Weight**: ~15kg (with battery)
- **Payload**: ~8kg (max 10kg)
- **Speed**: Up to 5 m/s
- **Battery**: 8,000mAh (optional 15,000mAh)
- **Runtime**: 2-4 hours
- **Sensors**: 4D LiDAR L1 (360°x90°), cameras
- **Connectivity**: Wi-Fi 6, Bluetooth, 4G
- **Price**: ~$1,600-2,000

**Key Features:**
- **Advanced AI**: Upside-down walking, adaptive roll-over, obstacle climbing
- **LiDAR Mapping**: 3D mapping and navigation
- **Voice Recognition**: Built-in voice control
- **Autonomous Navigation**: Path planning and obstacle avoidance
- **API Access**: Unitree SDK for developers

#### Integration Capabilities

**Potential Use Cases:**
1. **Security Patrol**: Autonomous home patrol
2. **Emergency Response**: Respond to medical emergencies
3. **Delivery**: Carry items between rooms
4. **Monitoring**: Mobile camera platform
5. **Companion**: Interactive pet-like behavior

**Integration Options:**

**Option 1: Unitree SDK**
- **Language**: Python, C++, ROS
- **Features**: Full robot control, sensor data access
- **Complexity**: Moderate (requires robotics knowledge)

**Option 2: ROS Integration**
- **Framework**: Robot Operating System (ROS)
- **Benefits**: Standard robotics framework
- **Integration**: Bridge ROS to MCP

**Option 3: MQTT Bridge**
- **Method**: Create MQTT bridge for Unitree
- **Benefits**: Easy integration with existing system
- **Complexity**: Moderate

#### Recommended Integration

```yaml
robotics:
  unitree_go2:
    enabled: false  # Enable when purchased
    integration_type: "unitree_sdk"
    unitree_sdk:
      api_key: ""  # Unitree API key
      robot_id: ""  # Robot identifier
      connection_type: "wifi"  # or "bluetooth", "4g"
    
    features:
      navigation: true
      patrol: true
      emergency_response: true
      delivery: true
      monitoring: true
    
    automation:
      security_patrol:
        enabled: true
        schedule: ["22:00", "02:00", "06:00"]  # Night patrols
        route: "default_patrol_route"
      
      emergency_response:
        enabled: true
        trigger_on: ["fall_detection", "gas_leak", "medical_emergency"]
        actions: ["navigate_to_location", "assess_situation", "alert_authorities"]
      
      delivery:
        enabled: false
        pickup_locations: []
        delivery_locations: []
```

### 3. Butlerbot (Planned 2025)

#### Research Findings

**Butlerbot Options:**

**Option 1: Unitree G1 (Humanoid)**
- **Type**: Humanoid robot
- **Features**: Bipedal walking, arm manipulation
- **Status**: Available 2024-2025
- **Price**: ~$16,000-20,000

**Option 2: Custom Butlerbot**
- **Base**: Mobile robot platform (TurtleBot, etc.)
- **Arms**: Robotic arms for manipulation
- **Custom Build**: Requires significant development

**Option 3: Commercial Butler Robots**
- **Aeolus Robot**: Home assistant robot
- **Temi Robot**: Telepresence and assistant
- **Astro (Amazon)**: Home monitoring and delivery

#### Recommended: Unitree G1 (If Budget Allows)

**Unitree G1 Humanoid:**
- **Height**: ~1.27m
- **Weight**: ~35kg
- **Payload**: ~3kg per arm
- **Features**: Bipedal walking, object manipulation, voice control
- **Integration**: Unitree SDK (similar to Go2)

## Database Schema

```sql
-- Kitchen appliances table
CREATE TABLE kitchen_appliances (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    device_type VARCHAR(50), -- 'water_boiler', 'refrigerator', 'grill', 'oven'
    brand VARCHAR(100), -- 'zojirushi', 'samsung', 'tefal'
    location VARCHAR(255), -- 'kitchen', 'dining_room'
    integration_type VARCHAR(50), -- 'smart_plug', 'api', 'mqtt'
    integration_config JSONB,
    enabled BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50), -- 'online', 'offline', 'error'
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Kitchen appliance states
CREATE TABLE kitchen_appliance_states (
    id SERIAL PRIMARY KEY,
    appliance_id INTEGER REFERENCES kitchen_appliances(id),
    state_type VARCHAR(50), -- 'power', 'temperature', 'water_level', 'inventory'
    value JSONB, -- Flexible value storage
    timestamp TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- Robotics table
CREATE TABLE robots (
    id SERIAL PRIMARY KEY,
    robot_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    robot_type VARCHAR(50), -- 'vacuum', 'quadruped', 'humanoid', 'butler', 'mobile_security'
    brand VARCHAR(100), -- 'irobot', 'unitree', 'moorebot', 'custom'
    model VARCHAR(100), -- 'roomba_j7', 'go2', 'g1', 'scout', 'scout_e'
    integration_type VARCHAR(50), -- 'api', 'sdk', 'mqtt', 'ros'
    integration_config JSONB,
    enabled BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP WITH TIME ZONE,
    battery_level INTEGER, -- 0-100
    status VARCHAR(50), -- 'idle', 'cleaning', 'patrolling', 'charging', 'error'
    current_location VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Robot tasks/jobs
CREATE TABLE robot_tasks (
    id SERIAL PRIMARY KEY,
    robot_id INTEGER REFERENCES robots(id),
    task_type VARCHAR(50), -- 'clean', 'patrol', 'delivery', 'monitor', 'emergency'
    status VARCHAR(50), -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    parameters JSONB, -- Task-specific parameters
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    metadata JSONB
);

-- Robot locations/positions
CREATE TABLE robot_positions (
    id SERIAL PRIMARY KEY,
    robot_id INTEGER REFERENCES robots(id),
    x FLOAT, -- X coordinate (if mapped)
    y FLOAT, -- Y coordinate (if mapped)
    z FLOAT, -- Z coordinate (if 3D)
    heading FLOAT, -- Orientation/heading
    room VARCHAR(255), -- Room name
    timestamp TIMESTAMP WITH TIME ZONE,
    source VARCHAR(50) -- 'lidar', 'camera', 'odometry'
);
```

## Configuration

```yaml
kitchen:
  enabled: true
  
  appliances:
    zojirushi_water_boiler:
      enabled: true
      device_type: "water_boiler"
      brand: "zojirushi"
      location: "kitchen"
      integration_type: "smart_plug"
      smart_plug_id: "tapo_p115_kitchen"
      schedule:
        morning_refill:
          enabled: true
          time: "06:00"
          duration_minutes: 15
        evening_refill:
          enabled: true
          time: "21:00"
          duration_minutes: 15
      monitoring:
        power_threshold_watts: 50
        alert_on_empty: true
    
    samsung_fridge:
      enabled: false
      device_type: "refrigerator"
      brand: "samsung"
      location: "kitchen"
      integration_type: "smartthings"
      smartthings:
        api_key: ""
        device_id: ""
        poll_interval_seconds: 60
      features:
        temperature_monitoring: true
        energy_monitoring: true
        door_status: true
    
    tefal_grill:
      enabled: false
      device_type: "grill"
      brand: "tefal"
      location: "kitchen"
      integration_type: "tuya"  # or "api"
      integration_config:
        device_id: ""
        api_key: ""

robotics:
  enabled: true
  
  moorebot_scout:
    enabled: false  # Enable XMas 2025
    robot_type: "mobile_security"
    brand: "moorebot"
    model: "scout_original"
    integration_type: "sdk_ros"
    sdk:
      github_repo: "https://github.com/Pilot-Labs-Dev/Scout-open-source"
      ros_version: "1.4"
      rosbridge_port: 9090
      video_stream_port: 8554
    connection:
      ip_address: ""
      port: 8080
    features:
      camera: true
      navigation: true
      obstacle_avoidance: true
      auto_dock: true
    automation:
      security_patrol:
        enabled: false
        schedule: ["08:00", "14:00", "20:00", "02:00"]
      benny_follow:
        enabled: false
  
  roomba:
    enabled: true
    robot_type: "vacuum"
    brand: "irobot"
    model: "j7+"  # or user's model
    integration_type: "irobot_api"
    irobot_api:
      username: ""
      password: ""
      endpoint: "https://api.irobot.com"
    features:
      start_cleaning: true
      stop_cleaning: true
      get_status: true
      get_map: true
      schedule_cleaning: true
    automation:
      schedule:
        enabled: true
        times: ["09:00", "15:00"]
      auto_clean_on_absence: false
  
  unitree_go2:
    enabled: false  # Enable when purchased
    robot_type: "quadruped"
    brand: "unitree"
    model: "go2"
    integration_type: "unitree_sdk"
    unitree_sdk:
      api_key: ""
      robot_id: ""
      connection_type: "wifi"
    features:
      navigation: true
      patrol: true
      emergency_response: true
      delivery: true
      monitoring: true
    automation:
      security_patrol:
        enabled: true
        schedule: ["22:00", "02:00", "06:00"]
        route: "default_patrol_route"
      emergency_response:
        enabled: true
        trigger_on: ["fall_detection", "gas_leak", "medical_emergency"]
  
  unitree_g1:
    enabled: false  # Future: butlerbot
    robot_type: "humanoid"
    brand: "unitree"
    model: "g1"
    integration_type: "unitree_sdk"
    # Similar config to Go2
```

## API Endpoints

### Kitchen Appliances

```python
# Kitchen appliance endpoints
GET /api/kitchen/appliances - List all kitchen appliances
GET /api/kitchen/appliances/{id} - Get appliance details
GET /api/kitchen/appliances/{id}/status - Get appliance status
POST /api/kitchen/appliances/{id}/control - Control appliance (on/off, temp, etc.)
GET /api/kitchen/appliances/{id}/schedule - Get appliance schedule
POST /api/kitchen/appliances/{id}/schedule - Update appliance schedule

# Water boiler specific
POST /api/kitchen/water-boiler/refill - Trigger refill
GET /api/kitchen/water-boiler/status - Get water level/power status

# Refrigerator specific
GET /api/kitchen/fridge/temperature - Get fridge temperatures
GET /api/kitchen/fridge/door-status - Get door open/close status
GET /api/kitchen/fridge/energy - Get energy usage
```

### Robotics

```python
# Robot endpoints
GET /api/robotics/robots - List all robots
GET /api/robotics/robots/{id} - Get robot details
GET /api/robotics/robots/{id}/status - Get robot status
GET /api/robotics/robots/{id}/position - Get robot position

# Robot control
POST /api/robotics/robots/{id}/start - Start robot task
POST /api/robotics/robots/{id}/stop - Stop robot
POST /api/robotics/robots/{id}/pause - Pause robot
POST /api/robotics/robots/{id}/return-home - Return to charging station

# Roomba specific
POST /api/robotics/roomba/clean - Start cleaning
POST /api/robotics/roomba/clean-room - Clean specific room
GET /api/robotics/roomba/map - Get cleaning map
GET /api/robotics/roomba/history - Get cleaning history

# Moorebot Scout specific
POST /api/robotics/moorebot/patrol - Start security patrol
POST /api/robotics/moorebot/navigate - Navigate to waypoint
GET /api/robotics/moorebot/camera/snapshot - Get camera snapshot
GET /api/robotics/moorebot/camera/stream - Get RTSP stream URL
GET /api/robotics/moorebot/sensors - Get sensor data (ToF, IMU, light)
POST /api/robotics/moorebot/dock - Return to charging dock
POST /api/robotics/moorebot/move - Control movement (mecanum wheels)

# Unitree specific
POST /api/robotics/unitree/patrol - Start patrol route
POST /api/robotics/unitree/navigate - Navigate to location
POST /api/robotics/unitree/emergency-response - Emergency response mode
GET /api/robotics/unitree/sensors - Get sensor data (LiDAR, cameras)
```

## Dashboard Pages

### 1. Kitchen Dashboard (`/kitchen`)

**Features:**
- Water boiler status and schedule
- Refrigerator temperature and status
- Smart grill status
- Appliance energy usage
- Quick controls (refill boiler, etc.)

### 2. Robotics Dashboard (`/robotics`)

**Features:**
- Robot status overview (all robots)
- **Moorebot Scout**: Live camera feed, patrol status, battery, position, controls
- Roomba: Cleaning status, map, schedule
- Unitree Go2: Status, battery, current task, position
- Robot controls (start/stop tasks)
- Task history and logs
- Live robot positions (if mapped)

**Moorebot Scout Panel:**
- Live 1080p camera stream (RTSP)
- Manual controls (joystick, rotate)
- Battery level and charging status
- Sensor readings (ToF distance, IMU, light)
- Quick actions: Start patrol, Return to dock, Benny follow
- Patrol schedule editor
- Position on apartment map
- Event log (motion detected, bark detected, etc.)

## Integration Services

### 1. Zojirushi Water Boiler Service

```python
class ZojirushiWaterBoilerService:
    """Service for Zojirushi water boiler via smart plug"""
    
    def __init__(self, smart_plug_id: str):
        self.smart_plug_id = smart_plug_id
        self.tapo_manager = TapoPlugManager()
    
    async def get_status(self) -> Dict:
        """Get water boiler status (power consumption indicates empty/full)"""
        device = await self.tapo_manager.get_device_status(self.smart_plug_id)
        power = device.current_power
        
        # Logic: Low power = empty, high power = heating, medium = maintaining
        if power < 50:
            status = "empty"
        elif power > 500:
            status = "heating"
        else:
            status = "maintaining"
        
        return {
            "status": status,
            "power_watts": power,
            "is_on": device.power_state
        }
    
    async def schedule_refill(self, time: str, duration_minutes: int):
        """Schedule automatic refill"""
        # Use existing scheduling system
        pass
    
    async def trigger_refill(self):
        """Manually trigger refill"""
        await self.tapo_manager.toggle_device(self.smart_plug_id, turn_on=True)
        # Schedule auto-off after duration
        pass
```

### 2. Roomba Integration Service

```python
class RoombaIntegrationService:
    """Service for iRobot Roomba integration"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.api_client = None
    
    async def get_robot_status(self, robot_id: str) -> Dict:
        """Get Roomba status"""
        # Use iRobot API
        pass
    
    async def start_cleaning(self, robot_id: str, room: str = None):
        """Start cleaning (optionally specific room)"""
        pass
    
    async def get_cleaning_map(self, robot_id: str) -> Dict:
        """Get current cleaning map"""
        pass
```

### 3. Unitree Integration Service

```python
class UnitreeIntegrationService:
    """Service for Unitree Go2/G1 integration"""
    
    def __init__(self, api_key: str, robot_id: str):
        self.api_key = api_key
        self.robot_id = robot_id
        self.sdk_client = None
    
    async def get_robot_status(self) -> Dict:
        """Get robot status (battery, position, current task)"""
        pass
    
    async def start_patrol(self, route: str):
        """Start security patrol route"""
        pass
    
    async def navigate_to(self, x: float, y: float, z: float = None):
        """Navigate to specific location"""
        pass
    
    async def emergency_response(self, location: Dict, emergency_type: str):
        """Respond to emergency at location"""
        pass
```

## Implementation Timeline

### Phase 1: Kitchen Integration (Weeks 1-4)
- Week 1-2: Zojirushi smart plug integration
- Week 3: Samsung fridge integration (if API available)
- Week 4: Tefal grill integration

### Phase 2: Moorebot Scout Integration (Weeks 5-7)
- Week 5: SDK setup and ROS bridge
- Week 6: Camera streaming and controls
- Week 7: Patrol automation and Benny follow mode

### Phase 3: Roomba Integration (Weeks 8-9)
- Week 8: iRobot API integration
- Week 9: Roomba dashboard and controls

### Phase 4: Robotics Dashboard (Weeks 10-11)
- Week 10: Robotics dashboard UI
- Week 11: Robot status and controls

### Phase 5: Unitree Preparation (Weeks 12-13)
- Week 12: Unitree SDK research and setup
- Week 13: Unitree integration framework (ready for when purchased)

**Total Estimated Time**: 13 weeks (3.25 months)

## Cost Analysis

### Kitchen Appliances
- **Zojirushi Smart Plug**: Already owned (Tapo P115)
- **Samsung Smart Fridge**: $2,000-4,000 (if upgrading)
- **Tefal Grill**: Already owned

### Robotics
- **Moorebot Scout**: ~€200-300 (XMas 2025 purchase)
- **Roomba**: Already owned
- **Unitree Go2**: ~$1,600-2,000 (planned purchase)
- **Unitree G1**: ~$16,000-20,000 (future consideration)

### Development Costs
- Developer time: ~10 weeks
- API access: Free (iRobot, SmartThings developer accounts)
- Infrastructure: No additional costs

## Security & Privacy

### Kitchen Appliances
- **Data Privacy**: Appliance usage data
- **Access Control**: Restrict control access
- **Safety**: Prevent unauthorized appliance control

### Robotics
- **Robot Control**: Secure API access
- **Location Data**: Robot position privacy
- **Safety**: Emergency stop mechanisms
- **Autonomous Behavior**: Safe operation protocols

## References

- [Moorebot Scout Open Source SDK](https://github.com/Pilot-Labs-Dev/Scout-open-source)
- [Moorebot Official Website](https://www.moorebot.com/)
- [ROS Melodic Documentation](http://wiki.ros.org/melodic)
- [iRobot API Documentation](https://developer.irobot.com/)
- [Unitree Go2 Specifications](https://www.unitree.com/mobile/go2/)
- [Unitree G1 Humanoid](https://www.unitree.com/)
- [Samsung SmartThings API](https://developer.smartthings.com/)
- [Home Assistant Roomba Integration](https://www.home-assistant.io/integrations/roomba/)
- [Valetudo (Open Source Roomba)](https://valetudo.cloud/)

## Related Documents

- `docs/EMERGENCY_DETECTION_AND_VOICE_INTEGRATION_PLAN.md` - Emergency response (Unitree integration)
- `docs/HOME_SECURITY_ENERGY_PLAN.md` - Energy monitoring (Tapo P115 integration)

---

**Last Updated**: 2025-12-02  
**Next Review**: When Moorebot Scout arrives (post-XMas 2025)

