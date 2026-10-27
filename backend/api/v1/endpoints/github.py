"""
QForge — GitHub Repositories REST Endpoints
Allows fetching repo trees, file content, and triggering test generation from GitHub.
"""
import re
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.services.github.client import github_client, LANGUAGE_EXTENSION_MAP
from backend.core.session_manager import get_session_manager, SessionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/github", tags=["GitHub Integration"])


class RepoTreeRequest(BaseModel):
    repo: str = Field(..., description="Repository full name 'owner/repo' or GitHub URL")
    branch: Optional[str] = Field(None, description="Branch or commit SHA (defaults to default branch)")
    token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token (for private repos)")


class FileContentRequest(BaseModel):
    owner: str
    repo: str
    sha: Optional[str] = None
    path: Optional[str] = None
    branch: Optional[str] = "main"
    token: Optional[str] = None


def _parse_repo_string(repo_input: str) -> tuple[str, str]:
    """Extracts (owner, repo) from 'owner/repo' or 'https://github.com/owner/repo'."""
    clean = repo_input.strip()
    # If full URL: https://github.com/owner/repo or git@github.com:owner/repo
    url_match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git|/)?$", clean)
    if url_match:
        return url_match.group(1), url_match.group(2)

    parts = clean.strip("/").split("/")
    if len(parts) == 2:
        return parts[0], parts[1].replace(".git", "")

    raise ValueError(f"Invalid repository specification: '{repo_input}'. Expected format: 'owner/repo' or GitHub URL.")


@router.get("/status")
async def get_github_app_status():
    """Returns the current GitHub App integration status."""
    has_key = bool(github_client._load_private_key())
    token = await github_client.get_installation_token()
    return {
        "app_id": github_client.app_id or "Not configured",
        "has_private_key": has_key,
        "authenticated": token is not None,
        "token_prefix": token[:8] + "..." if token else None,
        "mode": "GitHub App Authenticated" if token else "Public / Personal Access Token Mode",
    }


@router.post("/tree")
async def fetch_repository_tree(payload: RepoTreeRequest):
    """
    Fetches the recursive source file tree of a GitHub repository via Git Trees API.
    Returns both a flat list of source files and a hierarchical nested folder tree for UI.
    """
    try:
        owner, repo_name = _parse_repo_string(payload.repo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        tree_result = await github_client.get_repo_tree(
            owner=owner,
            repo=repo_name,
            branch=payload.branch,
            custom_token=payload.token,
        )
        return tree_result
    except Exception as e:
        logger.error(f"[GITHUB] Failed to fetch tree for {payload.repo}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository tree: {str(e)}")


@router.post("/file")
async def fetch_file_content(payload: FileContentRequest):
    """Retrieves file content by SHA or file path."""
    try:
        if payload.sha:
            content = await github_client.get_file_content(
                owner=payload.owner,
                repo=payload.repo,
                sha=payload.sha,
                custom_token=payload.token,
            )
        elif payload.path:
            content = await github_client.get_file_by_path(
                owner=payload.owner,
                repo=payload.repo,
                file_path=payload.path,
                branch=payload.branch or "main",
                custom_token=payload.token,
            )
        else:
            raise HTTPException(status_code=400, detail="Must provide either 'sha' or 'path'")

        ext = payload.path.split(".")[-1].lower() if payload.path else ""
        lang = LANGUAGE_EXTENSION_MAP.get(f".{ext}", "text")

        return {
            "owner": payload.owner,
            "repo": payload.repo,
            "path": payload.path,
            "sha": payload.sha,
            "language": lang,
            "content": content,
            "size": len(content),
        }
    except Exception as e:
        logger.error(f"[GITHUB] Failed to fetch file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
