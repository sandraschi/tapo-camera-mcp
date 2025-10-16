"""
Check Pydantic version and compatibility.
"""

import pydantic
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def check_pydantic():
    """Check Pydantic version and compatibility."""
    try:
        logger.info(f"Pydantic version: {pydantic.__version__}")

        # Check if we can create a simple model
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            value: int = 42

        # Test model creation
        test = TestModel(name="test")
        logger.info(f"Test model created: {test}")

        return True
    except Exception as e:
        logger.error(f"Error checking Pydantic: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    if check_pydantic():
        logger.info("Pydantic check completed successfully!")
        sys.exit(0)
    else:
        logger.error("Pydantic check failed!")
        sys.exit(1)
