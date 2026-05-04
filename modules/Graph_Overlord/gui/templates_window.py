"""
Templates Window for Graph_Overlord application.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, 
    QGroupBox, QMessageBox, QFileDialog, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal


class TemplatesWindow(QWidget):
    """Floating window for managing templates."""
    
    template_applied = pyqtSignal(object)  # Emits applied template
    
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.setWindowTitle("Templates")
        self.setMinimumSize(400, 500)
        
        self._setup_ui()
        self._load_templates()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search templates...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_edit)
        
        # Splitter for list and preview
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Templates list
        list_group = QGroupBox("Templates")
        list_layout = QVBoxLayout(list_group)
        
        self.templates_list = QListWidget()
        self.templates_list.itemClicked.connect(self._on_template_selected)
        list_layout.addWidget(self.templates_list)
        
        btn_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply to Selected")
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        btn_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save Selection")
        self.save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        btn_layout.addWidget(self.delete_btn)
        
        list_layout.addLayout(btn_layout)
        
        splitter.addWidget(list_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Import/Export buttons
        io_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self._on_import_clicked)
        io_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._on_export_clicked)
        io_layout.addWidget(self.export_btn)
        
        layout.addLayout(io_layout)
        
    def _load_templates(self):
        """Load templates from manager."""
        self.templates_list.clear()
        
        if self.main_window and self.main_window.project:
            manager = self.main_window.project.get_template_manager()
            for template in manager.get_all_templates():
                item = QListWidgetItem(template.name)
                item.setData(Qt.ItemDataRole.UserRole, template)
                self.templates_list.addItem(item)
                
    def _on_search_changed(self, text):
        """Handle search text change."""
        for i in range(self.templates_list.count()):
            item = self.templates_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def _on_template_selected(self, item):
        """Handle template selection."""
        template = item.data(Qt.ItemDataRole.UserRole)
        if template:
            self._show_preview(template)
            
    def _show_preview(self, template):
        """Show template preview."""
        preview = f"Template: {template.name}\n\n"
        preview += f"Nodes: {len(template.nodes)}\n"
        preview += f"Edges: {len(template.edges)}\n\n"
        preview += "Structure:\n"
        
        for node_data in template.nodes:
            indent = "  " * node_data.get('depth', 0)
            preview += f"{indent}- {node_data.get('name', 'Unknown')}\n"
            
        self.preview_text.setText(preview)
        
    def _on_apply_clicked(self):
        """Handle apply button."""
        item = self.templates_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "No template selected")
            return
            
        template = item.data(Qt.ItemDataRole.UserRole)
        if not template:
            return
            
        if self.main_window:
            selected_node = self.main_window.get_selected_node()
            if not selected_node:
                QMessageBox.warning(self, "Warning", "No node selected to apply template to")
                return
                
            # Apply template
            self.main_window.project.apply_template(template, selected_node)
            self.template_applied.emit(template)
            
            # Refresh tree views
            self.main_window.tree_a.refresh()
            self.main_window.tree_b.refresh()
            
    def _on_save_clicked(self):
        """Handle save button."""
        if self.main_window:
            selected_node = self.main_window.get_selected_node()
            if not selected_node:
                QMessageBox.warning(self, "Warning", "No node selected to save as template")
                return
                
            # Create template from selection
            name, ok = QLineEdit.getText(self, "Save Template", "Template name:")
            if ok and name:
                template = self.main_window.project.create_template_from_node(selected_node, name)
                self._load_templates()
                
    def _on_delete_clicked(self):
        """Handle delete button."""
        item = self.templates_list.currentItem()
        if not item:
            return
            
        reply = QMessageBox.question(
            self, "Delete Template",
            "Delete this template?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            template = item.data(Qt.ItemDataRole.UserRole)
            if template and self.main_window:
                self.main_window.project.delete_template(template)
                self._load_templates()
                
    def _on_import_clicked(self):
        """Handle import button."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Template", "", "JSON Files (*.json)"
        )
        
        if file_path and self.main_window:
            try:
                self.main_window.project.import_template(file_path)
                self._load_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import: {e}")
                
    def _on_export_clicked(self):
        """Handle export button."""
        item = self.templates_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "No template selected")
            return
            
        template = item.data(Qt.ItemDataRole.UserRole)
        if not template:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Template", f"{template.name}.json", "JSON Files (*.json)"
        )
        
        if file_path and self.main_window:
            try:
                self.main_window.project.export_template(template, file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
