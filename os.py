import re
import time
import os
import json
from random import randint

from process import Process, State, Priority
from typing import List

class OS():
    
    def __init__(self):
        self.acc: float = 0.0
        self.pc: int = None
        self.mneumonics = self.load_mnemonics()
        self.quantum = 2
        self.global_time = 0
        self.memory_capacity = 0
        self.p_list = []
        self.ready_list = []
        self.blocked_list = []

    def run_process(self, process: Process):
        # Aqui de fato rodar a instru dos processos!
        if process.last_pc > len(process.instructions)-1: return

        increment_pc = False
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
                increment_pc = True
                if process.last_pc > len(process.instructions)-1: return
                instruction = process.instructions[process.last_pc]
        else:
            instruction = process.instructions[pc]
            increment_pc = True
        
        print(f'Executing: {instruction}, Acc: {self.acc}, Global Time: {self.global_time}')
        time.sleep(2)
        self.exec_instruction(process, instruction, increment_pc)

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
                priority = Priority.priority(process_info['priority'].upper())
                content = process_file.read()
                code = re.search('(?s)(?<=.code).*?(?=.endcode)', content).group()
                data = re.search('(?s)(?<=.data).*?(?=.enddata)', content).group()

                instructions, labels = self.__parse_code(code)
                data_dict = self.__parse_data(data)

                process = Process(i, priority, instructions, 
                                labels, data_dict, State.NEW, 
                                arrival_time)
                self.p_list.append(process)

        self.__do_state_change()
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


    def __print_queues(self):
        time.sleep(2)
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

    def exec_instruction(self, process, instruction, increment_pc):
        # exemplos
        #   (1) instruction = "LOAD variable" => op = LOAD e target = variable
        #   (2) as instrucoes podem vim de um label LABEL_X:
        #       instructions = process.labels[LABEL_X] = ["BRZEO fim", "load a", "add b",...]

            op, target  = instruction.split(" ")
            op = op.upper()

            if op in self.mneumonics["memory"]:
                self.memory_instructions(op, target, process, increment_pc)

            elif op in self.mneumonics["system"]:
                self.system_instructions(process, target, increment_pc)

            elif op in self.mneumonics["jump"]:
                self.jump_instructions(process, op, label=target)

            elif op in self.mneumonics["arithmetic"]:
                self.artithmetic_instructions(process, op, target, increment_pc)

    def memory_instructions(self, op, target, process, increment_pc):
        # se tiver o (#) na frente => enderecamento imediato (target)
        # se NAO tiver o (#) na frente => enderecamento direto (o valor dessa variavel target precisa ser capturada no campo .data)
        if op == "LOAD":
            target = self.get_target_value(target, process)
            self.acc = target
        elif op == "STORE":
            process.data[target] = self.acc

        if increment_pc:
            process.last_pc += 1

    def artithmetic_instructions(self, process, op, target, increment_pc):
        target = self.get_target_value(target, process)
        if op == "ADD":
            self.acc += target
        elif op == "SUB":
            self.acc -= target
        elif op == "MULT":
            self.acc *= target
        elif op == "DIV":
            try:
                self.acc /= target
            except ZeroDivisionError:
                process.state = State.EXIT
                print('Division By Zero!')
                time.sleep(10)
                return

        if increment_pc:
            process.last_pc += 1
    
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

    def system_instructions(self, process, index, increment_pc):
        if index == 0:
            process.state = State.EXIT
        self.ready_list.pop(0)
        process.state = State.BLOCKED_SUSPENDED
        process.blocked_time = randint(1, 8)
        if index == 1:
            pass
        elif index == 2:
            pass
        
        if increment_pc:
            process.last_pc += 1
    
    def __decrement_blocked_times(self):
        func = lambda p : p.state == State.BLOCKED or p.state == State.BLOCKED_SUSPENDED
        blocked_processes = filter(func, self.p_list)

        for process in blocked_processes:
            process.blocked_time -= 1

    def __get_min_process_index(self, lst: list):
        return min(range(len(lst)), key=lst.__getitem__)

    def __handle_queues(self, state_changeable_processes, lst: list, states: tuple):
        lst = [p for p in lst if p.state == states[0]] #cleaning

        for process in state_changeable_processes:
            if len(lst) < self.memory_capacity:
                process.state = states[0]
                lst.append(process)
                continue

            min_process_idx = self.__get_min_process_index(lst)
            min_process = lst[min_process_idx]

            if process.priority.value > min_process.priority.value:
                del lst[min_process_idx]
                min_process.state = states[1]
                process.state = states[0]
                lst.append(process)
                continue

            process.state = states[1]

        return lst

    def __should_exit(self, process) -> None:
        if process.last_pc > len(process.instructions)-1:
            process.state = State.EXIT
            return True

        return False

    def __do_state_change(self):
        func_ready = lambda p : p.arrival_time <= self.global_time and p.blocked_time <= 0 and p.state != State.EXIT
        states = (State.READY, State.READY_SUSPENDED)
        ready_states = list(filter(func_ready, self.p_list))
        self.ready_list = self.__handle_queues(ready_states, self.ready_list, states)

        # self.blocked_list = [p for p in self.blocked_list if p.state == State.BLOCKED]
        states = (State.BLOCKED, State.BLOCKED_SUSPENDED)
        func_blocked_suspended = lambda p : p.state == State.BLOCKED_SUSPENDED
        blocked_suspended_states = list(filter(func_blocked_suspended, self.p_list))
        self.blocked_list = self.__handle_queues(blocked_suspended_states, self.blocked_list, states)

    def exec_processes(self):
        while self.ready_list or self.blocked_list:
            self.__print_queues()
            process = self.ready_list[0] if self.ready_list else None

            ## Contar quantum com o processo corrente
            if process:                
                print(f'Running: {process}')
                state_breaker = [State.EXIT, State.BLOCKED_SUSPENDED]
                process.state = State.RUNNING
                self.__print_queues()
                for i in range(self.quantum):
                    self.__decrement_blocked_times()
                    self.run_process(process)
                    self.global_time += 1
                    if process.state in state_breaker or self.__should_exit(process):
                        self.__do_state_change()
                        break
            else:
                self.global_time += 1
                self.__decrement_blocked_times()
                
            self.__do_state_change()
        self.__print_queues()


if __name__ == "__main__":
    os_ = OS()
    process = 'input.json'

    os_.read_input_file(process)
    os_.exec_processes()