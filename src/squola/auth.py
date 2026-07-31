"""Authentication and current-session helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from squola.database import get_db
from squola.models import AuthSession, User, Workspace, WorkspaceMembership, WorkspaceRole

SESSION_COOKIE_NAME = "squola_session"
SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60
PASSWORD_MIN_LENGTH = 12


@dataclass
class SessionContext:
    """Current authenticated context."""

    user: User
    workspace: Workspace
    session: AuthSession


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_password(password: str) -> str:
    """Hash a password using scrypt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a scrypt hash."""
    try:
        algorithm, salt_b64, digest_b64 = password_hash.split("$", maxsplit=2)
    except ValueError:
        return False
    if algorithm != "scrypt":
        return False
    try:
        salt = base64.b64decode(salt_b64)
        expected_digest = base64.b64decode(digest_b64)
    except Exception:
        return False
    actual_digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return hmac.compare_digest(actual_digest, expected_digest)


def hash_session_token(token: str) -> str:
    """Hash a session token to avoid storing raw secrets."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_auth_session(db: Session, user_id: int) -> tuple[str, AuthSession]:
    """Create a new auth session and return raw token + db record."""
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_session_token(raw_token)
    session = AuthSession(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=_utcnow() + timedelta(seconds=SESSION_MAX_AGE_SECONDS),
    )
    db.add(session)
    return raw_token, session


def _load_session_context(db: Session, raw_token: str) -> SessionContext | None:
    token_hash = hash_session_token(raw_token)
    stmt = (
        select(AuthSession, User, Workspace)
        .join(User, User.id == AuthSession.user_id)
        .join(WorkspaceMembership, WorkspaceMembership.user_id == User.id)
        .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
        .where(AuthSession.token_hash == token_hash)
        .where(AuthSession.revoked_at.is_(None))
        .where(AuthSession.expires_at > _utcnow())
        .order_by(WorkspaceMembership.role.desc(), WorkspaceMembership.id.asc())
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    auth_session, user, workspace = row
    return SessionContext(user=user, workspace=workspace, session=auth_session)


def get_session_context(
    db: Session = Depends(get_db),
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> SessionContext:
    """FastAPI dependency for authenticated requests."""
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    context = _load_session_context(db, session_cookie)
    if context is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return context


def get_current_user(context: SessionContext = Depends(get_session_context)) -> User:
    return context.user


def get_current_workspace(context: SessionContext = Depends(get_session_context)) -> Workspace:
    return context.workspace


def enforce_password_policy(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters long",
        )


def revoke_session_by_token(db: Session, raw_token: str) -> None:
    token_hash = hash_session_token(raw_token)
    session = db.get(AuthSession, token_hash)
    if session is None or session.revoked_at is not None:
        return
    session.revoked_at = _utcnow()


def revoke_user_sessions(db: Session, user_id: int) -> None:
    sessions = db.scalars(
        select(AuthSession)
        .where(AuthSession.user_id == user_id)
        .where(AuthSession.revoked_at.is_(None))
    ).all()
    now = _utcnow()
    for session in sessions:
        session.revoked_at = now

