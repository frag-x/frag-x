from typing import List, Union

# TODO: these will need to be generalized to work on the textual info from the server
# Not just the x and y thing


def player_data_to_str(player_data: List[Union[str, int, float]]) -> str:
    return "|".join(str(x) for x in player_data)


def str_to_player_data(player_data: str) -> List[Union[str, int, float]]:
    """Here we x, y, mouse can be referring to delta's coming into the server, or in the
    client where they'll be absolute positions or angles"""
    player_id, x, y, mouse, delta_time, firing, weapon_request = player_data.split("|")
    return [
        player_id,
        float(x),
        float(y),
        float(mouse),
        float(delta_time),
        int(firing),
        int(weapon_request),
    ]


def str_to_player_data_no_dt(player_data: str) -> List[Union[str, float]]:
    """Here we x, y, mouse can be referring to delta's coming into the server, or in the
    client where they'll be absolute positions or angles"""
    player_id, x, y, mouse = player_data.split("|")
    return [player_id, float(x), float(y), float(mouse)]
