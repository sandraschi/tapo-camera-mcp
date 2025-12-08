# Port Conflict Handling

## What Happens When Port 7777 is Already in Use?

### Current Behavior (v1.8.0+)

When you try to start the dashboard and port 7777 is already in use (e.g., by a Docker container), the system now provides **clear error messages and solutions**.

### Detection Layers

1. **PowerShell Script Check** (`start_dashboard.ps1`):
   - Checks port availability **before** starting Python
   - Shows which process is using the port (PID, name, path)
   - Provides 3 solutions:
     - Stop the conflicting process
     - Stop Docker container
     - Use a different port

2. **Python Server Check** (`server.py`):
   - Double-checks port availability before binding
   - Catches `OSError` with clear error messages
   - Logs helpful troubleshooting steps

### Error Messages

#### PowerShell Script Output:
```
❌ PORT CONFLICT DETECTED!
   Port 7777 is already in use by:
   • Process: python (PID: 12345)
   • Path: C:\Program Files\Python\python.exe

💡 Solutions:
   1. Stop the conflicting process:
      Stop-Process -Id 12345 -Force

   2. Stop Docker container (if using Docker):
      docker ps | findstr tapo
      docker stop <container-id>

   3. Use a different port:
      python -m tapo_camera_mcp.web --host 0.0.0.0 --port 7778
```

#### Python Server Output:
```
❌ PORT CONFLICT: Port 7777 is already in use!
   Another process (possibly Docker container) is using port 7777.
   Solutions:
   1. Stop the conflicting process:
      PowerShell: Get-NetTCPConnection -LocalPort 7777 | Select-Object OwningProcess
      Then: Stop-Process -Id <PID> -Force
   2. Stop Docker container:
      docker ps | findstr tapo
      docker stop <container-id>
   3. Use a different port:
      python -m tapo_camera_mcp.web --port 7778
```

### Common Scenarios

#### Scenario 1: Docker Container Running
```powershell
# Check what's using port 7777
Get-NetTCPConnection -LocalPort 7777

# Stop Docker container
docker ps
docker stop tapo-camera-mcp-container
```

#### Scenario 2: Previous Dashboard Instance
```powershell
# Find Python processes
Get-Process python | Where-Object {$_.Path -like "*tapo-camera-mcp*"}

# Stop specific process
Stop-Process -Id <PID> -Force
```

#### Scenario 3: Use Different Port
```powershell
# Start on port 7778 instead
python -m tapo_camera_mcp.web --host 0.0.0.0 --port 7778
```

### Helper Function

A `find_available_port()` function is available in `server.py` for automatic port detection (future enhancement).

### Best Practices

1. **Always check before starting:**
   ```powershell
   Get-NetTCPConnection -LocalPort 7777
   ```

2. **Stop Docker containers first:**
   ```powershell
   docker ps | findstr tapo
   docker stop <container-id>
   ```

3. **Use the startup script:**
   ```powershell
   .\start_dashboard.ps1
   ```
   It automatically checks for conflicts!

### Future Enhancements

- [ ] Auto-detect and use next available port
- [ ] Graceful shutdown of conflicting processes
- [ ] Port conflict notification in health dashboard
- [ ] Docker container auto-detection and stopping

---

**Last Updated:** 2025-12-02  
**Version:** 1.8.0

