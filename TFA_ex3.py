from typing import Tuple, Optional
from TimedAutomaton import TimedFiniteAutomaton

# Define the timing function with intervals: (m, n, m_inclusive, n_inclusive)
def timing_function(transition: Tuple[str, str, str]) -> Tuple[float, float, bool, bool]:
    timing_map = {
        # Initial observable start
        ("x0", "e1", "x1"): (0, 0, True, True),
        
        # Branch 1: Unobservable transition that resets the clock
        ("x1", "(e2)", "x2"): (2, 5, True, True),
        # Observable continuation from Branch 1
        ("x2", "e3", "x4"): (1, 3, True, True),
        
        # Branch 2: Observable transition that resets the clock
        ("x1", "e4", "x3"): (4, 6, True, True),
        # Unobservable continuation from Branch 2
        ("x3", "(e5)", "x5"): (2, 4, True, True),
        
        # Joining the branches: Unobservable reset vs Observable no-reset
        ("x4", "(e6)", "x6"): (2, 4, True, True),
        ("x5", "e7", "x6"): (3, 5, True, True)
    }
    # Default to [0, 0] if not found
    return timing_map.get(transition, (0, 0, True, True))

# Define the reset function: returns an interval (typically [0,0]) or None
def reset_function(transition: Tuple[str, str, str]) -> Optional[Tuple[float, float, bool, bool]]:
    reset_map = {
        ("x0", "e1", "x1"): (0, 0, True, True),      # Observable reset
        
        ("x1", "(e2)", "x2"): (0, 0, True, True),    # UNOBSERVABLE RESET!
        #("x1", "(e2)", "x2"): None,    
        ("x2", "e3", "x4"): None,                    # No reset
        
        ("x1", "e4", "x3"): (0, 0, True, True),      # Observable reset
        ("x3", "(e5)", "x5"): None,                  # No reset
        
        ("x4", "(e6)", "x6"): (0, 0, True, True),    # UNOBSERVABLE RESET!
        ("x5", "e7", "x6"): None                     # No reset
    }
    return reset_map.get(transition, None)

def define_example3():
    # Define the automaton parameters
    states = {"x0", "x1", "x2", "x3", "x4", "x5", "x6"}
    events = {"e1", "(e2)", "e3", "e4", "(e5)", "(e6)", "e7"}
    transitions = {
        ("x0", "e1", "x1"),
        ("x1", "(e2)", "x2"),
        ("x2", "e3", "x4"),
        ("x1", "e4", "x3"),
        ("x3", "(e5)", "x5"),
        ("x4", "(e6)", "x6"),
        ("x5", "e7", "x6")
    }
    initial_states = {"x0"}

    # Initialize the TFA
    tfa = TimedFiniteAutomaton(
        states=states,
        events=events,
        transitions=transitions,
        timing_function=timing_function,
        reset_function=reset_function,
        initial_states=initial_states
    )

    return tfa