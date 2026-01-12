#!/usr/bin/env python3
"""
Log Management CLI Tool for Tapo Camera MCP

This script provides command-line access to log management functions:
- View log statistics
- Manually rotate logs
- Compress old logs
- Clean up old log files
- Run full sanitization

Usage:
    python manage_logs.py stats
    python manage_logs.py rotate tapo_mcp.log
    python manage_logs.py compress
    python manage_logs.py cleanup
    python manage_logs.py sanitize
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tapo_camera_mcp.utils.log_manager import LogManager, LogConfig, sanitize_logs_now, get_log_stats

def print_stats():
    """Print log statistics"""
    print("STATS: Log Statistics")
    print("=" * 50)

    try:
        stats = get_log_stats()

        if stats.get("enabled") is False:
            print("ERROR: Log management is disabled")
            return

        if "error" in stats:
            print(f"ERROR: Error getting stats: {stats['error']}")
            return

        print(f"DIR: Directory: {stats.get('directory', 'Unknown')}")
        print(f"FILES: Total Files: {stats.get('total_files', 0)}")
        print(f"SIZE: Total Size: {stats.get('total_size_mb', 0):.2f} MB")
        print()

        if stats.get('oldest_file'):
            print(f"DATE: Oldest File: {stats['oldest_file']}")
        if stats.get('newest_file'):
            print(f"NEW: Newest File: {stats['newest_file']}")
        print()

        file_types = stats.get('files_by_type', {})
        print("TYPES: File Types:")
        print(f"  • Active Logs: {file_types.get('active_logs', 0)}")
        print(f"  • Rotated Logs: {file_types.get('rotated_logs', 0)}")
        print(f"  • Compressed Logs: {file_types.get('compressed_logs', 0)}")

    except Exception as e:
        print(f"ERROR: Failed to get log statistics: {e}")

def rotate_log(filename):
    """Rotate a specific log file"""
    print(f"ROTATE: Rotating log file: {filename}")

    try:
        log_manager = LogManager()
        success = log_manager.rotate_log(filename, force=True)

        if success:
            print(f"SUCCESS: Successfully rotated {filename}")
        else:
            print(f"WARNING: Rotation completed with warnings or no action needed for {filename}")

    except Exception as e:
        print(f"ERROR: Failed to rotate log file: {e}")

def compress_logs():
    """Compress old log files"""
    print("COMPRESS: Compressing old log files...")

    try:
        log_manager = LogManager()
        compressed = log_manager.compress_old_logs()

        print(f"SUCCESS: Compressed {compressed} log files")

    except Exception as e:
        print(f"ERROR: Failed to compress logs: {e}")

def cleanup_logs():
    """Clean up old log files"""
    print("CLEANUP: Cleaning up old log files...")

    try:
        log_manager = LogManager()
        deleted = log_manager.cleanup_old_logs()

        print(f"SUCCESS: Cleaned up {deleted} old log files")

    except Exception as e:
        print(f"ERROR: Failed to cleanup logs: {e}")

def sanitize_logs():
    """Run full log sanitization"""
    print("SANITIZE: Running full log sanitization...")

    try:
        results = sanitize_logs_now()

        print("SUCCESS: Log sanitization completed:")
        print(f"  • Rotated: {results.get('rotated', 0)} files")
        print(f"  • Compressed: {results.get('compressed', 0)} files")
        print(f"  • Deleted: {results.get('deleted', 0)} files")

    except Exception as e:
        print(f"ERROR: Failed to sanitize logs: {e}")

def show_help():
    """Show help information"""
    print("Log Management CLI Tool for Tapo Camera MCP")
    print("=" * 50)
    print()
    print("Commands:")
    print("  stats           Show log file statistics")
    print("  rotate <file>   Rotate a specific log file")
    print("  compress        Compress old log files")
    print("  cleanup         Delete very old log files")
    print("  sanitize        Run full sanitization (rotate + compress + cleanup)")
    print("  help            Show this help message")
    print()
    print("Examples:")
    print("  python manage_logs.py stats")
    print("  python manage_logs.py rotate tapo_mcp.log")
    print("  python manage_logs.py sanitize")
    print()
    print("Configuration:")
    print("Add these settings to your config.yaml:")
    print("  log_management_enabled: true")
    print("  log_max_size_mb: 10.0")
    print("  log_max_files: 5")
    print("  log_compress_after_days: 1")
    print("  log_delete_after_days: 30")

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "stats":
        print_stats()
    elif command == "rotate":
        if len(sys.argv) < 3:
            print("❌ Error: Please specify a log file to rotate")
            print("Usage: python manage_logs.py rotate <filename>")
            sys.exit(1)
        rotate_log(sys.argv[2])
    elif command == "compress":
        compress_logs()
    elif command == "cleanup":
        cleanup_logs()
    elif command == "sanitize":
        sanitize_logs()
    elif command == "help" or command == "--help" or command == "-h":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        print()
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()