from graphviz import Digraph

def compute_observer(za) -> dict:
    """
    Computes the observer graph (Diagnoser) from a ZoneAutomaton.
    
    :param za: An instance of ZoneAutomaton.
    :return: A dictionary containing the observer's states, events, transitions, and initial_state.
    """
    # 1. Start with the unobservable closure of the initial states.
    # We use frozenset so the observer states can be hashed and added to sets.
    initial_closure = za._compute_unobservable_closure(za.initial_states)
    initial_obs_state = frozenset(initial_closure)

    obs_states = {initial_obs_state}
    obs_events = set()
    obs_transitions = set()

    # Queue for breadth-first exploration of the observer graph
    queue = [initial_obs_state]

    while queue:
        current_obs = queue.pop(0)

        # Dictionary to group destination states by their observable events
        destinations_by_event = {}

        # 2. Find all transitions originating from ANY state within our current belief state
        for ext_state in current_obs:
            for src, event, dst in za.transitions:
                if src == ext_state and za._is_observable(event):
                    if event not in destinations_by_event:
                        destinations_by_event[event] = set()
                    destinations_by_event[event].add(dst)

        # 3. For each observable event, compute the next belief state
        for event, dest_states in destinations_by_event.items():
            # The next state is the unobservable closure of all reached states
            closure = za._compute_unobservable_closure(dest_states)
            next_obs_state = frozenset(closure)

            # Record the transition and event
            obs_transitions.add((current_obs, event, next_obs_state))
            obs_events.add(event)

            # If this is a new belief state, add it to our tracking set and queue
            if next_obs_state not in obs_states:
                obs_states.add(next_obs_state)
                queue.append(next_obs_state)

    return {
        "states": obs_states,
        "events": obs_events,
        "transitions": obs_transitions,
        "initial_state": initial_obs_state
    }

def draw_observer(observer, filename, format):
    """
    Dibuja el autómata observador utilizando Graphviz.

    :param observer: Diccionario devuelto por compute_observer(), que contiene:
                     - "states": conjunto de estados observadores (frozensets de estados extendidos),
                                 donde cada estado extendido es una tupla (estado, zona).
                     - "events": conjunto de eventos observables.
                     - "transitions": conjunto de transiciones (source, event, destination).
                     - "initial_state": el estado observador inicial.
    :param filename: Nombre base del archivo de salida (sin extensión).
    :param format: Formato de salida (por ejemplo, 'png', 'pdf').
    :return: Objeto Digraph generado.
    """

    def format_zone(zone):
        a, b, c, d = zone
        start_bracket = "[" if c else "("
        end_bracket = "]" if d else ")"
        return f"{start_bracket}{a}, {b}{end_bracket}"

    def format_extended_state(ext_state):
        """
        Dado un estado extendido (estado, zona), devuelve una cadena formateada.
        """
        state_name, zone = ext_state
        return f"{state_name} {format_zone(zone)}"

    dot = Digraph(comment="Observer Automaton")

    # Crear nodos para cada estado observador.
    state_to_node = {}
    for obs_state in observer["states"]:
        # Cada obs_state es un frozenset de estados extendidos.
        node_id = f"node_{hash(obs_state)}"
        state_to_node[obs_state] = node_id
        # Formateamos la etiqueta uniendo la representación de cada estado extendido.
        label = "\n".join(sorted([format_extended_state(s) for s in obs_state]))
        # Se resalta el estado inicial.
        if obs_state == observer["initial_state"]:
            dot.node(node_id, label=label, shape="doublecircle", color="green")
        else:
            dot.node(node_id, label=label)

    # Crear arcos para cada transición.
    for (src, event, dst) in observer["transitions"]:
        if src == dst and str(event)[0].isdigit():
            continue  
        src_id = state_to_node[src]
        dst_id = state_to_node[dst]
        dot.edge(src_id, dst_id, label=event)

    dot.render(filename, format=format, cleanup=True)
    return dot
