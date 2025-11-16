"""
Ingestion services for external sensors and smart devices.
"""

from .tapo_p115 import IngestionUnavailableError, TapoP115IngestionService

__all__ = [
    "IngestionUnavailableError",
    "TapoP115IngestionService",
]
