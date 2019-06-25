from Akuga.MatchServer.Player import (Player, NeutralPlayer)


class PlayerNode:
    """
    Represents a node in a chain of players.
    """
    def __init__(self, player, prev_player_node, next_player_node):
        """
        A PlayerNode is a node within a circular double linked list
        so the prev and next has to be known
        """
        self.player = player
        self.prev_player_node = prev_player_node
        self.next_player_node = next_player_node

    def set_next(self, next_player_node):
        """
        Set the next node
        """
        self.next_player_node = next_player_node

    def set_prev(self, prev_player_node):
        """
        Set the prev node
        """
        self.prev_player_node = prev_player_node

    def get_next(self):
        """
        Get the next node
        """
        return self.next_player_node

    def get_prev(self):
        """
        Get the prev node
        """
        return self.prev_player_node

    def get_next_player(self):
        """
        Get the player of the next node
        """
        return self.next_player_node.player

    def get_player(self):
        """
        Get the player of this node
        """
        return self.player


class PlayerChain:
    """
    Represents a circular chain of players
    which is used to determine which player is the current player
    Dead players are removed from this chain for obvious reasons.
    The PlayerChain stores the start, the end as well as the current node.
    The current node is used to determine the current player
    """
    def __init__(self, start_player, end_player):
        self.startNode = PlayerNode(start_player, None, None)
        self.endNode = PlayerNode(end_player, self.startNode, self.startNode)
        self.startNode.set_next(self.endNode)
        self.startNode.set_prev(self.endNode)
        self.currentNode = self.startNode
        self.len = 2
        self.not_neutral_len = 2

    def get_length(self):
        """
        Return the absolute length of the player chain
        """
        return self.len

    def get_not_neutral_length(self):
        """
        Return the length of the player chain without neutral players
        """
        return self.not_neutral_len

    def insert_player(self, player):
        """
        Insert a player a the "end" of the chain. This way the new node
        becomes the end node
        """
        newNode = PlayerNode(player, self.endNode, self.startNode)
        self.endNode.set_next(newNode)
        self.endNode = newNode
        self.startNode.set_prev(self.endNode)
        self.len += 1
        if type(player) is not NeutralPlayer:
            self.not_neutral_len += 1

    def remove_player(self, player):
        """
        Removes a player from the chain
        """
        # A temporary node pointer to walk through the chain
        node_pointer = self.startNode
        while True:
            if node_pointer.get_player() is player:
                """
                If the current player dies jump to the prev player
                cause of the end of turn next_players_turn will be invoked
                so the current player is going to be the player after
                the one who died.
                """
                if node_pointer is self.currentNode:
                    self.currentNode = self.currentNode.get_prev()
                # If the matching node is the start node update it
                if node_pointer is self.startNode:
                    self.startNode = self.startNode.get_next()
                # If the matching node is the end node update it
                if node_pointer is self.endNode:
                    self.endNode = self.endNode.get_prev()
                # Set the next of the prev to the next of the current node
                node_pointer.get_prev().set_next(node_pointer.get_next())
                # Set the prev of the next to the prev of the current node
                node_pointer.get_next().set_prev(node_pointer.get_prev())
                # Decrement the length of the chain
                self.len -= 1
                if type(node_pointer.get_current_player()) is not NeutralPlayer:
                    self.not_neutral_len -= 1
                break
            # Jump to the next node to walk through the chain
            node_pointer = node_pointer.get_next()
            """
            If now the node_pointer is the start node it jumped from the
            end node to the start node, the chain has been walked through
            and no matching player was found
            """
            if node_pointer is self.startNode:
                break

    def remove_node(self, node):
        """
        Removes a node from the chain
        """
        # If the current player dies instantly jump to the next player
        if node is self.currentNode:
            self.currentNode = self.currentNode.get_prev()
        # If the matching node is the start node update it
        if node is self.startNode:
            self.startNode = self.startNode.get_next()
        # If the matching node is the end node update it
        if node is self.endNode:
            self.endNode = self.endNode.get_prev()
        # Set the next of the prev to the next of the current node
        node.get_prev().set_next(node.get_next())
        # Set the prev of the next to the prev of the current node
        node.get_next().set_prev(node.get_prev())
        # Decrement the length of the chain by 1
        self.len -= 1
        if type(node.get_player()) is not NeutralPlayer:
            self.not_neutral_len -= 1

    def update(self):
        """
        Removes dead player from the player chain
        """
        node_pointer = self.startNode
        while True:
            if node_pointer.get_player().is_dead():
                self.remove_node(node_pointer)
            # Leave the loop if every node has been walked through
            if node_pointer is self.endNode:
                break
            # Walk through the list of players
            node_pointer = node_pointer.get_next()

    def next_players_turn(self):
        """
        Go to the next players turn
        """
        self.currentNode = self.currentNode.get_next()

    def prev_players_turn(self):
        """
        Go to the prev players turn
        """
        self.currentNode = self.currentNode.get_prev()

    def get_current_player(self):
        """
        Get the current player
        """
        return self.currentNode.get_player()

    def get_players(self):
        """
        Get all players in a list
        """
        node_pointer = self.startNode
        player_list = []
        while True:
            player_list.append(node_pointer.get_player())
            # Walk through the list of players
            if node_pointer is self.endNode:
                break
            node_pointer = node_pointer.get_next()
        return player_list

    def __str__(self):
        """
        Return the name of every player in the playerchain
        """
        string_representation = ''
        node_pointer = self.startNode
        while True:
            string_representation += node_pointer.get_player().name + ' '
            # Walk through the list of players
            node_pointer = node_pointer.get_next()
            if node_pointer is self.endNode:
                break
        return string_representation


if __name__ == "__main__":
    """
    A small testprogramm using strings as players
    """
    player1 = Player("player1", [])
    player2 = Player("player2", [])
    player3 = Player("neutral", [])
    player_chain = PlayerChain(player1, player2)
    player_chain.insert_player(player3)

    print(player_chain.get_players())
    print(str(player_chain))
