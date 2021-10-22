from simulation_object import player
import typing, abc


class GameMode:
    pass


class TimedGameMode(GameMode):  # skill mode, duel
    pass


class ConditionGameMode(GameMode):  # CTF
    pass


class FirstToNFrags(ConditionGameMode):
    def __init__(self, frags_to_win=15, respawn_time = 5):
        self.frags_to_win = frags_to_win
        self.respawn_time = respawn_time  # measured in seconds


class InstakillGameMode(FirstToNFrags): #Instakill
    def __init__(self, frags_to_win=15, respawn_time = 5):
        super().__init__(frags_to_win=frags_to_win, respawn_time=respawn_time)

