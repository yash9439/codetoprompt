# compressor/compressor.py
from typing import Dict, Any, Optional

from .analysers.factory import AnalyserFactory
from .formatters.factory import FormatterFactory
from .analysers.base import BaseAnalyser # For language detection

class Compressor:
    """
    Analyses a source code file, extracts its structure,
    and formats it into a compressed text representation.
    """
    def __init__(self):
        # The BaseAnalyser has the language detection logic
        self.base_analyser = BaseAnalyser()

    def generate_compressed_prompt(self, file_path: str) -> str:
        """
        Generate a compressed prompt for the given file.
        
        Args:
            file_path: Path to the file to analyse
            
        Returns:
            Compressed representation of the file structure
        """
        try:
            # 1. Detect language
            language = self.base_analyser.detect_language(file_path)
            if not language:
                return f"# Error: Could not detect language for {file_path}"
            
            # 2. Get the specific analyser for the language
            analyser = AnalyserFactory.get_analyser(language)
            if not analyser:
                return f"# Error: No analyser available for language: {language}"

            # 3. Get the parser
            parser = analyser.get_parser_for_language(language)
            if not parser:
                return f"# Error: No parser available for language: {language}"

            # 4. Read and parse the file to get the AST
            with open(file_path, 'rb') as f:
                source_code = f.read()
            tree = parser.parse(source_code)

            # 5. Extract the structure
            structure = analyser.extract_structure(tree, source_code)
            
            # 6. Get the specific formatter for the language
            formatter = FormatterFactory.get_formatter(language)
            if not formatter:
                return f"# Error: No formatter available for language: {language}"
            
            # 7. Format the structure into the final prompt
            header = f"# File: {file_path}\n# Language: {language}\n\n"
            content = formatter.format_structure(structure)
            return header + content
            
        except Exception as e:
            return f"# Error analyzing {file_path}: {str(e)}"

# You can also provide the convenience functions from the original script
def analyse_file(file_path: str) -> str:
    """Convenience function to analyse a single file."""
    compressor = Compressor()
    return compressor.generate_compressed_prompt(file_path)