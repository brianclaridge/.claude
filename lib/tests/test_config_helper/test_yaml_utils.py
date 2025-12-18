"""Tests for config_helper.yaml_utils module."""

import pytest

from config_helper import safe_load, safe_dump


class TestSafeLoad:
    """Tests for safe_load function."""

    def test_loads_from_string(self):
        """Should parse YAML from string."""
        yaml_str = "key: value\nlist:\n  - item1\n  - item2"
        result = safe_load(yaml_str)
        assert result["key"] == "value"
        assert result["list"] == ["item1", "item2"]

    def test_loads_from_path(self, temp_dir):
        """Should parse YAML from file path."""
        yaml_file = temp_dir / "test.yml"
        yaml_file.write_text("name: test\ncount: 42")
        result = safe_load(yaml_file)
        assert result["name"] == "test"
        assert result["count"] == 42

    def test_loads_from_string_path(self, temp_dir):
        """Should parse YAML from string file path."""
        yaml_file = temp_dir / "test.yml"
        yaml_file.write_text("data: hello")
        result = safe_load(str(yaml_file))
        assert result["data"] == "hello"

    def test_returns_empty_dict_for_empty_content(self):
        """Should return empty dict for empty/null YAML."""
        result = safe_load("")
        assert result == {}

    def test_raises_for_missing_file(self, temp_dir):
        """Should raise FileNotFoundError for missing file."""
        missing_file = temp_dir / "nonexistent.yml"
        with pytest.raises(FileNotFoundError):
            safe_load(missing_file)


class TestSafeDump:
    """Tests for safe_dump function."""

    def test_dumps_to_string(self):
        """Should return YAML string when dest is None."""
        data = {"key": "value", "count": 10}
        result = safe_dump(data)
        assert "key: value" in result
        assert "count: 10" in result

    def test_dumps_to_file(self, temp_dir):
        """Should write YAML to file when dest provided."""
        output_file = temp_dir / "output.yml"
        data = {"name": "test", "items": [1, 2, 3]}
        safe_dump(data, output_file)
        assert output_file.exists()
        content = output_file.read_text()
        assert "name: test" in content

    def test_creates_parent_directories(self, temp_dir):
        """Should create parent directories if needed."""
        nested_file = temp_dir / "nested" / "dir" / "output.yml"
        safe_dump({"data": "value"}, nested_file)
        assert nested_file.exists()

    def test_sort_keys_option(self):
        """Should sort keys when sort_keys=True."""
        data = {"z": 1, "a": 2, "m": 3}
        result = safe_dump(data, sort_keys=True)
        # Keys should appear in alphabetical order
        assert result.index("a:") < result.index("m:") < result.index("z:")
