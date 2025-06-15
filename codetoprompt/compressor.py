# codetoprompt/compressor.py
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from tree_sitter_language_pack import get_language, get_parser
import tree_sitter

class FileAnalyzer:
    """Analyzes files to detect language and extract compressed structure."""
    
    # Language mappings based on file extensions
    EXTENSION_TO_LANGUAGE = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rs': 'rust'
    }
    
    def __init__(self):
        self.parsers = {}
        self.languages = {}
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect the programming language of a file based on extension and content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name if detected, None otherwise
        """
        path = Path(file_path)
        
        # Check by extension first
        ext = path.suffix.lower()
        if ext in self.EXTENSION_TO_LANGUAGE:
            return self.EXTENSION_TO_LANGUAGE[ext]
        
        # Try to detect by shebang or content patterns
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                
            if first_line.startswith('#!'):
                if 'python' in first_line:
                    return 'python'
                elif 'node' in first_line:
                    return 'javascript'
        except Exception:
            pass
        
        # If we couldn't detect the language, return None
        return None
    
    def get_parser_for_language(self, language: str) -> Optional[tree_sitter.Parser]:
        """Get or create a parser for the specified language."""
        if language not in self.parsers:
            try:
                lang = get_language(language)
                parser = get_parser(language)
                self.languages[language] = lang
                self.parsers[language] = parser
                return parser
            except Exception as e:
                print(f"Failed to get parser for {language}: {e}")
                return None
        return self.parsers[language]
    
    def extract_node_text(self, node: tree_sitter.Tree, source_code: bytes) -> str:
        """Extract text from a tree-sitter node."""
        if not node or not source_code:
            return ""
        try:
            return source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
        except Exception:
            return ""
    
    def extract_preceding_comment(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[str]:
        """Extract comment or javadoc that precedes a node."""
        if not node.parent:
            return None
        
        # Look for comment nodes before this node
        parent = node.parent
        node_index = None
        for i, child in enumerate(parent.children):
            if child == node:
                node_index = i
                break
        
        if node_index is None or node_index == 0:
            return None
        
        # Check previous siblings for comments
        for i in range(node_index - 1, -1, -1):
            sibling = parent.children[i]
            if sibling.type in ['line_comment', 'block_comment']:
                comment_text = self.extract_node_text(sibling, source_code)
                return self.clean_comment(comment_text)
            elif sibling.type not in ['modifiers']:  # Stop if we hit non-modifier, non-comment
                break
        
        return None
    
    def clean_comment(self, comment: str) -> str:
        """Clean and format comment."""
        # Remove comment markers
        comment = comment.strip()
        if comment.startswith('/**') and comment.endswith('*/'):
            # Javadoc
            comment = comment[3:-2].strip()
        elif comment.startswith('/*') and comment.endswith('*/'):
            # Block comment
            comment = comment[2:-2].strip()
        elif comment.startswith('//'):
            # Line comment
            comment = comment[2:].strip()
        elif comment.startswith('#'):
            # Python comment
            comment = comment[1:].strip()
        
        # Clean up formatting
        lines = comment.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('*'):
                line = line[1:].strip()
            if line and not line.startswith('@'):  # Skip javadoc tags for now
                cleaned_lines.append(line)
        
        result = ' '.join(cleaned_lines)
        return result[:200] + ('...' if len(result) > 200 else '')
    
    def format_java_parameters(self, parameters: List[Dict[str, str]]) -> str:
        """Format Java parameters for display."""
        if not parameters:
            return ""
        
        param_strings = []
        for param in parameters:
            if isinstance(param, dict):
                param_strings.append(f"{param['type']} {param['name']}")
            else:
                param_strings.append(str(param))
        
        return ", ".join(param_strings)
    
    def extract_python_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
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
                class_info = self.extract_python_class_info(node, source_code)
                structure['classes'].append(class_info)
            
            elif node.type == 'function_definition':
                func_info = self.extract_python_function_info(node, source_code)
                structure['functions'].append(func_info)
            
            elif node.type == 'assignment':
                # Check if it's a module-level constant (uppercase variable)
                if node.parent and node.parent.type == 'module':
                    const_info = self.extract_python_constant_info(node, source_code)
                    if const_info:
                        structure['constants'].append(const_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_python_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
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
                        method_info = self.extract_python_function_info(stmt, source_code)
                        class_info['methods'].append(method_info)
        
        return class_info
    
    def extract_python_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
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
                            break  # First string is the docstring
        
        return func_info
    
    def extract_python_constant_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, str]]:
        """Extract Python constant information (uppercase variables)."""
        for child in node.children:
            if child.type == 'identifier':
                name = self.extract_node_text(child, source_code)
                if name.isupper() and len(name) > 1:  # Convention for constants
                    value_node = None
                    for sibling in node.children:
                        if sibling != child and sibling.type != '=':
                            value_node = sibling
                            break
                    
                    value = self.extract_node_text(value_node, source_code) if value_node else '...'
                    return {'name': name, 'value': value[:50] + '...' if len(value) > 50 else value}
        return None
    
    def clean_docstring(self, docstring: str) -> str:
        """Clean and format docstring."""
        # Remove quotes and clean up
        docstring = docstring.strip('\'"')
        lines = docstring.split('\n')
        # Take first line and maybe second if first is very short
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 20 and len(lines) > 1:
                return (first_line + ' ' + lines[1].strip())[:100] + '...'
            return first_line[:100] + ('...' if len(first_line) > 100 else '')
        return docstring
    
    def extract_javascript_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from JavaScript/TypeScript code."""
        structure = {
            'imports': [],
            'exports': [],
            'functions': [],
            'classes': [],
            'constants': []
        }
        
        def traverse(node):
            if node.type in ['import_statement', 'import_declaration']:
                import_text = self.extract_node_text(node, source_code).strip()
                structure['imports'].append(import_text)
            
            elif node.type in ['export_statement', 'export_declaration']:
                export_text = self.extract_node_text(node, source_code).strip()
                structure['exports'].append(export_text)
            
            elif node.type in ['function_declaration', 'function_expression', 'arrow_function']:
                func_info = self.extract_js_function_info(node, source_code)
                structure['functions'].append(func_info)
            
            elif node.type == 'class_declaration':
                class_info = self.extract_js_class_info(node, source_code)
                structure['classes'].append(class_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_js_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract JavaScript function information."""
        func_info = {
            'name': 'anonymous',
            'parameters': [],
            'is_async': False,
            'return_type': None
        }
        
        # Check if async
        if any(child.type == 'async' for child in node.children):
            func_info['is_async'] = True
        
        for child in node.children:
            if child.type == 'identifier':
                func_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'identifier':
                        param_info = {
                            'name': self.extract_node_text(param, source_code),
                            'type': 'any'  # Default type for JavaScript
                        }
                        func_info['parameters'].append(param_info)
                    elif param.type == 'required_parameter':
                        for param_child in param.children:
                            if param_child.type == 'identifier':
                                param_info = {
                                    'name': self.extract_node_text(param_child, source_code),
                                    'type': 'any'  # Default type for JavaScript
                                }
                                func_info['parameters'].append(param_info)
            elif child.type == 'type_annotation':
                func_info['return_type'] = self.extract_node_text(child, source_code)
        
        return func_info
    
    def extract_js_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract JavaScript class information."""
        class_info = {
            'name': '',
            'extends': None,
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'identifier':
                class_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'class_heritage':
                class_info['extends'] = self.extract_node_text(child, source_code)
            elif child.type == 'class_body':
                for method in child.children:
                    if method.type in ['method_definition', 'function_expression']:
                        method_info = self.extract_js_function_info(method, source_code)
                        class_info['methods'].append(method_info)
        
        return class_info
    
    def extract_java_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from Java code."""
        structure = {
            'package': None,
            'imports': [],
            'classes': [],
            'interfaces': [],
            'enums': []
        }
        
        def traverse(node):
            if node.type == 'package_declaration':
                structure['package'] = self.extract_node_text(node, source_code).strip()
            
            elif node.type == 'import_declaration':
                import_text = self.extract_node_text(node, source_code).strip()
                structure['imports'].append(import_text)
            
            elif node.type == 'class_declaration':
                class_info = self.extract_java_class_info(node, source_code)
                structure['classes'].append(class_info)
            
            elif node.type == 'interface_declaration':
                interface_info = self.extract_java_interface_info(node, source_code)
                structure['interfaces'].append(interface_info)
            
            elif node.type == 'enum_declaration':
                enum_info = self.extract_java_enum_info(node, source_code)
                structure['enums'].append(enum_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_java_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
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
                for modifier in child.children:
                    if modifier.type == 'modifier':
                        class_info['modifiers'].append(self.extract_node_text(modifier, source_code))
            
            elif child.type == 'identifier':
                class_info['name'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'superclass':
                class_info['extends'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'super_interfaces':
                for interface in child.children:
                    if interface.type == 'type_identifier':
                        class_info['implements'].append(self.extract_node_text(interface, source_code))
            
            elif child.type == 'class_body':
                for member in child.children:
                    if member.type == 'field_declaration':
                        field_info = self.extract_java_field_info(member, source_code)
                        if field_info:
                            class_info['fields'].append(field_info)
                    elif member.type == 'method_declaration':
                        method_info = self.extract_java_method_info(member, source_code)
                        class_info['methods'].append(method_info)
                    elif member.type == 'constructor_declaration':
                        constructor_info = self.extract_java_constructor_info(member, source_code)
                        class_info['constructors'].append(constructor_info)
        
        return class_info
    
    def extract_java_interface_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java interface information."""
        interface_info = {
            'name': '',
            'modifiers': [],
            'extends': [],
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type == 'modifier':
                        interface_info['modifiers'].append(self.extract_node_text(modifier, source_code))
            
            elif child.type == 'identifier':
                interface_info['name'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'extends_interfaces':
                for interface in child.children:
                    if interface.type == 'type_identifier':
                        interface_info['extends'].append(self.extract_node_text(interface, source_code))
            
            elif child.type == 'interface_body':
                for member in child.children:
                    if member.type == 'method_declaration':
                        method_info = self.extract_java_method_info(member, source_code)
                        interface_info['methods'].append(method_info)
        
        return interface_info
    
    def extract_java_enum_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java enum information."""
        enum_info = {
            'name': '',
            'modifiers': [],
            'constants': [],
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type == 'modifier':
                        enum_info['modifiers'].append(self.extract_node_text(modifier, source_code))
            
            elif child.type == 'identifier':
                enum_info['name'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'enum_body':
                for member in child.children:
                    if member.type == 'enum_constant':
                        constant_info = self.extract_java_enum_constant_info(member, source_code)
                        enum_info['constants'].append(constant_info)
                    elif member.type == 'method_declaration':
                        method_info = self.extract_java_method_info(member, source_code)
                        enum_info['methods'].append(method_info)
        
        return enum_info
    
    def extract_java_field_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract Java field information."""
        field_info = {
            'name': '',
            'type': '',
            'modifiers': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type == 'modifier':
                        field_info['modifiers'].append(self.extract_node_text(modifier, source_code))
            
            elif child.type == 'type':
                field_info['type'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'variable_declarator':
                for var_child in child.children:
                    if var_child.type == 'identifier':
                        field_info['name'] = self.extract_node_text(var_child, source_code)
        
        return field_info if field_info['name'] else None
    
    def extract_java_method_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java method information."""
        method_info = {
            'name': '',
            'return_type': '',
            'parameters': [],
            'modifiers': [],
            'is_abstract': False
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type == 'modifier':
                        mod = self.extract_node_text(modifier, source_code)
                        method_info['modifiers'].append(mod)
                        if mod == 'abstract':
                            method_info['is_abstract'] = True
            
            elif child.type == 'type':
                method_info['return_type'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'identifier':
                method_info['name'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'parameter':
                        param_info = {
                            'name': '',
                            'type': ''
                        }
                        for param_child in param.children:
                            if param_child.type == 'identifier':
                                param_info['name'] = self.extract_node_text(param_child, source_code)
                            elif param_child.type == 'type':
                                param_info['type'] = self.extract_node_text(param_child, source_code)
                        if param_info['name']:
                            method_info['parameters'].append(param_info)
        
        return method_info
    
    def extract_java_constructor_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Java constructor information."""
        constructor_info = {
            'name': '',
            'parameters': [],
            'modifiers': []
        }
        
        for child in node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type == 'modifier':
                        constructor_info['modifiers'].append(self.extract_node_text(modifier, source_code))
            
            elif child.type == 'identifier':
                constructor_info['name'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'parameter':
                        param_info = {
                            'name': '',
                            'type': ''
                        }
                        for param_child in param.children:
                            if param_child.type == 'identifier':
                                param_info['name'] = self.extract_node_text(param_child, source_code)
                            elif param_child.type == 'type':
                                param_info['type'] = self.extract_node_text(param_child, source_code)
                        if param_info['name']:
                            constructor_info['parameters'].append(param_info)
        
        return constructor_info
    
    def extract_java_enum_constant_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, str]:
        """Extract Java enum constant information."""
        return {
            'name': self.extract_node_text(node, source_code).strip()
        }
    
    def extract_generic_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Generic structure extraction for unsupported languages."""
        return {
            'functions': [],
            'classes': [],
            'note': 'Generic parsing - limited structure extraction'
        }
    
    def extract_c_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from C code."""
        structure = {
            'includes': [],
            'structs': [],
            'unions': [],
            'enums': [],
            'typedefs': [],
            'functions': [],
            'macros': [],
            'globals': []
        }
        
        def traverse(node, is_inside_function=False):
            if node.type == 'preproc_include':
                include_text = self.extract_node_text(node, source_code).strip()
                structure['includes'].append(include_text)
            
            elif node.type == 'preproc_def':
                macro_text = self.extract_node_text(node, source_code).strip()
                structure['macros'].append(macro_text)
            
            elif node.type == 'struct_specifier':
                struct_info = self.extract_c_struct_info(node, source_code)
                structure['structs'].append(struct_info)
            
            elif node.type == 'union_specifier':
                union_info = self.extract_c_union_info(node, source_code)
                structure['unions'].append(union_info)
            
            elif node.type == 'enum_specifier':
                enum_info = self.extract_c_enum_info(node, source_code)
                structure['enums'].append(enum_info)
            
            elif node.type == 'type_definition':
                typedef_info = self.extract_c_typedef_info(node, source_code)
                structure['typedefs'].append(typedef_info)
            
            elif node.type == 'function_definition':
                func_info = self.extract_c_function_info(node, source_code)
                structure['functions'].append(func_info)
                for child in node.children:
                    traverse(child, True)
                return
            
            elif node.type == 'declaration' and not is_inside_function:
                global_info = self.extract_c_global_info(node, source_code)
                if global_info:
                    structure['globals'].append(global_info)
            
            for child in node.children:
                traverse(child, is_inside_function)
        
        traverse(tree.root_node)
        return structure
    
    def extract_c_struct_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C struct information."""
        struct_info = {
            'name': '',
            'fields': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                struct_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'field_declaration':
                        field_info = self.extract_c_field_info(field, source_code)
                        if field_info:
                            struct_info['fields'].append(field_info)
        
        return struct_info
    
    def extract_c_union_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C union information."""
        union_info = {
            'name': '',
            'fields': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                union_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'field_declaration':
                        field_info = self.extract_c_field_info(field, source_code)
                        if field_info:
                            union_info['fields'].append(field_info)
        
        return union_info
    
    def extract_c_enum_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C enum information."""
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
                        enum_info['enumerators'].append(self.extract_node_text(enumerator, source_code))
        
        return enum_info
    
    def extract_c_typedef_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, str]:
        """Extract C typedef information."""
        typedef_info = {
            'name': '',
            'type': ''
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                typedef_info['name'] = self.extract_node_text(child, source_code)
            elif child.type in ['primitive_type', 'type_identifier']:
                typedef_info['type'] = self.extract_node_text(child, source_code)
        
        return typedef_info
    
    def extract_c_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C function information."""
        func_info = {
            'name': '',
            'return_type': '',
            'parameters': [],
            'is_static': False,
            'is_inline': False
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
                                    'name': '',
                                    'type': ''
                                }
                                for param_child in param.children:
                                    if param_child.type == 'identifier':
                                        param_info['name'] = self.extract_node_text(param_child, source_code)
                                    elif param_child.type in ['primitive_type', 'type_identifier']:
                                        param_info['type'] = self.extract_node_text(param_child, source_code)
                                if param_info['name']:
                                    func_info['parameters'].append(param_info)
            
            elif child.type == 'primitive_type':
                func_info['return_type'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'storage_class_specifier':
                spec = self.extract_node_text(child, source_code)
                if spec == 'static':
                    func_info['is_static'] = True
                elif spec == 'inline':
                    func_info['is_inline'] = True
        
        return func_info
    
    def extract_c_global_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract C global variable information."""
        global_info = {
            'name': '',
            'type': '',
            'is_static': False,
            'is_extern': False
        }
        
        for child in node.children:
            if child.type == 'storage_class_specifier':
                spec = self.extract_node_text(child, source_code)
                if spec == 'static':
                    global_info['is_static'] = True
                elif spec == 'extern':
                    global_info['is_extern'] = True
            
            elif child.type == 'primitive_type':
                global_info['type'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'init_declarator':
                for init_child in child.children:
                    if init_child.type == 'identifier':
                        global_info['name'] = self.extract_node_text(init_child, source_code)
        
        return global_info if global_info['name'] else None
    
    def extract_c_field_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, str]]:
        """Extract C struct/union field information."""
        field_info = {
            'name': '',
            'type': ''
        }
        
        for child in node.children:
            if child.type in ['primitive_type', 'type_identifier']:
                field_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == 'field_identifier':
                field_info['name'] = self.extract_node_text(child, source_code)
        
        return field_info if field_info['name'] else None
    
    def extract_cpp_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from C++ code."""
        structure = {
            'includes': [],
            'namespaces': [],
            'classes': [],
            'structs': [],
            'enums': [],
            'typedefs': [],
            'functions': [],
            'macros': [],
            'globals': []
        }
        
        def traverse(node, is_inside_function=False):
            if node.type == 'preproc_include':
                include_text = self.extract_node_text(node, source_code).strip()
                structure['includes'].append(include_text)
            
            elif node.type == 'preproc_def':
                macro_text = self.extract_node_text(node, source_code).strip()
                structure['macros'].append(macro_text)
            
            elif node.type == 'namespace_definition':
                namespace_info = self.extract_cpp_namespace_info(node, source_code)
                structure['namespaces'].append(namespace_info)
            
            elif node.type == 'class_specifier':
                class_info = self.extract_cpp_class_info(node, source_code)
                structure['classes'].append(class_info)
            
            elif node.type == 'struct_specifier':
                struct_info = self.extract_cpp_struct_info(node, source_code)
                structure['structs'].append(struct_info)
            
            elif node.type == 'enum_specifier':
                enum_info = self.extract_cpp_enum_info(node, source_code)
                structure['enums'].append(enum_info)
            
            elif node.type == 'type_definition':
                typedef_info = self.extract_cpp_typedef_info(node, source_code)
                structure['typedefs'].append(typedef_info)
            
            elif node.type == 'function_definition':
                func_info = self.extract_cpp_function_info(node, source_code)
                structure['functions'].append(func_info)
                for child in node.children:
                    traverse(child, True)
                return
            
            elif node.type == 'declaration' and not is_inside_function:
                global_info = self.extract_cpp_global_info(node, source_code)
                if global_info:
                    structure['globals'].append(global_info)
            
            for child in node.children:
                traverse(child, is_inside_function)
        
        traverse(tree.root_node)
        return structure
    
    def extract_cpp_namespace_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ namespace information."""
        namespace_info = {
            'name': '',
            'classes': [],
            'structs': [],
            'functions': [],
            'enums': [],
            'typedefs': []
        }
        
        for child in node.children:
            if child.type == 'namespace_identifier':
                namespace_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'declaration_list':
                for decl in child.children:
                    if decl.type == 'class_specifier':
                        class_info = self.extract_cpp_class_info(decl, source_code)
                        namespace_info['classes'].append(class_info)
                    elif decl.type == 'struct_specifier':
                        struct_info = self.extract_cpp_struct_info(decl, source_code)
                        namespace_info['structs'].append(struct_info)
                    elif decl.type == 'function_definition':
                        func_info = self.extract_cpp_function_info(decl, source_code)
                        namespace_info['functions'].append(func_info)
                    elif decl.type == 'enum_specifier':
                        enum_info = self.extract_cpp_enum_info(decl, source_code)
                        namespace_info['enums'].append(enum_info)
                    elif decl.type == 'type_definition':
                        typedef_info = self.extract_cpp_typedef_info(decl, source_code)
                        namespace_info['typedefs'].append(typedef_info)
        
        return namespace_info
    
    def extract_cpp_class_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ class information."""
        class_info = {
            'name': '',
            'base_classes': [],
            'access_specifiers': [],
            'methods': [],
            'fields': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                class_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'base_class_clause':
                for base in child.children:
                    if base.type == 'type_identifier':
                        class_info['base_classes'].append(self.extract_node_text(base, source_code))
            elif child.type == 'access_specifier':
                access = self.extract_node_text(child, source_code)
                class_info['access_specifiers'].append(access)
            elif child.type == 'field_declaration_list':
                for member in child.children:
                    if member.type == 'function_definition':
                        method_info = self.extract_cpp_function_info(member, source_code)
                        class_info['methods'].append(method_info)
                    elif member.type == 'field_declaration':
                        field_info = self.extract_cpp_field_info(member, source_code)
                        if field_info:
                            class_info['fields'].append(field_info)
        
        return class_info
    
    def extract_cpp_struct_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ struct information."""
        struct_info = {
            'name': '',
            'base_classes': [],
            'fields': [],
            'methods': []
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                struct_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'base_class_clause':
                for base in child.children:
                    if base.type == 'type_identifier':
                        struct_info['base_classes'].append(self.extract_node_text(base, source_code))
            elif child.type == 'field_declaration_list':
                for member in child.children:
                    if member.type == 'function_definition':
                        method_info = self.extract_cpp_function_info(member, source_code)
                        struct_info['methods'].append(method_info)
                    elif member.type == 'field_declaration':
                        field_info = self.extract_cpp_field_info(member, source_code)
                        if field_info:
                            struct_info['fields'].append(field_info)
        
        return struct_info
    
    def extract_cpp_enum_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ enum information."""
        enum_info = {
            'name': '',
            'enumerators': [],
            'is_class': False
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                enum_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'enum_class':
                enum_info['is_class'] = True
            elif child.type == 'enumerator_list':
                for enumerator in child.children:
                    if enumerator.type == 'enumerator':
                        enum_info['enumerators'].append(self.extract_node_text(enumerator, source_code))
        
        return enum_info
    
    def extract_cpp_typedef_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, str]:
        """Extract C++ typedef information."""
        typedef_info = {
            'name': '',
            'type': ''
        }
        
        for child in node.children:
            if child.type == 'type_identifier':
                typedef_info['name'] = self.extract_node_text(child, source_code)
            elif child.type in ['primitive_type', 'type_identifier', 'template_type']:
                typedef_info['type'] = self.extract_node_text(child, source_code)
        
        return typedef_info
    
    def extract_cpp_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract C++ function information."""
        func_info = {
            'name': '',
            'return_type': '',
            'parameters': [],
            'is_static': False,
            'is_virtual': False,
            'is_const': False,
            'is_override': False,
            'is_final': False
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
                                    'name': '',
                                    'type': ''
                                }
                                for param_child in param.children:
                                    if param_child.type == 'identifier':
                                        param_info['name'] = self.extract_node_text(param_child, source_code)
                                    elif param_child.type in ['primitive_type', 'type_identifier', 'template_type']:
                                        param_info['type'] = self.extract_node_text(param_child, source_code)
                                if param_info['name']:
                                    func_info['parameters'].append(param_info)
            
            elif child.type in ['primitive_type', 'type_identifier', 'template_type']:
                func_info['return_type'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'storage_class_specifier':
                spec = self.extract_node_text(child, source_code)
                if spec == 'static':
                    func_info['is_static'] = True
                elif spec == 'virtual':
                    func_info['is_virtual'] = True
            
            elif child.type == 'cv_qualifier':
                qual = self.extract_node_text(child, source_code)
                if qual == 'const':
                    func_info['is_const'] = True
            
            elif child.type == 'override_specifier':
                func_info['is_override'] = True
            
            elif child.type == 'final_specifier':
                func_info['is_final'] = True
        
        return func_info
    
    def extract_cpp_global_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract C++ global variable information."""
        global_info = {
            'name': '',
            'type': '',
            'is_static': False,
            'is_extern': False,
            'is_const': False
        }
        
        for child in node.children:
            if child.type == 'storage_class_specifier':
                spec = self.extract_node_text(child, source_code)
                if spec == 'static':
                    global_info['is_static'] = True
                elif spec == 'extern':
                    global_info['is_extern'] = True
            
            elif child.type in ['primitive_type', 'type_identifier', 'template_type']:
                global_info['type'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'cv_qualifier':
                qual = self.extract_node_text(child, source_code)
                if qual == 'const':
                    global_info['is_const'] = True
            
            elif child.type == 'init_declarator':
                for init_child in child.children:
                    if init_child.type == 'identifier':
                        global_info['name'] = self.extract_node_text(init_child, source_code)
        
        return global_info if global_info['name'] else None
    
    def extract_cpp_field_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract C++ class/struct field information."""
        field_info = {
            'name': '',
            'type': '',
            'is_static': False,
            'is_const': False,
            'is_mutable': False
        }
        
        for child in node.children:
            if child.type == 'storage_class_specifier':
                spec = self.extract_node_text(child, source_code)
                if spec == 'static':
                    field_info['is_static'] = True
                elif spec == 'mutable':
                    field_info['is_mutable'] = True
            
            elif child.type in ['primitive_type', 'type_identifier', 'template_type']:
                field_info['type'] = self.extract_node_text(child, source_code)
            
            elif child.type == 'cv_qualifier':
                qual = self.extract_node_text(child, source_code)
                if qual == 'const':
                    field_info['is_const'] = True
            
            elif child.type == 'field_identifier':
                field_info['name'] = self.extract_node_text(child, source_code)
        
        return field_info if field_info['name'] else None
    
    def format_compressed_prompt(self, file_path: str, language: str, structure: Dict[str, Any]) -> str:
        """Format the extracted structure into a compressed prompt."""
        prompt = f"# File: {file_path}\n"
        prompt += f"# Language: {language}\n\n"
        
        # Package (Java)
        if 'package' in structure and structure['package']:
            prompt += f"## Package:\n{structure['package']}\n\n"
        
        # Includes/Imports
        if 'includes' in structure and structure['includes']:
            prompt += "## Includes:\n"
            for inc in structure['includes'][:10]:  # Limit includes
                prompt += f"- {inc}\n"
            prompt += "\n"
        elif 'imports' in structure and structure['imports']:
            prompt += "## Imports:\n"
            for imp in structure['imports'][:10]:  # Limit imports
                prompt += f"- {imp}\n"
            prompt += "\n"
        
        # Namespaces (C++)
        if 'namespaces' in structure and structure['namespaces']:
            prompt += "## Namespaces:\n"
            for namespace in structure['namespaces']:
                prompt += f"### namespace {namespace['name']}:\n"
                if namespace.get('comment'):
                    prompt += f"    // {namespace['comment']}\n"
                for cls in namespace.get('classes', []):
                    prompt += f"    class {cls['name']};\n"
                for func in namespace.get('functions', []):
                    params_str = self.format_java_parameters(func['parameters'])
                    prompt += f"    {func['return_type']} {func['name']}({params_str});\n"
                prompt += "\n"
        
        # Modules (Rust)
        if 'modules' in structure and structure['modules']:
            prompt += "## Modules:\n"
            for module in structure['modules']:
                prompt += f"### mod {module['name']}:\n"
                if module.get('comment'):
                    prompt += f"    // {module['comment']}\n"
                for item in module.get('items', []):
                    prompt += f"    {item}\n"
                prompt += "\n"
        
        # Constants
        if 'constants' in structure and structure['constants']:
            prompt += "## Constants:\n"
            for const in structure['constants']:
                prompt += f"- {const['name']} = {const['value']}\n"
            prompt += "\n"
        
        # Interfaces (Java)
        if 'interfaces' in structure and structure['interfaces']:
            prompt += "## Interfaces:\n"
            for interface in structure['interfaces']:
                modifiers = ' '.join(interface['modifiers']) + ' ' if interface['modifiers'] else ''
                extends = f" extends {', '.join(interface['extends'])}" if interface['extends'] else ""
                prompt += f"### {modifiers}interface {interface['name']}{extends}:\n"
                if interface.get('comment'):
                    prompt += f"    // {interface['comment']}\n"
                
                for method in interface.get('methods', []):
                    modifiers_str = ' '.join(method['modifiers']) + ' ' if method['modifiers'] else ''
                    params_str = self.format_java_parameters(method['parameters'])
                    throws_str = f" throws {', '.join(method['throws'])}" if method.get('throws') else ""
                    prompt += f"    {modifiers_str}{method['return_type']} {method['name']}({params_str}){throws_str};\n"
                    if method.get('comment'):
                        prompt += f"        // {method['comment']}\n"
                prompt += "\n"
        
        # Traits (Rust)
        if 'traits' in structure and structure['traits']:
            prompt += "## Traits:\n"
            for trait in structure['traits']:
                prompt += f"### trait {trait['name']}:\n"
                if trait.get('comment'):
                    prompt += f"    // {trait['comment']}\n"
                for method in trait.get('methods', []):
                    params_str = ', '.join(f"{p['name']}: {p['type']}" for p in method['parameters'])
                    return_str = f" -> {method['return_type']}" if method['return_type'] else ""
                    prompt += f"    fn {method['name']}({params_str}){return_str};\n"
                    if method.get('comment'):
                        prompt += f"        // {method['comment']}\n"
                prompt += "\n"
        
        # Classes
        if 'classes' in structure and structure['classes']:
            prompt += "## Classes:\n"
            for cls in structure['classes']:
                # Handle different class formats
                if 'modifiers' in cls:  # Java class
                    modifiers = ' '.join(cls['modifiers']) + ' ' if cls['modifiers'] else ''
                    extends = f" extends {cls['extends']}" if cls.get('extends') else ""
                    implements = f" implements {', '.join(cls['implements'])}" if cls.get('implements') else ""
                    prompt += f"### {modifiers}class {cls['name']}{extends}{implements}:\n"
                elif 'base_classes' in cls:  # C++ class
                    base_classes = f" : {', '.join(cls['base_classes'])}" if cls['base_classes'] else ""
                    prompt += f"### class {cls['name']}{base_classes}:\n"
                else:  # Python class
                    inheritance = f"({cls['inheritance']})" if cls.get('inheritance') else ""
                    prompt += f"### class {cls['name']}{inheritance}:\n"
                
                if cls.get('comment'):
                    prompt += f"    // {cls['comment']}\n"
                elif cls.get('docstring'):
                    prompt += f"    \"\"\"{cls['docstring']}\"\"\"\n"
                
                # Fields
                for field in cls.get('fields', []):
                    if 'modifiers' in field:  # Java/C++ field
                        modifiers_str = ' '.join(field['modifiers']) + ' ' if field['modifiers'] else ''
                        prompt += f"    {modifiers_str}{field['type']} {field['name']};\n"
                        if field.get('comment'):
                            prompt += f"        // {field['comment']}\n"
                    else:  # Rust field
                        prompt += f"    {field['name']}: {field['type']},\n"
                
                # Methods
                for method in cls.get('methods', []):
                    if 'modifiers' in method:  # Java/C++ method
                        modifiers_str = ' '.join(method['modifiers']) + ' ' if method['modifiers'] else ''
                        params_str = self.format_java_parameters(method['parameters'])
                        throws_str = f" throws {', '.join(method['throws'])}" if method.get('throws') else ""
                        prompt += f"    {modifiers_str}{method['return_type']} {method['name']}({params_str}){throws_str} {{\n"
                        if method.get('comment'):
                            prompt += f"        // {method['comment']}\n"
                        prompt += f"        ...\n    }}\n"
                    else:  # Python/Rust method
                        if language == 'python':
                            prompt += f"    def {method['name']}{method['parameters']}:\n"
                            if method.get('docstring'):
                                prompt += f"        \"\"\"{method['docstring']}\"\"\"\n"
                            prompt += f"        ...\n"
                        else:  # Rust
                            params_str = ', '.join(f"{p['name']}: {p['type']}" for p in method['parameters'])
                            return_str = f" -> {method['return_type']}" if method['return_type'] else ""
                            prompt += f"    fn {method['name']}({params_str}){return_str} {{\n"
                            if method.get('comment'):
                                prompt += f"        // {method['comment']}\n"
                            prompt += f"        ...\n    }}\n"
                prompt += "\n"
        
        # Structs
        if 'structs' in structure and structure['structs']:
            prompt += "## Structs:\n"
            for struct in structure['structs']:
                if 'base_classes' in struct:  # C++ struct
                    base_classes = f" : {', '.join(struct['base_classes'])}" if struct['base_classes'] else ""
                    prompt += f"### struct {struct['name']}{base_classes}:\n"
                else:  # C/Rust struct
                    prompt += f"### struct {struct['name']}:\n"
                
                if struct.get('comment'):
                    prompt += f"    // {struct['comment']}\n"
                
                for field in struct.get('fields', []):
                    if 'type' in field:  # C/C++/Rust field
                        prompt += f"    {field['name']}: {field['type']},\n"
                
                for method in struct.get('methods', []):
                    params_str = ', '.join(f"{p['name']}: {p['type']}" for p in method['parameters'])
                    return_str = f" -> {method['return_type']}" if method['return_type'] else ""
                    prompt += f"    fn {method['name']}({params_str}){return_str} {{\n"
                    if method.get('comment'):
                        prompt += f"        // {method['comment']}\n"
                    prompt += f"        ...\n    }}\n"
                prompt += "\n"
        
        # Enums
        if 'enums' in structure and structure['enums']:
            prompt += "## Enums:\n"
            for enum in structure['enums']:
                prompt += f"### enum {enum['name']}:\n"
                if enum.get('comment'):
                    prompt += f"    // {enum['comment']}\n"
                
                if 'enumerators' in enum:  # C enum
                    for enumerator in enum['enumerators']:
                        value_str = f" = {enumerator['value']}" if enumerator.get('value') else ""
                        prompt += f"    {enumerator['name']}{value_str},\n"
                elif 'variants' in enum:  # Rust enum
                    for variant in enum['variants']:
                        prompt += f"    {variant['name']}"
                        if variant['fields']:
                            fields_str = ', '.join(f"{f['name']}: {f['type']}" for f in variant['fields'])
                            prompt += f"({fields_str})"
                        prompt += ",\n"
                prompt += "\n"
        
        # Functions (standalone)
        if 'functions' in structure and structure['functions']:
            prompt += "## Functions:\n"
            for func in structure['functions']:
                if 'modifiers' in func:  # Java/C++ style
                    modifiers_str = ' '.join(func['modifiers']) + ' ' if func['modifiers'] else ''
                    params_str = self.format_java_parameters(func['parameters'])
                    throws_str = f" throws {', '.join(func['throws'])}" if func.get('throws') else ""
                    prompt += f"### {modifiers_str}{func['return_type']} {func['name']}({params_str}){throws_str} {{\n"
                    if func.get('comment'):
                        prompt += f"    // {func['comment']}\n"
                    prompt += f"    ...\n}}\n\n"
                else:  # Python/JavaScript/Rust style
                    if language == 'python':
                        async_prefix = "async " if func.get('is_async') else ""
                        return_type = f" -> {func['return_type']}" if func.get('return_type') else ""
                        prompt += f"### {async_prefix}def {func['name']}{func['parameters']}{return_type}:\n"
                        if func.get('docstring'):
                            prompt += f"    \"\"\"{func['docstring']}\"\"\"\n"
                        prompt += f"    ...\n\n"
                    elif language in ['javascript', 'typescript']:
                        async_prefix = "async " if func.get('is_async') else ""
                        params_str = ', '.join(f"{p['name']}: {p['type']}" for p in func['parameters'])
                        return_str = f": {func['return_type']}" if func.get('return_type') else ""
                        prompt += f"### {async_prefix}function {func['name']}({params_str}){return_str} {{\n"
                        if func.get('comment'):
                            prompt += f"    // {func['comment']}\n"
                        prompt += f"    ...\n}}\n\n"
                    else:  # Rust
                        params_str = ', '.join(f"{p['name']}: {p['type']}" for p in func['parameters'])
                        return_str = f" -> {func['return_type']}" if func['return_type'] else ""
                        prompt += f"### fn {func['name']}({params_str}){return_str}:\n"
                        if func.get('comment'):
                            prompt += f"    // {func['comment']}\n"
                        prompt += f"    ...\n\n"
        
        # Exports (for JS/TS)
        if 'exports' in structure and structure['exports']:
            prompt += "## Exports:\n"
            for exp in structure['exports'][:5]:  # Limit exports
                prompt += f"- {exp}\n"
            prompt += "\n"
        
        # Generic note
        if structure.get('note'):
            prompt += f"## Note:\n{structure['note']}\n\n"
        
        return prompt
    
    def generate_compressed_prompt(self, file_path: str) -> str:
        """
        Generate a compressed prompt for the given file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Compressed representation of the file structure
        """
        try:
            # Detect language
            language = self.detect_language(file_path)
            if not language:
                return f"Could not detect language for {file_path}"
            
            # Get parser
            parser = self.get_parser_for_language(language)
            if not parser:
                return f"No parser available for language: {language}"
            
            # Read file
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            # Parse the file
            tree = parser.parse(source_code)
            
            # Extract structure based on language
            if language == 'python':
                structure = self.extract_python_structure(tree, source_code)
            elif language in ['javascript', 'typescript']:
                structure = self.extract_javascript_structure(tree, source_code)
            elif language == 'java':
                structure = self.extract_java_structure(tree, source_code)
            elif language == 'c':
                structure = self.extract_c_structure(tree, source_code)
            elif language == 'cpp':
                structure = self.extract_cpp_structure(tree, source_code)
            elif language == 'rust':
                structure = self.extract_rust_structure(tree, source_code)
            else:
                # Generic structure extraction
                structure = self.extract_generic_structure(tree, source_code)
            
            # Generate prompt
            return self.format_compressed_prompt(file_path, language, structure)
            
        except Exception as e:
            return f"Error analyzing {file_path}: {str(e)}"

    def extract_rust_structure(self, tree: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract structure from Rust code."""
        structure = {
            'modules': [],
            'structs': [],
            'enums': [],
            'traits': [],
            'impls': [],
            'functions': [],
            'macros': [],
            'globals': []
        }
        
        def traverse(node):
            if node.type == 'module':
                module_info = self.extract_rust_module_info(node, source_code)
                structure['modules'].append(module_info)
            
            elif node.type == 'struct_item':
                struct_info = self.extract_rust_struct_info(node, source_code)
                structure['structs'].append(struct_info)
            
            elif node.type == 'enum_item':
                enum_info = self.extract_rust_enum_info(node, source_code)
                structure['enums'].append(enum_info)
            
            elif node.type == 'trait_item':
                trait_info = self.extract_rust_trait_info(node, source_code)
                structure['traits'].append(trait_info)
            
            elif node.type == 'impl_item':
                impl_info = self.extract_rust_impl_info(node, source_code)
                structure['impls'].append(impl_info)
            
            elif node.type == 'function_item':
                func_info = self.extract_rust_function_info(node, source_code)
                structure['functions'].append(func_info)
            
            elif node.type == 'macro_definition':
                macro_text = self.extract_node_text(node, source_code).strip()
                structure['macros'].append(macro_text)
            
            elif node.type == 'static_item':
                global_info = self.extract_rust_global_info(node, source_code)
                if global_info:
                    structure['globals'].append(global_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return structure
    
    def extract_rust_module_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
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
                for item in child.children:
                    if item.type == 'struct_item':
                        struct_info = self.extract_rust_struct_info(item, source_code)
                        module_info['items'].append(('struct', struct_info))
                    elif item.type == 'enum_item':
                        enum_info = self.extract_rust_enum_info(item, source_code)
                        module_info['items'].append(('enum', enum_info))
                    elif item.type == 'trait_item':
                        trait_info = self.extract_rust_trait_info(item, source_code)
                        module_info['items'].append(('trait', trait_info))
                    elif item.type == 'impl_item':
                        impl_info = self.extract_rust_impl_info(item, source_code)
                        module_info['items'].append(('impl', impl_info))
                    elif item.type == 'function_item':
                        func_info = self.extract_rust_function_info(item, source_code)
                        module_info['items'].append(('function', func_info))
        
        return module_info
    
    def extract_rust_struct_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust struct information."""
        struct_info = {
            'name': '',
            'is_public': False,
            'fields': [],
            'generics': []
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                struct_info['is_public'] = True
            elif child.type == 'identifier':
                struct_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'generic_parameters':
                for param in child.children:
                    if param.type == 'generic_parameter':
                        struct_info['generics'].append(self.extract_node_text(param, source_code))
            elif child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'field_declaration':
                        field_info = self.extract_rust_field_info(field, source_code)
                        if field_info:
                            struct_info['fields'].append(field_info)
        
        return struct_info
    
    def extract_rust_enum_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust enum information."""
        enum_info = {
            'name': '',
            'is_public': False,
            'variants': [],
            'generics': []
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                enum_info['is_public'] = True
            elif child.type == 'identifier':
                enum_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'generic_parameters':
                for param in child.children:
                    if param.type == 'generic_parameter':
                        enum_info['generics'].append(self.extract_node_text(param, source_code))
            elif child.type == 'enum_variant_list':
                for variant in child.children:
                    if variant.type == 'enum_variant':
                        variant_info = self.extract_rust_variant_info(variant, source_code)
                        if variant_info:
                            enum_info['variants'].append(variant_info)
        
        return enum_info
    
    def extract_rust_trait_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust trait information."""
        trait_info = {
            'name': '',
            'is_public': False,
            'methods': [],
            'generics': [],
            'supertraits': []
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                trait_info['is_public'] = True
            elif child.type == 'identifier':
                trait_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'generic_parameters':
                for param in child.children:
                    if param.type == 'generic_parameter':
                        trait_info['generics'].append(self.extract_node_text(param, source_code))
            elif child.type == 'trait_bounds':
                for bound in child.children:
                    if bound.type == 'type_identifier':
                        trait_info['supertraits'].append(self.extract_node_text(bound, source_code))
            elif child.type == 'declaration_list':
                for item in child.children:
                    if item.type == 'function_item':
                        method_info = self.extract_rust_function_info(item, source_code)
                        trait_info['methods'].append(method_info)
        
        return trait_info
    
    def extract_rust_impl_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust implementation information."""
        impl_info = {
            'trait': None,
            'type': '',
            'methods': [],
            'generics': []
        }
        
        for child in node.children:
            if child.type == 'generic_parameters':
                for param in child.children:
                    if param.type == 'generic_parameter':
                        impl_info['generics'].append(self.extract_node_text(param, source_code))
            elif child.type == 'type_identifier':
                impl_info['type'] = self.extract_node_text(child, source_code)
            elif child.type == 'trait_bounds':
                for bound in child.children:
                    if bound.type == 'type_identifier':
                        impl_info['trait'] = self.extract_node_text(bound, source_code)
            elif child.type == 'declaration_list':
                for item in child.children:
                    if item.type == 'function_item':
                        method_info = self.extract_rust_function_info(item, source_code)
                        impl_info['methods'].append(method_info)
        
        return impl_info
    
    def extract_rust_function_info(self, node: tree_sitter.Tree, source_code: bytes) -> Dict[str, Any]:
        """Extract Rust function information."""
        func_info = {
            'name': '',
            'is_public': False,
            'parameters': [],
            'return_type': None,
            'generics': [],
            'is_unsafe': False,
            'is_async': False
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                func_info['is_public'] = True
            elif child.type == 'identifier':
                func_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'generic_parameters':
                for param in child.children:
                    if param.type == 'generic_parameter':
                        func_info['generics'].append(self.extract_node_text(param, source_code))
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
                        if param_info['name']:
                            func_info['parameters'].append(param_info)
            elif child.type == 'type_annotation':
                func_info['return_type'] = self.extract_node_text(child, source_code)
            elif child.type == 'unsafe':
                func_info['is_unsafe'] = True
            elif child.type == 'async':
                func_info['is_async'] = True
        
        return func_info
    
    def extract_rust_global_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract Rust global variable information."""
        global_info = {
            'name': '',
            'type': '',
            'is_public': False,
            'is_mutable': False
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
        
        return global_info if global_info['name'] else None
    
    def extract_rust_field_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
        """Extract Rust struct field information."""
        field_info = {
            'name': '',
            'type': '',
            'is_public': False
        }
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                field_info['is_public'] = True
            elif child.type == 'field_identifier':
                field_info['name'] = self.extract_node_text(child, source_code)
            elif child.type == 'type_annotation':
                field_info['type'] = self.extract_node_text(child, source_code)
        
        return field_info if field_info['name'] else None
    
    def extract_rust_variant_info(self, node: tree_sitter.Tree, source_code: bytes) -> Optional[Dict[str, Any]]:
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
                        field_info = self.extract_rust_field_info(field, source_code)
                        if field_info:
                            variant_info['fields'].append(field_info)
        
        return variant_info if variant_info['name'] else None


def analyze_file(file_path: str) -> str:
    """
    Convenience function to analyze a single file.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Compressed prompt representation of the file
    """
    analyzer = FileAnalyzer()
    return analyzer.generate_compressed_prompt(file_path)


def analyze_directory(directory_path: str, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Analyze all files in a directory.
    
    Args:
        directory_path: Path to the directory
        extensions: List of file extensions to include (e.g., ['.py', '.js'])
        
    Returns:
        Dictionary mapping file paths to their compressed prompts
    """
    analyzer = FileAnalyzer()
    results = {}
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Filter by extensions if specified
            if extensions:
                if not any(file.endswith(ext) for ext in extensions):
                    continue
            
            # Skip hidden files and common non-code files
            if file.startswith('.') or file.endswith(('.pyc', '.pyo', '.pyd')):
                continue
            
            try:
                compressed_prompt = analyzer.generate_compressed_prompt(file_path)
                results[file_path] = compressed_prompt
            except Exception as e:
                results[file_path] = f"Error: {str(e)}"
    
    return results