"""
FastAPI middleware plugin for agent_orch API with rate limiting, logging, auth, and CORS.
Single file implementation.
"""
import time
import logging
import asyncio
from typing import Dict, Tuple, Optional, Callable
from collections import defaultdict
from functools import wraps
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse
import jwt
from pydantic import BaseModel, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_orch_middleware")

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.rate = requests_per_minute
        self.buckets: Dict[str, Dict] = defaultdict(lambda: {
            'tokens': requests_per_minute,
            'last_refill': time.time()
        })
        self.lock = asyncio.Lock()
    
    async def check(self, key: str) -> Tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, retry_after_seconds)"""
        async with self.lock:
            bucket = self.buckets[key]
            now = time.time()
            elapsed = now - bucket['last_refill']
            
            # Refill tokens
            bucket['tokens'] = min(
                self.rate,
                bucket['tokens'] + elapsed * (self.rate / 60.0)
            )
            bucket['last_refill'] = now
            
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True, 0
            else:
                retry_after = int((1 - bucket['tokens']) * 60 / self.rate) + 1
                return False, retry_after

class AuthMiddl