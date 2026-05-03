"""
Graph Overlord - Графический интерфейс на PyQt5
Управление графом увлечений пользователя с двумя осями оценки (Att/Int)
"""

import sys
import os
import json
from typing import Optional, Dict, Any, List, Tuple

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from Graph_Overlord.graph import InterestGraph
    from Graph_Overlord.interest_node import InterestNode
    from Graph_Overlord.calculator import GraphCalculator
    from Graph_Overlord.templates import TemplateManager
    from Graph_Overlord.edge import Edge, EdgeType
except ImportError:
    from graph import InterestGraph
    from interest_node import InterestNode
    from calculator import GraphCalculator
    from templates import TemplateManager
    from edge import Edge, EdgeType

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QGroupBox, QLabel, QLineEdit, QTextEdit,
    QSlider, QSpinBox, QCheckBox, QPushButton, QStatusBar, QMenuBar, QMenu,
    QAction, QToolBar, QDialog, QDialogButtonBox, QFormLayout, QScrollArea,
    QDockWidget, QFileDialog, QMessageBox, QStyle, QStyledItemDelegate,
    QHeaderView, QComboBox, QDoubleSpinBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QSettings, QPoint
from PyQt5.QtGui import QFont, QColor, QIcon


class NodeTreeWidget(QTreeWidget):
    """Древовидное представление узлов графа"""
    
    node_selected = pyqtSignal(str)  # signal with node_id
    node_double_clicked = pyqtSignal(str)
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.selected_node_id: Optional[str] = None
        self.partner_tree: Optional['NodeTreeWidget'] = None
        self.highlighted_nodes: Dict[str, str] = {}  # node_id -> highlight_type
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка UI"""
        self.setHeaderLabels(["Узел", "Интерес", "Отношение", "Связей"])
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 80)
        self.setColumnWidth(2, 80)
        self.setColumnWidth(3, 60)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.setExpandsOnDoubleClick(False)
        
        # Поиск
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(f"🔍 Поиск в {self.title}...")
        self.search_box.textChanged.connect(self._filter_nodes)
        
        # Контейнер для поиска и дерева
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.search_box)
        layout.addWidget(self)
        
        # Обертка контейнера для использования в качестве виджета
        self.container_widget = container
        
        # Сигналы
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
    def set_partner_tree(self, tree: 'NodeTreeWidget'):
        """Установить партнёрское дерево для создания связей"""
        self.partner_tree = tree
        
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработка клика по элементу"""
        node_id = item.data(0, Qt.UserRole)
        if node_id:
            self.selected_node_id = node_id
            self.node_selected.emit(node_id)
            self._update_highlighting()
            
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработка двойного клика"""
        node_id = item.data(0, Qt.UserRole)
        if node_id:
            self.node_double_clicked.emit(node_id)
            
    def _filter_nodes(self, text: str):
        """Фильтрация узлов по имени"""
        text = text.lower()
        for i in range(self.topLevelItemCount()):
            top_item = self.topLevelItem(i)
            self._filter_item_recursive(top_item, text)
            
    def _filter_item_recursive(self, item: QTreeWidgetItem, text: str):
        """Рекурсивная фильтрация элемента"""
        visible = text in item.text(0).lower()
        for i in range(item.childCount()):
            child_visible = self._filter_item_recursive(item.child(i), text)
            visible = visible or child_visible
        item.setHidden(not visible)
        return visible
        
    def load_graph(self, graph: InterestGraph, calculator: GraphCalculator):
        """Загрузить граф в дерево"""
        self.clear()
        self.highlighted_nodes.clear()
        
        # Пересчёт
        calculator.calculate()
        
        # Получаем корневые узлы
        root_ids = graph.get_root_nodes()
        for node_id in root_ids:
            node = graph.get_node(node_id)
            if node and node.active:
                self._add_node_recursive(node, graph, None)
                
    def _add_node_recursive(self, node: InterestNode, graph: InterestGraph, 
                           parent_item: Optional[QTreeWidgetItem]):
        """Рекурсивно добавить узел и его потомков"""
        if not node.active:
            return
            
        # Подсчёт связей
        edge_count = 0
        parent_id = graph.get_parent(node.id)
        if parent_id:
            edge_count += 1
        edge_count += len(graph.get_children(node.id))
        edge_count += len(graph.get_associations(node.id))
        
        # Формирование отображаемых значений
        int_display = f"{node.int:.0f}" if node.int is not None else "-"
        att_display = f"{node.att:.0f}" if node.att is not None else "-"
        
        # Создание элемента
        item = QTreeWidgetItem([node.name, int_display, att_display, str(edge_count)])
        item.setData(0, Qt.UserRole, node.id)
        
        # Иконка
        if node.is_category:
            item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
        else:
            item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
            
        # Статусные иконки
        status_icons = []
        if node.locked:
            status_icons.append("🔒")
        if node.user_att is not None or node.user_int is not None:
            status_icons.append("✏️")
        if status_icons:
            item.setText(0, item.text(0) + " " + " ".join(status_icons))
        
        if parent_item:
            parent_item.addChild(item)
        else:
            self.addTopLevelItem(item)
            
        # Дети
        for child_id in graph.get_children(node.id):
            child = graph.get_node(child_id)
            if child and child.active:
                self._add_node_recursive(child, graph, item)
                
    def set_highlighted_nodes(self, highlighted: Dict[str, str]):
        """Установить подсвеченные узлы"""
        self.highlighted_nodes = highlighted
        self._update_highlighting()
        
    def _update_highlighting(self):
        """Обновить подсветку узлов"""
        # Сброс всех цветов
        for i in range(self.topLevelItemCount()):
            self._reset_item_colors(self.topLevelItem(i))
            
        # Применение подсветки
        for node_id, highlight_type in self.highlighted_nodes.items():
            item = self._find_item_by_node_id(node_id)
            if item:
                if highlight_type == "outgoing":
                    item.setBackground(0, QColor(220, 255, 220))  # светло-зелёный
                elif highlight_type == "incoming":
                    item.setBackground(0, QColor(255, 220, 220))  # светло-красный
                elif highlight_type == "bidirectional":
                    item.setBackground(0, QColor(255, 255, 200))  # жёлтый
                    
    def _reset_item_colors(self, item: QTreeWidgetItem):
        """Сбросить цвета элемента"""
        item.setBackground(0, Qt.transparent)
        for i in range(item.childCount()):
            self._reset_item_colors(item.child(i))
            
    def _find_item_by_node_id(self, node_id: str) -> Optional[QTreeWidgetItem]:
        """Найти элемент по ID узла"""
        for i in range(self.topLevelItemCount()):
            found = self._find_item_recursive(self.topLevelItem(i), node_id)
            if found:
                return found
        return None
        
    def _find_item_recursive(self, item: QTreeWidgetItem, node_id: str) -> Optional[QTreeWidgetItem]:
        """Рекурсивный поиск элемента"""
        if item.data(0, Qt.UserRole) == node_id:
            return item
        for i in range(item.childCount()):
            found = self._find_item_recursive(item.child(i), node_id)
            if found:
                return found
        return None
        
    def clear_selection(self):
        """Снять выделение"""
        self.selected_node_id = None
        self.clearSelection()
        self.highlighted_nodes.clear()
        self._update_highlighting()


class TreeListPanel(QDockWidget):
    """Левая панель - Список деревьев"""
    
    list_selected = pyqtSignal(str)  # signal with list_name
    
    def __init__(self, parent=None):
        super().__init__("Списки деревьев", parent)
        self.setObjectName("TreeListPanel")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.tree_lists: Dict[str, Dict] = {}  # name -> {nodes, internal_edges, external_edges}
        self.current_list: Optional[str] = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка UI"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Поиск
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Фильтр списков...")
        self.search_box.textChanged.connect(self._filter_lists)
        layout.addWidget(self.search_box)
        
        # Таблица списков
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Название", "Узлов", "Внутр. связей", "Внешн. связей"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemClicked.connect(self._on_list_selected)
        self.table.itemDoubleClicked.connect(self._on_list_double_clicked)
        layout.addWidget(self.table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("➕ Создать")
        self.create_btn.clicked.connect(self._create_list)
        btn_layout.addWidget(self.create_btn)
        
        self.delete_btn = QPushButton("🗑 Удалить")
        self.delete_btn.clicked.connect(self._delete_list)
        btn_layout.addWidget(self.delete_btn)
        
        self.rename_btn = QPushButton("✏️ Переименовать")
        self.rename_btn.clicked.connect(self._rename_list)
        btn_layout.addWidget(self.rename_btn)
        
        layout.addLayout(btn_layout)
        
        self.setWidget(container)
        
    def add_list(self, name: str, nodes: List[str], internal_edges: int, external_edges: int):
        """Добавить список в таблицу"""
        self.tree_lists[name] = {
            "nodes": nodes,
            "internal_edges": internal_edges,
            "external_edges": external_edges
        }
        self._refresh_table()
        
    def _refresh_table(self):
        """Обновить таблицу"""
        self.table.setRowCount(0)
        filter_text = self.search_box.text().lower()
        
        for name, data in self.tree_lists.items():
            if filter_text and filter_text not in name.lower():
                continue
                
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(str(len(data["nodes"]))))
            self.table.setItem(row, 2, QTableWidgetItem(str(data["internal_edges"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(data["external_edges"])))
            
            # Подсветка текущего списка
            if name == self.current_list:
                for col in range(4):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor(173, 216, 230))  # светло-синий
                        
    def _filter_lists(self, text: str):
        """Фильтрация списков"""
        self._refresh_table()
        
    def _on_list_selected(self, item: QTableWidgetItem):
        """Выбор списка"""
        row = item.row()
        name = self.table.item(row, 0).text()
        self.current_list = name
        self._refresh_table()
        self.list_selected.emit(name)
        
    def _on_list_double_clicked(self, item: QTableWidgetItem):
        """Двойной клик по списку - переименование"""
        self.table.editItem(item)
        
    def _create_list(self):
        """Создание нового списка"""
        name, ok = QInputDialog.getText(self, "Создать список", "Введите название списка:")
        if ok and name:
            self.add_list(name, [], 0, 0)
            
    def _delete_list(self):
        """Удаление списка"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            name = self.table.item(current_row, 0).text()
            reply = QMessageBox.question(self, "Подтверждение",
                                         f"Удалить список '{name}'?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.tree_lists[name]
                self._refresh_table()
                
    def _rename_list(self):
        """Переименование списка"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            old_name = self.table.item(current_row, 0).text()
            new_name, ok = QInputDialog.getText(self, "Переименовать список",
                                                "Новое название:", text=old_name)
            if ok and new_name and new_name != old_name:
                self.tree_lists[new_name] = self.tree_lists.pop(old_name)
                self._refresh_table()


class InspectorPanel(QDockWidget):
    """Правая панель - Инспектор"""
    
    node_changed = pyqtSignal(str)  # node_id
    connection_selected = pyqtSignal(object)  # edge object
    connection_deleted = pyqtSignal(object)
    recalculate_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Инспектор", parent)
        self.setObjectName("InspectorPanel")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setMinimumWidth(350)
        
        self.graph: Optional[InterestGraph] = None
        self.calculator: Optional[GraphCalculator] = None
        self.current_node_id: Optional[str] = None
        self.current_edge: Optional[Edge] = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка UI"""
        container = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        
        layout = QVBoxLayout(container)
        
        # Группа "Инфо узла"
        self.info_group = QGroupBox("Инфо узла")
        info_layout = QFormLayout(self.info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        info_layout.addRow("Имя:", self.name_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        info_layout.addRow("Описание:", self.desc_edit)
        
        self.id_label = QLabel("-")
        info_layout.addRow("ID узла:", self.id_label)
        
        layout.addWidget(self.info_group)
        
        # Группа "Параметры"
        self.params_group = QGroupBox("Параметры")
        params_layout = QVBoxLayout(self.params_group)
        
        self.active_check = QCheckBox("Активен (включая всё поддерево)")
        self.active_check.stateChanged.connect(self._on_active_changed)
        params_layout.addWidget(self.active_check)
        
        self.locked_check = QCheckBox("Заблокирован (исключён из перерасчётов)")
        self.locked_check.stateChanged.connect(self._on_locked_changed)
        params_layout.addWidget(self.locked_check)
        
        weight_layout = QHBoxLayout()
        self.weight_label = QLabel("-")
        weight_layout.addWidget(QLabel("Текущий вес:"))
        weight_layout.addWidget(self.weight_label)
        weight_layout.addStretch()
        
        self.recalc_btn = QPushButton("🔄 Пересчитать")
        self.recalc_btn.clicked.connect(lambda: self.recalculate_requested.emit())
        weight_layout.addWidget(self.recalc_btn)
        
        params_layout.addLayout(weight_layout)
        layout.addWidget(self.params_group)
        
        # Группа "Ручная настройка"
        self.manual_group = QGroupBox("Ручная настройка")
        manual_layout = QFormLayout(self.manual_group)
        
        # Интерес
        int_layout = QHBoxLayout()
        self.int_manual_check = QCheckBox("Ручной режим")
        self.int_slider = QSlider(Qt.Horizontal)
        self.int_slider.setRange(0, 100)
        self.int_spin = QDoubleSpinBox()
        self.int_spin.setRange(0, 1)
        self.int_spin.setSingleStep(0.01)
        self.int_spin.setDecimals(2)
        
        self.int_slider.valueChanged.connect(lambda v: self.int_spin.setValue(v / 100.0))
        self.int_spin.valueChanged.connect(lambda v: self.int_slider.setValue(int(v * 100)))
        
        int_layout.addWidget(QLabel("Интерес:"))
        int_layout.addWidget(self.int_slider)
        int_layout.addWidget(self.int_spin)
        int_layout.addWidget(self.int_manual_check)
        manual_layout.addRow(int_layout)
        
        # Отношение
        att_layout = QHBoxLayout()
        self.att_manual_check = QCheckBox("Ручной режим")
        self.att_slider = QSlider(Qt.Horizontal)
        self.att_slider.setRange(0, 100)
        self.att_spin = QDoubleSpinBox()
        self.att_spin.setRange(0, 1)
        self.att_spin.setSingleStep(0.01)
        self.att_spin.setDecimals(2)
        
        self.att_slider.valueChanged.connect(lambda v: self.att_spin.setValue(v / 100.0))
        self.att_spin.valueChanged.connect(lambda v: self.att_slider.setValue(int(v * 100)))
        
        att_layout.addWidget(QLabel("Отношение:"))
        att_layout.addWidget(self.att_slider)
        att_layout.addWidget(self.att_spin)
        att_layout.addWidget(self.att_manual_check)
        manual_layout.addRow(att_layout)
        
        layout.addWidget(self.manual_group)
        
        # Группа "Монитор связей"
        self.monitor_group = QGroupBox("Монитор связей (0 связей)")
        monitor_layout = QVBoxLayout(self.monitor_group)
        
        self.connections_list = QListWidget()
        self.connections_list.itemClicked.connect(self._on_connection_selected)
        monitor_layout.addWidget(self.connections_list)
        
        self.add_connection_btn = QPushButton("➕ Добавить связь")
        self.add_connection_btn.clicked.connect(self._add_connection)
        self.add_connection_btn.setEnabled(False)
        monitor_layout.addWidget(self.add_connection_btn)
        
        layout.addWidget(self.monitor_group)
        
        # Группа "Редактор связи" (скрыта по умолчанию)
        self.editor_group = QGroupBox("Редактор связи")
        self.editor_group.setVisible(False)
        editor_layout = QVBoxLayout(self.editor_group)
        
        # Два столбца
        columns_layout = QHBoxLayout()
        
        # Прямое влияние
        forward_group = QGroupBox("Прямое влияние")
        forward_layout = QFormLayout(forward_group)
        
        self.fw_att_slider = QSlider(Qt.Horizontal)
        self.fw_att_slider.setRange(0, 100)
        self.fw_att_spin = QDoubleSpinBox()
        self.fw_att_spin.setRange(0, 1)
        self.fw_att_spin.setSingleStep(0.01)
        self.fw_att_spin.setDecimals(2)
        self.fw_att_slider.valueChanged.connect(lambda v: self.fw_att_spin.setValue(v / 100.0))
        self.fw_att_spin.valueChanged.connect(lambda v: self.fw_att_slider.setValue(int(v * 100)))
        
        fw_att_layout = QHBoxLayout()
        fw_att_layout.addWidget(self.fw_att_slider)
        fw_att_layout.addWidget(self.fw_att_spin)
        forward_layout.addRow("Att:", fw_att_layout)
        
        self.fw_int_slider = QSlider(Qt.Horizontal)
        self.fw_int_slider.setRange(0, 100)
        self.fw_int_spin = QDoubleSpinBox()
        self.fw_int_spin.setRange(0, 1)
        self.fw_int_spin.setSingleStep(0.01)
        self.fw_int_spin.setDecimals(2)
        self.fw_int_slider.valueChanged.connect(lambda v: self.fw_int_spin.setValue(v / 100.0))
        self.fw_int_spin.valueChanged.connect(lambda v: self.fw_int_slider.setValue(int(v * 100)))
        
        fw_int_layout = QHBoxLayout()
        fw_int_layout.addWidget(self.fw_int_slider)
        fw_int_layout.addWidget(self.fw_int_spin)
        forward_layout.addRow("Int:", fw_int_layout)
        
        columns_layout.addWidget(forward_group)
        
        # Обратное влияние
        backward_group = QGroupBox("Обратное влияние")
        backward_layout = QFormLayout(backward_group)
        
        self.bw_att_slider = QSlider(Qt.Horizontal)
        self.bw_att_slider.setRange(0, 100)
        self.bw_att_spin = QDoubleSpinBox()
        self.bw_att_spin.setRange(0, 1)
        self.bw_att_spin.setSingleStep(0.01)
        self.bw_att_spin.setDecimals(2)
        self.bw_att_slider.valueChanged.connect(lambda v: self.bw_att_spin.setValue(v / 100.0))
        self.bw_att_spin.valueChanged.connect(lambda v: self.bw_att_slider.setValue(int(v * 100)))
        
        bw_att_layout = QHBoxLayout()
        bw_att_layout.addWidget(self.bw_att_slider)
        bw_att_layout.addWidget(self.bw_att_spin)
        backward_layout.addRow("Att:", bw_att_layout)
        
        self.bw_int_slider = QSlider(Qt.Horizontal)
        self.bw_int_slider.setRange(0, 100)
        self.bw_int_spin = QDoubleSpinBox()
        self.bw_int_spin.setRange(0, 1)
        self.bw_int_spin.setSingleStep(0.01)
        self.bw_int_spin.setDecimals(2)
        self.bw_int_slider.valueChanged.connect(lambda v: self.bw_int_spin.setValue(v / 100.0))
        self.bw_int_spin.valueChanged.connect(lambda v: self.bw_int_slider.setValue(int(v * 100)))
        
        bw_int_layout = QHBoxLayout()
        bw_int_layout.addWidget(self.bw_int_slider)
        bw_int_layout.addWidget(self.bw_int_spin)
        backward_layout.addRow("Int:", bw_int_layout)
        
        columns_layout.addWidget(backward_group)
        
        editor_layout.addLayout(columns_layout)
        
        # Кнопки редактора
        editor_btn_layout = QHBoxLayout()
        
        self.sync_btn = QPushButton("🔄 Синхронизировать")
        self.sync_btn.clicked.connect(self._show_sync_menu)
        editor_btn_layout.addWidget(self.sync_btn)
        
        self.apply_btn = QPushButton("💾 Применить")
        self.apply_btn.clicked.connect(self._apply_edge_changes)
        editor_btn_layout.addWidget(self.apply_btn)
        
        self.delete_edge_btn = QPushButton("🗑 Удалить связь")
        self.delete_edge_btn.clicked.connect(self._delete_edge)
        editor_btn_layout.addWidget(self.delete_edge_btn)
        
        editor_layout.addLayout(editor_btn_layout)
        
        layout.addWidget(self.editor_group)
        
        layout.addStretch()
        
        self.setWidget(scroll)
        
    def set_graph(self, graph: InterestGraph, calculator: GraphCalculator):
        """Установить граф и калькулятор"""
        self.graph = graph
        self.calculator = calculator
        
    def load_node(self, node_id: str):
        """Загрузить данные узла"""
        if not self.graph:
            return
            
        node = self.graph.get_node(node_id)
        if not node:
            return
            
        self.current_node_id = node_id
        
        # Инфо
        self.name_edit.blockSignals(True)
        self.name_edit.setText(node.name)
        self.name_edit.blockSignals(False)
        
        self.desc_edit.blockSignals(True)
        self.desc_edit.setText(getattr(node, 'description', ''))
        self.desc_edit.blockSignals(False)
        
        self.id_label.setText(node.id)
        
        # Параметры
        self.active_check.blockSignals(True)
        self.active_check.setChecked(node.active)
        self.active_check.blockSignals(False)
        
        self.locked_check.blockSignals(True)
        self.locked_check.setChecked(node.locked)
        self.locked_check.blockSignals(False)
        
        # Вес
        uncertainty = self.calculator.get_uncertainty(node_id) if self.calculator else (0, False)
        weight = node.user_weight_override if node.user_weight_override is not None else \
                 (node.user_weight_att + node.user_weight_int) / 2 if node.user_att or node.user_int else 0
        self.weight_label.setText(f"{weight:.4f}")
        
        # Ручная настройка
        self.int_manual_check.blockSignals(True)
        self.int_manual_check.setChecked(node.user_int is not None)
        self.int_manual_check.blockSignals(False)
        
        self.att_manual_check.blockSignals(True)
        self.att_manual_check.setChecked(node.user_att is not None)
        self.att_manual_check.blockSignals(False)
        
        int_val = node.user_int if node.user_int is not None else node.int
        att_val = node.user_att if node.user_att is not None else (node.att + 100) / 2
        
        self.int_slider.blockSignals(True)
        self.int_spin.blockSignals(True)
        self.int_slider.setValue(int(int_val))
        self.int_spin.setValue(int_val / 100.0)
        self.int_slider.blockSignals(False)
        self.int_spin.blockSignals(False)
        
        self.att_slider.blockSignals(True)
        self.att_spin.blockSignals(True)
        self.att_slider.setValue(int(max(0, min(100, att_val))))
        self.att_spin.setValue(max(0, min(1, att_val / 100.0)))
        self.att_slider.blockSignals(False)
        self.att_spin.blockSignals(False)
        
        # Монитор связей
        self._refresh_connections_list(node)
        
        # Скрыть редактор связи
        self.editor_group.setVisible(False)
        self.current_edge = None
        
    def _refresh_connections_list(self, node: InterestNode):
        """Обновить список связей"""
        self.connections_list.clear()
        
        if not self.graph:
            self.monitor_group.setTitle("Монитор связей (0 связей)")
            return
            
        incoming = []
        outgoing = []
        bidirectional = []
        
        # Входящие
        parent_id = self.graph.get_parent(node.id)
        if parent_id:
            parent = self.graph.get_node(parent_id)
            if parent:
                incoming.append((parent, "↓", parent_id))
                
        for child_id in self.graph.get_children(node.id):
            child = self.graph.get_node(child_id)
            if child:
                outgoing.append((child, "↑", child_id))
                
        # Ассоциации
        for connected_id, edge in self.graph.get_associations(node.id):
            connected = self.graph.get_node(connected_id)
            if connected:
                if edge.source_id == node.id and edge.target_id == connected_id:
                    if any(e.source_id == connected_id and e.target_id == node.id 
                           for _, e in self.graph.get_associations(connected_id)):
                        bidirectional.append((connected, "↔", connected_id, edge))
                    else:
                        outgoing.append((connected, "→", connected_id, edge))
                else:
                    incoming.append((connected, "←", connected_id, edge))
                    
        total = len(incoming) + len(outgoing) + len(bidirectional)
        self.monitor_group.setTitle(f"Монитор связей ({total} связей)")
        
        # Добавляем в список
        for conn, icon, conn_id, *extra in incoming:
            item_text = f"{icon} {conn.name} ({conn_id})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, ("incoming", conn_id, extra[0] if extra else None))
            self.connections_list.addItem(item)
            
        for conn, icon, conn_id, *extra in outgoing:
            item_text = f"{icon} {conn.name} ({conn_id})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, ("outgoing", conn_id, extra[0] if extra else None))
            self.connections_list.addItem(item)
            
        for conn, icon, conn_id, edge in bidirectional:
            item_text = f"{icon} {conn.name} ({conn_id})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, ("bidirectional", conn_id, edge))
            self.connections_list.addItem(item)
            
    def _on_name_changed(self, text: str):
        """Изменение имени узла"""
        if self.current_node_id and self.graph:
            node = self.graph.get_node(self.current_node_id)
            if node:
                node.name = text
                self.node_changed.emit(self.current_node_id)
                
    def _on_desc_changed(self):
        """Изменение описания"""
        pass  # Можно реализовать при необходимости
        
    def _on_active_changed(self, state: int):
        """Изменение активности"""
        if self.current_node_id and self.graph:
            node = self.graph.get_node(self.current_node_id)
            if node:
                node.active = bool(state)
                self.node_changed.emit(self.current_node_id)
                
    def _on_locked_changed(self, state: int):
        """Изменение блокировки"""
        if self.current_node_id and self.graph:
            node = self.graph.get_node(self.current_node_id)
            if node:
                node.locked = bool(state)
                self.node_changed.emit(self.current_node_id)
                
    def _on_connection_selected(self, item: QListWidgetItem):
        """Выбор связи из списка"""
        data = item.data(Qt.UserRole)
        if not data:
            self.editor_group.setVisible(False)
            self.current_edge = None
            return
            
        direction, conn_id, edge = data
        
        if edge:
            self.current_edge = edge
            self.editor_group.setTitle(f"Редактор связи: {self._get_edge_title()}")
            self.editor_group.setVisible(True)
            
            # Загрузка значений
            self.fw_att_slider.setValue(int(edge.fw_att * 100))
            self.fw_int_slider.setValue(int(edge.fw_int * 100))
            self.bw_att_slider.setValue(int(edge.bw_att * 100))
            self.bw_int_slider.setValue(int(edge.bw_int * 100))
            
            self.connection_selected.emit(edge)
        else:
            self.editor_group.setVisible(False)
            self.current_edge = None
            
    def _get_edge_title(self) -> str:
        """Получить заголовок для редактора связи"""
        if not self.current_edge or not self.graph:
            return ""
        src = self.graph.get_node(self.current_edge.source_id)
        tgt = self.graph.get_node(self.current_edge.target_id)
        src_name = src.name if src else self.current_edge.source_id
        tgt_name = tgt.name if tgt else self.current_edge.target_id
        return f"{src_name} → {tgt_name}"
        
    def _add_connection(self):
        """Добавить связь (открывает диалог)"""
        # Будет реализовано через главный класс
        pass
        
    def _show_sync_menu(self):
        """Показать меню синхронизации"""
        menu = QMenu(self)
        menu.addAction("Зеркалировать Att и Int внутри прямого", 
                       lambda: self._sync_fw_att_int())
        menu.addAction("Зеркалировать прямое и обратное",
                       lambda: self._sync_forward_backward())
        menu.addAction("Нормализовать",
                       lambda: self._normalize_weights())
        menu.exec_(self.sync_btn.mapToGlobal(self.sync_btn.rect().bottomLeft()))
        
    def _sync_fw_att_int(self):
        """Синхронизировать Att и Int в прямом направлении"""
        val = self.fw_att_slider.value()
        self.fw_int_slider.setValue(val)
        
    def _sync_forward_backward(self):
        """Синхронизировать прямое и обратное"""
        self.bw_att_slider.setValue(self.fw_att_slider.value())
        self.bw_int_slider.setValue(self.fw_int_slider.value())
        
    def _normalize_weights(self):
        """Нормализовать веса"""
        fw_total = self.fw_att_slider.value() + self.fw_int_slider.value()
        if fw_total > 100:
            scale = 100 / fw_total
            self.fw_att_slider.setValue(int(self.fw_att_slider.value() * scale))
            self.fw_int_slider.setValue(int(self.fw_int_slider.value() * scale))
            
        bw_total = self.bw_att_slider.value() + self.bw_int_slider.value()
        if bw_total > 100:
            scale = 100 / bw_total
            self.bw_att_slider.setValue(int(self.bw_att_slider.value() * scale))
            self.bw_int_slider.setValue(int(self.bw_int_slider.value() * scale))
            
    def _apply_edge_changes(self):
        """Применить изменения связи"""
        if self.current_edge:
            self.current_edge.fw_att = self.fw_att_slider.value() / 100.0
            self.current_edge.fw_int = self.fw_int_slider.value() / 100.0
            self.current_edge.bw_att = self.bw_att_slider.value() / 100.0
            self.current_edge.bw_int = self.bw_int_slider.value() / 100.0
            self.node_changed.emit(self.current_node_id)
            
    def _delete_edge(self):
        """Удалить связь"""
        if self.current_edge and self.graph:
            reply = QMessageBox.question(self, "Подтверждение",
                                         "Удалить эту связь?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.graph.remove_edge(self.current_edge)
                self.editor_group.setVisible(False)
                self.current_edge = None
                self.connection_deleted.emit(self.current_edge)
                self.node_changed.emit(self.current_node_id)


class TemplatesWindow(QWidget):
    """Плавающее окно шаблонов"""
    
    template_applied = pyqtSignal(str)  # template_name
    template_saved = pyqtSignal(str)
    
    def __init__(self, template_manager: TemplateManager):
        super().__init__()
        self.template_manager = template_manager
        self.setWindowTitle("Шаблоны")
        self.resize(600, 400)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка UI"""
        layout = QVBoxLayout(self)
        
        # Поиск
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Поиск шаблонов...")
        self.search_box.textChanged.connect(self._filter_templates)
        layout.addWidget(self.search_box)
        
        # Горизонтальный сплиттер
        splitter = QSplitter(Qt.Horizontal)
        
        # Список шаблонов
        self.templates_list = QListWidget()
        self._refresh_templates_list()
        splitter.addWidget(self.templates_list)
        
        # Предпросмотр
        self.preview_tree = QTreeWidget()
        self.preview_tree.setHeaderLabels(["Шаблон", "Параметры"])
        self.preview_tree.setEnabled(False)
        splitter.addWidget(self.preview_tree)
        
        splitter.setSizes([300, 300])
        layout.addWidget(splitter)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("📋 Применить")
        self.apply_btn.clicked.connect(self._apply_template)
        btn_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("💾 Сохранить выделенное")
        self.save_btn.clicked.connect(self._save_template)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("🗑 Удалить шаблон")
        self.delete_btn.clicked.connect(self._delete_template)
        btn_layout.addWidget(self.delete_btn)
        
        self.export_btn = QPushButton("📤 Экспорт")
        self.export_btn.clicked.connect(self._export_template)
        btn_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("📥 Импорт")
        self.import_btn.clicked.connect(self._import_template)
        btn_layout.addWidget(self.import_btn)
        
        layout.addLayout(btn_layout)
        
    def _refresh_templates_list(self):
        """Обновить список шаблонов"""
        self.templates_list.clear()
        for name in self.template_manager.list_templates():
            self.templates_list.addItem(name)
            
    def _filter_templates(self, text: str):
        """Фильтрация шаблонов"""
        text = text.lower()
        for i in range(self.templates_list.count()):
            item = self.templates_list.item(i)
            item.setHidden(text not in item.text().lower())
            
    def _apply_template(self):
        """Применить шаблон"""
        current = self.templates_list.currentItem()
        if current:
            self.template_applied.emit(current.text())
            
    def _save_template(self):
        """Сохранить шаблон"""
        name, ok = QInputDialog.getText(self, "Сохранить шаблон", "Название шаблона:")
        if ok and name:
            self.template_saved.emit(name)
            
    def _delete_template(self):
        """Удалить шаблон"""
        current = self.templates_list.currentItem()
        if current:
            reply = QMessageBox.question(self, "Подтверждение",
                                         f"Удалить шаблон '{current.text()}'?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.template_manager.templates[current.text()]
                self._refresh_templates_list()
                
    def _export_template(self):
        """Экспорт шаблона"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт шаблона", "", "JSON files (*.json)"
        )
        if filename:
            current = self.templates_list.currentItem()
            if current:
                template = self.template_manager.get_template(current.text())
                if template:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(template.to_json())
                        
    def _import_template(self):
        """Импорт шаблона"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Импорт шаблона", "", "JSON files (*.json)"
        )
        if filename:
            try:
                self.template_manager.load_template_from_file(filename)
                self._refresh_templates_list()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))


class CreateNodeDialog(QDialog):
    """Диалог создания узла"""
    
    def __init__(self, parent=None, parent_nodes: List[Tuple[str, str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Создать узел")
        self.resize(400, 300)
        
        self.parent_nodes = parent_nodes or []
        
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        layout.addRow("Имя:", self.name_edit)
        
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("(корневой)", "")
        for node_id, name in self.parent_nodes:
            self.parent_combo.addItem(name, node_id)
        layout.addRow("Родитель:", self.parent_combo)
        
        self.int_slider = QSlider(Qt.Horizontal)
        self.int_slider.setRange(0, 100)
        self.int_spin = QDoubleSpinBox()
        self.int_spin.setRange(0, 1)
        self.int_spin.setSingleStep(0.01)
        self.int_spin.setDecimals(2)
        self.int_slider.valueChanged.connect(lambda v: self.int_spin.setValue(v / 100.0))
        self.int_spin.valueChanged.connect(lambda v: self.int_slider.setValue(int(v * 100)))
        
        int_widget = QWidget()
        int_layout = QHBoxLayout(int_widget)
        int_layout.setContentsMargins(0, 0, 0, 0)
        int_layout.addWidget(self.int_slider)
        int_layout.addWidget(self.int_spin)
        layout.addRow("Интерес:", int_widget)
        
        self.att_slider = QSlider(Qt.Horizontal)
        self.att_slider.setRange(0, 100)
        self.att_spin = QDoubleSpinBox()
        self.att_spin.setRange(0, 1)
        self.att_spin.setSingleStep(0.01)
        self.att_spin.setDecimals(2)
        self.att_slider.valueChanged.connect(lambda v: self.att_spin.setValue(v / 100.0))
        self.att_spin.valueChanged.connect(lambda v: self.att_slider.setValue(int(v * 100)))
        
        att_widget = QWidget()
        att_layout = QHBoxLayout(att_widget)
        att_layout.setContentsMargins(0, 0, 0, 0)
        att_layout.addWidget(self.att_slider)
        att_layout.addWidget(self.att_spin)
        layout.addRow("Отношение:", att_widget)
        
        self.active_check = QCheckBox("Активен")
        self.active_check.setChecked(True)
        layout.addRow(self.active_check)
        
        self.locked_check = QCheckBox("Заблокирован")
        layout.addRow(self.locked_check)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_data(self) -> Dict:
        """Получить данные диалога"""
        return {
            "name": self.name_edit.text(),
            "parent_id": self.parent_combo.currentData(),
            "int": self.int_spin.value() * 100,
            "att": self.att_spin.value() * 200 - 100,  # Преобразование в диапазон [-100, 100]
            "active": self.active_check.isChecked(),
            "locked": self.locked_check.isChecked(),
        }


class CreateEdgeDialog(QDialog):
    """Диалог создания связи"""
    
    def __init__(self, parent=None, nodes: List[Tuple[str, str]] = None,
                 source_id: str = None, target_id: str = None):
        super().__init__(parent)
        self.setWindowTitle("Создать связь")
        self.resize(450, 350)
        
        self.nodes = nodes or []
        
        layout = QFormLayout(self)
        
        # Источник
        self.source_combo = QComboBox()
        for node_id, name in self.nodes:
            self.source_combo.addItem(f"{name} ({node_id})", node_id)
            if source_id and node_id == source_id:
                self.source_combo.setCurrentIndex(self.source_combo.count() - 1)
        layout.addRow("Источник:", self.source_combo)
        
        # Цель
        self.target_combo = QComboBox()
        for node_id, name in self.nodes:
            self.target_combo.addItem(f"{name} ({node_id})", node_id)
            if target_id and node_id == target_id:
                self.target_combo.setCurrentIndex(self.target_combo.count() - 1)
        layout.addRow("Цель:", self.target_combo)
        
        # Тип связи
        self.edge_type_combo = QComboBox()
        self.edge_type_combo.addItem("Иерархия (Parent)", "parent")
        self.edge_type_combo.addItem("Ассоциация", "association")
        layout.addRow("Тип связи:", self.edge_type_combo)
        
        # Веса
        weights_group = QGroupBox("Веса влияния")
        weights_layout = QFormLayout(weights_group)
        
        self.fw_att_spin = QDoubleSpinBox()
        self.fw_att_spin.setRange(-1, 1)
        self.fw_att_spin.setSingleStep(0.1)
        self.fw_att_spin.setValue(0.7)
        weights_layout.addRow("Прямое Att:", self.fw_att_spin)
        
        self.fw_int_spin = QDoubleSpinBox()
        self.fw_int_spin.setRange(0, 1)
        self.fw_int_spin.setSingleStep(0.1)
        self.fw_int_spin.setValue(0.6)
        weights_layout.addRow("Прямое Int:", self.fw_int_spin)
        
        self.bw_att_spin = QDoubleSpinBox()
        self.bw_att_spin.setRange(-1, 1)
        self.bw_att_spin.setSingleStep(0.1)
        self.bw_att_spin.setValue(0.7)
        weights_layout.addRow("Обратное Att:", self.bw_att_spin)
        
        self.bw_int_spin = QDoubleSpinBox()
        self.bw_int_spin.setRange(0, 1)
        self.bw_int_spin.setSingleStep(0.1)
        self.bw_int_spin.setValue(0.6)
        weights_layout.addRow("Обратное Int:", self.bw_int_spin)
        
        layout.addRow(weights_group)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_data(self) -> Dict:
        """Получить данные диалога"""
        return {
            "source_id": self.source_combo.currentData(),
            "target_id": self.target_combo.currentData(),
            "type": self.edge_type_combo.currentData(),
            "fw_att": self.fw_att_spin.value(),
            "fw_int": self.fw_int_spin.value(),
            "bw_att": self.bw_att_spin.value(),
            "bw_int": self.bw_int_spin.value(),
        }


# Import QInputDialog for dialogs
from PyQt5.QtWidgets import QInputDialog


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph Overlord - Управление графом увлечений")
        self.resize(1400, 900)
        
        # Инициализация компонентов
        self.graph = InterestGraph()
        self.calculator = GraphCalculator(self.graph)
        self.template_manager = TemplateManager()
        self.template_manager.create_builtin_templates()
        
        # Создаём начальные корневые узлы
        self._create_root_nodes()
        
        # Настройка UI
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Восстановление настроек
        self._restore_settings()
        
        # Первоначальное обновление
        self._refresh_all()
        
    def _create_root_nodes(self):
        """Создать корневые категории"""
        root_categories = [
            ("root_sports", "Спорт", True),
            ("root_games", "Игры", True),
            ("root_creative", "Творчество", True),
            ("root_science", "Наука", True),
            ("root_lifestyle", "Образ жизни", True),
        ]
        
        for node_id, name, is_cat in root_categories:
            self.graph.add_node(node_id, name, is_category=is_cat)
            
    def _setup_ui(self):
        """Настройка основного UI"""
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Горизонтальный сплиттер для двух деревьев
        h_splitter = QSplitter(Qt.Horizontal)
        
        # Дерево А
        self.tree_a = NodeTreeWidget("Дерево А")
        h_splitter.addWidget(self.tree_a.container_widget)
        
        # Дерево Б
        self.tree_b = NodeTreeWidget("Дерево Б")
        h_splitter.addWidget(self.tree_b.container_widget)
        
        h_splitter.setSizes([700, 700])
        
        main_layout.addWidget(h_splitter)
        
        # Установка партнёрских деревьев
        self.tree_a.set_partner_tree(self.tree_b)
        self.tree_b.set_partner_tree(self.tree_a)
        
        # Сигналы деревьев
        self.tree_a.node_selected.connect(self._on_node_selected)
        self.tree_b.node_selected.connect(self._on_node_selected)
        
        # Левая панель - списки деревьев
        self.left_panel = TreeListPanel(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_panel)
        self.left_panel.list_selected.connect(self._on_list_selected)
        
        # Правая панель - инспектор
        self.right_panel = InspectorPanel(self)
        self.right_panel.set_graph(self.graph, self.calculator)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_panel)
        self.right_panel.node_changed.connect(self._on_node_changed)
        self.right_panel.recalculate_requested.connect(self._recalculate)
        
        # Окно шаблонов (плавающее)
        self.templates_window = TemplatesWindow(self.template_manager)
        self.templates_window.template_applied.connect(self._apply_template)
        
    def _setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu("Файл")
        
        new_action = QAction("📁 Новый", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        load_action = QAction("📂 Загрузить", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_project)
        file_menu.addAction(load_action)
        
        save_action = QAction("💾 Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Правка
        edit_menu = menubar.addMenu("Правка")
        
        undo_action = QAction("↩ Отменить", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("↪ Повторить", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        apply_all_action = QAction("Применить всё", self)
        apply_all_action.triggered.connect(self._apply_all)
        edit_menu.addAction(apply_all_action)
        
        # Расчёт
        calc_menu = menubar.addMenu("Расчёт")
        
        recalc_action = QAction("🔄 Перерасчёт весов", self)
        recalc_action.setShortcut("F5")
        recalc_action.triggered.connect(self._recalculate)
        calc_menu.addAction(recalc_action)
        
        reset_calc_action = QAction("Сброс перерасчёта", self)
        reset_calc_action.triggered.connect(self._reset_calculation)
        calc_menu.addAction(reset_calc_action)
        
        # Вид
        view_menu = menubar.addMenu("Вид")
        
        templates_action = QAction("📋 Показать шаблоны", self)
        templates_action.setShortcut("Ctrl+T")
        templates_action.triggered.connect(self._toggle_templates)
        view_menu.addAction(templates_action)
        
        dark_theme_action = QAction("🌓 Тёмная тема", self)
        dark_theme_action.triggered.connect(self._toggle_dark_theme)
        view_menu.addAction(dark_theme_action)
        
        view_menu.addSeparator()
        
        reset_layout_action = QAction("Сбросить layout", self)
        reset_layout_action.triggered.connect(self._reset_layout)
        view_menu.addAction(reset_layout_action)
        
        # Помощь
        help_menu = menubar.addMenu("Помощь")
        
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("📖 Документация", self)
        docs_action.triggered.connect(self._show_docs)
        help_menu.addAction(docs_action)
        
    def _setup_toolbar(self):
        """Настройка тулбара"""
        toolbar = QToolBar("Основные действия")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        toolbar.addAction("📁", self._new_project)
        toolbar.addAction("💾", self._save_project)
        toolbar.addAction("↩", self._undo)
        toolbar.addAction("↪", self._redo)
        toolbar.addSeparator()
        toolbar.addAction("➕", self._add_node)
        toolbar.addAction("🗑", self._delete_node)
        toolbar.addSeparator()
        toolbar.addAction("🔄", self._recalculate)
        toolbar.addAction("🔍", self._search_project)
        toolbar.addSeparator()
        toolbar.addAction("🌓", self._toggle_dark_theme)
        toolbar.addAction("❓", self._show_about)
        
    def _setup_statusbar(self):
        """Настройка статус-бара"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Индикатор состояния
        self.status_indicator = QLabel("🟢")
        self.status_bar.addWidget(self.status_indicator)
        
        # Информация о выбранном узле
        self.selection_label = QLabel("Ничего не выбрано")
        self.status_bar.addWidget(self.selection_label)
        
        # Количество связей
        self.connections_label = QLabel("Связей: 0")
        self.status_bar.addWidget(self.connections_label)
        
        # Вес узла
        self.weight_label = QLabel("Вес: -")
        self.status_bar.addWidget(self.weight_label)
        
        self.status_bar.addPermanentWidget(QLabel("💾 Сохранено"))
        
    def _refresh_all(self):
        """Обновить все компоненты"""
        self.tree_a.load_graph(self.graph, self.calculator)
        self.tree_b.load_graph(self.graph, self.calculator)
        self._update_tree_lists()
        
        if self.right_panel.current_node_id:
            self.right_panel.load_node(self.right_panel.current_node_id)
            
        self._update_statusbar()
        
    def _update_tree_lists(self):
        """Обновить список деревьев в левой панели"""
        # Реализация зависит от логики управления списками
        pass
        
    def _on_node_selected(self, node_id: str):
        """Обработка выбора узла"""
        # Обновление подсветки в обоих деревьях
        self._update_highlights(node_id)
        
        # Загрузка в инспектор
        self.right_panel.load_node(node_id)
        
        # Обновление статус-бара
        self._update_statusbar()
        
        # Активация кнопки добавления связи
        if self.tree_a.selected_node_id and self.tree_b.selected_node_id:
            self.right_panel.add_connection_btn.setEnabled(True)
        else:
            self.right_panel.add_connection_btn.setEnabled(False)
            
    def _update_highlights(self, selected_node_id: str):
        """Обновить подсветку связанных узлов"""
        if not self.graph:
            return
            
        # Определяем типы связей для каждого узла
        highlights_a = {}
        highlights_b = {}
        
        # Для Дерева А
        if selected_node_id:
            # Исходящие связи
            for child_id in self.graph.get_children(selected_node_id):
                highlights_a[child_id] = "outgoing"
                
            # Входящие связи
            parent_id = self.graph.get_parent(selected_node_id)
            if parent_id:
                highlights_a[parent_id] = "incoming"
                
            # Ассоциации
            for connected_id, edge in self.graph.get_associations(selected_node_id):
                if edge.source_id == selected_node_id:
                    highlights_a[connected_id] = "outgoing"
                else:
                    highlights_a[connected_id] = "incoming"
                    
        self.tree_a.set_highlighted_nodes(highlights_a)
        self.tree_b.set_highlighted_nodes(highlights_b)
        
    def _update_statusbar(self):
        """Обновить статус-бар"""
        node_id = self.right_panel.current_node_id
        if node_id and self.graph:
            node = self.graph.get_node(node_id)
            if node:
                self.selection_label.setText(f"Выбран: {node.name}")
                
                # Подсчёт связей
                conn_count = len(self.graph.get_children(node_id))
                if self.graph.get_parent(node_id):
                    conn_count += 1
                conn_count += len(self.graph.get_associations(node_id))
                self.connections_label.setText(f"Связей: {conn_count}")
                
                # Вес
                weight = node.user_weight_override if node.user_weight_override is not None else "-"
                if weight != "-":
                    self.weight_label.setText(f"Вес: {weight:.4f}")
                else:
                    self.weight_label.setText("Вес: -")
            else:
                self.selection_label.setText("Ничего не выбрано")
        else:
            self.selection_label.setText("Ничего не выбрано")
            
    def _on_list_selected(self, list_name: str):
        """Выбор списка деревьев"""
        # Загрузка выбранного списка в оба дерева
        pass
        
    def _on_node_changed(self, node_id: str):
        """Изменение узла"""
        self._set_unsaved_changes(True)
        self._refresh_all()
        
    def _recalculate(self):
        """Пересчитать граф"""
        self.calculator.calculate()
        self._refresh_all()
        self._set_unsaved_changes(True)
        
    def _set_unsaved_changes(self, has_changes: bool):
        """Установить индикатор несохранённых изменений"""
        if has_changes:
            self.status_indicator.setText("🟡")
        else:
            self.status_indicator.setText("🟢")
            
    # Действия меню
    def _new_project(self):
        """Новый проект"""
        reply = QMessageBox.question(self, "Новый проект",
                                     "Очистить все данные и создать пустой проект?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.graph = InterestGraph()
            self.calculator = GraphCalculator(self.graph)
            self._create_root_nodes()
            self._refresh_all()
            self._set_unsaved_changes(False)
            
    def _load_project(self):
        """Загрузить проект"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Загрузить проект", "", "JSON files (*.json);;All files (*)"
        )
        if filename:
            try:
                self.graph = InterestGraph.load_from_file(filename)
                self.calculator = GraphCalculator(self.graph)
                self._refresh_all()
                self._set_unsaved_changes(False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")
                
    def _save_project(self):
        """Сохранить проект"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить проект", "", "JSON files (*.json)"
        )
        if filename:
            try:
                self.graph.save_to_file(filename)
                self._set_unsaved_changes(False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")
                
    def _undo(self):
        """Отменить"""
        QMessageBox.information(self, "Инфо", "Функция отмены в разработке")
        
    def _redo(self):
        """Повторить"""
        QMessageBox.information(self, "Инфо", "Функция повтора в разработке")
        
    def _apply_all(self):
        """Применить все изменения"""
        self._refresh_all()
        
    def _reset_calculation(self):
        """Сброс перерасчёта"""
        for node in self.graph.nodes.values():
            if not node.user_att:
                node.att = 0
            if not node.user_int:
                node.int = 50
        self._refresh_all()
        
    def _toggle_templates(self):
        """Показать/скрыть окно шаблонов"""
        if self.templates_window.isVisible():
            self.templates_window.hide()
        else:
            self.templates_window.show()
            
    def _toggle_dark_theme(self):
        """Переключить тему"""
        app = QApplication.instance()
        current_style = app.styleSheet()
        if "dark" in current_style.lower():
            app.setStyleSheet("")
        else:
            app.setStyleSheet("""
                QMainWindow, QDialog { background-color: #2b2b2b; color: #ffffff; }
                QTreeWidget, QListWidget, QTableWidget { 
                    background-color: #3c3c3c; color: #ffffff; 
                    alternate-background-color: #4a4a4a;
                }
                QGroupBox { border: 1px solid #555555; }
            """)
            
    def _reset_layout(self):
        """Сбросить layout"""
        self.resize(1400, 900)
        self.move(100, 100)
        self.restoreDocks()
        
    def _show_about(self):
        """О программе"""
        QMessageBox.about(self, "О программе", """
            Graph Overlord v2.0
            
            Система управления графом увлечений пользователя.
            
            Особенности:
            • Две оси оценки: Отношение (Att) и Интерес (Int)
            • Итеративное распространение оценок
            • Поддержка шаблонов графов
            • Выявление неопределённостей
            • PyQt5 интерфейс
        """)
        
    def _show_docs(self):
        """Документация"""
        QMessageBox.information(self, "Документация", 
                                "Документация находится в разработке.")
                                
    def _add_node(self):
        """Добавить узел"""
        nodes = [(nid, n.name) for nid, n in self.graph.nodes.items() if n.active]
        dialog = CreateNodeDialog(self, nodes)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data["name"]:
                import uuid
                node_id = f"node_{uuid.uuid4().hex[:8]}"
                self.graph.add_node(
                    node_id,
                    data["name"],
                    user_att=data["att"],
                    user_int=data["int"],
                    active=data["active"],
                    locked=data["locked"],
                )
                
                if data["parent_id"]:
                    edge = Edge.create_parent_edge(data["parent_id"], node_id)
                    self.graph.add_edge(edge)
                    
                self._refresh_all()
                self._set_unsaved_changes(True)
                
    def _delete_node(self):
        """Удалить узел"""
        node_id = self.right_panel.current_node_id
        if node_id:
            reply = QMessageBox.question(self, "Подтверждение",
                                         "Удалить выбранный узел и всё поддерево?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.graph.remove_node(node_id)
                self._refresh_all()
                self._set_unsaved_changes(True)
                
    def _search_project(self):
        """Поиск по проекту"""
        text, ok = QInputDialog.getText(self, "Поиск", "Введите текст для поиска:")
        if ok and text:
            # Реализация поиска
            pass
            
    def _apply_template(self, template_name: str):
        """Применить шаблон"""
        try:
            # Применяем к корневому узлу или выбранному
            parent_id = None
            roots = self.graph.get_root_nodes()
            if roots:
                parent_id = roots[0]
                
            self.template_manager.apply_template(template_name, self.graph, parent_id)
            self._refresh_all()
            self._set_unsaved_changes(True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            
    def _restore_settings(self):
        """Восстановить настройки"""
        settings = QSettings("GraphOverlord", "MainWindow")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("state")
        if state:
            self.restoreState(state)
            
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        settings = QSettings("GraphOverlord", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        event.accept()


def main():
    """Точка входа приложения"""
    app = QApplication(sys.argv)
    app.setApplicationName("Graph Overlord")
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
