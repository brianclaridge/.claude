"""
Project metadata schema definitions using dataclasses.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class GitCommit:
    """Git commit information."""

    hash: str
    message: str
    author: str
    date: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "hash": self.hash,
            "message": self.message,
            "author": self.author,
            "date": self.date.isoformat(),
        }


@dataclass
class GitMetadata:
    """Git repository metadata."""

    remote_url: str | None = None
    branch: str | None = None
    last_commit: GitCommit | None = None
    total_commits: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "remote_url": self.remote_url,
            "branch": self.branch,
            "last_commit": self.last_commit.to_dict() if self.last_commit else None,
            "total_commits": self.total_commits,
        }


@dataclass
class Languages:
    """Language detection results."""

    primary: str | None = None
    all: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "all": [f"{lang}: {pct:.0%}" for lang, pct in self.all.items()],
        }


@dataclass
class Dependencies:
    """Project dependencies."""

    python: list[str] = field(default_factory=list)
    node: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        if self.python:
            result["python"] = self.python
        if self.node:
            result["node"] = self.node
        return result


@dataclass
class Structure:
    """Project structure information."""

    type: str = "standard"  # monorepo, standard, library, etc.
    key_directories: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "key_directories": self.key_directories,
            "entry_points": self.entry_points,
        }


@dataclass
class DockerConfig:
    """Docker configuration."""

    compose_file: str | None = None
    services: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        if self.compose_file:
            result["compose_file"] = self.compose_file
        if self.services:
            result["services"] = self.services
        return result


@dataclass
class Runtime:
    """Runtime configuration."""

    docker: DockerConfig | None = None
    mcp_servers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        if self.docker:
            result["docker"] = self.docker.to_dict()
        if self.mcp_servers:
            result["mcp_servers"] = self.mcp_servers
        return result


@dataclass
class Session:
    """Session history entry."""

    id: str
    started: datetime
    ended: datetime | None = None
    commits: int = 0
    files_changed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "started": self.started.isoformat(),
            "ended": self.ended.isoformat() if self.ended else None,
            "commits": self.commits,
            "files_changed": self.files_changed,
        }


@dataclass
class Activity:
    """Activity tracking."""

    status: str = "active"  # active, stale, archived
    first_seen: datetime | None = None
    last_updated: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class ProjectMetadata:
    """Complete project metadata."""

    path: str
    name: str
    slug: str
    description: str = ""

    # Components
    git: GitMetadata = field(default_factory=GitMetadata)
    languages: Languages = field(default_factory=Languages)
    frameworks: list[str] = field(default_factory=list)
    dependencies: Dependencies = field(default_factory=Dependencies)
    structure: Structure = field(default_factory=Structure)
    runtime: Runtime = field(default_factory=Runtime)
    activity: Activity = field(default_factory=Activity)
    sessions: list[Session] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "git": self.git.to_dict(),
            "languages": self.languages.to_dict(),
            "frameworks": self.frameworks,
            "dependencies": self.dependencies.to_dict(),
            "structure": self.structure.to_dict(),
            "runtime": self.runtime.to_dict(),
            "activity": self.activity.to_dict(),
            "sessions": [s.to_dict() for s in self.sessions],
        }
