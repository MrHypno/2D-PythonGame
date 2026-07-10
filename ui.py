import pygame
from item import ITEM_DATA, Item
from config import WHITE, BLACK

class DialogueBox:
    def __init__(self):
        self.active = False
        self.speaker = ""
        self.full_text = ""
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.char_speed = 30

        self.scale_x = 1.0
        self.scale_y = 1.0
        self._init_fonts()

    def _init_fonts(self):
        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        self._name_font = pygame.font.SysFont("arial", int(20*s), bold=True)
        self._text_font = pygame.font.SysFont("arial", int(18*s))
        self._hint_font = pygame.font.SysFont("arial", int(14*s))
        self._hint_surf = self._hint_font.render("Press E to continue", True, (160, 160, 160))

    def update_scale(self, scale_x, scale_y):
        if self.scale_x != scale_x or self.scale_y != scale_y:
            self.scale_x = scale_x
            self.scale_y = scale_y
            self._init_fonts()

    def show(self, speaker, text):
        self.active = True
        self.speaker = speaker
        self.full_text = text
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = pygame.time.get_ticks()

    def update(self):
        if not self.active:
            return
        now = pygame.time.get_ticks()
        if self.char_index < len(self.full_text):
            chars_to_add = max(1, (now - self.char_timer) // self.char_speed)
            self.char_index = min(self.char_index + chars_to_add, len(self.full_text))
            self.displayed_text = self.full_text[:self.char_index]
            self.char_timer = now

    def skip_or_close(self):
        if self.char_index < len(self.full_text):
            self.char_index = len(self.full_text)
            self.displayed_text = self.full_text
        else:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return

        sx = self.scale_x; sy = self.scale_y
        box_h = int(110 * sy)
        box_y = surface.get_height() - box_h - int(10 * sy)
        box_x = int(20 * sx)
        box_w = surface.get_width() - int(40 * sx)

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((10, 10, 30, 220))
        surface.blit(bg, (box_x, box_y))
        pygame.draw.rect(surface, (200, 180, 100), (box_x, box_y, box_w, box_h), max(1, int(2*sx)))

        name_surf = self._name_font.render(self.speaker, True, (255, 220, 100))
        surface.blit(name_surf, (box_x + int(14*sx), box_y + int(8*sy)))

        max_w = box_w - int(28*sx)
        words = self.displayed_text.split()
        lines, current = [], ""
        for word in words:
            test = (current + " " + word).strip()
            if self._text_font.size(test)[0] <= max_w:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        y = box_y + int(34*sy)
        for line in lines[:3]:
            txt = self._text_font.render(line, True, (230, 230, 230))
            surface.blit(txt, (box_x + int(14*sx), y))
            y += self._text_font.get_linesize()

        surface.blit(self._hint_surf, (box_x + box_w - self._hint_surf.get_width() - int(14*sx),
                                       box_y + box_h - int(22*sy)))


class UI:
    def __init__(self):
        self.scale_x = 1.0
        self.scale_y = 1.0
        self._init_fonts()

        self.show_inventory = False
        self.show_big_map = False

        self.feedback_msg = ""
        self.feedback_timer = 0
        self.feedback_duration = 2500

    def _init_fonts(self):
        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        self.font = pygame.font.SysFont("arial", int(22*s))
        self.small_font = pygame.font.SysFont("arial", int(18*s))
        self.title_font = pygame.font.SysFont("arial", int(32*s), bold=True)
        self.room_font = pygame.font.SysFont("arial", int(20*s), bold=True)
        self.mini_font = pygame.font.SysFont("arial", max(10, int(10*s)))

        self._inv_title = self.title_font.render("INVENTORY", True, (255, 215, 0))
        self._inv_hint = self.small_font.render("1/2/3 use  |  I close", True, (160, 160, 160))
        self._inv_empty = self.font.render("Your inventory is empty.", True, (140, 140, 140))
        self._ready_surf = self.small_font.render("READY", True, (100, 255, 100))

    def update_scale(self, scale_x, scale_y):
        if self.scale_x != scale_x or self.scale_y != scale_y:
            self.scale_x = scale_x
            self.scale_y = scale_y
            self._init_fonts()

    def show_feedback(self, message):
        self.feedback_msg = message
        self.feedback_timer = pygame.time.get_ticks()

    def toggle_inventory(self):
        self.show_inventory = not self.show_inventory

    def toggle_map(self):
        self.show_big_map = not self.show_big_map

    def draw_health_bar(self, surface, player):
        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        bx, by, bw, bh = int(20*sx), int(20*sy), int(200*sx), int(22*sy)
        ratio = max(0, player.vitality / player.max_vitality)

        pygame.draw.rect(surface, (180, 40, 40), (bx, by, bw, bh))
        pygame.draw.rect(surface, (50, 200, 50), (bx, by, int(bw * ratio), bh))
        pygame.draw.rect(surface, WHITE, (bx, by, bw, bh), 2)

        txt = self.font.render(f"Vitality  {player.vitality}/{player.max_vitality}", True, WHITE)
        surface.blit(txt, txt.get_rect(center=(bx + bw // 2, by + bh // 2)))

    def draw_armor_bar(self, surface, player):
        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        bx, by, bw, bh = int(20*sx), int(48*sy), int(200*sx), int(16*sy)
        ratio = player.current_armor / player.max_armor if player.max_armor else 0

        pygame.draw.rect(surface, (60, 60, 100), (bx, by, bw, bh))
        pygame.draw.rect(surface, (100, 140, 230), (bx, by, int(bw * ratio), bh))
        pygame.draw.rect(surface, (200, 200, 255), (bx, by, bw, bh), 2)

        txt = self.small_font.render(f"Armor  {player.current_armor}/{player.max_armor}", True, (200, 220, 255))
        surface.blit(txt, txt.get_rect(center=(bx + bw // 2, by + bh // 2)))

    def draw_cooldown(self, surface, player):
        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        bx, by, bw, bh = int(20*sx), int(70*sy), int(200*sx), int(10*sy)
        now = pygame.time.get_ticks()
        elapsed = now - player.last_attack_time
        ratio = min(1.0, elapsed / player.attack_cooldown)

        pygame.draw.rect(surface, (40, 40, 40), (bx, by, bw, bh))

        r = int(255 * (1 - ratio))
        g = int(255 * ratio)
        pygame.draw.rect(surface, (r, g, 50), (bx, by, int(bw * ratio), bh))
        pygame.draw.rect(surface, (120, 120, 120), (bx, by, bw, bh), 1)

    def draw_room_name(self, surface, level):
        pass

    def draw_entry_desc(self, surface, level):
        desc, is_new = level.get_entry_desc()

        elapsed = pygame.time.get_ticks() - level.entry_desc_timer
        remaining = level.entry_desc_duration - elapsed

        if remaining <= 0:
            return

        alpha = int(220 * min(1, remaining / 1000)) if remaining < 1000 else 220

        name = level.get_current_room_name()
        title_surf = self.title_font.render(name, True, (255, 230, 150))
        title_surf.set_alpha(alpha)
        sx = self.scale_x; sy = self.scale_y
        title_x = (surface.get_width() - title_surf.get_width()) // 2
        title_y = int(40 * sy)
        surface.blit(title_surf, (title_x, title_y))

        if is_new:
            discovery_surf = self.small_font.render("New Area Discovered!", True, (150, 255, 150))
            discovery_surf.set_alpha(alpha)
            disc_x = (surface.get_width() - discovery_surf.get_width()) // 2
            disc_y = title_y + title_surf.get_height() + int(5 * sy)
            surface.blit(discovery_surf, (disc_x, disc_y))

        if not desc:
            return

        max_w, padding_x, padding_y = int(600 * sx), int(12 * sx), int(12 * sy)
        lines, current = [], ""
        for word in desc.split():
            test = (current + " " + word).strip()
            if self.small_font.size(test)[0] <= max_w - padding_x * 2:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_h = self.small_font.get_linesize()
        bh = line_h * len(lines) + padding_y * 2
        bx = (surface.get_width() - max_w) // 2
        by = surface.get_height() - bh - int(70 * sy)

        bg = pygame.Surface((max_w, bh), pygame.SRCALPHA)
        bg.fill((0, 0, 0, min(alpha, 180)))
        surface.blit(bg, (bx, by))

        for i, line in enumerate(lines):
            txt = self.small_font.render(line, True, (230, 215, 170))
            txt.set_alpha(alpha)
            surface.blit(txt, (bx + padding_x, by + padding_y + i * line_h))

    def draw_inventory(self, surface, player):
        if not self.show_inventory:
            return

        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        iw, ih = int(420*sx), int(320*sy)
        ix = (surface.get_width() - iw) // 2
        iy = (surface.get_height() - ih) // 2

        bg = pygame.Surface((iw, ih), pygame.SRCALPHA)
        bg.fill((20, 20, 30, 210))
        surface.blit(bg, (ix, iy))
        pygame.draw.rect(surface, (200, 200, 200), (ix, iy, iw, ih), 2)

        surface.blit(self._inv_title, (ix + (iw - self._inv_title.get_width()) // 2, iy + int(14 * sy)))
        surface.blit(self._inv_hint, (ix + int(120 * sx), iy + int(52 * sy)))

        start_y = iy + int(82 * sy)
        if not player.inventory:
            surface.blit(self._inv_empty, (ix + int(30 * sx), start_y))
            return

        counts = {}
        for it in player.inventory:
            counts[it] = counts.get(it, 0) + 1

        Item._load_images()
        for idx, (name, count) in enumerate(counts.items()):
            data = ITEM_DATA.get(name, {})
            display = data.get("display_name", name.capitalize())
            effect = data.get("effect", {})
            color = data.get("color", (255, 215, 0))

            img = Item._images.get(name)
            if img:
                surface.blit(pygame.transform.scale(img, (int(20*sx), int(20*sy))), (ix + int(13 * sx), start_y + int(1 * sy)))
            else:
                pygame.draw.rect(surface, color, (ix + int(16 * sx), start_y + int(4 * sy), int(14 * sx), int(14 * sy)))
                pygame.draw.rect(surface, WHITE, (ix + int(16 * sx), start_y + int(4 * sy), int(14 * sx), int(14 * sy)), max(1, int(1*sx)))

            label = f"{idx + 1}. {display}" + (f"  (x{count})" if count > 1 else "")
            surface.blit(self.font.render(label, True, WHITE), (ix + int(36 * sx), start_y))

            if effect:
                eff_str = "  ".join(f"+{v} {k.upper()}" for k, v in effect.items())
                surface.blit(self.small_font.render(eff_str, True, (140, 230, 140)), (ix + int(36 * sx), start_y + int(22 * sy)))
            else:
                desc = data.get("desc", "")
                surface.blit(self.small_font.render(desc[:55] + ("…" if len(desc) > 55 else ""),
                                                    True, (160, 160, 160)),
                             (ix + int(36 * sx), start_y + int(22 * sy)))

            start_y += int(54 * sy)

    def draw_feedback(self, surface):
        if not self.feedback_msg:
            return

        elapsed = pygame.time.get_ticks() - self.feedback_timer
        if elapsed > self.feedback_duration:
            self.feedback_msg = ""
            return

        alpha = int(255 * ((self.feedback_duration - elapsed) / 800)) \
                if elapsed > self.feedback_duration - 800 else 255

        txt = self.font.render(self.feedback_msg, True, (255, 240, 100))
        txt.set_alpha(alpha)
        surface.blit(txt, (surface.get_width() // 2 - txt.get_width() // 2, surface.get_height() - int(46 * self.scale_y)))

    def draw_merchant(self, surface, player):
        sx = self.scale_x; sy = self.scale_y
        mw, mh = int(500*sx), int(340*sy)
        mx = (surface.get_width() - mw) // 2
        my = (surface.get_height() - mh) // 2

        bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
        bg.fill((20, 15, 30, 220))
        surface.blit(bg, (mx, my))
        pygame.draw.rect(surface, (200, 160, 50), (mx, my, mw, mh), max(1, int(3*sx)))

        title = self.title_font.render("MERCHANT", True, (255, 215, 0))
        surface.blit(title, (mx + (mw - title.get_width()) // 2, my + int(14*sy)))

        has_coin = "gold coin" in player.inventory

        if has_coin:
            surface.blit(self.font.render("You have a Gold Coin. Choose a trade:", True, WHITE),
                         (mx + int(20*sx), my + int(65*sy)))
            options = [
                ("1. Sharpen Sword   (+10 ATK)", (255, 180, 100)),
                ("2. Reinforced Armor (+50 Armor)", (100, 180, 255)),
                ("3. Vitality Elixir  (+50 Max Vitality)", (100, 240, 120)),
                ("4. Leave", (160, 160, 160)),
            ]
            for i, (text, color) in enumerate(options):
                surface.blit(self.font.render(text, True, color), (mx + int(40*sx), my + int(110*sy) + i * int(48*sy)))
        else:
            surface.blit(self.font.render("You have no Gold Coin. Come back later.", True, (200, 120, 120)),
                         (mx + int(30*sx), my + int(120*sy)))
            surface.blit(self.small_font.render("Press E to leave.", True, (160, 160, 160)),
                         (mx + int(30*sx), my + int(175*sy)))

    def draw_minimap(self, surface, level):
        positions = level.room_positions
        visited = level.visited_rooms
        current = level.current_room_name

        if not positions:
            return

        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        cell_w, cell_h = int(14*sx), int(10*sy)
        gap = max(1, int(2*s))
        step_x = cell_w + gap
        step_y = cell_h + gap

        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        map_w = (max_x - min_x + 1) * step_x + 12
        map_h = (max_y - min_y + 1) * step_y + 12
        base_x = surface.get_width() - map_w - 8
        base_y = surface.get_height() - map_h - 8

        bg = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (base_x, base_y))
        pygame.draw.rect(surface, (100, 100, 100), (base_x, base_y, map_w, map_h), 1)

        # adjacnt unexplored rooms
        adjacent_unvisited = set()
        for rname in visited:
            for d in ["north", "south", "east", "west"]:
                nxt = level.world_maps.get(rname, {}).get(d)
                if nxt and nxt not in visited and nxt in positions:
                    adjacent_unvisited.add(nxt)

        drawn_connections = set()
        for room_name, (gx, gy) in positions.items():
            if room_name not in visited:
                continue
            rx = base_x + 6 + (gx - min_x) * step_x
            ry = base_y + 6 + (gy - min_y) * step_y

            room_data = level.world_maps[room_name]
            for direction in ["east", "south", "west", "north"]:
                nxt = room_data.get(direction)
                if nxt and nxt in positions:
                    conn_key = tuple(sorted([room_name, nxt]))
                    if conn_key not in drawn_connections:
                        drawn_connections.add(conn_key)
                        nx = base_x + 6 + (positions[nxt][0] - min_x) * step_x
                        ny = base_y + 6 + (positions[nxt][1] - min_y) * step_y
                        line_color = (80, 80, 80) if nxt in visited else (50, 50, 50)
                        pygame.draw.line(surface, line_color,
                                         (rx + cell_w // 2, ry + cell_h // 2),
                                         (nx + cell_w // 2, ny + cell_h // 2), 1)

        for room_name, (gx, gy) in positions.items():
            if room_name not in visited and room_name not in adjacent_unvisited:
                continue
            rx = base_x + 6 + (gx - min_x) * step_x
            ry = base_y + 6 + (gy - min_y) * step_y

            if room_name not in visited:
                pygame.draw.rect(surface, (45, 45, 55), (rx, ry, cell_w, cell_h))
                pygame.draw.rect(surface, (70, 70, 80), (rx, ry, cell_w, cell_h), 1)
                continue

            if room_name == current:
                color = (255, 220, 80)
            elif level.world_maps[room_name].get("enemies"):
                color = (180, 80, 80) if room_name not in level.cleared_enemy_rooms else (80, 160, 80)
            else:
                color = (100, 120, 160)

            pygame.draw.rect(surface, color, (rx, ry, cell_w, cell_h))
            pygame.draw.rect(surface, (200, 200, 200), (rx, ry, cell_w, cell_h), 1)

    def draw_big_map(self, surface, level):
        if not self.show_big_map:
            return

        positions = level.room_positions
        visited = level.visited_rooms
        current = level.current_room_name

        adjacent_unvisited = set()
        for rname in visited:
            for d in ["north", "south", "east", "west"]:
                nxt = level.world_maps.get(rname, {}).get(d)
                if nxt and nxt not in visited and nxt in positions:
                    adjacent_unvisited.add(nxt)

        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        sx = self.scale_x; sy = self.scale_y; s = min(sx, sy)
        cell_w, cell_h = int(36*sx), int(24*sy)
        gap = max(1, int(6*s))
        step_x = cell_w + gap
        step_y = cell_h + gap

        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        total_w = (max_x - min_x + 1) * step_x
        total_h = (max_y - min_y + 1) * step_y
        base_x = (surface.get_width() - total_w) // 2
        base_y = (surface.get_height() - total_h) // 2

        title = self.room_font.render("MAP  (Tab to close)", True, (255, 230, 150))
        title_y = max(6, base_y - 36)
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, title_y))

        drawn_connections = set()
        for room_name, (gx, gy) in positions.items():
            if room_name not in visited:
                continue
            rx = base_x + (gx - min_x) * step_x
            ry = base_y + (gy - min_y) * step_y
            room_data = level.world_maps[room_name]
            for direction in ["east", "south", "west", "north"]:
                nxt = room_data.get(direction)
                if nxt and nxt in positions:
                    conn_key = tuple(sorted([room_name, nxt]))
                    if conn_key not in drawn_connections:
                        drawn_connections.add(conn_key)
                        nx = base_x + (positions[nxt][0] - min_x) * step_x
                        ny = base_y + (positions[nxt][1] - min_y) * step_y
                        line_color = (120, 120, 120) if nxt in visited else (65, 65, 75)
                        pygame.draw.line(surface, line_color,
                                         (rx + cell_w // 2, ry + cell_h // 2),
                                         (nx + cell_w // 2, ny + cell_h // 2), 2)

        for room_name, (gx, gy) in positions.items():
            if room_name not in visited and room_name not in adjacent_unvisited:
                continue

            rx = base_x + (gx - min_x) * step_x
            ry = base_y + (gy - min_y) * step_y

            if room_name not in visited:
                pygame.draw.rect(surface, (45, 45, 58), (rx, ry, cell_w, cell_h))
                pygame.draw.rect(surface, (75, 75, 90), (rx, ry, cell_w, cell_h), 1)
                q = self.mini_font.render("?", True, (100, 100, 120))
                surface.blit(q, (rx + cell_w // 2 - q.get_width() // 2,
                                  ry + cell_h // 2 - q.get_height() // 2))
                continue

            if room_name == current:
                color = (255, 220, 80)
            elif level.world_maps[room_name].get("enemies"):
                color = (180, 80, 80) if room_name not in level.cleared_enemy_rooms else (80, 160, 80)
            else:
                color = (80, 110, 160)

            pygame.draw.rect(surface, color, (rx, ry, cell_w, cell_h))
            pygame.draw.rect(surface, (220, 220, 220), (rx, ry, cell_w, cell_h), 1)

            short = level.world_maps[room_name].get("name", room_name)[:6]
            label = self.mini_font.render(short, True, WHITE)
            surface.blit(label, (rx + cell_w // 2 - label.get_width() // 2,
                                  ry + cell_h // 2 - label.get_height() // 2))

    def draw(self, surface, player, level):
        self.draw_health_bar(surface, player)
        self.draw_armor_bar(surface, player)
        self.draw_cooldown(surface, player)
        self.draw_room_name(surface, level)
        self.draw_entry_desc(surface, level)
        self.draw_inventory(surface, player)
        self.draw_feedback(surface)
        self.draw_minimap(surface, level)
        self.draw_big_map(surface, level)
