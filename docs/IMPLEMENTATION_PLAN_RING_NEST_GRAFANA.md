# Implementation Plan: Energy, Environment, Ring, Nest + Grafana

## 1) Objectives
- Local dashboard (port 7777): Working charts for Energy (P115) and Environment (Netatmo).
- Prometheus metrics: Single `/metrics` endpoint exposing energy, environment, and security integrations.
- Grafana dashboards: Energy, Environment, and Security Integrations with alerts (CO2 + power spikes).
- Security integrations: Initial Ring and Nest Protect status, device counts, and health metrics (incrementally replace stubs with real data).

## 2) Deliverables
- Code
  - `/metrics` exposes series:
    - Energy (P115): `tapo_p115_power_watts`, `tapo_p115_voltage_volts`, `tapo_p115_current_amps`, `tapo_p115_daily_energy_kwh`, `tapo_p115_power_state`.
    - Environment (Netatmo): `netatmo_temperature_celsius`, `netatmo_humidity_percent`, `netatmo_co2_ppm`, `netatmo_pressure_mbar`.
    - Security Integrations: `ring_integration_enabled`, `ring_devices_total`, `nest_protect_integration_enabled`, `nest_protect_devices_total`.
  - FastAPI endpoints:
    - `GET /api/security/ring/status` → summary, devices, health (incremental).
    - `GET /api/security/nest/status` → summary, devices, health (incremental).
- Config
  - `deploy/prometheus/prometheus.yaml` scrapes `http://localhost:7777/metrics` every 30s.
  - `config.yaml` energy devices include `readonly: true|false` per plug.
- Dashboards (Grafana provisioning)
  - Energy: use `grafana/provisioning/dashboards/sensor-overview.json` (timeseries queries to `tapo_p115_*`).
  - Environment: `grafana/provisioning/dashboards/environment-overview.json` (Netatmo series).
  - Security: `grafana/provisioning/dashboards/security-overview.json` (Ring/Nest enabled + counts).
- Alerts
  - Energy power spike: `grafana/provisioning/alerting/p115-power-spike-alerts.yaml` (500W/800W).
  - CO2: show warning ≥ 800 ppm, danger ≥ 1000 ppm (visual and optional Grafana rule later).

## 3) Prerequisites
- Python deps installed (`tapo`, FastAPI, etc.).
- Prometheus and Grafana reachable.
- At least one P115 host reachable (config: `energy.tapo_p115.devices`).
- For Netatmo: use simulated weather API now; wire real Netatmo after credentials are provided.
- For Ring/Nest: start with stubs; later switch to real libs/servers or internal MCP integrations.

## 4) Implementation Steps (Actionable)

### A. Prometheus & Metrics Endpoint
1. Ensure `deploy/prometheus/prometheus.yaml` contains a single consolidated config scraping `localhost:7777/metrics` (30s).
2. In `src/tapo_camera_mcp/web/server.py` add to `/metrics`:
   - P115 metrics via `tapo_plug_manager` (already present).
   - Netatmo metrics via `api.weather` helpers (present; uses simulated data if no real station is connected).
   - Ring/Nest integration flags and device counts (initially placeholders; to be replaced by live data in section C).
3. Verify curl:
   - `curl http://localhost:7777/metrics | Select-String tapo_p115_`
   - `curl http://localhost:7777/metrics | Select-String netatmo_`
   - `curl http://localhost:7777/metrics | Select-String ring_|nest_`

### B. Local Dashboard (Port 7777)
1. Energy page `src/tapo_camera_mcp/web/templates/energy.html`
   - Chart.js pulls from `/api/sensors/tapo-p115` and `/api/sensors/tapo-p115/{device_id}/history?hours=N`.
   - Time ranges: 24h/7d/30d; thresholds >500W (spike), >800W (surge).
   - Read-only devices: UI reflects `readonly` and disables toggle; backend returns 403 on toggle.
2. Environment page `src/tapo_camera_mcp/web/templates/weather.html`
   - Chart.js for temperature/humidity/pressure/CO2 with 24h/7d/30d.
   - CO2 thresholds: 800/1000 ppm; visual warning + browser notification (if allowed).

### C. Security Integrations
1. Add new router `src/tapo_camera_mcp/web/api/security.py`:
   - `GET /api/security/ring/status` → `{ enabled: bool, devices_total: int, devices: [], health: { ok: bool, msg } }`
   - `GET /api/security/nest/status` → same shape.
   - For now: read `SecuritySettings.integrations` from config to set `enabled`; return `devices_total = 0` and simple health.
2. Wire `/metrics` to use these values instead of placeholders:
   - `ring_integration_enabled{}` = 1 when enabled, else 0
   - `ring_devices_total{} = <count>`
   - `nest_protect_integration_enabled{}` = 1 when enabled, else 0
   - `nest_protect_devices_total{} = <count>`
3. Future (when real Ring/Nest available):
   - Replace stubs with actual client code (or MCP adapters) to fetch device lists and health.
   - Add series for per-device status, battery, signal, etc.

### D. Grafana Dashboards & Alerts
1. Environment Dashboard `grafana/provisioning/dashboards/environment-overview.json`
   - Panels query: `netatmo_temperature_celsius`, `netatmo_humidity_percent`, `netatmo_co2_ppm`, `netatmo_pressure_mbar`.
2. Security Integrations Dashboard `grafana/provisioning/dashboards/security-overview.json`
   - Panels query: `ring_integration_enabled`, `nest_protect_integration_enabled`, `ring_devices_total`, `nest_protect_devices_total`.
3. Energy Dashboard `grafana/provisioning/dashboards/sensor-overview.json`
   - Confirm timeseries panel queries `tapo_p115_power_watts` and cost/energy panels match actual series names (`tapo_p115_daily_energy_kwh`, `tapo_p115_daily_cost_usd` if used).
4. Alerts
   - Power spike rules file: `grafana/provisioning/alerting/p115-power-spike-alerts.yaml` (already created).
   - CO2 alert: add Grafana rule with danger at 1000 ppm; optional warning at 800 ppm (future step).

### E. Configuration & Safety
1. Energy (`config.yaml` → `energy.tapo_p115.devices`):
   - For each device: `host`, `device_id`, `name`, `location`, `readonly: true|false`.
   - The server plug MUST have `readonly: true`.
2. Security settings (`config/models.py` → `SecuritySettings.integrations`):
   - `nest_protect.enabled: bool`, `ring_mcp.enabled: bool`.
3. CORS & GZip already configured; keep as-is.

### F. Testing & Validation
1. Local dashboard:
   - `/energy` shows real devices and timeseries (requires at least one P115 online).
   - `/weather` shows environment charts and CO2 thresholds.
2. Metrics:
   - Check `/metrics` includes all listed series.
3. Prometheus:
   - Load `deploy/prometheus/prometheus.yaml`; validate target UP and series present.
4. Grafana:
   - Import dashboards; verify charts populate.
5. Read-only enforcement:
   - POST `/api/sensors/tapo-p115/{device_id}/toggle` on readonly device returns 403.

## 5) Timeline
- Day 1: Metrics, Prometheus, local dashboards verified end-to-end.
- Day 2: Grafana dashboards verified; Ring/Nest endpoints + metrics (stub → real once creds/integration ready).

## 6) Acceptance Criteria
- Charts visible at `/energy` and `/weather` with real data streams.
- `/metrics` includes energy, environment, and security series.
- Grafana dashboards render all panels without errors; alerts fire on power spikes.
- Read-only plug protection enforced in UI and API.

## 7) Follow-ups (Post-MVP)
- Replace Ring/Nest stubs with real integrations; add per-device series and panels.
- Add CO2 Grafana alerts with 800/1000 ppm thresholds.
- Persist environment history (optional TSDB/db) for longer horizons.
- Add authentication and RBAC to local dashboard.


