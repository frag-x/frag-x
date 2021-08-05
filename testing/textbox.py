import pygame


class TextInputBox:
    def __init__(self, x, y, w, font):
        super().__init__()
        self.color = (255, 255, 255)
        self.backcolor = None
        self.pos = (x, y)
        self.width = w
        self.font = font
        self.text = ""
        self.render_text()

    def render_text(self):
        t_surf = font.render(self.text, True, self.color, self.backcolor)
        self.image = pygame.Surface(
            (max(self.width, t_surf.get_width() + 10), t_surf.get_height() + 10),
            pygame.SRCALPHA,
        )
        if self.backcolor:
            self.image.fill(self.backcolor)
        self.image.blit(t_surf, (5, 5))
        pygame.draw.rect(
            self.image, self.color, self.image.get_rect().inflate(-2, -2), 2
        )
        self.rect = self.image.get_rect(topleft=self.pos)

    def update(self, event_list):
        for event in event_list:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode


pygame.init()
width, height = 500, 200
center_point = (width / 2, height / 2)
window = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 100)

text_input_box = TextInputBox(50, 50, 400, font)


def button_pressed(event_list, key):
    for event in event_list:
        if event.type == pygame.KEYDOWN:
            if event.key == key:
                return True
    return False


def start_typing(event_list):
    return button_pressed(event_list, pygame.K_t)


def end_typing_and_do_action(event_list):
    return button_pressed(event_list, pygame.K_RETURN)


def end_typing_and_do_nothing(event_list):
    return button_pressed(event_list, pygame.K_ESCAPE)


typing = False
just_started = False
run = True
while run:
    clock.tick(60)
    event_list = pygame.event.get()
    for event in event_list:
        if event.type == pygame.QUIT:
            run = False
        if not typing:
            if start_typing(event_list):  # only check if they pressd when not typing
                typing = True
                just_started = True
        else:
            if end_typing_and_do_action(
                event_list
            ):  # they are typing and then press return
                typing = False
                # DO ACTION
                print(f"sending {text_input_box.text}")
                text_input_box.text = ""
            elif end_typing_and_do_nothing(event_list):
                typing = False
                text_input_box.text = ""

    if typing and not just_started:
        text_input_box.update(event_list)  # update the textbox if they're typing

    text_input_box.render_text()

    just_started = False

    window.fill(0)

    window.blit(text_input_box.image, (0, 0))

    pygame.display.flip()

pygame.quit()
exit()
