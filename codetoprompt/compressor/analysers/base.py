"""Base analyser class for language analysis."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from tree_sitter_language_pack import get_language, get_parser
import tree_sitter

class BaseAnalyser:
    """Base class for language analysers."""
    
    # Language mappings based on file extensions
    EXTENSION_TO_LANGUAGE = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rs': 'rust'
    }
    
    def __init__(self):
        self.parsers = {}
        self.languages = {}
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect the programming language of a file based on extension and content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name if detected, None otherwise
        """
        path = Path(file_path)
        
        # Check by extension first
        ext = path.suffix.lower()
        if ext in self.EXTENSION_TO_LANGUAGE:
            return self.EXTENSION_TO_LANGUAGE[ext]
        
        # Try to detect by shebang or content patterns
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                
            if first_line.startswith('#!'):
                if 'python' in first_line:
                    return 'python'
                elif 'node' in first_line:
                    return 'javascript'
        except Exception:
            pass
        
        # If we couldn't detect the language, return None
        return None
    
    def get_parser_for_language(self, language: str) -> Optional[tree_sitter.Parser]:
        """Get or create a parser for the specified language."""
        if language not in self.parsers:
            try:
                lang = get_language(language)
                parser = get_parser(language)
                self.languages[language] = lang
                self.parsers[language] = parser
                return parser
            except Exception as e:
                print(f"Failed to get parser for {language}: {e}")
                return None
        return self.parsers[language]
    
    def extract_node_text(self, node: tree_sitter.Tree, source_code: bytes) -> str:
        """Extract text from a tree-sitter node."""
        if not node or not source_code:
            return ""
        try:
            return source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
        except Exception:
            return ""
    
    def extract_preceding_comment(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[str]:
        """Extract comment or javadoc that precedes a node."""
        if not node.parent:
            return None
        
        # Look for comment nodes before this node
        parent = node.parent
        node_index = None
        for i, child in enumerate(parent.children):
            if child == node:
                node_index = i
                break
        
        if node_index is None or node_index == 0:
            return None
        
        # Check previous siblings for comments
        for i in range(node_index - 1, -1, -1):
            sibling = parent.children[i]
            if sibling.type in ['line_comment', 'block_comment']:
                comment_text = self.extract_node_text(sibling, source_code)
                return self.clean_comment(comment_text)
            elif sibling.type not in ['modifiers']:  # Stop if we hit non-modifier, non-comment
                break
        
        return None
    
    def clean_comment(self, comment: str) -> str:
        """Clean and format comment."""
        # Remove comment markers
        comment = comment.strip()
        if comment.startswith('/**') and comment.endswith('*/'):
            # Javadoc
            comment = comment[3:-2].strip()
        elif comment.startswith('/*') and comment.endswith('*/'):
            # Block comment
            comment = comment[2:-2].strip()
        elif comment.startswith('//'):
            # Line comment
            comment = comment[2:].strip()
        elif comment.startswith('#'):
            # Python comment
            comment = comment[1:].strip()
        
        # Clean up formatting
        lines = comment.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('*'):
                line = line[1:].strip()
            if line and not line.startswith('@'):  # Skip javadoc tags for now
                cleaned_lines.append(line)
        
        result = ' '.join(cleaned_lines)
        return result[:200] + ('...' if len(result) > 200 else '')
    
    def clean_docstring(self, docstring: str) -> str:
        """Clean and format docstring."""
        # Remove quotes and clean up
        docstring = docstring.strip('\'"')
        lines = docstring.split('\n')
        # Take first line and maybe second if first is very short
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 20 and len(lines) > 1:
                return (first_line + ' ' + lines[1].strip())[:100] + '...'
            return first_line[:100] + ('...' if len(first_line) > 100 else '')
        return docstring