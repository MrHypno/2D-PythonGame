import pygame
import math

_ENEMY_SPRITES = {
    "bandit": {
        "idle":   "assets/Skeleton01_01_S_Idle.png",
        "walk":   "assets/Skeleton01_01_S_Walk.png",
        "attack": "assets/Skeleton01_01_S_Attack01.png",
        "frame_size": 48,
        "display_size": (64, 64),
    },
    "archer bandit": {
        "idle":   "assets/BrittleArcher.png",
        "walk":   "assets/BrittleArcher.png",
        "attack": "assets/BrittleArcher.png",
        "frame_size": 16,
        "display_size": (48, 48),
    },
    "bandit leader": {
        "idle":   "assets/bearzodiac_idle.png",
        "walk":   "assets/bearzodiac_walk.png",
        "attack": "assets/bearzodiac_attack.png",
        "frame_size": 48,
        "display_size": (128, 128),
    },
}

class Enemy:
    def __init__(self, x, y, name, hp, attack_power):
        self.name = name
        self.hp = hp
        self.max_vitality = hp
        self.attack_power = attack_power

        name_lower = name.lower()
        sprite_cfg = _ENEMY_SPRITES.get(name_lower)
        self._has_sprites = False
        self._frame_size = 48
        self.display_size = (64, 64)

        if sprite_cfg:
            self._frame_size = sprite_cfg["frame_size"]
            self.display_size = sprite_cfg["display_size"]
            try:
                self._idle_sheet = pygame.image.load(sprite_cfg["idle"]).convert_alpha()
                self._walk_sheet = pygame.image.load(sprite_cfg["walk"]).convert_alpha()
                self._attack_sheet = pygame.image.load(sprite_cfg["attack"]).convert_alpha()
                self._has_sprites = True
            except Exception:
                pass

        dw, dh = self.display_size
        self.image_rect = pygame.Rect(x, y, dw, dh)
        self.hitbox = pygame.Rect(x + (dw - 32) // 2, y + dh - 20, 32, 20)

        self.speed = 2
        self.detection_range = 260
        self.start_x = x
        self.patrol_range = 100
        self.direction = 1

        self.is_ranged = "archer" in name.lower()
        self.attack_range = 175 if self.is_ranged else 42

        self.is_hit = False
        self.hit_timer = 0
        self.last_attack_time = 0
        self.attack_cooldown = 800

        self.frame = 0.0
        self.animation_speed = 0.12
        self._chasing = False
        self._attacking = False
        self._facing_left = False

    def _get_sprite_frame(self, sheet, col):
        fs = self._frame_size
        rect = pygame.Rect(col * fs, 0, fs, fs)
        frame = sheet.subsurface(rect)
        scaled = pygame.transform.scale(frame, self.display_size)
        if self._facing_left:
            scaled = pygame.transform.flip(scaled, True, False)
        return scaled

    def update(self, player_hitbox, walls):
        dx = player_hitbox.centerx - self.hitbox.centerx
        dy = player_hitbox.centery - self.hitbox.centery
        dist = math.sqrt(dx**2 + dy**2)

        if dist < self.detection_range:
            self._chasing = True
            if dx < 0:
                self._facing_left = True
            elif dx > 0:
                self._facing_left = False

            # in atack range = play attack anim
            if dist <= self.attack_range:
                self._attacking = True
            else:
                self._attacking = False

            if dist > self.attack_range and dist != 0:
                self.speed = 3
                move_x = (dx / dist) * self.speed
                move_y = (dy / dist) * self.speed
                self.hitbox.x += move_x
                if self.hitbox.colliderect(player_hitbox):
                    self.hitbox.x -= move_x
                self.hitbox.y += move_y
                if self.hitbox.colliderect(player_hitbox):
                    self.hitbox.y -= move_y
        else:
            self._chasing = False
            self._attacking = False
            self.speed = 2
            self.hitbox.x += self.speed * self.direction
            if self.direction < 0:
                self._facing_left = True
            else:
                self._facing_left = False
            if abs(self.hitbox.x - self.start_x) > self.patrol_range:
                self.direction *= -1

        self.image_rect.midbottom = self.hitbox.midbottom

    def take_damage(self, amount):
        self.hp -= amount
        self.is_hit = True
        self.hit_timer = pygame.time.get_ticks()
        return self.hp <= 0

    def draw(self, surface):
        now = pygame.time.get_ticks()

        if self._has_sprites:
            # pick sheet based on state
            if self._attacking:
                sheet = self._attack_sheet
            elif self._chasing:
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
            elif self.is_ranged:
                color = (180, 80, 200)
            else:
                color = (200, 50, 50)

            if self.is_hit and now - self.hit_timer >= 150:
                self.is_hit = False

            pygame.draw.rect(surface, color, self.image_rect)

        bar_w = self.image_rect.width
        bar_h = 5
        bar_x = self.image_rect.left
        bar_y = self.image_rect.bottom + 3
        ratio = max(0, self.hp / self.max_vitality)

        pygame.draw.rect(surface, (120, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 50, 50), (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)
