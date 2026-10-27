"""
QForge — GitHub App Client Service
Handles:
  1. GitHub App authentication via RS256 JWT
  2. Installation Access Token generation (with auto-discovery from /app/installations)
  3. Recursive Repository Tree API (git/trees/{sha}?recursive=1)
  4. Hierarchical nested directory tree generation for React UI
  5. On-demand Blob Content fetching (base64 decode)
  6. Multi-language file filtering (Python, TS/JS, Java, Go, Rust, C#, C/C++, SQL)
  7. Automated Branch & Pull Request creation
"""
import time
import base64
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import httpx
import jwt

from backend.config import settings

logger = logging.getLogger(__name__)

# Extensions mapped to language identifiers
LANGUAGE_EXTENSION_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".sql": "sql",
}

# Directories and files to automatically ignore
IGNORED_PATTERNS = {
    "node_modules", ".git", ".github", "__pycache__", ".pytest_cache",
    "dist", "build", "target", "vendor", ".venv", "venv", ".idea", ".vscode",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock"
}


def build_nested_file_tree(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts a flat list of file paths into a nested tree node structure for UI rendering."""
    tree_root: Dict[str, Any] = {}

    for file_info in files:
        parts = file_info["path"].split("/")
        current = tree_root
        for i, part in enumerate(parts):
            is_file = (i == len(parts) - 1)
            if part not in current:
                current[part] = {
                    "name": part,
                    "path": "/".join(parts[:i + 1]),
                    "type": "file" if is_file else "directory",
                    "children": {} if not is_file else None,
                }
                if is_file:
                    current[part].update(file_info)
            if not is_file:
                current = current[part]["children"]

    def _convert_dict_to_list(node_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = []
        for key in sorted(node_dict.keys()):
            item = node_dict[key]
            if item["type"] == "directory" and item.get("children"):
                item["children"] = _convert_dict_to_list(item["children"])
            nodes.append(item)
        return nodes

    return _convert_dict_to_list(tree_root)


class GitHubClient:
    """Async client for interacting with GitHub App and Git Trees APIs."""

    def __init__(self):
        self.app_id = settings.github_app_id
        self.installation_id = settings.github_app_installation_id
        self.private_key_path = settings.github_private_key_path
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _load_private_key(self) -> Optional[str]:
        """Reads RSA PEM private key from configured path or raw string."""
        if not self.private_key_path:
            return None
        if "BEGIN RSA PRIVATE KEY" in self.private_key_path or "BEGIN PRIVATE KEY" in self.private_key_path:
            return self.private_key_path.replace("\\n", "\n")
        p = Path(self.private_key_path)
        if not p.is_absolute():
            p = Path(os.getcwd()) / p
        if not p.exists():
            alt = Path(os.getcwd()) / "data" / "github" / "app.private-key.pem"
            if alt.exists():
                return alt.read_text(encoding="utf-8")
            return None
        return p.read_text(encoding="utf-8")

    def _generate_jwt(self) -> Optional[str]:
        """Generates RS256 signed JWT for GitHub App authentication."""
        if not self.app_id:
            return None
        private_key = self._load_private_key()
        if not private_key:
            return None
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (9 * 60),
            "iss": str(self.app_id),
        }
        return jwt.encode(payload, private_key, algorithm="RS256")

    async def get_installation_token(self) -> Optional[str]:
        """Obtains an installation access token, auto-discovering installation ID if needed."""
        now = time.time()
        if self._cached_token and now < (self._token_expires_at - 120):
            return self._cached_token

        jwt_token = self._generate_jwt()
        if not jwt_token:
            return None

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "QForge-Engine",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            target_install_id = None
            # If installation_id is integer string, use it directly
            if self.installation_id and self.installation_id.isdigit():
                target_install_id = self.installation_id
            else:
                # Auto-discover from /app/installations
                resp = await client.get("https://api.github.com/app/installations", headers=headers)
                if resp.status_code == 200:
                    installations = resp.json()
                    if installations:
                        target_install_id = str(installations[0].get("id"))
                        logger.info(f"[GITHUB] Auto-discovered installation ID: {target_install_id}")

            if not target_install_id:
                logger.info("[GITHUB] No installation found for this App yet. Operating in public/fallback mode.")
                return None

            url = f"https://api.github.com/app/installations/{target_install_id}/access_tokens"
            resp = await client.post(url, headers=headers)
            if resp.status_code in (200, 201):
                data = resp.json()
                self._cached_token = data["token"]
                self._token_expires_at = now + 3500
                return self._cached_token
            return None

    async def _get_auth_headers(self, custom_token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "QForge-Engine",
        }
        token = custom_token or settings.github_token or await self.get_installation_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def get_repo_tree(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        custom_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetches the complete recursive directory and file tree using GitHub Git Trees API.
        GET /repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1
        """
        headers = await self._get_auth_headers(custom_token)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Resolve default branch if none provided
            if not branch:
                repo_resp = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}",
                    headers=headers
                )
                if repo_resp.status_code == 404:
                    raise RuntimeError(f"Repository '{owner}/{repo}' not found or private. Ensure App is installed or repo is public.")
                elif repo_resp.status_code != 200:
                    raise RuntimeError(f"GitHub API Error ({repo_resp.status_code}): {repo_resp.text}")

                repo_info = repo_resp.json()
                branch = repo_info.get("default_branch", "main")
            else:
                repo_info = {}

            # 2. Call Git Trees API with recursive=1
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch git tree for {owner}/{repo}@{branch}: {resp.text}")

            tree_data = resp.json()
            raw_tree = tree_data.get("tree", [])

            # 3. Filter source files
            files = []
            for item in raw_tree:
                path = item.get("path", "")
                parts = path.split("/")

                # Filter ignored directories/files
                if any(p in IGNORED_PATTERNS for p in parts):
                    continue

                if item.get("type") == "blob":
                    ext = os.path.splitext(path)[1].lower()
                    lang = LANGUAGE_EXTENSION_MAP.get(ext)
                    if lang:
                        files.append({
                            "path": path,
                            "filename": parts[-1],
                            "sha": item.get("sha"),
                            "size": item.get("size", 0),
                            "language": lang,
                            "extension": ext,
                        })

            # 4. Generate nested folder hierarchy for UI
            nested_tree = build_nested_file_tree(files)

            return {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "tree_sha": tree_data.get("sha"),
                "total_source_files": len(files),
                "files": files,
                "nested_tree": nested_tree,
            }

    async def get_file_content(
        self, owner: str, repo: str, sha: str, custom_token: Optional[str] = None
    ) -> str:
        """
        Retrieves blob content via SHA and decodes base64 string to UTF-8 text.
        GET /repos/{owner}/{repo}/git/blobs/{sha}
        """
        headers = await self._get_auth_headers(custom_token)
        url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch blob {sha}: {resp.text}")

            data = resp.json()
            encoding = data.get("encoding", "base64")
            content_raw = data.get("content", "")

            if encoding == "base64":
                clean_b64 = content_raw.replace("\n", "").replace("\r", "")
                decoded_bytes = base64.b64decode(clean_b64)
                return decoded_bytes.decode("utf-8", errors="replace")
            return content_raw

    async def get_file_by_path(
        self, owner: str, repo: str, file_path: str, branch: str = "main", custom_token: Optional[str] = None
    ) -> str:
        """
        Retrieves raw file content by file path.
        GET /repos/{owner}/{repo}/contents/{path}?ref={branch}
        """
        headers = await self._get_auth_headers(custom_token)
        headers["Accept"] = "application/vnd.github.raw+json"
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch file {file_path}: {resp.text}")
            return resp.text


# Global client instance
github_client = GitHubClient()
