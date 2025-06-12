import os
import pygit2
import tiktoken
import pyperclip
from pathlib import Path
from typing import List, Optional, Set
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from rich.console import Console
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from concurrent.futures import ThreadPoolExecutor
import threading
import platform
import subprocess

class CodeToPrompt:
    def __init__(
        self,
        root_dir: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        respect_gitignore: bool = True,
        show_line_numbers: bool = True,
        max_tokens: Optional[int] = None,
    ):
        self.root_dir = Path(root_dir).resolve()
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.respect_gitignore = respect_gitignore
        self.show_line_numbers = show_line_numbers
        self.max_tokens = max_tokens
        self.console = Console()
        
        # Initialize git repository if exists
        try:
            self.repo = pygit2.Repository(str(self.root_dir))
        except pygit2.GitError:
            self.repo = None
            
        # Initialize tokenizer with special token handling
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        # Allow all special tokens to be processed as normal text
        self.tokenizer.allowed_special = set()
        self.tokenizer.disallowed_special = set()
        
        # Initialize pathspec for gitignore
        if self.respect_gitignore and self.repo:
            gitignore_path = self.root_dir / ".gitignore"
            if gitignore_path.exists():
                with open(gitignore_path) as f:
                    self.gitignore = PathSpec.from_lines(GitWildMatchPattern, f)
            else:
                self.gitignore = None
        else:
            self.gitignore = None

    def _check_clipboard_requirements(self) -> bool:
        """Check if clipboard requirements are met."""
        if platform.system() == "Linux":
            try:
                # Check if xclip is installed
                subprocess.run(["which", "xclip"], check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError:
                self.console.print("\n[yellow]⚠️  Clipboard functionality is disabled because xclip is not installed.[/yellow]")
                self.console.print("\n[yellow]To enable clipboard support, run this command:[/yellow]")
                self.console.print("\n[bold cyan]sudo apt-get install xclip[/bold cyan]")
                self.console.print("\n[yellow]After installing xclip, run codetoprompt again to use clipboard functionality.[/yellow]\n")
                return False
        return True

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included based on patterns and gitignore."""
        rel_path = file_path.relative_to(self.root_dir)
        
        # Check include patterns
        if not any(rel_path.match(pattern) for pattern in self.include_patterns):
            return False
            
        # Check exclude patterns
        if any(rel_path.match(pattern) for pattern in self.exclude_patterns):
            return False
            
        # Check gitignore
        if self.gitignore and self.gitignore.match_file(str(rel_path)):
            return False
            
        return True

    def _get_file_content(self, file_path: Path) -> str:
        """Read and format file content with optional line numbers."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if self.show_line_numbers:
                lines = content.splitlines()
                numbered_lines = [f"{i+1:4d} | {line}" for i, line in enumerate(lines)]
                return "\n".join(numbered_lines)
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _get_git_info(self) -> str:
        """Get git repository information."""
        if not self.repo:
            return ""
            
        info = []
        try:
            head = self.repo.head
            info.append(f"Current branch: {head.name}")
            info.append(f"Latest commit: {head.target.hex}")
            info.append(f"Author: {head.peel().author.name} <{head.peel().author.email}>")
            info.append(f"Date: {head.peel().author.time}")
            info.append(f"Message: {head.peel().message.strip()}")
        except Exception as e:
            info.append(f"Error getting git info: {str(e)}")
            
        return "\n".join(info)

    def _process_file(self, file_path: Path) -> tuple:
        """Process a single file and return its content."""
        rel_path = file_path.relative_to(self.root_dir)
        content = self._get_file_content(file_path)
        return (rel_path, content)

    def generate_prompt(self, progress: Optional[Progress] = None) -> str:
        """Generate the prompt from the codebase."""
        prompt_parts = []
        
        # Add git information if available
        git_info = self._get_git_info()
        if git_info:
            prompt_parts.append("=== Git Repository Information ===")
            prompt_parts.append(git_info)
            prompt_parts.append("")
            
        # Add file tree
        prompt_parts.append("=== File Structure ===")
        tree = Tree("📁 " + str(self.root_dir.name))
        self._build_tree(self.root_dir, tree)
        # Convert tree to string using rich's console
        console = Console(width=100)  # Set a reasonable width
        with console.capture() as capture:
            console.print(tree)
        prompt_parts.append(capture.get())
        prompt_parts.append("")
            
        # Get all files
        files = list(self._get_files())
            
        # Process files in parallel
        prompt_parts.append("=== File Contents ===")
            
        with ThreadPoolExecutor() as executor:
            for rel_path, content in executor.map(self._process_file, files):
                prompt_parts.append(f"\n=== {rel_path} ===")
                prompt_parts.append(content)
            
        prompt = "\n".join(prompt_parts)
        
        # Check token limit
        if self.max_tokens:
            tokens = self.tokenizer.encode(prompt)
            if len(tokens) > self.max_tokens:
                self.console.print(f"[yellow]Warning: Prompt exceeds {self.max_tokens} tokens ({len(tokens)} tokens)[/yellow]")
                
        return prompt

    def _build_tree(self, path: Path, tree: Tree) -> None:
        """Build a tree representation of the codebase."""
        for item in sorted(path.iterdir()):
            if item.is_dir():
                if self._should_include_file(item):
                    branch = tree.add(f"📁 {item.name}")
                    self._build_tree(item, branch)
            else:
                if self._should_include_file(item):
                    tree.add(f"📄 {item.name}")

    def _get_files(self) -> Set[Path]:
        """Get all files that should be included in the prompt."""
        files = set()
        for pattern in self.include_patterns:
            files.update(self.root_dir.glob(f"**/{pattern}"))
        return {f for f in files if f.is_file() and self._should_include_file(f)}

    def save_to_file(self, output_path: str) -> None:
        """Save the generated prompt to a file."""
        prompt = self.generate_prompt()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(prompt)

    def copy_to_clipboard(self) -> bool:
        """Copy the generated prompt to clipboard. Returns True if successful."""
        # Check clipboard requirements first, before any progress bars
        if not self._check_clipboard_requirements():
            return False
            
        prompt = self.generate_prompt()
        try:
            pyperclip.copy(prompt)
            return True
        except Exception as e:
            self.console.print(f"[red]Error copying to clipboard: {str(e)}[/red]")
            return False

    def get_token_count(self) -> int:
        """Get the number of tokens in the generated prompt."""
        prompt = self.generate_prompt()
        return len(self.tokenizer.encode(prompt)) 