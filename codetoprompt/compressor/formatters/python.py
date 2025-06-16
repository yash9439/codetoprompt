from typing import Dict, Any, List, Optional
from .base import BaseFormatter

class PythonFormatter(BaseFormatter):
    """Formatter for Python code."""
    
    def format_structure(self, structure: Dict[str, Any]) -> str:
        """Format a complete Python code structure."""
        formatted = []
        
        # Format imports
        imports = structure.get('imports', [])
        if imports:
            formatted.extend(imports)
            formatted.append("")  # Empty line after imports
        
        # Format constants
        constants = structure.get('constants', [])
        if constants:
            for const in constants:
                formatted.append(self.format_constant(const))
            formatted.append("")  # Empty line after constants
        
        # Format classes
        classes = structure.get('classes', [])
        if classes:
            for class_info in classes:
                formatted.append(self.format_class(class_info))
                formatted.append("")  # Empty line after each class
        
        # Format functions
        functions = structure.get('functions', [])
        if functions:
            for func in functions:
                formatted.append(self.format_function(func))
                formatted.append("")  # Empty line after each function
        
        return "\n".join(formatted)
    
    def format_constant(self, constant: Dict[str, str]) -> str:
        """Format a Python constant."""
        name = constant.get('name', '')
        value = constant.get('value', '')
        return f"{name} = {value}"
    
    def format_function(self, function: Dict[str, Any]) -> str:
        """Format a function definition."""
        signature = f"def {function['name']}({function['parameters']})"
        if function.get('return_type'):
            signature += f" -> {function['return_type']}"
        signature += ":"
        
        formatted = [signature]
        if function.get('docstring'):
            formatted.append(f"    \"\"\"{function['docstring']}\"\"\"")
        
        return "\n".join(formatted)
    
    def format_class(self, class_info: Dict[str, Any]) -> str:
        """Format a Python class."""
        name = class_info.get('name', '')
        inheritance = class_info.get('inheritance', [])
        docstring = class_info.get('docstring', '')
        methods = class_info.get('methods', [])
        
        # Format inheritance
        inheritance_str = ""
        if inheritance:
            inheritance_str = f"({', '.join(inheritance)})"
        
        # Format class definition
        class_def = f"class {name}{inheritance_str}:"
        formatted = [class_def]
        
        # Add docstring
        if docstring:
            formatted.append(f'    """{docstring}"""')
        
        # Format methods
        for method in methods:
            formatted.append(self.format_method(method))
        
        return "\n".join(formatted)
    
    def format_method(self, method: Dict[str, Any]) -> str:
        """Format a method definition."""
        signature = f"def {method['name']}({method['parameters']})"
        if method.get('return_type'):
            signature += f" -> {method['return_type']}"
        signature += ":"
        
        formatted = [f"    {signature}"]
        if method.get('docstring'):
            formatted.append(f"        \"\"\"{method['docstring']}\"\"\"")
        
        return "\n".join(formatted)
    
    def format_docstring(self, docstring: Optional[str]) -> str:
        """Format a Python docstring."""
        if not docstring:
            return ""
        
        return f'"""{docstring}"""' 