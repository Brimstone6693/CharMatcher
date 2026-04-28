import sys
import json
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTreeView, 
                             QAbstractItemView, QMessageBox, QVBoxLayout, QWidget, 
                             QDialog, QFormLayout, QLineEdit, QPushButton, QLabel, 
                             QComboBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex, QVariant
from PyQt6.QtGui import QColor

# --- КОНСТАНТЫ И ТИПЫ ДАННЫХ ---

STATUS_MAP = {
    -3: "Критический минус",
    -2: "Сильный минус",
    -1: "Слабый минус",
    0: "Нет оценки / Авто",
    1: "Слабый плюс",
    2: "Сильный плюс",
    3: "Критический плюс"
}

class DataNode:
    """Базовый класс для всех элементов иерархии."""
    def __init__(self, name: str, node_type: str, parent=None):
        self.name = name
        self.node_type = node_type  # 'root', 'branch', 'row', 'subrow'
        self.parent = parent
        self.children: List[DataNode] = []
        
        # Атрибуты
        self.status: int = 0  # -3 to 3
        self.custom_status: Optional[str] = None # Пользовательский статус (текст)
        self.is_auto: bool = True # Флаг "Авто"
        
        # Взаимосвязи (наследство, ссылки на другие таблицы)
        self.relations: Dict[str, Any] = {} 

    def to_dict(self) -> Dict:
        """Сериализация узла в словарь для JSON."""
        data = {
            "name": self.name,
            "type": self.node_type,
            "status": self.status,
            "custom_status": self.custom_status,
            "is_auto": self.is_auto,
            "relations": self.relations,
            "children": [child.to_dict() for child in self.children]
        }
        return data

    @staticmethod
    def from_dict(data: Dict, parent=None) -> 'DataNode':
        """Десериализация из словаря."""
        node = DataNode(
            name=data.get("name", "Unnamed"),
            node_type=data.get("type", "row"),
            parent=parent
        )
        node.status = data.get("status", 0)
        node.custom_status = data.get("custom_status")
        node.is_auto = data.get("is_auto", True)
        node.relations = data.get("relations", {})
        
        for child_data in data.get("children", []):
            child = DataNode.from_dict(child_data, parent=node)
            node.children.append(child)
            
        return node

# --- МОДЕЛЬ ДАННЫХ ДЛЯ QT ---

class TreeModel(QAbstractItemModel):
    """Модель, связывающая наши классы DataNode с QTreeView."""
    
    def __init__(self, root_node: DataNode, parent=None):
        super().__init__(parent)
        self.root_node = root_node
        # Заголовки колонок
        self.headers = ["Название", "Тип", "Статус (Оценка)", "Авто?", "Комментарий"]

    def index(self, row: int, column: int, parent=QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self.root_node if not parent.isValid() else parent.internalPointer()
        
        if row < len(parent_item.children):
            child_item = parent_item.children[row]
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self.root_node or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.children.index(parent_item), 0, parent_item)

    def rowCount(self, parent=QModelIndex()) -> int:
        parent_item = self.root_node if not parent.isValid() else parent.internalPointer()
        return len(parent_item.children)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return item.name
            elif col == 1: return item.node_type
            elif col == 2: 
                val = STATUS_MAP.get(item.status, str(item.status))
                if item.is_auto: return f"[AUTO] {val}"
                return val
            elif col == 3: return "Да" if item.is_auto else "Нет"
            elif col == 4: return item.custom_status if item.custom_status else "-"
            
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Подсветка статуса цветом
            if index.column() == 2:
                s = item.status
                if s > 0: return QColor(200, 255, 200) # Зеленый
                if s < 0: return QColor(255, 200, 200) # Красный
        return None

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        item = index.internalPointer()
        col = index.column()

        if col == 0:
            item.name = str(value)
        elif col == 2:
            # Простая логика для примера: ввод числа -3..3
            try:
                val = int(value)
                if -3 <= val <= 3:
                    item.status = val
                else:
                    return False
            except ValueError:
                return False
        elif col == 3:
            # Переключение Авто (да/нет)
            item.is_auto = (str(value).lower() in ['да', 'true', '1', 'yes'])
            if not item.is_auto:
                # Если выключили авто, можно сбросить кастомный статус или оставить
                pass
        elif col == 4:
            item.custom_status = str(value) if value else None

        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.BackgroundRole])
        return True

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        # Делаем все колонки редактируемыми для демонстрации
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def save_to_file(self, filepath: str):
        """Сохранение всей структуры в JSON."""
        data = self.root_node.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str):
        """Загрузка структуры из JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.beginResetModel()
        self.root_node = DataNode.from_dict(data)
        self.endResetModel()

# --- ОКНО РЕДАКТИРОВАНИЯ ВЗАИМОСВЯЗЕЙ ---

class RelationsDialog(QDialog):
    def __init__(self, node: DataNode, model: TreeModel, parent=None):
        super().__init__(parent)
        self.node = node
        self.model = model
        self.setWindowTitle(f"Взаимосвязи: {self.node.name}")
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Список текущих связей (упрощенно)
        self.label_info = QLabel(f"Редактирование связей для '{node.name}'")
        layout.addWidget(self.label_info)
        
        # Здесь будет сложный интерфейс добавления связей
        # Для примера просто покажем текущие данные из relations
        relations_text = json.dumps(self.node.relations, ensure_ascii=False, indent=2)
        self.text_display = QLabel(relations_text)
        self.text_display.setWordWrap(True)
        layout.addWidget(self.text_display)
        
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)

# --- ГЛАВНОЕ ОКНО ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tag Hierarchy Manager v2.0")
        self.resize(1000, 700)
        
        self.current_file = None
        self.root_node = DataNode("Root", "root")
        self.model = TreeModel(self.root_node)
        
        self._init_ui()
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Панель инструментов
        toolbar_layout = QHBoxLayout()
        
        btn_open = QPushButton("Открыть файл")
        btn_open.clicked.connect(self.open_file)
        toolbar_layout.addWidget(btn_open)
        
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_file)
        toolbar_layout.addWidget(btn_save)
        
        btn_new = QPushButton("Новый файл")
        btn_new.clicked.connect(self.new_file)
        toolbar_layout.addWidget(btn_new)
        
        btn_relations = QPushButton("Окно взаимосвязей")
        btn_relations.clicked.connect(self.open_relations_window)
        toolbar_layout.addWidget(btn_relations)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Дерево
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.header().setStretchLastSection(True)
        self.tree_view.doubleClicked.connect(self.on_double_click)
        
        layout.addWidget(self.tree_view)
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе. Выберите файл.")

    def on_double_click(self, index: QModelIndex):
        """Обработка двойного клика - открытие редактора связей"""
        if index.isValid():
            node = index.internalPointer()
            # Открываем диалог только если клик не по первой колонке (чтобы не мешать редактированию текста)
            # Или можно сделать отдельную кнопку в строке, но для старта так проще
            dialog = RelationsDialog(node, self.model, self)
            dialog.exec()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл иерархии", "", "JSON Files (*.json)")
        if file_path:
            try:
                self.model.load_from_file(file_path)
                self.current_file = file_path
                self.statusBar().showMessage(f"Открыт файл: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def save_file(self):
        if not self.current_file:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", "hierarchy.json", "JSON Files (*.json)")
            if file_path:
                self.current_file = file_path
            else:
                return
        
        try:
            self.model.save_to_file(self.current_file)
            self.statusBar().showMessage(f"Сохранено в: {self.current_file}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def new_file(self):
        reply = QMessageBox.question(self, 'Новый файл', 
                                     "Текущие несохраненные данные будут потеряны. Создать новый?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.root_node = DataNode("Root", "root")
            # Создадим тестовую структуру для демонстрации
            branch = DataNode("Ветвь 1", "branch", self.root_node)
            self.root_node.children.append(branch)
            
            row = DataNode("Строка 1.1", "row", branch)
            row.status = 1
            row.is_auto = False
            row.custom_status = "Важная строка"
            branch.children.append(row)
            
            subrow = DataNode("Подстрока 1.1.1", "subrow", row)
            subrow.status = -2
            row.children.append(subrow)
            
            self.model.beginResetModel()
            self.model.endResetModel()
            self.current_file = None
            self.statusBar().showMessage("Создан новый файл")

    def open_relations_window(self):
        # В будущем здесь будет отдельное окно со списком всех связей проекта
        QMessageBox.information(self, "Взаимосвязи", "Функционал общего окна взаимосвязей будет реализован в следующем шаге.\nПока используйте двойной клик по элементу для просмотра его локальных связей.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
