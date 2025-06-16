from typing import Dict, Any, List, Optional
from .base import BaseFormatter

class JavaScriptFormatter(BaseFormatter):
    """Formatter for JavaScript code."""
    
    def format_structure(self, structure: Dict[str, Any]) -> str:
        """Format a complete JavaScript code structure."""
        formatted = []
        
        # Format imports
        imports = structure.get('imports', [])
        if imports:
            for import_stmt in imports:
                formatted.append(import_stmt)
            formatted.append("")
        
        # Format constants
        constants = structure.get('constants', [])
        if constants:
            for constant in constants:
                formatted.append(self.format_constant(constant))
            formatted.append("")
        
        # Format classes
        classes = structure.get('classes', [])
        if classes:
            for class_info in classes:
                formatted.append(self.format_class(class_info))
                formatted.append("")
        
        # Format functions
        functions = structure.get('functions', [])
        if functions:
            for func in functions:
                formatted.append(self.format_function(func))
                formatted.append("")
        
        return "\n".join(formatted)
    
    def format_constant(self, constant: Dict[str, Any]) -> str:
        """Format a JavaScript constant."""
        name = constant.get('name', '')
        value = constant.get('value')
        
        return f"const {name} = {value};"
    
    def format_function(self, func: Dict[str, Any]) -> str:
        """Format a JavaScript function."""
        name = func.get('name', '')
        parameters = func.get('parameters', [])
        if isinstance(parameters, list):
            param_str = ', '.join(parameters)
        else:
            param_str = parameters
        is_async = func.get('is_async', False)
        
        prefix = "async " if is_async else ""
        return f"{prefix}function {name}({param_str})"
    
    def format_class(self, class_info: Dict[str, Any]) -> str:
        """Format a JavaScript class."""
        name = class_info["name"]
        inheritance = class_info.get("inheritance", [])
        methods = class_info.get("methods", [])
        properties = class_info.get("properties", [])
        
        # Format class signature
        class_def = f"class {name}"
        if inheritance:
            class_def += f" extends {inheritance[0]}"
        
        formatted = [class_def + " {"]
        
        # Format properties
        if properties:
            for prop in properties:
                formatted.append(self.format_property(prop))
        
        # Format methods
        if methods:
            for method in methods:
                formatted.append(self.format_method(method))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_property(self, property_info: Dict[str, Any]) -> str:
        """Format a JavaScript class property."""
        name = property_info.get('name', '')
        value = property_info.get('value')
        is_static = property_info.get('is_static', False)
        
        prefix = "static " if is_static else ""
        return f"    {prefix}{name} = {value};"
    
    def format_method(self, method_info: Dict[str, Any]) -> str:
        """Format a JavaScript method."""
        name = method_info.get('name', '')
        parameters = method_info.get('parameters', [])
        if isinstance(parameters, list):
            param_str = ', '.join(parameters)
        else:
            param_str = parameters
        is_async = method_info.get('is_async', False)
        is_static = method_info.get('is_static', False)
        is_private = method_info.get('is_private', False)
        
        prefix = []
        if is_static:
            prefix.append("static")
        if is_async:
            prefix.append("async")
        if is_private:
            name = "#" + name
        
        method_def = []
        if prefix:
            method_def.append(" ".join(prefix))
        method_def.append(f"{name}({param_str})")
        
        return "    " + " ".join(method_def)
    
    def format_docstring(self, docstring: Optional[str]) -> str:
        """Format a JavaScript docstring."""
        if not docstring:
            return ""
        
        return f"    /**\n     * {docstring}\n     */" 