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

if __name__ == "__main__":
    tfa_ex3 = define_example3()
    tfa_ex2 = define_example2()
    
    
    timed_sequence = [("e1", 8.0), ("e2", 4.5), ("e4",8640.0), ("e8", 1200.0)]


    #run_symbolic_test("TFA Example 3 - Real Time Path", tfa_ex3, timed_sequence)
    run_symbolic_test("TFA Example 2 - Real Time Path", tfa_ex2, timed_sequence)