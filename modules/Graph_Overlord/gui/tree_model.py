"""
Tree Model for displaying interest nodes in QTreeView.
"""

from PyQt6.QtCore import Qt, QModelIndex, QVariant, pyqtSignal, QAbstractItemModel
from PyQt6.QtGui import QColor, QBrush


class TreeModel(QAbstractItemModel):
    """Custom tree model for interest nodes."""
    
    data_changed_signal = pyqtSignal()
    
    def __init__(self, tree, parent=None):
        super().__init__(parent)
        self.tree = tree
        self.root_node = tree.root if tree else None
        
    def refresh(self):
        """Refresh the model."""
        self.dataChanged.emit(
            self.index(0, 0, QModelIndex()),
            self.index(self.rowCount(QModelIndex()) - 1, 
                      self.columnCount(QModelIndex()) - 1, 
                      QModelIndex())
        )
        
    def index(self, row, column, parent=QModelIndex()):
        """Create index for given row, column and parent."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
            
        if not parent.isValid():
            parent_item = self.root_node
        else:
            parent_item = parent.internalPointer()
            
        child_item = parent_item.get_child(row) if parent_item else None
        
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()
        
    def parent(self, index):
        """Get parent index."""
        if not index.isValid():
            return QModelIndex()
            
        child_item = index.internalPointer()
        parent_item = child_item.parent if child_item else None
        
        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()
            
        return self.createIndex(parent_item.row(), 0, parent_item)
        
    def rowCount(self, parent=QModelIndex()):
        """Get number of rows."""
        if not parent.isValid():
            parent_item = self.root_node
        else:
            parent_item = parent.internalPointer()
            
        if not parent_item:
            return 0
            
        return parent_item.child_count()
        
    def columnCount(self, parent=QModelIndex()):
        """Get number of columns."""
        return 4  # Name, Interest, Attitude, Links
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Get data for index."""
        if not index.isValid():
            return QVariant()
            
        node = index.internalPointer()
        column = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return node.name
            elif column == 1:
                return int(node.int)
            elif column == 2:
                return int(node.att)
            elif column == 3:
                return len(node.get_all_edges())
                
        elif role == Qt.ItemDataRole.EditRole:
            if column == 0:
                return node.name
            elif column == 1:
                return int(node.int)
            elif column == 2:
                return int(node.att)
                
        elif role == Qt.ItemDataRole.ForegroundRole:
            if node.locked:
                return QBrush(QColor(128, 128, 128))  # Gray for locked
                
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Highlight based on uncertainty
            if hasattr(node, 'uncertainty') and node.uncertainty > 0.5:
                return QBrush(QColor(255, 255, 200))  # Light yellow
                
        elif role == Qt.ItemDataRole.ToolTipRole:
            return f"{node.name}\nInterest: {node.int:.1f}\nAttitude: {node.att:.1f}\nLocked: {node.locked}"
            
        return QVariant()
        
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Set data for index."""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
            
        node = index.internalPointer()
        column = index.column()
        
        if column == 0:
            node.name = str(value)
        elif column == 1:
            node.user_int = int(value)
        elif column == 2:
            node.user_att = int(value)
        else:
            return False
            
        self.dataChanged.emit(index, index, [role])
        return True
        
    def flags(self, index):
        """Get item flags."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
            
        default_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
        if index.column() == 0:
            return default_flags | Qt.ItemFlag.ItemIsEditable
        elif index.column() in [1, 2]:
            return default_flags | Qt.ItemFlag.ItemIsEditable
            
        return default_flags
        
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Get header data."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            headers = ["Node", "Interest", "Attitude", "Links"]
            if section < len(headers):
                return headers[section]
        return QVariant()
        
    def find_node(self, node):
        """Find index for a specific node."""
        def search_recursive(current_node, current_index):
            if current_node == node:
                return current_index
                
            for i in range(current_node.child_count()):
                child = current_node.get_child(i)
                child_index = self.index(i, 0, current_index)
                result = search_recursive(child, child_index)
                if result.isValid():
                    return result
                    
            return QModelIndex()
            
        if self.root_node:
            return search_recursive(self.root_node, QModelIndex())
        return QModelIndex()
