"""Validation primitives for repository-grounded tool trajectories."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import re
from typing import Any

EVENTS = ("inspect", "diagnose", "edit", "observe", "retry", "final")
TOOLS = ("read_file", "search", "run", "apply_patch")
SAFE_COMMAND_PREFIXES = ("tsc --noEmit", "npx tsc --noEmit", "npm exec tsc --noEmit")
SHELL_METACHARACTERS = re.compile(r"[;&|`$()]|\n|\r")

TRAJECTORY_SCHEMA = {
    "outer": "object with trajectory array and final string",
    "outer_envelope": "only top-level keys trajectory and final; trajectory must be the first key",
    "inspect": "event, tool=read_file or search, args object containing path or query",
    "diagnose": "event, tool=run, args.command string",
    "edit": "event, tool=apply_patch, args.path plus either complete args.content or exact args.replacements",
    "replacements": "each replacement has non-empty old and string new; old must occur exactly once",
    "large_file_edit": "when repository_facts.large_file or edit_mode=exact-replacements, use args.replacements instead of complete content",
    "edit_content_completeness": "args.content must be the complete target file, including unchanged context; abbreviated snippets are invalid",
    "observe": "event and integer exit_code; no tool or args",
    "retry": "event and optional content; only after an edit",
    "final": "event and non-empty content; must be last",
    "verification": "an observe exit_code 0 must occur after the last edit",
}

PATCH_EMITTER_SCHEMA = {
    "outer": "object with path string and replacements array",
    "path": "repository-relative target path",
    "replacements": "minimal exact once-only old/new replacement list; do not copy unchanged context",
    "diagnostic_alignment": "the compiler location may be downstream from the offending text; inspect the whole numbered window and change the offending expression, never return an unchanged replacement",
}


@dataclass(frozen=True)
class TrajectoryIssue:
    code: str
    message: str
    index: int | None = None


def _issue(code: str, message: str, index: int | None = None) -> TrajectoryIssue:
    return TrajectoryIssue(code, message, index)


def apply_replacements(original: str, replacements: list[dict[str, str]]) -> str:
    """Apply exact once-only replacements without shell or fuzzy matching."""
    if not isinstance(replacements, list) or not replacements:
        raise ValueError("replacements must be a non-empty list")
    updated = original
    for replacement in replacements:
        if not isinstance(replacement, dict) or not isinstance(replacement.get("old"), str) or not isinstance(replacement.get("new"), str) or not replacement["old"]:
            raise ValueError("each replacement requires non-empty old and string new")
        if replacement["old"] == replacement["new"]:
            raise ValueError("replacement must change the anchored text")
        count = updated.count(replacement["old"])
        if count != 1:
            raise ValueError(f"replacement anchor occurs {count} times; expected exactly once")
        updated = updated.replace(replacement["old"], replacement["new"], 1)
    return updated


def bounded_file_excerpt(content: str, start_line: int, end_line: int | None = None,
                        radius: int = 3, max_chars: int = 2400) -> str:
    """Return a numbered, bounded source window for a patch-emitter stage."""
    if not isinstance(content, str) or start_line < 1:
        raise ValueError("content must be text and start_line must be positive")
    lines = content.splitlines(keepends=True)
    if not lines:
        return ""
    end_line = end_line if end_line is not None else start_line
    if end_line < start_line:
        raise ValueError("end_line must not precede start_line")
    first = max(1, start_line - radius)
    last = min(len(lines), end_line + radius)
    while first <= last:
        excerpt = "".join(f"{number}: {lines[number - 1]}" for number in range(first, last + 1))
        if len(excerpt) <= max_chars or (first == start_line == 1 and last == len(lines)):
            return excerpt[:max_chars]
        if first < start_line:
            first += 1
        elif last > end_line:
            last -= 1
        else:
            return excerpt[:max_chars]
    return ""


def diagnostic_file_location(diagnostic: str) -> tuple[str, int, int] | None:
    """Extract the first TypeScript path(line,column) location from compiler text."""
    locations = diagnostic_file_locations(diagnostic)
    return locations[0] if locations else None


def diagnostic_file_locations(diagnostic: str) -> list[tuple[str, int, int]]:
    """Extract all TypeScript path(line,column) locations from compiler text."""
    if not isinstance(diagnostic, str):
        return []
    return [(match.group(1), int(match.group(2)), int(match.group(3)))
            for match in re.finditer(r"(?m)^\s*([^\s()]+)\((\d+),(\d+)\):\s*(?:error|warning)\b", diagnostic)]


def patch_emitter_context(repository_files: dict[str, str], diagnostic: str,
                          radius: int = 8, max_chars: int = 2400) -> dict[str, Any] | None:
    """Build a bounded patch context from a compiler diagnostic and snapshots."""
    locations = diagnostic_file_locations(diagnostic)
    if not locations:
        return None
    path, line, column = locations[0]
    content = repository_files.get(path)
    if not isinstance(content, str):
        return None
    same_file_lines = [candidate_line for candidate_path, candidate_line, _ in locations if candidate_path == path]
    end_line = max(same_file_lines) if same_file_lines else line
    start_line = min(same_file_lines) if same_file_lines else line
    return {
        "path": path,
        "diagnostic": diagnostic,
        "line": line,
        "column": column,
        "diagnostic_locations": [{"line": candidate_line, "column": candidate_column}
                                 for candidate_path, candidate_line, candidate_column in locations
                                 if candidate_path == path],
        "source_localization_rule": "If a diagnostic points at a downstream use, patch the earlier expression that introduced the wrong type; never patch a no-op use site.",
        "file_context": bounded_file_excerpt(content, start_line, end_line=end_line, radius=radius, max_chars=max_chars),
    }


def build_patch_emitter_request(record: dict[str, Any], diagnostic: str,
                                radius: int = 8, max_chars: int = 2400) -> dict[str, Any]:
    """Build stage-two input without placing the complete repository in context."""
    context = patch_emitter_context(record.get("repository_files", {}), diagnostic,
                                    radius=radius, max_chars=max_chars)
    if context is None:
        raise ValueError("diagnostic does not identify a snapshotted repository file")
    return {
        "task": record.get("task", ""),
        "repository_facts": record.get("repository_facts", {}),
        "compiler_diagnostic": diagnostic,
        "target": context,
        "patch_emitter_contract": PATCH_EMITTER_SCHEMA,
    }


def validate_trajectory(record: dict[str, Any]) -> list[TrajectoryIssue]:
    """Validate structure and safe ordering without executing tools."""
    issues: list[TrajectoryIssue] = []
    if not isinstance(record.get("task"), str) or not record["task"].strip():
        issues.append(_issue("missing_task", "task must be a non-empty string"))
    if not isinstance(record.get("repository_facts"), dict):
        issues.append(_issue("missing_repository_facts", "repository_facts must be an object"))
    events = record.get("trajectory")
    if not isinstance(events, list) or not events:
        return issues + [_issue("missing_trajectory", "trajectory must be a non-empty list")]
    seen_final = False
    seen_edit = False
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            issues.append(_issue("invalid_event", "event must be an object", index))
            continue
        kind = event.get("event")
        if kind not in EVENTS:
            issues.append(_issue("invalid_event_type", f"unsupported event type: {kind!r}", index))
        if seen_final:
            issues.append(_issue("event_after_final", "no events may follow final", index))
        if kind == "final":
            seen_final = True
            if not isinstance(event.get("content"), str) or not event["content"].strip():
                issues.append(_issue("missing_final", "final content must be non-empty", index))
        if kind in {"inspect", "diagnose", "edit"}:
            tool = event.get("tool")
            if tool not in TOOLS:
                issues.append(_issue("invalid_tool", f"unsupported tool: {tool!r}", index))
            if kind == "edit":
                seen_edit = True
                args = event.get("args")
                valid_content = isinstance(args, dict) and isinstance(args.get("content"), str) and "replacements" not in args
                valid_replacements = isinstance(args, dict) and "content" not in args and isinstance(args.get("replacements"), list) and bool(args["replacements"])
                if not isinstance(args, dict) or not isinstance(args.get("path"), str) or not (valid_content or valid_replacements):
                    issues.append(_issue("invalid_edit", "edit requires path plus complete content or exact replacements", index))
                elif valid_replacements:
                    for replacement in args["replacements"]:
                        if not isinstance(replacement, dict) or not isinstance(replacement.get("old"), str) or not replacement["old"] or not isinstance(replacement.get("new"), str) or replacement.get("old") == replacement.get("new"):
                            issues.append(_issue("invalid_replacement", "each replacement requires non-empty old and string new", index))
                elif isinstance(record.get("repository_files"), dict):
                    original = record["repository_files"].get(args["path"])
                    content = args["content"]
                    if isinstance(original, str) and len(original) >= 512 and len(content) < max(128, len(original) // 4):
                        issues.append(_issue("incomplete_edit_content", "edit content is too short to be the complete large target file", index))
                if valid_replacements and isinstance(record.get("repository_files"), dict) and isinstance(record["repository_files"].get(args["path"]), str):
                    try:
                        apply_replacements(record["repository_files"][args["path"]], args["replacements"])
                    except ValueError as exc:
                        issues.append(_issue("invalid_replacement", str(exc), index))
            args = event.get("args")
            if isinstance(args, dict) and isinstance(args.get("path"), str):
                path = args["path"]
                path_parts = path.replace("\\", "/").split("/")
                if path.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:", path) or ".." in path_parts:
                    issues.append(_issue("unsafe_path", "trajectory paths must stay within the repository", index))
        if kind == "diagnose":
            args = event.get("args", {})
            command = args.get("command") if isinstance(args, dict) else None
            if not isinstance(command, str) or not any(command.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES):
                issues.append(_issue("unsafe_command", "diagnose must use an allowlisted TypeScript compiler command", index))
            elif SHELL_METACHARACTERS.search(command):
                issues.append(_issue("unsafe_command", "diagnose command contains shell metacharacters", index))
        if kind == "observe":
            if "exit_code" not in event or not isinstance(event["exit_code"], int):
                issues.append(_issue("invalid_observation", "observe requires an integer exit_code", index))
        if kind == "retry" and not seen_edit:
            issues.append(_issue("retry_without_edit", "retry requires an earlier edit", index))
    if not seen_final:
        issues.append(_issue("missing_final", "trajectory must end with a final event"))
    if not seen_edit:
        issues.append(_issue("missing_edit", "repair trajectory must contain an edit"))
    last_edit = max((index for index, event in enumerate(events) if isinstance(event, dict) and event.get("event") == "edit"), default=-1)
    first_edit = min((index for index, event in enumerate(events) if isinstance(event, dict) and event.get("event") == "edit"), default=len(events))
    if seen_edit and not any(isinstance(event, dict) and event.get("event") == "diagnose" for event in events[:first_edit]):
        issues.append(_issue("missing_pre_edit_diagnosis", "trajectory must diagnose before editing", first_edit))
    if seen_edit and not any(isinstance(event, dict) and event.get("event") == "diagnose" for event in events[last_edit + 1:]):
        issues.append(_issue("missing_post_edit_diagnosis", "trajectory must diagnose after the last edit", last_edit))
    successful_observation = any(
        isinstance(event, dict) and event.get("event") == "observe" and event.get("exit_code") == 0
        for event in events[last_edit + 1:]
    )
    if seen_edit and not successful_observation:
        issues.append(_issue("missing_successful_verification", "trajectory must observe exit_code 0 after its last edit"))
    return issues


def is_valid_trajectory(record: dict[str, Any]) -> bool:
    return not validate_trajectory(record)


def normalize_trajectory(value: dict[str, Any]) -> dict[str, Any]:
    """Conservatively canonicalize shorthand tool arguments for replay.

    This is an interoperability layer, not a validity bypass: callers must
    still run ``validate_trajectory`` after normalization. Only unambiguous
    fields are moved into the contract's ``args`` object.
    """
    normalized = deepcopy(value)
    trajectory = normalized.get("trajectory")
    if not isinstance(trajectory, list):
        return normalized
    for event in trajectory:
        if not isinstance(event, dict):
            continue
        kind = event.get("event")
        if kind == "diagnose" and "tool" not in event and isinstance(event.get("command"), str):
            event["tool"] = "run"
        if kind in {"inspect", "diagnose", "edit"}:
            args = event.get("args")
            if not isinstance(args, dict):
                args = {}
                event["args"] = args
            for key in ("path", "content", "command"):
                if key in event and key not in args:
                    args[key] = event.pop(key)
            if kind == "diagnose" and isinstance(args.get("command"), str):
                args["command"] = args["command"].removesuffix(" using tsconfig.json")
            if kind == "edit" and isinstance(args.get("content"), str) and "\\n" in args["content"] and "\n" not in args["content"]:
                args["content"] = args["content"].replace("\\n", "\n")
    return normalized
