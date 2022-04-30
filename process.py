from enum import Enum


class Priority(Enum):
    LOW = 0
    MEDIUM = 0.5
    HIGH = 1

# [Proc(p=0.5), Proc(p=0)]

# exe : Proc(p=1)
# quantum: [Proc(p=1), Proc(p=0.5), Proc(p=0)]


class Process():
    def __init__(self, instructions: list, labels: dict, data: dict, priority: Priority):
        self.instructions = instructions
        self.data = data
        self.labels = labels
        self.priority = priority.value

    def __eq__(self, other) -> bool:
        return self.priority == other.priority

    def __lt__(self, other) -> bool:
        return self.priority < other.priority

    def __gt__(self, other) -> bool:
        return self.priority > other.priority