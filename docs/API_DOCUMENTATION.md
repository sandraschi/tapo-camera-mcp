# API Documentation - Tapo Camera MCP

Complete API reference for the Tapo Camera MCP platform including device onboarding, energy management, security integration, and camera control.

## 🎯 **Device Onboarding API**

### **Discovery & Configuration**

#### `POST /api/onboarding/discover`
Start device discovery process.

**Response:**
```json
{
  "status": "success",
  "message": "Device discovery started",
  "estimated_duration": "30-60 seconds"
}
```

#### `GET /api/onboarding/discover/results`
Get device discovery results.

**Response:**
```json
{
  "status": "success",
  "discovery_results": {
    "tapo_p115": [
      {
        "device_id": "tapo_p115_001",
        "device_type": "tapo_p115",
        "display_name": "Smart Plug 101",
        "ip_address": "192.168.1.101",
        "mac_address": "00:11:22:33:44:55",
        "model": "Tapo P115",
        "location": "Living Room",
        "capabilities": ["energy_monitoring", "power_control", "scheduling"],
        "requires_auth": true,
        "status": "discovered"
      }
    ],
    "nest_protect": [...],
    "ring_devices": [...],
    "usb_webcams": [...]
  },
  "device_counts": {
    "tapo_p115": 3,
    "nest_protect": 2,
    "ring_devices": 1,
    "usb_webcams": 1
  },
  "total_devices": 7
}
```

#### `POST /api/onboarding/configure`
Configure a discovered device.

**Request Body:**
```json
{
  "device_id": "tapo_p115_001",
  "display_name": "Living Room TV Plug",
  "location": "Living Room",
  "settings": {
    "energy_rate": 0.12,
    "automation_enabled": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Device Living Room TV Plug configured successfully",
  "device": {
    "device_id": "tapo_p115_001",
    "display_name": "Living Room TV Plug",
    "location": "Living Room",
    "status": "configured"
  }
}
```

#### `GET /api/onboarding/progress`
Get current onboarding progress.

**Response:**
```json
{
  "status": "success",
  "progress": {
    "current_step": 2,
    "total_devices_discovered": 7,
    "devices_configured": 5,
    "completed_steps": ["discovery", "configuration"],
    "onboarding_complete": false
  },
  "device_summary": {
    "tapo_p115": {"total": 3, "configured": 3},
    "nest_protect": {"total": 2, "configured": 2},
    "ring_devices": {"total": 1, "configured": 0},
    "usb_webcams": {"total": 1, "configured": 0}
  },
  "completion_percentage": 71.4,
  "next_recommended_steps": [
    "Configure 2 remaining devices",
    "Set up authentication for protected devices"
  ]
}
```

#### `POST /api/onboarding/complete`
Complete the onboarding process.

**Response:**
```json
{
  "status": "success",
  "message": "Device onboarding completed successfully!",
  "onboarding_complete": true,
  "total_devices_configured": 7,
  "device_summary": {
    "tapo_p115": 3,
    "nest_protect": 2,
    "ring_devices": 1,
    "usb_webcams": 1
  },
  "next_steps": [
    "Start using your configured devices",
    "Set up automation rules if desired",
    "Configure alert preferences",
    "Access the main dashboard at http://localhost:7777"
  ]
}
```

#### `GET /api/onboarding/recommendations`
Get smart setup recommendations based on discovered devices.

**Response:**
```json
{
  "status": "success",
  "recommendations": [
    {
      "type": "security_integration",
      "title": "Emergency Power Shutdown",
      "description": "Automatically turn off non-essential devices during smoke alarms",
      "safety_benefit": "Reduces fire risk",
      "complexity": "low",
      "estimated_setup_time": "5 minutes"
    },
    {
      "type": "energy_optimization",
      "title": "Whole House Energy Management",
      "description": "Set up coordinated schedules for all smart plugs",
      "estimated_savings": "$50-100/year",
      "complexity": "medium",
      "estimated_setup_time": "15 minutes"
    }
  ]
}
```

## ⚡ **Energy Management API**

### **Tapo P115 Smart Plug Control**

#### `GET /api/energy/smart-plugs`
Get status of all Tapo P115 smart plugs.

**Response:**
```json
{
  "status": "success",
  "devices": [
    {
      "device_id": "tapo_p115_001",
      "name": "Living Room TV Plug",
      "location": "Living Room",
      "device_model": "Tapo P115",
      "power_state": true,
      "current_power": 85.5,
      "voltage": 120.2,
      "current": 0.71,
      "daily_energy": 2.1,
      "monthly_energy": 63.5,
      "daily_cost": 0.25,
      "monthly_cost": 7.62,
      "last_seen": "2025-01-15T10:30:00Z",
      "automation_enabled": true,
      "power_schedule": "7:00-23:00 daily",
      "energy_saving_mode": false
    }
  ],
  "summary": {
    "total_devices": 3,
    "total_power": 245.8,
    "daily_energy": 6.3,
    "monthly_energy": 189.0,
    "daily_cost": 0.76,
    "monthly_cost": 22.68
  }
}
```

#### `POST /api/energy/smart-plugs/{device_id}/control`
Control a specific smart plug.

**Request Body:**
```json
{
  "action": "toggle_power",
  "parameters": {
    "power_state": true,
    "energy_saving_mode": false
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Device power state updated successfully",
  "device": {
    "device_id": "tapo_p115_001",
    "power_state": true,
    "current_power": 85.5,
    "energy_saving_mode": false
  }
}
```

#### `GET /api/energy/smart-plugs/{device_id}/stats`
Get detailed statistics for a specific smart plug.

**Response:**
```json
{
  "status": "success",
  "device_stats": {
    "device_id": "tapo_p115_001",
    "electrical_parameters": {
      "voltage": 120.2,
      "current": 0.71,
      "power": 85.5,
      "power_factor": 0.98
    },
    "energy_consumption": {
      "daily_kwh": 2.1,
      "monthly_kwh": 63.5,
      "total_kwh": 1250.8,
      "daily_cost": 0.25,
      "monthly_cost": 7.62,
      "total_cost": 150.10
    },
    "device_status": {
      "online": true,
      "last_seen": "2025-01-15T10:30:00Z",
      "uptime": "15 days, 8 hours",
      "automation_enabled": true,
      "energy_saving_mode": false
    },
    "historical_data": {
      "hourly_data": [
        {"hour": "00:00", "power": 0.0, "energy": 0.0},
        {"hour": "01:00", "power": 0.0, "energy": 0.0},
        {"hour": "07:00", "power": 85.5, "energy": 0.085},
        {"hour": "08:00", "power": 85.5, "energy": 0.085}
      ],
      "note": "Historical data limited to current day (P115 limitation)"
    }
  }
}
```

#### `POST /api/energy/smart-plugs/{device_id}/energy-saving`
Enable or disable energy saving mode.

**Request Body:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Energy saving mode enabled",
  "power_reduction": "10%",
  "estimated_savings": "$15-25/year"
}
```

## 🚨 **Security Integration API**

### **Nest Protect Devices**

#### `GET /api/alarms/nest-protect`
Get status of all Nest Protect devices.

**Response:**
```json
{
  "status": "success",
  "devices": [
    {
      "device_id": "nest_protect_001",
      "name": "Kitchen Smoke Detector",
      "location": "Kitchen",
      "model": "Nest Protect 2nd Gen",
      "battery_level": 85,
      "connectivity": "wifi",
      "smoke_level": "normal",
      "co_level": "normal",
      "last_seen": "2025-01-15T10:30:00Z",
      "test_status": "passed",
      "last_test": "2025-01-01T00:00:00Z"
    }
  ],
  "system_status": {
    "total_devices": 2,
    "online_devices": 2,
    "battery_warnings": 0,
    "connectivity_issues": 0,
    "last_alert": null
  }
}
```

### **Ring Devices**

#### `GET /api/alarms/ring`
Get status of all Ring devices.

**Response:**
```json
{
  "status": "success",
  "devices": [
    {
      "device_id": "ring_doorbell_001",
      "name": "Front Door Camera",
      "location": "Front Door",
      "model": "Ring Doorbell Pro",
      "battery_level": 78,
      "connectivity": "wifi",
      "motion_enabled": true,
      "night_vision": true,
      "last_motion": "2025-01-15T09:45:00Z",
      "last_seen": "2025-01-15T10:30:00Z"
    }
  ],
  "security_status": {
    "alarm_mode": "disarmed",
    "motion_alerts": "enabled",
    "door_alerts": "enabled",
    "last_event": "motion_detected"
  }
}
```

## 📊 **Analytics API**

### **Performance Analytics**

#### `GET /api/analytics/performance`
Get system performance analytics.

**Response:**
```json
{
  "status": "success",
  "performance_metrics": {
    "camera_system": {
      "total_cameras": 5,
      "online_cameras": 4,
      "average_response_time": 1.2,
      "stream_quality": "high",
      "storage_usage": "45%"
    },
    "energy_system": {
      "total_devices": 3,
      "average_power": 245.8,
      "daily_consumption": 6.3,
      "efficiency_score": 8.5
    },
    "security_system": {
      "total_devices": 4,
      "online_devices": 4,
      "last_alert": null,
      "security_score": 9.2
    }
  },
  "recommendations": [
    {
      "type": "performance",
      "title": "Optimize Camera Streaming",
      "description": "Reduce stream quality to improve performance",
      "impact": "medium"
    }
  ]
}
```

### **AI Scene Analysis**

#### `POST /api/analytics/scene-analysis`
Analyze camera scenes using AI.

**Request Body:**
```json
{
  "camera_id": "webcam_001",
  "analysis_type": "object_detection",
  "confidence_threshold": 0.7
}
```

**Response:**
```json
{
  "status": "success",
  "analysis_results": {
    "objects_detected": [
      {
        "object": "person",
        "confidence": 0.95,
        "bounding_box": [100, 150, 200, 300],
        "timestamp": "2025-01-15T10:30:00Z"
      }
    ],
    "scene_summary": "Person detected in living room",
    "recommendations": [
      "Consider enabling motion alerts for this area"
    ]
  }
}
```

## 🎥 **Camera Control API**

### **Camera Management**

#### `GET /api/cameras`
Get list of all cameras.

**Response:**
```json
{
  "success": true,
  "cameras": [
    {
      "camera_id": "webcam_001",
      "name": "USB Webcam",
      "type": "webcam",
      "status": "online",
      "location": "Office",
      "last_seen": "2025-01-15T10:30:00Z"
    }
  ]
}
```

#### `GET /api/cameras/{camera_id}/stream`
Get camera video stream.

**Response:**
```json
{
  "stream_url": "http://localhost:7777/api/cameras/webcam_001/stream",
  "type": "mjpeg",
  "quality": "high"
}
```

#### `GET /api/cameras/{camera_id}/snapshot`
Get camera snapshot.

**Response:** JPEG image data

#### `POST /api/cameras/{camera_id}/control`
Control camera actions.

**Request Body:**
```json
{
  "action": "start_stream"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Stream started successfully",
  "stream_url": "http://localhost:7777/api/cameras/webcam_001/stream"
}
```

## 🔧 **System Management API**

### **Server Status**

#### `GET /api/status`
Get server status.

**Response:**
```json
{
  "status": "ok",
  "version": "1.2.0",
  "debug": false,
  "uptime": "15 days, 8 hours",
  "active_connections": 12
}
```

### **Health Check**

#### `GET /api/health`
Get system health status.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "camera_manager": "healthy",
    "energy_manager": "healthy",
    "security_manager": "healthy"
  },
  "last_check": "2025-01-15T10:30:00Z"
}
```

## 📝 **Error Handling**

All API endpoints return consistent error responses:

```json
{
  "error": "Error message description",
  "error_code": "DEVICE_NOT_FOUND",
  "details": {
    "device_id": "invalid_device_id",
    "suggestion": "Check device_id format"
  }
}
```

## 🔐 **Authentication**

Most endpoints require authentication. Include the API key in the header:

```
Authorization: Bearer your_api_key_here
```

## 📊 **Rate Limiting**

API requests are rate-limited to prevent abuse:

- **General endpoints**: 100 requests per minute
- **Device control**: 10 requests per minute
- **Streaming endpoints**: 5 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## 🌐 **WebSocket Support**

Real-time updates are available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:7777/ws/updates');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

## 📱 **Mobile API**

Mobile-specific endpoints with optimized responses:

- `GET /api/mobile/status` - Mobile-optimized status
- `GET /api/mobile/cameras` - Simplified camera list
- `POST /api/mobile/quick-action` - Quick device actions

## 🔄 **Webhooks**

Configure webhooks for real-time notifications:

```json
{
  "webhook_url": "https://your-server.com/webhooks/tapo-camera",
  "events": ["device_status_change", "motion_detected", "energy_alert"],
  "secret": "your_webhook_secret"
}
```

This comprehensive API documentation covers all aspects of the Tapo Camera MCP platform, from device onboarding to advanced analytics and automation.
