from typing import Dict, Any, List, Optional
from .base import BaseFormatter

class CppFormatter(BaseFormatter):
    """Formatter for C/C++ code."""
    
    def format_structure(self, structure: Dict[str, Any]) -> str:
        """Format a complete C/C++ code structure."""
        formatted = []
        
        # Includes
        includes = structure.get('includes', [])
        for include in includes:
            formatted.append(f"#include {include}")
        if includes:
            formatted.append("")
        
        # Namespaces
        namespaces = structure.get('namespaces', [])
        for namespace in namespaces:
            name = namespace.get('name', '')
            content = namespace.get('content', [])
            formatted.append(f"namespace {name} {{")
            for item in content:
                formatted.append(f"    {item}")
            formatted.append("}")
            formatted.append("")
        
        # Classes
        classes = structure.get('classes', [])
        for class_info in classes:
            name = class_info.get('name', '')
            inheritance = class_info.get('inheritance', [])
            fields = class_info.get('fields', [])
            methods = class_info.get('methods', [])
            
            # Class definition
            if inheritance:
                formatted.append(f"class {name} : {', '.join(inheritance)} {{")
            else:
                formatted.append(f"class {name} {{")
            
            # Fields
            for field in fields:
                formatted.append(self.format_field(field))
            
            # Methods
            for method in methods:
                formatted.append(self.format_method(method))
            
            formatted.append("};")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def format_namespace(self, namespace_info: Dict[str, Any]) -> str:
        """Format a namespace definition."""
        name = namespace_info["name"]
        content = namespace_info.get("content", [])

        # Format namespace definition
        namespace_def = f"namespace {name} {{"

        # Format content
        if content:
            return f"{namespace_def}\n    " + "\n    ".join(content) + "\n}"
        return f"{namespace_def}\n}}"

    def format_class(self, class_info: Dict[str, Any]) -> str:
        """Format a class definition."""
        name = class_info["name"]
        inheritance = class_info.get("inheritance", [])
        fields = class_info.get("fields", [])
        methods = class_info.get("methods", [])

        # Format inheritance
        inheritance_str = ""
        if inheritance:
            inheritance_str = f" : {', '.join(inheritance)}"

        # Format class definition
        class_def = f"class {name}{inheritance_str} {{"

        # Format fields and methods
        members = []
        for field in fields:
            members.append(self.format_field(field))
        for method in methods:
            members.append(self.format_method(method))

        # Combine everything
        if members:
            return f"{class_def}\n    " + "\n    ".join(members) + "\n};"
        return f"{class_def}\n}};"
    
    def format_struct(self, struct_info: Dict[str, Any]) -> str:
        """Format a C/C++ struct."""
        name = struct_info.get('name', '')
        fields = struct_info.get('fields', [])
        
        formatted = []
        
        # Struct signature
        formatted.append(f"struct {name}")
        formatted.append("{")
        
        # Fields
        if fields:
            for field in fields:
                formatted.append(self.format_field(field))
        
        formatted.append("};")
        
        return "\n".join(formatted)
    
    def format_enum(self, enum_info: Dict[str, Any]) -> str:
        """Format a C/C++ enum."""
        name = enum_info.get('name', '')
        values = enum_info.get('values', [])
        
        formatted = []
        
        # Enum signature
        formatted.append(f"enum {name}")
        formatted.append("{")
        
        # Values
        if values:
            formatted.append("    " + ",\n    ".join(values))
        
        formatted.append("};")
        
        return "\n".join(formatted)
    
    def format_typedef(self, typedef_info: Dict[str, Any]) -> str:
        """Format a C/C++ typedef."""
        name = typedef_info.get('name', '')
        type_name = typedef_info.get('type', '')
        
        return f"typedef {type_name} {name};"
    
    def format_function(self, func: Dict[str, Any]) -> str:
        """Format a C/C++ function."""
        name = func.get('name', '')
        return_type = func.get('return_type', 'void')
        parameters = func.get('parameters', [])
        is_const = func.get('is_const', False)
        is_virtual = func.get('is_virtual', False)
        is_pure_virtual = func.get('is_pure_virtual', False)
        
        formatted = []
        
        # Function signature
        signature = []
        if is_virtual:
            signature.append("virtual")
        signature.append(return_type)
        signature.append(name)
        signature.append("(")
        signature.append(", ".join(parameters))
        signature.append(")")
        if is_const:
            signature.append("const")
        if is_pure_virtual:
            signature.append("= 0")
        signature.append(";")
        
        formatted.append(" ".join(signature))
        
        return "\n".join(formatted)
    
    def format_field(self, field: Dict[str, Any]) -> str:
        """Format a C/C++ field."""
        name = field.get('name', '')
        type_name = field.get('type', '')
        value = field.get('value', '')
        
        field_str = f"{type_name} {name}"
        if value:
            field_str += f" = {value}"
        field_str += ";"
        
        return "    " + field_str
    
    def format_method(self, method: Dict[str, Any]) -> str:
        """Format a C/C++ method."""
        name = method.get('name', '')
        return_type = method.get('return_type', 'void')
        parameters = method.get('parameters', [])
        is_const = method.get('is_const', False)
        is_virtual = method.get('is_virtual', False)
        is_pure_virtual = method.get('is_pure_virtual', False)
        
        # Method signature
        signature = []
        if is_virtual:
            signature.append("virtual")
        signature.append(return_type)
        # Format: name(params)
        param_str = ", ".join(parameters)
        method_sig = f"{name}({param_str})"
        signature.append(method_sig)
        if is_const:
            signature.append("const")
        if is_pure_virtual:
            signature.append("= 0")
        # Join with spaces, add semicolon at end
        return "    " + " ".join(signature) + ";" 