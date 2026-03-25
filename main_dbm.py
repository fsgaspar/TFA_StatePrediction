from TFA_ex4 import define_example4
from TFA_ex5 import define_example5
from symbolic_observer import SymbolicObserver
from TFA_ex3 import define_example3  
from TFA_ex2 import define_example2  

def run_symbolic_test(test_name: str, tfa_object, observation_sequence: list):
    print(f"\n{'='*60}")
    print(f"  RUNNING TEST: {test_name}")
    print(f"{'='*60}")

    # 1. Dynamically extract unobservable events (look for parentheses)
    unobs_events = {e for e in tfa_object.events if e.startswith('(')}
    
    # 2. Extract initial state
    initial_loc = list(tfa_object.initial_states)[0]

    # 3. Initialize Engine with your direct functions
    observer = SymbolicObserver(
        initial_location=initial_loc,
        transitions=tfa_object.transitions,
        unobservable_events=unobs_events,
        timing_func=tfa_object.timing_function,
        reset_func=tfa_object.reset_function
    )

    print(f"--> Initial Belief State (t=0):")
    for state in observer.current_belief:
        print(f"    {state}")

    if not observation_sequence:
        return

    print(f"\n--> Executing Timed Sequence: {observation_sequence}")
    
    for step, (obs_event, time_elapsed) in enumerate(observation_sequence, start=1):
        print(f"\n{'='*40}")
        print(f"  STEP {step}: '{obs_event}' with delay = {time_elapsed}s")
        print(f"{'='*40}")
        
        observer.process_timed_observation(obs_event, time_elapsed)
        
        print(f"\n  => SURVIVING BELIEF STATE: {observer.current_belief}")
        
        if not observer.current_belief:
            print(f"\n  [!] FATAL: All states dropped. Sequence is impossible.")
            return 

    print(f"\n{'='*40}")
    print(f"  END OF SEQUENCE - FORECASTING FUTURE")
    print(f"{'='*40}")
    
    future_states = observer.predict_future_belief()
    
    print("\n  => IF WE WAIT FOREVER, SYSTEM COULD BE IN:")
    for state in future_states:
        print(f"      {state}")
    print(f"\n{'='*60}\n")

from graphviz import Digraph

def draw_observer_graph(graph: dict, filename: str = "observer_graph"):
    """
    Renders the Symbolic Observer Graph to a PDF using Graphviz.
    """
    dot = Digraph(comment='Symbolic Observer Graph', format='pdf')
    dot.attr(rankdir='LR', size='10,8')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightcyan', fontname='Helvetica', fontsize='12')
    dot.attr('edge', fontname='Helvetica', fontsize='10', color='gray30')

    # Helper function to format a belief state nicely inside the node box
    def format_node(belief_node):
        if not belief_node:
            return "Empty"
        # Sort by location for consistent display (e.g., x1 above x2)
        sorted_states = sorted(list(belief_node), key=lambda s: s.location)
        lines = [f"{s.location}: {s.interval}" for s in sorted_states]
        return "\n".join(lines)

    # Assign unique IDs to each frozenset node so Graphviz can connect them
    node_ids = {}
    for i, node in enumerate(graph.keys()):
        node_ids[node] = f"N{i}"
        
        # Highlight the initial state node in a different color
        if i == 0:
            dot.node(node_ids[node], format_node(node), fillcolor='lightgreen', penwidth='2')
        else:
            dot.node(node_ids[node], format_node(node))

    # Add edges based on the observable transitions
    for source_node, edges in graph.items():
        for event, target_node in edges:
            dot.edge(node_ids[source_node], node_ids[target_node], label=f"  {event}  ")

    # Render and open the PDF
    dot.render(filename, view=True)
    print(f"\n  [Success] Observer graph saved and opened as {filename}.pdf")

if __name__ == "__main__":
    tfa_ex3 = define_example3()
    tfa_ex2 = define_example2()
    tfa_ex4 = define_example4()
    tfa_ex5 = define_example5()
    
    
    timed_sequence = [("e1", 8.0), ("e2", 4.5), ("e4",8640.0), ("e8", 1200.0), ("e10", 65.0)]


    #run_symbolic_test("TFA Example 3 - Real Time Path", tfa_ex3, timed_sequence)
    run_symbolic_test("TFA Example 2 - Real Time Path", tfa_ex2, timed_sequence)
    #run_symbolic_test("TFA Example 4 - Real Time Path", tfa_ex4, timed_sequence)

    unobs_events2 = {e for e in tfa_ex2.events if e.startswith('(')}
    unobs_events3 = {e for e in tfa_ex3.events if e.startswith('(')}
    unobs_events4 = {e for e in tfa_ex4.events if e.startswith('(')}
    unobs_events5 = {e for e in define_example5().events if e.startswith('(')}
    initial_loc2 = list(tfa_ex2.initial_states)[0]
    initial_loc3 = list(tfa_ex3.initial_states)[0]
    initial_loc4 = list(tfa_ex4.initial_states)[0]
    initial_loc5 = list(define_example5().initial_states)[0]
    
    # Initialize the Observer
    observer2 = SymbolicObserver(
        initial_location=initial_loc2,
        transitions=tfa_ex2.transitions,
        unobservable_events=unobs_events2,
        timing_func=tfa_ex2.timing_function,
        reset_func=tfa_ex2.reset_function
    )

    observer3 = SymbolicObserver(
        initial_location=initial_loc3,
        transitions=tfa_ex3.transitions,
        unobservable_events=unobs_events3,
        timing_func=tfa_ex3.timing_function,
        reset_func=tfa_ex3.reset_function
    )

    observer4 = SymbolicObserver(
        initial_location=initial_loc4,
        transitions=tfa_ex4.transitions,
        unobservable_events=unobs_events4,
        timing_func=tfa_ex4.timing_function,
        reset_func=tfa_ex4.reset_function
    )

    observer5 = SymbolicObserver(
        initial_location=initial_loc5,
        transitions=tfa_ex5.transitions,
        unobservable_events=unobs_events5,
        timing_func=tfa_ex5.timing_function,
        reset_func=tfa_ex5.reset_function
    )

    # 1. Build the complete mathematical graph
    obs_graph2 = observer2.build_observer_graph()
    obs_graph3 = observer3.build_observer_graph()
    obs_graph4 = observer4.build_observer_graph()
    obs_graph5 = observer5.build_observer_graph()
    # 2. Draw it to a PDF!
    #draw_observer_graph(obs_graph2, filename="TFA_Example_2_Graph")
    #draw_observer_graph(obs_graph3, filename="TFA_Example_3_Graph")
    #draw_observer_graph(obs_graph4, filename="TFA_Example_4_Graph")
    draw_observer_graph(obs_graph5, filename="TFA_Example_5_Graph")