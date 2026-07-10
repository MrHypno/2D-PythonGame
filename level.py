from config import ASSETS_DIR
import os
import pygame
from item import Item, Chest
from enemy import Enemy
from characters import NPC, Guard
import xml.etree.ElementTree as ET

TILE_SIZE     = 40
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600

SMALL_ROOM_HEIGHT = 4 * TILE_SIZE

def load_tileset_and_scale(image_path, original_size=16, target_size=40, columns=6):
    tiles = {}
    sheet = pygame.image.load(image_path).convert_alpha()
    sheet_height = sheet.get_height()

    rows = sheet_height // original_size

    tile_id = 1 
    
    for y in range(rows):
        for x in range(columns):
            rect = pygame.Rect(x * original_size, y * original_size, original_size, original_size)
            image = sheet.subsurface(rect)
            scaled_image = pygame.transform.scale(image, (target_size, target_size))
            tiles[str(tile_id)] = scaled_image
            tile_id += 1
            
    return tiles

def read_tmx(tmx_path):
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    layers = []
    
    for layer in root.findall('layer'):
        data = layer.find('data').text
        lines = [line.strip() for line in data.strip().split('\n')]
        layer_data = []
        for line in lines:
            row = [val for val in line.split(',') if val]
            if row:
                layer_data.append(row)
        layers.append(layer_data)
        
    return layers

class Level:
    def __init__(self):
        self.grass_image = pygame.image.load(f"{ASSETS_DIR}/map/grass.png").convert()
        self.grass_image = pygame.transform.scale(self.grass_image, (TILE_SIZE, TILE_SIZE))
        self.tileset_images = load_tileset_and_scale(f"{ASSETS_DIR}/map/plains.png", original_size=16, target_size=40, columns=6)
        try:
            self.interior_tileset = load_tileset_and_scale(f"{ASSETS_DIR}/map/interior_tiles.png", original_size=16, target_size=40, columns=48)
        except FileNotFoundError:
            self.interior_tileset = {}

        try:
            self.map_layers = []
        except FileNotFoundError:
            floors_sheet = pygame.Surface((400, 400)); floors_sheet.fill((50,200,50))
            walls_sheet = pygame.Surface((400, 400)); walls_sheet.fill((50,150,50))
            dungeon_sheet = pygame.Surface((400, 400)); dungeon_sheet.fill((100,100,100))
            field_sheet = pygame.Surface((80, 240)); field_sheet.fill((50,200,50))

        self.unlocked_doors = set()
        self.unlock_door = pygame.mixer.Sound(f"{ASSETS_DIR}/sounds/unlock.wav")

        self.bandit_camp_cleared = False

        self.world_maps = {

            "ambush area": {
                "tmx": "ambush_area.tmx",
                "region": "forest",
                "west": "forest", "east": "woods",
                "name": "Ambush Area",
                "desc": "You were ambushed here. The bandits are still searching for you. Move quickly!",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "woods": {
                "tmx": "woods.tmx",
                "region": "forest",
                "west": "ambush area", "east": "deep forest2", "north": "forest2",
                "name": "Woods",
                "desc": "It is unnaturally quiet. Not even the birds are singing. Something is wrong.",
                "map": [
                    "11111111000011111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [],
                "enemies": [{"name": "Bandit", "x": 400, "y": 300, "hp": 60, "ap": 15}]
            },

            "forest": {
                "tmx": "forest.tmx",
                "region": "forest",
                "west": "town square", "east": "ambush area",
                "name": "Forest",
                "desc": "You can see town houses on the horizon. If it's safe, there might be something useful there.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "town square": {
                "tmx": "town_square.tmx",
                "region": "town",
                "north": "road", "south": "town house", "west": "middle house", "east": "forest",
                "name": "Town Square",
                "desc": "You've arrived at the town center. You can try entering the buildings around you.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [],
                "npcs": [{"type": "merchant", "x": 319, "y": 248}],
                "enemies": []
            },

            "road": {
                "tmx": "road.tmx",
                "region": "town",
                "west": "big house", "north": "road2", "south": "town square",
                "name": "Road",
                "desc": "A cobblestone road leading north through the town.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], 
                "chests": [{"x": 586, "y": 508, "loot": ["golden key", "armor", "bandage"]}], 
                "npcs": [], "enemies": []
            },

            "road2": {
                "tmx": "road2.tmx",
                "region": "town",
                "south": "road", "north": "road3",
                "name": "Road",
                "desc": "The road continues north. You can hear distant sounds of the town behind you.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "road3": {
                "tmx": "road3.tmx",
                "region": "town",
                "south": "road2", "north": "town hall entrance", "east": "road4",
                "name": "Road",
                "desc": "The town hall looms ahead to the north. A side road branches east.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "road4": {
                "tmx": "road4.tmx",
                "region": "town",
                "west": "road3", "east": "abandoned camp",
                "name": "Road",
                "desc": "A quieter stretch of road. Abandoned wagons line the sides.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [],
                "enemies": [{"name": "Bandit", "x": 450, "y": 200, "hp": 60, "ap": 15}]
            },

            "big house": {
                "tmx": "big_house_enterance.tmx",
                "region": "house",
                "east": "road", "west": "big house hallway", "south": "big house guest room",
                "name": "Town House — Entrance",
                "desc": "A sturdy townhouse. The floorboards creak under your boots.",
                "villager_room": True,
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [],
                "npcs": [{"type": "villager", "x": 696, "y": 237}],
                "enemies": []
            },

            "big house guest room": {
                "tmx": "big_house_guest_room.tmx",
                "region": "house",
                "north": "big house",
                "name": "Town House — Guest Room",
                "desc": "A smaller, simpler room. It looks like it hasn't been used in a while.",
                "map": [
                    "11111111110011111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [{"x": 500, "y": 200, "loot": ["bandage", "herbs", "armor"], "locked": True}],
                "npcs": [], "enemies": []
            },

            "big house hallway": {
                "tmx": "big_house_hallway.tmx",
                "region": "house",
                "north": "big house bedroom", "east": "big house",
                "name": "Town House — Hallway",
                "desc": "A narrow corridor. Faded paintings hang crookedly on the walls.",
                "map": [
                    "11111111110011111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "big house bedroom": {
                "tmx": "big_house_bedroom.tmx",
                "region": "house",
                "south": "big house hallway", "west": "big house kitchen",
                "name": "Town House — Master Bedroom",
                "desc": "A dusty bedroom. The bed hasn't been slept in for days.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [{"x": 100, "y": 200, "loot": ["key", "gold coin", "armor"], "locked": True}],
                "npcs": [], "enemies": []
            },

            "big house kitchen": {
                "tmx": "big_house_kitchen.tmx",
                "region": "house",
                "west": "deep forest", "east": "big house bedroom",
                "name": "Town House — Kitchen",
                "desc": "A cold hearth and empty shelves. Someone left in a hurry.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [{"name": "bandage", "x": 400, "y": 200}],
                "chests": [], "npcs": [], "enemies": []
            },

            "deep forest": {
                "tmx": "deep_forest.tmx",
                "region": "forest",
                "west": "cliffs", "east": "big house kitchen",
                "name": "Deep Forest",
                "desc": "The trees are so thick here that they block out the sun. You feel like you're being watched.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "cliffs": {
                "tmx": "cliffs.tmx",
                "region": "forest",
                "east": "deep forest",
                "name": "Cliffs",
                "desc": "You stand at the edge of extremely high cliffs. The wind howls around you. One wrong step...",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [{"x": 300, "y": 300, "loot": ["golden key", "armor", "herbs"]}],
                "npcs": [], "enemies": []
            },

            "middle house": {
                "tmx": "middle_house_enterance.tmx",
                "region": "house",
                "east": "town square", "west": "middle house bedroom",
                "north": "middle house kitchen", "south": "middle house workshop",
                "name": "Town House — Entrance",
                "desc": "A modest house on the edge of the square. The door was left wide open.",
                "villager_room": True,
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [],
                "npcs": [{"type": "villager", "x": 300, "y": 260}],
                "enemies": []
            },

            "middle house bedroom": {
                "tmx": "middle_house_bedroom.tmx",
                "region": "house",
                "east": "middle house",
                "name": "Town House — Bedroom",
                "desc": "A simple bedroom. A child's drawing is pinned to the wall.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [{"name": "herbs", "x": 140, "y": 180}],
                "chests": [], "npcs": [], "enemies": []
            },

            "middle house kitchen": {
                "tmx": "middle_house_kitchen.tmx",
                "region": "house",
                "south": "middle house",
                "name": "Town House — Kitchen",
                "desc": "A modest kitchen. Something still simmers on the cold stove.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "middle house workshop": {
                "tmx": "middle_house_workshop.tmx",
                "region": "house",
                "north": "middle house",
                "name": "Town House — Workshop",
                "desc": "A dusty workshop smelling of sawdust and oil. Tools hang on the walls.",
                "locked_by": "key",
                "map": [
                    "11111111110011111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [{"name": "key", "x": 500, "y": 100}],
                "chests": [], "npcs": [], "enemies": []
            },

            "town hall entrance": {
                "tmx": "town_hall_enterance.tmx",
                "region": "dungeon",
                "north": "town hall hallway", "south": "road3", "west": "archives", "east": "town hall courtroom",
                "name": "Town Hall — Entrance",
                "desc": "The entrance is silent. A dusty reception desk sits empty in the corner.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "archives": {
                "tmx": "town_hall_archives.tmx",
                "region": "dungeon",
                "east": "town hall entrance",
                "name": "Town Hall — Archives",
                "desc": "The room smells of old paper and decaying parchment. Rows of shelves tower over you.",
                "locked_by": "key",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [{"x": 300, "y": 300, "loot": ["gold coin", "armor", "bandage"]}],
                "npcs": [], "enemies": []
            },

            "town hall hallway": {
                "tmx": "town_hall_hallway.tmx",
                "region": "dungeon",
                "south": "town hall entrance", "north": "mayor's office",
                "east": "treasury", "west": "town hall council chamber",
                "name": "Town Hall — Hallway",
                "desc": "A long corridor. Portraits of past mayors seem to watch you from the walls.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "town hall courtroom": {
                "tmx": "town_hall_courtroom.tmx",
                "region": "dungeon",
                "west": "town hall entrance",
                "name": "Town Hall — Courtroom",
                "desc": "Rows of empty wooden benches face the front. You feel like you are on trial.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "mayor's office": {
                "tmx": "town_hall_mayors_office.tmx",
                "region": "house",
                "south": "town hall hallway", "west": "town hall storage",
                "name": "Town Hall — Mayor's Office",
                "desc": "It looks like someone left in a hurry. Papers are scattered across the fancy desk.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [{"name": "bandage", "x": 400, "y": 100}, {"name": "golden key", "x": 500, "y": 100}],
                "chests": [], "npcs": [], "enemies": []
            },

            "treasury": {
                "tmx": "town_hall_treasury.tmx",
                "region": "dungeon",
                "west": "town hall hallway",
                "locked_by": "key",
                "name": "Town Hall — Treasury",
                "desc": "The air is cold here. Thick stone walls suggest this room was built to keep things safe.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [{"name": "gold coin", "x": 300, "y": 200}],
                "chests": [{"x": 500, "y": 200, "loot": ["golden key", "armor", "gold coin"], "locked": True}],
                "npcs": [], 
                "enemies": [{"name": "Bandit", "x": 400, "y": 300, "hp": 60, "ap": 15}]
            },

            "town hall storage": {
                "tmx": "town_hall_storage.tmx",
                "region": "dungeon",
                "east": "mayor's office", "north": "safe road", "south": "town hall council chamber",
                "locked_by": "key",
                "name": "Town Hall — Storage",
                "desc": "Just a small storage room. There is barely enough space to turn around.",
                "map": [
                    "11111111000011111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111000011111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "town hall council chamber": {
                "tmx": "town_hall_council_chamber.tmx",
                "region": "dungeon",
                "north": "town hall storage", "east": "town hall hallway",
                "name": "Town Hall — Council Chamber",
                "desc": "A heavy oak table sits in the center. Stacks of tax ledgers left on top.",
                "map": [
                    "11111111000011111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111000011111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "safe road": {
                "tmx": "safe_road.tmx",
                "region": "town",
                "south": "town hall storage", "east": "safe road2",
                "name": "Safe Road",
                "desc": "You're on a well-lit road. Guards are visible in the distance. You're almost there!",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "safe road2": {
                "tmx": "safe_road2.tmx",
                "region": "town",
                "west": "safe road", "east": "castle",
                "name": "Safe Road",
                "desc": "The castle gate is within sight. Just a little further!",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "town house": {
                "tmx": "town_house_enterance.tmx",
                "region": "house",
                "north": "town square", "west": "town house bedroom", "south": "town house larder",
                "name": "Town House — Entrance",
                "desc": "A humble townhouse. The air feels heavy and dusty.",
                "villager_room": True,
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [],
                "chests": [],
                "npcs": [{"type": "villager", "x": 500, "y": 100}],
                "enemies": []
            },

            "town house bedroom": {
                "tmx": "town_house_bedroom.tmx",
                "region": "house",
                "east": "town house",
                "name": "Town House — Bedroom",
                "desc": "A small bedroom. The bed looks unmade.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [{"name": "key", "x": 300, "y": 200}],
                "chests": [], "npcs": [], "enemies": []
            },

            "town house larder": {
                "tmx": "town_house_larder.tmx",
                "region": "house",
                "north": "town house",
                "name": "Town House — Larder",
                "desc": "A storage room smelling of dried herbs and salted meat.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [{"name": "herbs", "x": 619, "y": 109}],
                "chests": [], "npcs": [], "enemies": []
            },

            "deep forest2": {
                "tmx": "deep_forest2.tmx",
                "region": "forest",
                "west": "woods", "north": "bandit camp",
                "name": "Deep Forest",
                "desc": "This place doesn't look safe. You can see smoke rising in the distance.",
                "map": [
                    "11111111000011111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [], "chests": [], "npcs": [],
                "enemies": [{"name": "Bandit", "x": 400, "y": 300, "hp": 60, "ap": 15}]
            },

            "bandit camp": {
                "tmx": "bandit_camp.tmx",
                "region": "forest",
                "south": "deep forest2", "north": "old road",
                "name": "Bandit Camp",
                "desc": "A cold shiver runs down your spine. This place reeks of death.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [{"name": "key", "x": 200, "y": 100}, {"name": "bandage", "x": 550, "y": 100}],
                "chests": [{"x": 641, "y": 219, "loot": ["golden key", "armor", "bandage"], "locked": True}],
                "npcs": [],
                "enemies": [{"name": "Bandit Leader", "x": 400, "y": 150, "hp": 200, "ap": 35}]
            },

            "old road": {
                "tmx": "old_road.tmx",
                "region": "town",
                "south": "bandit camp", "west": "old road2",
                "name": "Old Road",
                "desc": "This place doesn't seem very safe. Watch your step.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [{"name": "bandage", "x": 400, "y": 100}],
                "chests": [], "npcs": [], "enemies": []
            },

            "old road2": {
                "tmx": "old_road2.tmx",
                "region": "town",
                "south": "forest4", "west": "abandoned camp", "east": "old road",
                "name": "Old Road",
                "desc": "There are fresh footprints in the mud that don't look like they belong to a soldier.",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000000",
                    "00000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "abandoned camp": {
                "tmx": "abandoned_camp.tmx",
                "region": "forest",
                "west": "road4", "north": "lighted road", "east": "old road2",
                "name": "Abandoned Camp",
                "desc": "You've come to an abandoned campsite. Some belongings may have been left behind.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000000",
                    "10000000000000000000",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111111111111111"
                ],
                "items": [{"name": "herbs", "x": 300, "y": 80}],
                "chests": [], "npcs": [], "enemies": []
            },

            "lighted road": {
                "tmx": "lighted_road.tmx",
                "region": "town",
                "north": "guards", "south": "abandoned camp",
                "name": "Lighted Road",
                "desc": "You're on a well-lit road. Guards are visible in the distance.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },

            "guards": {
                "tmx": "guards.tmx",
                "region": "town",
                "north": "castle", "south": "lighted road",
                "name": "Guards",
                "desc": "Royal guards stand at attention. They watch you carefully.",
                "guard_room": True,
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [],
                "npcs": [
                    {"type": "knight", "x": 120, "y": 60},
                    {"type": "knight", "x": 580, "y": 60},
                ],
                "enemies": []
            },

            "forest2": {
                "tmx": "forest2.tmx",
                "region": "forest",
                "south": "woods", "north": "forest3",
                "name": "Forest",
                "desc": "The trees grow denser. The path narrows and the shadows deepen.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [{"x": 400, "y": 300, "loot": ["herbs", "bandage", "golden key"]}],
                "npcs": [],
                "enemies": [{"name": "Bandit", "x": 200, "y": 200, "hp": 60, "ap": 15}]
            },

            "forest3": {
                "tmx": "forest3.tmx",
                "region": "forest",
                "south": "forest2", "north": "forest4",
                "name": "Forest",
                "desc": "This place doesn't seem very safe. You should be careful.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [], "chests": [], "npcs": [],
                "enemies": [{"name": "Archer Bandit", "x": 500, "y": 250, "hp": 50, "ap": 18}]
            },

            "forest4": {
                "tmx": "forest4.tmx",
                "south": "forest3", "north": "old road2",
                "name": "Forest",
                "desc": "The forest begins to thin. You can see a road ahead.",
                "map": [
                    "11111111100111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111100111111111"
                ],
                "items": [{"name": "herbs", "x": 400, "y": 300}],
                "chests": [], "npcs": [], "enemies": []
            },

            "castle": {
                "region": "dungeon",
                "west": "safe road2", "south": "guards",
                "name": "Castle",
                "desc": "You made it! The castle gates open before you. The King is safe!",
                "map": [
                    "11111111111111111111",
                    "10000000000000000001",
                    "10000000000000000001",
                    "00000000000000000001",
                    "00000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "10000000000000000001",
                    "11111111000011111111"
                ],
                "items": [], "chests": [], "npcs": [], "enemies": []
            },
        }

        self.current_room_name  = "ambush area"
        self.walls              = []
        self.active_items       = []
        self.active_enemies     = []
        self.active_chests      = []
        self.active_npcs        = []
        self.active_guard       = None

        self.visited_rooms       = set()
        self.entry_desc          = None
        self.entry_desc_timer    = 0
        self.entry_desc_duration = 4000
        self.is_new_discovery    = False

        self.cleared_enemy_rooms = set()
        self.opened_chests       = set()
        self.collected_items     = set()
        self.guard_room_state    = None

        self.room_positions = {}
        self._compute_room_positions()

        self.load_room(self.current_room_name)

    #Fixed minimap positions for rooms 
    def _compute_room_positions(self):
        self.room_positions = {
            "ambush area":       ( 0,  0),
            "forest":            (-1,  0),
            "town square":       (-2,  0),
            "woods":             ( 1,  0),
            "deep forest2":      ( 2,  0),

            "road":              (-2, -1),
            "road2":             (-2, -2),
            "road3":             (-2, -3),
            "road4":             (-1, -3),
            "abandoned camp":    ( 0, -4),

            "town house":         (-1,  1),
            "town house bedroom": (-2,  1),
            "town house larder":  (-1,  2),

            "middle house":          (-3,  2),
            "middle house bedroom":  (-4,  2),
            "middle house kitchen":  (-3,  1),
            "middle house workshop": (-3,  3),

            "big house":             (-4, -1),
            "big house guest room":  (-4,  0),
            "big house hallway":     (-5, -1),
            "big house bedroom":     (-5, -2),
            "big house kitchen":     (-6, -2),

            "deep forest":       (-7, -2),
            "cliffs":            (-8, -2),

            "town hall entrance":       (-2, -4),
            "archives":                 (-3, -4),
            "town hall courtroom":      (-1, -4),
            "town hall hallway":        (-2, -5),
            "mayor's office":           (-2, -6),
            "treasury":                 (-1, -5),
            "town hall council chamber":(-3, -5),
            "town hall storage":        (-3, -6),

            "forest2":           ( 1, -1),
            "forest3":           ( 1, -2),
            "forest4":           ( 1, -3),

            "bandit camp":       ( 2, -1),
            "old road":          ( 2, -4),
            "old road2":         ( 1, -4),

            "lighted road":      ( 0, -5),
            "guards":            ( 0, -6),
            "castle":            ( 0, -7),
            "safe road":         (-3, -7),
            "safe road2":        (-2, -7),
        }
        occupied = set(self.room_positions.values())
        remaining = [r for r in self.world_maps if r not in self.room_positions]
        if remaining:
            offsets = {"north": (0, -1), "south": (0, 1),
                       "east": (1, 0),   "west": (-1, 0)}
            for name in remaining:
                room = self.world_maps[name]
                placed = False
                for d, (dx, dy) in offsets.items():
                    neighbor = room.get(d)
                    if neighbor and neighbor in self.room_positions:
                        nx, ny = self.room_positions[neighbor]
                        cx, cy = nx - dx, ny - dy
                        if (cx, cy) not in occupied:
                            self.room_positions[name] = (cx, cy)
                            occupied.add((cx, cy))
                            placed = True
                            break
                if not placed:
                    bx = max(v[0] for v in occupied) + 1
                    self.room_positions[name] = (bx, 0)
                    occupied.add((bx, 0))

        NSOPEN = "11111111000011111111"
        for rdata in self.world_maps.values():
            rmap = list(rdata["map"])
            n    = len(rmap)
            if n >= 8:
                ta = n // 2
                tb = n // 2 + 1
                if 1 <= ta and tb <= n - 2:
                    side_rows = [ri for ri in range(1, n - 1)
                                 if rmap[ri][0] == "0" or rmap[ri][-1] == "0"]
                    if 0 < len(side_rows) <= 2 and sorted(side_rows) != [ta, tb]:
                        lo = rmap[side_rows[0]][0]
                        ro = rmap[side_rows[0]][-1]
                        for ri in side_rows:
                            rmap[ri] = "1" + "0" * 18 + "1"
                        for ri in [ta, tb]:
                            rmap[ri] = lo + "0" * 18 + ro
            if rdata.get("north") and rmap[0] == NSOPEN:
                rmap.insert(1, NSOPEN)
            if rdata.get("south") and rmap[-1] == NSOPEN:
                if (len(rmap) + 1) * TILE_SIZE <= SCREEN_HEIGHT:
                    rmap.insert(len(rmap) - 1, NSOPEN)
            rdata["map"] = rmap

    def open_guard_gate(self):
        if self.current_room_name != "guards":
            return
        room = self.world_maps["guards"]
        room["map"][0] = "11111111100111111111"
        self.walls.clear()
        for ri, row in enumerate(room["map"]):
            for ci, cell in enumerate(row):
                if cell == "1":
                    self.walls.append(pygame.Rect(ci * TILE_SIZE, ri * TILE_SIZE,
                                                  TILE_SIZE, TILE_SIZE))
                    
    def load_region(self, tmx_filename):
        dosya_yolu = f"{ASSETS_DIR}/map/{tmx_filename}"
        self.map_layers = read_tmx(dosya_yolu)

    def load_room(self, room_name):
        self.walls.clear()
        self.current_room_name = room_name
        room = self.world_maps[room_name]
        region = room.get("region", "forest")

        #TMX loader
        tmx_file = room.get("tmx")
        has_tmx = False
        if tmx_file:
            try:
                self.load_region(tmx_file)
                has_tmx = True
            except Exception as e:
                self.map_layers = []
        else:
            self.map_layers = []

        # non-walkble and walkable tile ids
        if region in ("house", "dungeon"):
            walkable_house = {
                "16", "17", "18", "64", "65", "66", "112", "113", "114", "160", "161", "162",
                "208", "209", "210", "256", "257", "258", "304", "305", "306", "352", "353", "354",
                "400", "401", "402", "288", "289", "290", "291", "100", "101", "102", "103", "148", "149", "150", "151", "390"
            }
            NON_WALKABLE_TILES = {str(i) for i in range(1, 1000)} - walkable_house
        else:
            NON_WALKABLE_TILES = {
                "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "49", 
                "50", "51", "52", "55", "56", "57", "58", "61", "62", "63", "64", "67", "68", "69", "70"
            }

        if has_tmx and getattr(self, "map_layers", None) and len(self.map_layers) > 0:
            rows = len(self.map_layers[0])
            cols = len(self.map_layers[0][0])
            for ri in range(rows):
                for ci in range(cols):
                    is_wall = False
                    for layer in self.map_layers:
                        if ri < len(layer) and ci < len(layer[ri]):
                            tmx_id = layer[ri][ci]
                            if tmx_id != "-1" and tmx_id != "0":
                                tiled_ui_id = str(int(tmx_id) - 1)
                                if tiled_ui_id in NON_WALKABLE_TILES:
                                    is_wall = True
                                    break
                    
                    if is_wall and ri < len(room["map"]) and ci < len(room["map"][ri]):
                        if ri == 0 and room["map"][0][ci] == "0":
                            is_wall = False
                        elif ri == len(room["map"]) - 1 and room["map"][-1][ci] == "0":
                            is_wall = False
                        elif ci == 0 and room["map"][ri][0] == "0":
                            is_wall = False
                        elif ci == len(room["map"][ri]) - 1 and room["map"][ri][-1] == "0":
                            is_wall = False
                                
                    if is_wall:
                        self.walls.append(pygame.Rect(ci * TILE_SIZE, ri * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            
            # string map walls for house regions
            if region in ("house", "dungeon"):
                for ri, row in enumerate(room["map"]):
                    for ci, cell in enumerate(row):
                        if cell == "1":
                            self.walls.append(pygame.Rect(ci * TILE_SIZE, ri * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        else:
            for ri, row in enumerate(room["map"]):
                for ci, cell in enumerate(row):
                    if cell == "1":
                        self.walls.append(pygame.Rect(ci * TILE_SIZE, ri * TILE_SIZE,
                                                      TILE_SIZE, TILE_SIZE))

        self.active_items = []
        for d in room.get("items", []):
            key = (room_name, d["name"], d["x"])
            if key not in self.collected_items:
                self.active_items.append(Item(d["x"], d["y"], d["name"]))

        self.active_chests = []
        for i, d in enumerate(room.get("chests", [])):
            chest = Chest(d["x"], d["y"], d["loot"], locked=d.get("locked", False))
            if (room_name, i) in self.opened_chests:
                chest.state = "opened"
            self.active_chests.append(chest)

        if room_name in self.cleared_enemy_rooms:
            self.active_enemies = []
        else:
            self.active_enemies = [Enemy(d["x"], d["y"], d["name"], d["hp"], d["ap"])
                                   for d in room.get("enemies", [])]

        self.active_npcs = [NPC(d["x"], d["y"], d["type"]) for d in room.get("npcs", [])]

        if room.get("guard_room"):
            if self.guard_room_state:
                gs = self.guard_room_state
                self.active_guard = Guard(gs["guard_x"], gs["guard_y"], is_riddle_guard=True)
                self.active_guard.is_hostile = gs["guard_hostile"]
                self.active_guard.hp = gs["guard_hp"]
                self.active_guard.gate_open = gs["gate_open"]
                self.active_guard.asked_already = gs["asked_already"]
                self.active_guard.mistakes = gs["mistakes"]
                if gs["guard_dead"]:
                    self.active_guard = None
                saved_npcs = gs.get("npcs", [])
                self.active_npcs = []
                for nd in saved_npcs:
                    npc = NPC(nd["x"], nd["y"], nd["type"])
                    npc.is_hostile = nd["hostile"]
                    npc.hp = nd["hp"]
                    self.active_npcs.append(npc)
            else:
                self.active_guard = Guard(400, 60, is_riddle_guard=True)
        else:
            self.active_guard = None

        self._room_pixel_height = len(room["map"]) * TILE_SIZE

        self.entry_desc = room.get("desc", "")
        self.entry_desc_timer = pygame.time.get_ticks()
        self.is_new_discovery = room_name not in self.visited_rooms
        self.visited_rooms.add(room_name)

    def mark_item_collected(self, item):
        self.collected_items.add((self.current_room_name, item.name, item.rect.x))

    def mark_chest_opened(self, chest):
        try:
            idx = self.active_chests.index(chest)
            self.opened_chests.add((self.current_room_name, idx))
        except ValueError:
            pass

    def check_enemies_cleared(self):
        room = self.world_maps[self.current_room_name]
        if room.get("enemies") and not self.active_enemies:
            self.cleared_enemy_rooms.add(self.current_room_name)
            if self.current_room_name == "bandit camp":
                self.bandit_camp_cleared = True

    def clamp_player(self, player):
        room_h = self._room_pixel_height
        room_map = self.world_maps[self.current_room_name]["map"]
        room_w = len(room_map[0]) * TILE_SIZE if room_map else SCREEN_WIDTH

        if player.hitbox.top < 0:
            player.hitbox.top = 0

        max_bottom = min(room_h, SCREEN_HEIGHT)
        if player.hitbox.bottom > max_bottom:
            player.hitbox.bottom = max_bottom

        if player.hitbox.left < 0:
            player.hitbox.left = 0
        if player.hitbox.right > min(room_w, SCREEN_WIDTH):
            player.hitbox.right = min(room_w, SCREEN_WIDTH)

        player.image_rect.midbottom = player.hitbox.midbottom

    def try_change_room(self, direction, player):
        try:
            next_name = self.world_maps[self.current_room_name].get(direction)
            if not next_name or next_name not in self.world_maps:
                return None

            next_room = self.world_maps[next_name]
            lock_key  = next_room.get("locked_by")
            door_id   = (next_name, "entry")

            if lock_key and door_id not in self.unlocked_doors:
                if lock_key in player.inventory:
                    player.inventory.remove(lock_key)
                    self.unlocked_doors.add(door_id)
                    self._do_change_room(direction, next_name, player)
                    self.unlock_door.play()
                    kname = "Golden Key" if lock_key == "golden key" else "Key"
                    return f"You used the {kname} to unlock the door!"
                else:
                    kname = "Golden Key" if lock_key == "golden key" else "Key"
                    return f"This door is locked. You need a {kname}."

            self._do_change_room(direction, next_name, player)
            return True

        except Exception:
            return None

    def _save_guard_room_state(self):
        if self.current_room_name != "guards":
            return
        guard = self.active_guard
        gs = {
            "guard_dead": guard is None,
            "guard_x": guard.hitbox.x if guard else 0,
            "guard_y": guard.hitbox.y if guard else 0,
            "guard_hostile": guard.is_hostile if guard else False,
            "guard_hp": guard.hp if guard else 0,
            "gate_open": guard.gate_open if guard else False,
            "asked_already": guard.asked_already if guard else True,
            "mistakes": guard.mistakes if guard else 0,
            "npcs": [],
        }
        for npc in self.active_npcs:
            gs["npcs"].append({
                "x": int(npc.hitbox.x), "y": int(npc.hitbox.y),
                "type": npc.npc_type,
                "hostile": npc.is_hostile, "hp": npc.hp,
            })
        self.guard_room_state = gs

    def _do_change_room(self, direction, next_name, player):
        self._save_guard_room_state()
        self.load_room(next_name)
        room = self.world_maps[next_name]
        room_map = room["map"]
        room_h = len(room_map) * TILE_SIZE
        room_w = len(room_map[0]) * TILE_SIZE if room_map else SCREEN_WIDTH

        pad = 50

        if direction == "east":
            open_y = self._find_opening_vertical(room_map, col=0)
            player.hitbox.centerx = pad
            player.hitbox.centery = open_y

        elif direction == "west":
            last_col = len(room_map[0]) - 1 if room_map else 19
            open_y = self._find_opening_vertical(room_map, col=last_col)
            player.hitbox.centerx = room_w - pad
            player.hitbox.centery = open_y

        elif direction == "south":
            open_x = self._find_opening_horizontal(room_map, row=0)
            player.hitbox.centerx = open_x
            player.hitbox.centery = pad

        elif direction == "north":
            last_row = len(room_map) - 1
            open_x = self._find_opening_horizontal(room_map, row=last_row)
            player.hitbox.centerx = open_x
            player.hitbox.centery = min(room_h, SCREEN_HEIGHT) - pad

        player.image_rect.midbottom = player.hitbox.midbottom

    def _find_opening_vertical(self, room_map, col):
        opens = []
        for ri, row in enumerate(room_map):
            if col < len(row) and row[col] == "0":
                opens.append(ri)
        if opens:
            mid = opens[len(opens) // 2]
            return mid * TILE_SIZE + TILE_SIZE // 2
        return len(room_map) * TILE_SIZE // 2

    def _find_opening_horizontal(self, room_map, row):
        if row < 0 or row >= len(room_map):
            return SCREEN_WIDTH // 2
        opens = []
        for ci, cell in enumerate(room_map[row]):
            if cell == "0":
                opens.append(ci)
        if opens:
            mid = opens[len(opens) // 2]
            return mid * TILE_SIZE + TILE_SIZE // 2
        return SCREEN_WIDTH // 2

    def get_current_room_name(self):
        return self.world_maps[self.current_room_name].get("name", self.current_room_name.title())

    def get_entry_desc(self):
        elapsed = pygame.time.get_ticks() - self.entry_desc_timer
        if elapsed < self.entry_desc_duration:
            return self.entry_desc, self.is_new_discovery
        return None, False

    def is_guard_room(self):
        return bool(self.world_maps[self.current_room_name].get("guard_room"))

    def is_villager_room(self):
        return bool(self.world_maps[self.current_room_name].get("villager_room"))

    def draw(self, surface):
        room = self.world_maps[self.current_room_name]
        region = room.get("region", "forest")

        # pick tileset based on regon type
        active_tileset = self.interior_tileset if region in ("house", "dungeon") else self.tileset_images

        if getattr(self, "map_layers", None) and len(self.map_layers) > 0:
            for layer in self.map_layers:
                for row_index, row in enumerate(layer):
                    for col_index, tile_id in enumerate(row):
                        if tile_id != "-1" and tile_id != "0": 
                            img = active_tileset.get(tile_id)
                            if img:
                                x = col_index * 40 
                                y = row_index * 40
                                surface.blit(img, (x, y))
        else:
            for ri, row in enumerate(room["map"]):
                for ci, cell in enumerate(row):
                    x = ci * TILE_SIZE
                    y = ri * TILE_SIZE
                    if cell == "0":
                        if region == "forest":
                            surface.blit(self.grass_image, (x, y))
                        elif region == "town":
                            pygame.draw.rect(surface, (130, 130, 130), (x, y, TILE_SIZE, TILE_SIZE))
                        elif region == "house":
                            pygame.draw.rect(surface, (139, 69, 19), (x, y, TILE_SIZE, TILE_SIZE))
                        else:
                            pygame.draw.rect(surface, (80, 80, 80), (x, y, TILE_SIZE, TILE_SIZE))
                                
            for wall in self.walls:
                if region == "forest":
                    pygame.draw.rect(surface, (34, 139, 34), wall)
                elif region == "town":
                    pygame.draw.rect(surface, (105, 105, 105), wall)
                elif region == "house":
                    pygame.draw.rect(surface, (160, 82, 45), wall)
                else:
                    pygame.draw.rect(surface, (60, 60, 60), wall)

        for obj in self.active_chests + self.active_items + self.active_npcs:
            obj.draw(surface)

        if self.active_guard:
            self.active_guard.draw(surface)

        for enemy in self.active_enemies:
            enemy.draw(surface)
