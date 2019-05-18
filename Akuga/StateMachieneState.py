class StateMachieneState:
    """
    Represents a state within the statemachiene.
    It will contain a kwarg list of arbirtrary informations
    provided by the previous state and set by the state machiene.
    It also safes the fsm its a part of. This way the data dict of the
    fsm can be used to provide variables which are globally accessable within
    all states
    """
    def __init__(self, name, fsm=None):
        """
        Set the name of the state and init the state_variables as
        an empty dictionary. It will be set by the state machiene
        """
        self.name = name
        self.fsm = fsm
        self.state_variables = {}

    def SetFSM(self, fsm):
        """
        Set the fsm
        """
        self.fsm = fsm

    def Run(self, event):
        """
        The function invoked by the state machiene if the current
        state is active.
        Returns: A tupel containing the state the state machiene should
                 jump to and the informations which should be passed to
                 the next state
        """
        pass
