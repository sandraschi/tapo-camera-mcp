"""
LLMs.txt Generator for Tapo Camera MCP.

This module implements the LLMs.txt standard (https://llmstxt.org) for LLM-optimized documentation,
providing a structured way to document APIs and tools for large language models.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TypedDict, Union

import pkg_resources


class ToolMetadata(TypedDict, total=False):
    """Metadata structure for API tools."""

    name: str
    description: str
    category: str
    rate_limit: str
    requires_auth: bool
    input_schema: Dict
    output_schema: Dict


class LLMsTxtGenerator:
    """Generator for LLMs.txt standard files.

    This class generates LLM-optimized documentation in the LLMs.txt format,
    providing a structured way to document APIs and tools for consumption by
    large language models.

    Example:
        >>> generator = LLMsTxtGenerator("https://example.com")
        >>> generator.write_files("./docs")
    """

    VERSION = "1.0.0"

    def __init__(self, base_url: str = "https://github.com/yourusername/tapo-camera-mcp"):
        """Initialize the LLMs.txt generator.

        Args:
            base_url: Base URL for documentation links. This should be the base URL
                    where your documentation is hosted.

        Example:
            >>> generator = LLMsTxtGenerator("https://example.com/docs")
        """
        self.base_url = base_url.rstrip("/")
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.version = self._get_version()
        self.tools_metadata: List[ToolMetadata] = []

    def _get_version(self) -> str:
        """Get the current package version.

        Returns:
            str: Package version string
        """
        try:
            return pkg_resources.get_distribution("tapo-camera-mcp").version
        except pkg_resources.DistributionNotFound:
            return self.VERSION

    def generate_navigation(self) -> str:
        """Generate the llms.txt navigation file.

        This file serves as a table of contents and quick reference for the API.
        It's designed to be concise and easily parseable by LLMs.

        Returns:
            str: Formatted llms.txt content

        Example:
            >>> generator = LLMsTxtGenerator("https://example.com")
            >>> print(generator.generate_navigation())
        """
        return f"""# Tapo Camera MCP v{self.version}
> Control and monitor Tapo cameras through the Model Context Protocol (MCP).
> Generated: {self.timestamp}
> Documentation: {self.base_url}
> Version: {self.version}

## API Information
- **Base URL**: {self.base_url}/api
- **Authentication**: Required (API Key or OAuth2)
- **Rate Limit**: 100 requests/minute per API key
- **Data Retention**: 30 days for logs and analytics

## Core Documentation
- [Quick Start]({self.base_url}/docs/quickstart): Get started with Tapo Camera MCP
- [API Reference]({self.base_url}/docs/api): Complete API documentation
- [Tool Reference]({self.base_url}/docs/tools): Available tools and their usage
- [Configuration]({self.base_url}/docs/configuration): Setup and configuration guide
- [Authentication]({self.base_url}/docs/auth): API authentication methods
- [Rate Limits]({self.base_url}/docs/rate-limits): API usage limits and quotas

## Tools
### Camera Control
- [Camera Status]({self.base_url}/docs/tools#camera-status): Get camera status and information
- [Stream Control]({self.base_url}/docs/tools#stream-control): Start/stop video streams
- [Presets]({self.base_url}/docs/tools#presets): Manage camera presets

### PTZ Controls
- [Pan/Tilt]({self.base_url}/docs/tools#pan-tilt): Control camera movement
- [Zoom]({self.base_url}/docs/tools#zoom): Adjust zoom level
- [Presets]({self.base_url}/docs/tools#ptz-presets): Save/recall PTZ positions

### System Management
- [Device Info]({self.base_url}/docs/tools#device-info): Get system information
- [Reboot]({self.base_url}/docs/tools#reboot): Reboot the camera
- [Firmware]({self.base_url}/docs/tools#firmware): Check for updates

### Media Handling
- [Snapshot]({self.base_url}/docs/tools#snapshot): Capture still images
- [Recording]({self.base_url}/docs/tools#recording): Manage video recordings
- [Playback]({self.base_url}/docs/tools#playback): Access recorded media

## Resources
- [GitHub Repository]({self.base_url}): Source code and issue tracker
- [Examples]({self.base_url}/examples): Usage examples and code samples
- [Tapo API](https://www.tapo.com): Official Tapo API documentation
- [Support]({self.base_url}/support): Get help and support
- [Changelog]({self.base_url}/changelog): Version history and changes

## Privacy & Compliance
- [Privacy Policy]({self.base_url}/privacy): Data handling and privacy information
- [Terms of Service]({self.base_url}/terms): Usage terms and conditions
- [Security]({self.base_url}/security): Security best practices

## Full Documentation
For complete documentation including request/response schemas and examples, see [llms-full.txt]({self.base_url}/llms-full.txt)
    """

    def generate_full_documentation(self) -> str:
        """Generate the complete llms-full.txt documentation.

        Returns:
            str: Complete documentation in markdown format
        """
        return f"""# Tapo Camera MCP - Complete Documentation

## Table of Contents
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Tools Reference](#tools-reference)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)

## Getting Started

### Installation
```bash
pip install tapo-camera-mcp
```

### Quick Start
```python
from tapo_camera_mcp import TapoCameraServer

# Initialize the server
server = TapoCameraServer()

# Start the server
server.start()
```

## API Reference

### Base URL
All API endpoints are relative to: {self.base_url}/api/v1

### Authentication
Authentication is required for all API endpoints. Include your API key in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

## Tools Reference

### Camera Control

#### Camera Status
**Description**: Get the current status of the camera.

**Endpoint**: GET /api/v1/camera/status

**Parameters**: None

**Response**:
```json
{{
  "status": "online",
  "model": "Tapo C200",
  "firmware": "1.0.0",
  "uptime": 12345
}}
```

#### Stream Control
**Description**: Start or stop the video stream.

**Endpoint**: POST /api/v1/camera/stream

**Parameters**:
- action (string, required): Either "start" or "stop"
- quality (string, optional): Stream quality ("high", "medium", "low")

**Response**:
```json
{{
  "success": true,
  "stream_url": "rtsp://camera/stream"
}}
```

### PTZ Controls

#### Pan/Tilt
**Description**: Control the camera's pan and tilt.

**Endpoint**: POST /api/v1/ptz/move

**Parameters**:
- pan (number, required): Pan angle in degrees (-180 to 180)
- tilt (number, required): Tilt angle in degrees (-90 to 90)
- speed (number, optional): Movement speed (1-100)

**Response**:
```json
{{
  "success": true,
  "position": {{
    "pan": 0,
    "tilt": 0
  }}
}}
```

## Authentication

### Obtaining an API Key
1. Register your application at {self.base_url}/developers
2. Create a new API key
3. Include the key in the Authorization header

## Rate Limiting
- 100 requests per minute per API key
- Exceeding the limit will result in a 429 status code
- The following headers are included in rate-limited responses:
  - X-RateLimit-Limit: The maximum number of requests allowed
  - X-RateLimit-Remaining: The number of requests remaining
  - X-RateLimit-Reset: Time when the rate limit resets (UTC timestamp)

## Error Handling

### Error Response Format
```json
{{
  "error": {{
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {{}}
  }}
}}
```

### Common Error Codes
- 400 Bad Request: Invalid request parameters
- 401 Unauthorized: Missing or invalid API key
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Resource not found
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Server error

## Support
For support, please contact support@example.com or visit our GitHub repository: {self.base_url}

## License
Apache 2.0 License: {self.base_url}/license
    """

    def write_files(self, output_dir: Union[str, Path]) -> None:
        """Write the LLMs.txt files to the specified directory.

        Args:
            output_dir: Directory where the files will be written.

        Raises:
            OSError: If the directory cannot be created or is not writable.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write the main navigation file
        nav_path = output_path / "llms.txt"
        nav_path.write_text(self.generate_navigation(), encoding="utf-8")

        # Write the full documentation file
        full_docs_path = output_path / "llms-full.txt"
        full_docs_path.write_text(self.generate_full_documentation(), encoding="utf-8")


def generate_llms_txt(output_dir: Union[str, Path], base_url: Optional[str] = None) -> None:
    """Generate LLMs.txt files for the project.

    Args:
        output_dir: Directory to write the files to
        base_url: Base URL for documentation links (default: GitHub repo)
    """
    if base_url is None:
        base_url = "https://github.com/sandraschi/tapo-camera-mcp"

    generator = LLMsTxtGenerator(base_url=base_url)
    generator.write_files(output_dir)


if __name__ == "__main__":
    # Generate documentation in the project root when run directly
    project_root = Path(__file__).parent.parent.parent
    generate_llms_txt(project_root)
