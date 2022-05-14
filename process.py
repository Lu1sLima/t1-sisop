from enum import Enum


class State(Enum):
    NEW = 'New'
    READY = 'Ready'
    READY_SUSPENDED = 'Ready/Suspended'
    RUNNING = 'Running'
    BLOCKED = 'Blocked'
    BLOCKED_SUSPENDED = 'Blocked/Suspended'
    EXIT = 'Exit'


class Priority(Enum):
    HIGH = 1
    MEDIUM = 0.5
    LOW = 0

    @classmethod
    def priority(cls, priority: str):
        if priority == 'HIGH':
            return Priority.HIGH
        elif priority == 'MEDIUM':
            return Priority.MEDIUM
        else:
            return Priority.LOW


class Process():
    def __init__(self, pid: int, priority: Priority, instructions: list, labels: dict, data: dict, state: State, arrival_time: int, process_time: int):
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
        self.blocked_time = -1
        self.process_time = process_time

    def __eq__(self, other):
        return self.priority.value == other.priority.value

    def __lt__(self, other):
        return self.priority.value < other.priority.value

    def __gt__(self, other):
        return self.priority.value > other.priority.value

    def __str__(self):
        return f"PID {self.pid} ({self.priority})"

    def __repr__(self):
        return f"PID {self.pid} ({self.priority}), AT: {self.arrival_time}, STATE: {self.state.value}"

