# file: gui/mixins/creation_screen_mixin.py
"""Mixin for character creation screen functionality."""
import tkinter as tk
from tkinter import ttk, messagebox


class CreationScreenMixin:
    """Provides character creation screen functionality for MainWindow."""
    
    def show_creation_screen(self):
        """Shows the character creation screen."""
        # Clear previous content
        for widget in self.winfo_children():
            widget.destroy()

        if not self.available_bodies:
            messagebox.showwarning("No Bodies", "No body types found. Cannot create character.")
            self.show_start_screen()
            return

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Character name
        ttk.Label(frame, text="Character Name:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(frame)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))

        # Body type selection
        ttk.Label(frame, text="Body Type:").pack(anchor=tk.W)
        body_names = list(self.available_bodies.keys())
        self.body_var = tk.StringVar(value=body_names[0] if body_names else "")
        self.body_combo = ttk.Combobox(frame, textvariable=self.body_var, values=body_names, state="readonly")
        self.body_combo.pack(fill=tk.X, pady=(0, 10))

        # Component selection - получаем компоненты из главного окна
        ttk.Label(frame, text="Select Components:").pack(anchor=tk.W)
        self.component_vars = {}
        comp_frame = ttk.Frame(frame)
        comp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        canvas = tk.Canvas(comp_frame)
        scrollbar = ttk.Scrollbar(comp_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Используем available_components из главного окна (MainWindow)
        available_components = getattr(self, 'available_components', {})
        for comp_name in available_components.keys():
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(scrollable_frame, text=comp_name, variable=var)
            chk.pack(anchor=tk.W)
            self.component_vars[comp_name] = var

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create button
        create_btn = ttk.Button(frame, text="Create Character", command=self.on_create_confirm_clicked)
        create_btn.pack(pady=10)

        # Back button
        back_btn = ttk.Button(frame, text="Back", command=self.show_start_screen)
        back_btn.pack()

    def on_create_confirm_clicked(self):
        """Handler for create confirmation button."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Invalid Input", "Please enter a character name.")
            return

        # Get selected body type
        selected_body_name = self.body_var.get()
        selected_body_class = self.available_bodies.get(selected_body_name)
        if not selected_body_class:
            messagebox.showerror("Creation Error", f"Selected body type '{selected_body_name}' not found.")
            return

        # Create body instance (with minimal parameters for example)
        body_instance = selected_body_class(race=selected_body_name.replace("Body", "").lower(), gender="N/A")

        # Создаём данные персонажа как словарь и передаём через callback
        # Это позволяет body_maker не зависеть от core.character
        character_data = {
            'name': name,
            'body': body_instance.to_dict() if hasattr(body_instance, 'to_dict') else str(body_instance),
            'components': []
        }

        # Add selected components - получаем компоненты из главного окна
        available_components = getattr(self, 'available_components', {})
        for comp_name, var in self.component_vars.items():
            if var.get():
                comp_class = available_components.get(comp_name)
                if comp_class:
                    comp_instance = comp_class()
                    if hasattr(comp_instance, 'to_dict'):
                        character_data['components'].append({
                            'type': comp_class.__name__,
                            'data': comp_instance.to_dict()
                        })

        # Передаём данные персонажа через callback главному окну
        if hasattr(self, 'on_character_created_callback'):
            self.on_character_created_callback(character_data)
        else:
            # Fallback: создаём персонажа через метод главного окна
            if hasattr(self, '_create_character_from_data'):
                self._create_character_from_data(character_data)

        print(f"GUI: Created character {name}")
        if hasattr(self, 'show_character_view'):
            self.show_character_view()
