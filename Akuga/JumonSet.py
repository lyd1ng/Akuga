"""
This module defines the JumonSet class which represents both the jumon
collection and all jumon sets a user creates.
"""
from functools import reduce


def jumon_set_from_list(jumon_name_list):
    """
    Creates a dictionary of the form jumon_name: amount
    from a list of jumon names
    """
    jumon_set = {}
    if jumon_name_list == '':
        return jumon_set
    for name in jumon_name_list:
        if name == '':
            continue
        # Insert the name of the jumon to the jumon set
        insert_name(jumon_set, name)
    return jumon_set


def insert_name(jumon_set, jumon_name):
    """
    Insert a jumon name to a jumon_set,
    that means add a new record if there is no record
    for the jumon or increment the amount of the specified record
    """
    try:
        # Just try to increment the amount of the record
        jumon_set[jumon_name] += 1
    except KeyError:
        # If there is no record for this name a KeyError is thrown
        # add a new record with an amount of 1
        jumon_set[jumon_name] = 1
    return jumon_set


def is_subset(smaller_set, larger_set):
    """
    Checks if the smaller set is a subset of the larger set
    """
    # A set is a subset of an other set if it does not contain any
    # record not present in the larger set. In this case also the amount
    # of the record has to be less than or equal to the amount of the
    # larger set
    for record in smaller_set.items():
        try:
            # If the amount of the record is larger then the amount
            # of the record in the larger set smaller_set cant be a subset
            # of the larger set
            if record[1] > larger_set[record[0]]:
                return False
        except KeyError:
            # A KeyErrors occures if the current record is not listed
            # in the larger set, so again smaller_set cant be a subset of
            # the larger set
            return False
    # If there is no record found which is not listed within the larger
    # set and all records in smaller_set have a smaller amount than the records
    # in the larger set smaller_set is a subset of the larger set.
    return True


def serialize_set(jumon_set):
    """
    Return the set as a plain string of coma delimited jumon names.
    The amount of a jumons is represented by repetitions of the name
    """
    serialized_string = ''
    for record in jumon_set.items():
        for i in range(record[1]):
            serialized_string += record[0] + ','
    # Skip the last character its a superfluous coma
    return serialized_string[:-1]


def serialize_set_to_list(jumon_set):
    """
    Return the set as a list of jumon names.
    The amount of a jumos is represented by repetitions of the item
    """
    result = []
    for record in jumon_set.items():
        for i in range(record[1]):
            result.append(record[0])
    return result


def get_set_size(jumon_set):
    """
    Returns the length of a set aka a the sum of all amounts of all elements
    """
    return reduce(lambda x, y: x + y, jumon_set.values(), 0)


if __name__ == '__main__':
    setA = jumon_set_from_list(['jumon1', 'jumon2', 'jumon2', 'jumon4'])
    setB = jumon_set_from_list(['jumon1', 'jumon2', 'jumon2', 'jumon4'])
    print(serialize_set(setA))
    print(serialize_set_to_list(setA))
    print(get_set_size(setA))
