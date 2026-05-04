"""
Main Window for Graph_Overlord application.
Implements the main layout with two tree views, inspector panel, menu bar, toolbar and status bar.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar,
    QAction, QShortcut, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QIcon

from ..models import Project
from .tree_view import InterestTreeView
from .inspector import NodeInspector, NavigationPanel
from .dialogs import CreateNodeDialog, CreateEdgeDialog, CreateTreeDialog, ConfirmDialog
from .templates_window import TemplatesWindow


class MainWindow(QMainWindow):
    """Main application window with dual tree view layout."""
    
    project_changed = pyqtSignal()
    selection_changed = pyqtSignal(object)  # Emits selected node or None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.active_tree_view = None  # Track which tree view has focus
        self.templates_window = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_shortcuts()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the main UI layout."""
        self.setWindowTitle("Graph Overlord - Char Maker Module")
        self.setMinimumSize(1200, 800)
        
        # Central widget with splitter for two tree views
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left Tree View (Tree A)
        self.tree_a = InterestTreeView(tree_name="Tree A", main_window=self)
        splitter.addWidget(self.tree_a)
        
        # Right Tree View (Tree B) - Central
        self.tree_b = InterestTreeView(tree_name="Tree B", main_window=self)
        splitter.addWidget(self.tree_b)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        # Left Dock Widget - Tree A selector (already embedded, but can show info)
        self.left_dock = QDockWidget("Tree A", self)
        self.left_dock.setWidget(self.tree_a.create_header_widget())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)
        
        # Right Dock Widget - Inspector and Navigation
        self.right_dock = QDockWidget("Inspector & Navigation", self)
        self.inspector_tabs = QTabWidget()
        
        self.node_inspector = NodeInspector(main_window=self)
        self.navigation_panel = NavigationPanel(main_window=self)
        
        self.inspector_tabs.addTab(self.node_inspector, "Node Inspector")
        self.inspector_tabs.addTab(self.navigation_panel, "Navigation")
        
        self.right_dock.setWidget(self.inspector_tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)
        
        # Track active tree view
        self.tree_a.focus_in.connect(self._on_tree_focus)
        self.tree_b.focus_in.connect(self._on_tree_focus)
        
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        self.action_new = QAction("&New Project", self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.triggered.connect(self.new_project)
        file_menu.addAction(self.action_new)
        
        self.action_open = QAction("&Open Project", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self.open_project)
        file_menu.addAction(self.action_open)
        
        self.action_save = QAction("&Save Project", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self.save_project)
        file_menu.addAction(self.action_save)
        
        file_menu.addSeparator()
        
        self.action_exit = QAction("E&xit", self)
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        self.action_undo = QAction("&Undo", self)
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.action_undo.triggered.connect(self.undo)
        edit_menu.addAction(self.action_undo)
        
        self.action_redo = QAction("&Redo", self)
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.action_redo.triggered.connect(self.redo)
        edit_menu.addAction(self.action_redo)
        
        edit_menu.addSeparator()
        
        self.action_apply = QAction("&Apply All Changes", self)
        self.action_apply.triggered.connect(self.apply_changes)
        edit_menu.addAction(self.action_apply)
        
        # Calculation Menu
        calc_menu = menubar.addMenu("&Calculation")
        
        self.action_recalc = QAction("&Recalculate Weights", self)
        self.action_recalc.setShortcut(QKeySequence(Qt.Key.Key_F5))
        self.action_recalc.triggered.connect(self.recalculate_weights)
        calc_menu.addAction(self.action_recalc)
        
        self.action_reset = QAction("&Reset Recalculation", self)
        self.action_reset.triggered.connect(self.reset_recalculation)
        calc_menu.addAction(self.action_reset)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        self.action_templates = QAction("Show &Templates", self)
        self.action_templates.setShortcut(QKeySequence("Ctrl+T"))
        self.action_templates.triggered.connect(self.toggle_templates)
        view_menu.addAction(self.action_templates)
        
        self.action_dark_theme = QAction("&Dark Theme", self)
        self.action_dark_theme.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.action_dark_theme)
        
        self.action_reset_layout = QAction("&Reset Layout", self)
        self.action_reset_layout.triggered.connect(self.reset_layout)
        view_menu.addAction(self.action_reset_layout)
        
    def _setup_toolbar(self):
        """Setup toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(True)
        self.addToolBar(toolbar)
        
        # Add actions to toolbar
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_undo)
        toolbar.addAction(self.action_redo)
        toolbar.addSeparator()
        
        self.action_add_node_toolbar = QAction("Add Node", self)
        self.action_add_node_toolbar.triggered.connect(self.add_node_to_active_tree)
        toolbar.addAction(self.action_add_node_toolbar)
        
        self.action_delete_node_toolbar = QAction("Delete Node", self)
        self.action_delete_node_toolbar.triggered.connect(self.delete_selected_node)
        toolbar.addAction(self.action_delete_node_toolbar)
        
        toolbar.addSeparator()
        toolbar.addAction(self.action_recalc)
        
        self.action_search = QAction("Global Search", self)
        self.action_search.triggered.connect(self.global_search)
        toolbar.addAction(self.action_search)
        
        toolbar.addSeparator()
        toolbar.addAction(self.action_dark_theme)
        
        self.action_help = QAction("Help", self)
        self.action_help.triggered.connect(self.show_help)
        toolbar.addAction(self.action_help)
        
    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.status_save = QLabel("Ready")
        self.statusbar.addWidget(self.status_save)
        
        self.status_selection = QLabel("Nothing selected")
        self.statusbar.addPermanentWidget(self.status_selection)
        
        self.status_links = QLabel("Links: 0")
        self.statusbar.addPermanentWidget(self.status_links)
        
        self.status_weight = QLabel("Weight: N/A")
        self.statusbar.addPermanentWidget(self.status_weight)
        
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Add node shortcut
        shortcut_add = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        shortcut_add.activated.connect(self.add_node_to_active_tree)
        
        # Delete node shortcut
        shortcut_del = QShortcut(QKeySequence.StandardKey.Delete, self)
        shortcut_del.activated.connect(self.delete_selected_node)
        
        # Rename shortcut
        shortcut_rename = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        shortcut_rename.activated.connect(self.rename_selected_node)
        
        # Search in current tree
        shortcut_search = QShortcut(QKeySequence.StandardKey.Find, self)
        shortcut_search.activated.connect(self.search_in_active_tree)
        
        # Expand/Collapse all
        shortcut_expand = QShortcut(QKeySequence("Ctrl++"), self)
        shortcut_expand.activated.connect(self.expand_active_tree)
        
        shortcut_collapse = QShortcut(QKeySequence("Ctrl+-"), self)
        shortcut_collapse.activated.connect(self.collapse_active_tree)
        
        # Deselect
        shortcut_deselect = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        shortcut_deselect.activated.connect(self.deselect_all)
        
        # Lock/Unlock node
        shortcut_lock = QShortcut(QKeySequence("Ctrl+D"), self)
        shortcut_lock.activated.connect(self.toggle_lock_selected_node)
        
    def _connect_signals(self):
        """Connect internal signals."""
        self.tree_a.selection_changed.connect(self._on_selection_changed)
        self.tree_b.selection_changed.connect(self._on_selection_changed)
        
    def _on_tree_focus(self, tree_view):
        """Handle tree view focus change."""
        self.active_tree_view = tree_view
        
    def _on_selection_changed(self, node):
        """Handle node selection change."""
        self.selection_changed.emit(node)
        if node:
            self.status_selection.setText(f"Selected: {node.name} ({'Tree A' if self.active_tree_view == self.tree_a else 'Tree B'})")
            self.status_links.setText(f"Links: {len(node.get_all_edges())}")
            weight = node.calculate_weight()
            self.status_weight.setText(f"Weight: {weight:.4f}")
        else:
            self.status_selection.setText("Nothing selected")
            self.status_links.setText("Links: 0")
            self.status_weight.setText("Weight: N/A")
            
        # Update inspector
        self.node_inspector.set_node(node)
        
    # Action methods
    def new_project(self):
        """Create a new project."""
        if self.project and not self.confirm_discard():
            return
            
        dialog = CreateTreeDialog(self)
        if dialog.exec():
            tree_name = dialog.get_tree_name()
            self.project = Project()
            tree = self.project.create_tree(tree_name)
            
            self.tree_a.load_tree(tree)
            self.tree_b.load_tree(tree)  # Both show same tree initially
            
            self.project_changed.emit()
            self.status_save.setText("New project created")
            
    def open_project(self):
        """Open existing project."""
        # Implementation for file dialog and loading
        QMessageBox.information(self, "Open", "Open project functionality to be implemented")
        
    def save_project(self):
        """Save current project."""
        if self.project:
            # Implementation for saving to file
            self.status_save.setText("Project saved")
        else:
            QMessageBox.warning(self, "Save", "No project to save")
            
    def undo(self):
        """Undo last action."""
        if self.project:
            self.project.undo()
            
    def redo(self):
        """Redo last undone action."""
        if self.project:
            self.project.redo()
            
    def apply_changes(self):
        """Apply all pending changes."""
        if self.project:
            self.project.apply_changes()
            
    def recalculate_weights(self):
        """Trigger global recalculation."""
        if self.project:
            solver = self.project.get_solver()
            solver.solve()
            self.tree_a.refresh()
            self.tree_b.refresh()
            self.status_save.setText("Recalculated")
            
    def reset_recalculation(self):
        """Reset recalculation to default values."""
        if self.project:
            # Implementation for reset
            pass
            
    def toggle_templates(self):
        """Show/hide templates window."""
        if self.templates_window is None:
            self.templates_window = TemplatesWindow(self)
            
        if self.templates_window.isVisible():
            self.templates_window.hide()
        else:
            self.templates_window.show()
            
    def toggle_theme(self):
        """Toggle dark/light theme."""
        app = QApplication.instance()
        current_style = app.styleSheet()
        if "dark" in current_style.lower():
            app.setStyleSheet("")
        else:
            # Simple dark theme
            app.setStyleSheet("""
                QMainWindow, QDialog, QDockWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTreeView, QListView, QTableView {
                    background-color: #3b3b3b;
                    color: #ffffff;
                }
            """)
            
    def reset_layout(self):
        """Reset window layout to default."""
        self.resize(1200, 800)
        self.move(100, 100)
        # Reset dock widgets positions
        
    def add_node_to_active_tree(self):
        """Add node to currently active tree."""
        if self.active_tree_view:
            self.active_tree_view.add_node()
            
    def delete_selected_node(self):
        """Delete currently selected node."""
        if self.active_tree_view:
            self.active_tree_view.delete_selected()
            
    def rename_selected_node(self):
        """Rename currently selected node."""
        if self.active_tree_view:
            self.active_tree_view.edit_selected()
            
    def global_search(self):
        """Open global search dialog."""
        self.navigation_panel.open_global_search()
        
    def search_in_active_tree(self):
        """Search in active tree."""
        if self.active_tree_view:
            self.active_tree_view.open_search()
            
    def expand_active_tree(self):
        """Expand all nodes in active tree."""
        if self.active_tree_view:
            self.active_tree_view.expand_all()
            
    def collapse_active_tree(self):
        """Collapse all nodes in active tree."""
        if self.active_tree_view:
            self.active_tree_view.collapse_all()
            
    def deselect_all(self):
        """Clear all selections."""
        if self.tree_a:
            self.tree_a.clear_selection()
        if self.tree_b:
            self.tree_b.clear_selection()
            
    def toggle_lock_selected_node(self):
        """Toggle lock state of selected node."""
        if self.active_tree_view:
            self.active_tree_view.toggle_lock_selected()
            
    def show_help(self):
        """Show help dialog."""
        QMessageBox.information(self, "Help", "Graph Overlord Help\n\nSee documentation for details.")
        
    def confirm_discard(self):
        """Confirm discarding unsaved changes."""
        reply = QMessageBox.question(
            self, "Discard Changes?",
            "You have unsaved changes. Discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
        
    def set_project(self, project):
        """Set the current project."""
        self.project = project
        # Load trees into views
        self.project_changed.emit()
        
    def get_active_tree_view(self):
        """Get currently active tree view."""
        return self.active_tree_view or self.tree_a
        
    def get_selected_node(self):
        """Get currently selected node from active tree."""
        if self.active_tree_view:
            return self.active_tree_view.get_selected_node()
        return None
