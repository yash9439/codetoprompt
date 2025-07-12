"""Core Functionality for CodeToPrompt."""

import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from urllib.parse import urlparse

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from rich.console import Console
from rich.tree import Tree
from rich.progress import Progress

from .utils import (
    is_text_file, should_skip_path, read_file_safely, EXT_TO_LANG,
    read_and_truncate_file, DATA_FILE_EXTENSIONS, DATA_FILE_LINE_LIMIT, is_url
)
from . import remote

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

try:
    import nbformat
    from nbconvert import PythonExporter
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False


class CodeToPrompt:
    """Convert code files or URLs to a context-rich prompt."""

    def __init__(
        self,
        target: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        respect_gitignore: bool = True,
        show_line_numbers: bool = False,
        compress: bool = False,
        max_tokens: Optional[int] = None,
        tree_depth: int = 5,
        output_format: str = "default",
        explicit_files: Optional[List[Path]] = None,
    ):
        self.console = Console()
        self.target = target
        self.is_remote = is_url(self.target)

        # Common attributes
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.show_line_numbers = show_line_numbers
        self.max_tokens = max_tokens
        self.output_format = output_format
        self.compress = compress
        
        # Local-only attributes
        self.root_dir: Optional[Path] = None
        self.respect_gitignore = respect_gitignore
        self.tree_depth = tree_depth
        self.explicit_files = explicit_files
        self.explicit_files_set: Optional[Set[Path]] = None
        self.gitignore_root: Optional[Path] = None
        self.gitignore: Optional[PathSpec] = None

        if not self.is_remote:
            self.root_dir = Path(target).resolve()
            if self.explicit_files:
                self.explicit_files_set = set(self.explicit_files)
            if self.respect_gitignore:
                self.gitignore = self._get_gitignore_spec()
                self.gitignore_root = self.root_dir if self.gitignore else None
        
        # Initialize components and state
        self.compressor = self._get_compressor() if not self.is_remote else None
        self.tokenizer = self._get_tokenizer()
        self.processed_files: Dict[Any, Dict[str, Any]] = {}
        self._generated_prompt: Optional[str] = None
        self._files_processed = False
        self.xml_index = 1

    def _get_compressor(self):
        """Get code compressor if enabled and available."""
        if not self.compress:
            return None
        try:
            from .compressor import Compressor
            return Compressor()
        except ImportError:
            self.console.print("[yellow]Warning: Compression dependencies not installed. Compression is disabled.[/yellow]")
            self.compress = False
            return None

    def _get_tokenizer(self):
        """Get tokenizer if available."""
        if not HAS_TIKTOKEN: return None
        try: return tiktoken.get_encoding("cl100k_base")
        except Exception: return None

    def _get_gitignore_spec(self):
        """Get gitignore patterns if available."""
        if not self.root_dir: return None
        gitignore_path = self.root_dir / ".gitignore"
        if not gitignore_path.exists(): return None
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                return PathSpec.from_lines(GitWildMatchPattern, f)
        except Exception:
            return None

    def _count_tokens(self, text: str) -> int:
        """Safely count tokens in a string, ignoring special tokens."""
        if not self.tokenizer:
            return 0
        # The disallowed_special=() argument prevents errors when the
        # input text contains special tokens like '<|endoftext|>'.
        return len(self.tokenizer.encode(text, disallowed_special=()))

    def generate_prompt(self, progress: Optional[Progress] = None) -> str:
        """Generate prompt from a local path or a remote URL."""
        if self._generated_prompt:
            return self._generated_prompt

        if self.is_remote:
            self._process_remote_source(progress)
        else:
            self._process_local_files(progress)

        if self.max_tokens and self.get_token_count() > self.max_tokens:
            self.console.print(f"[yellow]Warning: Prompt exceeds token limit of {self.max_tokens}[/yellow]")

        return self._generated_prompt or ""

    def _process_remote_source(self, progress: Optional[Progress] = None):
        """Fetches and formats content from a remote URL."""
        if progress:
            task = progress.add_task("Fetching remote content...", total=None)
        
        url_type = remote.get_url_type(self.target)
        
        if url_type == "github":
            data = remote.process_github_repo(self.target)
            self._populate_processed_files_from_github(data)
            self._build_github_prompt(data)
        else:
            data = remote.process_youtube_transcript(self.target) if url_type == "youtube" else remote.process_web_source(self.target)
            self._populate_processed_files_from_single_source(data)
            self._build_single_source_prompt(data)

        if progress:
            progress.stop_task(task)
            progress.refresh()
        self._files_processed = True

    def _populate_processed_files_from_github(self, data: Dict[str, Any]):
        """Populates processed_files dictionary from GitHub data."""
        self.processed_files.clear()
        for file_info in data.get('files', []):
            path_obj = Path(file_info['path'])
            content = file_info.get('content', '')
            self.processed_files[path_obj] = {
                'content': content,
                'tokens': self._count_tokens(content),
                'lines': len(content.splitlines()),
                'is_compressed': False,
            }

    def _populate_processed_files_from_single_source(self, data: Dict[str, Any]):
        """Populates processed_files for single URL sources like web pages or YouTube."""
        self.processed_files.clear()
        source_url = data.get('source', self.target)
        content = data.get('content', '')
        self.processed_files[source_url] = {
            'content': content,
            'tokens': self._count_tokens(content),
            'lines': len(content.splitlines()),
        }

    def _build_github_prompt(self, data: Dict[str, Any]):
        """Builds the final prompt string for a GitHub repository."""
        parts = []
        tree = Tree(f"📁 {urlparse(self.target).path.strip('/')}")
        self._add_paths_to_tree([Path(f['path']) for f in data.get('files', [])], tree)
        with self.console.capture() as capture:
            self.console.print(tree)
        parts.extend(["Project Structure:", capture.get(), ""])
        
        self._format_processed_files(parts)
        self._generated_prompt = "\n".join(parts).strip()
    
    def _add_paths_to_tree(self, paths: List[Path], root_node: Tree):
        """Builds a Rich Tree from a flat list of paths."""
        tree_dict: Dict = {}
        for path in paths:
            current_level = tree_dict
            for part in path.parts:
                current_level = current_level.setdefault(part, {})
        
        def build_rich_tree(d: Dict, parent_node: Tree):
            for name, children in sorted(d.items()):
                icon = "📁" if children else "📄"
                node = parent_node.add(f"{icon} {name}")
                if children:
                    build_rich_tree(children, node)
        
        build_rich_tree(tree_dict, root_node)

    def _build_single_source_prompt(self, data: Dict[str, Any]):
        """Builds the final prompt string for a single URL source."""
        source = data.get('source', self.target)
        content = data.get('content', 'No content found.')
        self._generated_prompt = f"Source: {source}\n\n---\n\n{content}"

    def _process_notebook_file(self, file_path: Path) -> Optional[str]:
        """Processes a Jupyter notebook file, extracting Python code."""
        if not HAS_NBFORMAT:
            self.console.print(f"[yellow]Warning: 'nbformat' and 'nbconvert' not installed to process notebooks. Skipping: {file_path}[/yellow]")
            return None
        
        try:
            with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
                content_str = f.read()

            if '"nbformat"' not in content_str:
                self.console.print(f"[yellow]Warning: File {file_path} has .ipynb extension but not a valid notebook. Reading as plain text.[/yellow]")
                return read_file_safely(file_path, self.show_line_numbers)
            
            notebook_node = nbformat.reads(content_str, as_version=4)
            exporter = PythonExporter()
            python_code, _ = exporter.from_notebook_node(notebook_node)
            
            if self.show_line_numbers:
                lines = python_code.splitlines()
                return '\n'.join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
            
            return python_code.strip()
        except Exception as e:
            self.console.print(f"[bold red]Error processing notebook {file_path}: {e}[/bold red]")
            return f"# ERROR PROCESSING NOTEBOOK: {e}\n"

    def _process_local_files(self, progress: Optional[Progress] = None):
        """Process all local files to populate statistics."""
        if self._files_processed: return

        files = self._get_files_to_process()
        if progress:
            task = progress.add_task("Processing files...", total=len(files))
        
        self.processed_files.clear()
        for file_path in files:
            content: Optional[str] = None
            is_compressed = False

            # Priority 1: Handle Jupyter Notebooks
            if file_path.suffix.lower() == ".ipynb":
                content = self._process_notebook_file(file_path)

            if content is None:
                # Priority 2: Truncate known data files
                if file_path.suffix.lower() in DATA_FILE_EXTENSIONS:
                    raw_content, was_truncated = read_and_truncate_file(file_path, DATA_FILE_LINE_LIMIT)
                    if raw_content is not None:
                        if self.show_line_numbers:
                            lines = raw_content.splitlines()
                            content = '\n'.join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
                        else:
                            content = raw_content.rstrip('\n')
                        if was_truncated:
                            content += f"\n... (file content truncated to first {DATA_FILE_LINE_LIMIT} lines)"
                
                # Priority 3: Try compressing (if not a data file)
                if content is None and self.compressor:
                    compressed_output = self.compressor.generate_compressed_prompt(str(file_path))
                    if compressed_output:
                        content = compressed_output
                        is_compressed = True
                
                # Priority 4: Fallback to full file read
                if content is None:
                    content = read_file_safely(file_path, self.show_line_numbers)

            if content is not None:
                file_token_count = self._count_tokens(content)
                self.processed_files[file_path] = {
                    "content": content,
                    "tokens": file_token_count,
                    "lines": len(content.splitlines()),
                    "is_compressed": is_compressed,
                }
            if progress: progress.update(task, advance=1)
        
        self._files_processed = True
        self._build_local_prompt()

    def _build_local_prompt(self):
        """Builds the final prompt string for a local directory."""
        if not self.root_dir: return
        parts = ["Project Structure:", self._build_tree_structure(), ""]
        self._format_processed_files(parts)
        self._generated_prompt = "\n".join(parts).strip()
        
    def _format_processed_files(self, parts: List[str]):
        """Shared formatting logic for a list of processed files."""
        if self.output_format == "cxml":
            parts.append("<documents>")
        
        if not self.processed_files:
            if self.is_remote:
                parts.append("No processable files found at the URL.")
            else:
                parts.append("No files found matching the specified criteria.")
        else:
            sorted_files = sorted(self.processed_files.items())
            self.xml_index = 1
            for file_path, file_data in sorted_files:
                self._format_file_content(parts, file_path, file_data)
        
        if self.output_format == "cxml":
            parts.append("</documents>")

    def _format_file_content(self, parts: List[str], file_path: Any, file_data: Dict[str, Any]):
        """Formats the content of a single file and appends to parts list."""
        content = file_data["content"]
        is_compressed = file_data.get("is_compressed", False)

        if is_compressed:
            parts.extend([content, ""])
            return

        rel_path = file_path.relative_to(self.root_dir) if not self.is_remote and self.root_dir else file_path
        lang = EXT_TO_LANG.get(Path(str(file_path)).suffix.lstrip('.'), "")
        
        if self.output_format == "default":
            parts.extend([f"Relative File Path: {rel_path}", "", f"```{lang}", content, f"```", ""])
        elif self.output_format == "markdown":
            backticks = "```"
            while backticks in content: backticks += "`"
            parts.extend([f"## {rel_path}", f"{backticks}{lang}", content, f"{backticks}", ""])
        elif self.output_format == "cxml":
            parts.extend([
                f'<document index="{self.xml_index}">', f"<source>{rel_path}</source>",
                "<document_content>", content, "</document_content>", "</document>", ""
            ])
            self.xml_index += 1

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a local file should be included."""
        if not self.root_dir: return False
        if self.explicit_files_set is not None:
            return file_path in self.explicit_files_set
        
        if should_skip_path(file_path, self.root_dir) or not file_path.is_file() or not is_text_file(file_path):
            return False
        
        rel_path = file_path.relative_to(self.root_dir)
        
        if not any(rel_path.match(p) for p in self.include_patterns): return False
        if any(rel_path.match(p) for p in self.exclude_patterns): return False
        
        if self.gitignore and self.gitignore_root:
            try:
                if self.gitignore.match_file(str(file_path.relative_to(self.gitignore_root))):
                    return False
            except ValueError: pass
        
        return True

    def _build_tree_structure(self) -> str:
        """Build visual tree representation for a local directory."""
        if not self.root_dir: return ""
        tree = Tree(f"📁 {self.root_dir.name}")
        self._add_to_tree(self.root_dir, tree, 0)
        with self.console.capture() as capture:
            self.console.print(tree)
        return capture.get()

    def _add_to_tree(self, path: Path, tree_node: Tree, depth: int):
        """Recursively add local items to tree."""
        if depth >= self.tree_depth:
            tree_node.add("... (depth limit reached)")
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if self.root_dir and should_skip_path(item, self.root_dir): continue
                if item.is_dir():
                    branch = tree_node.add(f"📁 {item.name}")
                    self._add_to_tree(item, branch, depth + 1)
                elif self._should_include_file(item):
                    tree_node.add(f"📄 {item.name}")
        except PermissionError:
            tree_node.add("❌ Permission denied")

    def _get_files_to_process(self) -> List[Path]:
        """Get list of local files to process."""
        if not self.root_dir: return []
        if self.explicit_files is not None: return sorted(self.explicit_files)

        files_to_process = []
        dirs_to_visit = [self.root_dir]
        while dirs_to_visit:
            current_dir = dirs_to_visit.pop(0)
            if should_skip_path(current_dir, self.root_dir) and current_dir != self.root_dir: continue
            try:
                for path in current_dir.iterdir():
                    if path.is_dir():
                        dirs_to_visit.append(path)
                    elif self._should_include_file(path):
                        files_to_process.append(path)
            except (PermissionError, FileNotFoundError): continue
        return sorted(files_to_process)

    def analyse(self, progress: Optional[Progress] = None, top_n: int = 10) -> Dict[str, Any]:
        """Runs a full analysis of the codebase (local only)."""
        if self.is_remote:
            raise NotImplementedError("Analysis of remote URLs is not supported.")
        if not self.root_dir: return {}
            
        self._process_local_files(progress)

        total_tokens = sum(d['tokens'] for d in self.processed_files.values())
        total_lines = sum(d['lines'] for d in self.processed_files.values())

        extension_stats: Dict[str, Dict[str, int]] = {}
        for path, data in self.processed_files.items():
            ext = path.suffix if path.suffix else ".<no_ext>"
            stats = extension_stats.setdefault(ext, {"file_count": 0, "tokens": 0, "lines": 0})
            stats["file_count"] += 1
            stats["tokens"] += data["tokens"]
            stats["lines"] += data["lines"]

        sorted_extensions = sorted(extension_stats.items(), key=lambda item: item[1]["tokens"], reverse=True)
        sorted_by_tokens = sorted(self.processed_files.items(), key=lambda item: item[1]["tokens"], reverse=True)
        
        return {
            "overall": {"file_count": len(self.processed_files), "total_tokens": total_tokens, "total_lines": total_lines},
            "by_extension": [{"extension": ext, **stats} for ext, stats in sorted_extensions[:top_n]],
            "top_files_by_tokens": [
                {"path": p.relative_to(self.root_dir), "tokens": d["tokens"], "lines": d["lines"]} for p, d in sorted_by_tokens[:top_n]
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
            try: subprocess.run(["which", "xclip"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try: subprocess.run(["which", "wl-copy"], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.console.print("[yellow]Warning: xclip or wl-clipboard not found.[/yellow]")
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
            self.generate_prompt()
        return sum(d.get('tokens', 0) for d in self.processed_files.values())

    def get_top_files_by_tokens(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get the top files sorted by token count."""
        if not self._files_processed: self.generate_prompt()
        if not self.processed_files or not self.root_dir: return []
        sorted_files = sorted(self.processed_files.items(), key=lambda item: item[1].get("tokens", 0), reverse=True)
        return [{"path": p.relative_to(self.root_dir), "tokens": d.get("tokens", 0)} for p, d in sorted_files[:count]]

    def get_top_extensions_by_tokens(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the top file extensions sorted by token count."""
        if not self._files_processed: self.generate_prompt()
        if not self.processed_files: return []

        extension_tokens: Dict[str, int] = {}
        for path, data in self.processed_files.items():
            ext = Path(str(path)).suffix if Path(str(path)).suffix else ".<no_ext>"
            extension_tokens[ext] = extension_tokens.get(ext, 0) + data.get("tokens", 0)

        sorted_extensions = sorted(extension_tokens.items(), key=lambda item: item[1], reverse=True)
        return [{"extension": ext, "tokens": tokens} for ext, tokens in sorted_extensions[:count]]