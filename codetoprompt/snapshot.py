"""Snapshot and diff functionality for CodeToPrompt.

Creates a JSON snapshot of a local project, and computes a diff between
current state and a previous snapshot, without relying on git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import difflib
import platform
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from .core import CodeToPrompt
from .config import load_config, show_config_panel
from .utils import is_url, is_text_file, should_skip_path
from .version import __version__

try:
    import pyperclip
    HAS_PYPERCLIP = True
except Exception:
    HAS_PYPERCLIP = False


try:
    import tiktoken
    _TOKENIZER = tiktoken.get_encoding("cl100k_base")
except Exception:
    _TOKENIZER = None


@dataclass
class SnapshotFile:
    path: str  # relative path within root
    size: int
    mtime: float
    sha256: str
    is_text: bool
    content: Optional[str]  # present for text files; None for binary or oversized


def _sha256_bytes(data: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def _read_text_content(file_path: Path) -> str:
    """
    Read text content with reasonable fallbacks, preserving empty files as "".
    Does not inject line numbers.
    """
    encodings = ["utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            return file_path.read_text(encoding=enc, errors="strict")
        except Exception:
            continue
    try:
        return file_path.read_bytes().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _scan_files_with_scanner(root_dir: Path, include_patterns: Optional[List[str]], exclude_patterns: Optional[List[str]], respect_gitignore: bool) -> List[Path]:
    """
    Use CodeToPrompt's scanning and inclusion logic to get files to consider.
    This ensures consistency with how the tool normally processes a project.
    """
    scanner = CodeToPrompt(
        target=str(root_dir),
        include_patterns=include_patterns if include_patterns is not None else None,
        exclude_patterns=exclude_patterns if exclude_patterns is not None else None,
        respect_gitignore=respect_gitignore,
        show_line_numbers=False,
        compress=False,
    )
    return scanner._get_files_to_process()


def _should_inline_content(path: Path, max_bytes: int, max_lines: int) -> bool:
    try:
        if max_bytes and path.stat().st_size > max_bytes:
            return False
        if max_lines:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for i, _ in enumerate(f, start=1):
                    if i > max_lines:
                        return False
    except Exception:
        # On any error reading, default to not inlining to avoid huge content
        return False
    return True


def create_snapshot_data(root_dir: Path, include_patterns: Optional[List[str]], exclude_patterns: Optional[List[str]], respect_gitignore: bool) -> Dict[str, Any]:
    """Create in-memory snapshot data for the given directory."""
    cfg = load_config()
    max_bytes = int(cfg.get("snapshot_max_bytes") or 0)
    max_lines = int(cfg.get("snapshot_max_lines") or 0)

    files: List[SnapshotFile] = []
    for path in _scan_files_with_scanner(root_dir, include_patterns, exclude_patterns, respect_gitignore):
        try:
            rel = str(path.relative_to(root_dir))
        except Exception:
            rel = str(path)

        try:
            raw = path.read_bytes()
        except Exception:
            continue

        text = is_text_file(path)
        content: Optional[str] = None
        if text and _should_inline_content(path, max_bytes, max_lines):
            content = _read_text_content(path)
        files.append(
            SnapshotFile(
                path=rel,
                size=path.stat().st_size,
                mtime=path.stat().st_mtime,
                sha256=_sha256_bytes(raw),
                is_text=text,
                content=content if text else None,
            )
        )

    snapshot: Dict[str, Any] = {
        "schema_version": 1,
        "tool_version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root_dir": str(root_dir),
        "respect_gitignore": respect_gitignore,
        "include_patterns": include_patterns or [],
        "exclude_patterns": exclude_patterns or [],
        "snapshot_max_bytes": max_bytes,
        "snapshot_max_lines": max_lines,
        "files": [f.__dict__ for f in files],
    }
    return snapshot


def save_snapshot_to_file(snapshot: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)


def load_snapshot(snapshot_path: Path) -> Dict[str, Any]:
    with open(snapshot_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_snapshot_command(args: argparse.Namespace, console: Console) -> int:
    """CLI handler to create a snapshot JSON for a local directory."""
    if is_url(args.target):
        console.print("[red]Error:[/red] Snapshot is only supported for local directories, not URLs.")
        return 1

    root = Path(args.target).resolve()
    if not root.exists() or not root.is_dir():
        console.print(f"[red]Error:[/red] '{args.target}' is not a valid directory.")
        return 1

    if not args.output:
        console.print("[red]Error:[/red] --output <snapshot.json> is required for the snapshot command.")
        return 1

    config = load_config()
    include_patterns = [p.strip() for p in args.include.split(',')] if args.include else config["include_patterns"]
    exclude_patterns = [p.strip() for p in args.exclude.split(',')] if args.exclude else config["exclude_patterns"]
    respect_gitignore = args.respect_gitignore if args.respect_gitignore is not None else config.get("respect_gitignore", True)

    display_config = {
        "Root Directory": str(root),
        "Include Patterns": include_patterns or ['*'],
        "Exclude Patterns": exclude_patterns or [],
        "Respect .gitignore": respect_gitignore,
        "Output File": str(Path(args.output).resolve()),
        "Snapshot Max Bytes": config.get("snapshot_max_bytes"),
        "Snapshot Max Lines": config.get("snapshot_max_lines"),
    }
    show_config_panel(console, display_config, "Create Snapshot")

    snapshot = create_snapshot_data(root, include_patterns, exclude_patterns, respect_gitignore)
    save_snapshot_to_file(snapshot, Path(args.output))

    panel = Panel.fit(
        f"[bold]Snapshot created:[/bold] {args.output}\n[bold]Files captured:[/bold] {len(snapshot['files'])}",
        title="Snapshot Complete",
        border_style="green",
    )
    console.print(panel)
    return 0


def _build_current_index(root_dir: Path, include_patterns: Optional[List[str]], exclude_patterns: Optional[List[str]], respect_gitignore: bool) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for path in _scan_files_with_scanner(root_dir, include_patterns, exclude_patterns, respect_gitignore):
        rel = str(path.relative_to(root_dir))
        try:
            raw = path.read_bytes()
        except Exception:
            # Skip unreadable
            continue
        index[rel] = {
            "path": rel,
            "size": path.stat().st_size,
            "mtime": path.stat().st_mtime,
            "sha256": _sha256_bytes(raw),
            "is_text": is_text_file(path),
            # content loaded lazily for text files below
        }
    return index


def _unified_diff(old_text: str, new_text: str, rel_path: str) -> str:
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm="",
        n=3,
    )
    return "\n".join(diff)


def _count_tokens(text: str) -> int:
    if _TOKENIZER is None:
        # Fallback approximation: whitespace tokenization
        return len(text.split()) if text else 0
    try:
        return len(_TOKENIZER.encode(text, disallowed_special=()))
    except Exception:
        return len(text.split()) if text else 0


def _copy_text_to_clipboard(text: str, console: Console) -> bool:
    """Copy text to the system clipboard with Linux fallbacks. Returns True on success."""
    # Prefer pyperclip if available and functional
    if HAS_PYPERCLIP:
        # On Linux, ensure xclip or wl-copy exists to avoid silent failures
        if platform.system() == "Linux":
            has_tool = False
            for tool in ("xclip", "wl-copy"):
                try:
                    subprocess.run(["which", tool], check=True, capture_output=True)
                    has_tool = True
                    break
                except Exception:
                    continue
            if not has_tool:
                # Try anyway; pyperclip may have another backend
                pass
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            pass

    # Linux direct fallbacks
    if platform.system() == "Linux":
        try:
            # Try wl-copy first
            subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
            return True
        except Exception:
            try:
                subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True)
                return True
            except Exception:
                pass
    return False


def run_diff_command(args: argparse.Namespace, console: Console) -> int:
    """CLI handler to show diff against a previous snapshot JSON for a local directory."""
    if is_url(args.target):
        console.print("[red]Error:[/red] Diff is only supported for local directories, not URLs.")
        return 1

    root = Path(args.target).resolve()
    if not root.exists() or not root.is_dir():
        console.print(f"[red]Error:[/red] '{args.target}' is not a valid directory.")
        return 1

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        console.print(f"[red]Error:[/red] Snapshot file not found: {args.snapshot}")
        return 1

    snapshot = load_snapshot(snapshot_path)
    include_patterns = snapshot.get("include_patterns") if args.use_snapshot_filters else ([p.strip() for p in args.include.split(',')] if args.include else load_config().get("include_patterns"))
    exclude_patterns = snapshot.get("exclude_patterns") if args.use_snapshot_filters else ([p.strip() for p in args.exclude.split(',')] if args.exclude else load_config().get("exclude_patterns"))
    respect_gitignore = snapshot.get("respect_gitignore") if args.use_snapshot_filters else (args.respect_gitignore if args.respect_gitignore is not None else load_config().get("respect_gitignore", True))

    display_config = {
        "Root Directory": str(root),
        "Using Snapshot Filters": bool(args.use_snapshot_filters),
        "Include Patterns": include_patterns or ['*'],
        "Exclude Patterns": exclude_patterns or [],
        "Respect .gitignore": respect_gitignore,
        "Snapshot File": str(snapshot_path.resolve()),
    }
    show_config_panel(console, display_config, "Diff Against Snapshot")

    prev_files: Dict[str, Dict[str, Any]] = {f["path"]: f for f in snapshot.get("files", [])}
    curr_index = _build_current_index(root, include_patterns, exclude_patterns, respect_gitignore)

    prev_paths = set(prev_files.keys())
    curr_paths = set(curr_index.keys())

    added = sorted(curr_paths - prev_paths)
    deleted = sorted(prev_paths - curr_paths)
    common = sorted(prev_paths & curr_paths)

    modified: List[str] = []
    diffs: List[str] = []

    for rel in common:
        prev = prev_files[rel]
        curr = curr_index[rel]
        if prev.get("sha256") != curr.get("sha256"):
            modified.append(rel)
            if prev.get("is_text") and curr.get("is_text"):
                # Load current text
                curr_text = _read_text_content(root / rel)
                prev_text = prev.get("content", "") or ""
                unified = _unified_diff(prev_text, curr_text, rel)
                if unified:
                    diffs.append(unified)
                else:
                    diffs.append(f"diff --git a/{rel} b/{rel}\n(no textual changes detected)")
            else:
                diffs.append(f"Binary files differ: a/{rel} b/{rel}")

    # Compose full textual output for clipboard/file
    lines: List[str] = []
    lines.append("Diff Summary")
    lines.append(f"Added: {len(added)}")
    lines.append(f"Deleted: {len(deleted)}")
    lines.append(f"Modified: {len(modified)}")
    # Append detailed sections and unified diffs to the clipboard/file text only
    if added:
        lines.append("\n# Added")
        lines.extend([f"A\t{p}" for p in added])
    if deleted:
        lines.append("\n# Deleted")
        lines.extend([f"D\t{p}" for p in deleted])
    if modified:
        lines.append("\n# Modified")
        lines.extend([f"M\t{p}" for p in modified])
    if diffs:
        lines.append("\n# Diffs")
        lines.extend(diffs)
    diff_text = "\n".join(lines).strip()
    diff_tokens = _count_tokens(diff_text)

    # Print only a concise summary to console (avoid large diffs in terminal)
    destination = "clipboard"
    if getattr(args, "output", None):
        destination = str(Path(args.output).resolve())
    summary = Panel.fit(
        f"[bold]Added:[/bold] {len(added)}\n[bold]Deleted:[/bold] {len(deleted)}\n[bold]Modified:[/bold] {len(modified)}\n[bold]Diff Tokens:[/bold] {diff_tokens:,}\n[bold]Output Destination:[/bold] {destination}",
        title="Diff Summary",
        border_style="cyan",
    )
    console.print(summary)

    if getattr(args, "output", None):
        try:
            Path(args.output).write_text(diff_text, encoding="utf-8")
            console.print(Panel.fit(f"[green]Diff written to:[/] {args.output}", border_style="green"))
        except Exception as e:
            console.print(Panel.fit(f"[red]Failed to write diff:[/] {e}", border_style="red"))
    else:
        copied = _copy_text_to_clipboard(diff_text, console)
        if copied:
            console.print(Panel.fit("[green]Diff copied to clipboard[/green]", border_style="green"))
        else:
            console.print(Panel.fit("[yellow]Could not copy diff to clipboard. Install xclip or wl-clipboard on Linux, or ensure clipboard access is available.[/yellow]", border_style="yellow"))

    return 0 