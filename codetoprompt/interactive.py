"""Interactive mode for CodeToPrompt."""

from typing import Set, List, Optional, Iterable
from pathlib import Path
from rich.text import Text

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static
from textual.widgets.tree import TreeNode
from textual.events import Key

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

    def __init__(self, root_path: Path, candidate_files: Set[Path]):
        super().__init__()
        self.root_path = root_path
        self.candidate_files = candidate_files
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
        self._populate_tree(self.root_path, tree.root)
        self._update_all_labels()
        tree.root.expand()

    def _populate_tree(self, dir_path: Path, node: TreeNode) -> None:
        """Recursively populates the tree with directories and candidate files."""
        paths = sorted(list(dir_path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))

        for path in paths:
            if path.is_dir():
                if any(p.is_relative_to(path) for p in self.candidate_files):
                    child_node = node.add(path.name, data={"path": path, "is_dir": True, "selected": False})
                    self._populate_tree(path, child_node)
            elif path in self.candidate_files:
                node.add_leaf(path.name, data={"path": path, "is_dir": False, "selected": False})

    def _is_fully_selected(self, node: TreeNode) -> bool:
        """Recursively checks if a node and all its descendants are marked as selected."""
        if not node.data["selected"]:
            return False
        if node.data["is_dir"]:
            return all(self._is_fully_selected(child) for child in node.children)
        return True

    def _set_node_and_children_selected(self, node: TreeNode, selected: bool):
        """Recursively sets the 'selected' data for a node and all its children."""
        node.data["selected"] = selected
        if node.data["is_dir"]:
            for child in node.children:
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
            if not node.children:
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

    def action_confirm_selection(self) -> None:
        """Called on Enter. Collects all selected files and exits."""
        selected_files = []
        def collect(node: TreeNode):
            if not node.data["is_dir"] and node.data["selected"]:
                selected_files.append(node.data["path"])
            for child in node.children:
                collect(child)

        collect(self.query_one(Tree).root)
        self.exit(selected_files)
