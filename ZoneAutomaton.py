from typing import Set, Tuple
from graphviz import Digraph


class ZoneAutomaton:
    def __init__(self,
                 states: Set[Tuple[str, Tuple[float, float, bool, bool]]],
                 events: Set[str],
                 transitions: Set[Tuple[Tuple[str, Tuple[float, float, bool, bool]], str, Tuple[str, Tuple[float, float, bool, bool]]]],
                 initial_states: Set[Tuple[str, Tuple[float, float, bool, bool]]]):
        """
        Inicializa un autómata de zonas.

        :param states: Conjunto de estados extendidos (V), donde cada estado es una tupla (estado, zona).
                       Cada zona se representa como (inicio, fin, inicio_inclusivo, fin_inclusivo).
        :param events: Conjunto de eventos (E_τ), que incluye eventos observables y de avance temporal.
        :param transitions: Conjunto de transiciones (Δ_z) representadas como
                            ((estado, zona), evento, (siguiente_estado, zona)).
        :param initial_states: Conjunto de estados extendidos iniciales (V0).
        """
        # Se incluyen eventos de tiempo basados en el límite superior de cada zona.
        self.states = states
        self.events = events.union({f"{z[1]}" for _, z in states}).union({f"{z[1]}+" for _, z in states})
        self.transitions = sorted(transitions, key=lambda t: t[0][0])
        self.initial_states = initial_states

    @classmethod
    def from_timed_automaton(cls, timed_automaton):
        """
        Constructs a zone automaton from a given timed finite automaton (TFA).
        The computation uses the new compute_all_zones() function, which returns,
        for each state, a sorted list of clock bounds. From these bounds, the following
        zone intervals are computed:
          - For bounds B = [b0, b1, ..., b_{n-1}], zones are:
              [b0, b0], (b0, b1), [b1, b1], (b1, b2), ..., [b_{n-1}, b_{n-1}], (b_{n-1}, ∞).
          - Consequently, if B = {0,1,5}, the intervals are:
              [0,0], (0,1), [1,1], (1,5), [5,5], (5,∞).
        Additionally, temporal (time advance) transitions are added between successive zones.
        """
        # Get computed clock bounds for all states (a dict: state -> sorted list of bounds)
        all_bounds = timed_automaton.compute_all_zones()

        # Helper: compute zone intervals from sorted bounds.
        def compute_intervals(bounds):
            intervals = []
            if not bounds:
                return intervals
            # If the last bound is infinity, remove it.
            if bounds[-1] == float('inf'):
                bounds = bounds[:-1]
            # Add degenerate interval at first bound: [b0, b0]
            intervals.append((bounds[0], bounds[0], True, True))
            for i in range(len(bounds) - 1):
                # Open interval (b_i, b_{i+1})
                intervals.append((bounds[i], bounds[i + 1], False, False))
                # Degenerate interval at b_{i+1}: [b_{i+1}, b_{i+1]]
                intervals.append((bounds[i + 1], bounds[i + 1], True, True))
            # Add open interval from last bound to infinity: (b_{n-1}, ∞)
            intervals.append((bounds[-1], float('inf'), False, False))
            return intervals

        # Helper: determine the time event label between two consecutive zones.
        def time_event_label(current_zone, next_zone):
            # current_zone = (a, b, a_inc, b_inc)
            a, b, a_inc, b_inc = current_zone
            # If the current zone is degenerate, label with "b+"; otherwise, label with "b".
            if a == b and a_inc and b_inc:
                return f"{b}+"
            else:
                return f"{b}"

        states = set()
        events = timed_automaton.events.copy()
        transitions = set()
        initial_states = set()

        # Process each state in the TFA.
        for state in timed_automaton.states:
            bounds = all_bounds.get(state, [])
            if not bounds:
                continue  # Skip if no bounds computed.
            zone_intervals = compute_intervals(bounds)
            # Create extended states for this state based on its zone intervals.
            extended_states_for_state = []
            for zone in zone_intervals:
                extended_state = (state, zone)
                states.add(extended_state)
                extended_states_for_state.append(extended_state)
            # Mark the first extended state as initial if the state is an initial state.
            if state in timed_automaton.initial_states:
                initial_states.add(extended_states_for_state[0])

            # Add temporal transitions between successive zones for the same state.
            for i in range(len(extended_states_for_state) - 1):
                src = extended_states_for_state[i]
                dst = extended_states_for_state[i + 1]
                label = time_event_label(zone_intervals[i], zone_intervals[i + 1])
                #print("src=",src,"label=",label,"dst=",dst)
                transitions.add((src, label, dst))
                events.add(label)
            print("Events=",events)
            # For each logical event, add transitions from the extended states.
            for ext_state, zone in zip(extended_states_for_state, zone_intervals):
                lower, upper, lower_inc, upper_inc = zone
                # Choose a representative time within the zone.
                if upper == float('inf'):
                    rep_time = lower + 1  # Arbitrary value for unbounded interval.
                else:
                    if lower == upper:  # Degenerate zone.
                        rep_time = lower
                    else:
                        rep_time = (lower + upper) / 2
                # Evaluate transitions for each event.
                for event in timed_automaton.events:
                    next_state_zone = timed_automaton.get_next_state(state, event, rep_time)
                    if next_state_zone:
                        next_state, _ = next_state_zone
                        reset_interval = timed_automaton.reset_function((state, event, next_state))
                        if reset_interval is not None:
                            # If a reset occurs, the clock is reset; use the lower bound (degenerate interval).
                            next_zone = (reset_interval[0], reset_interval[0], True, True)
                        else:
                            # Otherwise, remain in the same zone.
                            next_zone = zone
                        dst_extended = (next_state, next_zone)
                        transitions.add((ext_state, event, dst_extended))
                        states.add(dst_extended)

        return cls(states, events, transitions, initial_states)

    def print_automaton(self):
        """
        Imprime los detalles del autómata de zonas.
        """
        print("Zone Automaton:")
        print(f"States: {self.states}")
        print(f"Events: {self.events}")
        print("Transitions:")
        for transition in self.transitions:
            print(f"  {transition[0]} -- {transition[1]} --> {transition[2]}")
        print(f"Initial States: {self.initial_states}")

    def draw_automaton(self, filename, format):
        """
        Dibuja el autómata de zonas usando Graphviz y guarda el resultado en un archivo.

        :param filename: Nombre base del archivo de salida (sin extensión).
        :param format: Formato de salida (por ejemplo, 'png', 'pdf').
        :return: Objeto Digraph de graphviz.
        """

        # Función auxiliar para formatear la zona (intervalo)
        def format_zone(zone):
            start, end, start_inc, end_inc = zone
            start_bracket = "[" if start_inc else "("
            end_bracket = "]" if end_inc else ")"
            return f"{start_bracket}{start}, {end}{end_bracket}"

        dot = Digraph(comment="Zone Automaton")

        # Crear nodos para cada estado extendido
        for state in self.states:
            state_name, zone = state
            # Se genera un identificador único para cada nodo a partir de sus componentes
            node_id = f"{state_name}_{zone[0]}_{zone[1]}_{int(zone[2])}_{int(zone[3])}"
            label = f"{state_name}\n{format_zone(zone)}"
            #print("Label=",label)
            dot.node(node_id, label=label)

        # Crear arcos para cada transición
        for src, event, dst in self.transitions:
            if src == dst and str(event)[0].isdigit():
                continue

            src_name, src_zone = src
            dst_name, dst_zone = dst
            src_id = f"{src_name}_{src_zone[0]}_{src_zone[1]}_{int(src_zone[2])}_{int(src_zone[3])}"
            dst_id = f"{dst_name}_{dst_zone[0]}_{dst_zone[1]}_{int(dst_zone[2])}_{int(dst_zone[3])}"
            dot.edge(src_id, dst_id, label=str(event))

        # Renderiza y guarda el archivo
        dot.render(filename, format=format, cleanup=True)
        return dot

    def reduce_states(self):
        """
        Returns a new ZoneAutomaton with unreachable states removed.
        Unreachable states are those that cannot be reached from any of the initial states
        following the transitions.
        """
        # Compute reachable states using a breadth-first search.
        reachable_states = set()
        frontier = list(self.initial_states)
        while frontier:
            current = frontier.pop(0)
            if current not in reachable_states:
                reachable_states.add(current)
                # Look for transitions originating from the current state.
                for (src, event, dst) in self.transitions:
                    if src == current and dst not in reachable_states:
                        frontier.append(dst)

        # Filter transitions: keep only those whose source and destination are reachable.
        reduced_transitions = {
            (src, event, dst)
            for (src, event, dst) in self.transitions
            if src in reachable_states and dst in reachable_states
        }

        # Recompute the events set from the remaining transitions.
        reduced_events = {event for (_, event, _) in reduced_transitions}

        # The initial states remain those in the intersection.
        reduced_initial_states = self.initial_states.intersection(reachable_states)

        # Return a new ZoneAutomaton with the reduced components.
        return ZoneAutomaton(reachable_states, reduced_events, reduced_transitions, reduced_initial_states)

    def _is_observable(self, event: str) -> bool:
        """
        Returns True if the event is observable.
        Unobservable events are assumed to have parentheses around them.
        """
        return not (event.startswith("(") and event.endswith(")"))

    def _compute_unobservable_closure(self, states: set) -> set:
        """
        Computes the closure of a set of extended states with respect to unobservable transitions.
        That is, it returns all states reachable from any state in 'states' by following transitions
        whose events are unobservable.
        """
        closure = set(states)
        stack = list(states)
        while stack:
            current_state = stack.pop()
            for (src, event, dst) in self.transitions:
                if src == current_state and not self._is_observable(event) and dst not in closure:
                    closure.add(dst)
                    stack.append(dst)
        return closure

    #New method to compute global bounds across all states
    @classmethod
    def from_timed_automaton_global(cls, timed_automaton):
        """
        Constructs a zone automaton using a Global Time Grid, but collapses
        'informationless' future zones for states that have no bounds that high.
        """
        # Get individual bounds to find the max bound per state
        all_local_bounds = timed_automaton.compute_all_zones()
        # Get the global grid
        global_bounds = timed_automaton.compute_global_bounds()

        def compute_intervals(bnds):
            intervals = []
            if not bnds: return intervals
            if bnds[-1] == float('inf'): bnds = bnds[:-1]
            intervals.append((bnds[0], bnds[0], True, True))
            for i in range(len(bnds) - 1):
                intervals.append((bnds[i], bnds[i + 1], False, False))
                intervals.append((bnds[i + 1], bnds[i + 1], True, True))
            intervals.append((bnds[-1], float('inf'), False, False))
            return intervals

        def time_event_label(current_zone, next_zone):
            a, b, a_inc, b_inc = current_zone
            if a == b and a_inc and b_inc: return f"{b}+"
            else: return f"{b}"

        global_zone_intervals = compute_intervals(global_bounds)

        states = set()
        events = timed_automaton.events.copy()
        transitions = set()
        initial_states = set()

        for state in timed_automaton.states:
            local_bnds = all_local_bounds.get(state, [])
            if not local_bnds:
                continue
            
            # Find the maximum meaningful boundary for this specific state
            finite_bnds = [b for b in local_bnds if b != float('inf')]
            max_bound = max(finite_bnds) if finite_bnds else 0

            # Map the global zones to collapsed state-specific zones
            mapped_zones = []
            for zone in global_zone_intervals:
                lower, upper, l_inc, u_inc = zone
                # If the zone is strictly past the state's max meaningful bound, collapse it
                if lower > max_bound or (lower == max_bound and not l_inc):
                    mapped_zones.append((max_bound, float('inf'), False, False))
                else:
                    mapped_zones.append(zone)

            # 1. Create states and initial states
            for i in range(len(global_zone_intervals)):
                ext_state = (state, mapped_zones[i])
                states.add(ext_state)
                if i == 0 and state in timed_automaton.initial_states:
                    initial_states.add(ext_state)

            # 2. Add temporal transitions based on the GLOBAL sequence
            for i in range(len(global_zone_intervals) - 1):
                src = (state, mapped_zones[i])
                dst = (state, mapped_zones[i + 1])
                label = time_event_label(global_zone_intervals[i], global_zone_intervals[i + 1])
                transitions.add((src, label, dst))
                events.add(label)

            # 3. Add logical transitions
            for zone in set(mapped_zones): # Use set to only evaluate each unique zone once
                ext_state = (state, zone)
                lower, upper, lower_inc, upper_inc = zone
                
                # Representative time for guard evaluation
                if upper == float('inf'): rep_time = lower + 1
                elif lower == upper: rep_time = lower
                else: rep_time = (lower + upper) / 2
                        
                for event in timed_automaton.events:
                    next_state_zone = timed_automaton.get_next_state(state, event, rep_time)
                    if next_state_zone:
                        next_state, _ = next_state_zone
                        reset_interval = timed_automaton.reset_function((state, event, next_state))
                        
                        if reset_interval is not None:
                            # Jump back to 0 (or whatever the reset is)
                            next_zone = (reset_interval[0], reset_interval[0], True, True)
                            transitions.add((ext_state, event, (next_state, next_zone)))
                            states.add((next_state, next_zone))
                        else:
                            # If no reset, apply the destination's collapsing rules to the current time
                            dest_bnds = all_local_bounds.get(next_state, [])
                            dest_finite = [b for b in dest_bnds if b != float('inf')]
                            dest_max = max(dest_finite) if dest_finite else 0
                            
                            if lower > dest_max or (lower == dest_max and not lower_inc):
                                next_zone = (dest_max, float('inf'), False, False)
                            else:
                                next_zone = zone
                                
                            transitions.add((ext_state, event, (next_state, next_zone)))
                            states.add((next_state, next_zone))

        return cls(states, events, transitions, initial_states)
    
   