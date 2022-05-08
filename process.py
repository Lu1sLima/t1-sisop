from enum import Enum


class State(Enum):
    READY = 'Ready'
    READY_SUSPENDED = 'Ready/Suspended'
    RUNNING = 'Running'
    BLOCKED = 'Blocked'
    BLOCKED_SUSPENDED = 'Blocked/Suspended'
    EXIT = 'Exit'

class Process():
    def __init__(self, pid: int, priority: str, instructions: list, labels: dict, data: dict, state: State, arrival_time: int):
        self.pid = pid
        self.instructions = instructions
        self.data = data
        self.labels = labels
        self.state = state
        self.last_pc = 0
        self.last_label_pc = 0 
        self.last_label = None
        self.priority = priority
        self.arrival_time = arrival_time
        self.last_acc = None
        self.time_blocked = -1

    def __eq__(self, other):
        return self.pid == other.pid

    def __str__(self):
        return f"PID {self.pid} ({self.priority})"

    def __repr__(self):
        return f"PID {self.pid} ({self.priority})"

