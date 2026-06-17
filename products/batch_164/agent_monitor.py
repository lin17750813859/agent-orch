#!/usr/bin/env python3
"""System monitor reporting CPU, memory, disk usage, and agent system health."""

import os
import sys
import time
import json
import signal
import argparse
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from collections import deque

try:
    import psutil
except ImportError:
    print("ERROR: psutil is required. Install with: pip install psutil", file=sys.stderr)
    sys.exit(1)


class SystemMonitor:
    """Monitors system resources and agent health."""

    def __init__(self, interval=2, history_size=60, agent_pid=None):
        self.interval = interval
        self.history_size = history_size
        self.agent_pid = agent_pid
        self.running = False
        self.history = {
            "cpu": deque(maxlen=history_size),
            "memory": deque(maxlen=history_size),
            "disk": deque(maxlen=history_size),
            "agent": deque(maxlen=history_size),
            "timestamps": deque(maxlen=history_size),
        }

    def get_cpu_info(self):
        """Get CPU usage percentage and load average."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
        return {
            "percent": cpu_percent,
            "count": cpu_count,
            "load_avg_1min": round(load_avg[0], 2),
            "load_avg_5min": round(load_avg[1], 2),
            "load_avg_15min": round(load_avg[2], 2),
        }

    def get_memory_info(self):
        """Get memory usage details."""
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

    def get_disk_info(self):