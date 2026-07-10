from config import ASSETS_DIR
import os
import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

_FONT_CACHE = {}
def get_sys_font(name, size, bold=False):
    key = (name, size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(name, size, bold=bold)
    return _FONT_CACHE[key]

KING_COLOR = (220, 180, 50)
KING_OUTLINE = (255, 230, 100)
FOLLOW_DIST = 80
KING_SPEED = 2.5

# loads individual frame files into a list
def _load_frame_files(pattern, count=4, size=32, display=(64, 64)):
    frames = []
    for i in range(1, count + 1):
        path = pattern.replace("*", str(i))
        try:
            img = pygame.image.load(path).convert_alpha()
            frames.append(pygame.transform.scale(img, display))
        except Exception:
            pass
    return frames

class King:
    def __init__(self, x, y):
        self.max_vitality = 80
        self.vitality = 80
        self.is_alive = True

        self.display_size = (64, 64)
        self.image_rect = pygame.Rect(x, y, 64, 64)
        self.hitbox = pygame.Rect(x + 16, y + 44, 32, 20)

        self.is_hit = False
        self.hit_timer = 0
        self.hit_cooldown = 800

        self._label_font = pygame.font.SysFont("arial", 13, bold=True)
        self._bar_font = pygame.font.SysFont("arial", 13)
        self._label_surf = self._label_font.render("KING", True, (255, 255, 255))

        self._frames = _load_frame_files(f"{ASSETS_DIR}/HighElf_M_Idle + Walk_*.png", 4, 32, self.display_size)
        self._has_sprites = len(self._frames) > 0
        self._frame_idx = 0.0
        self._anim_speed = 0.08
        self._facing_left = False

    def update(self, player_hitbox, walls):
        dx = player_hitbox.centerx - self.hitbox.centerx
        dy = player_hitbox.centery - self.hitbox.centery
        dist = math.sqrt(dx**2 + dy**2)

        if dist > FOLLOW_DIST:
            if dx < 0:
                self._facing_left = True
            elif dx > 0:
                self._facing_left = False
            move_x = (dx / dist) * KING_SPEED
            move_y = (dy / dist) * KING_SPEED

            self.hitbox.x += move_x
            for wall in walls:
                if self.hitbox.colliderect(wall):
                    if move_x > 0: self.hitbox.right = wall.left
                    if move_x < 0: self.hitbox.left = wall.right

            self.hitbox.y += move_y
            for wall in walls:
                if self.hitbox.colliderect(wall):
                    if move_y > 0: self.hitbox.bottom = wall.top
                    if move_y < 0: self.hitbox.top = wall.bottom

        self.image_rect.midbottom = self.hitbox.midbottom

    def take_damage(self, amount):
        if self.is_hit:
            return
        self.vitality -= amount
        self.is_hit = True
        self.hit_timer = pygame.time.get_ticks()
        if self.vitality <= 0:
            self.vitality = 0
            self.is_alive = False

    def on_room_change(self, player_hitbox):
        self.hitbox.centerx = player_hitbox.centerx - 50
        self.hitbox.centery = player_hitbox.centery
        self.image_rect.midbottom = self.hitbox.midbottom

    def draw(self, surface):
        if self._has_sprites:
            self._frame_idx = (self._frame_idx + self._anim_speed) % len(self._frames)
            sprite = self._frames[int(self._frame_idx)]
            if self._facing_left:
                sprite = pygame.transform.flip(sprite, True, False)

            if self.is_hit:
                elapsed = pygame.time.get_ticks() - self.hit_timer
                if elapsed < 400:
                    tinted = sprite.copy()
                    tinted.fill((255, 80, 80, 100), special_flags=pygame.BLEND_RGBA_MULT)
                    surface.blit(tinted, self.image_rect)
                else:
                    self.is_hit = False
                    surface.blit(sprite, self.image_rect)
            else:
                surface.blit(sprite, self.image_rect)
        else:
            if self.is_hit:
                elapsed = pygame.time.get_ticks() - self.hit_timer
                color = (220, 60, 60) if elapsed < 400 else KING_COLOR
                if elapsed >= 400:
                    self.is_hit = False
            else:
                color = KING_COLOR

            pygame.draw.rect(surface, color, self.image_rect)
            pygame.draw.rect(surface, KING_OUTLINE, self.image_rect, 2)

    def draw_hp_bar(self, surface, sx=1.0, sy=1.0):
        bar_x, bar_y = surface.get_width() - int(220*sx), int(50*sy)
        bar_w, bar_h = int(200*sx), max(1, int(16*sy))
        ratio = max(0, self.vitality / self.max_vitality)

        pygame.draw.rect(surface, (120, 80, 0), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 180, 50), (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surface, (255, 230, 100), (bar_x, bar_y, bar_w, bar_h), max(1, int(2*sx)))

        font = get_sys_font("arial", max(1, int(16 * min(sx, sy))), bold=True)
        txt = font.render(f"King Vitality  {self.vitality}/{self.max_vitality}", True, (255, 240, 180))
        surface.blit(txt, txt.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2)))


RIDDLE_POOL = [
    {"q": "If you speak my name, you break me. What am I?",
     "a": ["silence"]},
    {"q": "I have cities but no houses, mountains but no trees, water but no fish. What am I?",
     "a": ["map"]},
    {"q": "The more you take, the more you leave behind. What are they?",
     "a": ["footsteps", "steps"]},
    {"q": "The maker doesn't want it; the buyer doesn't use it; the user doesn't see it. What is it?",
     "a": ["coffin"]},
    {"q": "If you have me, you want to share me. If you share me, you haven't got me. What am I?",
     "a": ["secret"]},
]

class Guard:
    GATE_LOCK_Y = 30

    def __init__(self, x, y, is_riddle_guard=False):
        self.is_riddle_guard = is_riddle_guard
        self.display_size = (64, 64)
        self.image_rect = pygame.Rect(x, y, 64, 64)
        self.hitbox = pygame.Rect(x + 16, y + 44, 32, 20)

        self.riddle = random.choice(RIDDLE_POOL)
        self.mistakes = 0
        self.is_hostile = False
        self.gate_open = False
        self.asked_already = False

        self.attack_power = 20
        self.speed = 2
        self.start_x = x
        self.hp = 120
        self.max_vitality = 120
        self.last_attack_time = 0
        self.attack_cooldown = 800

        self.is_hit = False
        self.hit_timer = 0

        self._font = pygame.font.SysFont("arial", 13, bold=True)
        self._label_surf = self._font.render("GUARD", True, (255, 255, 255))
        self._color = (100, 120, 200)

        self.frame = 0.0
        self.animation_speed = 0.12
        self._facing_left = False
        self._attacking = False
        self.attack_range = 42
        if is_riddle_guard:
            prefix = "gladius"
            self._frame_size = 32
        else:
            prefix = "demorden"
            self._frame_size = 32
        try:
            self._idle_sheet = pygame.image.load(f"{ASSETS_DIR}/{prefix}_idle.png").convert_alpha()
            self._walk_sheet = pygame.image.load(f"{ASSETS_DIR}/{prefix}_walk.png").convert_alpha()
            self._attack_sheet = pygame.image.load(f"{ASSETS_DIR}/{prefix}_attack.png").convert_alpha()
            self._has_sprites = True
        except Exception:
            self._has_sprites = False

    def check_approach(self, player_hitbox):
        if self.gate_open or self.asked_already or self.is_hostile:
            return False
        dist_x = abs(player_hitbox.centerx - self.hitbox.centerx)
        dist_y = abs(player_hitbox.centery - self.hitbox.centery)
        return dist_x < 80 and dist_y < 80

    def answer(self, text):
        if text.strip().lower() in self.riddle["a"]:
            self.gate_open = True
            self.asked_already = True
            return "correct"

        self.mistakes += 1
        if self.mistakes >= 3:
            self.is_hostile = True
            self.asked_already = True
            return "failed"
        return "wrong"

    def update(self, player_hitbox, walls):
        if not self.is_hostile:
            return

        dx = player_hitbox.centerx - self.hitbox.centerx
        dy = player_hitbox.centery - self.hitbox.centery
        dist = math.sqrt(dx**2 + dy**2)

        if dist > 0:
            if dx < 0:
                self._facing_left = True
            elif dx > 0:
                self._facing_left = False

            # switch to atack anim when close enough
            self._attacking = dist <= self.attack_range

            move_x = (dx / dist) * self.speed
            move_y = (dy / dist) * self.speed

            self.hitbox.x += move_x
            for wall in walls:
                if self.hitbox.colliderect(wall):
                    if move_x > 0: self.hitbox.right = wall.left
                    else: self.hitbox.left = wall.right

            self.hitbox.y += move_y
            for wall in walls:
                if self.hitbox.colliderect(wall):
                    if move_y > 0: self.hitbox.bottom = wall.top
                    else: self.hitbox.top = wall.bottom

        self.image_rect.midbottom = self.hitbox.midbottom

    def take_damage(self, amount):
        self.hp -= amount
        self.is_hit = True
        self.hit_timer = pygame.time.get_ticks()
        return self.hp <= 0

    def _get_sprite_frame(self, sheet, col):
        fs = self._frame_size
        rect = pygame.Rect(col * fs, 0, fs, fs)
        frame = sheet.subsurface(rect)
        scaled = pygame.transform.scale(frame, self.display_size)
        if self._facing_left:
            scaled = pygame.transform.flip(scaled, True, False)
        return scaled

    def draw(self, surface):
        now = pygame.time.get_ticks()
        if self._has_sprites:
            # pick sheet: attack only when in range
            if self.is_hostile and self._attacking:
                sheet = self._attack_sheet
            elif self.is_hostile:
                sheet = self._walk_sheet
            else:
                sheet = self._idle_sheet
            num_cols = sheet.get_width() // self._frame_size
            self.frame = (self.frame + self.animation_speed) % num_cols
            sprite = self._get_sprite_frame(sheet, int(self.frame))

            if self.is_hit and now - self.hit_timer < 150:
                tinted = sprite.copy()
                tinted.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(tinted, self.image_rect)
            else:
                if self.is_hit and now - self.hit_timer >= 150:
                    self.is_hit = False
                surface.blit(sprite, self.image_rect)
        else:
            if self.is_hit and now - self.hit_timer < 150:
                color = (255, 255, 255)
            elif self.is_hostile:
                color = (180, 50, 50)
            else:
                color = self._color
            if self.is_hit and now - self.hit_timer >= 150:
                self.is_hit = False
            pygame.draw.rect(surface, color, self.image_rect)
            pygame.draw.rect(surface, (255, 255, 255), self.image_rect, 2)

        # label moved to draw_ui

    def draw_ui(self, surface, sx=1.0, sy=1.0):
        font = get_sys_font("arial", max(1, int(13 * min(sx, sy))), bold=True)
        label_surf = font.render("GUARD", True, (255, 255, 255))
        lx = int(self.image_rect.centerx * sx) - label_surf.get_width() // 2
        ly = int((self.image_rect.top - 18) * sy)
        surface.blit(label_surf, (lx, ly))

        if self.is_hostile:
            bar_w = int(self.image_rect.width * sx)
            bar_h = max(1, int(5 * sy))
            bar_x = int(self.image_rect.left * sx)
            bar_y = int((self.image_rect.bottom + 3) * sy)
            ratio = max(0, self.hp / self.max_vitality)

            pygame.draw.rect(surface, (120, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (220, 50, 50), (bar_x, bar_y, int(bar_w * ratio), bar_h))
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), max(1, int(1*sx)))


NPC_COLORS = {
    "merchant": (200, 160, 50),
    "knight": (100, 120, 200),
    "villager": (160, 120, 80),
}
NPC_LABELS = {
    "merchant": "Merchant",
    "knight": "Knight",
    "villager": "Villager",
}

VILLAGER_DIALOGUES = {
    "hero": [
        "You killed the Bandit Leader! You are our hero!",
        "We are finally free! Please, take whatever you need.",
        "I knew you were a savior the moment I saw you!",
        "The King will surely reward you for this!",
    ],
    "suspicious": [
        "Get out! You look just like those bandits!",
        "Did you kill the knights? Stay away from my family!",
        "I don't trust you. You have blood on your hands.",
        "Don't hurt me! Take what you want and leave!",
    ],
    "info": [
        "I saw smoke rising from the deep forest. The bandit camp must be there.",
        "The Mayor hid something in the archives before he fled. But it's locked.",
        "Be careful on the cliffs. The ground is unstable.",
        "I heard the merchant in the town square likes gold coins.",
        "Those bandits... they have heavy armor. You'll need a strong weapon.",
    ],
    "friendly": [
        "Please help us... We have no food left.",
        "May the gods protect you, traveler.",
        "It's dangerous to go alone. Watch your back.",
        "If you see the King, tell him we are still loyal.",
    ],
    "attack": "I won't let you hurt anyone else! DIE TRAITOR!",
}

class NPC:
    def __init__(self, x, y, npc_type):
        self.npc_type = npc_type
        self.color = NPC_COLORS.get(npc_type, (180, 180, 180))
        self.label = NPC_LABELS.get(npc_type, npc_type.capitalize())

        self._has_sprites = False
        self._has_sheet = False
        self._frame_size = 32
        self.display_size = (64, 64)
        self._sprite_frame = 0.0
        self._sprite_anim_speed = 0.12
        self._facing_left = False
        self._ind_frames = []

        # knight uses spritesheet, villager/merchant use individual frames
        if npc_type == "knight":
            try:
                self._idle_sheet = pygame.image.load(f"{ASSETS_DIR}/demorden_idle.png").convert_alpha()
                self._walk_sheet = pygame.image.load(f"{ASSETS_DIR}/demorden_walk.png").convert_alpha()
                self._attack_sheet = pygame.image.load(f"{ASSETS_DIR}/demorden_attack.png").convert_alpha()
                self._has_sheet = True
                self._has_sprites = True
            except Exception:
                pass
        elif npc_type == "villager":
            self._ind_frames = _load_frame_files(f"{ASSETS_DIR}/NormalCleric_Idle + Walk_*.png", 4, 32, self.display_size)
            if self._ind_frames:
                self._has_sprites = True
        elif npc_type == "merchant":
            self._ind_frames = _load_frame_files(f"{ASSETS_DIR}/Wizard_Idle + Walk_*.png", 4, 32, self.display_size)
            if self._ind_frames:
                self._has_sprites = True

        if self._has_sprites:
            dw, dh = self.display_size
            self.image_rect = pygame.Rect(x, y, dw, dh)
            self.hitbox = pygame.Rect(x + 16, y + 44, 32, 20)
        else:
            self.image_rect = pygame.Rect(x, y, 32, 48)
            self.hitbox = pygame.Rect(x, y + 28, 32, 20)

        self._font = pygame.font.SysFont("arial", 14, bold=True)
        self._label_surf = self._font.render(self.label, True, (255, 255, 255))

        self.dialogue = ""
        self.is_hostile = False
        self.attack_power = 5
        self.hp = 30
        self.max_vitality = 30
        self.is_hit = False
        self.hit_timer = 0
        self.last_attack_time = 0
        self.attack_cooldown = 800
        self._talked = False

    def trigger_villager(self, bandit_camp_cleared):
        if self.npc_type != "villager" or self._talked:
            return "", False

        self._talked = True

        if bandit_camp_cleared:
            self.dialogue = random.choice(VILLAGER_DIALOGUES["hero"])
            return self.dialogue, False

        # random roll decides villager reacton
        roll = random.randint(1, 100)

        if roll <= 10:
            self.dialogue = VILLAGER_DIALOGUES["attack"]
            self.is_hostile = True
            return self.dialogue, True
        elif roll <= 40:
            self.dialogue = random.choice(VILLAGER_DIALOGUES["suspicious"])
        elif roll <= 70:
            self.dialogue = random.choice(VILLAGER_DIALOGUES["info"])
        else:
            self.dialogue = random.choice(VILLAGER_DIALOGUES["friendly"])

        return self.dialogue, False

    def take_damage(self, amount):
        self.hp -= amount
        self.is_hit = True
        self.hit_timer = pygame.time.get_ticks()
        return self.hp <= 0

    def update(self, player_hitbox):
        if not self.is_hostile:
            return
        dx = player_hitbox.centerx - self.hitbox.centerx
        dy = player_hitbox.centery - self.hitbox.centery
        dist = math.sqrt(dx**2 + dy**2) or 1
        # updaet face direction when chasing
        if dx < 0:
            self._facing_left = True
        elif dx > 0:
            self._facing_left = False
        self.hitbox.x += (dx / dist) * 1.5
        self.hitbox.y += (dy / dist) * 1.5
        self.image_rect.midbottom = self.hitbox.midbottom

    def _get_sprite_frame(self, sheet, col):
        fs = self._frame_size
        rect = pygame.Rect(col * fs, 0, fs, fs)
        frame = sheet.subsurface(rect)
        scaled = pygame.transform.scale(frame, self.display_size)
        if self._facing_left:
            scaled = pygame.transform.flip(scaled, True, False)
        return scaled

    def draw(self, surface):
        now = pygame.time.get_ticks()

        if self._has_sprites and self._has_sheet:
            if self.is_hostile:
                sheet = self._attack_sheet
            else:
                sheet = self._idle_sheet
            num_cols = sheet.get_width() // self._frame_size
            self._sprite_frame = (self._sprite_frame + self._sprite_anim_speed) % num_cols
            sprite = self._get_sprite_frame(sheet, int(self._sprite_frame))

            if self.is_hit and now - self.hit_timer < 150:
                tinted = sprite.copy()
                tinted.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(tinted, self.image_rect)
            else:
                if self.is_hit and now - self.hit_timer >= 150:
                    self.is_hit = False
                surface.blit(sprite, self.image_rect)
        elif self._has_sprites and self._ind_frames:
            self._sprite_frame = (self._sprite_frame + self._sprite_anim_speed) % len(self._ind_frames)
            sprite = self._ind_frames[int(self._sprite_frame)]
            if self._facing_left:
                sprite = pygame.transform.flip(sprite, True, False)

            if self.is_hit and now - self.hit_timer < 150:
                tinted = sprite.copy()
                tinted.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(tinted, self.image_rect)
            else:
                if self.is_hit and now - self.hit_timer >= 150:
                    self.is_hit = False
                surface.blit(sprite, self.image_rect)
        else:
            if self.is_hit and now - self.hit_timer < 150:
                color = (255, 255, 255)
            elif self.is_hostile:
                color = (180, 50, 50)
            else:
                color = self.color

            if self.is_hit and now - self.hit_timer >= 150:
                self.is_hit = False

            pygame.draw.rect(surface, color, self.image_rect)
            pygame.draw.rect(surface, (255, 255, 255), self.image_rect, 2)

        # label moved to draw_ui

    def draw_ui(self, surface, sx=1.0, sy=1.0):
        font = get_sys_font("arial", max(1, int(13 * min(sx, sy))), bold=True)
        label_surf = font.render(getattr(self, 'label', 'GUARD'), True, (255, 255, 255))
        lx = int(self.image_rect.centerx * sx) - label_surf.get_width() // 2
        ly = int((self.image_rect.top - 18) * sy)
        surface.blit(label_surf, (lx, ly))

        if self.is_hostile:
            bar_w = int(self.image_rect.width * sx)
            bar_h = max(1, int(5 * sy))
            bar_x = int(self.image_rect.left * sx)
            bar_y = int((self.image_rect.bottom + 3) * sy)
            ratio = max(0, self.hp / self.max_vitality)

            pygame.draw.rect(surface, (120, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (220, 50, 50), (bar_x, bar_y, int(bar_w * ratio), bar_h))
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), max(1, int(1*sx)))
