# Log Management System

Automated log rotation, compression, and cleanup for Tapo Camera MCP to prevent log files from growing too large.

## Features

- **Automatic Rotation**: Rotate logs when they exceed size limits
- **Compression**: Compress old log files to save disk space
- **Cleanup**: Delete very old compressed logs
- **Web Interface**: Manage logs through the web UI
- **CLI Tools**: Command-line log management
- **Configurable**: Customize behavior through config.yaml

## Configuration

Add these settings to your `config.yaml`:

```yaml
# Log Management Settings
log_management_enabled: true
log_max_size_mb: 10.0        # Rotate when log exceeds 10MB
log_max_files: 5             # Keep max 5 rotated files
log_compress_after_days: 1   # Compress after 1 day
log_delete_after_days: 30    # Delete after 30 days
```

## Web Interface

Access the log management interface at: `http://localhost:7777/logs`

### Features:
- **Statistics Dashboard**: View log file sizes and counts
- **Quick Actions**: Sanitize all logs with one click
- **Manual Rotation**: Rotate specific log files
- **Real-time Updates**: Live statistics and status

## CLI Tools

Use the command-line tool for manual log management:

```bash
# Show log statistics
python scripts/manage_logs.py stats

# Rotate a specific log file
python scripts/manage_logs.py rotate tapo_mcp.log

# Compress old log files
python scripts/manage_logs.py compress

# Clean up very old files
python scripts/manage_logs.py cleanup

# Run full sanitization
python scripts/manage_logs.py sanitize
```

## Automatic Operation

The system runs automatically:

1. **Hourly Sanitization**: Runs every hour during server operation
2. **Size-based Rotation**: Rotates files when they exceed `log_max_size_mb`
3. **Age-based Compression**: Compresses files older than `log_compress_after_days`
4. **Age-based Deletion**: Deletes compressed files older than `log_delete_after_days`

## API Endpoints

### GET `/api/logs/stats`
Get log file statistics and configuration.

**Response:**
```json
{
  "enabled": true,
  "directory": "/app/logs",
  "total_files": 12,
  "total_size_mb": 45.67,
  "oldest_file": "2024-01-01T00:00:00",
  "newest_file": "2024-12-29T12:00:00",
  "files_by_type": {
    "active_logs": 3,
    "rotated_logs": 7,
    "compressed_logs": 2
  }
}
```

### POST `/api/logs/sanitize`
Trigger manual log sanitization (rotation, compression, cleanup).

**Response:**
```json
{
  "message": "Log sanitization started in background",
  "status": "running"
}
```

### POST `/api/logs/rotate/{filename}`
Rotate a specific log file.

**Response:**
```json
{
  "message": "Log rotation started for tapo_mcp.log",
  "status": "running"
}
```

## File Naming Convention

- **Active Logs**: `tapo_mcp.log`, `server.log`
- **Rotated Logs**: `tapo_mcp_20241229_120000.log`
- **Compressed Logs**: `tapo_mcp_20241229_120000.log.gz`

## Troubleshooting

### Logs Not Rotating
- Check that `log_management_enabled: true` in config
- Verify file permissions on log directory
- Check server logs for errors

### High Disk Usage
- Increase `log_delete_after_days` to keep logs longer
- Decrease `log_max_size_mb` for more frequent rotation
- Run manual cleanup: `python scripts/manage_logs.py cleanup`

### Web Interface Not Loading
- Ensure server is running with web UI enabled
- Check browser console for JavaScript errors
- Verify API endpoints are accessible

## Performance Impact

- **Memory**: Minimal (~1MB for log manager instance)
- **CPU**: Negligible (compression runs in background)
- **Disk I/O**: Only during rotation/compression operations
- **Network**: None (all operations are local)

## Security Considerations

- Log files may contain sensitive information
- Compressed logs are still readable (not encrypted)
- Consider log encryption for production deployments
- Restrict access to log management interface

## Integration

The log manager integrates with:

- **Web Server**: Automatic startup and periodic tasks
- **Configuration System**: Reads settings from config.yaml
- **Logging System**: Works with Python's logging module
- **File System**: Direct file operations (no external dependencies)

## Development

To extend the log management system:

1. **Add new operations** in `LogManager` class
2. **Create new API endpoints** in `log_management.py`
3. **Add web interface features** in `log_management.html`
4. **Extend CLI commands** in `manage_logs.py`

## Monitoring

Monitor log management effectiveness:

- Check log file sizes regularly
- Monitor disk usage trends
- Review rotation frequency
- Verify compression ratios
- Audit cleanup operations