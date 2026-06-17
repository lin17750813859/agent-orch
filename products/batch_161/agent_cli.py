#!/usr/bin/env python3
"""Agent Orchestrator CLI - Manage agent_orch agents from the command line."""

import argparse
import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    import aiohttp
except ImportError:
    print("Error: aiohttp is required. Install with: pip install aiohttp", file=sys.stderr)
    sys.exit(1)

API_BASE = os.environ.get("AGENT_ORCH_API", "http://localhost:8000")
DEFAULT_TIMEOUT = 30


def format_timestamp(ts: str) -> str:
    """Format ISO timestamp to human readable."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return str(ts)


def format_json(data: Any) -> str:
    """Pretty print JSON data."""
    return json.dumps(data, indent=2, default=str)


class AgentCLI:
    """CLI handler for agent operations."""

    def __init__(self, base_url: str = API_BASE, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to agent API."""
        url = f"{self.base_url}{path}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.request(method, url, **kwargs) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        return {"error": True, "status": resp.status, "message": text}
                    return await resp.json()
            except asyncio.TimeoutError:
                return {"error": True, "message": f"Request timed out after {self.timeout}s"}
            except aiohttp.ClientError as e:
                return {"error": True, "message": str(e)}

    async d