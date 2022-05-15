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
    def __init__(self, pid: int, priority: Priority, instructions: list, labels: dict, data: dict, state: State, arrival_time: int):
        # PROCESS INFO
        self.pid = pid
        self.instructions = instructions
        self.data = data
        self.priority = priority
        self.labels = labels
        self.state = state

        # PCB
        self.last_acc = 0
        self.last_label_pc = 0 
        self.last_label = None
        self.last_pc = 0

        # STATISTICS
        self.arrival_time = arrival_time
        self.process_time = 0
        self.blocked_time = -1
        self.waiting_time = 0
        self.start_time = -1
        self.end_time = 0
        self.turnaround_time = 0

    def __eq__(self, other):
        """ Método auxiliar (compare)

        Args:
            other (Process): outro processo a ser comparado

        Returns:
            bool
        """
        return self.priority.value == other.priority.value

    def __lt__(self, other):
        """ Método auxiliar (compare)

        Args:
            other (Process): outro processo a ser comparado

        Returns:
            bool
        """
        return self.priority.value < other.priority.value

    def __gt__(self, other):
        """ Método auxiliar (compare)

        Args:
            other (Process): outro processo a ser comparado

        Returns:
            bool
        """
        return self.priority.value > other.priority.value

    def __str__(self):
        """ Método auxiliar (compare)

        Args:
            other (Process): outro processo a ser comparado

        Returns:
            bool
        """
        return f"PID {self.pid} ({self.priority})"

    def __repr__(self):
        """ Método auxiliar (to string) """
        return f"PID {self.pid} ({self.priority}), AT: {self.arrival_time}, STATE: {self.state.value}"

    def get_value(self, value_search: str) -> str:
        value_search = value_search.lower().replace("|", "").strip()

        if value_search == "process":
            return self.__str__()

        return str(getattr(self, value_search))