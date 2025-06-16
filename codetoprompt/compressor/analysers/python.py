from typing import Dict, List, Optional, Any
import tree_sitter
from .base import BaseAnalyser

class PythonAnalyser(BaseAnalyser):
    """Analyser for Python code files."""
    
    def extract_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from Python code."""
        structure = {
            'imports': [],
            'classes': [],
            'functions': [],
            'constants': []
        }
        
        def traverse(node):
            if node.type == 'import_statement' or node.type == 'import_from_statement':
                import_text = self.extract_node_text(node, source_code).strip()
                structure['imports'].append(import_text)
            
            elif node.type == 'class_definition':
                class_info = self.extract_class_info(node, source_code)
                structure['classes'].append(class_info)
            
            elif node.type == 'function_definition':
                func_info = self.extract_function_info(node, source_code)
                structure['functions'].append(func_info)
            
            elif node.type == 'assignment':
                # Check if it's a module-level constant (uppercase variable)
                if node.parent and node.parent.type == 'module':
                    const_info = self.extract_constant_info(node, source_code)
                    if const_info:
                        structure['constants'].append(const_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Python class information."""
        class_info = {
            'name': '',
            'docstring': None,
            'methods': [],
            'inheritance': []
        }
        
        for child in node.children:
            if child.type == 'identifier':
                class_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'argument_list':  # inheritance
                inheritance_text = self.extract_node_text(child, source_code)
                class_info['inheritance'] = inheritance_text.strip('()')
            elif child.type == 'block':
                # Look for docstring and methods in the block
                for stmt in child.children:
                    if stmt.type == 'expression_statement':
                        # Check if it's a docstring
                        expr = stmt.children[0] if stmt.children else None
                        if expr and expr.type == 'string':
                            if class_info['docstring'] is None:  # First string is docstring
                                docstring = self.extract_node_text(expr, source_code)
                                class_info['docstring'] = self.clean_docstring(docstring)
                    elif stmt.type == 'function_definition':
                        method_info = self.extract_function_info(stmt, source_code)
                        class_info['methods'].append(method_info)
        
        return class_info
    
    def extract_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Python function information."""
        func_info = {
            'name': '',
            'parameters': '',
            'docstring': None,
            'return_type': None,
            'is_async': False
        }
        
        for child in node.children:
            if child.type == 'identifier':
                func_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'parameters':
                func_info['parameters'] = self.extract_node_text(child, source_code)
            elif child.type == 'type':  # return type annotation
                func_info['return_type'] = self.extract_node_text(child, source_code)
            elif child.type == 'async':
                func_info['is_async'] = True
            elif child.type == 'block':
                # Look for docstring in the block
                for stmt in child.children:
                    if stmt.type == 'expression_statement':
                        expr = stmt.children[0] if stmt.children else None
                        if expr and expr.type == 'string':
                            docstring = self.extract_node_text(expr, source_code)
                            func_info['docstring'] = self.clean_docstring(docstring)
                            break
        
        return func_info
    
    def extract_constant_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, str]]:
        """Extract Python constant information."""
        # Check if it's a module-level constant (uppercase variable)
        if node.type == 'assignment':
            left = node.children[0]
            if left.type == 'identifier':
                name = self.extract_node_text(left, source_code)
                if name.isupper():  # Only consider uppercase variables as constants
                    value = self.extract_node_text(node.children[1], source_code)
                    return {
                        'name': name,
                        'value': value
                    }
        return None 