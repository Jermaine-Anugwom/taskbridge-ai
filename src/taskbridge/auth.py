from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Callable
from enum import IntEnum

from fastapi import Header, HTTPException


class Role(IntEnum):
    VIEWER = 1
    OPERATOR = 2
    ADMIN = 3


def auth_required() -> bool:
    return os.getenv("TASKBRIDGE_REQUIRE_AUTH", "false").casefold() == "true"


def _token_role(token: str) -> Role | None:
    digest = hashlib.sha256(token.encode()).hexdigest()
    for role, variable in (
        (Role.ADMIN, "TASKBRIDGE_ADMIN_TOKEN_SHA256"),
        (Role.OPERATOR, "TASKBRIDGE_OPERATOR_TOKEN_SHA256"),
        (Role.VIEWER, "TASKBRIDGE_VIEWER_TOKEN_SHA256"),
    ):
        configured = os.getenv(variable)
        if configured and hmac.compare_digest(configured, digest):
            return role
    return None


def require_role(minimum: Role) -> Callable[..., Role]:
    def dependency(authorization: str | None = Header(default=None)) -> Role:
        if not auth_required():
            return Role.ADMIN
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer token required")
        role = _token_role(authorization.removeprefix("Bearer ").strip())
        if role is None:
            raise HTTPException(status_code=401, detail="Invalid bearer token")
        if role < minimum:
            raise HTTPException(status_code=403, detail="Role does not permit this operation")
        return role

    return dependency
