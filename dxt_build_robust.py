#!/usr/bin/env python3
"""
Robust DXT build script with proper error handling and dependency installation
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any

# Package information
PACKAGE_NAME = "tapo_camera_mcp"
VERSION = "0.1.0"
DIST_DIR = Path("dist")
DIST_DIR.mkdir(exist_ok=True)

def validate_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Validate the DXT manifest file."""
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        required_fields = ["name", "version", "display_name", "description", "server"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field in manifest: {field}")
        
        return manifest
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest: {e}")

def install_dependencies_robust(lib_dir: Path, requirements_file: Path):
    """Install dependencies with robust error handling."""
    print(f"📦 Installing dependencies to {lib_dir}")
    
    # Ensure lib directory exists
    lib_dir.mkdir(exist_ok=True)
    
    if not requirements_file.exists():
        print(f"⚠️ Requirements file {requirements_file} not found, skipping")
        return True
    
    # Read requirements
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"📋 Dependencies to install: {requirements}")
    
    # Method 1: Try installing all at once
    print(f"\n🚀 Method 1: Installing all dependencies at once...")
    cmd_all = [
        sys.executable, "-m", "pip", "install",
        "--target", str(lib_dir),
        "--upgrade"
    ] + requirements
    
    print(f"Command: {' '.join(cmd_all)}")
    result = subprocess.run(cmd_all, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ All dependencies installed successfully!")
        print(f"Output: {result.stdout}")
        return True
    
    print(f"❌ Batch installation failed:")
    print(f"Return code: {result.returncode}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    
    # Method 2: Try installing one by one
    print(f"\n🔄 Method 2: Installing dependencies one by one...")
    failed_deps = []
    
    for req in requirements:
        print(f"\n   Installing {req}...")
        cmd_single = [
            sys.executable, "-m", "pip", "install",
            "--target", str(lib_dir),
            "--upgrade",
            req
        ]
        
        result = subprocess.run(cmd_single, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ {req} installed successfully")
        else:
            print(f"   ❌ {req} failed to install")
            print(f"      Return code: {result.returncode}")
            print(f"      stderr: {result.stderr}")
            failed_deps.append(req)
    
    if failed_deps:
        print(f"\n💥 Failed to install dependencies: {failed_deps}")
        
        # Method 3: Try with --no-deps for problematic packages
        print(f"\n🔧 Method 3: Trying with --no-deps for failed packages...")
        for req in failed_deps:
            print(f"\n   Installing {req} with --no-deps...")
            cmd_nodeps = [
                sys.executable, "-m", "pip", "install",
                "--target", str(lib_dir),
                "--no-deps",
                req
            ]
            
            result = subprocess.run(cmd_nodeps, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {req} installed with --no-deps")
            else:
                print(f"   ❌ {req} still failed with --no-deps")
                print(f"      stderr: {result.stderr}")
        
        return False
    
    print("✅ All dependencies installed successfully (one by one)!")
    return True

def create_main_entry_point(temp_dir: Path):
    """Create main.py entry point for the DXT."""
    main_py_content = '''#!/usr/bin/env python3
"""
Main entry point for Tapo Camera MCP server (DXT version).
This file provides compatibility with Claude Desktop DXT extension execution.
"""

import sys
import os

# Add src and lib directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
lib_dir = os.path.join(current_dir, 'lib')

# Add directories to Python path (lib first for bundled dependencies)
sys.path.insert(0, lib_dir)
sys.path.insert(0, src_dir)

def main():
    """Main entry point."""
    try:
        from tapo_camera_mcp.server_v2 import main as server_main
        print("🚀 Starting Tapo Camera MCP server (DXT)...", file=sys.stderr)
        return server_main()
    except ImportError as e:
        print(f"❌ Import error: {e}", file=sys.stderr)
        print("📁 Python path:", file=sys.stderr)
        for i, p in enumerate(sys.path[:10]):
            print(f"   {i}: {p}", file=sys.stderr)
        
        print("📦 Checking lib directory contents:", file=sys.stderr)
        lib_path = os.path.join(os.path.dirname(__file__), 'lib')
        if os.path.exists(lib_path):
            contents = os.listdir(lib_path)
            print(f"   Lib contents: {contents[:10]}", file=sys.stderr)
        else:
            print("   ❌ Lib directory does not exist!", file=sys.stderr)
        
        # Try to import individual components for debugging
        try:
            import fastmcp
            print("✅ fastmcp imported successfully", file=sys.stderr)
        except ImportError as fe:
            print(f"❌ fastmcp import failed: {fe}", file=sys.stderr)
            
        try:
            import pytapo
            print("✅ pytapo imported successfully", file=sys.stderr)
        except ImportError as pe:
            print(f"❌ pytapo import failed: {pe}", file=sys.stderr)
            
        return 1
    except Exception as e:
        print(f"❌ Error starting server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    main_py_path = temp_dir / "main.py"
    main_py_path.write_text(main_py_content, encoding='utf-8')
    print(f"✅ Created main.py entry point")

def create_manifest_json(temp_dir: Path, dxt_manifest: Dict[str, Any]):
    """Create the simplified manifest.json for Claude Desktop."""
    manifest = {
        "name": dxt_manifest["name"],
        "version": dxt_manifest["version"],
        "description": dxt_manifest["description"],
        "dxt_version": "1.0.0",
        "author": dxt_manifest.get("author", "Unknown"),
        "server": {
            "type": "python",
            "entry_point": "main.py",
            "mcp_config": {
                "command": "python",
                "args": ["main.py", "--direct"],
                "env": {"PYTHONUNBUFFERED": "1"}
            }
        }
    }
    
    manifest_path = temp_dir / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Created manifest.json")

def copy_source_files(temp_dir: Path):
    """Copy source files to the temporary directory."""
    src_dest = temp_dir / "src"
    src_dest.mkdir(exist_ok=True)
    
    src_dir = Path("src") / PACKAGE_NAME
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    
    package_dest = src_dest / PACKAGE_NAME
    shutil.copytree(src_dir, package_dest, dirs_exist_ok=True)
    print(f"✅ Copied source files from {src_dir}")

def create_dxt_package():
    """Create the DXT package with bundled dependencies."""
    # Validate the manifest first
    manifest = validate_manifest(Path("dxt_manifest.json"))
    version = manifest.get("version", VERSION)
    
    # Create temporary directory for packaging
    with tempfile.TemporaryDirectory(prefix="dxt_build_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"📁 Using temporary directory: {temp_dir}")
        
        try:
            # Install dependencies to lib directory
            lib_dir = temp_dir / "lib"
            requirements_file = Path("requirements-core.txt")
            
            success = install_dependencies_robust(lib_dir, requirements_file)
            if not success:
                print("⚠️ Some dependencies failed to install, but continuing...")
            
            # Copy source files
            copy_source_files(temp_dir)
            
            # Create main.py entry point
            create_main_entry_point(temp_dir)
            
            # Create Claude Desktop manifest.json
            create_manifest_json(temp_dir, manifest)
            
            # Copy original DXT manifest
            shutil.copy2("dxt_manifest.json", temp_dir)
            
            # Copy other important files
            for file in ["README.md", "README_DXT.md"]:
                if Path(file).exists():
                    shutil.copy2(file, temp_dir)
            
            # Create the zip archive
            output_file = DIST_DIR / f"{PACKAGE_NAME}-{version}.dxt"
            if output_file.exists():
                output_file.unlink()
            
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            # Get file size
            file_size = output_file.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ Successfully created DXT package: {output_file} ({file_size:.2f} MB)")
            
            # Show lib directory contents
            lib_contents = list((temp_dir / "lib").iterdir()) if (temp_dir / "lib").exists() else []
            print(f"📦 Bundled {len(lib_contents)} dependencies in lib/")
            
            return True
        
        except Exception as e:
            print(f"❌ Error creating DXT package: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🔧 Building Tapo-Camera-MCP DXT package with robust dependency installation...")
    if create_dxt_package():
        print("🎯 DXT build completed successfully!")
        sys.exit(0)
    else:
        print("❌ DXT build failed!")
        sys.exit(1)
