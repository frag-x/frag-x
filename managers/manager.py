import map_loading


class GameManager:
    def __init__(self, map_fullname):
        self.id_to_player = {}
        # TODO make this a set eventually
        self.projectiles = []
        self.beam_messages = []
        self.time_running = 0
        self.partitioned_map_grid = map_loading.PartitionedMapGrid(
            map_loading.get_pixels(map_fullname), 10, 10
        )

    def get_ids(self):
        return list(self.id_to_player.keys())

    def get_players(self):
        return list(self.id_to_player.values())
