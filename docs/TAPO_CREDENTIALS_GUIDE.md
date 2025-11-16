# Tapo Camera Credentials Guide

## Finding Your Tapo Camera Credentials

After resetting a Tapo camera, the default credentials are typically:

### Default After Reset
- **Username:** `admin`
- **Password:** `admin`

However, **this is not guaranteed** - some cameras may have:
- Different default passwords (like `TPL075526460603` format)
- Password printed on the camera label
- Password in the device manual

### Where to Find Credentials

1. **Camera Label**
   - Check the bottom or back of your camera
   - Look for a sticker with username/password
   - Format might be: `TPL[numbers]` or similar

2. **Tapo App**
   - Open Tapo app → Your Camera
   - Device Settings → Advanced Settings → Local Device Settings
   - Look for "Local User" or "Local Admin Account"
   - This shows the LOCAL username/password (not cloud account)

3. **Device Manual**
   - Check the printed manual or PDF
   - Default credentials should be listed there

4. **After Setup**
   - If you set up the camera through the Tapo app
   - The LOCAL admin password might be different from your cloud account
   - Check: Tapo app → Camera → Advanced → Local Device Settings

### Important: Local vs Cloud Credentials

**Tapo cameras use LOCAL credentials for API access, NOT your cloud account!**

- **Cloud Account:** Used for Tapo app access (email: sandraschipal@hotmail.com)
- **Local Account:** Used for API/local access (usually admin/your-local-password)

These are **separate** - you need to find or set the LOCAL credentials.

### Setting Local Admin Password

If you haven't set one:

1. Open **Tapo app** → Your Camera
2. Go to **Device Settings** → **Advanced Settings**
3. Find **Local Device Settings** or **Local User Management**
4. Enable **Local Admin Account** (if not already enabled)
5. Set a username (usually `admin`) and password
6. **Write this down** - you'll need it for API access!

### Testing Credentials

Use the test script to check if credentials work:

```powershell
python scripts/test_tapo_connection.py
```

Or manually update the script:
```python
ip = "192.168.0.164"  # Your camera IP
username = "admin"  # Try admin first
password = "admin"  # Try admin first, or password from label/manual
```

### Common Issues

1. **"Invalid authentication"**
   - Wrong username/password
   - Using cloud account instead of local account
   - Password changed but not updated in config

2. **"Temporary Suspension"**
   - Too many failed login attempts
   - Wait 30 minutes or power cycle camera

3. **Can't find local settings in app**
   - Some older Tapo cameras use cloud account for local access
   - Try your cloud account email as username
   - Password might be your cloud password (but often different)

### Next Steps

1. **Check camera label** for default credentials
2. **Check Tapo app** for local admin settings
3. **Test with admin/admin** (common default after reset)
4. **If admin/admin doesn't work**, try:
   - Password from camera label (TPL format)
   - Your cloud password (less common)
   - Check device manual

Once you find the correct credentials, update `config.yaml`:

```yaml
tapo_kitchen:
  type: tapo
  params:
    host: 192.168.0.164
    username: "admin"  # Or username from label/app
    password: "YOUR_ACTUAL_PASSWORD"  # From label/manual/app
    port: 443
    verify_ssl: true
```

