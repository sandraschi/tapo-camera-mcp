"""Camera module imports."""

import logging

from .petcube import PetcubeCamera
from .tapo import TapoCamera
from .webcam import WebCamera

logger = logging.getLogger(__name__)

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

__all__ = ["PetcubeCamera", "TapoCamera", "WebCamera"]

# Only add RingCamera to __all__ if it's available
if RING_AVAILABLE:
    __all__.append("RingCamera")
