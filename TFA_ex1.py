from typing import Tuple, Optional
from TimedAutomaton import TimedFiniteAutomaton

# Define la función de temporización Γ con intervalos en el formato (m, n, m_inclusive, n_inclusive)
def timing_function(transition: Tuple[str, str, str]) -> Tuple[float, float, bool, bool]:
    timing_map = {
        ("x0", "c", "x1"): (1, 3, True, True),
        ("x0", "b", "x2"): (0, 1, True, True),
        ("x1", "a", "x4"): (1, 3, True, True),
        ("x2", "c", "x3"): (1, 2, True, True),
        ("x3", "a", "x2"): (0, 2, True, True),
        ("x4", "b", "x3"): (0, 1, True, True)
    }
    return timing_map.get(transition, (0, 0, True, True))

# Define la función de reinicio con intervalos en el formato (m, n, m_inclusive, n_inclusive)
def reset_function(transition: Tuple[str, str, str]) -> Optional[Tuple[float, float, bool, bool]]:
    reset_map = {
        ("x0", "c", "x1"): (1, 1, True, True),
        ("x1", "a", "x4"): (0, 1, True, True),
        ("x3", "a", "x2"): (0, 0, True, True),
        ("x4", "b", "x3"): (0, 0, True, True)
    }
    return reset_map.get(transition, None)

def define_example1():
    # Definir los parámetros del autómata
    states = {"x0", "x1", "x2", "x3", "x4"}
    events = {"a", "b", "c"}
    transitions = {
        ("x0", "c", "x1"),
        ("x0", "b", "x2"),
        ("x1", "a", "x4"),
        ("x2", "c", "x3"),
        ("x3", "a", "x2"),
        ("x4", "b", "x3")
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
