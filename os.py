import re
import sys
import time
import os
import json

from process import Process, State
from typing import List

class OS():
    def __init__(self):
        self.acc: float = 0.0
        self.pc: int = None
        self.queues = {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        self.quantum = 2
        self.global_time = 0
        self.memory_capacity = 0
        self.p_list = []

    def run_process(self, process: Process):
        # Aqui de fato rodar as instruções dos processos!
        pass

    def __parse_code(self, code_string: str) -> List[str]:
        code_string = code_string.strip()
        labels = {}
        instructions = []
        i = 0
        code_lines = code_string.split('\n')
        
        while i < len(code_lines):
            code = code_lines[i].strip()
            if ':' in code:
                label, code = code.split(':')
                label = label.strip()
                code = code.strip()
                instructions.append(label)
                labels[label] = []
                if code:
                    labels[label].append(code)
                    i += 1
                else:
                    i+= 1
                    while i < len(code_lines):
                        code = code_lines[i].strip()
                        if ":" in code:
                            break
                        labels[label].append(code)
                        i += 1
                continue
            instructions.append(code)
            i += 1

        return instructions, labels

    def __parse_data(self, data_string: str) -> dict:
        data_string = data_string.strip()
        data_dict = {}

        for data in data_string.split('\n'):
            var_name, value = data.split()
            data_dict[var_name.strip()] = int(value)

        return data_dict

    def read_input_file(self, filename: str) -> None:
        with open(filename, 'r') as file:
            file_json = json.loads(file.read())
            self.quantum = file_json['quantum']
            self.memory_capacity = file_json['memory']

            self.__read_processes(file_json['processes'])

    def __read_processes(self, processes: dict) -> None:
        min_time = float('inf')
        for i, process_info in enumerate(processes):
            arrival_time = int(process_info['arrival_time'])
            if arrival_time < min_time:
                min_time = arrival_time
            with open(os.path.join(process_info['filename']), 'r') as process_file:
                priority = process_info['priority'].upper()
                content = process_file.read()
                code = re.search('(?s)(?<=.code).*?(?=.endcode)', content).group()
                data = re.search('(?s)(?<=.data).*?(?=.enddata)', content).group()

                instructions, labels = self.__parse_code(code)
                data_dict = self.__parse_data(data)

                process = Process(i, priority, instructions, labels, data_dict, State.READY, arrival_time)
                self.queues[priority].append(process)
                self.p_list.append(process)
        self.global_time = min_time
    
    def __do_state_change(process, state):
        pass

    def __print_queues(self):
        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear') #clear console
        biggest = len(f"| {State.BLOCKED_SUSPENDED.value} {self.p_list} |")
        for state in State:
            processes_in_state = list(filter(lambda p : p.state == state, self.p_list))
            print_str = f"| {state.value} Queue: {processes_in_state}"
            print_str += f'{" " * (biggest - len(print_str)-1)}|' # output prettier
            line = "-" * biggest
            print(line)
            print(print_str)
        print(line)

    def exec_processes(self):
        while True:
            self.__print_queues()
            process = None
            for priority, queue in self.queues.items():
                if queue:
                    process = self.queues[priority].pop(0)
                    if process.arrival_time <= self.global_time:
                        process.state = State.RUNNING
                        break
                    else:
                        process = None
                        continue
                else:
                    continue
            

            ## Contar quantum com o processo corrente
            if process:
                for i in range(self.quantum):
                    if process.state.value == State.BLOCKED.value:
                        #chama função que decrementa
                        #verificar se chegou em zero o elapsed time
                        #se sim, coloca em ready da um break (se sim ou se não)
                        break
                    self.run_process(process)
                    self.global_time += 1
                process.state = State.EXIT
                # self.queues[process.priority].append(process)
            else:
                self.global_time += 1


if __name__ == "__main__":
    os_ = OS()
    process = 'input.json'

    os_.read_input_file(process)
    os_.exec_processes()