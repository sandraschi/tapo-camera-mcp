"""
Storage utilities for recordings and events.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventStore:
    """Simple event storage for camera events."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize event store."""
        if storage_dir is None:
            storage_dir = Path("~/.local/share/tapo-camera-mcp/events").expanduser()
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.storage_dir / "events.jsonl"

    def add_event(
        self,
        event_type: str,
        camera_id: Optional[str] = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add an event to storage."""
        event = {
            "id": f"{datetime.now().timestamp():.6f}",
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "camera_id": camera_id,
            "message": message,
            "metadata": metadata or {},
        }

        try:
            with open(self.events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            logger.exception("Error writing event")

        return event

    def get_events(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        camera_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get events from storage."""
        events = []

        if not self.events_file.exists():
            return events

        try:
            with open(self.events_file, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)

                        # Filter by type
                        if event_type and event.get("type") != event_type:
                            continue

                        # Filter by camera
                        if camera_id and event.get("camera_id") != camera_id:
                            continue

                        # Filter by time
                        if since:
                            event_time = datetime.fromisoformat(event.get("timestamp", ""))
                            if event_time < since:
                                continue

                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            logger.exception("Error reading events")

        # Sort by timestamp descending
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Limit results
        return events[:limit]

    def clear_old_events(self, days: int = 30) -> int:
        """Clear events older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        events = self.get_events(limit=10000)
        filtered_events = [
            e for e in events if datetime.fromisoformat(e.get("timestamp", "")) > cutoff
        ]

        if len(filtered_events) == len(events):
            return 0

        try:
            with open(self.events_file, "w", encoding="utf-8") as f:
                for event in filtered_events:
                    f.write(json.dumps(event) + "\n")
            return len(events) - len(filtered_events)
        except Exception:
            logger.exception("Error clearing old events")
            return 0


class RecordingStore:
    """Simple recording storage for camera recordings."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize recording store."""
        if storage_dir is None:
            storage_dir = Path("~/.local/share/tapo-camera-mcp/recordings").expanduser()
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.recordings_file = self.storage_dir / "recordings.jsonl"
        self.videos_dir = self.storage_dir / "videos"
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def add_recording(
        self,
        camera_id: str,
        video_path: Optional[Path] = None,
        duration_seconds: float = 0.0,
        size_bytes: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a recording to storage."""
        recording = {
            "id": f"{datetime.now().timestamp():.6f}",
            "timestamp": datetime.now().isoformat(),
            "camera_id": camera_id,
            "video_path": str(video_path) if video_path else None,
            "duration_seconds": duration_seconds,
            "size_bytes": size_bytes,
            "metadata": metadata or {},
        }

        try:
            with open(self.recordings_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(recording) + "\n")
        except Exception:
            logger.exception("Error writing recording")

        return recording

    def get_recordings(
        self,
        limit: int = 100,
        camera_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get recordings from storage."""
        recordings = []

        if not self.recordings_file.exists():
            return recordings

        try:
            with open(self.recordings_file, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        recording = json.loads(line)

                        # Filter by camera
                        if camera_id and recording.get("camera_id") != camera_id:
                            continue

                        # Filter by time
                        if since:
                            recording_time = datetime.fromisoformat(recording.get("timestamp", ""))
                            if recording_time < since:
                                continue

                        recordings.append(recording)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            logger.exception("Error reading recordings")

        # Sort by timestamp descending
        recordings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Limit results
        return recordings[:limit]

    def delete_recording(self, recording_id: str) -> bool:
        """Delete a recording and its file."""
        recordings = self.get_recordings(limit=10000)
        recording = next((r for r in recordings if r.get("id") == recording_id), None)

        if not recording:
            return False

        # Delete video file if it exists
        video_path = recording.get("video_path")
        if video_path:
            try:
                Path(video_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning("Error deleting video file: %s", e)

        # Remove from storage
        filtered_recordings = [r for r in recordings if r.get("id") != recording_id]
        try:
            with open(self.recordings_file, "w", encoding="utf-8") as f:
                for rec in filtered_recordings:
                    f.write(json.dumps(rec) + "\n")
            return True
        except Exception:
            logger.exception("Error deleting recording")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        recordings = self.get_recordings(limit=10000)
        total_size = sum(r.get("size_bytes", 0) for r in recordings)
        total_count = len(recordings)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = len(
            [r for r in recordings if datetime.fromisoformat(r.get("timestamp", "")) >= today]
        )

        return {
            "total_recordings": total_count,
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "today_recordings": today_count,
        }
