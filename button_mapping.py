import pygame

class ButtonMapping:
    def __init__(self):
        pygame.joystick.init()
        self.joysticks = []

        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self.joysticks.append(joy)
            print(f"Controller connected: {joy.get_name()}")

    def movement_key(self):
        dx, dy = 0, 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1

        if self.joysticks:
            ax = self.joysticks[0].get_axis(0)
            ay = self.joysticks[0].get_axis(1)
            if ax < -0.25: dx -= 1
            elif ax > 0.25: dx += 1
            if ay < -0.25: dy -= 1
            elif ay > 0.25: dy += 1

        return dx, dy

    def is_action(self, event, action):
        joydown = event.type == pygame.JOYBUTTONDOWN

        if action == "attack":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                   (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
                   (joydown and event.button == 0)

        if action == "interact":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_e) or \
                   (joydown and event.button == 1)

        if action == "inventory":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_i) or \
                   (joydown and event.button == 2)

        if action == "use_1":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_1) or \
                   (event.type == pygame.JOYHATMOTION and event.value == (-1, 0))

        if action == "use_2":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_2) or \
                   (event.type == pygame.JOYHATMOTION and event.value == (0, 1))

        if action == "use_3":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_3) or \
                   (event.type == pygame.JOYHATMOTION and event.value == (1, 0))

        if action == "click":
            return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
                   (joydown and event.button == 0)

        if action == "back":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
                   (joydown and event.button == 1)

        if action == "pause":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
                   (joydown and event.button == 7)

        if action == "map_toggle":
            return (event.type == pygame.KEYDOWN and event.key == pygame.K_TAB) or \
                   (joydown and event.button == 6)

        return False
