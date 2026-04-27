# file: main_entry.py
"""
Точка входа в приложение Character Creator.
Использует core для загрузки модулей и управления персонажами.
"""

import os
import json
from core.character import Character
from core.module_loader import load_available_modules_and_bodies

def main():
    print("=== Welcome to Character Creator ===")

    # Шаг 1: Загрузка модулей и тел
    print("\nLoading available modules and body types...")
    # Пути теперь определяются автоматически в module_loader.py относительно корня проекта
    available_components, available_bodies = load_available_modules_and_bodies()

    if not available_components and not available_bodies:
        print("No modules or body types found in 'modules' or 'bodies' directories!")
        return

    print(f"Found {len(available_components)} module(s): {list(available_components.keys())}")
    print(f"Found {len(available_bodies)} body type(s): {list(available_bodies.keys())}\n")

    # Шаг 2: Выбор действия
    choice = input("Load existing character (L) or Create new (C)? ").lower()

    if choice == 'l':
        char = load_character_flow(available_components, available_bodies)
    elif choice == 'c':
        char = create_character_flow(available_components, available_bodies)
    else:
        print("Invalid choice.")
        return

    if char:
        print("\n--- Character Loaded/Created ---")
        print(char.describe())

        # Предложим пользователю сохранить персонажа
        save_choice = input("\nDo you want to save this character? (Y/n): ").lower()
        if save_choice == 'y' or save_choice == '':
            save_character_flow(char)


def load_character_flow(available_components, available_bodies):
    save_dir = os.path.join(PROJECT_ROOT, "saved_characters")
    if not os.path.exists(save_dir):
        print(f"Save directory '{save_dir}' not found.")
        return None

    saves = [f for f in os.listdir(save_dir) if f.endswith('.json')]
    if not saves:
        print(f"No save files found in '{save_dir}'.")
        return None

    print(f"Available saves: {saves}")
    chosen_save = input("Enter save file name (without .json): ") + ".json"
    save_path = os.path.join(save_dir, chosen_save)

    if not os.path.exists(save_path):
        print(f"Save file '{save_path}' not found.")
        return None

    try:
        with open(save_path, 'r') as f:
            data = json.load(f)
        # !!! Передаём и компоненты, и тела в from_dict !!!
        char = Character.from_dict(data, available_components, available_bodies)
        print(f"Successfully loaded character from {chosen_save}.")
        return char
    except Exception as e:
        print(f"Error loading character from {save_path}: {e}")
        return None


def create_character_flow(available_components, available_bodies):
    name = input("Enter character name: ")

    # --- Выбор тела ---
    if not available_bodies:
        print("No body types available to choose from!")
        return None

    print("\nAvailable body types:")
    body_names = list(available_bodies.keys())
    for i, body_name in enumerate(body_names):
        print(f"{i+1}. {body_name}")
    body_choice_idx = int(input("Choose a body type (number): ")) - 1
    if 0 <= body_choice_idx < len(body_names):
        selected_body_class = available_bodies[body_names[body_choice_idx]]
        # Здесь можно запросить параметры для конкретного тела, если нужно
        race = input(f"Enter race for {body_names[body_choice_idx]} (default: {selected_body_class.__name__.replace('Body', '').lower()}): ") or selected_body_class.__name__.replace('Body', '').lower()
        gender = input(f"Enter gender (optional): ") or "N/A"
        # Создаём тело с параметрами, если конструктор ожидает их
        # Для простоты предположим, что все тела принимают race и gender
        body = selected_body_class(race=race, gender=gender)
    else:
        print("Invalid choice for body type.")
        return None

    char = Character(name=name, body=body)

    # --- Выбор компонентов ---
    if not available_components:
        print("No components available to add!")
        print(f"\nCreated character with only body: {char.name}")
        return char

    print("\nAvailable modules to add:")
    for i, mod_name in enumerate(available_components.keys()):
        print(f"{i+1}. {mod_name}")
    print("Type numbers separated by commas (e.g., 1, 3) or 'all' to add everything.")

    user_input = input("Your choice: ").strip().lower()
    selected_modules = []

    if user_input == 'all':
        selected_modules = list(available_components.values())
    else:
        try:
            indices = [int(x.strip()) - 1 for x in user_input.split(',')]
            selected_modules = [list(available_components.values())[i] for i in indices if 0 <= i < len(available_components)]
        except ValueError:
            print("Invalid input format for module selection.")
            return None

    for ModClass in selected_modules:
        instance = ModClass()
        char.add_component(instance)

    print(f"\nCreated character: {char.name}")
    return char


# --- Функция сохранения ---
def save_character_flow(character):
    save_dir = os.path.join(PROJECT_ROOT, "saved_characters")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # --- Новое ---
    safe_name = character.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    filename = f"{safe_name}_save.json"
    # ---

    save_path = os.path.join(save_dir, filename)

    data = character.to_dict()
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Character saved to {save_path}")
    except Exception as e:
        print(f"Error saving character: {e}")


# Получаем корневую директорию проекта
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    main()