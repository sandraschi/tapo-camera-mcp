# Monitoring Stack Quickstart

## Overview
Spin up Prometheus, Alertmanager, Grafana, Elasticsearch, Logstash, Kibana, and Fluentd for the Tapo Camera MCP.

## Prerequisites
- Docker Desktop installed
- Tapo Camera MCP running locally on port `7777` (default from `config.yaml`)

## Start the stack (PowerShell)

```powershell
# From the repository root
docker compose -f .\deploy\monitoring\docker-compose.monitoring.yml up -d
```

## Services
- Prometheus: `http://localhost:9090`
- Alertmanager: `http://localhost:9093`
- Grafana: `http://localhost:3000` (admin/admin by default; password set in compose)
- Kibana: `http://localhost:5601`
- Elasticsearch: `http://localhost:9200`

## Prometheus scraping
Prometheus is preconfigured to scrape the MCP server metrics at `http://host.docker.internal:7777/metrics`.

Ensure the MCP web server is running and exposes `/metrics`. This repo's `src\tapo_camera_mcp\web\server.py` provides the endpoint.

## Grafana
Grafana is pre-provisioned with a Prometheus datasource and a minimal Tapo P115 dashboard.

Login, then navigate to:
- Dashboards → Manage → `Tapo P115 Overview`

## Stop the stack (PowerShell)
```powershell
docker compose -f .\deploy\monitoring\docker-compose.monitoring.yml down
```

## Notes
- If running MCP on a different host/port, update `deploy\monitoring\config\prometheus.yml` target.
- Windows users: `host.docker.internal` resolves the host from inside containers.


