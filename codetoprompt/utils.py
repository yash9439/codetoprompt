"""Utility functions for code to prompt conversion."""

from pathlib import Path
from typing import Optional, Set

# Text file extensions
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.md', '.txt', '.rst', '.tex', '.csv', '.sql', '.sh', '.bash', '.zsh',
    '.dockerfile', '.gitignore', '.env', '.c', '.cpp', '.h', '.hpp', '.java',
    '.kt', '.rb', '.php', '.go', '.rs', '.swift', '.dart', '.r', '.pl', '.lua'
}

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


def read_file_safely(file_path: Path, show_line_numbers: bool = True) -> Optional[str]:
    """Read file content with encoding fallback."""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            if not content.strip() or '\x00' in content:
                return None
            
            if show_line_numbers:
                lines = content.splitlines()
                return '\n'.join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
            
            return content
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
    
    return None