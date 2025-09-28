"""Utility functions for code to prompt conversion."""

from pathlib import Path
from typing import Optional, Set, Tuple
from urllib.parse import urlparse

# Map file extensions to language names for markdown code blocks
EXT_TO_LANG = {
    "py": "python",
    "ipynb": "python",
    "js": "javascript",
    "ts": "typescript",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "cs": "csharp",
    "html": "html",
    "css": "css",
    "xml": "xml",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "md": "markdown",
    "sh": "bash",
    "rb": "ruby",
    "go": "go",
    "rs": "rust",
    "php": "php",
    "kt": "kotlin",
    "swift": "swift",
    "sql": "sql",
    "toml": "toml",
    "dockerfile": "dockerfile",
}

# Text file extensions
TEXT_EXTENSIONS = {
    '.py', '.ipynb', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.md', '.txt', '.rst', '.tex', '.csv', '.sql', '.sh', '.bash', '.zsh',
    '.dockerfile', '.gitignore', '.env', '.c', '.cpp', '.h', '.hpp', '.java',
    '.kt', '.rb', '.php', '.go', '.rs', '.swift', '.dart', '.r', '.pl', '.lua'
}

# Data file extensions to truncate
DATA_FILE_EXTENSIONS = {'.csv', '.json', '.jsonl'}
DATA_FILE_LINE_LIMIT = 5

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin', '.png', '.jpg', 
    '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', '.ico', '.woff', '.woff2'
}

# Allowed hidden files
ALLOWED_HIDDEN = {'.gitignore', '.env', '.github'}


def is_text_file(file_path: Path, max_size_mb: int = 10) -> bool:
    """Check if a file is likely a text file."""
    # Check file size
    if file_path.stat().st_size > max_size_mb * 1024 * 1024:
        return False
    
    # Check extension
    ext = file_path.suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return False
    if ext in TEXT_EXTENSIONS:
        return True
    
    # For unknown extensions, check for binary content
    with open(file_path, 'rb') as f:
        chunk = f.read(1024)
        return b'\x00' not in chunk


def should_skip_path(path: Path, root_dir: Path) -> bool:
    """Check if a path should be skipped."""
    rel_path = path.relative_to(root_dir)
    
    # Skip hidden files/directories (except allowed ones)
    for part in rel_path.parts:
        if part.startswith('.') and part not in ALLOWED_HIDDEN:
            return True
    
    # Skip common build/cache directories
    skip_dirs = {'__pycache__', 'node_modules', '.git', 'dist', 'build', '.pytest_cache'}
    if any(part in skip_dirs for part in rel_path.parts):
        return True
    
    return False


def read_and_truncate_file(file_path: Path, line_limit: Optional[int] = None, byte_limit: Optional[int] = None) -> Tuple[Optional[str], bool]:
    """
    Reads a file's content, truncating it to a specific number of lines or bytes.
    Returns a tuple of (content, was_truncated). Content is None if reading fails.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252']
    was_truncated = False
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = []
                current_bytes = 0
                
                # Optimization: if no limits, read all efficiently
                if line_limit is None and byte_limit is None:
                    return f.read(), False

                for i, line in enumerate(f):
                    line_bytes = len(line.encode(encoding))
                    
                    # Check line limit
                    if line_limit is not None and i >= line_limit:
                        was_truncated = True
                        break
                    
                    # Check byte limit: We stop before adding the full line if it exceeds the limit.
                    if byte_limit is not None and current_bytes + line_bytes > byte_limit:
                        was_truncated = True
                        break
                    
                    lines.append(line)
                    current_bytes += line_bytes
                
                content = "".join(lines)
                if '\x00' in content: return None, False
                
                return content, was_truncated
        except Exception:
            continue
    return None, False


def read_file_safely(file_path: Path, show_line_numbers: bool = True) -> Optional[str]:
    """Read file content with encoding fallback, applying line numbers if requested."""
    # Use the general reader without limits
    content, _ = read_and_truncate_file(file_path, line_limit=None, byte_limit=None)
    
    if content is None or not content.strip():
        return None
    
    if show_line_numbers:
        lines = content.splitlines()
        return '\n'.join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
    
    return content

def is_url(path: str) -> bool:
    """Check if the given path string is a URL."""
    if not isinstance(path, str):
        return False
    try:
        result = urlparse(path)
        # A URL must have a scheme (http, https) and a network location (domain)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False