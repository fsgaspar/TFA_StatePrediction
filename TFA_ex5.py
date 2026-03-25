from typing import Tuple, Optional
from TimedAutomaton import TimedFiniteAutomaton
from graphviz import Digraph


# Define la función de temporización Γ con intervalos en el formato (m, n, m_inclusive, n_inclusive)
def timing_function(transition: Tuple[str, str, str]) -> Tuple[float, float, bool, bool]:
    timing_map = {
        ("x0", "e1", "x1"): (0, float('inf'), True, False),
        ("x1", "(e2)", "x2"): (15, 20, True, True),
        ("x2", "(e3)", "x3"): (60, 80, True, True),
        ("x3", "e4", "x4"): (0, 600, True, True),
        ("x4", "e5", "x5"): (0, 300, True, True),
        ("x4", "e6", "x6"): (0, float('inf'), True, False)
    }
    return timing_map.get(transition, (0, 0, True, True))

# Define la función de reinicio con intervalos en el formato (m, n, m_inclusive, n_inclusive)
def reset_function(transition: Tuple[str, str, str]) -> Optional[Tuple[float, float, bool, bool]]:
    reset_map = {
        ("x0", "e1", "x1"): (0, 0, True, True),
        ("x1", "(e2)", "x2"): (0, 0, True, True),
        ("x2", "(e3)", "x3"): None,
        ("x3", "e4", "x4"): (0, 0, True, True),
        ("x4", "e5", "x5"): None,
        ("x4", "e6", "x6"): None,
    }
    return reset_map.get(transition, None)

def define_example5():
    # Definir los parámetros del autómata
    states = {"x0", "x1", "x2", "x3", "x4", "x5", "x6"}
    events = {"e1","(e2)","(e3)","e4","e5","e6"}
    transitions = {
        ("x0", "e1", "x1"),
        ("x1", "(e2)", "x2"),
        ("x2", "(e3)", "x3"),
        ("x3", "e4", "x4"),
        ("x4", "e5", "x5"),
        ("x4", "e6", "x6")
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