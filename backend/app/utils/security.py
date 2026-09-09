"""
BhuSynch AI — Security Utilities
===================================
Keycloak OIDC JWT validation middleware.
Maps to: API Gateway & Security Ingress (Kong) — Section 1
• Keycloak OIDC (OAuth 2.0 / JWT)
• Role-Based RBAC/ABAC
"""

from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def verify_jwt_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> dict:
    """
    Validate JWT token from Keycloak OIDC.

    In production:
    - Fetches JWKS from Keycloak server
    - Validates token signature, expiry, audience
    - Extracts user roles for RBAC/ABAC

    Returns decoded token payload.
    """
    if credentials is None:
        # Allow unauthenticated access in development
        if settings.DEBUG:
            return {"sub": "dev-user", "roles": ["admin"], "realm_access": {"roles": ["revenue_officer"]}}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    token = credentials.credentials

    try:
        # Placeholder — in production:
        # from jose import jwt
        # jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
        # payload = jwt.decode(token, jwks, algorithms=["RS256"], audience=settings.KEYCLOAK_CLIENT_ID)
        # return payload

        # Development placeholder
        return {
            "sub": "placeholder-user",
            "roles": ["revenue_officer"],
            "realm_access": {"roles": ["revenue_officer"]},
        }

    except Exception as e:
        logger.error("jwt_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


def require_role(role: str):
    """Dependency that requires a specific Keycloak role."""
    async def role_checker(
        token: dict = Depends(verify_jwt_token),
    ) -> dict:
        user_roles = token.get("realm_access", {}).get("roles", [])
        if role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return token
    return role_checker
