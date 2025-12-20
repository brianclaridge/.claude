"""Pydantic schemas for gomplate-manager configuration."""

from typing import Any

from pydantic import BaseModel, Field, model_validator


class DatasourceConfig(BaseModel):
    """Datasource configuration for gomplate."""

    url: str = Field(..., description="URL or file path for the datasource")
    header: dict[str, str] | None = Field(default=None, description="HTTP headers")


class GomplateConfig(BaseModel):
    """Configuration schema for gomplate.yaml.

    Validates gomplate configuration files against required structure.
    Supports multiple input/output specification styles.
    """

    # Input specifications (one required)
    inputFiles: list[str] | None = Field(
        default=None,
        alias="inputFiles",
        description="List of input template files",
    )
    inputDir: str | None = Field(
        default=None,
        alias="inputDir",
        description="Directory containing input templates",
    )
    input: str | None = Field(
        default=None,
        alias="in",
        description="Inline template string",
    )

    # Output specifications (required unless using 'in')
    outputFiles: list[str] | None = Field(
        default=None,
        alias="outputFiles",
        description="List of output file paths",
    )
    outputDir: str | None = Field(
        default=None,
        alias="outputDir",
        description="Directory for output files",
    )
    outputMap: str | None = Field(
        default=None,
        alias="outputMap",
        description="Go template for output path mapping",
    )

    # Optional configurations
    datasources: dict[str, DatasourceConfig | str] | None = Field(
        default=None,
        description="Named datasources for template access",
    )
    plugins: dict[str, str] | None = Field(
        default=None,
        description="Plugin commands to execute",
    )
    excludes: list[str] | None = Field(
        default=None,
        description="Glob patterns to exclude from inputDir",
    )
    excludeProcessing: list[str] | None = Field(
        default=None,
        description="Glob patterns to copy without processing",
    )
    missingKey: str | None = Field(
        default=None,
        description="Behavior for missing keys: error, zero, default",
    )
    leftDelim: str | None = Field(
        default=None,
        description="Left template delimiter (default: {{)",
    )
    rightDelim: str | None = Field(
        default=None,
        description="Right template delimiter (default: }})",
    )

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow unknown fields for forward compatibility
        populate_by_name = True  # Allow both alias and field name

    @model_validator(mode="after")
    def validate_input_output(self) -> "GomplateConfig":
        """Validate that input and output specifications are present."""
        has_input = any([self.inputFiles, self.inputDir, self.input])
        has_output = any([self.outputFiles, self.outputDir, self.outputMap])

        if not has_input:
            raise ValueError(
                "Missing input specification: provide inputFiles, inputDir, or in"
            )

        # Output not required if using inline 'in'
        if not has_output and not self.input:
            raise ValueError(
                "Missing output specification: provide outputFiles, outputDir, or outputMap"
            )

        # Validate inputFiles/outputFiles count match
        if self.inputFiles and self.outputFiles:
            if len(self.inputFiles) != len(self.outputFiles):
                raise ValueError(
                    f"inputFiles count ({len(self.inputFiles)}) != "
                    f"outputFiles count ({len(self.outputFiles)})"
                )

        return self


def validate_gomplate_config(config: dict[str, Any]) -> GomplateConfig:
    """Validate a gomplate config dict and return typed config.

    Args:
        config: Raw config dict from YAML

    Returns:
        Validated GomplateConfig instance

    Raises:
        ValidationError: If config is invalid
    """
    return GomplateConfig(**config)
