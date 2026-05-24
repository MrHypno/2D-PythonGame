import json
import os
from config import SAVE_FILE

def save_game(player, king, level):
    data = {
        "player": {
            "class": player.name,
            "x": int(player.hitbox.x),
            "y": int(player.hitbox.y),
            "vitality": player.vitality,
            "max_vitality": player.max_vitality,
            "current_armor": player.current_armor,
            "attack_power": player.attack_power,
            "inventory": player.inventory[:],
        },
        "king": {
            "x": int(king.hitbox.x),
            "y": int(king.hitbox.y),
            "vitality": king.vitality,
            "is_alive": king.is_alive,
        },
        "level": {
            "current_room": level.current_room_name,
            "visited_rooms": list(level.visited_rooms),
            "unlocked_doors": [list(d) for d in level.unlocked_doors],
            "bandit_camp_cleared": level.bandit_camp_cleared,
            "cleared_enemy_rooms": list(level.cleared_enemy_rooms),
            "opened_chests": [list(c) for c in level.opened_chests],
            "collected_items": [list(c) for c in level.collected_items],
        },
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except IOError:
        return False


def load_game():
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def has_save():
    return os.path.exists(SAVE_FILE)
