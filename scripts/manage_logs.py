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
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import log_manager directly to avoid MCP package dependencies
import importlib.util
log_manager_spec = importlib.util.spec_from_file_location(
    "log_manager",
    src_path / "tapo_camera_mcp" / "utils" / "log_manager.py"
)
log_manager_module = importlib.util.module_from_spec(log_manager_spec)
log_manager_spec.loader.exec_module(log_manager_module)

# Import the classes and functions we need
LogManager = log_manager_module.LogManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
LogConfig = log_manager_module.LogConfig
sanitize_logs_now = log_manager_module.sanitize_logs_now
get_log_stats = log_manager_module.get_log_stats

def print_stats():
    """Print log statistics"""
    logger.info("STATS: Log Statistics")
    logger.info("=" * 50)

    try:
        stats = get_log_stats()

        if stats.get("enabled") is False:
            logger.error("ERROR: Log management is disabled")
            return

        if "error" in stats:
            logger.error(f"ERROR: Error getting stats: {stats['error']}")
            return

        logger.info(f"DIR: Directory: {stats.get('directory', 'Unknown')}")
        logger.info(f"FILES: Total Files: {stats.get('total_files', 0)}")
        logger.info(f"SIZE: Total Size: {stats.get('total_size_mb', 0):.2f} MB")
        logger.info("")

        if stats.get('oldest_file'):
            logger.info(f"DATE: Oldest File: {stats['oldest_file']}")
        if stats.get('newest_file'):
            logger.info(f"NEW: Newest File: {stats['newest_file']}")
        logger.info("")

        file_types = stats.get('files_by_type', {})
        logger.info("TYPES: File Types:")
        logger.info(f"  • Active Logs: {file_types.get('active_logs', 0)}")
        logger.info(f"  • Rotated Logs: {file_types.get('rotated_logs', 0)}")
        logger.info(f"  • Compressed Logs: {file_types.get('compressed_logs', 0)}")

    except Exception as e:
        logger.error(f"ERROR: Failed to get log statistics: {e}")

def rotate_log(filename):
    """Rotate a specific log file"""
    logger.info(f"ROTATE: Rotating log file: {filename}")

    try:
        log_manager = LogManager()
        success = log_manager.rotate_log(filename, force=True)

        if success:
            logger.info(f"SUCCESS: Successfully rotated {filename}")
        else:
            logger.warning(f"WARNING: Rotation completed with warnings or no action needed for {filename}")

    except Exception as e:
        logger.error(f"ERROR: Failed to rotate log file: {e}")

def compress_logs():
    """Compress old log files"""
    logger.info("COMPRESS: Compressing old log files...")

    try:
        log_manager = LogManager()
        compressed = log_manager.compress_old_logs()

        logger.info(f"SUCCESS: Compressed {compressed} log files")

    except Exception as e:
        logger.error(f"ERROR: Failed to compress logs: {e}")

def cleanup_logs():
    """Clean up old log files"""
    logger.info("CLEANUP: Cleaning up old log files...")

    try:
        log_manager = LogManager()
        deleted = log_manager.cleanup_old_logs()

        logger.info(f"SUCCESS: Cleaned up {deleted} old log files")

    except Exception as e:
        logger.error(f"ERROR: Failed to cleanup logs: {e}")

def sanitize_logs():
    """Run full log sanitization"""
    logger.info("SANITIZE: Running full log sanitization...")

    try:
        results = sanitize_logs_now()

        logger.info("SUCCESS: Log sanitization completed:")
        logger.info(f"  • Rotated: {results.get('rotated', 0)} files")
        logger.info(f"  • Compressed: {results.get('compressed', 0)} files")
        logger.info(f"  • Deleted: {results.get('deleted', 0)} files")

    except Exception as e:
        logger.error(f"ERROR: Failed to sanitize logs: {e}")

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
            print("ERROR: Please specify a log file to rotate")
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
        print(f"ERROR: Unknown command: {command}")
        print()
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()