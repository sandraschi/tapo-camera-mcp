# Robotics Interface & Virtual Spawn Protocol

## Overview
The "Make New Virtual Robot" button in the dashboard is an interface to the **Robotics MCP orchestration layer**. It allows for the instantiation of virtual robot "digital twins" (e.g., Moorebot Scout, Unitree Go2) in a connected simulation environment before physical deployment.

## Architecture
The button triggers a POST request to `/api/robots/create_vbot`, which orchestrates the following:

1.  **Orchestration**: Signals the `robotics-mcp` server.
2.  **Target Environment**: 
    - **Unity3D**: Spawns the robot prefab in the active scene.
    - **VRChat**: Triggers an OSC event to spawn the robot avatar/object.
3.  **Physical Hardware**: **NO** physical hardware is deployed by this button.

## Virtual Robots
Supported models for virtual instantiation:
- **Moorebot Scout**: Exploring patrol logic in confined spaces (under furniture).
- **Unitree Go2**: Testing quadruped locomotion and LiDAR mapping.
- **Unitree G1**: Humanoid interaction testing.

> [!NOTE]
> This feature requires the `robotics-mcp` and `unity3d-mcp` servers to be active and connected. If disconnected, the button will log an error but fail gracefully.
