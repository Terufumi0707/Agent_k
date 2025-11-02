"""Application service that exposes workspace CRUD operations."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Literal, Optional

from ...domain.workspaces import TranscriptEntry, Workspace
from ...infrastructure.workspaces import (
    WorkspaceNotFoundError,
    get_workspace_repository,
)


class WorkspaceServiceError(Exception):
    """Base error for workspace service operations."""


class WorkspaceNotFound(WorkspaceServiceError):
    """Raised when attempting to access a non-existent workspace."""


def list_workspaces() -> list[Workspace]:
    """Return all workspaces currently registered in the repository."""

    repository = get_workspace_repository()
    return repository.list()


def create_workspace(title: Optional[str] = None) -> Workspace:
    """Create a new workspace and return the resulting entity."""

    repository = get_workspace_repository()
    return repository.create(title)


def update_workspace(
    workspace_id: str,
    *,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    status: Optional[Literal["running", "completed"]] = None,
    transcript: Optional[Iterable[TranscriptEntry]] = None,
    last_updated_at: Optional[datetime] = None,
) -> Workspace:
    """Update fields of a workspace by delegating to the repository."""

    repository = get_workspace_repository()
    try:
        return repository.update(
            workspace_id,
            title=title,
            summary=summary,
            status=status,
            transcript=transcript,
            last_updated_at=last_updated_at,
        )
    except WorkspaceNotFoundError as exc:  # pragma: no cover - thin wrapper
        raise WorkspaceNotFound(workspace_id) from exc


def delete_workspace(workspace_id: str) -> None:
    """Remove a workspace from the repository."""

    repository = get_workspace_repository()
    try:
        repository.delete(workspace_id)
    except WorkspaceNotFoundError as exc:  # pragma: no cover - thin wrapper
        raise WorkspaceNotFound(workspace_id) from exc
