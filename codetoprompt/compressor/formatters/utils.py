from typing import List, Optional

def indent(text: str, level: int = 1, indent_str: str = "    ") -> str:
    """Indent text by the specified number of levels.
    
    Args:
        text: The text to indent.
        level: The number of indentation levels.
        indent_str: The string to use for each indentation level.
        
    Returns:
        The indented text.
    """
    if not text:
        return ""
    
    indent = indent_str * level
    return "\n".join(f"{indent}{line}" for line in text.split("\n"))

def format_docstring(docstring: Optional[str], style: str = "python") -> str:
    """Format a docstring according to the specified style.
    
    Args:
        docstring: The docstring to format.
        style: The docstring style ('python', 'javascript', 'java', 'cpp', 'rust').
        
    Returns:
        The formatted docstring.
    """
    if not docstring:
        return ""
    
    if style == "python":
        return f'"""\n{docstring}\n"""'
    elif style == "javascript":
        return f"/**\n * {docstring}\n */"
    elif style == "java":
        return f"/**\n * {docstring}\n */"
    elif style == "cpp":
        return f"/**\n * {docstring}\n */"
    elif style == "rust":
        return f"/// {docstring}"
    else:
        return docstring

def format_parameters(parameters: List[str], style: str = "python") -> str:
    """Format a list of parameters according to the specified style.
    
    Args:
        parameters: The list of parameters to format.
        style: The parameter style ('python', 'javascript', 'java', 'cpp', 'rust').
        
    Returns:
        The formatted parameter string.
    """
    if not parameters:
        return ""
    
    if style == "python":
        return ", ".join(parameters)
    elif style == "javascript":
        return ", ".join(parameters)
    elif style == "java":
        return ", ".join(parameters)
    elif style == "cpp":
        return ", ".join(parameters)
    elif style == "rust":
        return ", ".join(parameters)
    else:
        return ", ".join(parameters)

def format_modifiers(modifiers: List[str], style: str = "python") -> str:
    """Format a list of modifiers according to the specified style.
    
    Args:
        modifiers: The list of modifiers to format.
        style: The modifier style ('python', 'javascript', 'java', 'cpp', 'rust').
        
    Returns:
        The formatted modifier string.
    """
    if not modifiers:
        return ""
    
    if style == "python":
        return " ".join(modifiers)
    elif style == "javascript":
        return " ".join(modifiers)
    elif style == "java":
        return " ".join(modifiers)
    elif style == "cpp":
        return " ".join(modifiers)
    elif style == "rust":
        return " ".join(modifiers)
    else:
        return " ".join(modifiers)

def format_inheritance(inheritance: List[str], style: str = "python") -> str:
    """Format a list of inheritance items according to the specified style.
    
    Args:
        inheritance: The list of inheritance items to format.
        style: The inheritance style ('python', 'javascript', 'java', 'cpp', 'rust').
        
    Returns:
        The formatted inheritance string.
    """
    if not inheritance:
        return ""
    
    if style == "python":
        return f"({', '.join(inheritance)})"
    elif style == "javascript":
        return f"extends {inheritance[0]}"
    elif style == "java":
        if len(inheritance) == 1:
            return f"extends {inheritance[0]}"
        else:
            return f"extends {inheritance[0]} implements {', '.join(inheritance[1:])}"
    elif style == "cpp":
        return f": {', '.join(inheritance)}"
    elif style == "rust":
        return f": {', '.join(inheritance)}"
    else:
        return ", ".join(inheritance) 