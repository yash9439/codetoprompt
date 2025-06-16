from typing import Dict, List, Optional, Any
import tree_sitter
from .base import BaseAnalyser

class JavaAnalyser(BaseAnalyser):
    """Analyser for Java code files."""
    
    def extract_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from Java code."""
        structure = {
            'imports': [],
            'package': None,
            'classes': [],
            'interfaces': [],
            'enums': []
        }
        
        def traverse(node):
            if node.type == 'import_declaration':
                import_text = self.extract_node_text(node, source_code).strip()
                structure['imports'].append(import_text)
            elif node.type == 'package_declaration':
                package_text = self.extract_node_text(node, source_code).strip()
                structure['package'] = package_text.replace('package', '').strip(';')
            elif node.type == 'class_declaration':
                class_info = self.extract_class_info(node, source_code)
                structure['classes'].append(class_info)
            elif node.type == 'interface_declaration':
                interface_info = self.extract_interface_info(node, source_code)
                structure['interfaces'].append(interface_info)
            elif node.type == 'enum_declaration':
                enum_info = self.extract_enum_info(node, source_code)
                structure['enums'].append(enum_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java class information."""
        class_info = {
            'name': '',
            'modifiers': [],
            'extends': None,
            'implements': [],
            'fields': [],
            'methods': [],
            'constructors': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for mod in child.children:
                    class_info['modifiers'].append(self.extract_node_text(mod, source_code))
            elif child.type == 'identifier':
                class_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'superclass':
                extends_text = self.extract_node_text(child, source_code)
                class_info['extends'] = extends_text.replace('extends', '').strip()
            elif child.type == 'super_interfaces':
                implements_text = self.extract_node_text(child, source_code)
                class_info['implements'] = [i.strip() for i in implements_text.replace('implements', '').split(',')]
            elif child.type == 'class_body':
                for stmt in child.children:
                    if stmt.type == 'field_declaration':
                        field_info = self.extract_field_info(stmt, source_code)
                        if field_info:
                            class_info['fields'].append(field_info)
                    elif stmt.type == 'method_declaration':
                        method_info = self.extract_method_info(stmt, source_code)
                        class_info['methods'].append(method_info)
                    elif stmt.type == 'constructor_declaration':
                        constructor_info = self.extract_constructor_info(stmt, source_code)
                        class_info['constructors'].append(constructor_info)
        
        return class_info
    
    def extract_interface_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java interface information."""
        interface_info = {
            'name': '',
            'modifiers': [],
            'extends': [],
            'methods': [],
            'fields': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for mod in child.children:
                    interface_info['modifiers'].append(self.extract_node_text(mod, source_code))
            elif child.type == 'identifier':
                interface_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'extends_interfaces':
                extends_text = self.extract_node_text(child, source_code)
                interface_info['extends'] = [i.strip() for i in extends_text.replace('extends', '').split(',')]
            elif child.type == 'interface_body':
                for stmt in child.children:
                    if stmt.type == 'field_declaration':
                        field_info = self.extract_field_info(stmt, source_code)
                        if field_info:
                            interface_info['fields'].append(field_info)
                    elif stmt.type == 'method_declaration':
                        method_info = self.extract_method_info(stmt, source_code)
                        interface_info['methods'].append(method_info)
        
        return interface_info
    
    def extract_enum_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java enum information."""
        enum_info = {
            'name': '',
            'modifiers': [],
            'implements': [],
            'constants': [],
            'fields': [],
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for mod in child.children:
                    enum_info['modifiers'].append(self.extract_node_text(mod, source_code))
            elif child.type == 'identifier':
                enum_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'super_interfaces':
                implements_text = self.extract_node_text(child, source_code)
                enum_info['implements'] = [i.strip() for i in implements_text.replace('implements', '').split(',')]
            elif child.type == 'enum_body':
                for stmt in child.children:
                    if stmt.type == 'enum_constant':
                        const_info = self.extract_enum_constant_info(stmt, source_code)
                        enum_info['constants'].append(const_info)
                    elif stmt.type == 'field_declaration':
                        field_info = self.extract_field_info(stmt, source_code)
                        if field_info:
                            enum_info['fields'].append(field_info)
                    elif stmt.type == 'method_declaration':
                        method_info = self.extract_method_info(stmt, source_code)
                        enum_info['methods'].append(method_info)
        
        return enum_info
    
    def extract_field_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract Java field information."""
        field_info = {
            'name': '',
            'type': '',
            'modifiers': [],
            'value': None
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for mod in child.children:
                    field_info['modifiers'].append(self.extract_node_text(mod, source_code))
            elif child.type == 'type':
                field_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == 'variable_declarator':
                name_node = child.children[0]
                if name_node.type == 'identifier':
                    field_info['name'] = self.extract_node_text(name_node, source_code)
                    if len(child.children) > 1:
                        field_info['value'] = self.extract_node_text(child.children[1], source_code)
        
        return field_info if field_info['name'] else None
    
    def extract_method_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java method information."""
        method_info = {
            'name': '',
            'return_type': '',
            'modifiers': [],
            'parameters': [],
            'throws': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for mod in child.children:
                    method_info['modifiers'].append(self.extract_node_text(mod, source_code))
            elif child.type == 'type':
                method_info['return_type'] = self.extract_node_text(child, source_code)
            elif child.type == 'identifier':
                method_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'formal_parameter':
                        param_info = {
                            'type': '',
                            'name': ''
                        }
                        for param_child in param.children:
                            if param_child.type == 'type':
                                param_info['type'] = self.extract_node_text(param_child, source_code)
                            elif param_child.type == 'identifier':
                                param_info['name'] = self.extract_node_text(param_child, source_code)
                        method_info['parameters'].append(param_info)
            elif child.type == 'throws':
                throws_text = self.extract_node_text(child, source_code)
                method_info['throws'] = [t.strip() for t in throws_text.replace('throws', '').split(',')]
        
        return method_info
    
    def extract_constructor_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java constructor information."""
        constructor_info = {
            'name': '',
            'modifiers': [],
            'parameters': [],
            'throws': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for mod in child.children:
                    constructor_info['modifiers'].append(self.extract_node_text(mod, source_code))
            elif child.type == 'identifier':
                constructor_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'formal_parameter':
                        param_info = {
                            'type': '',
                            'name': ''
                        }
                        for param_child in param.children:
                            if param_child.type == 'type':
                                param_info['type'] = self.extract_node_text(param_child, source_code)
                            elif param_child.type == 'identifier':
                                param_info['name'] = self.extract_node_text(param_child, source_code)
                        constructor_info['parameters'].append(param_info)
            elif child.type == 'throws':
                throws_text = self.extract_node_text(child, source_code)
                constructor_info['throws'] = [t.strip() for t in throws_text.replace('throws', '').split(',')]
        
        return constructor_info
    
    def extract_enum_constant_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, str]:
        """Extract Java enum constant information."""
        return {
            'name': self.extract_node_text(node.children[0], source_code)
        } 