from random import randint
from Akuga.Arena import (ArenaTile, Arena)


def CreateArena(width, height, min_bonus, max_bonus):
    """
    Just creates an arena out of a 2d array of tiles
    without any ArenaTile special ability
    """
    tiles = []
    for y in range(0, height):
        row = []
        for x in range(0, width):
            color_boni = {}
            color_boni["red"] = randint(min_bonus, max_bonus)
            color_boni["blue"] = randint(min_bonus, max_bonus)
            color_boni["green"] = randint(min_bonus, max_bonus)
            color_boni["black"] = randint(min_bonus, max_bonus)
            color_boni["white"] = randint(min_bonus, max_bonus)
            row.append(ArenaTile(color_boni, None))
        tiles.append(row)
    return Arena(tiles)
