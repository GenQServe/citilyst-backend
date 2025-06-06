import logging
from typing import List, Callable, Optional
from functools import wraps
import time
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RBACMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        jwt_secret: str,
        allowed_paths: Optional[List[str]] = None,
        roles_field: str = "role",
    ):
        """
        Initialize RBAC middleware

        Args:
            app: The ASGI application
            jwt_secret: Secret key for JWT decoding
            allowed_paths: Paths that don't require authentication
            roles_field: Field name in JWT payload that contains roles
        """
        super().__init__(app)
        self.jwt_secret = jwt_secret
        self.allowed_paths = allowed_paths or []
        self.roles_field = roles_field

        # Add default public paths
        self.allowed_paths.extend(
            [
                "/docs",
                "/redoc",
                "/openapi.json",
                "/auth/login",
                "/auth/register",
                "/auth/google",
                "/auth/google/callback",
                "/auth/verify-otp",
                "/auth/resend-otp",
                "/auth/me",
                "/feedback-user",
                "/static/*",  # Allow access to static files
            ]
        )

        logging.info(
            f"RBAC Middleware initialized with allowed paths: {self.allowed_paths}"
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request through middleware

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint to call

        Returns:
            The response from the next middleware or endpoint
        """
        # Check if path is allowed without authentication
        path = request.url.path
        if self._is_path_allowed(path):
            return await call_next(request)

        # Get token from Authorization header
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "message": "Authentication required. Please provide a valid Bearer token."
                },
            )

        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            # Check if token is expired
            exp_timestamp = payload.get("exp")
            if not exp_timestamp:
                return JSONResponse(
                    status_code=401,
                    content={"message": "Invalid token: missing expiration time."},
                )

            current_timestamp = int(time.time())
            if current_timestamp > exp_timestamp:
                # Calculate how long ago the token expired
                expired_seconds = current_timestamp - exp_timestamp
                expired_minutes = expired_seconds // 60

                if expired_minutes < 60:
                    time_ago = (
                        f"{expired_minutes} minute{'s' if expired_minutes != 1 else ''}"
                    )
                else:
                    expired_hours = expired_minutes // 60
                    if expired_hours < 24:
                        time_ago = (
                            f"{expired_hours} hour{'s' if expired_hours != 1 else ''}"
                        )
                    else:
                        expired_days = expired_hours // 24
                        time_ago = (
                            f"{expired_days} day{'s' if expired_days != 1 else ''}"
                        )

                return JSONResponse(
                    status_code=401,
                    content={
                        "message": f"Authentication token expired {time_ago} ago. Please login again.",
                        "code": "token_expired",
                    },
                )

            # Extract role from payload
            role = payload.get(self.roles_field, "").lower()

            # Check if role is valid
            if not role or (role != "user" and role != "admin"):
                return JSONResponse(
                    status_code=403,
                    content={
                        "message": f"Insufficient permissions. Role '{role}' is not authorized."
                    },
                )

            # Add user info to request state
            request.state.user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": role,
                "image_url": payload.get("image_url"),
                "is_verified": payload.get("is_verified", False),
                "exp": exp_timestamp,
                "token_expiration": datetime.fromtimestamp(exp_timestamp).isoformat(),
            }

            # Continue with the request
            return await call_next(request)

        except JWTError as e:
            logging.error(f"JWT decode error: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={
                    "message": "Invalid authentication token. Please provide a valid Bearer token."
                },
            )
        except Exception as e:
            logging.error(f"RBAC middleware error: {str(e)}")
            return JSONResponse(
                status_code=500, content={"message": "Internal server error"}
            )

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract token from Authorization header only

        Args:
            request: The request object

        Returns:
            Optional[str]: The token if found, None otherwise
        """
        # Get from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[
                7:
            ].strip()  # Remove 'Bearer ' prefix and trim whitespace

        return None

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is in allowed paths list"""
        # If exact path is allowed
        if path in self.allowed_paths:
            return True

        # Check if path starts with any of the allowed paths
        for allowed_path in self.allowed_paths:
            if allowed_path.endswith("*") and path.startswith(allowed_path[:-1]):
                return True

        return False


class RoleChecker:
    """
    Helper class to check if user has required roles in specific endpoints

    Usage:
        @app.get("/admin-only")
        @RoleChecker(roles=["admin"])
        async def admin_only(request: Request):
            return {"message": "Admin only"}
    """

    def __init__(self, roles: List[str]):
        self.roles = [role.lower() for role in roles]

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)  # Preserve original function signature
        async def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required. Please provide a valid Bearer token.",
                )

            user_role = user.get("role", "").lower()

            if user_role not in self.roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Role '{user_role}' is not allowed to access this resource.",
                )

            return await func(request, *args, **kwargs)

        return wrapper


def requires_role(roles: List[str]):
    """
    Decorator to require specific roles for an endpoint

    Usage:
        @app.get("/admin-only")
        @requires_role(["admin"])
        async def admin_only(request: Request):
            return {"message": "Admin only"}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)  # Preserve original function signature
        async def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required. Please provide a valid Bearer token.",
                )

            user_role = user.get("role", "").lower()

            if user_role not in [role.lower() for role in roles]:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required role: {', '.join(roles)}",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def verify_role(required_roles: List[str]):
    """
    Dependency to verify user role

    Usage:
        @app.get("/admin-only")
        async def admin_only(
            role_check: bool = Depends(verify_role(["admin"]))
        ):
            return {"message": "Admin only"}
    """

    async def _verify_role(request: Request):
        user = getattr(request.state, "user", None)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please provide a valid Bearer token.",
            )

        user_role = user.get("role", "").lower()

        if user_role not in [role.lower() for role in required_roles]:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {', '.join(required_roles)}",
            )

        return True

    return _verify_role
