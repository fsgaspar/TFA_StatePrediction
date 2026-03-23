from symbolic_time import TimeInterval
from symbolic_state import SymbolicState

def test_math_engine():
    print("--- Testing TimeInterval Math ---")
    
    # 1. We are in a state where time is currently [0, 5]
    current_time = TimeInterval(0, 5)
    print(f"Current Time: {current_time}")
    
    # 2. Time passes (we wait). The upper bound should become infinity.
    passed_time = current_time.up()
    print(f"Time passes (up operation): {passed_time}")
    
    # 3. An event happens that requires time to be exactly [5, 15]
    event_guard = TimeInterval(5, 15)
    print(f"Event Guard requires: {event_guard}")
    
    # 4. Do they intersect? (Can the event fire?)
    valid_intersection = passed_time.intersect(event_guard)
    print(f"Intersection (Passed Time & Guard): {valid_intersection}")
    
    # 5. What if an event requires [20, 30] but we are at [0, 5]?
    impossible_guard = TimeInterval(20, 30)
    failed_intersection = current_time.intersect(impossible_guard)
    print(f"Failed Intersection ([0, 5] & [20, 30]): {failed_intersection} (Is empty? {failed_intersection.is_empty()})")

def test_state_sets():
    print("\n--- Testing SymbolicState Sets (Crucial for Belief States) ---")
    
    # Create two identical states independently
    state1 = SymbolicState("x1", TimeInterval(5, 15))
    state2 = SymbolicState("x1", TimeInterval(5, 15))
    
    # Create a completely different state
    state3 = SymbolicState("x2", TimeInterval(5, 15))
    
    # Put them all in a set. If our __hash__ and __eq__ work, state1 and state2 will merge.
    belief_state = {state1, state2, state3}
    
    print(f"We added 3 items to the set. The set size is: {len(belief_state)}")
    print(f"Contents of the Belief State: {belief_state}")

if __name__ == "__main__":
    test_math_engine()
    test_state_sets()