"""Test RTSP stream connectivity with OpenCV."""

import cv2
import time

def test_rtsp_stream(rtsp_url: str, timeout: int = 10):
    """Test RTSP stream connectivity."""
    print(f"Testing RTSP stream: {rtsp_url[:60]}...")

    # Try to open the stream
    cap = cv2.VideoCapture(rtsp_url)

    # Configure for low latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 30)

    start_time = time.time()
    while time.time() - start_time < timeout:
        if cap.isOpened():
            # Try to read a frame
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ SUCCESS: Stream opened! Resolution: {width}x{height}")
                cap.release()
                return True
            else:
                print("Stream opened but cannot read frames...")
        else:
            print("Waiting for stream to open...")

        time.sleep(0.5)

    print("❌ FAILED: Could not open RTSP stream within timeout")
    cap.release()
    return False

if __name__ == "__main__":
    # Test the kitchen camera RTSP URL
    rtsp_url = "rtsp://sandraschi:Sec1000kitchen@192.168.0.164:554/stream1"
    success = test_rtsp_stream(rtsp_url, timeout=15)

    if not success:
        print("\nTrying alternative RTSP URLs...")

        # Try without authentication
        rtsp_url_no_auth = "rtsp://192.168.0.164:554/stream1"
        print(f"Trying without auth: {rtsp_url_no_auth}")
        success = test_rtsp_stream(rtsp_url_no_auth, timeout=5)

        if not success:
            # Try different paths
            alternative_urls = [
                "rtsp://192.168.0.164:554/live",
                "rtsp://192.168.0.164:554/stream",
                "rtsp://192.168.0.164:554/Streaming/Channels/1",
                "rtsp://192.168.0.164:554/onvif1",
            ]

            for url in alternative_urls:
                print(f"Trying alternative: {url}")
                if test_rtsp_stream(url, timeout=5):
                    success = True
                    break

    if success:
        print("\n🎉 RTSP stream test PASSED")
    else:
        print("\n❌ RTSP stream test FAILED - Camera may not support RTSP or authentication issue")
