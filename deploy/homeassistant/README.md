# Home Assistant Setup for Nest Protect

Home Assistant is used as a bridge to access Nest Protect devices because Google has blocked direct OAuth access for third-party apps. Home Assistant has a verified Google OAuth application that works.

## Quick Start

### 1. Start Home Assistant

```powershell
cd deploy/homeassistant
docker-compose up -d
```

Wait ~2 minutes for first startup.

### 2. Initial Setup

1. Open http://localhost:8123
2. Create your account (remember credentials!)
3. Set your location (Vienna, Austria)
4. Skip any detected integrations for now

### 3. Add Nest Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**Nest**" (not "Google Nest")
3. Click **Configure**
4. Sign in with your Google account that has Nest devices
5. Authorize Home Assistant to access your Nest account
6. Select your Nest Protect devices

### 4. Create Access Token

1. Click your profile icon (bottom left)
2. Go to **Security** tab
3. Scroll to **Long-Lived Access Tokens**
4. Click **Create Token**
5. Name it "tapo-camera-mcp"
6. **Copy the token immediately** (it won't be shown again!)

### 5. Configure tapo-camera-mcp

Edit `config.yaml`:

```yaml
security:
  integrations:
    homeassistant:
      enabled: true
      url: http://localhost:8123
      access_token: "paste-your-token-here"
      cache_ttl: 30
```

### 6. Restart Server

```powershell
# Stop existing server (Ctrl+C or kill process)
python -m tapo_camera_mcp.web.server
```

Your Nest Protect devices should now appear on the Alarms page!

## Troubleshooting

### "Cannot connect to Home Assistant"
- Check HA is running: `docker ps`
- Check HA logs: `docker logs homeassistant`
- Verify URL in config.yaml

### "No Nest Protect devices found"
- Open HA and check Settings → Devices → Nest
- Make sure you selected the Nest (not Google Nest) integration
- Re-authenticate if needed

### "401 Unauthorized"
- Token may have expired - create a new one
- Make sure you copied the full token

## Docker Commands

```powershell
# Start Home Assistant
docker-compose up -d

# Stop Home Assistant
docker-compose down

# View logs
docker logs -f homeassistant

# Restart
docker-compose restart
```

## Resource Usage

- RAM: ~400-600 MB
- Disk: ~500 MB
- CPU: Minimal (only when polling)

## Why Home Assistant?

Google deprecated the "Works with Nest" API and blocked third-party OAuth apps from accessing Nest accounts. Home Assistant has a special agreement with Google that allows their verified OAuth app to continue working.

We use HA purely as a data bridge - it fetches Nest data via Google's API, and we pull that data from HA's REST API.

