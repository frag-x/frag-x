import pygame


class TextInputBox:
    def __init__(self, x: int, y: int, w: int, font: pygame.font.Font) -> None:
        self.color = (255, 255, 255)
        self.backcolor = None
        self.pos = (x, y)
        self.width = w
        self.font = font
        self.text = ""
        self.border_thickness = 2
        self.rect = None
        self.render_text()

    def render_text(self) -> None:
        t_surf = self.font.render(self.text, True, self.color, self.backcolor)
        self.image = pygame.Surface(
            (max(self.width, t_surf.get_width() + 10), t_surf.get_height() + 10),
            pygame.SRCALPHA,
        )
        if self.backcolor:
            self.image.fill(self.backcolor)
        self.image.blit(t_surf, (5, 5))
        pygame.draw.rect(
            self.image,
            self.color,
            self.image.get_rect().inflate(-2, -2),
            self.border_thickness,
        )
        self.rect = self.image.get_rect(topleft=self.pos)

    def update(self, event_list: list[pygame.event.Event]) -> None:
        for event in event_list:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
