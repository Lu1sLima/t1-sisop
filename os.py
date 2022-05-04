from process import Process, State
from typing import List
import re
import sys
import os

class OS():
    def __init__(self):
        self.acc: float = 0.0
        self.pc: int = None
        self.queues = {
            "high": [],
            "medium": [],
            "low": []
        }
        self.quantum = 0
        self.global_time = 0

    def run_process(self, process: Process):
        # Aqui de fato rodar as instruções dos processos!
        pass

    def __parse_code(self, code_string) -> List[str]:
        code_string = code_string.strip()
        labels = {}
        instructions = []

        for code in code_string.split('\n'):
            if ':' in code:
                label, code = code.split(':')
                labels[label.strip()] = code.strip()
                continue
            instructions.append(code.strip())

        return instructions, labels

    def __parse_data(self, data_string):
        data_string = data_string.strip()
        data_dict = {}

        for data in data_string.split('\n'):
            var_name, value = data.split()
            data_dict[var_name.strip()] = int(value)

        return data_dict

    def read_processes(self, processes_string):
        min_time = float('inf')
        for process in processes_string.split(', '):
            filename, priority, arrival_time = process.split()
            arrival_time = int(arrival_time)
            if arrival_time < min_time:
                min_time = arrival_time
            with open(os.path.join('process_files', filename), 'r') as process_file:
                content = process_file.read()
                code = re.search('(?s)(?<=.code).*?(?=.endcode)', content).group()
                data = re.search('(?s)(?<=.data).*?(?=.enddata)', content).group()

                instructions, labels = self.__parse_code(code)
                data_dict = self.__parse_data(data)

                self.queues[priority.lower()].append(Process(instructions, labels, data_dict, State.READY, arrival_time))
        self.global_time = min_time
    
    def exec_processes(self):
        while True:
            process = None
            for priority, queue in self.queues.items():
                if queue:
                    process = self.queues[priority][0]
                    if process.arrival_time <= self.global_time:
                        process.state = State.RUNNING
                        break
                    else:
                        continue
                else:
                    continue
            
            ## Contar quantum com o processo corrente
            for i in range(self.quantum):
                self.global_time += 1
                self.run_process(process)


if __name__ == "__main__":
    os_ = OS()
    process = 'p1.txt HIGH 10, p2.txt MEDIUM 2, p2.txt MEDIUM 2'

    os_.read_processes(process)
    os_.exec_processes()