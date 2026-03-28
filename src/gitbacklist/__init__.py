from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from github import Github


@dataclass
class RepoEntry:
    """A git repository to back up."""

    clone_url: str
    dir_name: str


class Backlist:
    """Incremental backup list for git repositories.

    Collects repository URLs (from GitHub profiles, Codeberg, or any
    git-compatible host) and clones/pulls them into a local directory.

    Args:
        target_dir: Directory where repository backups will be stored.
                    Defaults to the current working directory.
    """

    def __init__(self, target_dir: str | os.PathLike = ".") -> None:
        self.target_dir = Path(target_dir).resolve()
        self.repos: list[RepoEntry] = []

    def add_github_profile(self, username: str) -> None:
        """Add all public repositories of a GitHub user.

        Args:
            username: GitHub username whose public repos will be backed up.
        """
        gh = Github()
        user = gh.get_user(username)
        for repo in user.get_repos():
            self.repos.append(
                RepoEntry(
                    clone_url=repo.clone_url,
                    dir_name=f"{username}-{repo.name}",
                )
            )

    def add_git_repo(self, repo_url: str) -> None:
        """Add a single git repository by URL.

        Works with any git-compatible host (GitHub, Codeberg, GitLab,
        Bitbucket, self-hosted Gitea, etc.).

        The local directory name is derived from the URL as
        ``<owner>-<repo>`` (e.g. ``john-myproject``).

        Args:
            repo_url: Clone URL of the repository
                      (HTTPS or SSH, e.g. ``https://codeberg.org/user/repo``).
        """
        parsed = urlparse(repo_url)
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]

        parts = path.split("/")
        if len(parts) >= 2:
            owner, name = parts[-2], parts[-1]
            dir_name = f"{owner}-{name}"
        else:
            dir_name = parts[-1] if parts else "repo"

        self.repos.append(RepoEntry(clone_url=repo_url, dir_name=dir_name))

    def start(self, *, verbose: bool = False) -> None:
        """Clone or update every repository in the list.

        For each repository:
        - If the local directory does not exist, ``git clone`` is executed.
        - If it already exists, ``git fetch --all`` + ``git reset --hard
          origin/<default-branch>`` + ``git clean -fd`` ensures the working
          tree matches the remote state exactly.

        Args:
            verbose: If *True*, print progress messages to stdout.
        """
        self.target_dir.mkdir(parents=True, exist_ok=True)

        for entry in self.repos:
            dest = self.target_dir / entry.dir_name
            if verbose:
                print(f"{'Updating' if dest.exists() else 'Cloning'}: {entry.clone_url} -> {dest}")

            if not dest.exists():
                self._run(["git", "clone", entry.clone_url, str(dest)], verbose=verbose)
            else:
                self._run(["git", "-C", str(dest), "fetch", "--all", "--prune"], verbose=verbose)
                default_branch = self._get_default_branch(dest)
                self._run(
                    ["git", "-C", str(dest), "reset", "--hard", f"origin/{default_branch}"],
                    verbose=verbose,
                )
                self._run(["git", "-C", str(dest), "clean", "-fd"], verbose=verbose)

    @staticmethod
    def _get_default_branch(repo_dir: Path) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # e.g. "refs/remotes/origin/main" -> "main"
            return result.stdout.strip().split("/")[-1]
        return "main"

    @staticmethod
    def _run(cmd: list[str], *, verbose: bool = False) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
        )
        if result.returncode != 0:
            stderr = result.stderr if not verbose else ""
            raise RuntimeError(
                f"Command failed (exit {result.returncode}): {' '.join(cmd)}\n{stderr}".strip()
            )
        return result
