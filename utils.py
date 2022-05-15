import os
import time

from process import State, Process
from typing import List


def calc_turnaround_time(process_list: List[Process]) -> None:
    """ Método auxiliar que calcula o turnaround time de cada processo """

    for p in process_list:
        if p.state == State.EXIT:
            p.turnaround_time = p.end_time - p.start_time


def calc_waiting_time(process_list: List[Process]) -> None:
    """ Método auxiliar que calcula o waiting time de cada processo """

    states_not_waiting = [State.READY, State.READY_SUSPENDED]
    for process in process_list:
        if process.state in states_not_waiting:
            process.waiting_time += 1


def calc_process_time(process_list: List[Process]) -> None:
    """ Método auxiliar que calcula o process time de cada processo """

    total_running_time = 0
    for p in process_list:
        total_running_time = (p.end_time - p.arrival_time) - p.waiting_time
        p.process_time = total_running_time


def print_queues(process_list: List[Process]) -> None:
    """ Método auxiliar utilizado apenas para fazer o print
    das filas de (Ready/Blocked, ...) """

    # time.sleep(2)
    os.system('cls' if os.name == 'nt' else 'clear') #clear console
    biggest = len(f"| {State.BLOCKED_SUSPENDED.value} {process_list} |")
    for state in State:
        processes_in_state = list(filter(lambda p : p.state == state, process_list))
        print_str = f"| {state.value} Queue: {processes_in_state}"
        print_str += f'{" " * (biggest - len(print_str)-1)}|' # output prettier
        line = "-" * biggest
        print(line)
        print(print_str)
    print(line)


def print_statistics(process_list: List[Process]) -> None:
    """ Método apenas para montar uma tabela para printar as estatísticas  """

    max_process_len = max([len(process.__str__()) for process in process_list])
    sides = (max_process_len//2) - 1
    header = "|"
    process_h = " " * sides + "PROCESS" + " " * (sides-1) + "|"
    arrival_time = " ARRIVAL_TIME |" 
    start_time = " START_TIME |"
    end_time = " END_TIME |"
    process_time = " PROCESS_TIME |" 
    waiting_time = " WAITING_TIME |"
    turnaround_time = " TURNAROUND_TIME |"
    header_list = [process_h, arrival_time, start_time, end_time, process_time, waiting_time, turnaround_time]
    header += "".join(header_list)
    # header += "|"
    line = "-" * len(header)
    print(line)
    print(header)
    print(line)

    for process in process_list:
        row = "|"
        for i, header_str in enumerate(header_list):
            value = process.get_value(header_str)
            sides_dif = len(header_str) - len(value)
            sides = (sides_dif//2)
            temp = " " * sides + f"{value}" + " " * (sides-1)
            if sides_dif % 2 != 0:
                temp += " " * (sides_dif % 2 )
            temp += "|"
            row += temp
        print(row)
        print(line)