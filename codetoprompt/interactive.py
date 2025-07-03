"""Interactive mode for CodeToPrompt."""

from typing import Set, List, Optional, Iterable
from pathlib import Path
from rich.text import Text

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static
from textual.widgets.tree import TreeNode
from textual.events import Key

from .core import CodeToPrompt
from .utils import should_skip_path


class SelectableTree(Tree):
    """
    A custom Tree widget that overrides key-press behavior to create a
    more intuitive selection interface, including arrow and WASD navigation.
    """
    def on_key(self, event: Key) -> None:
        """Process key events to handle selection, confirmation, and navigation."""
        # Toggle selection with space
        if event.key == "space":
            self.app.action_toggle_selection()
            event.stop()
            return

        # Confirm selection with enter
        if event.key == "enter":
            self.app.action_confirm_selection()
            event.stop()
            return

        # Collapse folder with left arrow
        if event.key in ("left",):
            tree = self.app.query_one(Tree)
            node = tree.cursor_node
            if node and node.data.get("is_dir"):
                node.collapse()
                tree.refresh()
            event.stop()
            return

        # Expand folder with right arrow
        if event.key in ("right",):
            tree = self.app.query_one(Tree)
            node = tree.cursor_node
            if node and node.data.get("is_dir"):
                node.expand()
                tree.refresh()
            event.stop()
            return
            
        # WASD navigation:
        tree = self.app.query_one(Tree)
        node = tree.cursor_node
        if event.key == "w":            
            tree = self.app.query_one(Tree)
            # call the method on the Tree instance
            getattr(tree, "action_cursor_up")()
            tree.refresh()
            event.stop()
            return
        
        if event.key == "s":
            tree = self.app.query_one(Tree)
            # call the method on the Tree instance
            getattr(tree, "action_cursor_down")()
            tree.refresh()
            event.stop()
            return

        if event.key == "a":
            # treat 'a' like left arrow: collapse
            if node and node.data.get("is_dir"):
                node.collapse()
                tree.refresh()
            event.stop()
            return

        if event.key == "d":
            # treat 'd' like right arrow: expand
            if node and node.data.get("is_dir"):
                node.expand()
                tree.refresh()
            event.stop()
            return

class FileSelectorApp(App):
    """A Textual TUI for interactively selecting files and directories."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, root_path: Path, scanner: CodeToPrompt):
        super().__init__()
        self.root_path = root_path
        self.scanner = scanner
        self.selected_paths = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Navigate: [b]↑/↓/w/s[/b] | Expand/Collapse: [b]←/→/a/d[/b] | Toggle Select: [b]Space[/b] | Confirm: [b]Enter[/b]\n"
            "[green]✓[/green] = All selected | [yellow]-[/yellow] = Some selected | [grey50]◦[/grey50] = None selected",
            id="instructions",
        )
        yield SelectableTree(self.root_path.name, id="file_tree")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted. Sets up the UI."""
        self.query_one("#instructions").styles.text_align = "center"
        self.query_one("#instructions").styles.padding = (0, 1)

        tree = self.query_one(Tree)
        tree.root.data = {"path": self.root_path, "is_dir": True, "selected": False}
        self.populate_node(tree.root)
        self._update_all_labels()
        tree.root.expand()

    def populate_node(self, node: TreeNode) -> None:
        """Populates the direct children of a given tree node."""
        if not node.data:
            return

        dir_path: Path = node.data["path"]
        node.remove_children()

        try:
            paths = sorted(list(dir_path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            node.add_leaf("❌ Permission denied")
            return

        for path in paths:
            # Use the scanner's own logic to determine if a path should be skipped
            if should_skip_path(path, self.root_path):
                continue
            
            if path.is_dir():
                child_node = node.add(path.name, data={"path": path, "is_dir": True, "selected": False})
                child_node.add_leaf("...") # Placeholder for lazy loading
            elif self.scanner._should_include_file(path):
                node.add_leaf(path.name, data={"path": path, "is_dir": False, "selected": False})

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Lazily loads directory contents when a node is expanded."""
        node = event.node
        if node.children and not node.children[0].data: # A placeholder node has no data
            self.populate_node(node)
            if node.data.get("selected", False):
                self._set_node_and_children_selected(node, True)
            self._update_all_labels()
            node.expand()

    def _is_fully_selected(self, node: TreeNode) -> bool:
        """Recursively checks if a node and all its loaded descendants are selected."""
        if not node.data.get("selected"):
            return False
        if node.data.get("is_dir"):
            # If a directory has not been expanded, we treat it as fully selected if its own flag is set.
            if node.children and not node.children[0].data:
                return True
            return all(self._is_fully_selected(child) for child in node.children if child.data)
        return True

    def _set_node_and_children_selected(self, node: TreeNode, selected: bool):
        """Recursively sets the 'selected' data for a node and all its loaded children."""
        node.data["selected"] = selected
        if node.data["is_dir"]:
            for child in node.children:
                # Don't try to select the placeholder node
                if child.data:
                    self._set_node_and_children_selected(child, selected)

    def action_toggle_selection(self) -> None:
        """Called when the user presses space. Toggles the selection state."""
        tree = self.query_one(Tree)
        node = tree.cursor_node
        if not node:
            return

        new_state = not self._is_fully_selected(node)
        self._set_node_and_children_selected(node, new_state)
        self._update_all_labels()

    def _update_all_labels(self):
        """Recalculates labels for the entire tree and refreshes the view."""
        tree = self.query_one(Tree)
        if tree.root:
            self._recalculate_and_set_label(tree.root)
            tree.refresh()

    def _recalculate_and_set_label(self, node: TreeNode) -> str:
        """
        Recursively determines the visual status of a node and sets its label.
        """
        status = 'none'
        if not node.data["is_dir"]:
            status = 'full' if node.data["selected"] else 'none'
        else:
            # Check if directory is unexpanded (has a placeholder)
            if not node.children or not node.children[0].data:
                status = 'full' if node.data["selected"] else 'none'
            else:
                child_statuses = {self._recalculate_and_set_label(child) for child in node.children}
                if len(child_statuses) == 1:
                    status = child_statuses.pop()
                else:
                    status = 'partial'

        if status == 'full':
            prefix = "[green]✓[/green]"
        elif status == 'partial':
            prefix = "[yellow]-[/yellow]"
        else:
            prefix = "[grey50]◦[/grey50]"

        icon = "📁" if node.data["is_dir"] else "📄"
        name = f"[b]{node.data['path'].name}[/b]" if node.data["is_dir"] else node.data['path'].name
        node.set_label(Text.from_markup(f"{prefix} {icon} {name}"))
        return status

    def _scan_and_collect(self, dir_path: Path, collected_files: set):
        """
        Optimized recursive walk to find all valid files under a directory.
        It prunes entire subdirectories that should be skipped.
        """
        if should_skip_path(dir_path, self.root_path):
            return

        try:
            for item in dir_path.iterdir():
                if item.is_dir():
                    self._scan_and_collect(item, collected_files)
                elif self.scanner._should_include_file(item):
                    collected_files.add(item)
        except (PermissionError, FileNotFoundError):
            # Ignore directories we can't read
            pass

    def action_confirm_selection(self) -> None:
        """Called on Enter. Collects all selected files and exits."""
        selected_files = set()
        nodes_to_process = [self.query_one(Tree).root]

        while nodes_to_process:
            node = nodes_to_process.pop(0)
            if not node.data:
                continue
            
            is_selected = node.data.get("selected", False)
            path: Path = node.data["path"]

            if node.data["is_dir"]:
                if is_selected:
                    # Directory is fully selected. Scan the filesystem from here.
                    self._scan_and_collect(path, selected_files)
                else:
                    # Directory is not selected, but its children might be.
                    # Add loaded children to the queue.
                    if node.children and node.children[0].data:
                        nodes_to_process.extend(node.children)
            elif is_selected: # It's a file
                selected_files.add(path)
        
        self.exit(list(selected_files))