from typing import Dict, Type, Optional
from .base import BaseFormatter
from .python import PythonFormatter
from .javascript import JavaScriptFormatter
from .java import JavaFormatter
from .cpp import CppFormatter
from .rust import RustFormatter

class FormatterFactory:
    """Factory for creating formatters based on language."""
    
    _formatters: Dict[str, Type[BaseFormatter]] = {
        'python': PythonFormatter,
        'javascript': JavaScriptFormatter,
        'java': JavaFormatter,
        'cpp': CppFormatter,
        'rust': RustFormatter,
    }
    
    @classmethod
    def get_formatter(cls, language: str) -> Optional[BaseFormatter]:
        """Get a formatter instance for the specified language.
        
        Args:
            language: The programming language name.
            
        Returns:
            A formatter instance for the specified language, or None if no formatter is available.
        """
        formatter_class = cls._formatters.get(language.lower())
        if formatter_class:
            return formatter_class()
        return None
    
    @classmethod
    def register_formatter(cls, language: str, formatter_class: Type[BaseFormatter]) -> None:
        """Register a new formatter for a language.
        
        Args:
            language: The programming language name.
            formatter_class: The formatter class to register.
        """
        cls._formatters[language.lower()] = formatter_class
    
    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Get a list of supported programming languages.
        
        Returns:
            A list of supported programming language names.
        """
        return list(cls._formatters.keys()) 