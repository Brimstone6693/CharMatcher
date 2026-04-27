# file: gui/mixins/start_screen_mixin.py
"""Mixin for the start screen functionality."""
import tkinter as tk
from tkinter import ttk


class StartScreenMixin:
    """Provides start screen functionality for MainWindow."""
    
    def show_start_screen(self):
        """Shows the initial screen with Load and Create buttons."""
        # Clear previous content
        for widget in self.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self)
        frame.pack(expand=True)

        label = ttk.Label(frame, text="Welcome to Character Creator!", font=("Arial", 16))
        label.pack(pady=20)

        load_button = ttk.Button(frame, text="Load Character", command=self.on_load_clicked)
        load_button.pack(pady=5)

        create_button = ttk.Button(frame, text="Create New Character", command=self.on_create_clicked)
        create_button.pack(pady=5)

        manage_bodies_button = ttk.Button(frame, text="Manage Body Types", command=self.show_manage_bodies_screen)
        manage_bodies_button.pack(pady=5)
