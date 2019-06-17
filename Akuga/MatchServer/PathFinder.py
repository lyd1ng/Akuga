from Akuga.MatchServer.ArenaCreator import create_arena
from Akuga.MatchServer.Position import Position


def pos_in(position, nodes):
    """
    Checks if position exists within node_list
    """
    return next(filter(lambda x: x.position == position, nodes), None) is not None


class PathNode:
    """
    A representation of a node within the path
    """
    def __init__(self, position, predecessor):
        self.position = position
        self.predecessor = predecessor

    def expand_node(self, tiles, end_pos, frontier, visited, width, height):
        """
        Checks all four direct neighbour tiles and add them to the
        expand list if their are free and not yet in the frontier list
        """
        expand_list = []
        if self.position.x > 0:
            new_pos = self.position - Position(1, 0)
            if (not pos_in(new_pos, frontier) and tiles[new_pos.x][new_pos.y])\
                    or new_pos == end_pos:
                expand_list.append(PathNode(new_pos, self))

        if self.position.x < width - 1:
            new_pos = self.position + Position(1, 0)
            if (not pos_in(new_pos, frontier) and tiles[new_pos.x][new_pos.y])\
                    or new_pos == end_pos:
                expand_list.append(PathNode(new_pos, self))

        if self.position.y > 0:
            new_pos = self.position - Position(0, 1)
            if (not pos_in(new_pos, frontier) and tiles[new_pos.x][new_pos.y])\
                    or new_pos == end_pos:
                expand_list.append(PathNode(new_pos, self))

        if self.position.y < height - 1:
            new_pos = self.position + Position(0, 1)
            if (not pos_in(new_pos, frontier) and tiles[new_pos.x][new_pos.y])\
                    or new_pos == end_pos:
                expand_list.append(PathNode(new_pos, self))

        return expand_list


def backtrace_path(end_node):
    """
    Walkes through the predecessors until it is None, thats the start node
    """
    path = []
    current_node = end_node
    while True:
        path.append(current_node)
        current_node = current_node.predecessor
        if current_node is None:
            break
    return path


def find_path(start_position, end_position, arena):
    width = arena.board_width
    height = arena.board_width
    tiles = []
    frontier_nodes = [PathNode(start_position, None)]
    visited_nodes = []
    # Create a boolean map from the arena. True means the tile is free
    for x in range(0, width):
        row = []
        for y in range(0, height):
            row.append(arena.get_tile_at(Position(x, y)).occupied_by() is None)
        tiles.append(row)

    while len(frontier_nodes) > 0:
        """
        As long as there are nodes within the frontier list there is hope
        to find a path
        """
        expand_list = frontier_nodes[0].expand_node(tiles, end_position, frontier_nodes, visited_nodes, width, height)
        visited_nodes.append(frontier_nodes[0])
        frontier_nodes.remove(frontier_nodes[0])
        potentiel_end_node = next(filter(lambda x: x.position == end_position,
            visited_nodes), None)
        if potentiel_end_node:
            return backtrace_path(potentiel_end_node)
        frontier_nodes = frontier_nodes + expand_list
    return None


if __name__ == "__main__":
    width = 5
    height = 5
    arena = create_arena(width, height, 0, 0)
    # block a tile
    arena.place_unit_at("A", Position(0, 0))
    arena.place_unit_at("A", Position(1, 0))
    arena.place_unit_at("A", Position(0, 2))

    arena.place_unit_at("A", Position(2, 2))

    path = find_path(Position(4, 4), Position(2, 2), arena)
    if path is None:
        exit(-1)
    print(len(path))
    for p in path:
        print(str(p.position))
