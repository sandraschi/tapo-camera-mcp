"""
Direct import test for Tapo Camera MCP tool modules.
"""
import sys
import os
from pathlib import Path

def add_src_to_path():
    """Add the src directory to the Python path."""
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    print(f"Added to path: {src_dir}")

def test_import(module_name):
    """Test importing a module and print the result."""
    try:
        module = __import__(module_name, fromlist=['*'])
        print(f"✅ Successfully imported: {module_name}")
        
        # Print available attributes if any
        if hasattr(module, '__all__'):
            print(f"  Exports: {', '.join(module.__all__)}")
            
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"⚠️ Error importing {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to test imports."""
    add_src_to_path()
    
    # List of modules to test
    modules_to_test = [
        "tapo_camera_mcp.tools.camera",
        "tapo_camera_mcp.tools.system",
        "tapo_camera_mcp.tools.ptz",
        "tapo_camera_mcp.tools.media",
        "tapo_camera_mcp.tools.grafana"
    ]
    
    # Test each module
    results = {}
    for module in modules_to_test:
        print(f"\n--- Testing {module} ---")
        results[module] = test_import(module)
    
    # Print summary
    print("\n=== Import Test Summary ===")
    for module, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {module}")
    
    # Return non-zero exit code if any import failed
    if not all(results.values()):
        print("\nSome imports failed. Check the error messages above for details.")
        sys.exit(1)
    else:
        print("\nAll imports successful!")

if __name__ == "__main__":
    main()
