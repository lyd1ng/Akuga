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

    def InsertPlayer(self, player):
        """
        Insert a player a the "end" of the chain. This way the new node
        becomes the end node
        """
        newNode = PlayerNode(player, self.endNode, self.startNode)
        self.endNode.SetNext(newNode)
        self.endNode = newNode
        self.startNode.SetPrev(self.endNode)

    def RemovePlayer(self, player):
        """
        Removes a player from the chain
        """
        # A temporary node pointer to walk through the chain
        node_pointer = self.startNode
        while True:
            if node_pointer.GetPlayer() is player:
                print("Found player:" + node_pointer.GetPlayer())
                # If the current player dies instantly jump to the next player
                if node_pointer is self.currentNode:
                    print(node_pointer.GetPlayer() + " is the current_player")
                    self.currentNode = self.currentNode.GetNext()
                # If the matching node is the start node update it
                if node_pointer is self.startNode:
                    print("Node is the start node")
                    self.startNode = self.startNode.GetNext()
                # If the matching node is the end node update it
                if node_pointer is self.endNode:
                    self.endNode = self.endNode.GetPrev()
                # Set the next of the prev to the next of the current node
                node_pointer.GetPrev().SetNext(node_pointer.GetNext())
                # Set the prev of the next to the prev of the current node
                node_pointer.GetNext().SetPrev(node_pointer.GetPrev())
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
    player_chain = PlayerChain("Player1", "Player2")
    player_chain.InsertPlayer("Player3")
    for i in range(0, 5):
        print(player_chain.GetCurrentPlayer())
        player_chain.NextPlayersTurn()
    print("Player 3 dies...")
    player_chain.RemovePlayer("Player3")
    for i in range(0, 10):
        print(player_chain.GetCurrentPlayer())
        player_chain.NextPlayersTurn()
