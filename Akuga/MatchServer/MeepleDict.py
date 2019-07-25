"""
This module contain the name_constructor dict and other functions
to build up the pickpool and translate the active sets of all users
to a list of jumon instances
"""
from Akuga.MatchServer.Meeple import Jumon


JUMON_NAME_CONSTRUCTOR_DICT = {
    'Stumblestone':
        lambda _id: Jumon('Stumblestone', _id, 'blue', 350, 680, 1),
    'Orgenthor die Zwillingsbrut':
        lambda _id: Jumon('Orgenthor die Zwillingsbrut', _id, 'red', 800, 700, 1),
    'Engel des Eisenbaumwaldes':
        lambda _id: Jumon('Engel des Eisenbaumwaldes', _id, 'green', 600, 600, 2),
    'Unkrautjaehter':
        lambda _id: Jumon('Unkrautjaehter', _id, 'green', 660, 520, 1),
    'Krieger des Schattenstamms':
        lambda _id: Jumon('Krieger des Schattenstamms', _id, 'black', 660, 630, 1),
    'Steppenlaeufer':
        lambda _id: Jumon('Steppenlaeufer', _id, 'blue', 410, 450),
    'Kriselkrabbe':
        lambda _id: Jumon('Kriselkrabbe', _id, 'red', 440, 430),
    'Kopfgeldjaegerin Saphira':
        lambda _id: Jumon('Kopfgeldjaeger Saphira', _id, 'red', 600, 575, 1),
    'Wandersproessling':
        lambda _id: Jumon('Wandersproessling', _id, 'green', 370, 370, 1),
    'Erenorg Koenig der Wueste':
        lambda _id: Jumon('Erenorg Koenig der Wueste', _id, 'black', 750, 750, 1),
    'Phoenixkueken':
        lambda _id: Jumon('Phoenixkueken', _id, 'blue', 400, 370, 1),
    'Plodher':
        lambda _id: Jumon('Plodher', _id, 'green', 435, 435, 1)
}

if __name__ == '__main__':
    print(JUMON_NAME_CONSTRUCTOR_DICT['Jumon1'])
