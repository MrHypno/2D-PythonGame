import pygame
import random

ITEM_DATA = {
    "bandage": {
        "display_name": "Bandage",
        "desc": "A roll of clean cloth. Restores 25 Vitality.",
        "color": (220, 220, 220),
        "effect": {"heal": 25},
    },
    "herbs": {
        "display_name": "Herbs",
        "desc": "Fresh medicinal herbs. Restores 15 Vitality.",
        "color": (80, 200, 80),
        "effect": {"heal": 15},
    },
    "armor": {
        "display_name": "Armor Piece",
        "desc": "A set of heavy armor. Restores 15 Armor.",
        "color": (150, 150, 200),
        "effect": {"armor": 15},
    },
    "key": {
        "display_name": "Key",
        "desc": "An old iron key. Opens locked doors.",
        "color": (180, 180, 180),
        "effect": {},
    },
    "golden key": {
        "display_name": "Golden Key",
        "desc": "A shiny golden key. Opens locked chests.",
        "color": (255, 215, 0),
        "effect": {},
    },
    "shovel": { #Cut content
        "display_name": "Shovel",
        "desc": "A sturdy shovel. Useful for digging.",
        "color": (139, 90, 43),
        "effect": {},
    },
    "gold coin": {
        "display_name": "Gold Coin",
        "desc": "A shiny gold coin. The merchant wants this.",
        "color": (255, 200, 0),
        "effect": {},
    },
}

item_list = list(ITEM_DATA.keys())


class Item:
    _images = {}

    @classmethod
    def _load_images(cls):
        if not cls._images:
            image_paths = {
                "gold coin": "assets/gold_coin.png",
                "key": "assets/key.png",
                "golden key": "assets/gold_key.png",
                "herbs": "assets/herbs.png",
                "armor": "assets/armor.png",
                "bandage": "assets/bandage.png"
            }
            for name, path in image_paths.items():
                try:
                    img = pygame.image.load(path).convert_alpha()
                    cls._images[name] = pygame.transform.scale(img, (24, 24))
                except Exception:
                    pass

    def __init__(self, x, y, name):
        Item._load_images()
        self.name = name
        data = ITEM_DATA.get(name, {})
        self.display_name = data.get("display_name", name.title())
        self.desc = data.get("desc", "")
        self.color = data.get("color", (200, 200, 200))
        self.rect = pygame.Rect(x, y, 24, 24)
        self.image = Item._images.get(name)

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 1)


class Chest:
    _frames = None

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return
        try:
            sheet = pygame.image.load("assets/chest_01.png").convert_alpha()
            cls._frames = []
            for i in range(4):
                frame = sheet.subsurface(pygame.Rect(i * 16, 0, 16, 16))
                cls._frames.append(pygame.transform.scale(frame, (32, 32)))
        except Exception:
            cls._frames = []

    def __init__(self, x, y, loot, locked=False):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.loot = loot
        self.state = "locked" if locked else "closed"
        Chest._load_frames()

    def try_open(self, inventory):
        if self.state == "opened":
            return False, "This chest is empty.", None
        if self.state == "locked":
            if "golden key" in inventory:
                inventory.remove("golden key")
                self.state = "opened"
                reward = random.choice(self.loot) if self.loot else None
                if reward:
                    inventory.append(reward)
                return True, f"Chest opened! You found: {reward or 'nothing'}.", reward
            return False, "This chest is locked. You need a Golden Key.", None
        self.state = "opened"
        reward = random.choice(self.loot) if self.loot else None
        if reward:
            inventory.append(reward)
        return True, f"Chest opened! You found: {reward or 'nothing'}.", reward

    def draw(self, surface):
        frames = Chest._frames
        if frames:
            if self.state == "opened":
                surface.blit(frames[3], self.rect)
            elif self.state == "locked":
                surface.blit(frames[0], self.rect)
                lock_rect = pygame.Rect(self.rect.right - 10, self.rect.top + 2, 8, 8)
                pygame.draw.rect(surface, (255, 215, 0), lock_rect)
                pygame.draw.rect(surface, (180, 140, 0), lock_rect, 1)
            else:
                surface.blit(frames[0], self.rect)
        else:
            if self.state == "opened":
                color = (60, 40, 20)
            elif self.state == "locked":
                color = (200, 160, 60)
            else:
                color = (160, 110, 40)
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, (255, 215, 0), self.rect, 2)
