import math

import game_engine_constants

ROCKET_LAUNCHER_FIRE_RATE_HZ: int = 1

ROCKET_RADIUS: float = game_engine_constants.TILE_SIZE / 4

ROCKET_SPEED: int = 1750

ROCKET_EXPLOSION_RADIUS: int = 100

ROCKET_EXPLOSION_DAMAGE: int = 10

ROCKET_EXPLOSION_SHARDS: int = 32

ROCKET_EXPLOSION_COLLISION_FORCE: int = 300


RAILGUN_FIRE_RATE_HZ: int = 1.5

RAILGUN_DAMAGE: int = 60

RAILGUN_COLLISION_FORCE: int = 1000


SHOTGUN_FIRE_RATE_HZ: float = 2.5

SHOTGUN_MEATSHOT_DAMAGE: int = 80

SHOTGUN_PELLETS: int = 9

SHOTGUN_PELLET_DAMAGE: float = SHOTGUN_MEATSHOT_DAMAGE / SHOTGUN_PELLETS

SHOTGUN_SPRAY_ANGLE: float = math.tau / 8

SHOTGUN_SPRAY_RADIUS: int = 150

SHOTGUN_COLLISION_FORCE: int = 500
