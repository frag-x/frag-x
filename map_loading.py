from PIL import Image
import pygame
from enum import Enum, auto

def get_pixels(filename):
    img = Image.open(filename)
    w, h = img.size
    pix = list(img.getdata())
    return [pix[n:n+w] for n in range(0, w*h, w)]

def create_blank_map(filename):
    img = Image.open(filename)
    w, h = img.size
    return [[None for x in range(w)] for y in range(h)]


class Map:
    def __init__(self, walls):
        pass

class SquareWall:
    def __init__(self, x, y, color = pygame.color.THECOLORS['grey'], size = 32):
        self.size = size
        self.x_idx = x
        self.y_idx = y
        self.x = x * self.size
        self.y = y * self.size
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        self.color = color
        self.visible_sides = None

def construct_walls(pixel_map):
    walls = []
    for y, row in enumerate(pixel_map):
        for x, element in enumerate(row):
            if is_wall(x,y,pixel_map):
                walls.append(SquareWall(x,y))
    return walls

def construct_bounding_walls(pixel_map):
    bounding_walls = []
    for y, row in enumerate(pixel_map):
        for x, element in enumerate(row):
            if is_bounding(x,y, pixel_map):
                bounding_walls.append(SquareWall(x,y, pygame.color.THECOLORS['aquamarine4']))
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



