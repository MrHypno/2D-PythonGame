import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class Projectile:
    def __init__(self, x, y, target_x, target_y, damage):
        self.rect   = pygame.Rect(x, y, 8, 8)
        self.damage = damage
        speed       = 8

        self.fx = float(x)
        self.fy = float(y)

        dx   = target_x - x
        dy   = target_y - y
        dist = math.sqrt(dx**2 + dy**2) or 1
        self.vx = (dx / dist) * speed
        self.vy = (dy / dist) * speed

    def update(self, walls):
        self.fx += self.vx
        self.fy += self.vy
        self.rect.x = int(self.fx)
        self.rect.y = int(self.fy)

        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or \
           self.rect.bottom < 0 or self.rect.top  > SCREEN_HEIGHT:
            return True

        for wall in walls:
            if self.rect.colliderect(wall):
                return True

        return False

    def draw(self, surface):
        pygame.draw.ellipse(surface, (255, 200, 50), self.rect)


class Player:
    def __init__(self, x, y, name, hp, attack_power):
        self.name = name
        self.max_vitality = hp
        self.vitality = hp
        self.attack_power = attack_power
        self.is_alive = True
        self.inventory = []

        self.max_armor = 50
        self.current_armor = 0

        self.full_sheet = pygame.image.load("assets/player.png").convert_alpha()
        self.frame_width = 48
        self.frame_height = 48
        self.display_size = (80, 80)
        self.image = self._get_frame(0, 0)

        self.image_rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = pygame.Rect(x, y + 40, 40, 30)

        self.speed = 5
        self.frame = 0.0
        self.animation_speed = 0.15
        self.direction = "down"

        self.last_attack_time = 0
        self.attack_cooldown = 500

        self.is_hit = False
        self.hit_timer = 0

        self.projectiles = []
        self.sword_swing = [
            pygame.mixer.Sound("assets/sounds/sword_attack_1.wav"),
            pygame.mixer.Sound("assets/sounds/sword_attack_2.wav")
        ]
        self.sword_hit = pygame.mixer.Sound("assets/sounds/sword_hit.wav")

    def _get_frame(self, col, row):
        rect  = pygame.Rect(col * self.frame_width, row * self.frame_height,
                            self.frame_width, self.frame_height)
        frame = self.full_sheet.subsurface(rect)
        return pygame.transform.scale(frame, self.display_size)

    def animate(self, is_moving):
        if self.direction == "up":
            dir_offset = 2
        elif self.direction in ["right", "left"]:
            dir_offset = 1
        else:
            dir_offset = 0

        now = pygame.time.get_ticks()
        is_attacking = (now - self.last_attack_time < 300) and not isinstance(self, Archer)

        if is_attacking:
            row = 6 + dir_offset
            elapsed = now - self.last_attack_time
            frame_idx = int((elapsed / 300.0) * 4) % 4
            frame = self._get_frame(frame_idx, row)
        elif is_moving:
            row = 3 + dir_offset
            self.frame = (self.frame + self.animation_speed) % 6
            frame = self._get_frame(int(self.frame), row)
        else:
            row = 0 + dir_offset
            self.frame = (self.frame + self.animation_speed * 0.5) % 6
            frame = self._get_frame(int(self.frame), row)

        if self.direction == "left":
            frame = pygame.transform.flip(frame, True, False)

        self.image = frame

    def move(self, dx, dy, walls):
        if dx > 0: self.direction = "right"
        elif dx < 0: self.direction = "left"
        elif dy > 0: self.direction = "down"
        elif dy < 0: self.direction = "up"

        self.hitbox.x += dx
        for wall in walls:
            if self.hitbox.colliderect(wall):
                if dx > 0: self.hitbox.right = wall.left
                if dx < 0: self.hitbox.left  = wall.right

        self.hitbox.y += dy
        for wall in walls:
            if self.hitbox.colliderect(wall):
                if dy > 0: self.hitbox.bottom = wall.top
                if dy < 0: self.hitbox.top    = wall.bottom

        self.image_rect.midbottom = self.hitbox.midbottom

    def take_damage(self, amount):
        if self.is_hit:
            return

        if self.current_armor >= amount:
            self.current_armor -= amount
        elif self.current_armor > 0:
            amount -= self.current_armor
            self.current_armor = 0
            self.vitality -= amount
        else:
            self.vitality -= amount

        if self.vitality <= 0:
            self.vitality = 0
            self.is_alive = False

        self.is_hit    = True
        self.hit_timer = pygame.time.get_ticks()

    def heal(self, amount):
        if self.vitality < self.max_vitality:
            self.vitality = min(self.vitality + amount, self.max_vitality)
            return True
        return False

    def repair_armor(self, amount):
        if self.current_armor < self.max_armor:
            self.current_armor = min(self.current_armor + amount, self.max_armor)
            return True
        return False

    def get_unique_items(self):
        seen = []
        for item in self.inventory:
            if item not in seen:
                seen.append(item)
        return seen

    def use_item(self, item_name):
        from item import ITEM_DATA
        if item_name not in self.inventory:
            return False, "You don't have that item."

        data   = ITEM_DATA.get(item_name)
        if not data:
            return False, f"Unknown item: {item_name}"

        effect = data.get("effect", {})
        if not effect:
            return False, f"You can't use the {data['display_name']} like that."

        used, msg = False, ""

        if "heal" in effect:
            used = self.heal(effect["heal"])
            msg  = f"+{effect['heal']} Vitality!" if used else "Already at full vitality."
        elif "armor" in effect:
            used = self.repair_armor(effect["armor"])
            msg  = f"+{effect['armor']} Armor!" if used else "Armor is already full."
        elif "attack" in effect:
            self.attack_power += effect["attack"]
            used, msg = True, f"+{effect['attack']} Attack Power!"
        elif "max_vitality" in effect:
            self.max_vitality += effect["max_vitality"]
            self.heal(effect["max_vitality"])
            used, msg = True, f"+{effect['max_vitality']} Max Vitality!"

        if used:
            self.inventory.remove(item_name)
        return used, msg

    def attack(self, enemies, mouse_pos=None, walls=None):
        attack_rect = self.hitbox.inflate(40, 40)
        hit_anything = False
        for enemy in enemies[:]:
            if attack_rect.colliderect(enemy.hitbox):
                hit_anything = True
                if enemy.take_damage(self.attack_power):
                    enemies.remove(enemy)
        return hit_anything

    def update_projectiles(self, enemies, walls, guard=None, npcs=None):
        pass

    def draw(self, surface):
        if self.is_hit and pygame.time.get_ticks() - self.hit_timer < 200:
            temp = self.image.copy()
            temp.fill((255, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(temp, self.image_rect)
        else:
            self.is_hit = False
            surface.blit(self.image, self.image_rect)


class Knight(Player):
    def __init__(self, x, y):
        super().__init__(x, y, "Knight", hp=100, attack_power=20)
        self.attack_cooldown = 600

    def attack(self, enemies, mouse_pos=None, walls=None):
        hit_enemy = super().attack(enemies)
        current_sound = random.choice(self.sword_swing)
        current_sound.set_volume(0.75)
        current_sound.play()
        if hit_enemy:
            self.sword_hit.set_volume(0.5)
            self.sword_hit.play()


class Archer(Player):
    def __init__(self, x, y):
        super().__init__(x, y, "Archer", hp=70, attack_power=25)
        self.attack_cooldown = 400
        self.bow_attack = pygame.mixer.Sound("assets/sounds/bow_attack.wav")
        self.bow_hit = pygame.mixer.Sound("assets/sounds/bow_hit.wav")

    def attack(self, enemies, mouse_pos=None, walls=None):
        if not mouse_pos:
            return
        self.projectiles.append(
            Projectile(self.hitbox.centerx, self.hitbox.centery,
                       mouse_pos[0], mouse_pos[1], self.attack_power)
        )
        self.bow_attack.set_volume(0.75)
        self.bow_attack.play()

    def update_projectiles(self, enemies, walls, guard=None, npcs=None):
        for proj in self.projectiles[:]:
            dead = proj.update(walls)
            if not dead:
                for enemy in enemies[:]:
                    if proj.rect.colliderect(enemy.hitbox):
                        self.bow_hit.set_volume(0.5)
                        self.bow_hit.play()
                        if enemy.take_damage(self.attack_power):
                            enemies.remove(enemy)
                        dead = True
                        break
            if not dead and guard and guard.is_hostile:
                if proj.rect.colliderect(guard.image_rect):
                    self.bow_hit.set_volume(0.5)
                    self.bow_hit.play()
                    guard.take_damage(self.attack_power)
                    dead = True
            if not dead and npcs:
                for npc in npcs[:]:
                    if npc.is_hostile and proj.rect.colliderect(npc.image_rect):
                        self.bow_hit.set_volume(0.5)
                        self.bow_hit.play()
                        if npc.take_damage(self.attack_power):
                            npcs.remove(npc)
                        dead = True
                        break
            if dead:
                self.projectiles.remove(proj)

    def draw(self, surface):
        for proj in self.projectiles:
            proj.draw(surface)
        super().draw(surface)
