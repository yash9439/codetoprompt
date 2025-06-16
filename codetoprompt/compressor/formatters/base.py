from typing import Dict, Any, List, Optional
from pathlib import Path

class BaseFormatter:
    """Base class for all language formatters."""
    
    def format_imports(self, imports: List[str]) -> str:
        """Format a list of imports."""
        if not imports:
            return ""
        
        formatted = []
        for imp in imports:
            formatted.append(f"import {imp}")
        
        return "\n".join(formatted)
    
    def format_parameters(self, parameters: List[Dict[str, str]]) -> str:
        """Format a list of parameters."""
        if not parameters:
            return ""
        
        formatted = []
        for param in parameters:
            if isinstance(param, dict):
                formatted.append(f"{param['type']} {param['name']}")
            else:
                formatted.append(str(param))
        
        return ", ".join(formatted)
    
    def format_docstring(self, docstring: Optional[str]) -> str:
        """Format a docstring."""
        if not docstring:
            return ""
        
        return f"\"\"\"{docstring}\"\"\""
    
    def format_comment(self, comment: Optional[str]) -> str:
        """Format a comment."""
        if not comment:
            return ""
        
        return f"// {comment}"
    
    def format_modifiers(self, modifiers: List[str]) -> str:
        """Format a list of modifiers."""
        if not modifiers:
            return ""
        
        return " ".join(modifiers)
    
    def format_inheritance(self, base_classes: List[str]) -> str:
        """Format inheritance information."""
        if not base_classes:
            return ""
        
        return f"extends {', '.join(base_classes)}"
    
    def format_implements(self, interfaces: List[str]) -> str:
        """Format interface implementation information."""
        if not interfaces:
            return ""
        
        return f"implements {', '.join(interfaces)}"
    
    def format_field(self, field: Dict[str, Any]) -> str:
        """Format a field declaration."""
        modifiers = self.format_modifiers(field.get('modifiers', []))
        field_type = field.get('type', '')
        name = field.get('name', '')
        value = field.get('value')
        
        formatted = []
        if modifiers:
            formatted.append(modifiers)
        if field_type:
            formatted.append(field_type)
        formatted.append(name)
        if value is not None:
            formatted.append(f"= {value}")
        
        return " ".join(formatted)
    
    def format_method(self, method: Dict[str, Any]) -> str:
        """Format a method declaration."""
        modifiers = self.format_modifiers(method.get('modifiers', []))
        return_type = method.get('return_type', '')
        name = method.get('name', '')
        parameters = self.format_parameters(method.get('parameters', []))
        docstring = self.format_docstring(method.get('docstring'))
        
        formatted = []
        if modifiers:
            formatted.append(modifiers)
        if return_type:
            formatted.append(return_type)
        formatted.append(f"{name}({parameters})")
        
        if docstring:
            formatted.append(docstring)
        
        return " ".join(formatted)
    
    def format_class(self, class_info: Dict[str, Any]) -> str:
        """Format a class declaration."""
        modifiers = self.format_modifiers(class_info.get('modifiers', []))
        name = class_info.get('name', '')
        inheritance = self.format_inheritance(class_info.get('base_classes', []))
        implements = self.format_implements(class_info.get('implements', []))
        docstring = self.format_docstring(class_info.get('docstring'))
        
        formatted = []
        if modifiers:
            formatted.append(modifiers)
        formatted.append(f"class {name}")
        
        inheritance_parts = []
        if inheritance:
            inheritance_parts.append(inheritance)
        if implements:
            inheritance_parts.append(implements)
        if inheritance_parts:
            formatted.append(" ".join(inheritance_parts))
        
        if docstring:
            formatted.append(docstring)
        
        return " ".join(formatted)
    
    def format_interface(self, interface_info: Dict[str, Any]) -> str:
        """Format an interface declaration."""
        modifiers = self.format_modifiers(interface_info.get('modifiers', []))
        name = interface_info.get('name', '')
        extends = self.format_inheritance(interface_info.get('extends', []))
        docstring = self.format_docstring(interface_info.get('docstring'))
        
        formatted = []
        if modifiers:
            formatted.append(modifiers)
        formatted.append(f"interface {name}")
        
        if extends:
            formatted.append(extends)
        
        if docstring:
            formatted.append(docstring)
        
        return " ".join(formatted)
    
    def format_enum(self, enum_info: Dict[str, Any]) -> str:
        """Format an enum declaration."""
        modifiers = self.format_modifiers(enum_info.get('modifiers', []))
        name = enum_info.get('name', '')
        docstring = self.format_docstring(enum_info.get('docstring'))
        
        formatted = []
        if modifiers:
            formatted.append(modifiers)
        formatted.append(f"enum {name}")
        
        if docstring:
            formatted.append(docstring)
        
        return " ".join(formatted)
    
    def format_structure(self, structure: Dict[str, Any]) -> str:
        """Format a complete code structure."""
        raise NotImplementedError("Subclasses must implement format_structure") 