import player
import typing, abc

class GameMode:
    pass

class TimedGameMode(GameMode): # skill mode, duel
    pass

class ConditionGameMode(GameMode): # CTF
    pass

class FirstToNFrags(ConditionGameMode):
    def __init__(self, frags_to_win=10):
        self.frags_to_win = frags_to_win
        self.respawn_time = 5 # measured in seconds

    def generate_player_to_frag_count(self, players: typing.Set[player.KillableServerPlayer]):
        return {p: p.num_frags for p in players}

    def is_game_over(self, players: typing.Set[player.KillableServerPlayer]):
        """Figures out if the game is over and if it is then return who the winner is"""
        player_to_frag_count = self.generate_player_to_frag_count(players)
        for player, frag_count in player_to_frag_count.items():
            if frag_count >= self.frags_to_win: # TODO what if multiple people die in the same tick making many winners - this only returns the first winner based on the list ordering
                return (True, player)
        return (False, None)



