# FastMCP 2.12+ Development Best Practices

**Austrian Efficiency Guide for Professional MCP Server Development**

This document establishes best practices for building production-quality MCP servers using FastMCP 2.12+, optimized for rapid development with MCP Inspector integration and DXT packaging.

## ⚠️ **Critical FastMCP 2.12+ Framework Rules**

### 🚨 **NEVER USE THESE - FastMCP Doesn't Support**:
- **NO "description" argument** - FastMCP framework doesn't have this parameter
- **NO "parameters" in tool calls** - FastMCP handles this differently internally  
- **Errors are defined in "exceptions"** - use MCPError patterns, not description fields

### ✅ **Correct FastMCP Patterns**:
```python
# ✅ CORRECT: No description parameter
@mcp.tool()
async def example_tool(param: str) -> str:
    """Tool documentation goes in docstring, not description parameter."""
    return f"Processed: {param}"

# ❌ WRONG: Don't do this
@mcp.tool(description="This will cause errors")  # NO! FastMCP doesn't support this
async def wrong_tool(param: str) -> str:
    return f"This won't work: {param}"

# ✅ CORRECT: Error handling
try:
    result = process_data(input_data)
except Exception as e:
    raise MCPError(message=str(e), code="PROCESSING_ERROR")

# ❌ WRONG: Don't use description in errors
raise MCPError(description="Wrong pattern")  # NO! Use message parameter
```

## 🛠️ **PowerShell & Development Environment Rules**

### Core System Paths
- **Repos folder**: `D:\Dev\repos`
- **Python executable**: `C:\Users\sandr\AppData\Local\Programs\Python\Python313\python.exe`
- **Claude Config**: `C:\Users\sandr\AppData\Roaming\Claude\claude_desktop_config.json`

### PowerShell Best Practices - CRITICAL FOR RELIABILITY

#### 1. **ALWAYS Use PowerShell Cmdlets (NEVER external commands)**:
```powershell
# ✅ CORRECT:
New-Item -ItemType Directory -Path "C:\path\folder" -Force
Copy-Item -Path "source.txt" -Destination "dest.txt"
Remove-Item -Path "file.txt" -Force
Get-ChildItem -Path "C:\folder"

# ❌ NEVER USE:
mkdir folder        # Use New-Item instead
copy file.txt       # Use Copy-Item instead  
del file.txt        # Use Remove-Item instead
dir                 # Use Get-ChildItem instead
```

#### 2. **ALWAYS Use File Redirect + Read Back Pattern**:
```powershell
# ✅ BASIC commands:
Command > C:\temp\output.txt; Get-Content C:\temp\output.txt

# ✅ EXTERNAL executables:
Start-Process -FilePath "npm.cmd" -ArgumentList "--version" -Wait -RedirectStandardOutput "C:\temp\npm.txt" -WindowStyle Hidden; Get-Content C:\temp\npm.txt
```

#### 3. **CRITICAL: Folder Tree Creation Rules**:
```powershell
# ✅ CORRECT - Build one folder at a time:
New-Item -ItemType Directory -Path "D:\Dev\repos\project" -Force
New-Item -ItemType Directory -Path "D:\Dev\repos\project\src" -Force
New-Item -ItemType Directory -Path "D:\Dev\repos\project\src\tools" -Force

# ❌ NEVER USE Linux syntax:
mkdir folder && mkdir folder/subfolder  # This will fail on Windows!

# ❌ NEVER USE mkdir command:
mkdir "D:\path\folder"  # Use New-Item instead
```

#### 4. **Reliability Rules**:
- **ALWAYS quote paths with spaces**: `"C:\Program Files\"`
- **TEST paths first**: `Test-Path` before operations
- **SPECIFY encoding**: `Get-Content -Encoding UTF8`
- **ADD error handling**: `-ErrorAction SilentlyContinue`
- **USE unique temp names**: `C:\temp\op_$(Get-Date -Format 'HHmmss').txt`

#### 5. **Development Commands**:
```powershell
# ✅ Use where.exe for finding executables:
where.exe python    # CORRECT
where python        # WRONG - can cause issues

# ✅ Refresh environment variables:
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
```

## 📦 **DXT Packaging - Complete Guide**

### What is DXT?

**DXT (Dynamic eXTension)** is Anthropic's standardized packaging format for Claude Desktop extensions. It enables:
- **MCP Server Distribution**: Package MCP servers as installable extensions
- **Prompt Template Sharing**: Include reusable prompt templates
- **Extension Management**: Install/uninstall through Claude Desktop UI
- **Version Control**: Semantic versioning for extension updates
- **Dependency Management**: Automatic dependency resolution

### Anthropic DXT App

The **Anthropic DXT App** is the official command-line tool for:
- **Validation**: `dxt validate` - Check package structure and metadata
- **Packaging**: `dxt pack` - Create .dxt distribution files
- **NOT FOR**: `dxt init` or `dxt publish` (we handle these manually)

### DXT Installation & Usage in Claude Desktop

#### How DXT Files Are Installed:
1. **User Downloads**: .dxt file from GitHub releases or distribution
2. **Claude Desktop**: Import via "Extensions" → "Install Extension" → Select .dxt file
3. **Automatic Setup**: Claude Desktop extracts and configures the extension
4. **MCP Integration**: Server automatically appears in Claude's MCP configuration

#### Claude Desktop Extensions Directory Structure:
```
C:\Users\sandr\AppData\Roaming\Claude\Claude Extensions\
├── extension-name-v1.0.0\           # Extracted extension folder
│   ├── metadata.json                # Extension metadata
│   ├── mcp-config.json              # MCP server configuration  
│   ├── prompt-templates\             # Prompt templates directory
│   │   ├── templates.json           # Template definitions
│   │   ├── business-analysis.md     # Individual template files
│   │   ├── code-review.md
│   │   └── debug-assistant.md
│   ├── server\                      # MCP server files
│   │   ├── your_mcp_server.exe      # Windows executable
│   │   └── config.yaml              # Server configuration
│   └── docs\                        # Documentation
│       ├── README.md
│       └── user-guide.md
```

### DXT Project Structure for MCP Servers

```
your-mcp-server/                     # Root project directory
├── pyproject.toml                   # ✅ Python project configuration
├── dxt.toml                         # ✅ DXT packaging configuration
├── README.md                        # ✅ Main documentation
├── LICENSE                          # ✅ License file
├── CHANGELOG.md                     # ✅ Version history
├── .gitignore                       # ✅ Git exclusions
│
├── src/                             # ✅ Source code
│   └── your_mcp_server/
│       ├── __init__.py
│       ├── server.py                # Main MCP server
│       └── tools/
│           └── ...
│
├── dxt-package/                     # ✅ DXT packaging files
│   ├── metadata.json               # Extension metadata
│   ├── mcp-config.json             # MCP configuration template
│   ├── prompt-templates/           # Prompt templates
│   │   ├── templates.json          # Template definitions
│   │   ├── business-analysis.md    # Business analysis template
│   │   ├── code-review.md          # Code review template
│   │   ├── debug-assistant.md      # Debug helper template
│   │   └── data-analysis.md        # Data analysis template
│   └── docs/                       # User documentation
│       ├── installation.md
│       └── user-guide.md
│
├── tests/                           # ✅ Test suite
└── build/                           # ✅ Build artifacts (gitignored)
    └── your-mcp-server-v1.0.0.dxt  # Generated DXT package
```

### DXT Configuration Files

#### 1. **dxt.toml** - Main DXT Configuration:
```toml
[package]
name = "your-mcp-server"
version = "1.0.0"
description = "Professional MCP Server with business tools"
author = "Your Name <your.email@example.com>"
license = "MIT"
homepage = "https://github.com/yourusername/your-mcp-server"
repository = "https://github.com/yourusername/your-mcp-server.git"

[package.keywords]
categories = ["mcp-server", "business", "productivity", "ai-assistant"]
tags = ["fastmcp", "automation", "data-analysis", "workflow"]

[build]
# Source files to include in package
include = [
    "src/**/*.py",
    "dxt-package/**/*",
    "README.md",
    "LICENSE",
    "CHANGELOG.md"
]

# Files to exclude
exclude = [
    "tests/**/*",
    "**/__pycache__/**/*", 
    "**/*.pyc",
    ".git/**/*",
    "build/**/*"
]

# Build configuration
output_dir = "build"
compress = true

[mcp]
# MCP server configuration
server_executable = "python"
server_args = ["-m", "your_mcp_server.server"]
server_cwd = "."

# Environment variables for server
environment = {
    "MCP_ENVIRONMENT" = "production",
    "LOG_LEVEL" = "INFO"
}

[prompts]
# Prompt template configuration
templates_dir = "dxt-package/prompt-templates"
auto_register = true
```

#### 2. **dxt-package/metadata.json** - Extension Metadata:
```json
{
  "name": "your-mcp-server",
  "version": "1.0.0",
  "display_name": "Your MCP Server",
  "description": "Professional MCP server with business automation tools",
  "author": "Your Name",
  "email": "your.email@example.com",
  "homepage": "https://github.com/yourusername/your-mcp-server",
  "repository": "https://github.com/yourusername/your-mcp-server.git",
  "license": "MIT",
  "categories": ["mcp-server", "business", "productivity"],
  "tags": ["fastmcp", "automation", "data-analysis"],
  "claude_desktop_version": ">=1.0.0",
  "supported_platforms": ["windows", "macos", "linux"],
  "dependencies": {
    "python": ">=3.9",
    "fastmcp": ">=2.12.0"
  },
  "installation": {
    "auto_configure_mcp": true,
    "register_prompts": true,
    "create_shortcuts": false
  }
}
```

#### 3. **dxt-package/mcp-config.json** - MCP Server Configuration Template:
```json
{
  "mcpServers": {
    "your-mcp-server": {
      "command": "python",
      "args": ["-m", "your_mcp_server.server"],
      "cwd": "${EXTENSION_PATH}",
      "env": {
        "MCP_ENVIRONMENT": "production",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": "${EXTENSION_PATH}/src"
      }
    }
  }
}
```

### Prompt Templates in DXT

#### How Prompt Templates Work:
1. **Template Files**: Markdown files with placeholders and instructions
2. **Template Registry**: `templates.json` defines available templates
3. **Claude Integration**: Templates appear in Claude's prompt library
4. **User Access**: Users can invoke templates with `/template-name` or via UI

#### 4. **dxt-package/prompt-templates/templates.json** - Template Registry:
```json
{
  "templates": [
    {
      "id": "business-analysis",
      "name": "Business Analysis Assistant",
      "description": "Comprehensive business analysis with data insights",
      "file": "business-analysis.md",
      "category": "business",
      "tags": ["analysis", "data", "reporting"],
      "variables": [
        {
          "name": "company_name",
          "type": "string",
          "required": true,
          "description": "Name of the company to analyze"
        },
        {
          "name": "analysis_type",
          "type": "select",
          "required": true,
          "options": ["financial", "market", "competitive", "operational"],
          "description": "Type of business analysis to perform"
        },
        {
          "name": "time_period",
          "type": "string",
          "required": false,
          "default": "last 12 months",
          "description": "Time period for analysis"
        }
      ]
    },
    {
      "id": "code-review",
      "name": "Code Review Assistant", 
      "description": "Systematic code review with best practices",
      "file": "code-review.md",
      "category": "development",
      "tags": ["code", "review", "quality"],
      "variables": [
        {
          "name": "language",
          "type": "select",
          "required": true,
          "options": ["python", "javascript", "typescript", "java", "csharp", "go"],
          "description": "Programming language of the code"
        },
        {
          "name": "review_focus",
          "type": "select", 
          "required": false,
          "options": ["security", "performance", "maintainability", "style"],
          "description": "Primary focus area for review"
        }
      ]
    }
  ],
  "categories": [
    {
      "id": "business",
      "name": "Business Analysis",
      "description": "Templates for business intelligence and analysis"
    },
    {
      "id": "development", 
      "name": "Software Development",
      "description": "Templates for code review, debugging, and development"
    }
  ]
}
```

#### 5. **Example Prompt Template** - `dxt-package/prompt-templates/business-analysis.md`:
```markdown
# Business Analysis Assistant

You are a professional business analyst with expertise in {{analysis_type}} analysis. Your task is to provide comprehensive analysis for {{company_name}} covering the {{time_period}}.

## Analysis Framework

### 1. Executive Summary
- Provide a high-level overview of key findings
- Highlight critical insights and recommendations
- Summarize main risks and opportunities

### 2. {{analysis_type|title}} Analysis

{{#if analysis_type == "financial"}}
#### Financial Performance Analysis:
- Revenue trends and growth patterns
- Profitability metrics and margins
- Cash flow analysis
- Financial ratios and benchmarks
- Working capital management
{{/if}}

{{#if analysis_type == "market"}}
#### Market Analysis:
- Market size and growth potential
- Competitive landscape assessment
- Customer segmentation and behavior
- Market trends and drivers
- Positioning and differentiation
{{/if}}

### 3. Data Requirements
Please provide or request the following data for analysis:
- Financial statements (if applicable)
- Market research data
- Customer data and feedback
- Operational metrics
- Industry benchmarks

### 4. Methodology
- Quantitative analysis techniques
- Qualitative assessment methods  
- Benchmarking approach
- Risk assessment framework

### 5. Recommendations
- Strategic recommendations
- Tactical action items
- Implementation roadmap
- Success metrics and KPIs

---

**Instructions**: Please provide the data you'd like analyzed for {{company_name}}, and I'll conduct a comprehensive {{analysis_type}} analysis following this framework.
```

### DXT Build and Distribution Process

#### 1. **Validation and Building**:
```powershell
# Navigate to project directory
Set-Location "D:\Dev\repos\your-mcp-server"

# Validate DXT package structure and configuration
dxt validate

# If validation passes, build the DXT package
dxt pack

# This creates: build/your-mcp-server-v1.0.0.dxt
```

#### 2. **Distribution Methods**:

##### **GitHub Releases (Recommended)**:
```powershell
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Upload .dxt file to GitHub release
# Users download and install via Claude Desktop
```

## 🎯 **Core Architecture Principles**

### 1. **Modular Tool Organization**
```python
# Recommended structure for scalable MCP servers
src/your_mcp_server/
├── __init__.py
├── server.py              # Main server entry point
├── config.py              # Configuration management
├── tools/                 # Tool modules
│   ├── __init__.py
│   ├── core.py           # Essential tools (help, status, health)
│   ├── business.py       # Main business logic tools
│   ├── integrations.py   # External API integrations
│   └── debug.py          # Development and debugging tools
├── resources/             # MCP resources
│   ├── __init__.py
│   └── endpoints.py      # Resource endpoints
├── utils/                # Utilities
│   ├── __init__.py
│   ├── logging.py        # Logging configuration
│   ├── validators.py     # Input validation
│   └── helpers.py        # Helper functions
└── exceptions.py         # Custom exceptions
```

### 2. **FastMCP 2.12+ Server Foundation**
```python
"""Production-ready FastMCP server template."""
import asyncio
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import MCPError
from pydantic import BaseModel, Field

# Server configuration
SERVER_CONFIG = {
    "name": "Your MCP Server",
    "version": "1.0.0", 
    # NO description parameter - FastMCP doesn't support it
    "features": [
        "inspector_optimized",
        "error_tracking", 
        "performance_monitoring",
        "type_safety"
    ]
}

# Initialize server with Austrian efficiency
mcp = FastMCP(**SERVER_CONFIG)

# Global state management
_server_state = {
    "startup_time": datetime.now(),
    "request_count": 0,
    "error_count": 0,
    "last_health_check": None
}
```

## 🔧 **Tool Development Patterns**

### 1. **Standard Tool Template**
```python
from typing import Any, Dict, Optional
from fastmcp.exceptions import MCPError
from pydantic import BaseModel, Field

class ToolResponse(BaseModel):
    """Standard response format for consistency."""
    success: bool
    data: Any = None
    message: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

@mcp.tool()
async def example_business_tool(
    required_param: str,
    optional_param: Optional[int] = None,
    config_param: bool = True
) -> ToolResponse:
    """
    Business tool with Austrian efficiency patterns.
    
    Args:
        required_param: Description of required parameter
        optional_param: Description of optional parameter  
        config_param: Boolean configuration option
        
    Returns:
        ToolResponse: Standardized response format
        
    Raises:
        MCPError: When business logic validation fails
    """
    try:
        # Input validation
        if not required_param.strip():
            raise MCPError("Required parameter cannot be empty", code="INVALID_INPUT")
            
        # Business logic
        result = await process_business_logic(
            required_param, 
            optional_param, 
            config_param
        )
        
        # Track metrics
        _server_state["request_count"] += 1
        
        return ToolResponse(
            success=True,
            data=result,
            message=f"Successfully processed: {required_param}",
            metadata={
                "processing_time": "tracked_internally",
                "request_id": f"req_{_server_state['request_count']}"
            }
        )
        
    except Exception as e:
        _server_state["error_count"] += 1
        logger.error(f"Tool {example_business_tool.__name__} failed: {e}")
        
        # Convert to MCPError for proper Inspector display
        if isinstance(e, MCPError):
            raise
        else:
            raise MCPError(
                message=f"Processing failed: {str(e)}",
                code="PROCESSING_ERROR",
                data={"original_error": type(e).__name__}
            )
```

### 2. **Error Handling Best Practices**
```python
from enum import Enum

class MCPErrorCodes(str, Enum):
    """Standardized error codes for consistency."""
    INVALID_INPUT = "INVALID_INPUT"
    AUTHENTICATION_ERROR = "AUTH_ERROR"
    RESOURCE_NOT_FOUND = "NOT_FOUND"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    CONFIGURATION_ERROR = "CONFIG_ERROR"

def create_mcp_error(
    message: str, 
    code: MCPErrorCodes, 
    recoverable: bool = True,
    context: Optional[Dict[str, Any]] = None
) -> MCPError:
    """Create standardized MCP errors."""
    return MCPError(
        message=message,
        code=code.value,
        data={
            "recoverable": recoverable,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
    )
```

## 📝 **Basic Memory Tagging Discipline - CRITICAL QOL**

### ALWAYS tag notes with: [project-name, technology, status, priority]

Examples:
- **windows-operations-mcp work**: ["windows-operations-mcp", "powershell", "mcp", "fix", "critical"]  
- **llm-txt-mcp work**: ["llm-txt-mcp", "python", "fastmcp", "completed", "high"]
- **Research notes**: ["research", "technology-name", "solution", "medium"]
- **Bug fixes**: ["project-name", "bug", "fix", "technology", "priority"]

### Memory Rules
- **Always timestamp notes** to quickly find the LAST one of the day
- **Mark outdated notes with OBSOLETE** when produced during project work
- **At chat start ALWAYS read last basic memory note** to continue work quickly

**Tag properly = find instantly. Search poorly tagged notes = waste time.**

## 📈 **Austrian Efficiency Metrics**

### Key Performance Indicators:
- **Development Speed**: 10-30x faster with Inspector + proper practices
- **Error Detection**: Real-time vs delayed log analysis
- **Tool Testing**: Interactive vs manual
- **Package Management**: DXT distribution vs manual setup
- **Team Productivity**: Shared configurations and best practices

### Success Criteria:
- ✅ Inspector integration working
- ✅ All tools testable in browser
- ✅ Error handling visible and clear
- ✅ Performance monitoring active
- ✅ Health checks operational
- ✅ DXT packaging functional
- ✅ Prompt templates registered
- ✅ Production deployment ready

---

*These best practices ensure your FastMCP 2.12+ servers are production-ready, developer-friendly, maintainable, and properly packaged at Austrian efficiency standards with comprehensive DXT support.*