# file: gui/mixins/character_view_mixin.py
"""Mixin for character view screen functionality."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json


class CharacterViewMixin:
    """Provides character view and save functionality for MainWindow."""
    
    def show_character_view(self):
        """Shows the character view screen."""
        # Clear previous content
        for widget in self.winfo_children():
            widget.destroy()

        if not self.current_character:
            messagebox.showerror("View Error", "No character to display.")
            self.show_start_screen()
            return

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Name
        ttk.Label(frame, text=f"Name: {self.current_character.name}", font=("Arial", 12, "bold")).pack(anchor=tk.W)

        # Body
        ttk.Label(frame, text="Body:", font=("Arial", 10, "underline")).pack(anchor=tk.W)
        ttk.Label(frame, text=self.current_character.body.describe_appearance()).pack(anchor=tk.W, padx=(20, 0))

        # Components
        ttk.Label(frame, text="Components:", font=("Arial", 10, "underline")).pack(anchor=tk.W, pady=(10, 0))
        comp_details_frame = ttk.Frame(frame)
        comp_details_frame.pack(fill=tk.BOTH, expand=True, padx=(20, 0))

        for comp_type, comp_instance in self.current_character.components.items():
            comp_label = ttk.Label(comp_details_frame, text=f"- {comp_type.__name__}: {comp_instance.to_dict()}")
            comp_label.pack(anchor=tk.W)

        # Save button
        save_btn = ttk.Button(frame, text="Save Character", command=self.on_save_clicked)
        save_btn.pack(pady=10)

        # Back button
        back_btn = ttk.Button(frame, text="Back to Start", command=self.show_start_screen)
        back_btn.pack()

    def on_save_clicked(self):
        """Handler for save button."""
        if not self.current_character:
            messagebox.showwarning("Save Warning", "No character is currently loaded to save.")
            return

        # Prepare safe filename
        safe_name_for_file = self.current_character.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        initial_filename = f"{safe_name_for_file}_save.json"

        file_path = filedialog.asksaveasfilename(
            title="Save Character As",
            initialdir="saved_characters",
            initialfile=initial_filename,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                data = self.current_character.to_dict()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"GUI: Saved character {self.current_character.name} to {file_path}")
                messagebox.showinfo("Save Success", f"Character saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save character:\n{e}")

    def on_load_clicked(self):
        """Handler for load button."""
        file_path = filedialog.askopenfilename(
            title="Select Character Save File",
            initialdir="saved_characters",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                from core.character import Character
                self.current_character = Character.from_dict(data, self.available_components, self.available_bodies)
                print(f"GUI: Successfully loaded character {self.current_character.name} from {file_path}")
                self.show_character_view()
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load character:\n{e}")
