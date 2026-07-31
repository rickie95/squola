"""Account management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from squola.auth import (
    SessionContext,
    enforce_password_policy,
    get_session_context,
    hash_password,
    revoke_user_sessions,
    verify_password,
)
from squola.database import get_db
from squola.schemas import (
    AuthSessionResponse,
    ChangePasswordRequest,
    RenameWorkspaceRequest,
)

router = APIRouter(prefix="/account", tags=["account"])


@router.get("", response_model=AuthSessionResponse)
def get_account(context: SessionContext = Depends(get_session_context)) -> AuthSessionResponse:
    return AuthSessionResponse(user=context.user, workspace=context.workspace)


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    context: SessionContext = Depends(get_session_context),
    db: Session = Depends(get_db),
) -> None:
    if not verify_password(payload.current_password, context.user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    enforce_password_policy(payload.new_password)
    context.user.password_hash = hash_password(payload.new_password)
    revoke_user_sessions(db, context.user.id)
    db.commit()


@router.patch("/workspace", response_model=AuthSessionResponse)
def rename_workspace(
    payload: RenameWorkspaceRequest,
    context: SessionContext = Depends(get_session_context),
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    workspace_name = payload.name.strip()
    if not workspace_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace name cannot be empty")
    context.workspace.name = workspace_name
    db.commit()
    db.refresh(context.workspace)
    return AuthSessionResponse(user=context.user, workspace=context.workspace)
