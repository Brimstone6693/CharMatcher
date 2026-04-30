"""
Graph Overlord - Графический интерфейс
Управление графом увлечений пользователя с двумя осями оценки (Att/Int)
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import json
import os
import sys
from typing import Optional, Dict, Any
from dataclasses import asdict

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Graph_Overlord.graph import InterestGraph
from Graph_Overlord.interest_node import InterestNode
from Graph_Overlord.calculator import GraphCalculator
from Graph_Overlord.templates import TemplateManager


class NodeTreeview(ttk.Treeview):
    """Древовидное представление графа с цветовой индикацией"""
    
    def __init__(self, parent, graph: InterestGraph, calculator: GraphCalculator, **kwargs):
        super().__init__(parent, **kwargs)
        self.graph = graph
        self.calculator = calculator
        self.selected_node_id = None
        
        # Настройка колонок
        self["columns"] = ("name", "att", "int", "status")
        self.column("#0", width=250, minwidth=150)
        self.column("name", width=150)
        self.column("att", width=60, anchor="center")
        self.column("int", width=60, anchor="center")
        self.column("status", width=80, anchor="center")
        
        self.heading("#0", text="Узел")
        self.heading("name", text="Название")
        self.heading("att", text="Att")
        self.heading("int", text="Int")
        self.heading("status", text="Статус")
        
        # Теги для цветовой индикации
        self.tag_configure("high_att", background="#d4edda")  # зелёный
        self.tag_configure("low_att", background="#f8d7da")   # красный
        self.tag_configure("high_int", foreground="#0056b3")  # синий текст
        self.tag_configure("uncertain", background="#fff3cd") # жёлтый
        self.tag_configure("inactive", foreground="#999999")  # серый
        self.tag_configure("locked", foreground="#6f42c1")    # фиолетовый
        
        # Привязка события выбора
        self.bind("<<TreeviewSelect>>", self.on_select)
        
    def refresh(self):
        """Обновить отображение дерева"""
        self.delete(*self.get_children())
        
        # Запускаем пересчёт если нужно
        self.calculator.calculate()
        
        # Получаем корневые узлы
        root_nodes = [n for n in self.graph.nodes.values() 
                      if n.active and self.graph.get_parent(n.id) is None]
        
        for node in root_nodes:
            self._add_node_recursive(node)
            
    def _add_node_recursive(self, node: InterestNode, parent_iid=""):
        """Рекурсивно добавить узел и его детей"""
        if not node.active:
            return
            
        # Определяем теги
        tags = []
        
        # Статус активности
        if not node.active:
            tags.append("inactive")
        elif node.locked:
            tags.append("locked")
            
        # Цвет по Att
        if node.att > 30:
            tags.append("high_att")
        elif node.att < -30:
            tags.append("low_att")
            
        # Неопределённость
        uncertainty = self.calculator.get_uncertainty(node.id)
        if uncertainty and (uncertainty.get("conflict_score", 0) > 20 or 
                           uncertainty.get("weak_signal", False)):
            tags.append("uncertain")
            
        # Формируем отображаемые значения
        att_display = f"{node.att:.0f}" if node.att is not None else "-"
        int_display = f"{node.int:.0f}" if node.int is not None else "-"
        
        status_parts = []
        if node.locked:
            status_parts.append("🔒")
        if node.user_att is not None or node.user_int is not None:
            status_parts.append("✏️")
        if uncertainty and uncertainty.get("needs_review", False):
            status_parts.append("⚠️")
        status_str = " ".join(status_parts) if status_parts else ""
        
        iid = self.insert(parent_iid, "end", 
                         text=f"{node.name} ({node.id})",
                         values=(node.name, att_display, int_display, status_str),
                         tags=tags)
        
        # Добавляем детей
        children = self.graph.get_children(node.id)
        for child in children:
            if child.active:
                self._add_node_recursive(child, iid)
                
    def on_select(self, event):
        """Обработка выбора узла"""
        selection = self.selection()
        if selection:
            item = self.item(selection[0])
            text = item["text"]
            # Извлекаем ID из текста формата "name (id)"
            if " (" in text and text.endswith(")"):
                node_id = text.split(" (")[-1][:-1]
                self.selected_node_id = node_id
                # Генерируем событие для обновления панели редактирования
                self.event_generate("<<NodeSelected>>")


class NodeEditorFrame(ttk.LabelFrame):
    """Панель редактирования выбранного узла"""
    
    def __init__(self, parent, graph: InterestGraph, calculator: GraphCalculator, **kwargs):
        super().__init__(parent, text="Редактирование узла", **kwargs)
        self.graph = graph
        self.calculator = calculator
        self.current_node_id = None
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Создать элементы управления"""
        # Название
        ttk.Label(self, text="Название:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # Категория
        self.is_category_var = tk.BooleanVar()
        self.category_check = ttk.Checkbutton(self, text="Категория", 
                                              variable=self.is_category_var)
        self.category_check.grid(row=0, column=2, padx=10, pady=2)
        
        # Отношение (Att)
        ttk.Label(self, text="Отношение (Att):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.att_var = tk.DoubleVar()
        self.att_scale = ttk.Scale(self, from_=-100, to=100, variable=self.att_var, 
                                   orient="horizontal", length=200)
        self.att_scale.grid(row=1, column=1, padx=5, pady=2)
        self.att_label = ttk.Label(self, text="0", width=5)
        self.att_label.grid(row=1, column=2, padx=5, pady=2)
        self.att_scale.configure(command=lambda v: self.att_label.config(text=f"{float(v):.0f}"))
        
        # Пользовательское Att
        ttk.Label(self, text="Польз. Att:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.user_att_var = tk.DoubleVar()
        self.user_att_spin = ttk.Spinbox(self, from_=-100, to=100, textvariable=self.user_att_var, 
                                         width=10, command=self._on_user_value_change)
        self.user_att_spin.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(self, text="Очистить", command=self._clear_user_att).grid(row=2, column=2, padx=5, pady=2)
        
        # Интерес (Int)
        ttk.Label(self, text="Интерес (Int):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.int_var = tk.DoubleVar()
        self.int_scale = ttk.Scale(self, from_=0, to=100, variable=self.int_var, 
                                   orient="horizontal", length=200)
        self.int_scale.grid(row=3, column=1, padx=5, pady=2)
        self.int_label = ttk.Label(self, text="0", width=5)
        self.int_label.grid(row=3, column=2, padx=5, pady=2)
        self.int_scale.configure(command=lambda v: self.int_label.config(text=f"{float(v):.0f}"))
        
        # Пользовательское Int
        ttk.Label(self, text="Польз. Int:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.user_int_var = tk.DoubleVar()
        self.user_int_spin = ttk.Spinbox(self, from_=0, to=100, textvariable=self.user_int_var, 
                                         width=10, command=self._on_user_value_change)
        self.user_int_spin.grid(row=4, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(self, text="Очистить", command=self._clear_user_int).grid(row=4, column=2, padx=5, pady=2)
        
        # Вес пользовательской оценки
        ttk.Label(self, text="Вес польз. оценки:").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        self.user_weight_var = tk.DoubleVar()
        self.user_weight_spin = ttk.Spinbox(self, from_=0, to=1, increment=0.1, 
                                            textvariable=self.user_weight_var, width=10)
        self.user_weight_spin.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(self, text="(0-1, пустое = авто)").grid(row=5, column=2, sticky="w", padx=5, pady=2)
        
        # Блокировка и активность
        self.locked_var = tk.BooleanVar()
        self.locked_check = ttk.Checkbutton(self, text="🔒 Заблокирован (не пересчитывается)", 
                                            variable=self.locked_var, command=self._on_toggle_locked)
        self.locked_check.grid(row=6, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        self.active_var = tk.BooleanVar()
        self.active_check = ttk.Checkbutton(self, text="✅ Активен (включая поддерево)", 
                                            variable=self.active_var, command=self._on_toggle_active)
        self.active_check.grid(row=7, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        # Кнопки действий
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="💾 Применить", command=self._apply_changes).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Пересчитать", command=self._recalculate).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Удалить узел", command=self._delete_node).pack(side="left", padx=5)
        
        # Информация о неопределённости
        self.uncertainty_label = ttk.Label(self, text="", foreground="orange")
        self.uncertainty_label.grid(row=9, column=0, columnspan=3, pady=5)
        
    def load_node(self, node_id: str):
        """Загрузить данные узла в форму"""
        node = self.graph.get_node(node_id)
        if not node:
            return
            
        self.current_node_id = node_id
        
        # Основные поля
        self.name_var.set(node.name)
        self.is_category_var.set(node.is_category)
        self.att_var.set(node.att if node.att is not None else 0)
        self.int_var.set(node.int if node.int is not None else 0)
        self.att_label.config(text=f"{node.att:.0f}" if node.att is not None else "0")
        self.int_label.config(text=f"{node.int:.0f}" if node.int is not None else "0")
        
        # Пользовательские значения
        self.user_att_var.set(node.user_att if node.user_att is not None else 0)
        self.user_int_var.set(node.user_int if node.user_int is not None else 0)
        self.user_weight_var.set(node.user_weight_override if node.user_weight_override is not None else "")
        
        # Флаги
        self.locked_var.set(node.locked)
        self.active_var.set(node.active)
        
        # Обновляем состояние элементов
        self._update_widget_states()
        
        # Информация о неопределённости
        uncertainty = self.calculator.get_uncertainty(node_id)
        if uncertainty:
            parts = []
            if uncertainty.get("conflict_score", 0) > 20:
                parts.append(f"Конфликт: {uncertainty['conflict_score']:.1f}")
            if uncertainty.get("weak_signal", False):
                parts.append("Слабый сигнал")
            if uncertainty.get("needs_review", False):
                parts.append("⚠️ Требует уточнения")
            self.uncertainty_label.config(text=" | ".join(parts) if parts else "")
        else:
            self.uncertainty_label.config(text="")
            
    def _update_widget_states(self):
        """Обновить состояние элементов управления"""
        if self.locked_var.get():
            self.att_scale.state(['disabled'])
            self.int_scale.state(['disabled'])
        else:
            self.att_scale.state(['!disabled'])
            self.int_scale.state(['!disabled'])
            
    def _on_user_value_change(self):
        """Изменение пользовательского значения"""
        pass  # Вес пересчитается при применении
        
    def _clear_user_att(self):
        """Очистить пользовательское Att"""
        self.user_att_var.set(0)
        
    def _clear_user_int(self):
        """Очистить пользовательское Int"""
        self.user_int_var.set(0)
        
    def _on_toggle_locked(self):
        """Переключение блокировки"""
        self._update_widget_states()
        
    def _on_toggle_active(self):
        """Переключение активности"""
        if not self.active_var.get():
            if not messagebox.askyesno("Подтверждение", 
                "Отключение узла исключит его и всё поддерево из расчётов.\nПродолжить?"):
                self.active_var.set(True)
                return
                
    def _apply_changes(self):
        """Применить изменения к узлу"""
        if not self.current_node_id:
            return
            
        node = self.graph.get_node(self.current_node_id)
        if not node:
            return
            
        # Обновляем поля
        node.name = self.name_var.get()
        node.is_category = self.is_category_var.get()
        
        # Пользовательские значения
        user_att = self.user_att_var.get()
        user_int = self.user_int_var.get()
        
        # Проверяем, были ли установлены значения пользователем
        if abs(user_att) > 0.01 or messagebox.askyesno("Att", "Установить Att=0?"):
            node.user_att = user_att
        else:
            node.user_att = None
            
        if user_int > 0.01 or messagebox.askyesno("Int", "Установить Int=0?"):
            node.user_int = user_int
        else:
            node.user_int = None
            
        # Вес
        weight = self.user_weight_var.get()
        node.user_weight_override = weight if weight > 0 else None
        
        # Флаги
        old_active = node.active
        node.locked = self.locked_var.get()
        node.active = self.active_var.get()
        
        # Если изменилась активность, обновляем детей
        if old_active and not node.active:
            self.graph._set_subtree_active(node.id, False, force=False)
        elif not old_active and node.active:
            self.graph._set_subtree_active(node.id, True, force=False)
            
        messagebox.showinfo("Успех", f"Узел '{node.name}' обновлён")
        
    def _recalculate(self):
        """Пересчитать граф"""
        self.calculator.calculate()
        self.event_generate("<<RecalculateRequested>>")
        
    def _delete_node(self):
        """Удалить узел"""
        if not self.current_node_id:
            return
            
        if not messagebox.askyesno("Подтверждение удаления",
            f"Удалить узел '{self.current_node_id}' и все связи?\nЭто действие необратимо!"):
            return
            
        self.graph.remove_node(self.current_node_id)
        self.current_node_id = None
        self.event_generate("<<NodeDeleted>>")


class EdgeEditorFrame(ttk.LabelFrame):
    """Панель создания и редактирования связей"""
    
    def __init__(self, parent, graph: InterestGraph, **kwargs):
        super().__init__(parent, text="Связи", **kwargs)
        self.graph = graph
        self.current_edge = None
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Создать элементы управления"""
        # Выбор типа связи
        ttk.Label(self, text="Тип связи:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.edge_type_var = tk.StringVar(value="parent")
        ttk.Radiobutton(self, text="Иерархия (Parent)", variable=self.edge_type_var, 
                       value="parent", command=self._on_type_change).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(self, text="Ассоциация", variable=self.edge_type_var, 
                       value="association", command=self._on_type_change).grid(row=0, column=2, sticky="w")
        
        # Узлы
        ttk.Label(self, text="Источник:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(self, textvariable=self.source_var, width=25, state="readonly")
        self.source_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=2)
        
        ttk.Label(self, text="Цель:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(self, textvariable=self.target_var, width=25, state="readonly")
        self.target_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=2)
        
        # Контейнер для весов
        self.weights_frame = ttk.Frame(self)
        self.weights_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self._create_weight_widgets()
        
        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=5)
        
        ttk.Button(btn_frame, text="➕ Создать связь", command=self._create_edge).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 Обновить связь", command=self._update_edge).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Удалить связь", command=self._delete_edge).pack(side="left", padx=5)
        
        # Список существующих связей
        ttk.Label(self, text="Существующие связи:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.edges_listbox = tk.Listbox(self, height=6, width=50)
        self.edges_listbox.grid(row=6, column=0, columnspan=3, padx=5, pady=5)
        self.edges_listbox.bind("<<ListboxSelect>>", self._on_edge_select)
        
        # Обновляем списки узлов
        self._refresh_node_lists()
        
    def _create_weight_widgets(self):
        """Создать виджеты для весов"""
        # Очищаем предыдущие
        for widget in self.weights_frame.winfo_children():
            widget.destroy()
            
        edge_type = self.edge_type_var.get()
        
        if edge_type == "parent":
            # Веса для иерархии
            weights = [
                ("↓ Att (родитель→ребёнок)", "w_down_att", [-0.9, -0.7, -0.4, 0.0, 0.4, 0.7, 0.9]),
                ("↓ Int (родитель→ребёнок)", "w_down_int", [0.0, 0.1, 0.3, 0.6, 0.8, 1.0]),
                ("↑ Att (ребёнок→родитель)", "w_up_att", [-0.9, -0.7, -0.4, 0.0, 0.4, 0.7, 0.9]),
                ("↑ Int (ребёнок→родитель)", "w_up_int", [0.0, 0.1, 0.3, 0.6, 0.8, 1.0]),
            ]
        else:
            # Веса для ассоциации
            weights = [
                ("→ Att (прямое)", "fw_att", [-0.9, -0.7, -0.4, 0.0, 0.4, 0.7, 0.9]),
                ("→ Int (прямое)", "fw_int", [0.0, 0.1, 0.3, 0.6, 0.8, 1.0]),
                ("← Att (обратное)", "bw_att", [-0.9, -0.7, -0.4, 0.0, 0.4, 0.7, 0.9]),
                ("← Int (обратное)", "bw_int", [0.0, 0.1, 0.3, 0.6, 0.8, 1.0]),
            ]
            
        self.weight_vars = {}
        
        for i, (label, attr, values) in enumerate(weights):
            row = i // 2
            col = (i % 2) * 3
            
            ttk.Label(self.weights_frame, text=label + ":").grid(row=row, column=col, sticky="w", padx=5, pady=2)
            
            var = tk.DoubleVar(value=0.7 if "att" in attr and "down" in attr or "fw" in attr else 0.6)
            self.weight_vars[attr] = var
            
            combo = ttk.Combobox(self.weights_frame, textvariable=var, width=8, state="readonly")
            combo["values"] = [f"{v:.1f}" for v in values]
            combo.set(f"{var.get():.1f}")
            combo.grid(row=row, column=col+1, padx=5, pady=2)
            
    def _on_type_change(self):
        """Изменение типа связи"""
        self._create_weight_widgets()
        
    def _refresh_node_lists(self):
        """Обновить списки узлов"""
        nodes = [(n.id, n.name) for n in self.graph.nodes.values() if n.active]
        nodes_sorted = sorted(nodes, key=lambda x: x[1])
        
        self.source_combo["values"] = [f"{nid} - {name}" for nid, name in nodes_sorted]
        self.target_combo["values"] = [f"{nid} - {name}" for nid, name in nodes_sorted]
        
        # Обновляем список связей
        self.edges_listbox.delete(0, tk.END)
        for edge in self.graph.edges:
            src_name = self.graph.get_node(edge.source_id).name if self.graph.get_node(edge.source_id) else edge.source_id
            tgt_name = self.graph.get_node(edge.target_id).name if self.graph.get_node(edge.target_id) else edge.target_id
            edge_type_symbol = "→" if edge.type == "parent" else "↔"
            self.edges_listbox.insert(tk.END, f"{src_name} {edge_type_symbol} {tgt_name} ({edge.type})")
            
    def _parse_node_selection(self, selection: str) -> Optional[str]:
        """Извлечь ID узла из строки выбора"""
        if " - " in selection:
            return selection.split(" - ")[0]
        return None
        
    def _create_edge(self):
        """Создать новую связь"""
        source_str = self.source_var.get()
        target_str = self.target_var.get()
        
        source_id = self._parse_node_selection(source_str)
        target_id = self._parse_node_selection(target_str)
        
        if not source_id or not target_id:
            messagebox.showerror("Ошибка", "Выберите оба узла")
            return
            
        if source_id == target_id:
            messagebox.showerror("Ошибка", "Узел не может быть связан сам с собой")
            return
            
        edge_type = self.edge_type_var.get()
        
        # Проверка для иерархии
        if edge_type == "parent":
            existing_parent = self.graph.get_parent(target_id)
            if existing_parent:
                messagebox.showerror("Ошибка", "У узла уже есть родитель")
                return
                
        # Собираем веса
        weights = {attr: float(var.get()) for attr, var in self.weight_vars.items()}
        
        # Создаём связь
        try:
            self.graph.add_edge(source_id, target_id, edge_type, **weights)
            self._refresh_node_lists()
            messagebox.showinfo("Успех", "Связь создана")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            
    def _update_edge(self):
        """Обновить существующую связь"""
        # Аналогично созданию, но для существующей
        messagebox.showinfo("Инфо", "Функция обновления в разработке")
        
    def _delete_edge(self):
        """Удалить связь"""
        selection = self.edges_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите связь для удаления")
            return
            
        index = selection[0]
        edge = self.graph.edges[index]
        
        if messagebox.askyesno("Подтверждение", "Удалить эту связь?"):
            self.graph.remove_edge(edge.source_id, edge.target_id)
            self._refresh_node_lists()
            
    def _on_edge_select(self, event):
        """Выбор связи из списка"""
        selection = self.edges_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.graph.edges):
                self.current_edge = self.graph.edges[index]
                # Загрузить веса в форму (упрощённо)
                pass


class TemplateFrame(ttk.LabelFrame):
    """Панель работы с шаблонами"""
    
    def __init__(self, parent, graph: InterestGraph, template_manager: TemplateManager, **kwargs):
        super().__init__(parent, text="Шаблоны", **kwargs)
        self.graph = graph
        self.template_manager = template_manager
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Создать элементы управления"""
        # Список доступных шаблонов
        ttk.Label(self, text="Доступные шаблоны:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.template_listbox = tk.Listbox(self, height=5, width=40)
        self.template_listbox.grid(row=1, column=0, padx=5, pady=5)
        
        # Заполняем список
        available_templates = self.template_manager.list_templates()
        for tpl_name in available_templates:
            self.template_listbox.insert(tk.END, tpl_name)
            
        # Выбор родительского узла
        ttk.Label(self, text="Прикрепить к узлу:").grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.parent_node_var = tk.StringVar()
        self.parent_node_combo = ttk.Combobox(self, textvariable=self.parent_node_var, width=25, state="readonly")
        self.parent_node_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Обновляем список узлов
        self._refresh_node_list()
        
        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="📥 Импорт шаблона", command=self._import_template).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📤 Экспорт текущего", command=self._export_current).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📁 Открыть файл", command=self._load_from_file).pack(side="left", padx=5)
        
    def _refresh_node_list(self):
        """Обновить список узлов для привязки"""
        nodes = [(n.id, n.name) for n in self.graph.nodes.values() if n.active]
        nodes_sorted = sorted(nodes, key=lambda x: x[1])
        self.parent_node_combo["values"] = [f"{nid} - {name}" for nid, name in nodes_sorted]
        
    def _import_template(self):
        """Импортировать шаблон"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите шаблон")
            return
            
        template_name = self.template_listbox.get(selection[0])
        parent_str = self.parent_node_var.get()
        
        if not parent_str:
            messagebox.showwarning("Предупреждение", "Выберите родительский узел")
            return
            
        # Извлекаем ID
        parent_id = parent_str.split(" - ")[0] if " - " in parent_str else parent_str
        
        try:
            self.template_manager.apply_template(template_name, self.graph, parent_id)
            messagebox.showinfo("Успех", f"Шаблон '{template_name}' импортирован")
            # Генерируем событие обновления
            self.event_generate("<<TemplateImported>>")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            
    def _export_current(self):
        """Экспортировать текущий граф как шаблон"""
        template_name = "custom_export_" + os.urandom(4).hex()
        try:
            self.template_manager.export_template(self.graph, template_name)
            messagebox.showinfo("Успех", f"Шаблон сохранён как '{template_name}'")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            
    def _load_from_file(self):
        """Загрузить шаблон из файла"""
        filename = tk.filedialog.askopenfilename(
            title="Выберите файл шаблона",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.template_manager.load_template_file(filename)
                # Обновляем список
                self.template_listbox.delete(0, tk.END)
                for tpl_name in self.template_manager.list_templates():
                    self.template_listbox.insert(tk.END, tpl_name)
                messagebox.showinfo("Успех", "Шаблон загружен")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


class GraphOverlordGUI:
    """Основное приложение"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Overlord - Управление графом увлечений")
        self.root.geometry("1400x800")
        
        # Инициализация компонентов
        self.graph = InterestGraph()
        self.calculator = GraphCalculator(self.graph)
        self.template_manager = TemplateManager()
        
        # Создаём начальные корневые узлы
        self._create_root_nodes()
        
        # Создаём интерфейс
        self._create_ui()
        
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
            
    def _create_ui(self):
        """Создать пользовательский интерфейс"""
        # Главный контейнер с разделением
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - дерево
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Граф увлечений", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Дерево с прокруткой
        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = NodeTreeview(left_frame, self.graph, self.calculator,
                                yscrollcommand=tree_scroll.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        # Привязка события выбора узла
        self.tree.bind("<<NodeSelected>>", lambda e: self._on_node_selected())
        
        # Правая панель - редакторы
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        main_paned.add(right_paned, weight=2)
        
        # Редактор узлов
        self.node_editor = NodeEditorFrame(right_paned, self.graph, self.calculator)
        right_paned.add(self.node_editor, weight=1)
        
        # Привязка событий
        self.node_editor.bind("<<RecalculateRequested>>", lambda e: self._refresh_all())
        self.node_editor.bind("<<NodeDeleted>>", lambda e: self._refresh_all())
        
        # Редактор связей
        self.edge_editor = EdgeEditorFrame(right_paned, self.graph)
        right_paned.add(self.edge_editor, weight=1)
        
        # Шаблоны
        self.template_frame = TemplateFrame(right_paned, self.graph, self.template_manager)
        right_paned.add(self.template_frame, weight=1)
        
        # Привязка события импорта шаблона
        self.template_frame.bind("<<TemplateImported>>", lambda e: self._refresh_all())
        
        # Меню
        self._create_menu()
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _create_menu(self):
        """Создать меню приложения"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="💾 Сохранить граф", command=self._save_graph)
        file_menu.add_command(label="📂 Загрузить граф", command=self._load_graph)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Выход", command=self.root.quit)
        
        # Действия
        actions_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Действия", menu=actions_menu)
        actions_menu.add_command(label="🔄 Пересчитать всё", command=self._refresh_all)
        actions_menu.add_command(label="📊 Показать статистику", command=self._show_stats)
        
        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="ℹ️ О программе", command=self._show_about)
        
    def _on_node_selected(self):
        """Обработка выбора узла в дереве"""
        node_id = self.tree.selected_node_id
        if node_id:
            self.node_editor.load_node(node_id)
            
    def _refresh_all(self):
        """Обновить все компоненты"""
        self.tree.refresh()
        self.edge_editor._refresh_node_lists()
        self.template_frame._refresh_node_list()
        
        if self.tree.selected_node_id:
            self.node_editor.load_node(self.tree.selected_node_id)
            
        self.status_var.set(f"Пересчитано: {len([n for n in self.graph.nodes.values() if n.active])} активных узлов")
        
    def _save_graph(self):
        """Сохранить граф в файл"""
        filename = tk.filedialog.asksaveasfilename(
            title="Сохранить граф",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                data = self.graph.to_dict()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Успех", "Граф сохранён")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
                
    def _load_graph(self):
        """Загрузить граф из файла"""
        filename = tk.filedialog.askopenfilename(
            title="Загрузить граф",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.graph = InterestGraph.from_dict(data)
                self.calculator = GraphCalculator(self.graph)
                self._refresh_all()
                messagebox.showinfo("Успех", "Граф загружен")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
                
    def _show_stats(self):
        """Показать статистику графа"""
        active_count = len([n for n in self.graph.nodes.values() if n.active])
        locked_count = len([n for n in self.graph.nodes.values() if n.locked])
        edges_count = len(self.graph.edges)
        
        avg_att = sum(n.att for n in self.graph.nodes.values() if n.active and n.att) / max(active_count, 1)
        avg_int = sum(n.int for n in self.graph.nodes.values() if n.active and n.int) / max(active_count, 1)
        
        stats_text = f"""
Статистика графа:

Активных узлов: {active_count}
Заблокированных: {locked_count}
Всего связей: {edges_count}

Среднее Att: {avg_att:.1f}
Средний Int: {avg_int:.1f}

Высокий интерес (Int > 70): {len([n for n in self.graph.nodes.values() if n.int and n.int > 70])}
Отрицательное отношение (Att < -30): {len([n for n in self.graph.nodes.values() if n.att and n.att < -30])}
"""
        messagebox.showinfo("Статистика", stats_text)
        
    def _show_about(self):
        """Показать информацию о программе"""
        about_text = """
Graph Overlord v1.0

Система управления графом увлечений пользователя.

Особенности:
• Две оси оценки: Отношение (Att) и Интерес (Int)
• Итеративное распространение оценок
• Поддержка шаблонов графов
• Выявление неопределённостей

Разработано согласно техническому заданию.
"""
        messagebox.showinfo("О программе", about_text)


def main():
    """Точка входа приложения"""
    root = tk.Tk()
    
    # Настройка стиля
    style = ttk.Style()
    style.theme_use('clam')  # Более современный вид
    
    # Запуск приложения
    app = GraphOverlordGUI(root)
    
    root.mainloop()


if __name__ == "__main__":
    main()
