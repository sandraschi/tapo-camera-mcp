"""
Setup script for Tapo Camera MCP.
"""

from setuptools import setup, find_packages

# Read the README for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="tapo-camera-mcp",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="FastMCP 2.10 server for controlling TP-Link Tapo cameras",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tapo-camera-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "tapo_camera_mcp": [
            "config/*.toml",
            "templates/*",
            "static/*",
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tapo-camera-mcp=tapo_camera_mcp.cli:main",
        ],
        "fastmcp.plugins": [
            "tapo_camera = tapo_camera_mcp.plugin:register_plugin",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Video :: Capture",
        "Framework :: FastMCP",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/tapo-camera-mcp/issues",
        "Source": "https://github.com/yourusername/tapo-camera-mcp",
    },
)
