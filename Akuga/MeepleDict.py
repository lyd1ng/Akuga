from Akuga.Meeple import (Jumon, TestNeutralJumon)

"""
This module contains a dictionary with all meeples in the game
stored under their name. Every other part of the program will
reference this meeples. This is used to translate the meeple names
within the commands send over the internet to a the meeple references.
"""

MeepleDict = {
    "Jumon1\n": Jumon("Jumon1\n", "red", 400, 1, None, None),
    "Jumon2": Jumon("Jumon2", "blue", 400, 1, None, None),
    "Jumon3": Jumon("Jumon3", "green", 400, 1, None, None),
    "Jumon4": Jumon("Jumon4", "black", 400, 1, None, None),
    "Jumon5": Jumon("Jumon5", "white", 400, 1, None, None),
    "NeutralJumon1": TestNeutralJumon("NeutralJumon1", None)
}


def GetMeepleByName(meeple_name):
    """
    Get a meeple by its name
    """
    return MeepleDict[meeple_name]
