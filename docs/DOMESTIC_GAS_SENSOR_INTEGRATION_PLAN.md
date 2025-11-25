# Domestic Gas Sensor Integration Plan

**Timestamp**: 2025-01-17  
**Status**: PLANNING - Research Complete  
**Tags**: gas-detection, safety, home-automation, natural-gas, propane, co-detection

## Overview

This document outlines the plan for integrating domestic gas leak detection sensors into the Home Security MCP system. Gas leaks from cooking appliances (especially wok burners) and gas boilers pose serious safety risks, and early detection is critical for preventing accidents.

## Gas Types & Detection Requirements

### 1. Natural Gas (Methane - CH₄)
- **Source**: Gas stoves, ovens, water heaters, boilers
- **Properties**: Lighter than air, rises to ceiling
- **Detection**: Place sensors near ceiling (6-12 inches from top)
- **LEL (Lower Explosive Limit)**: 5% concentration
- **Odor**: Mercaptan added for detection (rotten egg smell)

### 2. Propane / LPG (Liquefied Petroleum Gas)
- **Source**: Portable stoves, outdoor grills, some boilers
- **Properties**: Heavier than air, sinks to floor
- **Detection**: Place sensors near floor (6-12 inches from bottom)
- **LEL**: 2.1% concentration
- **Odor**: Mercaptan added for detection

### 3. Carbon Monoxide (CO)
- **Source**: Incomplete combustion from gas appliances
- **Properties**: Slightly lighter than air, mixes with air
- **Detection**: Place at breathing level (5-6 feet high)
- **Danger Level**: 50 ppm (parts per million) - immediate danger
- **No Odor**: Silent killer, requires electronic detection

## Available Gas Sensors

### Commercial Smart Gas Detectors

#### 1. **DeNova Detect 10-Year Natural Gas Detector**
- **Type**: Natural gas (methane) detection
- **Technology**: MEMS hot-wire semiconductor
- **Battery**: 10-year battery life
- **Connectivity**: Amazon Sidewalk (enhanced connectivity)
- **Features**:
  - Voice alerts (English/Spanish)
  - Fast and accurate detection
  - Smart home integration
  - NFPA 715 compliant
- **Placement**: Near ceiling
- **Cost**: ~$100-150
- **Integration**: Amazon Sidewalk, smart home platforms
- **Reference**: [DeNova Detect](https://denovadetect.com/)

#### 2. **Kidde Smart Gas Detector**
- **Type**: Natural gas detection
- **Connectivity**: Wi-Fi
- **Features**:
  - Smartphone alerts
  - IFTTT integration
  - Battery backup
  - Mobile app monitoring
- **Cost**: ~$50-80
- **Integration**: Wi-Fi, IFTTT, Kidde app
- **Reference**: [Kidde](https://www.kidde.com/)

#### 3. **Grus Smart Gas Leak Detector**
- **Type**: Methane, propane, natural gas
- **Connectivity**: Wi-Fi, Grus App
- **Features**:
  - Detects leaks as low as 5% LEL
  - Remote monitoring
  - Instant alerts
  - Real-time gas concentration display
- **Cost**: ~$80-120
- **Integration**: Grus App, Wi-Fi
- **Reference**: [Grus](https://grus.io/)

#### 4. **ZUIDID Wi-Fi Natural Gas Alarm Sensor**
- **Type**: Natural gas detection
- **Connectivity**: Wi-Fi, Tuya app
- **Features**:
  - LCD display
  - Temperature monitoring
  - Audible and visual alerts
  - Phone notifications
  - Gas concentration levels
- **Cost**: ~$60-90
- **Integration**: Tuya app, Wi-Fi
- **Reference**: [ZUIDID](https://www.probablybest.co/)

#### 5. **Vighnaharta TSGC230-WiFi Gas Leak Sensor**
- **Type**: LPG, CNG, PNG (all types)
- **Connectivity**: Wi-Fi, IoT cloud
- **Features**:
  - Bar-graph gas concentration indication
  - Heat detection
  - Cloud connectivity
  - Mobile app alerts
- **Cost**: ~$100-150
- **Integration**: Wi-Fi, cloud platform
- **Reference**: [Vighnaharta](https://www.vighnaharta.in/)

#### 6. **IK-W6 Wireless Gas Leak Detector**
- **Type**: Natural gas detection
- **Connectivity**: RF433MHz, IKCONECT systems
- **Features**:
  - Wireless operation
  - Push notifications
  - Security alarm integration
  - Smart scene automations
- **Cost**: ~$70-100
- **Integration**: RF433MHz, IKCONECT alarm systems
- **Reference**: [IKCONECT](https://ikconect.com/)

#### 7. **Mini Merlin Gas Safety System**
- **Type**: Natural gas (methane) and CO
- **Connectivity**: BMS, fire panels
- **Features**:
  - Dual detection (gas + CO)
  - Automatic gas shutoff valve
  - Building Management System integration
  - Fire panel integration
- **Cost**: ~$300-500 (commercial grade)
- **Integration**: BMS, fire panels, professional systems
- **Reference**: [American Gas Safety](https://americangassafety.com/)

### DIY Gas Sensors (For Advanced Users)

#### 1. **MQ-2 Gas Sensor Module**
- **Type**: LPG, propane, methane, smoke, alcohol
- **Interface**: Analog output
- **Platform**: Arduino, ESP32, ESP8266, Raspberry Pi
- **Cost**: ~$5-10
- **Integration**: MQTT, Home Assistant, custom code
- **Pros**: Very cheap, versatile
- **Cons**: Requires calibration, less accurate than commercial

#### 2. **MQ-5 Gas Sensor Module**
- **Type**: Natural gas, LPG, town gas
- **Interface**: Analog output
- **Platform**: Arduino, ESP32, ESP8266
- **Cost**: ~$5-10
- **Integration**: MQTT, Home Assistant
- **Pros**: Cheap, good for natural gas
- **Cons**: Requires calibration

#### 3. **MQ-6 Gas Sensor Module**
- **Type**: LPG, butane, propane
- **Interface**: Analog output
- **Platform**: Arduino, ESP32, ESP8266
- **Cost**: ~$5-10
- **Integration**: MQTT, Home Assistant
- **Pros**: Cheap, good for LPG
- **Cons**: Requires calibration

#### 4. **ESP32 + MQ Sensor DIY Solution**
- **Components**: ESP32, MQ-2/MQ-5/MQ-6, relay module (optional)
- **Connectivity**: Wi-Fi, MQTT
- **Features**:
  - Custom firmware (ESPHome, Tasmota, or custom)
  - Home Assistant integration
  - MQTT publishing
  - Web interface
- **Cost**: ~$15-25 (components)
- **Integration**: MQTT, Home Assistant, custom API
- **Pros**: Full control, customizable, cheap
- **Cons**: Requires technical knowledge, calibration needed

## Integration Protocols & Methods

### 1. Wi-Fi Integration
**Supported Devices**: Kidde, Grus, ZUIDID, Vighnaharta

**Integration Methods**:
- **Manufacturer Apps**: Direct API access (if available)
- **Tuya Integration**: ZUIDID and other Tuya devices
- **IFTTT**: Kidde and other IFTTT-compatible devices
- **Reverse Engineering**: Intercept Wi-Fi traffic (advanced)

**Pros**:
- Direct internet connectivity
- Real-time alerts
- Remote monitoring

**Cons**:
- Requires internet connection
- May require cloud services
- Privacy concerns

### 2. Zigbee Integration
**Supported Devices**: Some commercial detectors

**Integration Methods**:
- **Zigbee2MQTT**: Convert Zigbee to MQTT
- **Home Assistant Zigbee**: Direct integration
- **Zigbee Hub**: Use compatible hub

**Pros**:
- Local network (no cloud)
- Low power consumption
- Mesh networking

**Cons**:
- Requires Zigbee hub
- Limited device selection

### 3. Z-Wave Integration
**Supported Devices**: Some commercial detectors

**Integration Methods**:
- **Z-Wave Controller**: Use compatible controller
- **Home Assistant Z-Wave**: Direct integration

**Pros**:
- Local network
- Reliable mesh network
- Good range

**Cons**:
- Requires Z-Wave controller
- More expensive devices

### 4. MQTT Integration (Recommended for DIY)
**Supported Devices**: ESP32-based DIY sensors, some commercial

**Integration Methods**:
- **MQTT Broker**: Mosquitto or similar
- **MQTT Client**: Subscribe to gas sensor topics
- **Home Assistant MQTT**: Direct integration

**Pros**:
- Standard protocol
- Works with any MQTT device
- Local or cloud
- Easy to integrate

**Cons**:
- Requires MQTT broker
- DIY sensors need firmware

### 5. RF433MHz Integration
**Supported Devices**: IK-W6, some alarm systems

**Integration Methods**:
- **RF433MHz Receiver**: USB dongle or ESP32
- **rtl_433**: Software-defined radio
- **Home Assistant RF433**: Integration via receiver

**Pros**:
- Works with many devices
- No pairing needed
- Long range

**Cons**:
- One-way communication (usually)
- Requires receiver hardware
- Less secure

## Recommended Integration Strategy

### Phase 1: Commercial Wi-Fi Sensors (Quick Start)

**Recommended Devices**:
1. **DeNova Detect** (natural gas) - Best overall
2. **Kidde Smart Gas Detector** (natural gas) - Budget option
3. **Grus Smart Gas Leak Detector** (multi-gas) - Versatile

**Integration Approach**:
1. Use manufacturer apps for initial setup
2. Reverse engineer API calls (if needed)
3. Create integration service to poll/connect to devices
4. Store readings in database
5. Trigger alerts in dashboard

### Phase 2: MQTT Integration (DIY Sensors)

**Recommended Setup**:
1. **ESP32 + MQ-5 Sensor** (natural gas)
2. **ESP32 + MQ-6 Sensor** (LPG/propane)
3. **ESPHome Firmware** (easy Home Assistant integration)
4. **MQTT Broker** (Mosquitto)

**Integration Approach**:
1. Flash ESPHome firmware to ESP32
2. Configure MQTT publishing
3. Connect to MQTT broker
4. Subscribe to gas sensor topics
5. Store readings in database
6. Trigger alerts

### Phase 3: Unified Integration Layer

**Architecture**:
```
Gas Sensors (Various Types)
  ↓
Integration Services (Wi-Fi, MQTT, Zigbee, etc.)
  ↓
Unified Gas Detection Service
  ↓
Database (PostgreSQL)
  ↓
Dashboard & Alerts
```

## Database Schema

```sql
-- Gas sensor devices table
CREATE TABLE gas_sensors (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    sensor_type VARCHAR(50), -- 'natural_gas', 'propane', 'lpg', 'co', 'multi'
    location VARCHAR(255), -- 'kitchen', 'boiler_room', 'garage'
    placement VARCHAR(50), -- 'ceiling', 'floor', 'breathing_level'
    integration_type VARCHAR(50), -- 'wifi', 'mqtt', 'zigbee', 'zwave'
    integration_config JSONB, -- API keys, MQTT topics, etc.
    enabled BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP WITH TIME ZONE,
    battery_level INTEGER, -- 0-100 if battery-powered
    status VARCHAR(50), -- 'online', 'offline', 'error'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gas readings table
CREATE TABLE gas_readings (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES gas_sensors(id),
    gas_type VARCHAR(50), -- 'natural_gas', 'propane', 'co'
    concentration FLOAT, -- ppm or % LEL
    unit VARCHAR(20), -- 'ppm', 'percent_lel'
    temperature FLOAT, -- if sensor has temperature
    timestamp TIMESTAMP WITH TIME ZONE,
    alert_triggered BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- Gas alerts table
CREATE TABLE gas_alerts (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER REFERENCES gas_sensors(id),
    alert_type VARCHAR(50), -- 'gas_leak', 'high_concentration', 'sensor_failure'
    severity VARCHAR(50), -- 'warning', 'critical', 'emergency'
    concentration FLOAT,
    threshold FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    actions_taken JSONB, -- What actions were taken (shutoff valve, ventilation, etc.)
    metadata JSONB
);
```

## Configuration

```yaml
gas_detection:
  enabled: true
  
  sensors:
    - device_id: "denova_kitchen_01"
      name: "Kitchen Natural Gas Detector"
      sensor_type: "natural_gas"
      location: "kitchen"
      placement: "ceiling"
      integration_type: "wifi"
      integration_config:
        type: "denova"
        api_key: ""  # If API available
        device_id: ""  # Device identifier
        poll_interval_seconds: 30
      thresholds:
        warning_ppm: 1000  # 0.1% natural gas
        critical_ppm: 5000  # 0.5% natural gas
        emergency_ppm: 10000  # 1% natural gas (explosive range)
    
    - device_id: "mqtt_boiler_01"
      name: "Boiler Room Gas Sensor"
      sensor_type: "natural_gas"
      location: "boiler_room"
      placement: "ceiling"
      integration_type: "mqtt"
      integration_config:
        broker_host: "localhost"
        broker_port: 1883
        topic: "home/gas/boiler_room"
        username: ""  # MQTT credentials
        password: ""
      thresholds:
        warning_ppm: 1000
        critical_ppm: 5000
        emergency_ppm: 10000
    
    - device_id: "grus_propane_01"
      name: "Garage Propane Detector"
      sensor_type: "propane"
      location: "garage"
      placement: "floor"
      integration_type: "wifi"
      integration_config:
        type: "grus"
        device_id: ""
        api_key: ""
        poll_interval_seconds: 30
      thresholds:
        warning_percent_lel: 10  # 10% of LEL
        critical_percent_lel: 25  # 25% of LEL
        emergency_percent_lel: 50  # 50% of LEL
  
  alerts:
    enabled: true
    notification_channels:
      - type: "dashboard"
        enabled: true
      - type: "sms"
        enabled: true
        phone_numbers: ["+1234567890"]
      - type: "email"
        enabled: true
        emails: ["user@example.com"]
      - type: "voice"
        enabled: true
        message: "WARNING: Gas leak detected in {location}!"
    
    escalation:
      warning:
        actions: ["dashboard_alert", "sms"]
        delay_seconds: 0
      critical:
        actions: ["dashboard_alert", "sms", "email", "voice_alert"]
        delay_seconds: 0
      emergency:
        actions: ["dashboard_alert", "sms", "email", "voice_alert", "emergency_services"]
        delay_seconds: 30  # Wait 30 seconds, then call 911 if not resolved
  
  automation:
    gas_shutoff_valve:
      enabled: false  # Requires smart gas valve
      trigger_on: "critical"  # or "emergency"
      valve_device_id: ""  # Smart valve device ID
    
    ventilation:
      enabled: false  # Requires smart ventilation
      trigger_on: "warning"  # or "critical"
      fan_device_ids: []  # Smart fan/ventilation device IDs
    
    emergency_services:
      enabled: true
      trigger_on: "emergency"
      auto_call: false  # Require confirmation
      critical_auto_call: true  # Auto-call for critical after delay
      location: "123 Main St, City, State"
```

## API Endpoints

```python
# Gas sensor endpoints
GET /api/gas/sensors - List all gas sensors
GET /api/gas/sensors/{id} - Get sensor details
GET /api/gas/sensors/{id}/readings - Get sensor readings
GET /api/gas/sensors/{id}/alerts - Get sensor alerts
POST /api/gas/sensors/{id}/test - Trigger test alarm

# Gas readings endpoints
GET /api/gas/readings - Get all gas readings (with filters)
GET /api/gas/readings/latest - Get latest readings from all sensors
GET /api/gas/readings/history - Get historical readings

# Gas alerts endpoints
GET /api/gas/alerts - Get all gas alerts
GET /api/gas/alerts/active - Get active alerts
POST /api/gas/alerts/{id}/acknowledge - Acknowledge alert
POST /api/gas/alerts/{id}/resolve - Mark alert as resolved

# Emergency actions
POST /api/gas/emergency/shutoff - Shut off gas valve (if available)
POST /api/gas/emergency/ventilate - Activate ventilation
POST /api/gas/emergency/911 - Call emergency services
```

## Integration Services

### 1. DeNova Detect Integration

```python
class DeNovaDetectClient:
    """Client for DeNova Detect gas sensors"""
    
    async def get_sensor_status(self, device_id: str) -> Dict:
        # Poll DeNova API or intercept Sidewalk traffic
        # Return sensor status, gas concentration, battery
        pass
    
    async def get_readings(self, device_id: str) -> Dict:
        # Get current gas readings
        pass
```

### 2. MQTT Integration Service

```python
class MQTTGasSensorClient:
    """Client for MQTT-based gas sensors"""
    
    def __init__(self, broker_host: str, broker_port: int):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.mqtt_client = None
    
    async def connect(self):
        # Connect to MQTT broker
        pass
    
    async def subscribe(self, topic: str, callback: Callable):
        # Subscribe to gas sensor topic
        # Callback receives: {"sensor_id": "...", "gas_type": "...", "concentration": 1234, "unit": "ppm"}
        pass
```

### 3. Grus Integration Service

```python
class GrusGasSensorClient:
    """Client for Grus smart gas detectors"""
    
    async def get_sensor_status(self, device_id: str) -> Dict:
        # Poll Grus API
        pass
    
    async def get_readings(self, device_id: str) -> Dict:
        # Get current gas readings
        pass
```

## Dashboard Integration

### Gas Detection Dashboard Page

**Features**:
- Real-time gas concentration displays
- Sensor status (online/offline, battery)
- Active alerts panel
- Historical charts (24h, 7d, 30d)
- Location-based sensor map
- Emergency action buttons

**UI Components**:
```html
<!-- Gas Detection Dashboard -->
<div class="gas-dashboard">
  <!-- Overview Cards -->
  <div class="gas-overview">
    <div class="gas-card">
      <h3>Kitchen Natural Gas</h3>
      <div class="gas-level">0 ppm</div>
      <div class="gas-status status-safe">Safe</div>
    </div>
    <!-- More sensor cards -->
  </div>
  
  <!-- Active Alerts -->
  <div class="gas-alerts">
    <h3>Active Alerts</h3>
    <!-- Alert list -->
  </div>
  
  <!-- Historical Charts -->
  <div class="gas-charts">
    <canvas id="gasChart"></canvas>
  </div>
</div>
```

## Emergency Response Automation

### Automated Actions

1. **Gas Shutoff Valve** (if available)
   - Trigger: Critical or emergency detection
   - Action: Automatically shut off gas supply
   - Safety: Manual override available

2. **Ventilation Activation**
   - Trigger: Warning or critical detection
   - Action: Turn on exhaust fans, open windows (if smart)
   - Safety: Helps disperse gas

3. **Emergency Services**
   - Trigger: Emergency detection (after delay)
   - Action: Call 911 with location and details
   - Safety: Requires confirmation (unless critical)

4. **Voice Alerts**
   - Trigger: Any detection
   - Action: "WARNING: Gas leak detected in [location]!"
   - Safety: Immediate notification

## Placement Guidelines

### Natural Gas Detectors
- **Location**: Near ceiling (6-12 inches from top)
- **Areas**: Kitchen (near stove), boiler room, water heater area
- **Avoid**: Drafty areas, near windows/doors, near exhaust fans

### Propane/LPG Detectors
- **Location**: Near floor (6-12 inches from bottom)
- **Areas**: Garage, outdoor areas, near propane tanks
- **Avoid**: Drafty areas, near windows/doors

### Carbon Monoxide Detectors
- **Location**: Breathing level (5-6 feet high)
- **Areas**: Near gas appliances, bedrooms, living areas
- **Avoid**: Directly above appliances, in dead air spaces

## Testing & Maintenance

### Regular Testing
- **Weekly**: Test alarm function (if available)
- **Monthly**: Check sensor status and connectivity
- **Quarterly**: Calibrate sensors (if required)
- **Annually**: Replace sensors (if battery-powered with limited life)

### Sensor Health Monitoring
- Battery level tracking
- Connectivity status
- Last reading timestamp
- Calibration status
- Error logs

## Cost Analysis

### Commercial Sensors
- **Budget**: $50-80 (Kidde)
- **Mid-range**: $80-150 (DeNova, Grus, ZUIDID)
- **Premium**: $150-300 (Multi-gas, professional)

### DIY Sensors
- **Components**: $15-25 (ESP32 + MQ sensor)
- **Time**: 2-4 hours setup
- **Ongoing**: Minimal (just maintenance)

### Integration Costs
- **Development**: ~2-4 weeks
- **MQTT Broker**: Free (self-hosted) or ~$5/month (cloud)
- **Infrastructure**: No additional costs (uses existing)

## Security & Safety

### Safety Considerations
- **False Positives**: Calibrate sensors properly
- **Sensor Failure**: Redundant sensors recommended
- **Power Outage**: Battery backup essential
- **Network Failure**: Local alerts should still work

### Privacy & Security
- **Data Encryption**: Encrypt gas reading data
- **Access Control**: Restrict access to gas sensor data
- **Audit Logging**: Log all gas alerts and actions
- **Compliance**: Follow local safety regulations

## Implementation Timeline

### Phase 1: Commercial Sensor Integration (Weeks 1-4)
- Week 1-2: Research and select sensors
- Week 3: Database schema and API design
- Week 4: Basic integration service

### Phase 2: Dashboard & Alerts (Weeks 5-6)
- Week 5: Dashboard UI development
- Week 6: Alert system and notifications

### Phase 3: DIY Sensor Support (Weeks 7-8)
- Week 7: MQTT integration service
- Week 8: ESP32 sensor firmware (if needed)

### Phase 4: Automation & Testing (Weeks 9-10)
- Week 9: Emergency automation (shutoff, ventilation)
- Week 10: Testing and refinement

**Total Estimated Time**: 10 weeks (2.5 months)

## References

- [DeNova Detect](https://denovadetect.com/)
- [Kidde Smart Gas Detector](https://www.kidde.com/)
- [Grus Smart Gas Leak Detector](https://grus.io/)
- [ESPHome Documentation](https://esphome.io/)
- [MQTT Protocol](https://mqtt.org/)
- [NFPA 715 - Natural Gas Detection](https://www.nfpa.org/)
- [Gas Sensor Placement Guidelines](https://www.nfpa.org/)

## Related Documents

- `docs/EMERGENCY_DETECTION_AND_VOICE_INTEGRATION_PLAN.md` - Emergency detection system
- `docs/HUMAN_HEALTH_MONITORING_PLAN.md` - Health monitoring (includes CO from gas appliances)

---

**Last Updated**: 2025-01-17  
**Next Review**: When Phase 1 implementation begins

