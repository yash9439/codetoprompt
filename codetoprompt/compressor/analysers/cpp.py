from typing import Dict, List, Optional, Any
import tree_sitter
from .base import BaseAnalyser

class CppAnalyser(BaseAnalyser):
    """Analyser for C/C++ code files."""
    
    def extract_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from C/C++ code."""
        structure = {
            'includes': [],
            'namespaces': [],
            'classes': [],
            'structs': [],
            'enums': [],
            'typedefs': [],
            'functions': [],
            'globals': []
        }
        
        def traverse(node, is_inside_function=False):
            if node.type == 'preproc_include':
                include_text = self.extract_node_text(node, source_code).strip()
                structure['includes'].append(include_text)
            elif node.type == 'namespace_definition':
                namespace_info = self.extract_namespace_info(node, source_code)
                structure['namespaces'].append(namespace_info)
            elif node.type == 'class_specifier':
                class_info = self.extract_class_info(node, source_code)
                structure['classes'].append(class_info)
            elif node.type == 'struct_specifier':
                struct_info = self.extract_struct_info(node, source_code)
                structure['structs'].append(struct_info)
            elif node.type == 'enum_specifier':
                enum_info = self.extract_enum_info(node, source_code)
                structure['enums'].append(enum_info)
            elif node.type == 'type_definition':
                typedef_info = self.extract_typedef_info(node, source_code)
                structure['typedefs'].append(typedef_info)
            elif node.type == 'function_definition':
                func_info = self.extract_function_info(node, source_code)
                structure['functions'].append(func_info)
            elif node.type == 'declaration' and not is_inside_function:
                global_info = self.extract_global_info(node, source_code)
                if global_info:
                    structure['globals'].append(global_info)
            
            # Check if we're entering a function body
            if node.type == 'function_definition':
                is_inside_function = True
            
            for child in node.children:
                traverse(child, is_inside_function)
            
            # Reset function context when leaving a function
            if node.type == 'function_definition':
                is_inside_function = False
        
        traverse(tree.root_node)
        return structure
    
    def extract_namespace_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ namespace information."""
        namespace_info = {
            'name': '',
            'classes': [],
            'structs': [],
            'enums': [],
            'typedefs': [],
            'functions': [],
            'globals': []
        }
        
        for child in node.children:
            if child.type == 'identifier':
                namespace_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'declaration_list':
                for stmt in child.children:
                    if stmt.type == 'class_specifier':
                        class_info = self.extract_class_info(stmt, source_code)
                        namespace_info['classes'].append(class_info)
                    elif stmt.type == 'struct_specifier':
                        struct_info = self.extract_struct_info(stmt, source_code)
                        namespace_info['structs'].append(struct_info)
                    elif stmt.type == 'enum_specifier':
                        enum_info = self.extract_enum_info(stmt, source_code)
                        namespace_info['enums'].append(enum_info)
                    elif stmt.type == 'type_definition':
                        typedef_info = self.extract_typedef_info(stmt, source_code)
                        namespace_info['typedefs'].append(typedef_info)
                    elif stmt.type == 'function_definition':
                        func_info = self.extract_function_info(stmt, source_code)
                        namespace_info['functions'].append(func_info)
                    elif stmt.type == 'declaration':
                        global_info = self.extract_global_info(stmt, source_code)
                        if global_info:
                            namespace_info['globals'].append(global_info)
        
        return namespace_info
    
    def extract_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ class information."""
        class_info = {
            'name': '',
            'base_classes': [],
            'access_specifiers': [],
            'fields': [],
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                class_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'base_class_clause':
                base_text = self.extract_node_text(child, source_code)
                class_info['base_classes'] = [b.strip() for b in base_text.split(',')]
            elif child.type == 'access_specifier':
                access = self.extract_node_text(child, source_code)
                class_info['access_specifiers'].append(access)
            elif child.type == 'field_declaration_list':
                for stmt in child.children:
                    if stmt.type == 'field_declaration':
                        field_info = self.extract_field_info(stmt, source_code)
                        if field_info:
                            class_info['fields'].append(field_info)
                    elif stmt.type == 'function_definition':
                        method_info = self.extract_function_info(stmt, source_code)
                        class_info['methods'].append(method_info)
        
        return class_info
    
    def extract_struct_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ struct information."""
        struct_info = {
            'name': '',
            'base_classes': [],
            'fields': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                struct_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'base_class_clause':
                base_text = self.extract_node_text(child, source_code)
                struct_info['base_classes'] = [b.strip() for b in base_text.split(',')]
            elif child.type == 'field_declaration_list':
                for stmt in child.children:
                    if stmt.type == 'field_declaration':
                        field_info = self.extract_field_info(stmt, source_code)
                        if field_info:
                            struct_info['fields'].append(field_info)
        
        return struct_info
    
    def extract_enum_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ enum information."""
        enum_info = {
            'name': '',
            'enumerators': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                enum_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'enumerator_list':
                for enumerator in child.children:
                    if enumerator.type == 'enumerator':
                        name = self.extract_node_text(enumerator.children[0], source_code)
                        value = None
                        if len(enumerator.children) > 1:
                            value = self.extract_node_text(enumerator.children[1], source_code)
                        enum_info['enumerators'].append({
                            'name': name,
                            'value': value
                        })
        
        return enum_info
    
    def extract_typedef_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, str]:
        """Extract C++ typedef information."""
        typedef_info = {
            'name': '',
            'type': ''
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                typedef_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'type_descriptor':
                typedef_info['type'] = self.extract_node_text(child, source_code)
        
        return typedef_info
    
    def extract_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ function information."""
        func_info = {
            'name': '',
            'return_type': '',
            'parameters': [],
            'is_virtual': False,
            'is_static': False,
            'is_const': False
        }
        
        for child in node.children:
            if child.type == 'function_declarator':
                for func_child in child.children:
                    if func_child.type == 'identifier':
                        func_info['name'] = self.extract_node_text(func_child, source_code)
                    elif func_child.type == 'parameter_list':
                        for param in func_child.children:
                            if param.type == 'parameter_declaration':
                                param_info = {
                                    'type': '',
                                    'name': ''
                                }
                                for param_child in param.children:
                                    if param_child.type == 'type_identifier':
                                        param_info['type'] = self.extract_node_text(param_child, source_code)
                                    elif param_child.type == 'identifier':
                                        param_info['name'] = self.extract_node_text(param_child, source_code)
                                func_info['parameters'].append(param_info)
            elif child.type == 'type_identifier':
                func_info['return_type'] = self.extract_node_text(child, source_code)
            elif child.type == 'virtual_specifier':
                func_info['is_virtual'] = True
            elif child.type == 'static_specifier':
                func_info['is_static'] = True
            elif child.type == 'const_specifier':
                func_info['is_const'] = True
        
        return func_info
    
    def extract_global_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract C++ global variable information."""
        global_info = {
            'name': '',
            'type': '',
            'value': None
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                global_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == 'init_declarator':
                for init_child in child.children:
                    if init_child.type == 'identifier':
                        global_info['name'] = self.extract_node_text(init_child, source_code)
                    elif init_child.type == '=':
                        global_info['value'] = self.extract_node_text(init_child.children[1], source_code)
        
        return global_info if global_info['name'] else None
    
    def extract_field_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract C++ field information."""
        field_info = {
            'name': '',
            'type': '',
            'value': None
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                field_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == 'init_declarator':
                for init_child in child.children:
                    if init_child.type == 'identifier':
                        field_info['name'] = self.extract_node_text(init_child, source_code)
                    elif init_child.type == '=':
                        field_info['value'] = self.extract_node_text(init_child.children[1], source_code)
        
        return field_info if field_info['name'] else None 