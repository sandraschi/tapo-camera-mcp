import sys
import os

# Add the src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from tapo_camera_mcp.server_v2 import main
    print("SUCCESS: Module imported successfully")
    print("Running main function...")
    main()
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
