from uuid import UUID
from network_object.player import PlayerNetworkObject
import pygame


class Leaderboard:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font,
    ):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font

    def _make_leaderboard_row(self, player: PlayerNetworkObject) -> str:
        return f"{str(player.uuid)[:4]}: {player.num_frags}"

    def render(self, our_player_id: UUID, players: list[PlayerNetworkObject]) -> None:
        players.sort(key=lambda player: player.num_frags, reverse=True)

        height = self.rect.y
        for player in players:
            text = self._make_leaderboard_row(player)
            color = "white" if player.uuid != our_player_id else "gold"
            row = self.font.render(text, False, pygame.Color(color))
            height += row.get_height()
            text_pos = (self.rect.x, height)
            self.screen.blit(row, text_pos)
