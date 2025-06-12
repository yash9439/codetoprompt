from typing import List, Optional, Dict
import pyperclip
from rich.progress import Progress
import os
import fnmatch
import pathspec


def process_files(
    root_dir: str,
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None,
    respect_gitignore: bool = True,
    show_line_numbers: bool = True,
    max_tokens: Optional[int] = None,
    copy_to_clipboard: bool = True,
    output_file: Optional[str] = None,
) -> str:
    """Process files and generate a prompt."""
    if include_patterns is None:
        include_patterns = ["*"]
    if exclude_patterns is None:
        exclude_patterns = []

    with Progress() as progress:
        # Get git information first
        git_task = progress.add_task("Getting git information...", total=1)
        git_info = get_git_info(root_dir) if respect_gitignore else None
        progress.update(git_task, completed=1)

        # Build file tree
        tree_task = progress.add_task("Building file tree...", total=1)
        file_tree = build_file_tree(root_dir, git_info)
        progress.update(tree_task, completed=1)

        # Find files to process
        find_task = progress.add_task("Finding files...", total=1)
        files = find_files(
            root_dir,
            include_patterns,
            exclude_patterns,
            respect_gitignore,
            git_info,
        )
        progress.update(find_task, completed=1)

        # Process files
        process_task = progress.add_task("Processing files...", total=len(files))
        file_contents = []
        total_tokens = 0

        for file_path in files:
            try:
                content = process_file(file_path, show_line_numbers)
                if content:
                    file_contents.append(content)
                    # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
                    total_tokens += len(content) // 4
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
            progress.update(process_task, advance=1)

    # Generate final prompt
    prompt = generate_prompt(file_tree, file_contents, git_info)

    # Handle token limit
    if max_tokens and total_tokens > max_tokens:
        print(f"Warning: Prompt exceeds {max_tokens} tokens ({total_tokens} tokens)")
        # TODO: Implement token limiting logic

    # Copy to clipboard if requested
    if copy_to_clipboard:
        try:
            pyperclip.copy(prompt)
            print("✓ Prompt copied to clipboard")
        except Exception as e:
            print(f"Warning: Could not copy to clipboard: {e}")

    # Save to file if requested
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(prompt)
            print(f"✓ Prompt saved to {output_file}")
        except Exception as e:
            print(f"Error saving to file: {e}")

    # Print summary
    print("\n╭── Processing Complete ───╮")
    print("│ Summary:                 │")
    print(f"│ Total Tokens: {total_tokens:,}      │")
    print(f"│ Output File: {output_file or 'None'}        │")
    print(f"│ Copied to Clipboard: {'Yes' if copy_to_clipboard else 'No'} │")
    print("╰──────────────────────────╯")

    return prompt


def find_files(
    root_dir: str,
    include_patterns: List[str],
    exclude_patterns: List[str],
    respect_gitignore: bool = True,
    git_info: Optional[Dict] = None,
) -> List[str]:
    """Find files to process based on patterns and gitignore rules."""
    files = []
    spec = pathspec.PathSpec.from_lines(
        "gitwildmatch", exclude_patterns if exclude_patterns else []
    )

    # Get gitignore patterns if needed
    gitignore_patterns = []
    if respect_gitignore and git_info and git_info.get("gitignore_patterns"):
        gitignore_patterns = git_info["gitignore_patterns"]

    # Combine gitignore patterns with exclude patterns
    all_exclude_patterns = exclude_patterns + gitignore_patterns
    exclude_spec = pathspec.PathSpec.from_lines("gitwildmatch", all_exclude_patterns)

    # Walk through directory
    for root, _, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, root_dir)

            # Check if file matches include patterns
            if not any(
                fnmatch.fnmatch(rel_path, pattern.strip())
                for pattern in include_patterns
            ):
                continue

            # Check if file matches exclude patterns
            if exclude_spec.match_file(rel_path):
                continue

            files.append(file_path)

    return sorted(files)
