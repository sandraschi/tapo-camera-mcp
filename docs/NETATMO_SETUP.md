# Netatmo Weather Station Integration (Preparation)

## Overview
Adds a configurable Netatmo integration with graceful fallback to simulated data until credentials are provided. When enabled, the weather API and `/metrics` can source real readings.

## Configuration
Add to your `config.yaml` (example):

```yaml
weather:
  integrations:
    netatmo:
      enabled: true
      client_id: "<your_client_id>"
      client_secret: "<your_client_secret>"
      username: "<your_netatmo_email>"
      password: "<your_netatmo_password>"
      home_id: "<optional_home_id>"
```

Notes:
- If `enabled: true` but credentials are missing/invalid, the system falls back to simulated data and logs a warning.
- When disabled, the weather API continues to serve simulated data for UI/dev.

## Endpoints
- `GET /api/weather/stations` — lists stations (real or simulated)
- `GET /api/weather/stations/{station_id}/data?module_type=indoor|outdoor|all` — current readings
- Additional endpoints (historical, health) remain available with simulated outputs until extended.

## Metrics
- `/metrics` already publishes Netatmo-style series. Once enabled, these can be backed by real readings.

## Install Dependency (optional, when wiring real client)
When you're ready for live queries:

```powershell
pip install pyatmo
```

The client wrapper is scaffolded at `src\tapo_camera_mcp\integrations\netatmo_client.py` and will switch to real calls when credentials are present and the library is installed.


