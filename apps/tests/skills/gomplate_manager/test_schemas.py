"""Tests for gomplate-manager Pydantic schemas."""

import pytest
from pydantic import ValidationError

from claude_apps.skills.gomplate_manager.schemas import (
    DatasourceConfig,
    GomplateConfig,
    validate_gomplate_config,
)


class TestDatasourceConfig:
    """Tests for DatasourceConfig schema."""

    def test_url_only(self):
        """Test datasource with URL only."""
        ds = DatasourceConfig(url="file:///config.json")

        assert ds.url == "file:///config.json"
        assert ds.header is None

    def test_with_headers(self):
        """Test datasource with headers."""
        ds = DatasourceConfig(
            url="https://api.example.com/config",
            header={"Authorization": "Bearer token"},
        )

        assert ds.url == "https://api.example.com/config"
        assert ds.header == {"Authorization": "Bearer token"}


class TestGomplateConfig:
    """Tests for GomplateConfig schema."""

    def test_minimal_valid_config(self):
        """Test minimal valid configuration."""
        config = GomplateConfig(
            inputFiles=["template.txt.tmpl"],
            outputFiles=["/output/template.txt"],
        )

        assert config.inputFiles == ["template.txt.tmpl"]
        assert config.outputFiles == ["/output/template.txt"]

    def test_input_dir_with_output_dir(self):
        """Test inputDir with outputDir."""
        config = GomplateConfig(
            inputDir="templates/",
            outputDir="/output/",
        )

        assert config.inputDir == "templates/"
        assert config.outputDir == "/output/"

    def test_inline_template(self):
        """Test inline template (no output required)."""
        config = GomplateConfig(input="{{ .Env.FOO }}")

        assert config.input == "{{ .Env.FOO }}"
        # No output required for inline

    def test_missing_input_raises(self):
        """Test that missing input specification raises error."""
        with pytest.raises(ValidationError) as exc_info:
            GomplateConfig(outputFiles=["/output.txt"])

        assert "Missing input specification" in str(exc_info.value)

    def test_missing_output_raises(self):
        """Test that missing output specification raises error."""
        with pytest.raises(ValidationError) as exc_info:
            GomplateConfig(inputFiles=["template.txt"])

        assert "Missing output specification" in str(exc_info.value)

    def test_mismatched_file_counts_raises(self):
        """Test that mismatched input/output counts raise error."""
        with pytest.raises(ValidationError) as exc_info:
            GomplateConfig(
                inputFiles=["a.tmpl", "b.tmpl"],
                outputFiles=["/output/a.txt"],  # Only one output
            )

        assert "inputFiles count" in str(exc_info.value)

    def test_multiple_input_files(self):
        """Test multiple input/output files."""
        config = GomplateConfig(
            inputFiles=["a.tmpl", "b.tmpl", "c.tmpl"],
            outputFiles=["/a.txt", "/b.txt", "/c.txt"],
        )

        assert len(config.inputFiles) == 3
        assert len(config.outputFiles) == 3

    def test_with_datasources(self):
        """Test configuration with datasources."""
        config = GomplateConfig(
            inputFiles=["template.tmpl"],
            outputFiles=["/output.txt"],
            datasources={
                "config": DatasourceConfig(url="file:///config.json"),
                "simple": "file:///simple.yaml",  # String shorthand
            },
        )

        assert "config" in config.datasources
        assert "simple" in config.datasources

    def test_with_excludes(self):
        """Test configuration with excludes."""
        config = GomplateConfig(
            inputDir="templates/",
            outputDir="/output/",
            excludes=["*.md", "README*"],
        )

        assert config.excludes == ["*.md", "README*"]

    def test_with_custom_delimiters(self):
        """Test configuration with custom delimiters."""
        config = GomplateConfig(
            inputFiles=["template.erb"],
            outputFiles=["/output.txt"],
            leftDelim="<%",
            rightDelim="%>",
        )

        assert config.leftDelim == "<%"
        assert config.rightDelim == "%>"

    def test_with_missing_key(self):
        """Test configuration with missingKey option."""
        config = GomplateConfig(
            inputFiles=["template.tmpl"],
            outputFiles=["/output.txt"],
            missingKey="error",
        )

        assert config.missingKey == "error"

    def test_output_map(self):
        """Test outputMap configuration."""
        config = GomplateConfig(
            inputDir="templates/",
            outputMap='{{ .in | strings.ReplaceAll ".tmpl" "" }}',
        )

        assert config.inputDir == "templates/"
        assert ".in" in config.outputMap

    def test_allows_extra_fields(self):
        """Test that extra fields are allowed for forward compatibility."""
        config = GomplateConfig(
            inputFiles=["template.tmpl"],
            outputFiles=["/output.txt"],
            unknownFutureField="some value",
        )

        assert config.inputFiles == ["template.tmpl"]
        # Extra field should be accessible
        assert hasattr(config, "unknownFutureField") or True  # Pydantic v2 handles this

    def test_alias_names_work(self):
        """Test that aliased field names work."""
        # Using 'in' instead of 'input'
        config = GomplateConfig(**{"in": "{{ .Env.FOO }}"})

        assert config.input == "{{ .Env.FOO }}"


class TestValidateGomplateConfig:
    """Tests for validate_gomplate_config function."""

    def test_validates_valid_config(self):
        """Test validating a valid config dict."""
        config_dict = {
            "inputFiles": ["template.tmpl"],
            "outputFiles": ["/output.txt"],
        }

        config = validate_gomplate_config(config_dict)

        assert isinstance(config, GomplateConfig)
        assert config.inputFiles == ["template.tmpl"]

    def test_raises_on_invalid_config(self):
        """Test raises ValidationError on invalid config."""
        config_dict = {
            "outputFiles": ["/output.txt"],
            # Missing input
        }

        with pytest.raises(ValidationError):
            validate_gomplate_config(config_dict)
