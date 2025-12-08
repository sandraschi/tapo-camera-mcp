# Monitoring Stack Connection Guide

**How the Tapo Camera MCP Dashboard connects to Prometheus, Loki, and Grafana running in Docker**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│         Tapo Camera MCP Dashboard (Host Machine)            │
│                    http://localhost:7777                    │
│                                                             │
│  • Exposes metrics endpoint: /metrics                       │
│  • Exposes messaging metrics: /api/messages/prometheus      │
│  • Writes structured JSON logs to: tapo_mcp.log            │
└─────────────────────────────────────────────────────────────┘
         │                          │                  │
         │ HTTP GET                 │ File Read        │ HTTP GET
         │ (Prometheus scrapes)     │ (Promtail reads) │ (Grafana queries)
         ▼                          ▼                  ▼
┌─────────────────┐      ┌─────────────────┐   ┌─────────────────┐
│   Prometheus    │      │    Promtail     │   │    Grafana      │
│  (Docker)       │      │  (Docker)       │   │   (Docker)      │
│  :9090          │      │  Reads logs     │   │   :3000         │
│                 │      │  → Sends to     │   │                 │
│  Scrapes:       │      │  → Loki         │   │  Queries:       │
│  • /metrics     │      │                 │   │  • Prometheus   │
│  • /api/messages│      │                 │   │  • Loki         │
│    /prometheus  │      │                 │   │                 │
└─────────────────┘      └─────────────────┘   └─────────────────┘
         │                          │                  │
         │                          ▼                  │
         │                  ┌─────────────────┐        │
         │                  │      Loki       │        │
         │                  │    (Docker)     │◄───────┘
         │                  │     :3100       │
         │                  │                 │
         │                  │  Stores logs    │
         └──────────────────┴─────────────────┘
```

---

## Connection Methods

### 1. Prometheus → Dashboard (Metrics Scraping)

**How it works:**
- Prometheus (in Docker) **pulls** metrics from the dashboard
- Dashboard **exposes** metrics endpoints (no push needed)
- Prometheus scrapes every 30 seconds (configurable)

**Connection Details:**

**From Docker to Host:**
```yaml
# deploy/prometheus/prometheus.yaml
scrape_configs:
  - job_name: tapo-camera-mcp
    metrics_path: /metrics  # OR /api/messages/prometheus
    static_configs:
      - targets:
          # Windows/Mac Docker Desktop:
          - host.docker.internal:7777
          
          # OR if dashboard is in Docker too:
          - myhomecontrol-app:7777
          
          # OR if on same Docker network:
          - 172.17.0.1:7777  # Docker bridge gateway
```

**Available Metrics Endpoints:**

1. **`/metrics`** - General system metrics
   - P115 power consumption
   - Device status
   - System health

2. **`/api/messages/prometheus`** - Messaging/alerting metrics
   - `tapo_messages_total{severity="info|warning|alarm"}`
   - `tapo_unacknowledged_alarms`
   - `tapo_messages_last_hour`

**Test Connection:**
```powershell
# From host machine
curl http://localhost:7777/metrics
curl http://localhost:7777/api/messages/prometheus

# From Docker container
docker exec monitoring-prometheus wget -qO- http://host.docker.internal:7777/metrics
```

---

### 2. Promtail → Dashboard Logs → Loki (Log Shipping)

**How it works:**
- Dashboard writes structured JSON logs to `tapo_mcp.log`
- Promtail (in Docker) **reads** log files from host
- Promtail **pushes** logs to Loki via HTTP API

**Connection Details:**

**Log File Location:**
```
D:\Dev\repos\tapo-camera-mcp\tapo_mcp.log
```

**Promtail Configuration:**
```yaml
# deploy/promtail/promtail-config.yaml
clients:
  - url: http://loki:3100/loki/api/v1/push  # Loki in Docker
    tenant_id: home-security

scrape_configs:
  - job_name: tapo-camera-mcp
    static_configs:
      - targets:
          - localhost
        labels:
          job: tapo-camera-mcp
          app: tapo_camera_mcp
        __path__: /var/log/tapo-camera-mcp/*.log  # Mounted volume
```

**Docker Volume Mount:**
```yaml
# docker-compose.yml
services:
  promtail:
    volumes:
      # Mount host log directory into container
      - D:\Dev\repos\tapo-camera-mcp:/var/log/tapo-camera-mcp:ro
      # OR use named volume if logs are in Docker volume
      - tapo_logs:/var/log/tapo-camera-mcp:ro
```

**Log Format (Structured JSON):**
```json
{
  "timestamp": "2025-12-04T21:00:00Z",
  "level": "WARNING",
  "category": "device_connection",
  "source": "camera_kitchen_cam",
  "message": "Camera offline",
  "details": {
    "device_type": "camera",
    "error": "timeout"
  },
  "labels": {
    "app": "tapo_camera_mcp",
    "severity": "warning"
  }
}
```

---

### 3. Grafana → Prometheus + Loki (Querying)

**How it works:**
- Grafana (in Docker) **queries** Prometheus for metrics
- Grafana **queries** Loki for logs
- Both connections are **HTTP GET** requests

**Connection Details:**

**Prometheus Datasource:**
```yaml
# deploy/monitoring/config/grafana/provisioning/datasources/datasource.yml
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090  # Docker service name
    isDefault: true
```

**Loki Datasource:**
```yaml
datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100  # Docker service name
```

**Network Configuration:**
```yaml
# deploy/monitoring/docker-compose.monitoring.yml
services:
  prometheus:
    networks:
      - monitoring  # Shared network
      
  loki:
    networks:
      - monitoring  # Shared network
      
  grafana:
    networks:
      - monitoring  # Shared network
      # Can also connect to external network if needed
      - myhomecontrol  # External network

networks:
  monitoring:
    driver: bridge
  myhomecontrol:
    external: true  # Connect to existing network
```

---

## Current Configuration Issues

### Issue 1: Prometheus Can't Reach Host Dashboard

**Problem:**
```yaml
# Current config uses localhost (won't work from Docker)
targets:
  - localhost:7777  # ❌ Prometheus in Docker can't reach this
```

**Solution:**
```yaml
# Use host.docker.internal (Windows/Mac Docker Desktop)
targets:
  - host.docker.internal:7777  # ✅ Works from Docker

# OR use Docker network if dashboard is also containerized
targets:
  - myhomecontrol-app:7777  # ✅ If in same Docker network
```

### Issue 2: Promtail Can't Read Host Log Files

**Problem:**
```yaml
# Current config assumes logs are in container
__path__: /var/log/tapo-camera-mcp/*.log  # ❌ Not mounted
```

**Solution:**
```yaml
# Mount host log directory
volumes:
  - D:\Dev\repos\tapo-camera-mcp:/var/log/tapo-camera-mcp:ro

# OR if using Docker volume
volumes:
  - tapo_logs:/var/log/tapo-camera-mcp:ro
```

### Issue 3: Metrics Path Mismatch

**Problem:**
- Prometheus config uses `/metrics`
- Documentation mentions `/api/messages/prometheus`
- Both exist but serve different data

**Solution:**
- Use `/metrics` for general system metrics
- Use `/api/messages/prometheus` for alerting metrics
- Or configure both as separate jobs

---

## Fixed Configuration Files

### Fixed Prometheus Config

```yaml
# deploy/prometheus/prometheus.yaml
global:
  scrape_interval: 30s
  scrape_timeout: 10s
  evaluation_interval: 30s

scrape_configs:
  # General system metrics
  - job_name: tapo-camera-mcp-system
    metrics_path: /metrics
    static_configs:
      - targets:
          - host.docker.internal:7777  # ✅ Fixed: Use host.docker.internal
        labels:
          service: tapo-camera-mcp
          role: control-plane
          location: stroheckgasse
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: tapo-camera-mcp-host

  # Messaging/alerting metrics
  - job_name: tapo-camera-mcp-messages
    metrics_path: /api/messages/prometheus
    static_configs:
      - targets:
          - host.docker.internal:7777  # ✅ Fixed
        labels:
          service: tapo-camera-mcp
          role: alerting
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: tapo-camera-mcp-messages
```

### Fixed Promtail Config

```yaml
# deploy/promtail/promtail-config.yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push
    tenant_id: home-security

scrape_configs:
  - job_name: tapo-camera-mcp
    static_configs:
      - targets:
          - localhost
        labels:
          job: tapo-camera-mcp
          app: tapo_camera_mcp
          location: stroheckgasse
        __path__: /var/log/tapo-camera-mcp/*.log  # ✅ Mounted volume
    
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

### Fixed Docker Compose (Monitoring Stack)

```yaml
# deploy/monitoring/docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: monitoring-prometheus
    ports:
      - "9095:9090"  # Avoid conflict with other Prometheus
    volumes:
      - ../prometheus/prometheus.yaml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  loki:
    image: grafana/loki:latest
    container_name: monitoring-loki
    ports:
      - "3100:3100"
    volumes:
      - ../loki/loki-config.yaml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:latest
    container_name: monitoring-promtail
    volumes:
      - ../promtail/promtail-config.yaml:/etc/promtail/config.yml:ro
      # ✅ FIXED: Mount host log directory
      - D:\Dev\repos\tapo-camera-mcp:/var/log/tapo-camera-mcp:ro
      - promtail_positions:/tmp
    command: -config.file=/etc/promtail/config.yml
    depends_on:
      - loki
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: monitoring-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
      - loki
    networks:
      - monitoring

volumes:
  prometheus_data:
  loki_data:
  grafana_data:
  promtail_positions:

networks:
  monitoring:
    driver: bridge
```

---

## Testing the Connection

### Test 1: Prometheus Can Scrape Metrics

```powershell
# Start monitoring stack
cd D:\Dev\repos\tapo-camera-mcp\deploy\monitoring
docker compose up -d

# Check Prometheus targets
Start-Process "http://localhost:9095/targets"

# Should see:
# ✅ tapo-camera-mcp-system (UP)
# ✅ tapo-camera-mcp-messages (UP)

# Query metrics in Prometheus UI
# PromQL: tapo_messages_total
# PromQL: tapo_unacknowledged_alarms
```

### Test 2: Promtail Can Read Logs

```powershell
# Check Promtail logs
docker logs monitoring-promtail

# Should see:
# "msg"="Starting Promtail" ...
# "msg"="Starting target manager" ...

# Check if logs are being shipped
# In Grafana, query Loki:
# {job="tapo-camera-mcp"}
```

### Test 3: Grafana Can Query Both

```powershell
# Access Grafana
Start-Process "http://localhost:3000"
# Login: admin/admin

# Test Prometheus datasource
# Explore → Prometheus → Query: tapo_messages_total

# Test Loki datasource
# Explore → Loki → Query: {job="tapo-camera-mcp"}
```

---

## Network Connectivity Summary

| Component | Location | Connection Method | Endpoint |
|-----------|----------|-------------------|----------|
| **Dashboard** | Host (Windows) | Exposes HTTP | `localhost:7777` |
| **Prometheus** | Docker | Scrapes via HTTP | `host.docker.internal:7777/metrics` |
| **Promtail** | Docker | Reads files | `/var/log/tapo-camera-mcp/*.log` (mounted) |
| **Loki** | Docker | Receives via HTTP | `http://loki:3100/loki/api/v1/push` |
| **Grafana** | Docker | Queries via HTTP | `http://prometheus:9090` + `http://loki:3100` |

---

## Key Points

1. **Dashboard is PULL-based**: Prometheus pulls metrics, doesn't push
2. **Logs are FILE-based**: Promtail reads log files, not HTTP
3. **Docker networking**: Use `host.docker.internal` to reach host from Docker
4. **Volume mounts**: Mount host log directory so Promtail can read it
5. **Service discovery**: Docker services use service names (e.g., `prometheus:9090`)

---

## Troubleshooting

### Prometheus shows "DOWN" for dashboard

**Check:**
```powershell
# Can Prometheus reach the host?
docker exec monitoring-prometheus wget -qO- http://host.docker.internal:7777/metrics

# Is dashboard running?
Get-NetTCPConnection -LocalPort 7777

# Firewall blocking?
# Windows Firewall may block Docker → Host connections
```

**Fix:**
- Use `host.docker.internal:7777` (not `localhost:7777`)
- Ensure dashboard is running on host
- Check Windows Firewall rules

### Promtail shows "no targets"

**Check:**
```powershell
# Is log file mounted?
docker exec monitoring-promtail ls -la /var/log/tapo-camera-mcp/

# Does log file exist on host?
Test-Path "D:\Dev\repos\tapo-camera-mcp\tapo_mcp.log"
```

**Fix:**
- Verify volume mount in docker-compose.yml
- Check log file path matches `__path__` in promtail config
- Ensure log file has read permissions

### Grafana can't query Prometheus/Loki

**Check:**
```powershell
# Are services on same network?
docker network inspect monitoring_monitoring

# Can Grafana reach Prometheus?
docker exec monitoring-grafana wget -qO- http://prometheus:9090/-/healthy

# Can Grafana reach Loki?
docker exec monitoring-grafana wget -qO- http://loki:3100/ready
```

**Fix:**
- Ensure all services use `monitoring` network
- Check datasource URLs use service names (not localhost)
- Verify services are running: `docker ps`

---

**Last Updated:** 2025-12-02  
**Status:** ✅ Configuration fixed and tested

