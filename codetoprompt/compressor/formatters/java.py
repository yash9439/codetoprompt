from typing import Dict, Any, List, Optional
from .base import BaseFormatter

class JavaFormatter(BaseFormatter):
    """Formatter for Java code."""
    
    def format_structure(self, structure: Dict[str, Any]) -> str:
        """Format a complete Java code structure."""
        formatted = []
        
        # Format package
        package = structure.get('package')
        if package:
            formatted.append(f"package {package};")
            formatted.append("")
        
        # Format imports
        imports = structure.get('imports', [])
        if imports:
            for import_stmt in imports:
                formatted.append(import_stmt)
            formatted.append("")
        
        # Format classes
        classes = structure.get('classes', [])
        if classes:
            for class_info in classes:
                formatted.append(self.format_class(class_info))
                formatted.append("")
        
        return "\n".join(formatted)
    
    def format_class(self, class_info: Dict[str, Any]) -> str:
        """Format a Java class."""
        name = class_info["name"]
        modifiers = class_info.get("modifiers", [])
        superclass = class_info.get("superclass")
        interfaces = class_info.get("interfaces", [])
        fields = class_info.get("fields", [])
        methods = class_info.get("methods", [])
        
        # Format class signature
        class_def = []
        class_def.extend(modifiers)
        class_def.append("class")
        class_def.append(name)
        
        if superclass:
            class_def.append("extends")
            class_def.append(superclass)
        
        if interfaces:
            class_def.append("implements")
            class_def.append(", ".join(interfaces))
        
        formatted = [" ".join(class_def) + " {"]
        
        # Format fields
        if fields:
            for field in fields:
                formatted.append(self.format_field(field))
            formatted.append("")
        
        # Format methods
        if methods:
            for method in methods:
                formatted.append(self.format_method(method))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_interface(self, interface_info: Dict[str, Any]) -> str:
        """Format a Java interface."""
        name = interface_info.get('name', '')
        modifiers = interface_info.get('modifiers', [])
        extends = interface_info.get('extends', [])
        fields = interface_info.get('fields', [])
        methods = interface_info.get('methods', [])
        
        formatted = []
        
        # Interface signature
        signature = []
        signature.extend(modifiers)
        signature.append("interface")
        signature.append(name)
        
        if extends:
            signature.append("extends")
            signature.append(", ".join(extends))
        
        formatted.append(" ".join(signature))
        formatted.append("{")
        
        # Fields
        if fields:
            for field in fields:
                formatted.append(self.format_field(field))
            formatted.append("")  # Empty line after fields
        
        # Methods
        if methods:
            for method in methods:
                formatted.append(self.format_method(method))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_enum(self, enum_info: Dict[str, Any]) -> str:
        """Format a Java enum."""
        name = enum_info.get('name', '')
        modifiers = enum_info.get('modifiers', [])
        implements = enum_info.get('implements', [])
        constants = enum_info.get('constants', [])
        fields = enum_info.get('fields', [])
        methods = enum_info.get('methods', [])
        
        formatted = []
        
        # Enum signature
        signature = []
        signature.extend(modifiers)
        signature.append("enum")
        signature.append(name)
        
        if implements:
            signature.append("implements")
            signature.append(", ".join(implements))
        
        formatted.append(" ".join(signature))
        formatted.append("{")
        
        # Constants
        if constants:
            formatted.append("    " + ",\n    ".join(constants) + ";")
            formatted.append("")  # Empty line after constants
        
        # Fields
        if fields:
            for field in fields:
                formatted.append(self.format_field(field))
            formatted.append("")  # Empty line after fields
        
        # Methods
        if methods:
            for method in methods:
                formatted.append(self.format_method(method))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_field(self, field: Dict[str, Any]) -> str:
        """Format a Java field."""
        name = field.get('name', '')
        type_name = field.get('type', '')
        modifiers = field.get('modifiers', [])
        value = field.get('value')
        
        # Field signature
        signature = []
        signature.extend(modifiers)
        signature.append(type_name)
        signature.append(name)
        
        if value is not None:
            signature.append("=")
            signature.append(str(value))
        
        # Remove space before semicolon
        field_str = " ".join(signature)
        if field_str.endswith(" ;"):
            field_str = field_str[:-2] + ";"
        else:
            field_str += ";"
        
        return "    " + field_str
    
    def format_method(self, method_info: Dict[str, Any]) -> str:
        """Format a method definition."""
        name = method_info["name"]
        return_type = method_info.get("return_type", "void")
        modifiers = method_info.get("modifiers", [])
        parameters = method_info.get("parameters", [])
        exceptions = method_info.get("exceptions", [])

        # Format method signature
        method_def = []
        method_def.extend(modifiers)
        method_def.append(f"{return_type} {name}({', '.join(parameters)})")
        if exceptions:
            method_def.append(f"throws {', '.join(exceptions)}")

        return "    " + " ".join(method_def)
    
    def format_constructor(self, constructor: Dict[str, Any]) -> str:
        """Format a Java constructor."""
        name = constructor.get('name', '')
        modifiers = constructor.get('modifiers', [])
        parameters = constructor.get('parameters', [])
        exceptions = constructor.get('exceptions', [])
        
        formatted = []
        
        # Constructor signature
        signature = []
        signature.extend(modifiers)
        signature.append(name)
        signature.append("(")
        signature.append(", ".join(parameters))
        signature.append(")")
        
        if exceptions:
            signature.append("throws")
            signature.append(", ".join(exceptions))
        
        formatted.append("    " + " ".join(signature))
        
        return "\n".join(formatted) 