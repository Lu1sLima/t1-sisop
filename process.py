from enum import Enum


class State(Enum):
    READY = 'Ready'
    READY_SUSPENDED = 'Ready/Suspended'
    RUNNING = 'Running'
    BLOCKED = 'Blocked'
    BLOCKED_SUSPENDED = 'Blocked/Suspended'
    EXIT = 'Exit'

class Process():
    def __init__(self, instructions: list, labels: dict, data: dict, state: State, arrival_time: int):
        self.instructions = instructions
        self.data = data
        self.labels = labels
        self.state = state.value
        self.last_pc = -1
        self.arrival_time = arrival_time