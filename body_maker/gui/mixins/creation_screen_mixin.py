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

        # Component selection
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

        for comp_name in self.available_components.keys():
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

        # Create character
        from core.character import Character
        self.current_character = Character(name=name, body=body_instance)

        # Add selected components
        for comp_name, var in self.component_vars.items():
            if var.get():
                comp_class = self.available_components[comp_name]
                comp_instance = comp_class()
                self.current_character.add_component(comp_instance)

        print(f"GUI: Created character {self.current_character.name}")
        self.show_character_view()
