# Tapo Camera Setup Status

**Last Updated**: November 21, 2025

## Kitchen Camera (192.168.0.164)

### Status: ⚠️ Configured but Auth Issues
- [x] Power cycled (lockout cleared)
- [x] Set up in Tapo app
- [x] Camera Account created (local credentials)
- [x] Config file updated with credentials
  - Username: `sandraschi`
  - Password: `Sec1000kitchen`
- [ ] API connection tested (authentication failing)

### Current Configuration
```yaml
tapo_kitchen:
  type: tapo
  params:
    host: 192.168.0.164
    username: "sandraschi"
    password: "Sec1000kitchen"
    port: 443
    verify_ssl: true
```

### Next Action
1. **Verify credentials** in Tapo app (Camera Account settings)
2. **Test connection**: `python scripts/test_tapo_connection.py`
3. **Check third-party compatibility** enabled in camera settings
4. **Verify network connectivity** (ping 192.168.0.164)

---

## Living Room Camera (192.168.0.206)

### Status: ⚠️ Configured but Auth Issues
- [x] Power cycled (if needed)
- [x] Set up in Tapo app
- [x] Camera Account created (local credentials)
- [x] Static IP enabled (192.168.0.206)
- [x] Config file updated with credentials
  - Username: `sandraschi`
  - Password: `Sec1000living`
- [ ] API connection tested (authentication failing)

### Current Configuration
```yaml
tapo_living_room:
  type: tapo
  params:
    host: 192.168.0.206
    username: "sandraschi"
    password: "Sec1000living"
    port: 443
    verify_ssl: true
```

### Next Action
1. **Verify credentials** in Tapo app (Camera Account settings)
2. **Test connection**: `python scripts/test_tapo_connection.py`
3. **Check third-party compatibility** enabled globally
4. **Verify network connectivity** (ping 192.168.0.206)

---

## Energy Management (Tapo P115 Smart Plugs)

### Status: ✅ Working

#### Aircon Plug (192.168.0.17)
- [x] Configured and working
- [x] Location: Living Room
- [x] Read-only: false (controllable)

#### Kitchen Zojirushi (192.168.0.137)
- [x] Configured and working
- [x] Location: Kitchen
- [x] Read-only: false (controllable)

#### Server Plug (192.168.0.38)
- [x] Configured and working
- [x] Location: Server Room
- [x] Read-only: true (monitoring only)

---

## Important Reminders

- **No default credentials** - C200 cameras don't have admin/admin
- **Camera Account needed** - Set in: Tapo app → Camera → Advanced → Camera Account
- **Separate from cloud** - Camera Account ≠ your email/password
- **Third-party compatibility** - Must be enabled in camera settings
- **Static IP recommended** - Prevents connection issues from IP changes

### Troubleshooting Steps
1. Verify Camera Account credentials in Tapo app
2. Check "Third-Party Compatibility" is enabled
3. Test network connectivity (ping camera IP)
4. Verify SSL certificate (port 443)
5. Check for rate limiting (wait 5 minutes between attempts)

See `scripts/tapo_setup_checklist.md` for detailed step-by-step instructions.

