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

    def _get_reset(self, transition: tuple):
        """Fetches the reset bounds and converts them to a TimeInterval."""
        reset_data = self.reset_func(transition)
        if reset_data is None:
            return None
        return TimeInterval(*reset_data)

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
    
    def build_time_segmented_graph(self) -> dict:
        print("\n  [Building Segmented Graph] Utilizing Clock-Interval Advance (Zone) Logic...")

        def get_max_upper_bound(location: str) -> float:
            max_ub = -1.0
            has_transitions = False
            for t in self.transitions:
                if t[0] == location:
                    has_transitions = True
                    ub = self._get_guard(t).upper
                    if ub == float('inf'): return float('inf')
                    if ub > max_ub: max_ub = ub
            return max_ub if has_transitions else float('inf')

        def get_time_step(macrostate: frozenset) -> float:
            """Finds the smallest exact time delta 'd' to the next logical boundary."""
            deltas = set()
            for state in macrostate:
                l, u = state.interval.lower, state.interval.upper
                for trans in self.transitions:
                    if trans[0] == state.location:
                        g = self._get_guard(trans)
                        if g.lower != float('inf'):
                            if g.lower - u > 0: deltas.add(g.lower - u)
                            if g.lower - l > 0: deltas.add(g.lower - l)
                        if g.upper != float('inf'):
                            if g.upper - u > 0: deltas.add(g.upper - u)
                            if g.upper - l > 0: deltas.add(g.upper - l)
                
                max_ub = get_max_upper_bound(state.location)
                if max_ub != float('inf'):
                    if max_ub - u > 0: deltas.add(max_ub - u)
                    if max_ub - l > 0: deltas.add(max_ub - l)
            return min(deltas) if deltas else float('inf')

        def apply_instant_closure(base_states: set) -> frozenset:
            """Applies unobservable closure instantaneously (e.g., right after an observation)."""
            closure = {s.location: [s.interval.lower, s.interval.upper] for s in base_states}
            worklist = list(base_states)
            
            while worklist:
                curr = worklist.pop(0)
                l, u = curr.interval.lower, curr.interval.upper
                
                for trans in self.transitions:
                    src, evt, tgt = trans
                    if src == curr.location and evt in self.unobservable_events:
                        g = self._get_guard(trans)
                        int_l, int_u = max(l, g.lower), min(u, g.upper)
                        
                        if int_l <= int_u:  # Firing is valid right now
                            reset = self._get_reset(trans)
                            new_l = reset.lower if reset else int_l
                            new_u = reset.upper if reset else int_u
                            
                            if tgt in closure:
                                old_l, old_u = closure[tgt]
                                merged_l, merged_u = min(old_l, new_l), max(old_u, new_u)
                                if merged_l < old_l or merged_u > old_u:
                                    closure[tgt] = [merged_l, merged_u]
                                    worklist.append(SymbolicState(tgt, TimeInterval(new_l, new_u, True, True)))
                            else:
                                closure[tgt] = [new_l, new_u]
                                worklist.append(SymbolicState(tgt, TimeInterval(new_l, new_u, True, True)))
                                
            return frozenset(SymbolicState(loc, TimeInterval(l, u, True, True)) for loc, (l, u) in closure.items())

        def apply_time_step_and_closure(macrostate: frozenset, d: float) -> frozenset:
            """Advances clocks by 'd' and evaluates unobservable transitions that fire DURING the step."""
            final_intervals = {}
            
            # 1. Advance existing timelines
            for state in macrostate:
                l, u = state.interval.lower, state.interval.upper
                max_ub = get_max_upper_bound(state.location)
                if l + d <= max_ub or max_ub == float('inf'):
                    final_intervals[state.location] = [l + d, u + d]

            # 2. Evaluate unobservable cascades during step 'd'
            worklist = list(macrostate)
            while worklist:
                curr = worklist.pop(0)
                l, u = curr.interval.lower, curr.interval.upper
                
                for trans in self.transitions:
                    src, evt, tgt = trans
                    if src == curr.location and evt in self.unobservable_events:
                        g, L, U = self._get_guard(trans), self._get_guard(trans).lower, self._get_guard(trans).upper
                        
                        # Calculate exact window where firing was valid DURING the step
                        t_min = max(0.0, L - u)
                        t_max = min(d, U - l)
                        
                        if t_min <= t_max:
                            reset = self._get_reset(trans)
                            if reset:
                                new_l = reset.lower + max(0.0, d - U + l)
                                new_u = reset.upper + min(d, d - L + u)
                            else:
                                new_l = max(l + d, L)
                                new_u = min(u + d, U + d)
                            
                            if tgt in final_intervals:
                                old_l, old_u = final_intervals[tgt]
                                merged_l, merged_u = min(old_l, new_l), max(old_u, new_u)
                                if merged_l < old_l or merged_u > old_u:
                                    final_intervals[tgt] = [merged_l, merged_u]
                                    worklist.append(SymbolicState(tgt, TimeInterval(new_l, new_u, True, True)))
                            else:
                                final_intervals[tgt] = [new_l, new_u]
                                worklist.append(SymbolicState(tgt, TimeInterval(new_l, new_u, True, True)))
                                
            return frozenset(SymbolicState(loc, TimeInterval(l, u, True, True)) for loc, (l, u) in final_intervals.items())

        # ==========================================
        # Main Graph Construction
        # ==========================================
        graph = {}
        # Apply instant closure to account for unobservables valid at exact start time
        initial_macrostate = apply_instant_closure(set(self.current_belief))
        
        queue = [initial_macrostate]
        visited = {initial_macrostate}
        
        observable_transitions = [t for t in self.transitions if t[1] not in self.unobservable_events]
        unique_obs_events = {t[1] for t in observable_transitions}

        while queue:
            curr_macro = queue.pop(0)
            if curr_macro not in graph:
                graph[curr_macro] = []
                
            # --- PHASE 1: Time Passage ---
            d = get_time_step(curr_macro)
            if d > 0 and d != float('inf'):
                next_macro_time = apply_time_step_and_closure(curr_macro, d)
                if next_macro_time:
                    edge_label = f"time -> {d}"
                    graph[curr_macro].append((edge_label, next_macro_time))
                    if next_macro_time not in visited:
                        visited.add(next_macro_time)
                        queue.append(next_macro_time)
                        
            # --- PHASE 2: Observable Events ---
            for obs_event in unique_obs_events:
                arrivals = set()
                for state in curr_macro:
                    for trans in self.transitions:
                        src, evt, tgt = trans
                        if src == state.location and evt == obs_event:
                            g = self._get_guard(trans)
                            l, u = state.interval.lower, state.interval.upper
                            int_l, int_u = max(l, g.lower), min(u, g.upper)
                            
                            if int_l <= int_u: # Observable enabled right now
                                reset = self._get_reset(trans)
                                new_l = reset.lower if reset else int_l
                                new_u = reset.upper if reset else int_u
                                arrivals.add(SymbolicState(tgt, TimeInterval(new_l, new_u, True, True)))
                
                if arrivals:
                    next_macro_obs = apply_instant_closure(arrivals)
                    graph[curr_macro].append((obs_event, next_macro_obs))
                    if next_macro_obs not in visited:
                        visited.add(next_macro_obs)
                        queue.append(next_macro_obs)

        return graph