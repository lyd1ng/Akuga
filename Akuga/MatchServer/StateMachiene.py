from .. import GlobalDefinitions as gd


class StateMachiene():
    """
    Represents the state machiene which will handle most of the
    game logic. It will invoke the the Run function of the current
    state and jump to the state the Run function of the current
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
        exec("self." + start_state.name + " = start_state")

    def AddState(self, state):
        """
        Add a state to the list of states under its name
        """
        state.fsm = self
        exec("self." + state.name + " = state")

    def AddData(self, data_name, data):
        """
        Add variable data to the fsm under the name data_name
        """
        exec("self." + data_name + " = data")

    def Run(self, event):
        """
        Invoke the Run function of the current state
        and eventually set change the state
        """
        print("Run: " + self.current_state.name if gd.DEBUG else "")
        result = self.current_state.Run(event)
        if result is not None:
            """
            If the result of the new state is not None
            change the current state and set the state variables
            """
            next_state = result[0]
            next_state_variables = result[1]
            self.current_state = next_state
            self.current_state.state_variables = next_state_variables
            print("Change State to: " + next_state.name if gd.DEBUG else "")
