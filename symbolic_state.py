from symbolic_time import TimeInterval

class SymbolicState:
    """
    Pairs a system location (e.g., 'x1') with a continuous time interval.
    This replaces the hardcoded DFA time-slice strings.
    """
    def __init__(self, location: str, interval: TimeInterval):
        self.location = location
        self.interval = interval

    def __eq__(self, other):
        if not isinstance(other, SymbolicState):
            return False
        return self.location == other.location and self.interval == other.interval

    def __hash__(self):
        return hash((self.location, self.interval))

    def __repr__(self):
        return f"({self.location}, {self.interval})"