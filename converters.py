from typing import List
# TODO: these will need to be generalized to work on the textual info from the server
# Not just the x and y thing

def player_data_to_str(player_data):
    return "|".join(str(x) for x in player_data)

def str_to_player_data(player_data: str):
    """Here we x, y, mouse can be referring to delta's coming into the server, or in the 
    client where they'll be absolute positions or angles"""
    player_id, x, y, mouse, delta_time = player_data.split("|")
    return [int(player_id), float(x), float(y), float(mouse), float(delta_time)]

def str_to_player_data_no_dt(player_data: str):
    """Here we x, y, mouse can be referring to delta's coming into the server, or in the 
    client where they'll be absolute positions or angles"""
    player_id, x, y, mouse = player_data.split("|")
    return [int(player_id), float(x), float(y), float(mouse)]
