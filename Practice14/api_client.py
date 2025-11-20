import requests

# === РОБОТА З API GENSHIN IMPACT ===
class GenshinAPIClient:

    def __init__(self):
        self.base_url = "https://genshin.jmp.blue"

    def get_all_character_names(self):
        """Отримання списку усіх імен персонажів"""
        try:
            url = f"{self.base_url}/characters"
            response = requests.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Помилка: {response.status_code}")
                return []
        except Exception as e:
            print(f"Помилка з'єднання: {e}")
            return []

    def get_character_details(self, character_name):
        """Отримання деталей про конкретного персонажа"""
        try:
            url = f"{self.base_url}/characters/{character_name}"
            response = requests.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Помилка: {e}")
            return None

# === ПЕРЕТВОРЮЄМО ДАНІ З API У ОБ'ЄКТИ CHARACTER ===
class GenshinCharacterParser:

    @staticmethod
    def parse_to_character(api_data, char_id, character_class):
        """
        api_data - словник з даними персонажа
        char_id - ID для нашої системи
        """
        name = api_data.get('name', 'Unknown')
        vision = api_data.get('vision', 'None')  # Елемент персонажа
        weapon = api_data.get('weapon', 'Unknown')
        rarity = api_data.get('rarity', 3)

        return character_class(
            id=char_id,
            name=name,
            char_type=f"{vision} ({weapon})",
            health=rarity * 20,
            attack=rarity * 10,
            image_url=f"https://genshin.jmp.blue/characters/{name.lower()}/icon"
        )