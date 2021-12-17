"""Utilities for parsing data returned by `hops`."""

import re


def _parse_tree_key(k):
    """Extracts coordinates from key"""
    # Extract coordinates.
    k = re.findall('{(.*?)}', k)[0]

    # Split by `;` to get individual indices.
    k = k.split(r';')

    return [int(k_) for k_ in k]


def _insert_at(mod_list, coor, data):
    """Inserts `data` into `mod_list` at `coor`.

    `coor` in general may be a list of coordinates. This function then
    recursively inserts lists until the appropriate level is reached.
    """
    if len(mod_list) < coor[0]:
        raise ValueError("List too short.")
    # TODO: Need to make clear whether this will ALWAYS add new items or
    # add to existing lists if they exis.
    if len(coor) > 1:
        # If list doesn't exist, insert one.
        if len(mod_list) <= coor[0]:
            mod_list.insert(coor[0], [])
        if not isinstance(mod_list[coor[0]], list):
            raise ValueError(
                "Cannot insert data at requested level. Not a list.")
        _insert_at(mod_list[coor[0]], coor[1:], data)
    else:
        mod_list.insert(coor[0], data)


def list_from_tree(tree):
    """Constructs list of list containing data in `tree`.

    It is useful to construct a list representation first, since different
    final indices may contain different.
    """
    address = [_parse_tree_key(k) for k in tree.keys()]
    data = tree.values()

    # Instantiate list which we will fill in whith data at `address`.
    lt = []

    [_insert_at(lt, a, d) for a, d in zip(address, data)]
    return lt
