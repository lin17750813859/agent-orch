#!/usr/bin/env python3
"""System Monitor - Reports CPU, memory, disk usage, and agent system health."""

import psutil
import json
import time
import os
import sys
from datetime import datetime


def get_cpu_info():
    """Get CPU usage information."""
    return {
        "percent": psutil.cpu_percent(interval=1),
        "count": psutil.cpu_count(),
        "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else None,
        "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
    }


def get_memory_info():
    """Get memory usage information."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent,
        "swap_total": swap.total,
        "swap_used": swap.used,
        "swap_percent": swap.percent,
    }


def get_disk_info():
    """Get disk usage information."""
    partitions = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except PermissionError:
            continue
    io = psutil.disk_io_counters()
    return {
        "partitions": partitions,
        "io_read_bytes": io.read_bytes if io else 0,
        "io_write_bytes": io.write_bytes if io else 0,
    }


def get_agent_health():
    """Get agent system health indicators."""
    health = {
        "process_count": len(psutil.pids()),
        "connections": len(psutil.net_connections()),
        "network_io": {},
        "sensors": {},
        "status": "healthy",
    }
    net_io = psutil.net_io_counters()
    if net_io:
        health["net