import os
from TFA_ex3 import define_example3
from TFA_ex2 import define_example2
from TimedAutomaton import TimedFiniteAutomaton
from ZoneAutomaton import ZoneAutomaton
from observer import compute_observer, draw_observer

def main():
    OUTPUT_DIR = "output/ex2"
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # --- CONFIGURATION ---
    # Change these two lines to switch between examples
    tfa = define_example2()
    EXAMPLE_NAME = "ex2"
    # ---------------------

    print(f"=== Timed Finite Automaton ({EXAMPLE_NAME}) ===")
    tfa.print_automaton()

    # Secuencia de eventos temporizados (You can adjust this per example)
    event_sequence = [("e1", 0.0), ("e4", 5.0), ("e7", 8.0)] 
    print(f"\nRunning test sequence: {event_sequence}")
    result = tfa.run(initial_state="x0", event_sequence=event_sequence)
    if result is not None:
        final_state, final_clock = result
        print(f"Final state: {final_state}, Final clock: {final_clock}")
    else:
        print("La secuencia de eventos es inválida.")

    # Computar las zonas
    zones = tfa.compute_all_zones()
    print(f"\nZones for all states: {zones}")

    # Construir el autómata de zonas LOCAL
    zone_automaton = ZoneAutomaton.from_timed_automaton(tfa)
    print("\n=== Zone Automaton ===")

    # Construir el autómata de zonas GLOBAL
    # zone_automaton = ZoneAutomaton.from_timed_automaton_global(tfa)
    # print("\n=== Zone Automaton Global===")
    
    # Save with example name
    za_file = f"{OUTPUT_DIR}/zone_automaton_{EXAMPLE_NAME}"
    zone_automaton.draw_automaton(za_file, "pdf")
    print(f"Zone Automaton saved to {za_file}.pdf")

    # Reducir estados inalcanzables
    rza_file = f"{OUTPUT_DIR}/zone_automaton_reduced_{EXAMPLE_NAME}"
    reduced_zone_automaton = zone_automaton.reduce_states()
    reduced_zone_automaton.draw_automaton(rza_file, "pdf")
    print(f"Reduced Zone Automaton saved to {rza_file}.pdf")

    # Construir el autómata observador
    print("\n=== Computing Observer Graph ===")
    observer_graph = compute_observer(reduced_zone_automaton)
    
    print(f"Observer states generated: {len(observer_graph['states'])}")
    print(f"Observer transitions generated: {len(observer_graph['transitions'])}")
    
    # Dibujar el observador
    obs_file = f"{OUTPUT_DIR}/observer_automaton_{EXAMPLE_NAME}"
    draw_observer(observer_graph, obs_file, "pdf")
    print(f"Observer Automaton saved to {obs_file}.pdf")

if __name__ == '__main__':
    main()