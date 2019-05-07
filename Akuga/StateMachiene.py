from Akuga.global_definitions import DEBUG


class StateMachiene():
    """
    Represents the state machiene which will handle most of the
    game logic. It will invoke the the run function of the current
    state and jump to the state the run function of the current
    state has provided
    """
    def __init__(self, states, start_state):
        """
        Just set the list of states within the state machiene
        and set the current state
        """
        self.states = states
        self.current_state = start_state

    def run(self, event):
        """
        Invoke the run function of the current state
        and eventually set change the state
        """
        print("Run: " + self.current_state.name if DEBUG else "")
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
            print("Change State to: " + next_state.name if DEBUG else "")
