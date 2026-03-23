from typing import Set, Tuple, Callable, Optional


class TimedFiniteAutomaton:
    def __init__(self,
                 states: Set[str],
                 events: Set[str],
                 transitions: Set[Tuple[str, str, str]],
                 timing_function: Callable[[Tuple[str, str, str]], Tuple[float, float, bool, bool]],
                 reset_function: Callable[[Tuple[str, str, str]], Optional[Tuple[float, float, bool, bool]]],
                 initial_states: Set[str]):
        """
        Inicializa un autómata finito temporizado (TFA).

        :param states: Conjunto de estados discretos (X).
        :param events: Conjunto de eventos (E).
        :param transitions: Conjunto de transiciones (Δ) representadas como (estado_actual, evento, siguiente_estado).
        :param timing_function: Función Γ(Δ) que asigna a cada transición un intervalo de tiempo,
                                representado como (m, n, m_inclusive, n_inclusive).
        :param reset_function: Función Reset(Δ) que asigna a una transición un intervalo de reinicio o None (sin reinicio).
        :param initial_states: Conjunto de estados iniciales (X0).
        """
        self.states = states
        self.events = events
        self.transitions = transitions
        self.timing_function = timing_function
        self.reset_function = reset_function
        self.initial_states = initial_states

    def _is_within_interval(self, clock: float, interval: Tuple[float, float, bool, bool]) -> bool:
        lower, upper, lower_inc, upper_inc = interval
        if lower_inc:
            lower_ok = clock >= lower
        else:
            lower_ok = clock > lower
        if upper_inc:
            upper_ok = clock <= upper
        else:
            upper_ok = clock < upper
        return lower_ok and upper_ok

    def is_transition_enabled(self, state: str, event: str, clock: float) -> bool:
        """
        Verifica si una transición está habilitada, considerando el reloj y el intervalo (con sus extremos abiertos o cerrados).

        :param state: Estado actual.
        :param event: Evento a evaluar.
        :param clock: Valor actual del reloj.
        :return: True si la transición está habilitada; False en caso contrario.
        """
        for transition in self.transitions:
            if transition[0] == state and transition[1] == event:
                interval = self.timing_function(transition)
                if self._is_within_interval(clock, interval):
                    return True
        return False

    def get_next_state(self, state: str, event: str, clock: float) -> Optional[Tuple[str, float]]:
        """
        Obtiene el siguiente estado y actualiza el reloj, considerando el intervalo correspondiente.

        :param state: Estado actual.
        :param event: Evento que dispara la transición.
        :param clock: Valor actual del reloj.
        :return: Una tupla (siguiente_estado, reloj_actualizado) o None si la transición no es válida.
        """
        for transition in self.transitions:
            if transition[0] == state and transition[1] == event:
                if self._is_within_interval(clock, self.timing_function(transition)):
                    reset_interval = self.reset_function(transition)
                    if reset_interval is not None:
                        # Se reinicia el reloj; se toma el límite inferior del intervalo de reinicio como valor representativo.
                        updated_clock = reset_interval[0]
                    else:
                        updated_clock = clock
                    return transition[2], updated_clock
        return None

    def run(self, initial_state: str, event_sequence: Set[Tuple[str, float]]) -> Optional[Tuple[str, float]]:
        """
        Simula el autómata con una secuencia de eventos temporizados.

        :param initial_state: Estado inicial.
        :param event_sequence: Secuencia de tuplas (evento, timestamp).
        :return: El estado final y el valor final del reloj, o None si la secuencia es inválida.
        """
        current_state = initial_state
        clock = 0.0

        for event, timestamp in event_sequence:
            elapsed_time = timestamp - clock
            clock += elapsed_time

            result = self.get_next_state(current_state, event, clock)
            if result is None:
                return None  # Transición inválida

            current_state, clock = result

        return current_state, clock

    def print_automaton(self):
        """
        Imprime los detalles del autómata temporizado.
        """
        print("Timed Finite Automaton:")
        print(f"States: {self.states}")
        print(f"Events: {self.events}")
        print("Transitions:")
        for transition in self.transitions:
            timing_interval = self.timing_function(transition)
            reset_interval = self.reset_function(transition)
            print(f"  {transition}: Timing = {timing_interval}, Reset = {reset_interval}")
        print(f"Initial States: {self.initial_states}")

    def compute_all_zones(self) -> dict:
        """
        Computes the zones (as sets of bounds) for all states in the timed automaton.
        The computation is done in two steps:
          Step 1: For each transition t = (p, g, r, q), add the guard bounds from timing_function(t)
                  to state p. If the transition resets the clock (i.e. reset_function(t) is not None),
                  add the reset bounds to both states p and q.
          Step 2: For transitions with no reset (reset_function(t) is None), propagate the bounds from
                  the source to the destination along the acyclic subgraph defined by these transitions.
                  A topological order is computed and used for this propagation.

        Returns:
            A dictionary mapping each state to a set of bounds (floats).
        """
        # Initialize zones: a dictionary mapping each state to an empty set.
        zones = {state: set() for state in self.states}

        # Add 0 to the clock bounds of the initial states.
        for init_state in self.initial_states:
            zones[init_state].add(0)

        # Step 1: Add guard and reset bounds.
        for t in self.transitions:
            p, event, q = t
            # Get guard interval from timing_function.
            guard_interval = self.timing_function(t)
            guard_lb, guard_ub, _, _ = guard_interval
            zones[p].add(guard_lb)
            zones[p].add(guard_ub)
            # If a reset occurs (i.e. reset_function returns non-None), add reset bounds to both p and q.
            reset_interval = self.reset_function(t)
            if reset_interval is not None:
                reset_lb, reset_ub, _, _ = reset_interval
#                zones[p].add(reset_lb)
#                zones[p].add(reset_ub)
                zones[q].add(reset_lb)
                zones[q].add(reset_ub)

        # Step 2: Propagate bounds along non-reset transitions.
        # T_prime contains transitions with no reset.
        T_prime = [t for t in self.transitions if self.reset_function(t) is None]
        # Compute in-degrees for each state in the subgraph induced by T_prime.
        in_degree = {state: 0 for state in self.states}
        for t in T_prime:
            _, _, q = t
            in_degree[q] += 1

        # Compute topological order using Kahn's algorithm.
        L = [state for state in self.states if in_degree[state] == 0]
        top_order = []
        # print("Topological order:",L)
        while L:
            # print("List L:",L)
            p = L.pop(0)
            top_order.append(p)
            for t in T_prime:
                if t[0] == p:
                    _, _, q = t
                    in_degree[q] -= 1
                    if in_degree[q] == 0:
                        L.append(q)

        print("Topological order:", top_order)
        # Propagate bounds: for each transition with no reset, add bounds from source to destination.
        for p in top_order:
            for t in T_prime:
                if t[0] == p:
                    _, _, q = t
                    zones[q].update(zones[p])
        ordered_zones = {state: sorted(zones[state]) for state in sorted(self.states)}
        return ordered_zones

    ## Newly added method to compute global bounds across all states
    def compute_global_bounds(self) -> list:
        """
        Computes a single, unified list of clock bounds for the entire automaton.
        This ensures that all states share the exact same temporal boundaries,
        allowing for synchronized global time steps in the observer.
        """
        zones_dict = self.compute_all_zones()
        global_bounds = set()
        for bounds in zones_dict.values():
            global_bounds.update(bounds)
        return sorted(list(global_bounds))