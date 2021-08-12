import map_loading


class GameManager:
    def __init__(self, map_name):
        self.id_to_player = {}
        # TODO make this a set eventually
        self.projectiles = []
        self.beam_messages = []
        self.time_running = 0
        self.partitioned_map_grid = map_loading.PartitionedMapGrid(
            map_loading.get_pixels(map_name), 10, 10
        )

    def get_ids(self):
        return self.id_to_player.keys()

    def get_players(self):
        return self.id_to_player.values()
