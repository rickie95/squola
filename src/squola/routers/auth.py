"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from sqlalchemy import select
from sqlalchemy.orm import Session

from squola.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    SessionContext,
    create_auth_session,
    enforce_password_policy,
    get_session_context,
    hash_password,
    revoke_session_by_token,
    verify_password,
)
from squola.database import get_db
from squola.models import User, Workspace, WorkspaceMembership, WorkspaceRole
from squola.schemas import AuthSessionResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    enforce_password_policy(payload.password)
    existing_user = db.scalars(select(User).where(User.username == payload.username)).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already in use")

    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()

    workspace_name = payload.workspace_name or f"Workspace di {payload.username}"
    workspace = Workspace(name=workspace_name)
    db.add(workspace)
    db.flush()

    membership = WorkspaceMembership(
        workspace_id=workspace.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER.value,
    )
    db.add(membership)

    raw_token, _ = create_auth_session(db, user.id)
    db.commit()
    db.refresh(user)
    db.refresh(workspace)
    _set_session_cookie(response, raw_token)
    return AuthSessionResponse(user=user, workspace=workspace)


@router.post("/login", response_model=AuthSessionResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )
    user = db.scalars(select(User).where(User.username == payload.username)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise generic_error

    membership = db.scalars(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.user_id == user.id)
        .order_by(WorkspaceMembership.role.desc(), WorkspaceMembership.id.asc())
    ).first()
    if membership is None:
        raise generic_error
    workspace = db.get(Workspace, membership.workspace_id)
    if workspace is None:
        raise generic_error

    raw_token, _ = create_auth_session(db, user.id)
    db.commit()
    _set_session_cookie(response, raw_token)
    return AuthSessionResponse(user=user, workspace=workspace)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> None:
    if session_cookie:
        revoke_session_by_token(db, session_cookie)
        db.commit()
    _clear_session_cookie(response)


@router.get("/me", response_model=AuthSessionResponse)
def me(context: SessionContext = Depends(get_session_context)) -> AuthSessionResponse:
    return AuthSessionResponse(user=context.user, workspace=context.workspace)
