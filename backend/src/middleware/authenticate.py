import jwt
import os
from fastapi import Request, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional

SECRET_KEY = os.getenv("JWT_ACCESS_SECRET", "your_secret_key") 

class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, secret_key: str = SECRET_KEY):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next):
        # Extract the JWT token from the cookie
        token: Optional[str] = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(status_code=401, detail="Access token is missing")

        try:
            # Decode and verify the JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            request.state.user = payload  # Attach the decoded payload to the request state
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Access token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid access token")

        # Proceed to the next middleware or endpoint
        response = await call_next(request)
        return response