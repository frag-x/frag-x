from client_elements import client_element
import game_engine_constants
import pygame
class WeaponDirectory(client_element.ClientTextElement):
    def render(self):
        text = str(game_engine_constants.WEAPON_NAME_TO_KEY)
        color = 'white' 
        rendered_text = self.font.render(text, False, pygame.Color(color))
        height = rendered_text.get_height()
        text_pos = (self.rect.x, height)
        self.screen.blit(rendered_text, text_pos)