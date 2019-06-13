import random
from Akuga.MatchServer.Meeple import (Jumon, TestNeutralJumon)

"""
This module contains a dictionary with all meeples in the game
stored under their name. Every other part of the program will
reference this meeples. This is used to translate the meeple names
within the commands send over the internet to a the meeple references.
"""

MeepleDict = {
    "Jumon1": Jumon("Jumon1", "red", 400, 400, 1, None, None),
    "Jumon2": Jumon("Jumon2", "blue", 400, 400, 1, None, None),
    "Jumon3": Jumon("Jumon3", "green", 400, 400, 1, None, None),
    "Jumon4": Jumon("Jumon4", "black", 400, 400, 1, None, None),
    "Jumon5": Jumon("Jumon5", "white", 400, 400, 1, None, None),
    "NJ1__neutral": TestNeutralJumon("NeutralJumon1", None)
}


def get_meeple_by_name(meeple_name):
    """
    Get a meeple by its name
    """
    return MeepleDict[meeple_name]


def get_neutral_meeples(amount):
    """
    Get a list of $amount neutral jumons without double occupancies
    """
    neutral_meeples = []
    pool = []
    # Filter for all neutral jumons (all jumons with a name including __neutral)
    for neutral_meeple_name in filter(lambda x: x.find("__neutral") > 1,
            list(MeepleDict.keys())):
        neutral_meeples.append(MeepleDict[neutral_meeple_name])
    # Get random jumons from the list without double occupancies
    indices_cached = []
    for i in range(0, min(amount, len(neutral_meeples))):
        random_index = random.randint(0, len(neutral_meeples) - 1)
        while random_index in indices_cached:
            random_index = random.randint(0, len(neutral_meeples) - 1)
        pool.append(neutral_meeples[random_index])
        indices_cached.append(random_index)
    return pool


def get_not_neutral_meeples(amount):
    """
    Get a list of $amount not neutral jumons without double occupancies
    """
    not_neutral_meeples = []
    pool = []
    # Filter for all non neutral jumons (all jumons with a name not including __neutral)
    for not_neutral_meeple_name in filter(lambda x: x.find("__neutral") < 0,
            list(MeepleDict.keys())):
        not_neutral_meeples.append(MeepleDict[not_neutral_meeple_name])
    # Get random jumons from the list
    indices_cached = []
    for i in range(0, min(amount, len(not_neutral_meeples))):
        random_index = random.randint(0, len(not_neutral_meeples) - 1)
        while random_index in indices_cached:
            random_index = random.randint(0, len(not_neutral_meeples) - 1)
        pool.append(not_neutral_meeples[random_index])
        indices_cached.append(random_index)
    return pool


if __name__ == "__main__":
    print(get_not_neutral_meeples(10))
    print(get_neutral_meeples(10))
