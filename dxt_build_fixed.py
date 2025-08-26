"""DXT build script for Tapo-Camera-MCP with dependency bundling.

This script handles the packaging of Tapo-Camera-MCP into a DXT package with all dependencies included.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

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
        
        # Check required fields
        required_fields = ["name", "version", "display_name", "description", "server"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field in manifest: {field}")
        
        # Ensure server configuration is valid
        server = manifest.get("server", {})
        if "command" not in server or not isinstance(server["command"], list):
            raise ValueError("Invalid or missing 'command' in server configuration")
        
        return manifest
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest: {e}")

def install_dependencies(lib_dir: Path, requirements_file: Path):
    """Install dependencies to the lib directory."""
    print(f"📦 Installing dependencies to {lib_dir}")
    
    # Ensure lib directory exists
    lib_dir.mkdir(exist_ok=True)
    
    # Install from requirements.txt
    if requirements_file.exists():
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--target", str(lib_dir),
            "-r", str(requirements_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to install dependencies:")
            print(f"Command: {' '.join(cmd)}")
            print(f"Return code: {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            
            # Try to install one by one for debugging
            print("\n🔍 Trying to install dependencies individually...")
            with open(requirements_file, 'r') as f:
                deps = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
            
            for dep in deps:
                print(f"\nTesting {dep}...")
                test_cmd = [sys.executable, "-m", "pip", "show", dep.split('>=')[0].split('==')[0]]
                test_result = subprocess.run(test_cmd, capture_output=True, text=True)
                if test_result.returncode == 0:
                    print(f"✅ {dep.split('>=')[0]} is available")
                else:
                    print(f"❌ {dep.split('>=')[0]} is NOT available")
                    # Try to find what versions are available
                    search_cmd = [sys.executable, "-m", "pip", "index", "versions", dep.split('>=')[0]]
                    search_result = subprocess.run(search_cmd, capture_output=True, text=True)
                    if search_result.stdout:
                        print(f"Available versions: {search_result.stdout}")
            
            raise RuntimeError("Dependency installation failed")
        
        print("✅ Dependencies installed successfully")
    else:
        print("⚠️ No requirements.txt found, skipping dependency installation")

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
        for p in sys.path[:5]:
            print(f"   {p}", file=sys.stderr)
        
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
    print(f"✅ Created main.py entry point at {main_py_path}")

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
    
    print(f"✅ Created manifest.json at {manifest_path}")

def copy_source_files(temp_dir: Path):
    """Copy source files to the temporary directory."""
    # Create src directory structure
    src_dest = temp_dir / "src"
    src_dest.mkdir(exist_ok=True)
    
    # Copy the main package
    src_dir = Path("src") / PACKAGE_NAME
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    
    package_dest = src_dest / PACKAGE_NAME
    shutil.copytree(src_dir, package_dest, dirs_exist_ok=True)
    print(f"✅ Copied source files from {src_dir} to {package_dest}")

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
            install_dependencies(lib_dir, requirements_file)
            
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
            
            # List contents for verification
            print("\n📋 DXT package contents:")
            with zipfile.ZipFile(output_file, 'r') as zipf:
                for name in sorted(zipf.namelist()[:20]):  # Show first 20 files
                    print(f"  {name}")
                if len(zipf.namelist()) > 20:
                    print(f"  ... and {len(zipf.namelist()) - 20} more files")
            
            return True
        
        except Exception as e:
            print(f"❌ Error creating DXT package: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🔧 Building Tapo-Camera-MCP DXT package with dependencies...")
    if create_dxt_package():
        print("🎯 DXT build completed successfully!")
        sys.exit(0)
    else:
        print("❌ DXT build failed!")
        sys.exit(1)
