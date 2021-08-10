import player
import typing, abc


class GameMode:
    pass


class TimedGameMode(GameMode):  # skill mode, duel
    pass


class ConditionGameMode(GameMode):  # CTF
    pass


class FirstToNFrags(ConditionGameMode):
    def __init__(self, frags_to_win=1000):
        self.frags_to_win = frags_to_win
        self.respawn_time = 5  # measured in seconds
