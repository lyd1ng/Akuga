from Akuga.Player import (Player, NeutralPlayer)


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

    def SetNext(self, next_player_node):
        """
        Set the next node
        """
        self.next_player_node = next_player_node

    def SetPrev(self, prev_player_node):
        """
        Set the prev node
        """
        self.prev_player_node = prev_player_node

    def GetNext(self):
        """
        Get the next node
        """
        return self.next_player_node

    def GetPrev(self):
        """
        Get the prev node
        """
        return self.prev_player_node

    def GetNextPlayer(self):
        """
        Get the player of the next node
        """
        return self.next_player_node.player

    def GetPlayer(self):
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
        self.startNode.SetNext(self.endNode)
        self.startNode.SetPrev(self.endNode)
        self.currentNode = self.startNode
        self.len = 2
        self.not_neutral_len = 2

    def GetLength(self):
        """
        Return the absolute length of the player chain
        """
        return self.len

    def GetNotNeutralLength(self):
        """
        Return the length of the player chain without neutral players
        """
        return self.not_neutral_len

    def InsertPlayer(self, player):
        """
        Insert a player a the "end" of the chain. This way the new node
        becomes the end node
        """
        newNode = PlayerNode(player, self.endNode, self.startNode)
        self.endNode.SetNext(newNode)
        self.endNode = newNode
        self.startNode.SetPrev(self.endNode)
        self.len += 1
        if type(player) is not NeutralPlayer:
            self.not_neutral_len += 1

    def RemovePlayer(self, player):
        """
        Removes a player from the chain
        """
        # A temporary node pointer to walk through the chain
        node_pointer = self.startNode
        while True:
            if node_pointer.GetPlayer() is player:
                """
                If the current player dies jump to the prev player
                cause of the end of turn NextPlayersTurn will be invoked
                so the current player is going to be the player after
                the one who died.
                """
                if node_pointer is self.currentNode:
                    self.currentNode = self.currentNode.GetPrev()
                # If the matching node is the start node Update it
                if node_pointer is self.startNode:
                    self.startNode = self.startNode.GetNext()
                # If the matching node is the end node Update it
                if node_pointer is self.endNode:
                    self.endNode = self.endNode.GetPrev()
                # Set the next of the prev to the next of the current node
                node_pointer.GetPrev().SetNext(node_pointer.GetNext())
                # Set the prev of the next to the prev of the current node
                node_pointer.GetNext().SetPrev(node_pointer.GetPrev())
                # Decrement the length of the chain
                self.len -= 1
                if type(node_pointer.GetCurrentPlayer()) is not NeutralPlayer:
                    self.not_neutral_len -= 1
                return
            # Jump to the next node to walk through the chain
            node_pointer = node_pointer.GetNext()
            """
            If now the node_pointer is the start node it jumped from the
            end node to the start node, the chain has been walked through
            and no matching player was found
            """
            if node_pointer is self.startNode:
                break

    def RemoveNode(self, node):
        """
        Removes a node from the chain
        """
        # If the current player dies instantly jump to the next player
        if node is self.currentNode:
            self.currentNode = self.currentNode.GetPrev()
        # If the matching node is the start node Update it
        if node is self.startNode:
            self.startNode = self.startNode.GetNext()
        # If the matching node is the end node Update it
        if node is self.endNode:
            self.endNode = self.endNode.GetPrev()
        # Set the next of the prev to the next of the current node
        node.GetPrev().SetNext(node.GetNext())
        # Set the prev of the next to the prev of the current node
        node.GetNext().SetPrev(node.GetPrev())
        # Decrement the length of the chain by 1
        self.len -= 1
        if type(node.GetPlayer()) is not NeutralPlayer:
            self.not_neutral_len -= 1

    def Update(self):
        """
        Removes dead player from the player chain
        """
        node_pointer = self.startNode
        while True:
            if node_pointer.GetPlayer().IsDead():
                self.RemoveNode(node_pointer)
            # Leave the loop if every node has been walked through
            if node_pointer is self.endNode:
                break
            # Walk through the list of players
            node_pointer = node_pointer.GetNext()

    def CheckForVictory(self):
        """
        Checks if a player has won and return per
        There are two cases which have to be checked
        1. There is only one not neutral player left
        2. A player has won with an alternative win condition
        1:
        Go throug the whole list and count the number of non neutral
        players, safe the last not neutral player as this will be the
        victor if the number of non neutral players is 1
        """
        not_neutral_player = None
        not_neutral_player_count = 0
        node_pointer = self.startNode
        while True:
            if type(node_pointer.GetPlayer()) is not NeutralPlayer:
                not_neutral_player_count += 1
                # Save this player, if per is the only one per is the victor
                not_neutral_player = node_pointer.GetPlayer()
            if node_pointer is self.endNode:
                """
                If the whole chane has been walked through break the loop
                """
                break
            # Jump to the next node
            node_pointer = node_pointer.GetNext()
        if not_neutral_player_count == 1:
            # Check the result and return the victor if there is one
            return not_neutral_player

        node_pointer = self.startNode
        """
        2:
        Go through the whole list and check if the current player is non
        neutral and if the player has won regardless of still existing
        opponents. This may occure with alternative win conditions
        """
        while True:
            if node_pointer.GetPlayer().HasWon() and\
                    type(self.startNode.GetPlayer()) is not NeutralPlayer:
                return node_pointer.GetPlayer()
            # Walk through the list of players
            node_pointer = node_pointer.GetNext()
            """
            If node_pointer now is the start node it jumped from the end node
            to the start node which means all nodes has been walked through
            """
            if node_pointer is self.startNode:
                break
        return None

    def CheckForDrawn(self):
        """
        Returns if all not neutral players are dead
        """
        return self.len == 0 or (self.len == 1 and type(self.startNode.
            GetPlayer()) is NeutralPlayer)

    def NextPlayersTurn(self):
        """
        Go to the next players turn
        """
        self.currentNode = self.currentNode.GetNext()

    def PrevPlayersTurn(self):
        """
        Go to the prev players turn
        """
        self.currentNode = self.currentNode.GetPrev()

    def GetCurrentPlayer(self):
        """
        Get the current player
        """
        return self.currentNode.GetPlayer()


if __name__ == "__main__":
    """
    A small testprogramm using strings as players
    """
    player1 = Player("player1", [])
    player2 = Player("player2", [])
    player3 = Player("neutral", [])
    player_chain = PlayerChain(player1, player2)
    player_chain.InsertPlayer(player3)

    print(player_chain.GetCurrentPlayer().name)  # player1
    player_chain.NextPlayersTurn()
    print(player_chain.GetCurrentPlayer().name)  # player2
    player_chain.NextPlayersTurn()
    print(player_chain.GetCurrentPlayer().name)  # neutral
    player_chain.GetCurrentPlayer().Kill()
    player_chain.Update()
    player_chain.NextPlayersTurn()
    print(player_chain.GetCurrentPlayer().name)  # ???
