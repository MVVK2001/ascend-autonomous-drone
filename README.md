# ASCEND Autonomous Drone

## Overview

ASCEND (Autonomous Survey, Charging and Evaluation Navigation Drone) is a ROS2-based autonomous drone framework developed for autonomous survey missions, telemetry monitoring, image acquisition, autonomous return-to-home, docking, charging, and mission validation.

The system is designed around a drone-side autonomy stack and a centralized base station located at the center of the operational arena.

---

## Current Architecture

### Drone Side

* Mission Manager
* Navigation Node
* Telemetry Node
* Vision Node (Planned)
* Docking Node (Planned)
* Data Transfer Node (Planned)

### Base Station

* Telemetry Dashboard
* Mission Dashboard
* Image Validation System
* Super Resolution Engine
* Mission Control

---

## Mission Flow

IDLE

↓

TAKEOFF

↓

SURVEY

↓

RETURN_HOME

↓

DOCK

↓

CHARGE

↓

TRANSFER_DATA

↓

VALIDATION

↓

REVISIT (if required)

↓

MISSION_COMPLETE

---

## Software Stack

* Ubuntu 22.04
* ROS2 Humble
* RViz2
* MAVROS
* Gazebo Harmonic
* ArduPilot SITL
* OpenCV
* Python

---

## Current Progress

### Completed

* ROS2 Workspace Setup
* Mission Manager Node
* Navigation Node
* Telemetry Node
* RViz Validation
* Survey Mission Execution
* Return-To-Home Logic
* Docking State Machine
* Charging State Machine
* Data Transfer State

### In Progress

* Vision Node
* Image Compression Pipeline

### Planned

* LR → HR Image Reconstruction
* Validation Engine
* Revisit Planning
* Base Station Dashboard
* Hardware Deployment

---

## Author

Vamsi Venkata Krishna Mandru

M.Tech Robotics and Automation

