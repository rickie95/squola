#!/usr/bin/env python3
"""Reset a Squola user's password from the command line.

Run from any directory with:
    uv run python helpers/reset_password.py <username>
"""

import argparse
import os
from getpass import getpass
from pathlib import Path

# The application's SQLite URL is relative to the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)

from sqlalchemy import select

from squola.auth import PASSWORD_MIN_LENGTH, hash_password, revoke_user_sessions
from squola.database import SessionLocal
from squola.models import User


def parse_args() -> argparse.Namespace:
    """Parse the target username."""
    parser = argparse.ArgumentParser(description="Reset a Squola user's password.")
    parser.add_argument("username", help="Username of the account to update")
    return parser.parse_args()


def prompt_for_password() -> str:
    """Prompt for a compliant password and require confirmation."""
    password = getpass("New password: ")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
        )

    confirmation = getpass("Confirm new password: ")
    if password != confirmation:
        raise ValueError("Passwords do not match.")

    return password


def main() -> None:
    """Update the password and revoke every active session for the user."""
    args = parse_args()

    try:
        password = prompt_for_password()
    except ValueError as error:
        raise SystemExit(str(error)) from error

    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.username == args.username)).first()
        if user is None:
            raise SystemExit(f"User {args.username!r} was not found.")

        user.password_hash = hash_password(password)
        revoke_user_sessions(db, user.id)
        username = user.username
        db.commit()

    print(f"Password reset for {username!r}; all active sessions were revoked.")


if __name__ == "__main__":
    main()
