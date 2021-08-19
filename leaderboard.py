from uuid import UUID
from network_object.player import PlayerNetworkObject
from typing import List
import pygame

class Leaderboard:
    def __init__(self, screen, x, y, width, height, font):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font

    def _make_leaderboard_row(self, player: PlayerNetworkObject):
        return f'{str(player.uuid)[:4]}: {player.num_frags}'

    def render(self, our_player_id: UUID, players: List[PlayerNetworkObject]):
        players.sort(key=lambda player: player.num_frags, reverse=True)

        height = self.rect.y
        for player in players:
            text = self._make_leaderboard_row(player)
            row = self.font.render(text, False, pygame.Color("white"))
            height += row.get_height()
            text_pos = (self.rect.x, height)
            self.screen.blit(row, text_pos)
