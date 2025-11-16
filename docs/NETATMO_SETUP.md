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
      redirect_uri: "https://localhost/callback"
      refresh_token: "<your_refresh_token>"
      # Legacy fallback (optional; not recommended):
      # username: "<your_netatmo_email>"
      # password: "<your_netatmo_password>"
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

## Install Dependency
When you're ready for live queries:

```powershell
pip install pyatmo
```

The client wrapper is scaffolded at `src\tapo_camera_mcp\integrations\netatmo_client.py` and will switch to real calls when credentials are present and the library is installed.

## OAuth Flow (Recommended)
1. Build an authorization URL and open it:
   ```powershell
   python .\\scripts\\netatmo_oauth_helper.py auth-url <CLIENT_ID> https://localhost/callback
   ```
2. After login/consent, copy the `code` from the redirect URL.
3. Exchange code for tokens:
   ```powershell
   python .\\scripts\\netatmo_oauth_helper.py exchange <CLIENT_ID> <CLIENT_SECRET> <CODE> https://localhost/callback
   ```
   Save `refresh_token` into `config.yaml` under `weather.integrations.netatmo.refresh_token`.
4. To periodically refresh access tokens (if needed for direct API calls):
   ```powershell
   python .\\scripts\\netatmo_oauth_helper.py refresh <CLIENT_ID> <CLIENT_SECRET> <REFRESH_TOKEN>
   ```

## Quick Verification
- With `enabled: true` and a valid `refresh_token`, run:
  ```powershell
  $response = Invoke-WebRequest http://localhost:7777/metrics -UseBasicParsing
  if ($response.Content -match "netatmo_") {
      "netatmo metrics present"
  } else {
      "no netatmo metrics found"
  }
  ```
  You should see: `netatmo_temperature_celsius`, `netatmo_humidity_percent`, `netatmo_co2_ppm`, `netatmo_pressure_mbar` populated from your station.


