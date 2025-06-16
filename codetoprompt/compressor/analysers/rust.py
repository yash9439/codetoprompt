from typing import Dict, List, Optional, Any
import tree_sitter
from .base import BaseAnalyser

class RustAnalyser(BaseAnalyser):
    """Analyser for Rust code files."""
    
    def extract_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from Rust code."""
        structure = {
            'modules': [],
            'structs': [],
            'enums': [],
            'traits': [],
            'impls': [],
            'functions': [],
            'globals': []
        }
        
        def traverse(node):
            if node.type == 'mod_item':
                module_info = self.extract_module_info(node, source_code)
                structure['modules'].append(module_info)
            elif node.type == 'struct_item':
                struct_info = self.extract_struct_info(node, source_code)
                structure['structs'].append(struct_info)
            elif node.type == 'enum_item':
                enum_info = self.extract_enum_info(node, source_code)
                structure['enums'].append(enum_info)
            elif node.type == 'trait_item':
                trait_info = self.extract_trait_info(node, source_code)
                structure['traits'].append(trait_info)
            elif node.type == 'impl_item':
                impl_info = self.extract_impl_info(node, source_code)
                structure['impls'].append(impl_info)
            elif node.type == 'function_item':
                func_info = self.extract_function_info(node, source_code)
                structure['functions'].append(func_info)
            elif node.type == 'static_item':
                global_info = self.extract_global_info(node, source_code)
                if global_info:
                    structure['globals'].append(global_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_module_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust module information."""
        module_info = {
            'name': '',
            'is_public': False,
            'items': []
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                module_info['is_public'] = True
            elif child.type == 'identifier':
                module_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'declaration_list':
                for stmt in child.children:
                    if stmt.type == 'struct_item':
                        struct_info = self.extract_struct_info(stmt, source_code)
                        module_info['items'].append(('struct', struct_info))
                    elif stmt.type == 'enum_item':
                        enum_info = self.extract_enum_info(stmt, source_code)
                        module_info['items'].append(('enum', enum_info))
                    elif stmt.type == 'trait_item':
                        trait_info = self.extract_trait_info(stmt, source_code)
                        module_info['items'].append(('trait', trait_info))
                    elif stmt.type == 'impl_item':
                        impl_info = self.extract_impl_info(stmt, source_code)
                        module_info['items'].append(('impl', impl_info))
                    elif stmt.type == 'function_item':
                        func_info = self.extract_function_info(stmt, source_code)
                        module_info['items'].append(('function', func_info))
                    elif stmt.type == 'static_item':
                        global_info = self.extract_global_info(stmt, source_code)
                        if global_info:
                            module_info['items'].append(('global', global_info))
        
        return module_info
    
    def extract_struct_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust struct information."""
        struct_info = {
            'name': '',
            'is_public': False,
            'fields': []
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                struct_info['is_public'] = True
            elif child.type == 'type_identifier':
                struct_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'field_declaration':
                        field_info = self.extract_field_info(field, source_code)
                        if field_info:
                            struct_info['fields'].append(field_info)
        
        return struct_info
    
    def extract_enum_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust enum information."""
        enum_info = {
            'name': '',
            'is_public': False,
            'variants': []
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                enum_info['is_public'] = True
            elif child.type == 'type_identifier':
                enum_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'enum_variant_list':
                for variant in child.children:
                    if variant.type == 'enum_variant':
                        variant_info = self.extract_variant_info(variant, source_code)
                        if variant_info:
                            enum_info['variants'].append(variant_info)
        
        return enum_info
    
    def extract_trait_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust trait information."""
        trait_info = {
            'name': '',
            'is_public': False,
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                trait_info['is_public'] = True
            elif child.type == 'type_identifier':
                trait_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'declaration_list':
                for stmt in child.children:
                    if stmt.type == 'function_item':
                        method_info = self.extract_function_info(stmt, source_code)
                        trait_info['methods'].append(method_info)
        
        return trait_info
    
    def extract_impl_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust implementation information."""
        impl_info = {
            'trait': None,
            'type': '',
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                impl_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == 'trait_bounds':
                trait_text = self.extract_node_text(child, source_code)
                impl_info['trait'] = trait_text.replace('for', '').strip()
            elif child.type == 'declaration_list':
                for stmt in child.children:
                    if stmt.type == 'function_item':
                        method_info = self.extract_function_info(stmt, source_code)
                        impl_info['methods'].append(method_info)
        
        return impl_info
    
    def extract_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust function information."""
        func_info = {
            'name': '',
            'is_public': False,
            'parameters': [],
            'return_type': None,
            'is_unsafe': False,
            'is_async': False
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                func_info['is_public'] = True
            elif child.type == 'identifier':
                func_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'parameters':
                for param in child.children:
                    if param.type == 'parameter':
                        param_info = {
                            'name': '',
                            'type': ''
                        }
                        for param_child in param.children:
                            if param_child.type == 'identifier':
                                param_info['name'] = self.extract_node_text(param_child, source_code)
                            elif param_child.type == 'type_annotation':
                                param_info['type'] = self.extract_node_text(param_child, source_code)
                        func_info['parameters'].append(param_info)
            elif child.type == 'type_annotation':
                func_info['return_type'] = self.extract_node_text(child, source_code)
            elif child.type == 'unsafe':
                func_info['is_unsafe'] = True
            elif child.type == 'async':
                func_info['is_async'] = True
        
        return func_info
    
    def extract_global_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract Rust global variable information."""
        global_info = {
            'name': '',
            'type': '',
            'is_public': False,
            'is_mutable': False,
            'value': None
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                global_info['is_public'] = True
            elif child.type == 'mutable_specifier':
                global_info['is_mutable'] = True
            elif child.type == 'identifier':
                global_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'type_annotation':
                global_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == '=':
                global_info['value'] = self.extract_node_text(child.children[1], source_code)
        
        return global_info if global_info['name'] else None
    
    def extract_field_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract Rust field information."""
        field_info = {
            'name': '',
            'type': '',
            'is_public': False
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                field_info['is_public'] = True
            elif child.type == 'identifier':
                field_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'type_annotation':
                field_info['type'] = self.extract_node_text(child, source_code)
        
        return field_info if field_info['name'] else None
    
    def extract_variant_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract Rust enum variant information."""
        variant_info = {
            'name': '',
            'fields': []
        }
        
        for child in node.children:
            if child.type == 'identifier':
                variant_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'field_declaration':
                        field_info = self.extract_field_info(field, source_code)
                        if field_info:
                            variant_info['fields'].append(field_info)
        
        return variant_info if variant_info['name'] else None 