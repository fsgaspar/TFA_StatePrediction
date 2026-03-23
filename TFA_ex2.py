from typing import Tuple, Optional
from TimedAutomaton import TimedFiniteAutomaton
from graphviz import Digraph


# Define la función de temporización Γ con intervalos en el formato (m, n, m_inclusive, n_inclusive)
def timing_function(transition: Tuple[str, str, str]) -> Tuple[float, float, bool, bool]:
    timing_map = {
        ("x0", "e1", "x1"): (0, float('inf'), True, False),
        ("x1", "e2", "x2"): (0, float('inf'), True, False),
        ("x1", "e3", "x3"): (0, float('inf'), True, False),
        ("x2", "e4", "x4"): (8640, 8640, True, True),
        ("x4", "(e5)", "x5"): (5, 15, True, True),
        ("x5", "(e6)", "x6"): (15, 30, True, True),
        ("x3", "(e7)", "x6"): (15, 30, True, True),
        ("x6", "e8", "x7"): (1080, 1560, True, True),
        ("x7", "(e9)", "x8"): (40, 50, True, True),
        ("x8", "e10", "x9"): (60, 90, True, True),
        ("x9", "(e11)", "x10"): (480, 510, True, True),
        ("x10", "(e12)", "x11"): (910, 1020, True, True),
        ("x11", "e13", "x12"): (1270, 1620, True, True)
    }
    return timing_map.get(transition, (0, 0, True, True))

# Define la función de reinicio con intervalos en el formato (m, n, m_inclusive, n_inclusive)
def reset_function(transition: Tuple[str, str, str]) -> Optional[Tuple[float, float, bool, bool]]:
    reset_map = {
        ("x0", "e1", "x1"): (0, 0, True, True),
        ("x1", "e2", "x2"): (0, 0, True, True),
        ("x1", "e3", "x3"): (0, 0, True, True),
        ("x2", "e4", "x4"): (0, 0, True, True),
        #("x4", "e5", "x5"): (5, 15, True, True),
        #("x5", "e6", "x6"): (15, 30, True, True),
        #("x3", "e7", "x6"): (15, 30, True, True),
        ("x6", "e8", "x7"): (0, 0, True, True),
        ("x7", "e9", "x8"): (0, 0, True, True),
        ("x8", "e10", "x9"): (0, 0, True, True),
        #("x9", "e11", "x10"): (480, 510, True, True),
        #("x10", "e12", "x11"): (430, 510, True, True),
        ("x11", "e13", "x12"): (0, 0, True, True)
    }
    return reset_map.get(transition, None)

def define_example2():
    # Definir los parámetros del autómata
    states = {"x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10", "x11", "x12"}
    events = {"e1","e2","e3","e4","(e5)","(e6)","(e7)","e8","(e9)","e10","(e11)","(e12)","e13"}
    transitions = {
        ("x0", "e1", "x1"),
        ("x1", "e2", "x2"),
        ("x1", "e3", "x3"),
        ("x2", "e4", "x4"),
        ("x4", "(e5)", "x5"),
        ("x5", "(e6)", "x6"),
        ("x3", "(e7)", "x6"),
        ("x6", "e8", "x7"),
        ("x7", "(e9)", "x8"),
        ("x8", "e10", "x9"),
        ("x9", "(e11)", "x10"),
        ("x10", "(e12)", "x11"),
        ("x11", "e13", "x12")
    }
    initial_states = {"x0"}

    # Inicializar el autómata temporizado
    tfa = TimedFiniteAutomaton(
        states=states,
        events=events,
        transitions=transitions,
        timing_function=timing_function,
        reset_function=reset_function,
        initial_states=initial_states
    )

    return tfa


