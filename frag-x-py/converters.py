from typing import List
# TODO: these will need to be generalized to work on the textual info from the server
# Not just the x and y thing

# TODO maybe I can encode my state by bits and not numbers?
def convert_player_data_to_str(player_id: int, x: float, y:float, delta_time: float) -> str:
    # TODO when the data gets longer use join
    return '|'.join([str(k) for k in [player_id, x, y, delta_time]])

def convert_player_pos_to_pos_str(x: float, y:float) -> str:
    # TODO when the data gets longer use join
    return '|'.join([str(k) for k in [x, y]])

def convert_str_to_player_data_server(player_data: str) -> List[int]:
    player_id, x, y, delta_time = player_data.split("|")
    return [int(player_id), float(x), float(y), float(delta_time)]

def convert_str_to_player_data_client(player_data: str) -> List[int]:
    player_id, x, y = player_data.split("|")
    return [int(player_id), float(x), float(y)]

def convert_pos_str_to_player_pos(player_data: str) -> List[int]:
    player_id, x, y= player_data.split("|")
    return [int(player_id), float(x), float(y)]

