from typing import Tuple, Optional
from TimedAutomaton import TimedFiniteAutomaton


# Timing function Γ
def timing_function(transition: Tuple[str, str, str]) -> Tuple[float, float, bool, bool]:
    timing_map = {

        # Start
        ("x0", "e1", "x1"): (0, 10, True, True),

        # Branching
        ("x1", "e2", "x2"): (2, 20, True, True),
        ("x1", "e3", "x3"): (1, 15, True, True),

        # Self-loop observable
        ("x2", "e4", "x2"): (5, 25, True, True),

        # Hidden reset loop (important stress case)
        ("x2", "(e5)", "x2"): (10, 30, True, True),

        # Move forward
        ("x2", "e6", "x4"): (15, 40, True, True),

        # Hidden chain
        ("x4", "(e7)", "x5"): (5, 10, True, True),
        ("x5", "(e8)", "x6"): (3, 12, True, True),

        # Observable progression
        ("x6", "e9", "x7"): (20, 60, True, True),

        # Return backward in the graph
        ("x7", "e10", "x3"): (5, 30, True, True),

        # Another hidden reset
        ("x3", "(e11)", "x8"): (4, 14, True, True),

        # Loop back to earlier state
        ("x8", "e12", "x2"): (25, 80, True, True),

        # Alternative path forward
        ("x3", "e13", "x9"): (10, 50, True, True),

        # Hidden cascade
        ("x9", "(e14)", "x10"): (6, 18, True, True),
        ("x10", "(e15)", "x11"): (8, 22, True, True),

        # Self-loop hidden reset (very hard case)
        ("x11", "(e16)", "x11"): (5, 40, True, True),

        # Final observable exit
        ("x11", "e17", "x12"): (30, 120, True, True),

        # Re-enter system
        ("x12", "e18", "x4"): (60, 200, True, True),
    }

    return timing_map.get(transition, (0, 0, True, True))


# Reset function
def reset_function(transition: Tuple[str, str, str]) -> Optional[Tuple[float, float, bool, bool]]:
    reset_map = {

        ("x0", "e1", "x1"): (0, 0, True, True),

        ("x1", "e2", "x2"): (0, 0, True, True),
        ("x1", "e3", "x3"): (0, 0, True, True),

        ("x2", "(e5)", "x2"): (0, 0, True, True),  # hidden reset loop
        ("x2", "e6", "x4"): (0, 0, True, True),

        ("x4", "(e7)", "x5"): (0, 0, True, True),
        ("x5", "(e8)", "x6"): None,

        ("x6", "e9", "x7"): (0, 0, True, True),

        ("x3", "(e11)", "x8"): (0, 0, True, True),

        ("x8", "e12", "x2"): None,

        ("x9", "(e14)", "x10"): (0, 0, True, True),
        ("x10", "(e15)", "x11"): None,

        ("x11", "(e16)", "x11"): (0, 0, True, True),  # dangerous loop

        ("x11", "e17", "x12"): (0, 0, True, True),
    }

    return reset_map.get(transition, None)


def define_example4():

    states = {
        "x0","x1","x2","x3","x4","x5","x6",
        "x7","x8","x9","x10","x11","x12"
    }

    events = {
        "e1","e2","e3","e4","(e5)","e6",
        "(e7)","(e8)","e9","e10","(e11)",
        "e12","e13","(e14)","(e15)","(e16)",
        "e17","e18"
    }

    transitions = {
        ("x0","e1","x1"),

        ("x1","e2","x2"),
        ("x1","e3","x3"),

        ("x2","e4","x2"),        # observable loop
        ("x2","(e5)","x2"),      # hidden reset loop
        ("x2","e6","x4"),

        ("x4","(e7)","x5"),
        ("x5","(e8)","x6"),

        ("x6","e9","x7"),
        ("x7","e10","x3"),

        ("x3","(e11)","x8"),
        ("x8","e12","x2"),

        ("x3","e13","x9"),

        ("x9","(e14)","x10"),
        ("x10","(e15)","x11"),

        ("x11","(e16)","x11"),   # hidden loop
        ("x11","e17","x12"),

        ("x12","e18","x4"),
    }

    initial_states = {"x0"}

    tfa = TimedFiniteAutomaton(
        states=states,
        events=events,
        transitions=transitions,
        timing_function=timing_function,
        reset_function=reset_function,
        initial_states=initial_states
    )

    return tfa