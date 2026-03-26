from symbolic_time import TimeInterval
from symbolic_state import SymbolicState

class SymbolicObserver:
    def __init__(self, initial_location: str, transitions: set, unobservable_events: set, timing_func, reset_func):
        self.transitions = transitions
        self.unobservable_events = unobservable_events
        self.timing_func = timing_func
        self.reset_func = reset_func
        self.global_time = 0.0
        
        start_state = SymbolicState(initial_location, TimeInterval(0.0, 0.0))
        self.current_belief = self.unobservable_reach({start_state})

    def _get_guard(self, transition: tuple) -> TimeInterval:
        lower, upper, l_inc, u_inc = self.timing_func(transition)
        return TimeInterval(lower, upper, l_inc, u_inc)

    def _apply_reset(self, interval: TimeInterval, transition: tuple) -> TimeInterval:
        if self.reset_func(transition) is not None:
            return interval.reset()
        return interval

    def unobservable_reach(self, belief_state: set) -> set:
        """Finds instant unobservable jumps (usually right after a clock reset)."""
        closure = set(belief_state)
        worklist = list(belief_state)

        while worklist:
            current_state = worklist.pop()
            loc = current_state.location
            interval = current_state.interval

            for trans in self.transitions:
                source, event, target = trans
                if source == loc and event in self.unobservable_events:
                    guard = self._get_guard(trans)
                    intersected_interval = interval.intersect(guard)
                    
                    if not intersected_interval.is_empty():
                        final_interval = self._apply_reset(intersected_interval, trans)
                        new_state = SymbolicState(target, final_interval)
                        if new_state not in closure:
                            closure.add(new_state)
                            worklist.append(new_state)
        return closure

    def _unobservable_reach_with_delay(self, delayed_belief: set) -> set:
        """
        The magic fix! Finds unobservable jumps that happen WHILE waiting.
        """
        closure = set(delayed_belief)
        worklist = list(delayed_belief)

        while worklist:
            current_state = worklist.pop()
            loc = current_state.location
            interval = current_state.interval # E.g., [0.0, inf)

            for trans in self.transitions:
                source, event, target = trans
                if source == loc and event in self.unobservable_events:
                    guard = self._get_guard(trans)
                    
                    # 1. Did time cross the guard while we were waiting?
                    intersected_interval = interval.intersect(guard)
                    
                    if not intersected_interval.is_empty():
                        # 2. Fire the unobservable transition
                        final_interval = self._apply_reset(intersected_interval, trans)
                        
                        # 3. CRUCIAL: Because this happened secretly in the past, 
                        # time CONTINUED to pass until the present moment!
                        final_delayed_interval = final_interval.up()
                        
                        new_state = SymbolicState(target, final_delayed_interval)
                        if new_state not in closure:
                            closure.add(new_state)
                            worklist.append(new_state)
        return closure

    def process_observation(self, observed_event: str):
        # Step 1: Time passes while waiting for the observation
        delayed_belief = set()
        for state in self.current_belief:
            delayed_belief.add(SymbolicState(state.location, state.interval.up()))

        # Step 2: Calculate all unobservable events that fired DURING that wait
        pre_observation_belief = self._unobservable_reach_with_delay(delayed_belief)

        # Step 3: Now process the actual observation
        next_belief = set()
        for state in pre_observation_belief:
            loc = state.location
            interval = state.interval

            for trans in self.transitions:
                source, trans_event, target = trans
                if source == loc and trans_event == observed_event:
                    guard = self._get_guard(trans)
                    valid_interval = interval.intersect(guard)
                    
                    if not valid_interval.is_empty():
                        final_interval = self._apply_reset(valid_interval, trans)
                        next_belief.add(SymbolicState(target, final_interval))

        # Step 4: Check for instant unobservables after the new state is reached
        self.current_belief = self.unobservable_reach(next_belief)
        return self.current_belief
    
    def process_timed_observation(self, observed_event: str, time_elapsed: float):
        """
        Processes an observation that occurred `time_elapsed` seconds AFTER the last observation.
        """
        if time_elapsed < 0:
            raise ValueError("Time elapsed cannot be negative!")
            
        # The time elapsed IS our delta_t! 
        delta_t = time_elapsed
        
        # We can still track global time just for your own logging/debugging
        self.global_time += delta_t

        print(f"\n  [Phase 1: Wait] Advancing clock by {delta_t}s (Global Time is now {self.global_time})...")
        
        pre_observation_belief = set()
        
        worklist = [(s.location, s.interval, delta_t) for s in self.current_belief]
        processed = set()
        
        while worklist:
            loc, interval, rem_delta = worklist.pop(0)
            
            # Prevent infinite loops if there are unobservable cycles
            sig = (loc, round(interval.lower, 4), round(interval.upper, 4), round(rem_delta, 4))
            if sig in processed:
                continue
            processed.add(sig)
            
            # 1. Base Case: Time finishes advancing, no more events fire.
            advanced_interval = interval.advance(rem_delta)
            pre_observation_belief.add(SymbolicState(loc, advanced_interval))
            
            # 2. Did an unobservable event fire DURING this remaining wait?
            for trans in self.transitions:
                source, event, target = trans
                if source == loc and event in self.unobservable_events:
                    guard = self._get_guard(trans)
                    d_min, d_max = interval.get_valid_delay_firing_window(rem_delta, guard)
                    
                    if d_min is not None:
                        if self.reset_func(trans) is not None:
                            # It fired and reset! Calculate the exact remaining wait time.
                            rem_min = rem_delta - d_max
                            rem_max = rem_delta - d_min
                            
                            # Add this exact final state directly to our belief
                            final_interval = TimeInterval(rem_min, rem_max)
                            pre_observation_belief.add(SymbolicState(target, final_interval))
                            
                            # If the target has MORE hidden events, queue it to keep chaining!
                            has_unobs = any(t[0] == target and t[1] in self.unobservable_events for t in self.transitions)
                            if has_unobs:
                                worklist.append((target, TimeInterval(0.0, 0.0), rem_max))
                        else:
                            # No reset. Clock keeps advancing exactly as it was.
                            worklist.append((target, interval, rem_delta))

        print("  --> Possible realities right BEFORE observation:")
        for s in pre_observation_belief:
            print(f"      {s}")

        print(f"\n  [Phase 2: Observation] Applying '{observed_event}' guard rules...")
        next_belief = set()
        for state in pre_observation_belief:
            loc = state.location
            interval = state.interval
            
            # Track if this state survives
            survived = False 
            
            for trans in self.transitions:
                source, trans_event, target = trans
                if source == loc and trans_event == observed_event:
                    guard = self._get_guard(trans)
                    valid_interval = interval.intersect(guard)
                    
                    if not valid_interval.is_empty():
                        final_interval = self._apply_reset(valid_interval, trans)
                        next_belief.add(SymbolicState(target, final_interval))
                        print(f"      ✓ SURVIVED: {loc} -> {target} | Clock {interval} intersects Guard {guard} -> {valid_interval}")
                        survived = True
                    else:
                        print(f"      X DROPPED: {loc} -> {target} | Clock {interval} misses Guard {guard}")
            
            # If no transition matched the observation at all
            if not survived and any(t[0] == loc and t[1] == observed_event for t in self.transitions) is False:
                 print(f"      X DROPPED: {loc} | No outgoing '{observed_event}' transition exists here.")

        # Phase 3: Instant unobservables right after arriving
        final_belief = self.unobservable_reach(next_belief)
        if len(final_belief) > len(next_belief):
            print(f"\n  [Phase 3: Chain Reaction] Instant unobservable jumps detected!")
            
        self.current_belief = final_belief
        return self.current_belief
    
    def predict_future_belief(self) -> set:
        """
        Predicts all possible future states that could be reached purely by 
        time passing and unobservable events occurring, from now until infinity.
        """
        print(f"\n  [Future Prediction] Calculating all possible future unobservable paths...")
        
        # Step 1: Stretch all current clocks to infinity
        future_belief = set()
        for state in self.current_belief:
            # We keep the lower bound, but the upper bound becomes infinity
            stretched_interval = TimeInterval(state.interval.lower, float('inf'))
            future_belief.add(SymbolicState(state.location, stretched_interval))
            
        # Step 2: Propagate through unobservable transitions
        closure = set(future_belief)
        worklist = list(future_belief)

        while worklist:
            current_state = worklist.pop()
            loc = current_state.location
            interval = current_state.interval

            for trans in self.transitions:
                source, event, target = trans
                if source == loc and event in self.unobservable_events:
                    guard = self._get_guard(trans)
                    
                    # Can the stretched clock eventually hit the guard in the future?
                    intersected = interval.intersect(guard)
                    
                    if not intersected.is_empty():
                        # If it fires, apply the reset (if any)
                        new_interval = self._apply_reset(intersected, trans)
                        
                        # CRUCIAL: Because we are predicting the unbounded future, 
                        # time CONTINUES to pass after this hidden event!
                        # So we instantly stretch the resulting clock to infinity again.
                        future_interval = TimeInterval(new_interval.lower, float('inf'))
                        
                        new_state = SymbolicState(target, future_interval)
                        
                        # Avoid infinite loops if there are unobservable cycles
                        if new_state not in closure:
                            closure.add(new_state)
                            worklist.append(new_state)
                            print(f"      -> Future hidden jump discovered: {loc} --{event}--> {target}")
                            
        return closure
    
    def build_observer_graph(self) -> dict:
        """
        Builds the complete Symbolic Observer Graph.
        Nodes represent the 'Delayed Macrostate' (Arrival + Time Elapse + Unobservable Cascades).
        """
        print("\n  [Building Observer Graph] Starting BFS exploration...")

        def get_macrostate(base_belief: set) -> frozenset:
            """
            Takes raw arrival states (like x4 [0,0]), stretches time to infinity,
            and discovers all unobservable states reached during that wait.
            """
            # 1. Stretch time (simulate waiting forever)
            delayed = set()
            for s in base_belief:
                delayed.add(SymbolicState(s.location, s.interval.up()))
            
            # 2. Find all unobservable states reached during this wait
            closure = set(delayed)
            worklist = list(delayed)
            
            while worklist:
                curr = worklist.pop(0)
                for trans in self.transitions:
                    src, evt, tgt = trans
                    if src == curr.location and evt in self.unobservable_events:
                        guard = self._get_guard(trans)
                        intersected = curr.interval.intersect(guard)
                        
                        if not intersected.is_empty():
                            new_int = self._apply_reset(intersected, trans)
                            
                            # CRUCIAL: Time continues passing after the hidden event fires!
                            future_int = new_int.up() 
                            new_state = SymbolicState(tgt, future_int)
                            
                            if new_state not in closure:
                                closure.add(new_state)
                                worklist.append(new_state)
                                
            return frozenset(closure)

        # Start BFS with the fully expanded initial macrostate
        initial_macrostate = get_macrostate(self.current_belief)
        
        graph = {}
        queue = [initial_macrostate]
        visited = {initial_macrostate}
        
        observable_transitions = [t for t in self.transitions if t[1] not in self.unobservable_events]
        unique_obs_events = {t[1] for t in observable_transitions}
        
        while queue:
            current_macrostate = queue.pop(0)
            graph[current_macrostate] = []
            
            # Apply Observable Events (The Slicer)
            for obs_event in unique_obs_events:
                next_arrival_belief = set()
                
                for state in current_macrostate:
                    for trans in self.transitions:
                        src, evt, tgt = trans
                        if src == state.location and evt == obs_event:
                            guard = self._get_guard(trans)
                            valid_int = state.interval.intersect(guard)
                            
                            if not valid_int.is_empty():
                                final_int = self._apply_reset(valid_int, trans)
                                next_arrival_belief.add(SymbolicState(tgt, final_int))
                                
                if next_arrival_belief:
                    # Expand the raw arrivals into the full Delayed Macrostate
                    next_macrostate = get_macrostate(next_arrival_belief)
                    
                    graph[current_macrostate].append((obs_event, next_macrostate))
                    
                    if next_macrostate not in visited:
                        visited.add(next_macrostate)
                        queue.append(next_macrostate)
                        
        return graph