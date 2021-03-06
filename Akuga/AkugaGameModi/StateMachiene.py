class StateMachiene():
    """
    Represents the state machiene which will handle most of the
    game logic. It will invoke the the run function of the current
    state and jump to the state the run function of the current
    state has provided. Every entry in the data dict will be used
    globally within the states
    """
    def __init__(self, start_state):
        """
        Just set the current state
        """
        self.current_state = start_state
        # Add the start state with its name to the fsm
        start_state.fsm = self
        self.__dict__[start_state.name] = start_state

    def add_state(self, state):
        """
        Add a state to the list of states under its name
        """
        state.fsm = self
        self.__dict__[state.name] = state

    def add_data(self, data_name, data):
        """
        Add variable data to the fsm under the name data_name
        """
        self.__dict__[data_name] = data

    def run(self, event):
        """
        Invoke the run function of the current state
        and eventually set change the state
        """
        result = self.current_state.run(event)
        if result is not None:
            """
            If the result of the new state is not None
            change the current state and set the state variables
            """
            next_state = result[0]
            next_state_variables = result[1]
            self.current_state = next_state
            self.current_state.state_variables = next_state_variables
