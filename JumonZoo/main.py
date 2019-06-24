import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from functools import reduce

DB_PATH = './jumonzoo.db'


def query_db(cursor, colors=['black', 'green', 'red', 'blue'], special=None):
    '''
    Query the db for all jumons with the specified color(s) and special
    ability
    '''
    # Create a query out of the color list
    color_query = '(color=\'' + colors[0] + '\''
    for i in range(1, len(colors)):
        color_query = color_query + ' or color=\'' + colors[i] + '\''
    color_query += ')'
    # Create a query for the special ability
    special_query = ''
    if special is not None:
        special_query = 'and special=' + str(special)
    query = 'select name,attack,defense from jumons where '\
        + color_query + ' ' + special_query
    print(query)
    cursor.execute(query)
    return cursor.fetchall()


def plot_jumons(jumons):
    '''
    Plot the jumons using matploblip
    '''
    print(jumons)
    # return None
    # Create a x index for every jumon
    x_indices = np.arange(len(jumons))
    # Create a subplot
    axis = plt.subplot(111)
    # Set the xticklabels to the name of the jumons
    plt.xticks(x_indices, rotation=45.0)
    plt.subplots_adjust(bottom=0.25)
    axis.set_xticklabels(list(map(lambda x: x[0], jumons)), ha='right')
    # Create the bar chart for the attack and defense values
    axis.bar(x_indices - 0.1, list(map(lambda x: x[1], jumons)), 0.2, color='red')
    axis.bar(x_indices + 0.1, list(map(lambda x: x[2], jumons)), 0.2, color='blue')
    # Get the average of the attack and defense values
    attack_avrg = reduce(lambda x, y: x + y, map(lambda x: x[1], jumons)) / len(jumons)
    defense_avrg = reduce(lambda x, y: x + y, map(lambda x: x[2], jumons)) / len(jumons)
    # Add a horizontal line for the average to the plot
    axis.axhline(attack_avrg, color='red')
    axis.axhline(defense_avrg, color='blue')

    plt.show()


if __name__ == '__main__':
    # Connect to the database and create a cursor
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    while True:
        packet = input('jumonzoo > ')
        tokens = packet.split(' ')
        result = []
        if len(tokens) == 1:
            # If only one token is specified no special ability is specified
            # so leave it as None
            colors = tokens[0].split(',')
            result = query_db(cursor, colors)
        if len(tokens) > 1:
            # If at least two tokens are specified interpret them as
            # colors and special
            colors = tokens[0].split(',')
            special = tokens[1]
            result = query_db(cursor, colors, special)
        plot_jumons(result)
