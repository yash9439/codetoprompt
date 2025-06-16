from typing import Dict, Type, Optional
from .base import BaseAnalyser
from .python import PythonAnalyser
from .javascript import JavaScriptAnalyser
from .java import JavaAnalyser
from .cpp import CppAnalyser
from .rust import RustAnalyser

# We'll need a CAnalyser later if we add it back
# from .c import CAnalyser 

class AnalyserFactory:
    """Factory for creating analysers based on language."""
    
    _analysers: Dict[str, Type[BaseAnalyser]] = {
        'python': PythonAnalyser,
        'javascript': JavaScriptAnalyser,
        'typescript': JavaScriptAnalyser, # TS uses the JS analyser
        'java': JavaAnalyser,
        'cpp': CppAnalyser,
        'c': CppAnalyser, # For now, C can use the CppAnalyser
        'rust': RustAnalyser,
    }
    
    @classmethod
    def get_analyser(cls, language: str) -> Optional[BaseAnalyser]:
        """Get an analyser instance for the specified language."""
        analyser_class = cls._analysers.get(language.lower())
        if analyser_class:
            return analyser_class()
        return None
    
    @classmethod
    def register_analyser(cls, language: str, analyser_class: Type[BaseAnalyser]) -> None:
        """Register a new analyser for a language."""
        cls._analysers[language.lower()] = analyser_class