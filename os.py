from platform import processor
import re
import sys
import time
import os
import json
from random import randint

from process import Process, State
from typing import List

class OS():
    
    def __init__(self):
        self.acc: float = 0.0
        self.pc: int = None
        self.mneumonics = self.load_mnemonics()
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
        # Aqui de fato rodar a instru dos processos!
        pc = process.last_pc
        temp_instruction = process.instructions[pc]
        if self.__is_label(temp_instruction):
            process.last_label = temp_instruction
        
        label, label_pc = process.last_label, process.last_label_pc

        if label:
            if label_pc < len(process.labels[label]):
                instruction = process.labels[label][label_pc]
                process.last_label_pc += 1
            else:
                label = None
                process.last_label = None
                process.last_label_pc = 0
                process.last_pc += 1
                instruction = process.instructions[process.last_pc]
        else:
            instruction = process.instructions[pc]
            process.last_pc += 1
        
        self.exec_instruction(process, instruction)

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

    def load_mnemonics(self):
        return { "arithmetic": ["ADD", "SUB", "MULT", "DIV"],
                 "memory":     ["LOAD", "STORE"],
                 "jump":       ["BRANY", "BRPOS", "BRZERO", "BRNEG"], 
                 "system":     ["SYSCALL"] }

    def get_target_value(self, target, process):
        """ 
        Args:
            target (int/str): target == #constante ou target == var (variavel declarada no .data)
        """
        return  int(target.split("#")[1]) if "#" in target else int(process.data[target])    
    
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

    def __is_label(self, instruction):
        # instruction = "loop"
        # instruction.split(" ") = ["loop"] 
        # ou
        # instruction = "LOAD var"
        # instruction.split(" ") = ["LOAD", "var"]
        return  len(instruction.split(" ")) == 1 

    def exec_instruction(self, process, instruction):
        # exemplos
        #   (1) instruction = "LOAD variable" => op = LOAD e target = variable
        #   (2) as instrucoes podem vim de um label LABEL_X:
        #       instructions = process.labels[LABEL_X] = ["BRZEO fim", "load a", "add b",...]

            op, target  = instruction.split(" ")
            op = op.upper()

            if op in self.mneumonics["memory"]:
                self.memory_instructions(op, target, process)

            elif op in self.mneumonics["system"]:
                self.system_instructions(process, target)

            elif op in self.mneumonics["jump"]:
                self.jump_instructions(process, op, label=target)

            elif op in self.mneumonics["arithmetic"]:
                self.artithmetic_instructions(process, op, target)

    def memory_instructions(self, op, target, process):
        # se tiver o (#) na frente => enderecamento imediato (target)
        # se NAO tiver o (#) na frente => enderecamento direto (o valor dessa variavel target precisa ser capturada no campo .data)
        if op == "LOAD":
            target = self.get_target_value(target, process)
            self.acc = target
        elif op == "STORE":
            process.data[target] = self.acc

    def artithmetic_instructions(self, process, op, target):
        target = self.get_target_value(target, process)
        if op == "ADD":
            self.acc += target
        elif op == "SUB":
            self.acc -= target
        elif op == "MULT":
            self.acc *= target
        elif op == "DIV":
            self.acc /= target
    
    def jump_instructions(self, process, op, label):
        need_to_jump = False
        if op == "BRANY":
            need_to_jump = True        
        if op == "BRPOS":
            if self.acc > 0:  
                need_to_jump = True
        elif op == "BRZERO":
            if self.acc == 0: 
                need_to_jump = True
        elif op == "BRNEG":
            if self.acc < 0:  
                need_to_jump = True
        
        if need_to_jump:
            curr_label = process.last_label
            if not self.__will_jump_to_same_label(curr_label, new_label=label):
                process.last_pc += 1

            process.last_label_pc = 0
    
    def __will_jump_to_same_label(self, curr_label, new_label):
        return curr_label == new_label

    def system_instructions(self, process, index):
        if index == 0:
            process.state = State.EXIT
        process.state = State.BLOCKED
        process.time_blocked = randint(1, 8)
        if index == 1:
            pass
        elif index == 2:
            pass
        
        process.last_pc += 1

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