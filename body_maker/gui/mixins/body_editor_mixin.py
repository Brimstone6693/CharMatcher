# file: gui/mixins/body_editor_mixin.py
"""Mixin for body editor integration functionality."""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from core.module_loader import load_available_modules_and_bodies, BODIES_DATA_DIR


class BodyEditorMixin:
    """Provides body editor integration for MainWindow."""
    
    def show_manage_bodies_screen(self):
        """Shows the body types management screen."""
        from core.body_types.core import BodyTypeManager
        if not hasattr(self, 'body_manager'):
            self.body_manager = BodyTypeManager(self)
        
        self.body_manager.create_manage_bodies_screen()

    def init_body_structure_with_root(self):
        """Initializes body structure with mandatory root part 'Body'."""
        self.current_body_structure = {None: ["Body"], "Body": []}
        self.update_body_parts_tree()

    def refresh_bodies_list(self):
        """Updates the list of displayed body types in ListBox."""
        self.bodies_listbox.delete(0, tk.END)
        for body_name in sorted(self.available_bodies.keys()):
            self.bodies_listbox.insert(tk.END, body_name)

    def get_final_gender(self):
        """Returns final gender value considering custom field."""
        from utils.gender_utils import get_final_gender_value
        base_gender = self.new_body_gender_var.get()
        custom_gender = self.new_body_gender_custom_entry.get().strip()
        return get_final_gender_value(base_gender, custom_gender)

    def update_auto_size(self, event=None):
        """Automatically determines size category based on height range."""
        from utils.size_calculator import calculate_size_category
        
        try:
            min_height_str = self.new_body_height_min_entry.get().strip()
            max_height_str = self.new_body_height_max_entry.get().strip()
            
            if not min_height_str or not max_height_str:
                self.auto_size_label.config(text="Enter values")
                return
                
            min_height = float(min_height_str)
            max_height = float(max_height_str)
            
            if min_height < 0 or max_height < 0:
                self.auto_size_label.config(text="No negatives")
                return
            
            if min_height > max_height:
                self.auto_size_label.config(text="Min > Max error")
                return
            
            avg_height = (min_height + max_height) / 2
            height_type = self.height_type_var.get()
            
            size_category = calculate_size_category(avg_height, height_type)
            self.auto_size_label.config(text=size_category)
        except ValueError:
            self.auto_size_label.config(text="Invalid input")

    def update_body_parts_tree(self):
        """Updates body parts tree based on current_body_structure with expanded state preservation."""
        from core.body_types.tree_operations import update_tree_from_structure
        update_tree_from_structure(
            self.body_parts_tree, 
            self.current_body_structure
        )

    def on_add_root_part(self):
        """Adds a root body part (to key None)."""
        from core.body_types.tree_editing import add_root_part_dialog
        add_root_part_dialog(self, self.current_body_structure, self.update_body_parts_tree)

    def on_add_child_part(self):
        """Adds a child part to selected nodes (supports multiple selection)."""
        from core.body_types.tree_editing import add_child_part_dialog
        add_child_part_dialog(self, self.body_parts_tree, self.current_body_structure, self.update_body_parts_tree)

    def on_delete_part(self):
        """Deletes selected part and all its descendants."""
        from core.body_types.tree_editing import delete_part_dialog
        delete_part_dialog(self, self.body_parts_tree, self.current_body_structure, self.update_body_parts_tree)

    def on_rename_part(self):
        """Renames selected part."""
        from core.body_types.tree_editing import rename_part_dialog
        rename_part_dialog(self, self.body_parts_tree, self.current_body_structure, 
                          self.get_all_part_names_from_structure, self.update_body_parts_tree)

    def get_all_part_names_from_structure(self):
        """Returns all part names from current structure."""
        names = []
        for children in self.current_body_structure.values():
            for child in children:
                names.append(child["name"] if isinstance(child, dict) else child)
        return names

    def on_create_body_type_clicked(self):
        """Handler for creating new body type through interface."""
        from core.body_types.body_crud import create_new_body_type
        create_new_body_type(
            main_window=self,
            class_name_entry=self.new_body_class_name_entry,
            display_name_entry=self.new_body_display_name_entry,
            gender_var=self.new_body_gender_var,
            gender_custom_entry=self.new_body_gender_custom_entry,
            desc_template_entry=self.new_body_desc_template_entry,
            height_min_entry=self.new_body_height_min_entry,
            height_max_entry=self.new_body_height_max_entry,
            auto_size_label=self.auto_size_label,
            current_body_structure=self.current_body_structure,
            available_bodies=self.available_bodies,
            refresh_callback=self.refresh_bodies_list,
            update_auto_size_callback=self.update_auto_size,
            update_tree_callback=self.update_body_parts_tree,
            get_final_gender_callback=self.get_final_gender
        )

    def on_body_list_right_click(self, event):
        """Handler for right-click on body types list."""
        index = self.bodies_listbox.nearest(event.y)
        self.bodies_listbox.selection_clear(0, tk.END)
        self.bodies_listbox.selection_set(index)
        self.bodies_listbox.activate(index)
        
        try:
            self.body_list_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.body_list_menu.grab_release()

    def on_load_body_to_editor(self):
        """Loads selected body type into editor for viewing/editing."""
        from core.body_types.body_crud import load_body_to_editor
        load_body_to_editor(
            bodies_listbox=self.bodies_listbox,
            class_name_entry=self.new_body_class_name_entry,
            display_name_entry=self.new_body_display_name_entry,
            height_min_entry=self.new_body_height_min_entry,
            height_max_entry=self.new_body_height_max_entry,
            gender_var=self.new_body_gender_var,
            gender_custom_entry=self.new_body_gender_custom_entry,
            desc_template_entry=self.new_body_desc_template_entry,
            current_body_structure=self.current_body_structure,
            update_auto_size_callback=self.update_auto_size,
            update_tree_callback=self.update_body_parts_tree
        )

    def on_rename_body_type(self):
        """Renames selected body type (creates copy with new name and deletes old)."""
        from core.body_types.body_crud import rename_body_type_dialog
        rename_body_type_dialog(
            main_window=self,
            bodies_listbox=self.bodies_listbox,
            available_bodies=self.available_bodies,
            refresh_callback=self.refresh_bodies_list
        )

    def on_copy_body_type(self):
        """Copies selected body type with new name."""
        from core.body_types.body_crud import copy_body_type_dialog
        copy_body_type_dialog(
            main_window=self,
            bodies_listbox=self.bodies_listbox,
            available_bodies=self.available_bodies,
            refresh_callback=self.refresh_bodies_list
        )

    def on_delete_body_type(self):
        """Deletes selected body type."""
        from core.body_types.body_crud import delete_body_type_dialog
        delete_body_type_dialog(
            main_window=self,
            bodies_listbox=self.bodies_listbox,
            refresh_callback=self.refresh_bodies_list
        )
