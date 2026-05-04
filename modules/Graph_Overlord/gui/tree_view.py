"""
Custom Tree View for displaying interest nodes.
Implements dual-tree layout with selection, context menus and filtering.
"""

from PyQt6.QtWidgets import (
    QTreeView, QMenu, QLineEdit, QPushButton, QWidget, QHBoxLayout,
    QAction, QMessageBox, QHeaderView, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel
from PyQt6.QtGui import QColor, QBrush

from ..models import InterestNode


class InterestTreeModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting tree nodes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""
        self.hide_locked = False
        self.int_min = 0
        self.int_max = 100
        self.att_min = -100
        self.att_max = 100
        self.show_only_linked_to = None
        
    def set_filter_text(self, text):
        self.filter_text = text.lower()
        self.invalidateFilter()
        
    def set_hide_locked(self, hide):
        self.hide_locked = hide
        self.invalidateFilter()
        
    def set_int_range(self, min_val, max_val):
        self.int_min = min_val
        self.int_max = max_val
        self.invalidateFilter()
        
    def set_att_range(self, min_val, max_val):
        self.att_min = min_val
        self.att_max = max_val
        self.invalidateFilter()
        
    def set_show_only_linked_to(self, node):
        self.show_only_linked_to = node
        self.invalidateFilter()
        
    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        if not index.isValid():
            return True
            
        node = index.internalPointer() if hasattr(index, 'internalPointer') else None
        if not node:
            return True
            
        # Text filter
        if self.filter_text and self.filter_text not in node.name.lower():
            # Check children
            has_matching_child = False
            for i in range(node.child_count()):
                child_index = self.sourceModel().index(i, 0, index)
                if self.filterAcceptsRow(i, index):
                    has_matching_child = True
                    break
            if not has_matching_child:
                return False
                
        # Locked filter
        if self.hide_locked and node.locked:
            return False
            
        # Interest range filter
        if node.int < self.int_min or node.int > self.int_max:
            return False
            
        # Attitude range filter
        if node.att < self.att_min or node.att > self.att_max:
            return False
            
        # Linked to filter
        if self.show_only_linked_to:
            if node != self.show_only_linked_to and not node.is_connected_to(self.show_only_linked_to):
                return False
                
        return True


class InterestTreeView(QTreeView):
    """Custom tree view for interest nodes with context menu and selection handling."""
    
    selection_changed = pyqtSignal(object)  # Emits selected node or None
    focus_in = pyqtSignal(object)  # Emits self when focused
    
    def __init__(self, tree_name="Tree", main_window=None, parent=None):
        super().__init__(parent)
        self.tree_name = tree_name
        self.main_window = main_window
        self.current_tree = None
        self.model = None
        
        self._setup_ui()
        self._setup_context_menu()
        
    def _setup_ui(self):
        """Setup tree view UI."""
        self.setHeaderHidden(False)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        
        # Setup header
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 80)  # Interest
        header.resizeSection(2, 80)  # Attitude
        header.resizeSection(3, 60)  # Links
        
        # Selection mode
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
    def _setup_context_menu(self):
        """Setup context menu actions."""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def create_header_widget(self):
        """Create header widget with tree selector and search."""
        header_widget = QWidget()
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Tree name label
        self.tree_label = QPushButton(self.tree_name)
        self.tree_label.clicked.connect(self._on_tree_selector_clicked)
        layout.addWidget(self.tree_label)
        
        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search...")
        self.search_field.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_field)
        
        # Add node button
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedWidth(30)
        self.add_btn.clicked.connect(self.add_node)
        layout.addWidget(self.add_btn)
        
        # Delete button
        self.delete_btn = QPushButton("-")
        self.delete_btn.setFixedWidth(30)
        self.delete_btn.clicked.connect(self.delete_selected)
        layout.addWidget(self.delete_btn)
        
        # Expand/Collapse button
        self.expand_btn = QPushButton("±")
        self.expand_btn.setFixedWidth(30)
        self.expand_btn.clicked.connect(self.toggle_expand_collapse)
        layout.addWidget(self.expand_btn)
        
        return header_widget
        
    def load_tree(self, tree):
        """Load a tree into the view."""
        self.current_tree = tree
        # Create and setup model
        from .tree_model import TreeModel
        self.model = TreeModel(tree)
        
        self.proxy_model = InterestTreeModel()
        self.proxy_model.setSourceModel(self.model)
        
        self.setModel(self.proxy_model)
        self.expandAll()
        
    def refresh(self):
        """Refresh the tree view."""
        if self.model:
            self.model.refresh()
            
    def _on_selection_changed(self, selected, deselected):
        """Handle selection change."""
        indexes = selected.indexes()
        if indexes and len(indexes) > 0:
            index = indexes[0]
            if self.proxy_model:
                source_index = self.proxy_model.mapToSource(index)
                node = source_index.internalPointer() if hasattr(source_index, 'internalPointer') else None
                self.selection_changed.emit(node)
        else:
            self.selection_changed.emit(None)
            
    def _show_context_menu(self, pos):
        """Show context menu at position."""
        index = self.indexAt(pos)
        if not index.isValid():
            return
            
        source_index = self.proxy_model.mapToSource(index) if self.proxy_model else index
        node = source_index.internalPointer() if hasattr(source_index, 'internalPointer') else None
        if not node:
            return
            
        menu = QMenu(self)
        
        # Add node action
        add_action = QAction("Add Node", self)
        add_action.triggered.connect(lambda: self.add_node(parent=node))
        menu.addAction(add_action)
        
        # Edit action
        edit_action = QAction("Edit (F2)", self)
        edit_action.triggered.connect(lambda: self.edit_node(node))
        menu.addAction(edit_action)
        
        # Delete action
        delete_action = QAction("Delete (Del)", self)
        delete_action.triggered.connect(lambda: self.delete_node(node))
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Lock/Unlock action
        lock_text = "Unlock" if node.locked else "Lock"
        lock_action = QAction(f"{lock_text} (Ctrl+D)", self)
        lock_action.triggered.connect(lambda: self.toggle_lock(node))
        menu.addAction(lock_action)
        
        menu.addSeparator()
        
        # Copy/Cut/Paste
        copy_action = QAction("Copy", self)
        menu.addAction(copy_action)
        
        cut_action = QAction("Cut", self)
        menu.addAction(cut_action)
        
        paste_action = QAction("Paste", self)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        # Expand/Collapse subtree
        expand_action = QAction("Expand Subtree", self)
        expand_action.triggered.connect(lambda: self.expandRecursively(index))
        menu.addAction(expand_action)
        
        collapse_action = QAction("Collapse Subtree", self)
        collapse_action.triggered.connect(lambda: self.collapseRecursively(index))
        menu.addAction(collapse_action)
        
        menu.addSeparator()
        
        # Create edge action (if node selected in other tree)
        create_edge_action = QAction("Create Edge", self)
        create_edge_action.triggered.connect(lambda: self.create_edge_from(node))
        menu.addAction(create_edge_action)
        
        # Add to favorites
        fav_action = QAction("Add to Favorites", self)
        fav_action.triggered.connect(lambda: self.add_to_favorites(node))
        menu.addAction(fav_action)
        
        menu.exec_(self.viewport().mapToGlobal(pos))
        
    def _on_tree_selector_clicked(self):
        """Handle tree selector click."""
        if self.main_window:
            # Show tree selection dropdown
            pass
            
    def _on_search_changed(self, text):
        """Handle search text change."""
        if self.proxy_model:
            self.proxy_model.set_filter_text(text)
            if text:
                self.expandAll()
                
    def add_node(self, parent=None):
        """Add a new node."""
        if not self.current_tree:
            QMessageBox.warning(self, "Error", "No tree loaded")
            return
            
        from .dialogs import CreateNodeDialog
        dialog = CreateNodeDialog(self, parent=parent)
        if dialog.exec():
            name = dialog.get_node_name()
            int_val = dialog.get_interest()
            att_val = dialog.get_attitude()
            locked = dialog.is_locked()
            
            node = self.current_tree.add_node(name, parent, int_val, att_val, locked)
            self.refresh()
            
            # Select newly created node
            self.select_node(node)
            
    def delete_selected(self):
        """Delete currently selected node."""
        indexes = self.selectedIndexes()
        if indexes and len(indexes) > 0:
            index = indexes[0]
            source_index = self.proxy_model.mapToSource(index) if self.proxy_model else index
            node = source_index.internalPointer() if hasattr(source_index, 'internalPointer') else None
            if node:
                self.delete_node(node)
                
    def delete_node(self, node):
        """Delete a specific node."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{node.name}' and all its children?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.current_tree:
                self.current_tree.remove_node(node)
                self.refresh()
                
    def edit_selected(self):
        """Edit currently selected node."""
        indexes = self.selectedIndexes()
        if indexes and len(indexes) > 0:
            index = indexes[0]
            source_index = self.proxy_model.mapToSource(index) if self.proxy_model else index
            node = source_index.internalPointer() if hasattr(source_index, 'internalPointer') else None
            if node:
                self.edit_node(node)
                
    def edit_node(self, node):
        """Edit a specific node."""
        from .dialogs import CreateNodeDialog
        dialog = CreateNodeDialog(self, node=node)
        if dialog.exec():
            node.name = dialog.get_node_name()
            node.user_int = dialog.get_interest()
            node.user_att = dialog.get_attitude()
            node.locked = dialog.is_locked()
            self.refresh()
            
    def toggle_lock_selected(self):
        """Toggle lock state of selected node."""
        indexes = self.selectedIndexes()
        if indexes and len(indexes) > 0:
            index = indexes[0]
            source_index = self.proxy_model.mapToSource(index) if self.proxy_model else index
            node = source_index.internalPointer() if hasattr(source_index, 'internalPointer') else None
            if node:
                self.toggle_lock(node)
                
    def toggle_lock(self, node):
        """Toggle lock state of a node."""
        node.locked = not node.locked
        self.refresh()
        
    def select_node(self, node):
        """Select a specific node in the tree."""
        if self.model:
            index = self.model.find_node(node)
            if index.isValid():
                proxy_index = self.proxy_model.mapFromSource(index) if self.proxy_model else index
                self.setCurrentIndex(proxy_index)
                
    def get_selected_node(self):
        """Get currently selected node."""
        indexes = self.selectedIndexes()
        if indexes and len(indexes) > 0:
            index = indexes[0]
            source_index = self.proxy_model.mapToSource(index) if self.proxy_model else index
            return source_index.internalPointer() if hasattr(source_index, 'internalPointer') else None
        return None
        
    def clear_selection(self):
        """Clear current selection."""
        self.clearSelection()
        self.selection_changed.emit(None)
        
    def open_search(self):
        """Open search field."""
        self.search_field.setFocus()
        
    def expand_all(self):
        """Expand all nodes."""
        self.expandAll()
        
    def collapse_all(self):
        """Collapse all nodes."""
        self.collapseAll()
        
    def toggle_expand_collapse(self):
        """Toggle between expand all and collapse all."""
        if self.isExpanded(self.rootIndex()):
            self.collapseAll()
        else:
            self.expandAll()
            
    def create_edge_from(self, source_node):
        """Create edge from this node to node in other tree."""
        if self.main_window:
            # Get selected node from other tree
            other_tree = self.main_window.tree_b if self == self.main_window.tree_a else self.main_window.tree_a
            target_node = other_tree.get_selected_node()
            
            if target_node:
                from .dialogs import CreateEdgeDialog
                dialog = CreateEdgeDialog(self, source_node, target_node)
                if dialog.exec():
                    # Create edge
                    pass
                    
    def add_to_favorites(self, node):
        """Add node to favorites."""
        if self.main_window and self.main_window.project:
            self.main_window.project.add_to_favorites(node.id)
            
    def focusInEvent(self, event):
        """Handle focus in event."""
        self.focus_in.emit(self)
        super().focusInEvent(event)
