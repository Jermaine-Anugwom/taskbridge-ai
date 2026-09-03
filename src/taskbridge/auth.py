from __future__ import annotations

import hashlib
import hmac
import os
import re
from collections.abc import Callable
from enum import IntEnum
from urllib.parse import unquote, urlsplit

from fastapi import Header, HTTPException


class Role(IntEnum):
    VIEWER = 1
    OPERATOR = 2
    ADMIN = 3


def auth_required() -> bool:
    return (
        os.getenv("TASKBRIDGE_ENV", "demo").casefold() == "production"
        or os.getenv("TASKBRIDGE_REQUIRE_AUTH", "false").casefold() != "false"
    )


def validate_runtime_config(database: str) -> None:
    environment = os.getenv("TASKBRIDGE_ENV", "demo").casefold()
    if environment not in {"demo", "production"}:
        raise ValueError("TASKBRIDGE_ENV must be demo or production")
    if os.getenv("TASKBRIDGE_REQUIRE_AUTH", "false").casefold() not in {"true", "false"}:
        raise ValueError("TASKBRIDGE_REQUIRE_AUTH must be true or false")
    if environment != "production":
        return
    if os.getenv("TASKBRIDGE_REQUIRE_AUTH", "false").casefold() != "true":
        raise ValueError("Production requires TASKBRIDGE_REQUIRE_AUTH=true")
    digests = [os.getenv(f"TASKBRIDGE_{role}_TOKEN_SHA256", "")
               for role in ("VIEWER", "OPERATOR", "ADMIN")]
    if any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in digests):
        raise ValueError("Production requires a valid SHA-256 token digest for each role")
    if len(set(digests)) != 3 or hashlib.sha256(b"").hexdigest() in digests:
        raise ValueError("Production role tokens must be distinct and nonempty")
    parsed = urlsplit(database)
    password = unquote(parsed.password or "")
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.username:
        raise ValueError("Production requires PostgreSQL with explicit credentials")
    if len(password) < 16 or password.casefold() in {"taskbridge", "postgres", "password"}:
        raise ValueError("Production requires a non-demo database password of at least 16 characters")


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
