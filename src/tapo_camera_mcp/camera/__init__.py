"""Camera module imports."""

import logging

logger = logging.getLogger(__name__)

from .petcube import PetcubeCamera

# Import all camera implementations to ensure they register with the factory
from .tapo import TapoCamera

# Import RingCamera with error handling
try:
    # Apply patch before importing ring module
    try:
        import patch_ring_doorbell

        patch_ring_doorbell.patch_ring_doorbell()
    except Exception as e:
        logger.warning(f"Failed to apply ring_doorbell patch: {e}")

    from .ring import RingCamera

    RING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Failed to import RingCamera: {e}")
    RING_AVAILABLE = False

from .webcam import WebCamera

__all__ = ["TapoCamera", "PetcubeCamera", "WebCamera"]

# Only add RingCamera to __all__ if it's available
if RING_AVAILABLE:
    __all__.append("RingCamera")
