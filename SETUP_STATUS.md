# Tapo Camera Setup Status

**Last Updated**: After power cycle

## Kitchen Camera (192.168.0.164)

### Status: ⏳ Setup Required
- [x] Power cycled (lockout cleared)
- [ ] Set up in Tapo app
- [ ] Camera Account created (local credentials)
- [ ] Config file updated with credentials
- [ ] API connection tested

### Next Action
1. **Set up camera in Tapo app** (scan QR code, connect to Wi-Fi)
2. **Create Camera Account**: Tapo app → Camera → Settings → Advanced → Camera Account
3. **Update config.yaml** with Camera Account username/password
4. **Test**: `python scripts/test_tapo_connection.py`

---

## Living Room Camera (192.168.0.206)

### Status: ⏳ Not Started
- [ ] Power cycled (if needed)
- [ ] Set up in Tapo app
- [ ] Camera Account created (local credentials)
- [ ] Config file updated with credentials
- [ ] API connection tested

---

## Important Reminders

- **No default credentials** - C200 cameras don't have admin/admin
- **Must set up in app first** - Can't use API until camera is added in Tapo app
- **Camera Account needed** - Set in: Tapo app → Camera → Advanced → Camera Account
- **Separate from cloud** - Camera Account ≠ your email/password

See `scripts/tapo_setup_checklist.md` for detailed step-by-step instructions.

