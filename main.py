import pygame, sys
import math
#import random
from config import *
from player import Knight, Archer
from level import Level
from ui import UI, DialogueBox
from characters import King
from button_mapping import ButtonMapping
from save_system import save_game, load_game, has_save

pygame.init()
pygame.mixer.init()
pygame.joystick.init()
screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Save the King!")
clock = pygame.time.Clock()
is_fullscreen = False

chest_open = pygame.mixer.Sound("assets/sounds/chest_open.wav")

ui_scale_x = 1.0
ui_scale_y = 1.0

def _get_font(name, size, bold=False):
    return pygame.font.SysFont(name, max(1, int(size * min(ui_scale_x, ui_scale_y))), bold=bold)

title_font = lambda: _get_font("arial", 64, bold=True)
menu_font  = lambda: _get_font("arial", 32)
small_font = lambda: _get_font("arial", 20)
input_font = lambda: _get_font("arial", 24)
inputs = ButtonMapping()

def draw_text(text, font, color, x, y, center_x=False):
    sx, sy = ui_scale_x, ui_scale_y
    txt = font().render(text, True, color)
    dx = (display_surface.get_width() - txt.get_width()) // 2 if center_x else int(x*sx)
    display_surface.blit(txt, (dx, int(y*sy)))

def draw_button(rect, text, font, hovered, center_x=False):
    sx, sy = ui_scale_x, ui_scale_y
    s = min(sx, sy)
    rw = int(rect.w * sx)
    rh = int(rect.h * sy)
    rx = (display_surface.get_width() - rw) // 2 if center_x else int(rect.x * sx)
    ry = int(rect.y * sy)
    s_rect = pygame.Rect(rx, ry, rw, rh)
    color = GREEN if hovered else GRAY
    pygame.draw.rect(display_surface, color, s_rect, border_radius=int(8*s))
    pygame.draw.rect(display_surface, WHITE, s_rect, max(1, int(2*s)), border_radius=int(8*s))
    txt = font().render(text, True, WHITE)
    display_surface.blit(txt, txt.get_rect(center=s_rect.center))

def quit_game():
    pygame.quit()
    sys.exit()

def toggle_fullscreen():
    global display_surface, is_fullscreen, ui_scale_x, ui_scale_y
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        ui_scale_x = display_surface.get_width() / SCREEN_WIDTH
        ui_scale_y = display_surface.get_height() / SCREEN_HEIGHT
    else:
        display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        ui_scale_x = 1.0
        ui_scale_y = 1.0
    pygame.display.set_caption("Save the King!")

def get_mouse_pos():
    mx, my = pygame.mouse.get_pos()
    return int(mx / ui_scale_x), int(my / ui_scale_y)

def update_display():
    if is_fullscreen:
        pygame.transform.smoothscale(screen, display_surface.get_size(), display_surface)
    else:
        display_surface.blit(screen, (0, 0))

def run_main_menu(ctx):
    while True:
        screen.fill((20, 20, 40))
        update_display()
        draw_text("SAVE THE KING!", title_font, WHITE, 150, 120, center_x=True)
        mx, my = get_mouse_pos()
        btn_play = pygame.Rect(300, 250, 200, 55)
        btn_load = pygame.Rect(300, 330, 200, 55)
        btn_quit = pygame.Rect(300, 410, 200, 55)
        draw_button(btn_play, "PLAY", menu_font, btn_play.collidepoint(mx, my), center_x=True)
        save_exists = has_save()
        if save_exists:
            draw_button(btn_load, "LOAD GAME", menu_font, btn_load.collidepoint(mx, my), center_x=True)
        else:
            s_rect = pygame.Rect((display_surface.get_width() - int(btn_load.w * ui_scale_x)) // 2, int(btn_load.y * ui_scale_y), int(btn_load.w * ui_scale_x), int(btn_load.h * ui_scale_y))
            pygame.draw.rect(display_surface, (60, 60, 60), s_rect, border_radius=int(8 * min(ui_scale_x, ui_scale_y)))
            dim_surf = menu_font().render("LOAD GAME", True, (80, 80, 80))
            display_surface.blit(dim_surf, dim_surf.get_rect(center=s_rect.center))
        draw_button(btn_quit, "QUIT", menu_font, btn_quit.collidepoint(mx, my), center_x=True)
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue
            if inputs.is_action(event, "click"): click = True
        if click:
            if btn_play.collidepoint(mx, my): return "character_select"
            elif btn_load.collidepoint(mx, my) and save_exists:
                ctx["load_save"] = True; return "playing"
            elif btn_quit.collidepoint(mx, my): return "quit"
        pygame.display.flip(); clock.tick(FPS)

def run_character_select(ctx):
    try:
        _sheet = pygame.image.load("assets/player.png").convert_alpha()
        _frame = _sheet.subsurface(pygame.Rect(0, 0, 48, 48))
        char_sprite = pygame.transform.scale(_frame, (96, 96))
    except Exception:
        char_sprite = None
    while True:
        screen.fill((20, 20, 40))
        
        kb = pygame.Rect(80, 180, 280, 300)
        ab = pygame.Rect(440, 180, 280, 300)
        pygame.draw.rect(screen, (40, 40, 80), kb, border_radius=12)
        mx, my = get_mouse_pos()
        pygame.draw.rect(screen, GREEN if kb.collidepoint(mx, my) else (100, 100, 160), kb, 3, border_radius=12)
        if char_sprite:
            screen.blit(char_sprite, (172, 200))
        else:
            pygame.draw.rect(screen, (100, 120, 200), pygame.Rect(190, 210, 60, 90))
            
        pygame.draw.rect(screen, (40, 40, 80), ab, border_radius=12)
        pygame.draw.rect(screen, GREEN if ab.collidepoint(mx, my) else (100, 100, 160), ab, 3, border_radius=12)
        if char_sprite:
            screen.blit(char_sprite, (532, 200))
        else:
            pygame.draw.rect(screen, (80, 180, 80), pygame.Rect(550, 210, 60, 90))
            
        update_display()
        
        draw_text("Choose Your Class", title_font, (255, 220, 80), 130, 60, center_x=True)
        draw_text("KNIGHT", menu_font, WHITE, 145, 315)
        draw_text("Vitality:    100", small_font, (100, 220, 100), 110, 360)
        draw_text("ATK:    20", small_font, (220, 100, 100), 110, 385)
        draw_text("Melee attack", small_font, (180, 180, 220), 110, 415)
        draw_text("High vitality", small_font, (180, 180, 220), 110, 440)
        draw_text("ARCHER", menu_font, WHITE, 500, 315)
        draw_text("Vitality:     70", small_font, (100, 220, 100), 470, 360)
        draw_text("ATK:    25", small_font, (220, 100, 100), 470, 385)
        draw_text("Ranged attack", small_font, (180, 180, 220), 470, 415)
        draw_text("High ATK", small_font, (180, 180, 220), 470, 440)
        draw_text("Press ESC to go back", small_font, GRAY, 280, 510, center_x=True)
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue
            if inputs.is_action(event, "click"): click = True
            if inputs.is_action(event, "back"): return "main_menu"
        if click:
            if kb.collidepoint(mx, my): ctx["chosen_class"] = "knight"; return "playing"
            elif ab.collidepoint(mx, my): ctx["chosen_class"] = "archer"; return "playing"
        pygame.display.flip(); clock.tick(FPS)

def run_game_over(ctx):
    reason = ctx.get("reason", "")
    while True:
        screen.fill((50, 10, 10))
        update_display()
        draw_text("GAME OVER", title_font, (255, 50, 50), 220, 150, center_x=True)
        draw_text(reason, small_font, (200, 100, 100), 220, 230, center_x=True)
        mx, my = get_mouse_pos()
        btn_menu = pygame.Rect(300, 320, 200, 55)
        btn_quit = pygame.Rect(300, 420, 200, 55)
        draw_button(btn_menu, "MAIN MENU", menu_font, btn_menu.collidepoint(mx, my), center_x=True)
        draw_button(btn_quit, "QUIT",      menu_font, btn_quit.collidepoint(mx, my), center_x=True)
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue
            if inputs.is_action(event, "click"): click = True
        if click:
            if btn_menu.collidepoint(mx, my): return "main_menu"
            elif btn_quit.collidepoint(mx, my): return "quit"
        pygame.display.flip()

def run_game_win(ctx):
    while True:
        screen.fill((20, 50, 20))
        update_display()
        draw_text("VICTORY!", title_font, (50, 255, 50), 250, 150, center_x=True)
        draw_text("You have saved the King and the realm!", small_font, (150, 255, 150), 220, 230, center_x=True)
        mx, my = get_mouse_pos()
        btn_menu = pygame.Rect(300, 320, 200, 55)
        btn_quit = pygame.Rect(300, 420, 200, 55)
        draw_button(btn_menu, "MAIN MENU", menu_font, btn_menu.collidepoint(mx, my), center_x=True)
        draw_button(btn_quit, "QUIT",      menu_font, btn_quit.collidepoint(mx, my), center_x=True)
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue
            if inputs.is_action(event, "click"): click = True
        if click:
            if btn_menu.collidepoint(mx, my): return "main_menu"
            elif btn_quit.collidepoint(mx, my): return "quit"
        pygame.display.flip()

def handle_pause(my_hero, my_king, my_level):
    opts = ["Resume", "Save Game", "Load Game", "Main Menu", "Quit"]
    while True:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        update_display()
        paused_surf = title_font().render("PAUSED", True, WHITE)
        display_surface.blit(paused_surf, ((display_surface.get_width() - paused_surf.get_width()) // 2, int(80*ui_scale_y)))
        mx, my = get_mouse_pos()
        rects = []
        for i, opt in enumerate(opts):
            r = pygame.Rect(300, 180 + i * 60, 200, 50)
            rects.append(r)
            draw_button(r, opt, menu_font, r.collidepoint(mx, my), center_x=True)
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue
            if inputs.is_action(event, "pause"): return "resume"
            if inputs.is_action(event, "click"): click = True
        if click:
            if rects[0].collidepoint(mx, my): return "resume"
            elif rects[1].collidepoint(mx, my):
                if save_game(my_hero, my_king, my_level):
                    saved_surf = menu_font().render("Game Saved!", True, (100, 255, 100))
                    display_surface.blit(saved_surf, ((display_surface.get_width() - saved_surf.get_width()) // 2, int((SCREEN_HEIGHT - 60)*ui_scale_y)))
                    pygame.display.flip(); pygame.time.wait(800)
                return "resume"
            elif rects[2].collidepoint(mx, my): return "load"
            elif rects[3].collidepoint(mx, my): return "main_menu"
            elif rects[4].collidepoint(mx, my): return "quit"
        pygame.display.flip()

def handle_riddle(guard):
    user_text = ""
    result = None
    msg = ""
    while result is None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        update_display()
        draw_text("The Guard asks:", menu_font, (255, 220, 100), 50, 60, center_x=True)
        question = guard.riddle["q"]
        words = question.split()
        lines = []
        cur   = ""
        for w in words:
            test_str = (cur + " " + w).strip()
            if small_font().size(test_str)[0] < 700:
                cur = test_str
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for i, line in enumerate(lines):
            draw_text(line, small_font, WHITE, 50, 120 + i * 28, center_x=True)
        y_input = 120 + len(lines) * 28 + 30
        draw_text(f"Attempts left: {3 - guard.mistakes}", small_font, (255, 150, 150), 50, y_input, center_x=True)
        
        ib_x = int(50 * ui_scale_x)
        ib_y = int((y_input + 35) * ui_scale_y)
        ib_w = int(700 * ui_scale_x)
        ib_h = int(40 * ui_scale_y)
        input_box = pygame.Rect(ib_x, ib_y, ib_w, ib_h)
        input_box.centerx = display_surface.get_width() // 2
        pygame.draw.rect(display_surface, (40, 40, 60), input_box)
        pygame.draw.rect(display_surface, WHITE, input_box, max(1, int(2 * min(ui_scale_x, ui_scale_y))))
        
        txt_surf = input_font().render(user_text + "|", True, WHITE)
        display_surface.blit(txt_surf, (input_box.x + int(10*ui_scale_x), input_box.y + int(8*ui_scale_y)))
        
        draw_text("Type your answer and press Enter", small_font, GRAY, 50, y_input + 85, center_x=True)
        if msg:
            draw_text(msg, menu_font, (255, 100, 100), 50, y_input + 120, center_x=True)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: quit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and user_text.strip():
                    ans = guard.answer(user_text)
                    if ans == "correct":
                        result = "correct"
                    elif ans == "failed":
                        result = "failed"
                    else:
                        msg = f"Wrong! {3 - guard.mistakes} attempts left."
                        user_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                elif event.unicode.isprintable() and len(user_text) < 40:
                    user_text += event.unicode
        pygame.display.flip()
    return result

def handle_merchant(my_hero, game_ui):
    while True:
        update_display()
        game_ui.draw_merchant(display_surface, my_hero)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: quit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue
            if inputs.is_action(event, "interact"): return
            if event.type == pygame.KEYDOWN and "gold coin" in my_hero.inventory:
                if event.key == pygame.K_1:
                    my_hero.inventory.remove("gold coin")
                    my_hero.attack_power += 10
                    game_ui.show_feedback("+10 Attack Power!"); return
                elif event.key == pygame.K_2:
                    my_hero.inventory.remove("gold coin")
                    my_hero.repair_armor(50)
                    game_ui.show_feedback("+50 Armor!"); return
                elif event.key == pygame.K_3:
                    my_hero.inventory.remove("gold coin")
                    my_hero.max_vitality += 50
                    my_hero.heal(50)
                    game_ui.show_feedback("+50 Max Vitality!"); return
                elif event.key == pygame.K_4:
                    return
        pygame.display.flip()

def _handle_attack(my_hero, my_level):
    now = pygame.time.get_ticks()
    if now - my_hero.last_attack_time <= my_hero.attack_cooldown:
        return
    my_hero.attack(my_level.active_enemies, mouse_pos=get_mouse_pos(), walls=my_level.walls)
    my_hero.last_attack_time = now

    attack_rect = my_hero.hitbox.inflate(40, 40)
    hit_guard_or_npc = False

    if my_level.active_guard and my_level.active_guard.is_hostile:
        guard = my_level.active_guard
        if attack_rect.colliderect(guard.hitbox):
            hit_guard_or_npc = True
            if guard.take_damage(my_hero.attack_power):
                my_level.active_guard = None

    for npc in my_level.active_npcs[:]:
        if npc.is_hostile and attack_rect.colliderect(npc.hitbox):
            hit_guard_or_npc = True
            if npc.take_damage(my_hero.attack_power):
                my_level.active_npcs.remove(npc)

    if hit_guard_or_npc and hasattr(my_hero, 'sword_hit'):
        my_hero.sword_hit.set_volume(0.5)
        my_hero.sword_hit.play()

def _draw_hud(screen, my_hero, my_level, game_ui, dialogue, nearby_item, nearby_chest):
    feedback_active = game_ui.feedback_msg and (
        pygame.time.get_ticks() - game_ui.feedback_timer < game_ui.feedback_duration)
    if dialogue.active or feedback_active:
        return

    if nearby_chest:
        if nearby_chest.state == "locked":
            hint_text = "[E] Open chest  (need: Golden Key)"
        elif nearby_chest.state == "opened":
            hint_text = "This chest is already empty."
        else:
            hint_text = "[E] Open chest"
        hint_surf = small_font().render(hint_text, True, (255, 220, 100))
        display_surface.blit(hint_surf, ((display_surface.get_width() - hint_surf.get_width()) // 2, int((SCREEN_HEIGHT - 40)*ui_scale_y)))
    elif nearby_item:
        hint_surf = small_font().render(f"[E] Pick up: {nearby_item.display_name}", True, WHITE)
        display_surface.blit(hint_surf, ((display_surface.get_width() - hint_surf.get_width()) // 2, int((SCREEN_HEIGHT - 40)*ui_scale_y)))

    for npc in my_level.active_npcs:
        if not npc.is_hostile and my_hero.hitbox.colliderect(npc.hitbox):
            hint_surf = small_font().render("[E] Talk to Merchant", True, (255, 215, 0))
            display_surface.blit(hint_surf, ((display_surface.get_width() - hint_surf.get_width()) // 2, int((SCREEN_HEIGHT - 40)*ui_scale_y)))

def run_game_loop(ctx):
    load_data = None
    if ctx.get("load_save"):
        load_data = load_game()
        ctx["load_save"] = False

    if load_data:
        pc = load_data["player"]["class"]
        my_hero = Knight(100, 100) if pc == "Knight" else Archer(100, 100)
        pd = load_data["player"]
        my_hero.vitality = pd["vitality"]
        my_hero.max_vitality = pd["max_vitality"]
        my_hero.current_armor = pd["current_armor"]
        my_hero.attack_power = pd["attack_power"]
        my_hero.inventory = pd["inventory"]
        my_level = Level()
        lv = load_data["level"]
        my_level.visited_rooms = set(lv["visited_rooms"])
        my_level.unlocked_doors = set(tuple(d) for d in lv["unlocked_doors"])
        my_level.bandit_camp_cleared = lv["bandit_camp_cleared"]
        my_level.cleared_enemy_rooms = set(lv["cleared_enemy_rooms"])
        my_level.opened_chests = set(tuple(c) for c in lv["opened_chests"])
        my_level.collected_items = set(tuple(c) for c in lv["collected_items"])
        my_level.load_room(lv["current_room"])
        king_data = load_data["king"]
        my_king = King(king_data["x"], king_data["y"])
        my_king.vitality = king_data["vitality"]
        my_king.is_alive = king_data["is_alive"]
        my_hero.hitbox.x = pd["x"]
        my_hero.hitbox.y = pd["y"]
        my_hero.image_rect.midbottom = my_hero.hitbox.midbottom
    else:
        chosen = ctx.get("chosen_class", "knight")
        my_hero = Knight(100, 100) if chosen == "knight" else Archer(100, 100)
        my_level = Level()
        my_king = King(160, 100)

    game_ui = UI()
    dialogue = DialogueBox()
    nearby_item = None
    nearby_chest = None
    merchant_active = False
    villager_triggered_rooms = set()
    guard_gate_opened = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                toggle_fullscreen(); continue

            if inputs.is_action(event, "pause"):
                pause_result = handle_pause(my_hero, my_king, my_level)
                if pause_result == "main_menu": return "main_menu"
                elif pause_result == "quit":    return "quit"
                elif pause_result == "load":
                    ctx["load_save"] = True; return "playing"
                continue

            if inputs.is_action(event, "map_toggle"):
                game_ui.toggle_map()

            if dialogue.active:
                if inputs.is_action(event, "interact"):
                    dialogue.skip_or_close()
                continue

            if merchant_active:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    game_ui.toggle_inventory()

                if event.key == pygame.K_e:
                    for npc in my_level.active_npcs:
                        if npc.npc_type == "merchant" and my_hero.hitbox.colliderect(
                                npc.hitbox.inflate(60, 60)):
                            merchant_active = True
                            break
                    if merchant_active:
                        handle_merchant(my_hero, game_ui)
                        merchant_active = False
                        continue

                    if nearby_chest:
                        opened, msg, reward = nearby_chest.try_open(my_hero.inventory)
                        game_ui.show_feedback(msg)
                        if opened:
                            chest_open.play()
                            my_level.mark_chest_opened(nearby_chest)
                    elif nearby_item:
                        my_hero.inventory.append(nearby_item.name)
                        my_level.mark_item_collected(nearby_item)
                        my_level.active_items.remove(nearby_item)
                        game_ui.show_feedback(f"Picked up: {nearby_item.display_name}")
                        nearby_item = None

                if game_ui.show_inventory:
                    unique      = my_hero.get_unique_items()
                    chosen_item = None
                    if inputs.is_action(event, "use_1") and len(unique) >= 1:
                        chosen_item = unique[0]
                    elif inputs.is_action(event, "use_2") and len(unique) >= 2:
                        chosen_item = unique[1]
                    elif inputs.is_action(event, "use_3") and len(unique) >= 3:
                        chosen_item = unique[2]
                    if chosen_item:
                        success, msg = my_hero.use_item(chosen_item)
                        game_ui.show_feedback(msg)

            if inputs.is_action(event, "attack"):
                _handle_attack(my_hero, my_level)

        if not dialogue.active:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= my_hero.speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += my_hero.speed
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= my_hero.speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += my_hero.speed
            my_hero.move(dx, dy, my_level.walls)
            my_hero.animate(dx != 0 or dy != 0)
        else:
            dialogue.update()

        room_map = my_level.world_maps[my_level.current_room_name]["map"]
        active_w = len(room_map[0]) * TILE_SIZE if room_map else SCREEN_WIDTH
        active_h = len(room_map) * TILE_SIZE    if room_map else SCREEN_HEIGHT

        limit = 5
        direction_to_try = None
        if my_hero.hitbox.left < -limit:
            direction_to_try = "west"
        elif my_hero.hitbox.right > active_w + limit:
            direction_to_try = "east"
        elif my_hero.hitbox.top < -limit:
            direction_to_try = "north"
        elif my_hero.hitbox.bottom > active_h + limit:
            direction_to_try = "south"

        if direction_to_try:
            result = my_level.try_change_room(direction_to_try, my_hero)
            if result is True:
                my_king.on_room_change(my_hero.hitbox)
                if my_level.is_villager_room() and my_level.current_room_name not in villager_triggered_rooms:
                    villager_triggered_rooms.add(my_level.current_room_name)
                    for npc in my_level.active_npcs:
                        if npc.npc_type == "villager":
                            text, hostile = npc.trigger_villager(my_level.bandit_camp_cleared)
                            if text:
                                dialogue.show("Villager", text)
                if my_level.is_guard_room():
                    guard_gate_opened = False
            elif result is None:
                if direction_to_try == "west":  my_hero.hitbox.left   = 5
                elif direction_to_try == "east": my_hero.hitbox.right  = active_w - 5
                elif direction_to_try == "north": my_hero.hitbox.top   = 5
                elif direction_to_try == "south": my_hero.hitbox.bottom = active_h - 5
                my_hero.image_rect.midbottom = my_hero.hitbox.midbottom
            elif isinstance(result, str):
                game_ui.show_feedback(result)
                if direction_to_try == "west":  my_hero.hitbox.left   = 5
                elif direction_to_try == "east": my_hero.hitbox.right  = active_w - 5
                elif direction_to_try == "north": my_hero.hitbox.top   = 5
                elif direction_to_try == "south": my_hero.hitbox.bottom = active_h - 5
                my_hero.image_rect.midbottom = my_hero.hitbox.midbottom

        if my_level.current_room_name == "castle" and my_king.is_alive:
            ctx["reason"] = "You have saved the King!"
            return "game_win"

        if my_level.active_guard and not my_level.active_guard.gate_open and not my_level.active_guard.is_hostile:
            if my_level.active_guard.check_approach(my_hero.hitbox):
                riddle_result = handle_riddle(my_level.active_guard)
                if riddle_result == "correct":
                    my_level.open_guard_gate()
                    game_ui.show_feedback("The gate opens! You may pass.")
                    guard_gate_opened = True
                elif riddle_result == "failed":
                    game_ui.show_feedback("The guards turn hostile!")
                    for npc in my_level.active_npcs:
                        npc.is_hostile = True
                        npc.dialogue = "You failed the riddle! DIE!"

        my_hero.update_projectiles(my_level.active_enemies, my_level.walls, guard=my_level.active_guard, npcs=my_level.active_npcs)
        if my_level.active_guard and my_level.active_guard.hp <= 0:
            my_level.active_guard = None
        my_king.update(my_hero.hitbox, my_level.walls)

        now = pygame.time.get_ticks()

        for enemy in my_level.active_enemies:
            enemy.update(my_hero.hitbox, my_level.walls)
            edx = my_hero.hitbox.centerx - enemy.hitbox.centerx
            edy = my_hero.hitbox.centery - enemy.hitbox.centery
            dist_to_hero = math.sqrt(edx**2 + edy**2)
            if dist_to_hero <= enemy.attack_range:
                if now - enemy.last_attack_time > enemy.attack_cooldown:
                    my_hero.take_damage(enemy.attack_power)
                    enemy.last_attack_time = now
            elif my_king.hitbox.colliderect(enemy.hitbox):
                if now - enemy.last_attack_time > enemy.attack_cooldown:
                    my_king.take_damage(enemy.attack_power)
                    enemy.last_attack_time = now

        if my_level.active_guard and my_level.active_guard.is_hostile:
            guard = my_level.active_guard
            guard.update(my_hero.hitbox, my_level.walls)
            if my_hero.hitbox.colliderect(guard.hitbox):
                if now - guard.last_attack_time > guard.attack_cooldown:
                    my_hero.take_damage(guard.attack_power)
                    guard.last_attack_time = now

        for npc in my_level.active_npcs:
            if npc.is_hostile:
                npc.update(my_hero.hitbox)
                if my_hero.hitbox.colliderect(npc.hitbox):
                    if now - npc.last_attack_time > npc.attack_cooldown:
                        my_hero.take_damage(npc.attack_power)
                        npc.last_attack_time = now

        my_level.check_enemies_cleared()

        if not my_hero.is_alive:
            ctx["reason"] = "You have fallen in battle..."
            return "game_over"
        if not my_king.is_alive:
            ctx["reason"] = "The King has been slain! All is lost."
            return "game_over"

        nearby_item  = None
        nearby_chest = None
        for chest in my_level.active_chests:
            if my_hero.hitbox.colliderect(chest.rect):
                nearby_chest = chest
                break
        if not nearby_chest:
            for item in my_level.active_items:
                if my_hero.hitbox.colliderect(item.rect):
                    nearby_item = item
                    break

        screen.fill(BG_COLOR)
        my_level.draw(screen)
        my_king.draw(screen)
        my_hero.draw(screen)

        update_display()
        
        my_king.draw_hp_bar(display_surface, ui_scale_x, ui_scale_y)
        
        for npc in my_level.active_npcs:
            npc.draw_ui(display_surface, ui_scale_x, ui_scale_y)
        if my_level.active_guard:
            my_level.active_guard.draw_ui(display_surface, ui_scale_x, ui_scale_y)

        game_ui.update_scale(ui_scale_x, ui_scale_y)
        dialogue.update_scale(ui_scale_x, ui_scale_y)
        game_ui.draw(display_surface, my_hero, my_level)
        dialogue.draw(display_surface)
        _draw_hud(display_surface, my_hero, my_level, game_ui, dialogue, nearby_item, nearby_chest)

        pygame.display.flip()
        clock.tick(FPS)

def main():
    state = "main_menu"
    ctx   = {}
    while state != "quit":
        if state == "main_menu": state = run_main_menu(ctx)
        elif state == "character_select": state = run_character_select(ctx)
        elif state == "playing": state = run_game_loop(ctx)
        elif state == "game_over": state = run_game_over(ctx)
        elif state == "game_win": state = run_game_win(ctx)
        else: state = "main_menu"
    pygame.quit()

if __name__ == "__main__":
    main()
