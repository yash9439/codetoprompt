# CodeToPrompt

Convert your codebase into a single LLM prompt!

## Installation

```bash
# Install the Python package
pip install --user codetoprompt

# If you get "command not found" error after installation, add this to your shell config file:
# For bash: ~/.bashrc
# For zsh: ~/.zshrc
# For fish: ~/.config/fish/config.fish

# Add this line to your shell config:
export PATH="$HOME/.local/bin:$PATH"

# Then reload your shell config:
source ~/.bashrc  # or source ~/.zshrc or source ~/.config/fish/config.fish

# System Dependencies
# For clipboard support on Linux:
# - X11: Install xclip
#   sudo apt-get install xclip  # Debian/Ubuntu
#   sudo dnf install xclip      # Fedora
#   sudo pacman -S xclip        # Arch Linux
# - Wayland: Install wl-clipboard
#   sudo apt-get install wl-clipboard  # Debian/Ubuntu
#   sudo dnf install wl-clipboard      # Fedora
#   sudo pacman -S wl-clipboard        # Arch Linux
```

## Quick Start

```bash
# Basic usage
codetoprompt /path/to/your/codebase

# Save to file
codetoprompt /path/to/your/codebase --output prompt.txt

# Include specific file patterns
codetoprompt /path/to/your/codebase --include "*.py,*.js"

# Exclude specific file patterns
codetoprompt /path/to/your/codebase --exclude "*.pyc,__pycache__"
```

## Features

- **Automatic Code Processing**: Convert codebases of any size into readable, formatted prompts
- **Smart Filtering**: Include/exclude files using glob patterns and respect `.gitignore` rules
- **Flexible Templating**: Customize prompts with Jinja2 templates for different use cases
- **Token Tracking**: Track token usage to stay within LLM context limits
- **Git Integration**: Include diffs, logs, and branch comparisons in your prompts
- **Developer Experience**: Automatic clipboard copy, line numbers, and file organization options

## Python API

```python
from codetoprompt import CodeToPrompt

# Initialize the processor
processor = CodeToPrompt(
    root_dir="/path/to/your/codebase",
    include_patterns=["*.py", "*.js"],
    exclude_patterns=["*.pyc", "__pycache__"]
)

# Generate the prompt
prompt = processor.generate_prompt()

# Save to file
processor.save_to_file("prompt.txt")

# Get token count
token_count = processor.get_token_count()
```

## License

MIT License - see LICENSE file for details 