import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from rich.console import Console
from rich.tree import Tree
from rich.progress import Progress

from .utils import is_text_file, should_skip_path, read_file_safely

try:
    import pygit2
    HAS_PYGIT2 = True
except ImportError:
    HAS_PYGIT2 = False

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


class CodeToPrompt:
    """Convert code files to prompt format."""

    def __init__(
        self,
        root_dir: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        respect_gitignore: bool = True,
        show_line_numbers: bool = True,
        max_tokens: Optional[int] = None,
        tree_depth: int = 5,
    ):
        self.root_dir = Path(root_dir).resolve()
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.respect_gitignore = respect_gitignore
        self.show_line_numbers = show_line_numbers
        self.max_tokens = max_tokens
        self.tree_depth = tree_depth
        self.console = Console()
        
        # Initialize components
        self.repo = self._get_git_repo()
        self.tokenizer = self._get_tokenizer()
        self.gitignore_root: Optional[Path] = None
        self.gitignore = self._get_gitignore_spec()
        
        self.processed_files: Dict[Path, Dict[str, Any]] = {}
        self._generated_prompt: Optional[str] = None
        self._files_processed = False

    def _get_git_repo(self):
        """Get git repository if available."""
        if not HAS_PYGIT2:
            return None
        try:
            return pygit2.Repository(str(self.root_dir))
        except pygit2.GitError:
            return None

    def _get_tokenizer(self):
        """Get tokenizer if available."""
        if not HAS_TIKTOKEN:
            return None
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None

    def _get_gitignore_spec(self):
        """Get gitignore patterns if available."""
        if not self.respect_gitignore:
            return None
        
        base_path = self.root_dir
        if self.repo and self.repo.workdir:
            base_path = Path(self.repo.workdir)

        gitignore_path = base_path / ".gitignore"
        if not gitignore_path.exists():
            return None
        
        self.gitignore_root = base_path
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                return PathSpec.from_lines(GitWildMatchPattern, f)
        except Exception:
            return None

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included."""
        if should_skip_path(file_path, self.root_dir):
            return False
        
        if not file_path.is_file() or not is_text_file(file_path):
            return False
        
        rel_path_to_root = file_path.relative_to(self.root_dir)
        
        # Check include patterns
        if self.include_patterns and not any(rel_path_to_root.match(pattern) for pattern in self.include_patterns):
            return False
        
        # Check exclude patterns
        if any(rel_path_to_root.match(pattern) for pattern in self.exclude_patterns):
            return False
        
        # Check gitignore
        if self.gitignore and self.gitignore_root:
            try:
                rel_path_for_gitignore = file_path.relative_to(self.gitignore_root)
                if self.gitignore.match_file(str(rel_path_for_gitignore)):
                    return False
            except ValueError:
                # File is not under the gitignore root, so gitignore rules don't apply
                pass
        
        return True

    def _process_files(self, progress: Optional[Progress] = None):
        """Process all files to populate statistics, without generating the prompt."""
        if self._files_processed:
            return

        files = self._get_files_to_process()
        if progress:
            task = progress.add_task("Processing files...", total=len(files))
        
        for file_path in files:
            content = read_file_safely(file_path, self.show_line_numbers)
            if content:
                # Store stats for each file
                file_token_count = 0
                if self.tokenizer:
                    file_token_count = len(self.tokenizer.encode(content, disallowed_special=()))
                else:
                    file_token_count = int(len(content.split()) * 0.75)
                
                self.processed_files[file_path] = {
                    "content": content,
                    "tokens": file_token_count,
                    "lines": len(content.splitlines())
                }
            if progress:
                progress.update(task, advance=1)
        
        self._files_processed = True

    def _get_git_info(self) -> str:
        """Get git repository information."""
        if not self.repo or self.repo.is_empty:
            return ""
        
        try:
            head = self.repo.head
            commit = head.peel()
            return (
                f"Current branch: {head.shorthand}\n"
                f"Latest commit: {commit.hex[:8]}\n"
                f"Author: {commit.author.name} <{commit.author.email}>\n"
                f"Message: {commit.message.strip()}"
            )
        except Exception:
            return ""

    def _build_tree_structure(self) -> str:
        """Build visual tree representation."""
        tree = Tree(f"📁 {self.root_dir.name}")
        self._add_to_tree(self.root_dir, tree, 0)
        
        with self.console.capture() as capture:
            self.console.print(tree)
        return capture.get()

    def _add_to_tree(self, path: Path, tree_node: Tree, depth: int):
        """Recursively add items to tree."""
        if depth >= self.tree_depth:
            tree_node.add("... (depth limit reached)")
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if should_skip_path(item, self.root_dir):
                    continue
                
                if item.is_dir():
                    branch = tree_node.add(f"📁 {item.name}")
                    self._add_to_tree(item, branch, depth + 1)
                elif self._should_include_file(item):
                    tree_node.add(f"📄 {item.name}")
        except PermissionError:
            tree_node.add("❌ Permission denied")

    def _get_files_to_process(self) -> List[Path]:
        """Get list of files to process."""
        files = []
        for file_path in self.root_dir.rglob("*"):
            if self._should_include_file(file_path):
                files.append(file_path)
        return sorted(files)

    def generate_prompt(self, progress: Optional[Progress] = None) -> str:
        """Generate prompt from codebase."""
        if self._generated_prompt:
            return self._generated_prompt

        self._process_files(progress)

        parts = []

        # Add git info
        git_info = self._get_git_info()
        if git_info:
            parts.extend(["Git Repository Information:", git_info, ""])

        # Add project structure
        parts.extend(["Project Structure:", self._build_tree_structure(), ""])

        if not self.processed_files:
            parts.append("No files found matching the specified criteria.")
        else:
            sorted_files = sorted(self.processed_files.keys())
            for file_path in sorted_files:
                content = self.processed_files[file_path]["content"]
                rel_path = file_path.relative_to(self.root_dir)
                parts.extend([
                    f"Relative File Path: {rel_path}",
                    "", "```", content, "```", ""
                ])

        self._generated_prompt = "\n".join(parts)
        
        if self.max_tokens and self.get_token_count() > self.max_tokens:
            self.console.print(f"[yellow]Warning: Prompt exceeds token limit[/yellow]")

        return self._generated_prompt

    def analyze(self, progress: Optional[Progress] = None, top_n: int = 20) -> Dict[str, Any]:
        """Runs a full analysis of the codebase."""
        self._process_files(progress)

        # Overall stats
        total_tokens = sum(d['tokens'] for d in self.processed_files.values())
        total_lines = sum(d['lines'] for d in self.processed_files.values())

        # Per-extension stats
        extension_stats: Dict[str, Dict[str, int]] = {}
        for path, data in self.processed_files.items():
            ext = path.suffix if path.suffix else ".<no_ext>"
            if ext not in extension_stats:
                extension_stats[ext] = {"file_count": 0, "tokens": 0, "lines": 0}
            extension_stats[ext]["file_count"] += 1
            extension_stats[ext]["tokens"] += data["tokens"]
            extension_stats[ext]["lines"] += data["lines"]

        sorted_extensions = sorted(
            extension_stats.items(), key=lambda item: item[1]["tokens"], reverse=True
        )

        # Top files by tokens and lines
        sorted_by_tokens = sorted(
            self.processed_files.items(), key=lambda item: item[1]["tokens"], reverse=True
        )
        
        return {
            "overall": {
                "file_count": len(self.processed_files),
                "total_tokens": total_tokens,
                "total_lines": total_lines,
            },
            "by_extension": [
                {"extension": ext, **stats} for ext, stats in sorted_extensions[:top_n]
            ],
            "top_files_by_tokens": [
                {"path": p.relative_to(self.root_dir), "tokens": d["tokens"], "lines": d["lines"]}
                for p, d in sorted_by_tokens[:top_n]
            ],
        }

    def save_to_file(self, output_path: str):
        """Save prompt to file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.generate_prompt())

    def copy_to_clipboard(self) -> bool:
        """Copy prompt to clipboard."""
        if not HAS_PYPERCLIP:
            self.console.print("[yellow]Warning: pyperclip is not installed. Skipping clipboard.[/yellow]")
            return False
        
        if platform.system() == "Linux":
            try:
                subprocess.run(["which", "xclip"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(["which", "wl-copy"], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.console.print("[yellow]Warning: xclip or wl-clipboard not found. Skipping clipboard.[/yellow]")
                    return False
        
        try:
            pyperclip.copy(self.generate_prompt())
            return True
        except Exception as e:
            self.console.print(f"[red]Could not copy to clipboard:[/red] {e}")
            return False

    def get_token_count(self) -> int:
        """Get token count of prompt."""
        if not self._files_processed:
            self._process_files()
        return sum(d.get('tokens', 0) for d in self.processed_files.values())

    def get_top_files_by_tokens(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get the top files sorted by token count."""
        self._process_files() # Ensure files are processed
        if not self.processed_files:
            return []

        sorted_files = sorted(
            self.processed_files.items(),
            key=lambda item: item[1].get("tokens", 0),
            reverse=True,
        )

        top_files = []
        for path, data in sorted_files[:count]:
            top_files.append({
                "path": path.relative_to(self.root_dir),
                "tokens": data.get("tokens", 0)
            })
        return top_files

    def get_top_extensions_by_tokens(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the top file extensions sorted by token count."""
        self._process_files() # Ensure files are processed
        if not self.processed_files:
            return []

        extension_tokens: Dict[str, int] = {}
        for path, data in self.processed_files.items():
            ext = path.suffix if path.suffix else ".<no_ext>"
            extension_tokens[ext] = extension_tokens.get(ext, 0) + data.get("tokens", 0)

        sorted_extensions = sorted(
            extension_tokens.items(),
            key=lambda item: item[1],
            reverse=True
        )
        
        return [{"extension": ext, "tokens": tokens} for ext, tokens in sorted_extensions[:count]]

    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        if not self._generated_prompt:
            self.generate_prompt()
        
        return {
            'files_processed': len(self.processed_files),
            'total_characters': len(self._generated_prompt),
            'total_tokens': self.get_token_count(),
            'total_lines': self._generated_prompt.count('\n'),
        }