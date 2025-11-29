"""Patch script to fix ring_doorbell imports."""

import importlib


def patch_ring_doorbell():
    """Patch the ring_doorbell package to fix imports."""
    try:
        # First, try to import the websockets package directly
        import websockets

        print(f"Websockets package found at: {websockets.__file__}")

        # Try to import the specific module that's failing
        try:
            from websockets.asyncio.client import connect

            print("Successfully imported websockets.asyncio.client")
        except ImportError as e:
            print(f"Error importing websockets.asyncio.client: {e}")
            # If the direct import fails, try to patch the module
            websockets.asyncio = importlib.import_module("websockets.asyncio")
            print("Patched websockets.asyncio")

        # Now try to import the ring_doorbell package
        try:
            from ring_doorbell.webrtcstream import RingWebRtcStream

            print("Successfully imported RingWebRtcStream")
            return True
        except ImportError as e:
            print(f"Error importing RingWebRtcStream: {e}")
            return False

    except ImportError as e:
        print(f"Error importing websockets: {e}")
        return False


if __name__ == "__main__":
    print("Attempting to patch ring_doorbell...")
    if patch_ring_doorbell():
        print("Successfully patched ring_doorbell!")
    else:
        print("Failed to patch ring_doorbell.")
