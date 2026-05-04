"""
Dialog windows for Graph_Overlord application.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QDialogButtonBox, QSpinBox, QCheckBox, 
    QComboBox, QMessageBox, QSlider
)
from PyQt6.QtCore import Qt


class CreateNodeDialog(QDialog):
    """Dialog for creating or editing a node."""
    
    def __init__(self, parent=None, node=None, parent_node=None):
        super().__init__(parent)
        self.node = node
        self.parent_node = parent_node
        
        self.setWindowTitle("Edit Node" if node else "Create Node")
        self._setup_ui()
        
        if node:
            self._load_node_data()
            
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Interest
        self.int_spin = QSpinBox()
        self.int_spin.setRange(0, 100)
        self.int_spin.setValue(50)
        form_layout.addRow("Interest:", self.int_spin)
        
        # Attitude
        self.att_spin = QSpinBox()
        self.att_spin.setRange(-100, 100)
        self.att_spin.setValue(0)
        form_layout.addRow("Attitude:", self.att_spin)
        
        # Locked checkbox
        self.locked_cb = QCheckBox("Locked")
        form_layout.addRow("", self.locked_cb)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def _load_node_data(self):
        if self.node:
            self.name_edit.setText(self.node.name)
            self.int_spin.setValue(int(self.node.int))
            self.att_spin.setValue(int(self.node.att))
            self.locked_cb.setChecked(self.node.locked)
            
    def get_node_name(self):
        return self.name_edit.text()
        
    def get_interest(self):
        return self.int_spin.value()
        
    def get_attitude(self):
        return self.att_spin.value()
        
    def is_locked(self):
        return self.locked_cb.isChecked()


class CreateEdgeDialog(QDialog):
    """Dialog for creating an edge between two nodes."""
    
    def __init__(self, parent=None, source_node=None, target_node=None):
        super().__init__(parent)
        self.source_node = source_node
        self.target_node = target_node
        
        self.setWindowTitle("Create Edge")
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Source and Target info
        source_label = QLabel(self.source_node.name if self.source_node else "")
        form_layout.addRow("Source:", source_label)
        
        target_label = QLabel(self.target_node.name if self.target_node else "")
        form_layout.addRow("Target:", target_label)
        
        # Direct Influence - Att
        self.att_direct_slider = QSlider(Qt.Orientation.Horizontal)
        self.att_direct_slider.setRange(0, 100)
        self.att_direct_slider.setValue(50)
        form_layout.addRow("Direct Att:", self.att_direct_slider)
        
        # Direct Influence - Int
        self.int_direct_slider = QSlider(Qt.Orientation.Horizontal)
        self.int_direct_slider.setRange(0, 100)
        self.int_direct_slider.setValue(50)
        form_layout.addRow("Direct Int:", self.int_direct_slider)
        
        # Inverse Influence - Att
        self.att_inverse_slider = QSlider(Qt.Orientation.Horizontal)
        self.att_inverse_slider.setRange(0, 100)
        self.att_inverse_slider.setValue(50)
        form_layout.addRow("Inverse Att:", self.att_inverse_slider)
        
        # Inverse Influence - Int
        self.int_inverse_slider = QSlider(Qt.Orientation.Horizontal)
        self.int_inverse_slider.setRange(0, 100)
        self.int_inverse_slider.setValue(50)
        form_layout.addRow("Inverse Int:", self.int_inverse_slider)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_att_direct(self):
        return self.att_direct_slider.value() / 100.0
        
    def get_int_direct(self):
        return self.int_direct_slider.value() / 100.0
        
    def get_att_inverse(self):
        return self.att_inverse_slider.value() / 100.0
        
    def get_int_inverse(self):
        return self.int_inverse_slider.value() / 100.0


class CreateTreeDialog(QDialog):
    """Dialog for creating a new tree."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Tree")
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        form_layout.addRow("Tree Name:", self.name_edit)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_tree_name(self):
        return self.name_edit.text()


class ConfirmDialog(QDialog):
    """Generic confirmation dialog."""
    
    @staticmethod
    def ask(parent, title, message):
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
