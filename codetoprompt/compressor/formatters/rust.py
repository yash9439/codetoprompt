from typing import Dict, Any, List, Optional
from .base import BaseFormatter

class RustFormatter(BaseFormatter):
    """Formatter for Rust code."""
    
    def format_structure(self, structure: Dict[str, Any]) -> str:
        """Format a complete Rust code structure."""
        formatted = []
        
        # Format modules
        modules = structure.get('modules', [])
        if modules:
            for module in modules:
                formatted.append(self.format_module(module))
                formatted.append("")
        
        # Format structs
        structs = structure.get('structs', [])
        if structs:
            for struct in structs:
                formatted.append(self.format_struct(struct))
                formatted.append("")
        
        # Format traits
        traits = structure.get('traits', [])
        if traits:
            for trait in traits:
                formatted.append(self.format_trait(trait))
                formatted.append("")
        
        # Format implementations
        implementations = structure.get('implementations', [])
        if implementations:
            for impl in implementations:
                formatted.append(self.format_implementation(impl))
                formatted.append("")
        
        return "\n".join(formatted)
    
    def format_module(self, module_info: Dict[str, Any]) -> str:
        """Format a Rust module."""
        name = module_info.get('name', '')
        visibility = module_info.get('visibility', '')
        
        prefix = f"{visibility} " if visibility else ""
        return f"{prefix}mod {name};"
    
    def format_struct(self, struct_info: Dict[str, Any]) -> str:
        """Format a Rust struct."""
        name = struct_info.get('name', '')
        visibility = struct_info.get('visibility', '')
        fields = struct_info.get('fields', [])
        
        # Format struct signature
        prefix = f"{visibility} " if visibility else ""
        struct_def = f"{prefix}struct {name} {{"
        
        # Format fields
        formatted = [struct_def]
        if fields:
            for field in fields:
                formatted.append(self.format_field(field))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_trait(self, trait_info: Dict[str, Any]) -> str:
        """Format a Rust trait."""
        name = trait_info.get('name', '')
        visibility = trait_info.get('visibility', '')
        methods = trait_info.get('methods', [])
        
        # Format trait signature
        prefix = f"{visibility} " if visibility else ""
        trait_def = f"{prefix}trait {name} {{"
        
        # Format methods
        formatted = [trait_def]
        if methods:
            for method in methods:
                formatted.append(self.format_method(method))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_implementation(self, impl_info: Dict[str, Any]) -> str:
        """Format a Rust implementation."""
        trait = impl_info.get('trait')
        type_name = impl_info.get('type')
        methods = impl_info.get('methods', [])
        
        # Format impl signature
        if trait:
            impl_def = f"impl {trait} for {type_name} {{"
        else:
            impl_def = f"impl {type_name} {{"
        
        # Format methods
        formatted = [impl_def]
        if methods:
            for method in methods:
                formatted.append(self.format_method(method))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_field(self, field_info: Dict[str, Any]) -> str:
        """Format a Rust field."""
        name = field_info.get('name', '')
        type_name = field_info.get('type', '')
        visibility = field_info.get('visibility', '')
        
        prefix = f"{visibility} " if visibility else ""
        return f"    {prefix}{name}: {type_name},"
    
    def format_method(self, method_info: Dict[str, Any]) -> str:
        """Format a Rust method."""
        name = method_info.get('name', '')
        parameters = method_info.get('parameters', [])
        return_type = method_info.get('return_type')
        visibility = method_info.get('visibility', '')
        
        # Format method signature
        prefix = f"{visibility} " if visibility else ""
        method_def = f"    {prefix}fn {name}({', '.join(parameters)})"
        
        if return_type:
            method_def += f" -> {return_type}"
        
        method_def += " {"
        method_def += "\n        // Implementation"
        method_def += "\n    }"
        
        return method_def
    
    def format_enum(self, enum_info: Dict[str, Any]) -> str:
        """Format a Rust enum."""
        name = enum_info.get('name', '')
        visibility = enum_info.get('visibility', '')
        variants = enum_info.get('variants', [])
        
        formatted = []
        
        # Enum signature
        signature = []
        if visibility:
            signature.append(visibility)
        signature.append(f"enum {name}")
        formatted.append(" ".join(signature))
        
        # Enum body
        formatted.append("{")
        
        # Variants
        if variants:
            for variant in variants:
                formatted.append(self.format_variant(variant))
        
        formatted.append("}")
        
        return "\n".join(formatted)
    
    def format_function(self, func: Dict[str, Any]) -> str:
        """Format a Rust function."""
        name = func.get('name', '')
        visibility = func.get('visibility', '')
        parameters = func.get('parameters', [])
        return_type = func.get('return_type')
        is_async = func.get('is_async', False)
        is_unsafe = func.get('is_unsafe', False)
        
        formatted = []
        
        # Function signature
        signature = []
        if visibility:
            signature.append(visibility)
        if is_unsafe:
            signature.append("unsafe")
        if is_async:
            signature.append("async")
        signature.append(f"fn {name}")
        signature.append("(")
        signature.append(", ".join(parameters))
        signature.append(")")
        if return_type:
            signature.append(f" -> {return_type}")
        signature.append(";")
        
        formatted.append(" ".join(signature))
        
        return "\n".join(formatted)
    
    def format_variant(self, variant: Dict[str, Any]) -> str:
        """Format a Rust enum variant."""
        name = variant.get('name', '')
        fields = variant.get('fields', [])
        
        formatted = []
        
        # Variant signature
        signature = []
        signature.append(name)
        
        if fields:
            signature.append("(")
            signature.append(", ".join(fields))
            signature.append(")")
        
        signature.append(",")
        formatted.append("    " + " ".join(signature))
        
        return "\n".join(formatted) 