import time
import logging
from typing import Callable, Dict, Optional
from collections import defaultdict
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_orch")

# Rate limiter configuration
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, client_id: str) -> bool:
        async with self.lock:
            now = time.time()
            window_start = now - 60
            
            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
            
            # Check limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False
            
            self.requests[client_id].append(now)
            return True

# Security
security = HTTPBearer(auto_error=False)

class AgentOrchMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        rate_limiter: Optional[RateLimiter] = None,
        api_key: Optional[str] = None,
        allowed_origins: list = ["*"],
        log_requests: bool = True
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.api_key = api_key
        self.log_requests = log_requests
        
        # Add CORS middl