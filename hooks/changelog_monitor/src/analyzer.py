"""Analyze changelog for opportunities and updates."""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from .parser import VersionEntry, extract_keywords

log = structlog.get_logger()


@dataclass
class AnalysisResult:
    """Results of changelog analysis."""

    new_versions: list[VersionEntry] = field(default_factory=list)
    hook_opportunities: list[str] = field(default_factory=list)
    skill_opportunities: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)
    notable_features: list[str] = field(default_factory=list)


def analyze_versions(versions: list[VersionEntry]) -> AnalysisResult:
    """Analyze version entries for opportunities."""
    result = AnalysisResult(new_versions=versions)

    for version in versions:
        # Analyze features
        for feature in version.features:
            keywords = extract_keywords(feature)

            # Hook opportunities
            if "hooks" in keywords or "events" in keywords or "triggers" in keywords:
                result.hook_opportunities.append(f"[{version.version}] {feature}")

            # Skill opportunities
            if "tools" in keywords or "mcp" in keywords or "api" in keywords:
                result.skill_opportunities.append(f"[{version.version}] {feature}")

            # Notable features (anything new)
            result.notable_features.append(f"[{version.version}] {feature}")

        # Breaking changes
        for breaking in version.breaking:
            result.breaking_changes.append(f"[{version.version}] {breaking}")

    log.debug(
        "analysis_complete",
        hook_opportunities=len(result.hook_opportunities),
        skill_opportunities=len(result.skill_opportunities),
        breaking_changes=len(result.breaking_changes),
    )

    return result


def format_context_injection(result: AnalysisResult) -> str:
    """Format analysis results for session context injection."""
    if not result.new_versions:
        return ""

    lines = ["## Claude Code Updates Available"]
    lines.append("")

    latest = result.new_versions[0] if result.new_versions else None
    if latest:
        lines.append(f"**Latest version:** {latest.version}")
        if latest.date:
            lines.append(f"**Released:** {latest.date}")
        lines.append("")

    if result.breaking_changes:
        lines.append("### Breaking Changes (Action Required)")
        for change in result.breaking_changes[:3]:
            lines.append(f"- {change}")
        lines.append("")

    if result.hook_opportunities:
        lines.append("### New Hook Opportunities")
        for opp in result.hook_opportunities[:3]:
            lines.append(f"- {opp}")
        lines.append("")

    if result.skill_opportunities:
        lines.append("### New Skill Opportunities")
        for opp in result.skill_opportunities[:3]:
            lines.append(f"- {opp}")
        lines.append("")

    if result.notable_features and not (result.hook_opportunities or result.skill_opportunities):
        lines.append("### Notable Features")
        for feature in result.notable_features[:5]:
            lines.append(f"- {feature}")
        lines.append("")

    lines.append("Run `/roadmap` to see full analysis or update the roadmap.")

    return "\n".join(lines)


def generate_roadmap_content(result: AnalysisResult, last_version: str | None) -> str:
    """Generate ROADMAP.md content from analysis."""
    from datetime import datetime, timezone

    lines = ["# Claude Code Feature Roadmap"]
    lines.append("")
    lines.append(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    if result.new_versions:
        lines.append(f"Last checked: {result.new_versions[0].version}")
    lines.append("")

    lines.append("## New Features to Evaluate")
    lines.append("")
    if result.notable_features:
        for feature in result.notable_features:
            lines.append(f"- [ ] {feature}")
    else:
        lines.append("No new features since last check.")
    lines.append("")

    lines.append("## Hook Opportunities")
    lines.append("")
    if result.hook_opportunities:
        for opp in result.hook_opportunities:
            lines.append(f"- [ ] {opp}")
    else:
        lines.append("No new hook events detected.")
    lines.append("")

    lines.append("## Skill Opportunities")
    lines.append("")
    if result.skill_opportunities:
        for opp in result.skill_opportunities:
            lines.append(f"- [ ] {opp}")
    else:
        lines.append("No new skill opportunities detected.")
    lines.append("")

    if result.breaking_changes:
        lines.append("## Breaking Changes (Action Required)")
        lines.append("")
        for change in result.breaking_changes:
            lines.append(f"- [ ] {change}")
        lines.append("")

    lines.append("## Version History")
    lines.append("")
    for version in result.new_versions[:10]:
        date_str = f" ({version.date})" if version.date else ""
        lines.append(f"### {version.version}{date_str}")
        lines.append("")
        if version.features:
            lines.append("**Features:**")
            for f in version.features[:5]:
                lines.append(f"- {f}")
        if version.fixes:
            lines.append("**Fixes:**")
            for f in version.fixes[:3]:
                lines.append(f"- {f}")
        lines.append("")

    return "\n".join(lines)
