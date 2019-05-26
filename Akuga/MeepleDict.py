from Akuga.Meeple import (Jumon, TestNeutralJumon)

MeepleDict = {
    "Jumon1\n": Jumon("Jumon1\n", "red", 400, 1, None, None),
    "Jumon2": Jumon("Jumon2", "blue", 400, 1, None, None),
    "Jumon3": Jumon("Jumon3", "green", 400, 1, None, None),
    "Jumon4": Jumon("Jumon4", "black", 400, 1, None, None),
    "Jumon5": Jumon("Jumon5", "white", 400, 1, None, None),
    "NeutralJumon1": TestNeutralJumon("NeutralJumon1", None)
}


def GetMeepleByName(meeple_name):
    return MeepleDict[meeple_name]
