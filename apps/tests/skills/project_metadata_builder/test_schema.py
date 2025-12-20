"""Tests for project metadata schema dataclasses."""

from datetime import datetime

import pytest

from claude_apps.skills.project_metadata_builder.schema import (
    Activity,
    Dependencies,
    DockerConfig,
    GitCommit,
    GitMetadata,
    Languages,
    ProjectMetadata,
    Runtime,
    Session,
    Structure,
)


class TestGitCommit:
    """Tests for GitCommit dataclass."""

    def test_to_dict(self):
        """Test serialization."""
        commit = GitCommit(
            hash="abc123",
            message="Initial commit",
            author="Test User",
            date=datetime(2025, 1, 15, 10, 30, 0),
        )

        d = commit.to_dict()

        assert d["hash"] == "abc123"
        assert d["message"] == "Initial commit"
        assert d["author"] == "Test User"
        assert d["date"] == "2025-01-15T10:30:00"


class TestGitMetadata:
    """Tests for GitMetadata dataclass."""

    def test_defaults(self):
        """Test default values."""
        meta = GitMetadata()

        assert meta.remote_url is None
        assert meta.branch is None
        assert meta.last_commit is None
        assert meta.total_commits == 0

    def test_to_dict_empty(self):
        """Test serialization with empty values."""
        meta = GitMetadata()
        d = meta.to_dict()

        assert d["remote_url"] is None
        assert d["branch"] is None
        assert d["last_commit"] is None
        assert d["total_commits"] == 0

    def test_to_dict_with_commit(self):
        """Test serialization with commit."""
        meta = GitMetadata(
            remote_url="https://github.com/user/repo",
            branch="main",
            last_commit=GitCommit(
                hash="abc123",
                message="Test",
                author="User",
                date=datetime(2025, 1, 15),
            ),
            total_commits=100,
        )

        d = meta.to_dict()

        assert d["remote_url"] == "https://github.com/user/repo"
        assert d["branch"] == "main"
        assert d["last_commit"]["hash"] == "abc123"
        assert d["total_commits"] == 100


class TestLanguages:
    """Tests for Languages dataclass."""

    def test_defaults(self):
        """Test default values."""
        langs = Languages()

        assert langs.primary is None
        assert langs.all == {}

    def test_to_dict_formats_percentages(self):
        """Test that percentages are formatted."""
        langs = Languages(
            primary="Python",
            all={"Python": 0.75, "JavaScript": 0.25},
        )

        d = langs.to_dict()

        assert d["primary"] == "Python"
        assert "Python: 75%" in d["all"]
        assert "JavaScript: 25%" in d["all"]


class TestDependencies:
    """Tests for Dependencies dataclass."""

    def test_defaults(self):
        """Test default values."""
        deps = Dependencies()

        assert deps.python == []
        assert deps.node == []

    def test_to_dict_only_includes_nonempty(self):
        """Test that empty lists are excluded."""
        deps = Dependencies(python=["pytest"], node=[])

        d = deps.to_dict()

        assert "python" in d
        assert d["python"] == ["pytest"]
        assert "node" not in d

    def test_to_dict_empty(self):
        """Test empty dict for no dependencies."""
        deps = Dependencies()
        d = deps.to_dict()

        assert d == {}


class TestStructure:
    """Tests for Structure dataclass."""

    def test_defaults(self):
        """Test default values."""
        struct = Structure()

        assert struct.type == "standard"
        assert struct.key_directories == []
        assert struct.entry_points == []

    def test_to_dict(self):
        """Test serialization."""
        struct = Structure(
            type="monorepo",
            key_directories=["apps", "packages"],
            entry_points=["main.py"],
        )

        d = struct.to_dict()

        assert d["type"] == "monorepo"
        assert d["key_directories"] == ["apps", "packages"]
        assert d["entry_points"] == ["main.py"]


class TestDockerConfig:
    """Tests for DockerConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = DockerConfig()

        assert config.compose_file is None
        assert config.services == []

    def test_to_dict_only_includes_present(self):
        """Test that None/empty values are excluded."""
        config = DockerConfig(
            compose_file="docker-compose.yml",
            services=[],
        )

        d = config.to_dict()

        assert d["compose_file"] == "docker-compose.yml"
        assert "services" not in d

    def test_to_dict_with_services(self):
        """Test with services."""
        config = DockerConfig(
            compose_file="docker-compose.yml",
            services=["app", "db"],
        )

        d = config.to_dict()

        assert d["compose_file"] == "docker-compose.yml"
        assert d["services"] == ["app", "db"]


class TestRuntime:
    """Tests for Runtime dataclass."""

    def test_defaults(self):
        """Test default values."""
        runtime = Runtime()

        assert runtime.docker is None
        assert runtime.mcp_servers == []

    def test_to_dict_only_includes_present(self):
        """Test that None/empty values are excluded."""
        runtime = Runtime()
        d = runtime.to_dict()

        assert d == {}

    def test_to_dict_with_docker(self):
        """Test with Docker config."""
        runtime = Runtime(
            docker=DockerConfig(compose_file="docker-compose.yml"),
            mcp_servers=["context7", "playwright"],
        )

        d = runtime.to_dict()

        assert "docker" in d
        assert d["docker"]["compose_file"] == "docker-compose.yml"
        assert d["mcp_servers"] == ["context7", "playwright"]


class TestSession:
    """Tests for Session dataclass."""

    def test_to_dict(self):
        """Test serialization."""
        session = Session(
            id="session-123",
            started=datetime(2025, 1, 15, 10, 0, 0),
            ended=datetime(2025, 1, 15, 11, 0, 0),
            commits=5,
            files_changed=10,
        )

        d = session.to_dict()

        assert d["id"] == "session-123"
        assert d["started"] == "2025-01-15T10:00:00"
        assert d["ended"] == "2025-01-15T11:00:00"
        assert d["commits"] == 5
        assert d["files_changed"] == 10

    def test_to_dict_no_ended(self):
        """Test serialization without end time."""
        session = Session(
            id="session-123",
            started=datetime(2025, 1, 15, 10, 0, 0),
        )

        d = session.to_dict()

        assert d["ended"] is None


class TestActivity:
    """Tests for Activity dataclass."""

    def test_defaults(self):
        """Test default values."""
        activity = Activity()

        assert activity.status == "active"
        assert activity.first_seen is None
        assert activity.last_updated is None

    def test_to_dict(self):
        """Test serialization."""
        activity = Activity(
            status="stale",
            first_seen=datetime(2025, 1, 1),
            last_updated=datetime(2025, 1, 15),
        )

        d = activity.to_dict()

        assert d["status"] == "stale"
        assert d["first_seen"] == "2025-01-01T00:00:00"
        assert d["last_updated"] == "2025-01-15T00:00:00"


class TestProjectMetadata:
    """Tests for ProjectMetadata dataclass."""

    def test_required_fields(self):
        """Test required fields."""
        meta = ProjectMetadata(
            path="/workspace/project",
            name="My Project",
            slug="my-project",
        )

        assert meta.path == "/workspace/project"
        assert meta.name == "My Project"
        assert meta.slug == "my-project"

    def test_defaults(self):
        """Test default component values."""
        meta = ProjectMetadata(
            path="/test",
            name="Test",
            slug="test",
        )

        assert meta.description == ""
        assert isinstance(meta.git, GitMetadata)
        assert isinstance(meta.languages, Languages)
        assert meta.frameworks == []
        assert isinstance(meta.dependencies, Dependencies)
        assert isinstance(meta.structure, Structure)
        assert isinstance(meta.runtime, Runtime)
        assert isinstance(meta.activity, Activity)
        assert meta.sessions == []

    def test_to_dict(self):
        """Test full serialization."""
        meta = ProjectMetadata(
            path="/workspace/project",
            name="My Project",
            slug="my-project",
            description="A test project",
            frameworks=["pytest", "FastAPI"],
        )

        d = meta.to_dict()

        assert d["name"] == "My Project"
        assert d["slug"] == "my-project"
        assert d["description"] == "A test project"
        assert d["frameworks"] == ["pytest", "FastAPI"]
        assert "git" in d
        assert "languages" in d
        assert "dependencies" in d
        assert "structure" in d
        assert "runtime" in d
        assert "activity" in d
        assert "sessions" in d
