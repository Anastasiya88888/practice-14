import json
import os
from api_client import GenshinAPIClient, GenshinCharacterParser

# === МОДЕЛЬ ДАНИХ ===
class Character:
    def __init__(self, id, name, char_type, health, attack, image_url=""):
        self.id = id
        self.name = name
        self.type = char_type
        self.health = health
        self.attack = attack
        self.image_url = image_url
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'health': self.health,
            'attack': self.attack,
            'image_url': self.image_url
        }

# === ЗБЕРЕЖЕННЯ ДАНИХ ===
class DataStorage:
    def __init__(self, filename='characters.json'):
        self.filename = filename
        self.characters = self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Character(**char) for char in data]
        return []
    
    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump([char.to_dict() for char in self.characters], f, 
                     ensure_ascii=False, indent=2)
    
    def add_character(self, character):
        self.characters.append(character)
        self.save()
    
    def get_all(self):
        return self.characters
    
    def get_by_id(self, char_id):
        for char in self.characters:
            if char.id == char_id:
                return char
        return None

# === ARG PARSER ===
class ArgParser:
    @staticmethod
    def parse_args(input_string):
        parts = input_string.strip().split()
        if not parts:
            return None, []
        return parts[0], parts[1:]

# === RENDERER ===
class IRenderer:
    def render(self, data):
        raise NotImplementedError

class ConsoleRenderer(IRenderer):
    def render(self, data):
        print(data)
    
    def transform(self, character):
        return f"{character.id}. {character.name} ({character.type}) - HP: {character.health}, ATK: {character.attack}"

# === КОМАНДИ (STRATEGY) ===
class ICommandStrategy:
    def get_command_selectors(self):
        raise NotImplementedError
    
    def exec_command(self, command, args, storage, renderer):
        raise NotImplementedError

class ListCommand(ICommandStrategy):
    def get_command_selectors(self):
        return ['list', 'ls']
    
    def exec_command(self, command, args, storage, renderer):
        chars = storage.get_all()
        if not chars:
            renderer.render("Список персонажів порожній")
        else:
            renderer.render("=== Список персонажів ===")
            for char in chars:
                renderer.render(renderer.transform(char))

class AddCommand(ICommandStrategy):
    def get_command_selectors(self):
        return ['add', 'create']
    
    def exec_command(self, command, args, storage, renderer):
        renderer.render("=== Створення персонажа ===")
        name = input("Ім'я: ")
        char_type = input("Тип (воїн/маг/лучник): ")
        health = int(input("Здоров'я: "))
        attack = int(input("Атака: "))
        image_url = input("URL зображення (необов'язково): ")
        
        char_id = len(storage.get_all()) + 1
        new_char = Character(char_id, name, char_type, health, attack, image_url)
        storage.add_character(new_char)
        renderer.render(f"✓ Персонаж '{name}' створено!")

class ShowCommand(ICommandStrategy):
    def get_command_selectors(self):
        return ['show', 'view']
    
    def exec_command(self, command, args, storage, renderer):
        if not args:
            renderer.render("Помилка: вкажіть ID персонажа")
            return
        
        char_id = int(args[0])
        char = storage.get_by_id(char_id)
        
        if char:
            renderer.render(f"\n=== {char.name} ===")
            renderer.render(f"ID: {char.id}")
            renderer.render(f"Тип: {char.type}")
            renderer.render(f"Здоров'я: {char.health}")
            renderer.render(f"Атака: {char.attack}")
            if char.image_url:
                renderer.render(f"Зображення: {char.image_url}")
        else:
            renderer.render("Персонаж не знайдений")

class HelpCommand(ICommandStrategy):
    def get_command_selectors(self):
        return ['help', '?']
    
    def exec_command(self, command, args, storage, renderer):
        help_text = """
=== Доступні команди ===
list, ls       - Показати всіх персонажів
add, create    - Додати нового персонажа
show <id>      - Показати деталі персонажа
import, fetch  - Імпортувати персонажів з API
help, ?        - Показати цю довідку
exit, quit     - Вийти з програми
        """
        renderer.render(help_text)

# === ІМПОРТ ПЕРСОНАЖІВ З API ===
class ImportCommand(ICommandStrategy):

    def get_command_selectors(self):
        return ['import', 'fetch']

    def exec_command(self, command, args, storage, renderer):
        renderer.render("=== Імпорт персонажів з API ===")
        renderer.render("Завантаження списку персонажів...")

        # Створюємо клієнт API
        api_client = GenshinAPIClient()
        parser = GenshinCharacterParser()

        # Отримуємо список імен
        character_names = api_client.get_all_character_names()

        if not character_names:
            renderer.render("❌ Не вдалося завантажити персонажів")
            return

        renderer.render(f"Знайдено {len(character_names)} персонажів")

        try:
            count = int(input(f"Скільки завантажити? (1-{len(character_names)}): "))
            count = min(count, len(character_names))
        except:
            count = 5

        renderer.render(f"Завантаження {count} персонажів...")

        imported = 0
        current_max_id = max([c.id for c in storage.get_all()], default=0)

        # Завантажуємо по одному
        for i, name in enumerate(character_names[:count]):
            renderer.render(f"[{i + 1}/{count}] Завантаження {name}...")

            details = api_client.get_character_details(name)
            if details:
                char = parser.parse_to_character(details, current_max_id + i + 1, Character)
                storage.add_character(char)
                imported += 1

        renderer.render(f"✓ Успішно імпортовано {imported} персонажів!")


# === ГОЛОВНИЙ CLI ===
class CLI:
    def __init__(self):
        self.storage = DataStorage()
        self.renderer = ConsoleRenderer()
        self.commands = [
            ListCommand(),
            AddCommand(),
            ShowCommand(),
            HelpCommand(),
            ImportCommand()
        ]
        self.parser = ArgParser()
    
    def display(self):
        print("\n" + "="*50)
        print("   КАТАЛОГ ПЕРСОНАЖІВ")
        print("="*50)
        print("Введіть 'help' для довідки\n")
    
    def exec_command(self, input_string):
        command, args = self.parser.parse_args(input_string)
        
        if command in ['exit', 'quit']:
            return False
        
        for cmd_strategy in self.commands:
            if command in cmd_strategy.get_command_selectors():
                cmd_strategy.exec_command(command, args, self.storage, self.renderer)
                return True
        
        self.renderer.render(f"Невідома команда: {command}")
        return True
    
    def run(self):
        self.display()
        
        while True:
            try:
                user_input = input("\n> ")
                if not self.exec_command(user_input):
                    print("До побачення!")
                    break
            except KeyboardInterrupt:
                print("\nДо побачення!")
                break
            except Exception as e:
                print(f"Помилка: {e}")

# === ЗАПУСК ===
if __name__ == "__main__":
    cli = CLI()
    cli.run()