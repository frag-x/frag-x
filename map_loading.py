from PIL import Image
import pygame
import game_engine_constants
import helpers
from typing import List, Optional, Tuple


def get_pixels(filename):
    img = Image.open(filename)
    w, h = img.size
    pix = list(img.getdata())
    return [pix[n:n+w] for n in range(0, w*h, w)]

def create_blank_map(filename):
    img = Image.open(filename)
    w, h = img.size
    return [[None for x in range(w)] for y in range(h)]


class Wall:
    def __init__(self, x, y, color = pygame.color.THECOLORS['grey']):
        self.size = game_engine_constants.TILE_SIZE
        self.x_idx = x
        self.y_idx = y

        self.x = x * self.size
        self.y = y * self.size

        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        self.color = color

class BoundingWall(Wall):
    def __init__(self, x, y, color = pygame.color.THECOLORS['grey']):
        super().__init__(x,y, color)
        self.visible_sides = None

# TODO make this taken in something other than filename for input so that ineheritance will work.
# Make it takin a list of pixels and then the partitioned version will call this on the chunked thing.
class MapGrid:
    def __init__(self, pixel_map):
        self.pixel_map = pixel_map
        self.walls = []
        self.bounding_walls = []
        self.base_height = len(pixel_map) 
        self.base_width = len(pixel_map[0]) 

        self.height = self.base_height * game_engine_constants.TILE_SIZE
        self.width = self.base_width * game_engine_constants.TILE_SIZE

        self.map = [[None for x in range(self.base_width)] for y in range(self.base_height)]

        self.construct_walls()
        self.construct_bounding_walls()
        self.classify_bounding_walls()


    def construct_walls(self):
        for y, row in enumerate(self.pixel_map):
            for x, element in enumerate(row):
                if is_wall(x,y,self.pixel_map):
                    w = Wall(x,y,pygame.color.THECOLORS['grey'])
                    self.walls.append(w)
                    self.map[y][x] = w

    def construct_bounding_walls(self):
        for y, row in enumerate(self.pixel_map):
            for x, element in enumerate(row):
                if is_bounding(x,y, self.pixel_map):
                    bw = BoundingWall(x,y, pygame.color.THECOLORS['aquamarine4'])
                    self.bounding_walls.append(bw)
                    self.map[y][x] = bw


    def classify_bounding_walls(self):
        # construct simple representation

        # Indices max
        max_x = len(self.map[0]) - 1
        max_y = len(self.map) - 1

        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                map_entity = self.map[y][x]
                if map_entity and type(map_entity) is BoundingWall:
                    bw = self.map[y][x]
                    around = []
                    """
                                     _A_
                                    |   |
                                 ___|___|___
                               D|   |   |   |B 
                                |___|___|___| 
                                    |   |
                                    |___|
                                      C
                    """
                    #              A        B       C       D 
                    circular = [(0, -1), (1, 0), (0, 1), (-1, 0)]
                    for i, j in circular:
                        point_x = x + i
                        point_y = y + j
                        # If these are valid indices
                        if 0 <= point_x <= max_x and 0 <= point_y <= max_y:
                            if self.map[point_y][point_x]:
                                around.append(True)
                            else:
                                around.append(False)
                        else:
                                around.append(False)

                    bw.visible_sides = [not x for x in around]

# TODO - so that it can be used in client and server
class PMGManager:
    """This class updates players within the partioned map grid"""
    pass

class PartitionedMapGrid(MapGrid):
    def __init__(self, pixel_map, partition_width_base, partition_height_base):
        super().__init__(pixel_map)

        self.partition_width_base = partition_width_base
        self.partition_height_base = partition_height_base

        self.partition_width = self.partition_width_base * game_engine_constants.TILE_SIZE
        self.partition_height = self.partition_height_base * game_engine_constants.TILE_SIZE

        assert self.base_width % partition_width_base == 0 and self.base_height % partition_height_base == 0

        self.num_x_partitions = self.base_width // self.partition_width_base
        self.num_y_partitions = self.base_height // self.partition_height_base
        self.partitioned_map = [[None for x in range(self.num_x_partitions)] for y in range(self.num_y_partitions)]
        self.collision_partitioned_map = [[None for x in range(self.num_x_partitions)] for y in range(self.num_y_partitions)]
        self.partition_map()

    def partition_map(self):
        for j in range(0, self.base_height, self.partition_height_base):
            for i in range(0, self.base_width, self.partition_width_base):


                x1, x2 = i, i + self.partition_width_base
                y1, y2 = j, j + self.partition_height_base
                map_partition = [row[x1: x2] for row in self.map[y1: y2]]

                # Even if a body is inside of a paritition part of it may be coming out of the partition, therefore we need to make sure we account for these extra blocks
                collision_buffer_size = 1 
                cx1, cx2 = helpers.clamp(x1 - collision_buffer_size, 0, self.base_width), helpers.clamp(x2 + collision_buffer_size, 0, self.base_width)
                cy1, cy2 = helpers.clamp(y1 - collision_buffer_size, 0, self.base_height), helpers.clamp(y2 + collision_buffer_size, 0, self.base_height)

                print(cx1, cx2, cy1, cy2)
                
                collision_map_partition = [row[cx1: cx2] for row in self.map[cy1: cy2]]

                j_idx = j // self.partition_height_base
                i_idx = i // self.partition_width_base

                self.partitioned_map[j_idx][i_idx] = MapGridPartition((i,j), self.partition_width_base, self.partition_height_base, map_partition)
                self.collision_partitioned_map[j_idx][i_idx] = MapGridPartition((i,j), self.partition_width_base, self.partition_height_base, collision_map_partition)

class MapGridPartition:
    def __init__(self, pos: Tuple[int, int], partition_width_base: int, partition_height_base: int, partition_data:List[List[Optional[Wall]]]):
        self.pos = (pos[0] * game_engine_constants.TILE_SIZE , pos[1] * game_engine_constants.TILE_SIZE)
        self.partition_width_base = partition_width_base * game_engine_constants.TILE_SIZE
        self.partition_height_base = partition_height_base * game_engine_constants.TILE_SIZE        
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.partition_width_base, self.partition_height_base)
        self.walls = []
        self.bounding_walls = []
        for row in partition_data:
            for data in row:
                if type(data) is BoundingWall:
                    self.bounding_walls.append(data)
                elif type(data) is Wall:
                    self.walls.append(data)


def construct_walls(pixel_map):
    walls = []
    for y, row in enumerate(pixel_map):
        for x, element in enumerate(row):
            if is_wall(x,y,pixel_map):
                walls.append(Wall(x,y))
    return walls

def construct_bounding_walls(pixel_map):
    bounding_walls = []
    for y, row in enumerate(pixel_map):
        for x, element in enumerate(row):
            if is_bounding(x,y, pixel_map):
                bounding_walls.append(Wall(x,y, pygame.color.THECOLORS['aquamarine4']))
    return bounding_walls

def is_wall(x, y, pixel_map):
    color = pixel_map[y][x]
    return color == (0, 0, 0, 255) or color == (0,0,0)


def is_empty(x, y, pixel_map):
    color = pixel_map[y][x]
    return color == (255, 255, 255, 255) or color == (255,255,255)

def is_bounding(x, y, pixel_map):
    # Assuming pixel map non-empty
    # minus one because of indices
    if is_wall(x, y, pixel_map):
        max_x = len(pixel_map[0]) - 1
        max_y = len(pixel_map) - 1
        for v in [-1, 0, 1]:
            point_x = x + v
            for k in [-1, 0, 1]:
                point_y = y + k
                if 0 <= point_x <= max_x and 0 <= point_y <= max_y:
                    # Then we can check this point
                    if is_empty(point_x, point_y, pixel_map):
                        # An empty square
                        return True
    else:
        return False


def classify_bounding_walls(bounding_walls, filename):
    # construct simple representation
    blank_map = create_blank_map(filename)
    for b_wall in bounding_walls:
        blank_map[b_wall.y_idx][b_wall.x_idx] = b_wall

    # Indices max
    max_x = len(blank_map[0]) - 1
    max_y = len(blank_map) - 1

    for y in range(len(blank_map)):
        for x in range(len(blank_map[y])):
            if blank_map[y][x]:
                wall = blank_map[y][x]
                around = []
                #circular = [(-1,-1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
                circular = [(0, -1), (1, 0), (0, 1), (-1, 0)]
                for i, j in circular:
                    point_x = x + i
                    point_y = y + j
                    # If these are valid indices
                    if 0 <= point_x <= max_x and 0 <= point_y <= max_y:
                        if blank_map[point_y][point_x]:
                            around.append(True)
                        else:
                            around.append(False)
                    else:
                            around.append(False)

                wall.visible_sides = [not x for x in around]



