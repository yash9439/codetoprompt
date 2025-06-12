"""Utility functions for code to prompt conversion."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


def get_git_info(root_dir: Path) -> Optional[PathSpec]:
    """Get git ignore patterns from .gitignore file.

    Args:
        root_dir: Root directory to look for .gitignore

    Returns:
        PathSpec object if .gitignore exists, None otherwise
    """
    gitignore_path = root_dir / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            return PathSpec.from_lines(GitWildMatchPattern, f)
    return None


def build_file_tree(root_dir: Path, git_info: Optional[PathSpec] = None) -> List[Path]:
    """Build a list of files to process.

    Args:
        root_dir: Root directory to process
        git_info: PathSpec object from .gitignore

    Returns:
        List of file paths to process
    """
    files = []
    for path in root_dir.rglob("*"):
        if path.is_file():
            # Skip files that match gitignore patterns
            if git_info and git_info.match_file(str(path.relative_to(root_dir))):
                continue
            # Skip hidden files and directories
            if any(part.startswith(".") for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def process_file(file_path: Path, show_line_numbers: bool = True) -> Optional[str]:
    """Process a single file and return its contents.

    Args:
        file_path: Path to the file
        show_line_numbers: Whether to show line numbers

    Returns:
        Processed file contents or None if file couldn't be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return None

        if show_line_numbers:
            lines = content.splitlines()
            numbered_lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
            return "\n".join(numbered_lines)

        return content
    except Exception:
        return None


def generate_prompt(
    file_tree: List[Path],
    file_contents: Dict[Path, str],
    git_info: Optional[PathSpec] = None,
) -> str:
    """Generate the final prompt from processed files.

    Args:
        file_tree: List of files to include
        file_contents: Dictionary mapping file paths to their contents
        git_info: PathSpec object from .gitignore

    Returns:
        The generated prompt
    """
    prompt_parts = []

    # Add gitignore info if available
    if git_info:
        prompt_parts.append("Files matching .gitignore patterns have been excluded.\n")

    # Add tree representation
    from rich.tree import Tree
    from rich.console import Console
    console = Console()
    
    # Handle empty file tree
    if not file_tree:
        prompt_parts.append("No files found in the specified directory.")
        return "\n".join(prompt_parts)
        
    root_path = file_tree[0].parent.parent  # Get the actual root directory
    tree = Tree(f"📁 {root_path.name}")
    
    def build_tree(path: Path, tree: Tree, current_depth: int = 0, max_depth: int = 3) -> None:
        """Build a tree representation of the codebase.
        
        Args:
            path: Current directory path
            tree: Current tree node
            current_depth: Current depth in the tree
            max_depth: Maximum depth to traverse
        """
        if current_depth >= max_depth:
            tree.add("... (depth limit reached)")
            return
            
        # Sort items: directories first, then files
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for item in items:
                # Skip hidden files and directories
                if any(part.startswith(".") for part in item.parts):
                    continue
                    
                if item.is_dir():
                    branch = tree.add(f"📁 {item.name}")
                    build_tree(item, branch, current_depth + 1, max_depth)
                else:
                    tree.add(f"📄 {item.name}")
        except Exception as e:
            tree.add(f"Error reading directory: {str(e)}")

    build_tree(root_path, tree)
    with console.capture() as capture:
        console.print(tree)
    prompt_parts.append("Project Structure:")
    prompt_parts.append(capture.get())
    prompt_parts.append("\n")

    # Add each file's contents
    for file_path in file_tree:
        if file_path in file_contents:
            rel_path = file_path.relative_to(root_path)
            prompt_parts.append(f"Relative File Path: {rel_path}\n")
            prompt_parts.append("```")
            prompt_parts.append(file_contents[file_path])
            prompt_parts.append("```\n")

    return "\n".join(prompt_parts)


def process_files(
    directory: Path,
    show_line_numbers: bool = True,
    respect_gitignore: bool = True,
    output_file: Optional[str] = None,
    count_tokens: bool = False,
    copy_to_clipboard: bool = True,
) -> str:
    """Process all files in a directory and generate a prompt.

    Args:
        directory: Directory to process
        show_line_numbers: Whether to show line numbers
        respect_gitignore: Whether to respect .gitignore rules
        output_file: Optional output file path
        count_tokens: Whether to count tokens in the output
        copy_to_clipboard: Whether to copy the prompt to clipboard

    Returns:
        str: The generated prompt
    """
    # Get git info if needed
    git_info = get_git_info(directory) if respect_gitignore else None

    # Build file tree
    file_tree = build_file_tree(directory, git_info)

    # Process each file
    file_contents = {}
    for file_path in file_tree:
        if file_path.is_file():
            content = process_file(file_path, show_line_numbers)
            if content:
                file_contents[file_path] = content

    # Generate the final prompt
    prompt = generate_prompt(file_tree, file_contents, git_info)

    # Count tokens if requested
    if count_tokens:
        token_count = len(prompt.split())
        print(f"\nToken count: {token_count}")

    # Copy to clipboard if requested
    if copy_to_clipboard:
        try:
            import pyperclip
            pyperclip.copy(prompt)
            print("\n✓ Prompt copied to clipboard")
        except Exception as e:
            print(f"\nWarning: Could not copy to clipboard: {e}")

    # Save to file or print to stdout
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"\nPrompt saved to: {output_file}")
    print("✅ Done. Ran successfully")

    # Store prompt as attribute for access in CLI
    process_files.prompt = prompt
    return prompt
