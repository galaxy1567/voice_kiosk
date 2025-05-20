import json

def load_menu():
    with open("menu_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_menu_data(data):
    with open("menu_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def filter_menu_by_allergy(menu, allergy):
    return [item for item in menu if allergy not in item["allergy"]]

def only_menu_with_allergy(menu, allergy):
    return [item for item in menu if allergy in item["allergy"]]

def filter_by_vegan_level(menu, level):
    return [item for item in menu if item["vegan_level"] == level]
