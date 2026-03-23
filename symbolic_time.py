class TimeInterval:
    """
    Represents a continuous 1D time interval [lower, upper].
    Handles all the mathematical operations needed to avoid state explosion.
    """
    def __init__(self, lower: float, upper: float, l_inc: bool = True, u_inc: bool = True):
        self.lower = float(lower)
        self.upper = float(upper)
        self.l_inc = l_inc
        self.u_inc = u_inc

    def is_empty(self) -> bool:
        """Returns True if the interval is mathematically impossible."""
        if self.lower > self.upper:
            return True
        if self.lower == self.upper and not (self.l_inc and self.u_inc):
            return True
        return False

    def intersect(self, other: 'TimeInterval') -> 'TimeInterval':
        """Intersects this interval with another (used for checking event guards)."""
        # Calculate new lower bound
        if self.lower > other.lower:
            new_l, new_l_inc = self.lower, self.l_inc
        elif self.lower < other.lower:
            new_l, new_l_inc = other.lower, other.l_inc
        else:
            new_l, new_l_inc = self.lower, (self.l_inc and other.l_inc)

        # Calculate new upper bound
        if self.upper < other.upper:
            new_u, new_u_inc = self.upper, self.u_inc
        elif self.upper > other.upper:
            new_u, new_u_inc = other.upper, other.u_inc
        else:
            new_u, new_u_inc = self.upper, (self.u_inc and other.u_inc)

        return TimeInterval(new_l, new_u, new_l_inc, new_u_inc)

    def up(self) -> 'TimeInterval':
        """Simulates time passing (delay). The upper bound stretches to infinity."""
        return TimeInterval(self.lower, float('inf'), self.l_inc, False)
        
    def reset(self) -> 'TimeInterval':
        """Simulates a clock reset to exactly 0."""
        return TimeInterval(0.0, 0.0, True, True)

    def __eq__(self, other):
        if not isinstance(other, TimeInterval):
            return False
        # If both are empty, they are equal regardless of specific numbers
        if self.is_empty() and other.is_empty():
            return True
        return (self.lower == other.lower and self.upper == other.upper and 
                self.l_inc == other.l_inc and self.u_inc == other.u_inc)

    def __hash__(self):
        if self.is_empty():
            return hash("empty")
        return hash((self.lower, self.upper, self.l_inc, self.u_inc))

    def __repr__(self):
        if self.is_empty():
            return "Ø"
        l_bracket = "[" if self.l_inc else "("
        u_bracket = "]" if self.u_inc else ")"
        return f"{l_bracket}{self.lower}, {self.upper}{u_bracket}"
    
    def advance(self, delta_t: float) -> 'TimeInterval':
        """Advances the clock by an exact amount of time."""
        return TimeInterval(self.lower + delta_t, self.upper + delta_t, self.l_inc, self.u_inc)
    
    def delay_and_reset(self, delta_t: float, guard: 'TimeInterval') -> 'TimeInterval':
        """
        Calculates the exact clock interval AFTER waiting delta_t, assuming an unobservable 
        event with the given `guard` fired DURING the wait and reset the clock.
        """
        # When could the event have fired during our wait?
        d1_low = max(0.0, guard.lower - self.upper)
        d1_high = min(delta_t, guard.upper - self.lower)

        if d1_low > d1_high:
            return TimeInterval(1, -1) # Mathematically impossible, returns empty
        
        # If it fired and reset to 0, how much of the wait time is REMAINING?
        remaining_low = delta_t - d1_high
        remaining_high = delta_t - d1_low
        
        # The clock at the end of the wait is exactly the remaining time.
        return TimeInterval(remaining_low, remaining_high)
    
    def get_valid_delay_firing_window(self, delta_t: float, guard: 'TimeInterval'):
        """
        If we wait delta_t, could the clock have crossed the guard during the wait?
        Returns the (min, max) time elapsed BEFORE it fired, or (None, None) if impossible.
        """
        delta_min = max(0.0, guard.lower - self.upper)
        delta_max = min(delta_t, guard.upper - self.lower)
        
        if delta_min <= delta_max:
            return delta_min, delta_max
        return None, None