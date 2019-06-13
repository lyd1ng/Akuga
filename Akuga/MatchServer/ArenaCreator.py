from random import randint
from Akuga.MatchServer.Arena import (ArenaTile, Arena)


def create_arena(width, height, min_bonus, max_bonus):
    """
    Just creates an arena out of a 2d array of tiles
    without any ArenaTile special ability
    """
    tiles = []
    """
    Go through x and then y, this way you address a tile with the more
    convenient way [x][y] instead of [y][x]
    """
    for x in range(0, width):
        row = []
        for y in range(0, height):
            color_boni = {}
            color_boni["red"] = (
                randint(min_bonus, max_bonus),
                randint(min_bonus, max_bonus))
            color_boni["blue"] = (
                randint(min_bonus, max_bonus),
                randint(min_bonus, max_bonus))
            color_boni["green"] = (
                randint(min_bonus, max_bonus),
                randint(min_bonus, max_bonus))
            color_boni["black"] = (
                randint(min_bonus, max_bonus),
                randint(min_bonus, max_bonus))
            row.append(ArenaTile(color_boni))
        tiles.append(row)
    return Arena(tiles, width, height)
