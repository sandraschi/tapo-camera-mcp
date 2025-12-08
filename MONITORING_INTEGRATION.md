# Monitoring Stack Integration - Prometheus, Loki, Grafana

**Date**: 2025-12-04  
**Status**: ✅ Ready for Integration  
**Dashboard**: http://localhost:7777

---

## Overview

Tapo Camera MCP v1.8.0 includes complete monitoring integration:

- ✅ **Prometheus Metrics**: Scrape-ready endpoint at `/api/messages/prometheus`
- ✅ **Loki Logs**: Structured JSON logging for Promtail ingestion
- ✅ **Grafana Dashboards**: Query both datasources for comprehensive monitoring

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Tapo Camera MCP Dashboard                  │
│                    (localhost:7777)                         │
└─────────────────────────────────────────────────────────────┘
         │                          │                  │
         │ Prometheus              │ Logs             │ UI
         │ /api/messages/          │ JSON             │ Browser
         │ prometheus              │ stdout           │
         ▼                          ▼                  ▼
┌─────────────┐            ┌─────────────┐    ┌─────────────┐
│ Prometheus  │            │  Promtail   │    │   Browser   │
│  :9090      │            │  → Loki     │    │  Dashboard  │
└─────────────┘            │  :3100      │    └─────────────┘
         │                  └─────────────┘
         │                          │
         └──────────────┬───────────┘
                        ▼
                ┌─────────────┐
                │   Grafana   │
                │   :3000     │
                └─────────────┘
```

---

## 1. Prometheus Setup

### Install Prometheus

**Windows:**
```powershell
# Download from https://prometheus.io/download/
# Extract to D:\monitoring\prometheus\

# Or via Chocolatey
choco install prometheus
```

**Docker:**
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  prometheus_data:
```

### Configure Prometheus

**prometheus.yml:**
```yaml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  # Tapo Camera MCP Dashboard
  - job_name: 'tapo_home'
    static_configs:
      - targets: ['host.docker.internal:7777']  # Docker
        # OR ['localhost:7777']  # Native Windows
    metrics_path: '/api/messages/prometheus'
    
    # Labels for Grafana filtering
    relabel_configs:
      - target_label: 'instance'
        replacement: 'sandra_home'
      - target_label: 'location'
        replacement: 'stroheckgasse_vienna'
```

### Test Prometheus

```powershell
# Start Prometheus
cd D:\monitoring\prometheus
.\prometheus.exe --config.file=prometheus.yml

# Or with Docker
docker compose up -d prometheus

# Access Prometheus UI
Start-Process "http://localhost:9090"

# Query metrics
# PromQL: tapo_messages_total
# PromQL: tapo_unacknowledged_alarms
```

---

## 2. Loki + Promtail Setup

### Install Loki & Promtail

**Docker (Recommended):**
```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./promtail-config.yml:/etc/promtail/config.yml
      - D:\Dev\repos\tapo-camera-mcp\logs:/var/log/tapo:ro
    command: -config.file=/etc/promtail/config.yml

volumes:
  loki_data:
```

### Configure Loki

**loki-config.yml:**
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

### Configure Promtail

**promtail-config.yml:**
```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Tapo Camera MCP structured logs
  - job_name: tapo_camera_mcp
    static_configs:
      - targets:
          - localhost
        labels:
          job: tapo_home
          app: tapo_camera_mcp
          location: stroheckgasse
          __path__: /var/log/tapo/*.log
    
    # Parse JSON logs
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            category: category
            source: source
            message: message
            severity: labels.severity
      
      - timestamp:
          source: timestamp
          format: RFC3339
      
      - labels:
          level:
          severity:
          category:
          source:
      
      - output:
          source: message
```

---

## 3. Grafana Setup

### Install Grafana

**Docker:**
```yaml
# docker-compose.yml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning

volumes:
  grafana_data:
```

### Add Datasources

**Prometheus Datasource:**
```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: 30s
```

**Loki Datasource:**
```yaml
# grafana/provisioning/datasources/loki.yml
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
```

---

## 4. Grafana Dashboards

### Dashboard 1: Device Health Overview

**Panels:**
- **Device Uptime** (Prometheus): Gauge showing health percentage
- **Messages Timeline** (Loki): Alert history over time
- **Offline Devices** (Prometheus): Current offline count
- **Power Consumption** (Tapo P115): Real-time wattage
- **Alert Rate** (Prometheus): Messages per hour

**PromQL Queries:**
```promql
# Health percentage
(sum(tapo_messages_total{severity="info"}) / sum(tapo_messages_total)) * 100

# Unacknowledged alarms
tapo_unacknowledged_alarms

# Messages last hour
rate(tapo_messages_total[1h])
```

**LogQL Queries:**
```logql
# All alarms
{job="tapo_home"} | json | severity="alarm"

# Device connection events
{job="tapo_home"} | json | category="device_connection"

# Specific device
{job="tapo_home"} | json | source="plug_tapo_p115_aircon"
```

### Dashboard 2: Smart Home Overview

**Panels:**
- **Tapo P115 Power** (Real-time): 318W total
- **Hue Lights Status**: 18/18 online
- **Netatmo Temperature**: Main 26.8°C, Bathroom 26.6°C
- **Camera Status**: All online
- **Recent Alerts**: Last 10 messages

---

## 5. Complete Docker Compose Stack

**Full monitoring stack:**

```yaml
# deploy/monitoring/docker-compose.yml
version: '3.8'

services:
  # Tapo Dashboard (use myhomecontrol stack from deploy/myhomecontrol/)
  # See deploy/myhomecontrol/docker-compose.yml for full configuration
  # This is just an example showing network integration

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - monitoring

  # Loki
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    networks:
      - monitoring

  # Promtail
  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./promtail-config.yml:/etc/promtail/config.yml
      - tapo_logs:/var/log/tapo:ro
    networks:
      - monitoring

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  tapo_logs:
  prometheus_data:
  loki_data:
  grafana_data:
```

**Start entire stack:**
```powershell
cd D:\Dev\repos\tapo-camera-mcp\deploy\monitoring
docker compose up -d

# Access
Start-Process "http://localhost:7777"  # Tapo Dashboard
Start-Process "http://localhost:9090"  # Prometheus
Start-Process "http://localhost:3000"  # Grafana (admin/admin)
```

---

## 6. Example Queries

### Prometheus Queries

**Alert Rate:**
```promql
rate(tapo_messages_total[5m])
```

**Alarm Percentage:**
```promql
(tapo_messages_total{severity="alarm"} / tapo_messages_total) * 100
```

**Devices with Issues:**
```promql
tapo_unacknowledged_alarms > 0
```

### Loki Queries

**All Alarms Last Hour:**
```logql
{job="tapo_home"} | json | severity="alarm" | line_format "{{.timestamp}} {{.message}}"
```

**Device Connection Issues:**
```logql
{job="tapo_home"} | json | category="device_connection" | severity!="info"
```

**Specific Device Events:**
```logql
{job="tapo_home"} | json | source="plug_tapo_p115_aircon"
```

**Power Spike Detection:**
```logql
{job="tapo_home"} | json | category="energy_alert" | details_power > 500
```

---

## 7. Grafana Dashboard JSON

**Import this dashboard for instant visualization:**

```json
{
  "dashboard": {
    "title": "Sandra's Smart Home - Stroheckgasse",
    "panels": [
      {
        "title": "Device Health",
        "type": "gauge",
        "targets": [{
          "expr": "(sum(up{job='tapo_home'}) / count(up{job='tapo_home'})) * 100"
        }]
      },
      {
        "title": "Alert Timeline",
        "type": "logs",
        "targets": [{
          "expr": "{job=\"tapo_home\"} | json | severity!=\"info\""
        }]
      },
      {
        "title": "Power Consumption",
        "type": "graph",
        "targets": [{
          "expr": "tapo_p115_power_watts"
        }]
      }
    ]
  }
}
```

---

## 8. Alert Rules (Prometheus)

**Create alert rules for critical conditions:**

**alerts.yml:**
```yaml
groups:
  - name: tapo_home_alerts
    interval: 30s
    rules:
      # Critical device offline
      - alert: DeviceOffline
        expr: tapo_unacknowledged_alarms > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Device(s) offline in smart home"
          description: "{{ $value }} unacknowledged alarm(s)"
      
      # High CO2
      - alert: HighCO2
        expr: tapo_netatmo_co2_ppm > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CO2 level high"
          description: "CO2 is {{ $value }} ppm (threshold: 1000 ppm)"
      
      # High Power Usage
      - alert: PowerSpike
        expr: tapo_p115_power_watts > 800
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High power consumption"
          description: "Power usage is {{ $value }}W"
```

---

## 9. Current Metrics Available

### Message Metrics
- `tapo_messages_total{severity="info|warning|alarm"}` - Total messages by severity
- `tapo_unacknowledged_alarms` - Current unacknowledged alarms
- `tapo_messages_last_hour` - Messages in last hour

### Device Metrics (Future)
- `tapo_device_online{device_id, type}` - Device online status (1/0)
- `tapo_p115_power_watts{device_id}` - Real-time power consumption
- `tapo_netatmo_temperature_celsius{module}` - Temperature by module
- `tapo_netatmo_co2_ppm{module}` - CO2 levels
- `tapo_hue_lights_online` - Philips Hue light count

---

## 10. Quick Start - Full Stack

### Step 1: Start Tapo Dashboard
```powershell
cd D:\Dev\repos\tapo-camera-mcp
.\start_dashboard.ps1
```

**Verify**: http://localhost:7777

### Step 2: Start Monitoring Stack
```powershell
cd D:\Dev\repos\tapo-camera-mcp\deploy\monitoring
docker compose up -d
```

**Verify**:
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100/ready
- Grafana: http://localhost:3000 (admin/admin)

### Step 3: Configure Grafana

1. Login to Grafana (admin/admin)
2. Add Prometheus datasource (http://prometheus:9090)
3. Add Loki datasource (http://loki:3100)
4. Import dashboard JSON (above)
5. Start monitoring!

### Step 4: Test Alerting

**Simulate device failure:**
```powershell
# Disconnect Tapo plug (simulate)
# Or unplug network cable from camera

# Check alerts
Start-Process "http://localhost:7777/alerts"

# Query in Grafana
# Loki: {job="tapo_home"} | json | severity="alarm"
```

---

## 11. Structured Log Examples

**INFO (Device Connected):**
```json
{
  "timestamp": "2025-12-04T21:00:00Z",
  "level": "INFO",
  "category": "device_connection",
  "source": "plug_tapo_p115_kitchen",
  "message": "Kitchen Zojirushi Reconnected: PLUG device reconnected successfully",
  "details": {
    "device_type": "plug",
    "device_name": "Kitchen Zojirushi"
  },
  "labels": {
    "app": "tapo_camera_mcp",
    "severity": "info",
    "category": "device_connection",
    "source": "plug_tapo_p115_kitchen"
  }
}
```

**WARNING (First Failure):**
```json
{
  "timestamp": "2025-12-04T21:05:00Z",
  "level": "WARNING",
  "category": "device_connection",
  "source": "camera_kitchen_cam",
  "message": "kitchen_cam Offline: CAMERA device connection lost: timeout",
  "details": {
    "device_type": "camera",
    "device_name": "kitchen_cam",
    "error": "timeout"
  },
  "labels": {
    "app": "tapo_camera_mcp",
    "severity": "warning",
    "category": "device_connection"
  }
}
```

**ALARM (Critical):**
```json
{
  "timestamp": "2025-12-04T21:08:00Z",
  "level": "ERROR",
  "category": "device_connection",
  "source": "camera_kitchen_cam",
  "message": "kitchen_cam CRITICAL: CAMERA device offline for 3 checks (180s). Check device and network.",
  "details": {
    "device_type": "camera",
    "device_name": "kitchen_cam",
    "error_count": 3,
    "duration_seconds": 180
  },
  "labels": {
    "app": "tapo_camera_mcp",
    "severity": "alarm",
    "category": "device_connection"
  }
}
```

---

## 12. Grafana Alert Notifications

**Configure notifications to:**
- Email
- Slack
- Discord
- Telegram
- SMS (via Twilio)
- Push notifications

**Example Slack notification:**
```yaml
# Grafana contact points
contact_points:
  - name: slack_alerts
    type: slack
    settings:
      url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      text: |
        🚨 Alert: {{ .CommonLabels.alertname }}
        Severity: {{ .CommonLabels.severity }}
        Message: {{ .CommonAnnotations.description }}
```

---

## Summary

**Your smart home dashboard now has:**

✅ **Real-time monitoring** via Prometheus  
✅ **Structured logging** via Loki  
✅ **Visual dashboards** via Grafana  
✅ **Alert escalation** (info → warning → alarm)  
✅ **Auto-recovery** (supervisor reconnects)  
✅ **Demo-proof** (no silent failures!)  

**Monitoring Stack Integration:**
- Prometheus scrapes metrics every 30s
- Promtail ships logs to Loki
- Grafana visualizes both
- Alerts notify you immediately

**No more "shazbat!"** 🎉


