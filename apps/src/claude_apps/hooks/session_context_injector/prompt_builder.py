"""Build agent invocation prompts based on session type."""

from typing import Any


def build_agent_prompt(source: str, config: dict[str, Any]) -> str:
    """Build prompt to trigger project-analysis agent.

    Args:
        source: Session source type (startup, resume, clear, compact)
        config: Session context configuration

    Returns:
        Prompt text to inject as additionalContext
    """
    behavior = config.get("session_behavior", {}).get(source, "full")

    if source == "startup":
        return _startup_prompt(behavior)
    elif source == "resume":
        return _resume_prompt(behavior)
    elif source == "compact":
        return _compact_prompt(behavior)
    elif source == "clear":
        return _clear_prompt(behavior)
    else:
        return _startup_prompt(behavior)


def _startup_prompt(behavior: str) -> str:
    """Prompt for new session startup."""
    return f"""## Session Context Injection

**Session Type:** New session (startup)
**Analysis Mode:** {behavior}

**INSTRUCTION:** Invoke the `project-analysis` agent with the following context:

```
Analyze the current directory. Session type: startup. Analysis mode: {behavior}.
Before presenting analysis, invoke the session-context skill to gather git history, recent plans, and pending work.
```

This is an automatic session initialization. Present the analysis results to the user without additional commentary."""


def _resume_prompt(behavior: str) -> str:
    """Prompt for resumed session."""
    return f"""## Session Context Injection

**Session Type:** Resumed session (--continue/--resume)
**Analysis Mode:** {behavior}

**INSTRUCTION:** Invoke the `project-analysis` agent with the following context:

```
Analyze the current directory. Session type: resume. Analysis mode: {behavior}.
Focus on: recent git activity, pending work, and changes since last session.
Invoke the session-context skill for context gathering.
```

This is a session resumption. Present abbreviated analysis focusing on what has changed."""


def _compact_prompt(behavior: str) -> str:
    """Prompt for post-compaction session."""
    return f"""## Session Context Injection

**Session Type:** Post-compaction
**Analysis Mode:** {behavior}

**INSTRUCTION:** Context was compacted. Invoke the `project-analysis` agent with:

```
Analyze the current directory. Session type: compact. Analysis mode: {behavior}.
This is a context refresh after compaction. Focus on current state and any pending work.
Invoke the session-context skill for context gathering.
```

Re-establish context awareness after compaction."""


def _clear_prompt(behavior: str) -> str:
    """Prompt for post-clear session."""
    return f"""## Session Context Injection

**Session Type:** Post-clear (/clear command)
**Analysis Mode:** {behavior}

**INSTRUCTION:** Session was cleared. Invoke the `project-analysis` agent with:

```
Analyze the current directory. Session type: clear. Analysis mode: {behavior}.
This is a fresh start after /clear. Perform full analysis.
Invoke the session-context skill for context gathering.
```

Provide full analysis as if starting fresh."""
