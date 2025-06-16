from typing import Dict, List, Optional, Any
import tree_sitter
from .base import BaseAnalyser

class JavaScriptAnalyser(BaseAnalyser):
    """Analyser for JavaScript/TypeScript code files."""
    
    def extract_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from JavaScript code."""
        structure = {
            'imports': [],
            'classes': [],
            'functions': [],
            'constants': []
        }
        
        def traverse(node):
            if node.type == 'import_statement':
                import_text = self.extract_node_text(node, source_code).strip()
                structure['imports'].append(import_text)
            
            elif node.type == 'class_declaration':
                class_info = self.extract_class_info(node, source_code)
                structure['classes'].append(class_info)
            
            elif node.type == 'function_declaration':
                func_info = self.extract_function_info(node, source_code)
                structure['functions'].append(func_info)
            
            elif node.type == 'variable_declaration':
                # Check if it's a module-level constant
                if node.parent and node.parent.type == 'program':
                    const_info = self.extract_constant_info(node, source_code)
                    if const_info:
                        structure['constants'].append(const_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract JavaScript class information."""
        class_info = {
            'name': '',
            'extends': None,
            'implements': [],
            'methods': [],
            'properties': []
        }
        
        for child in node.children:
            if child.type == 'identifier':
                class_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'extends_clause':
                extends_text = self.extract_node_text(child, source_code)
                class_info['extends'] = extends_text.replace('extends', '').strip()
            elif child.type == 'implements_clause':
                implements_text = self.extract_node_text(child, source_code)
                class_info['implements'] = [i.strip() for i in implements_text.replace('implements', '').split(',')]
            elif child.type == 'class_body':
                for stmt in child.children:
                    if stmt.type == 'method_definition':
                        method_info = self.extract_method_info(stmt, source_code)
                        class_info['methods'].append(method_info)
                    elif stmt.type == 'property_definition':
                        prop_info = self.extract_property_info(stmt, source_code)
                        class_info['properties'].append(prop_info)
        
        return class_info
    
    def extract_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract JavaScript function information."""
        func_info = {
            'name': '',
            'parameters': '',
            'is_async': False,
            'is_generator': False,
            'return_type': None
        }
        
        for child in node.children:
            if child.type == 'identifier':
                func_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'formal_parameters':
                func_info['parameters'] = self.extract_node_text(child, source_code)
            elif child.type == 'async':
                func_info['is_async'] = True
            elif child.type == 'generator_function':
                func_info['is_generator'] = True
            elif child.type == 'type_annotation':
                func_info['return_type'] = self.extract_node_text(child, source_code)
        
        return func_info
    
    def extract_method_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract JavaScript method information."""
        method_info = {
            'name': '',
            'parameters': '',
            'is_async': False,
            'is_generator': False,
            'is_static': False,
            'is_private': False,
            'return_type': None
        }
        
        for child in node.children:
            if child.type == 'property_identifier':
                method_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'formal_parameters':
                method_info['parameters'] = self.extract_node_text(child, source_code)
            elif child.type == 'async':
                method_info['is_async'] = True
            elif child.type == 'generator_function':
                method_info['is_generator'] = True
            elif child.type == 'static':
                method_info['is_static'] = True
            elif child.type == 'private_property_identifier':
                method_info['is_private'] = True
            elif child.type == 'type_annotation':
                method_info['return_type'] = self.extract_node_text(child, source_code)
        
        return method_info
    
    def extract_property_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract JavaScript property information."""
        prop_info = {
            'name': '',
            'type': None,
            'is_static': False,
            'is_private': False,
            'value': None
        }
        
        for child in node.children:
            if child.type == 'property_identifier':
                prop_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'type_annotation':
                prop_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == 'static':
                prop_info['is_static'] = True
            elif child.type == 'private_property_identifier':
                prop_info['is_private'] = True
            elif child.type == '=':
                prop_info['value'] = self.extract_node_text(child.children[1], source_code)
        
        return prop_info
    
    def extract_constant_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, str]]:
        """Extract JavaScript constant information."""
        if node.type == 'variable_declaration':
            for child in node.children:
                if child.type == 'variable_declarator':
                    name_node = child.children[0]
                    if name_node.type == 'identifier':
                        name = self.extract_node_text(name_node, source_code)
                        if name.isupper():  # Only consider uppercase variables as constants
                            value = self.extract_node_text(child.children[1], source_code)
                            return {
                                'name': name,
                                'value': value
                            }
        return None 