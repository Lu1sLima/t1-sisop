import re
import time
import os
import json
from random import randint

from process import Process, State, Priority
from utils import calc_turnaround_time, calc_waiting_time, print_queues, print_statistics
from typing import List, Tuple, Dict

class OS():
    
    def __init__(self):
        self.pc: int = None
        self.mneumonics = self.load_mnemonics()
        self.quantum = -1
        self.global_time = 0
        self.memory_capacity = 0
        self.p_list = []
        self.ready_list = []
        self.blocked_list = []

    def run_process(self, process: Process) -> None:
        """ Método responsável por de fato executar as instruções
        de um processo.

        Args:
            process (Process): Processo a ser executado
        """

        # Tratamento de processos que devem sofrer EXIT
        if process.last_pc > len(process.instructions)-1: return 

        increment_pc = False
        pc = process.last_pc
        temp_instruction = process.instructions[pc]
        if self.__is_label(temp_instruction):
            process.last_label = temp_instruction
        
        label, label_pc = process.last_label, process.last_label_pc

        # process.labels = {'label': [instru_1, ..., instru_n]}
        # Logo, process.labels['label'][0] = instru_1

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
                # Tratamento de processos que devem sofrer EXIT
                if process.last_pc > len(process.instructions)-1: return
                instruction = process.instructions[process.last_pc]
        else:
            instruction = process.instructions[pc]
            increment_pc = True
        
        self.exec_instruction(process, instruction, increment_pc)
        print(f'Executing: {instruction}, Acc: {process.last_acc}, Global Time: {self.global_time}')

    def __parse_code(self, code_string: str) -> Tuple[List[str], Dict]:
        """ Método responsável por fazer o parsing da string que contém
        as instruções. O método coloca as intruções em uma lista e as
        instruções dentro de labels em um dicionário.

        Args:
            code_string (str): string contendo o código (instruções)

        Returns:
            Tuple[List[str], Dict]: lista contendo as instruções e dict contendo labels
        """

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
        """ Método responsável por fazer o parsing da área
        de dados do arquivo. Coloca-os em um dicionário.

        Args:
            data_string (str): string contendo a área de dados

        Returns:
            dict: dicionário com variável:valor
        """

        data_string = data_string.strip()
        data_dict = {}

        for data in data_string.split('\n'):
            var_name, value = data.split()
            data_dict[var_name.strip()] = int(value)

        return data_dict

    def read_input_file(self, filename: str) -> None:
        """ Método responsável por ler o arquivo JSON de configuração.
        Chama os métodos necessários para ler as áres de código e dado.

        Args:
            filename (str): caminho do arquivo de configuração
        """

        with open(filename, 'r') as file:
            file_json = json.loads(file.read())
            self.quantum = file_json['quantum']
            self.memory_capacity = file_json['memory']

            self.__read_processes(file_json['processes'])

    def __read_processes(self, processes: Dict) -> None:
        """ Método responsável por ler os arquivos de processos
        do arquivo JSON de configuração. Encontra a área de código
        e dados utilizando uma regex e chama os métodos para fazer
        o parsing. Após isso, cria os processos de acordo com as
        configurações passadas, coloca-os em uma lista (self.p_list).

        Args:
            processes (dict): dicionário contendo as infos dos processos
        """

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
        print_queues(self.p_list)
        input(">>")
        self.__do_state_change()
        input(">>")

    def load_mnemonics(self) -> Dict:
        """ Método auxiliar que apenas carrega os mneumônicos em memória.

        Returns:
            Dict: dicionário contendo os mneumônicos
        """

        return { "arithmetic": ["ADD", "SUB", "MULT", "DIV"],
                 "memory":     ["LOAD", "STORE"],
                 "jump":       ["BRANY", "BRPOS", "BRZERO", "BRNEG"], 
                 "system":     ["SYSCALL"] }

    def get_target_value(self, target: str, process: Process) -> int:
        """ Método que retira um valor de uma instrução aritmética
        Args:
            target (int/str): target == #constante ou target == var (variavel declarada no .data)
        """
        return  int(target.split("#")[1]) if "#" in target else int(process.data[target])    

    def __is_label(self, instruction: str) -> bool:
        """ Método que verifica se uma instrução é uma label

        Args:
            instruction (str): string da instrução

        Returns:
            bool

        e.g.,
            instruction = "loop"
            instruction.split(" ") = ["loop"] 
            ou
            instruction = "LOAD var"
            instruction.split(" ") = ["LOAD", "var"]
        """
        return  len(instruction.split(" ")) == 1 

    def exec_instruction(self, process: Process, instruction: str, increment_pc: bool) -> None:
        """ Método que executa a instrução baseada no seu mneumônico

        Args:
            process (Process): processo sendo executado
            instruction (str): instrução a ser executada
            increment_pc (bool): variável auxiliar

        Exemplos:
            (1) instruction = "LOAD variable" => op = LOAD e target = variable
            (2) as instrucoes podem vim de um label LABEL_X:
            instructions = process.labels[LABEL_X] = ["BRZEO fim", "load a", "add b",...]
        """

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

    def memory_instructions(self, op: str, target: str, process: Process, increment_pc: bool) -> None:
        """ Método que executa instruções de memória

        Args:
            op (str): operador
            target (str): variável alvo
            process (Process): processo sendo executado
            increment_pc (bool): variável auxiliar

        e.g.,
            se tiver o (#) na frente => enderecamento imediato (target)
            se NAO tiver o (#) na frente => enderecamento direto (o valor dessa variavel target 
            precisa ser capturada no campo .data)
        """

        if op == "LOAD":
            target = self.get_target_value(target, process)
            process.last_acc = target
        elif op == "STORE":
            process.data[target] = process.last_acc

        if increment_pc:
            process.last_pc += 1

    def artithmetic_instructions(self, process: Process, op: str, target: str, increment_pc: bool) -> None:
        """ Método responsável por executar instruções aritméticas.

        Args:
            process (Process): processo sendo executado
            op (str): operador
            target (str): variável alvo
            increment_pc (bool): variável auxiliar
        """

        target = self.get_target_value(target, process)
        if op == "ADD":
            process.last_acc += target
        elif op == "SUB":
            process.last_acc -= target
        elif op == "MULT":
            process.last_acc *= target
        elif op == "DIV":
            try:
                process.last_acc /= target
            except ZeroDivisionError:
                # Se divisão por zero o processo vai para EXIT
                process.state = State.EXIT
                process.end_time = self.global_time
                print('Division By Zero! The process was killed')
                return

        if increment_pc:
            process.last_pc += 1
    
    def __will_jump_to_same_label(self, curr_label: str, new_label: str) -> bool:
        """ Método auxiliar para saber se o jump irá para a mesma label.
        Trata jumps em loop.

        Args:
            curr_label (str): label atual
            new_label (str): nova label

        Returns:
            bool
        """

        return curr_label == new_label

    def jump_instructions(self, process: Process, op: str, label: str) -> None:
        """ Processo responsável por tratar instruções de JUMP.

        Args:
            process (Process): processo sendo executado
            op (str): operador
            label (str): label que o jump irá pular
        """

        need_to_jump = False
        if op == "BRANY":
            need_to_jump = True        
        if op == "BRPOS":
            if process.last_acc > 0:  
                need_to_jump = True
        elif op == "BRZERO":
            if process.last_acc == 0: 
                need_to_jump = True
        elif op == "BRNEG":
            if process.last_acc < 0:  
                need_to_jump = True
        
        if need_to_jump:
            curr_label = process.last_label

            if curr_label is None:
                process.last_label = label

            elif not self.__will_jump_to_same_label(curr_label, new_label=label):
                process.last_pc += 1

            process.last_label_pc = 0

    def system_instructions(self, process: Process, index: int, increment_pc: bool) -> None:
        """ Método que trata as instruções de chamada de sistema.
        Manda o processo para BLOCKED/SUSPENDED quando corre um bloqueio.

        Args:
            process (Process): processo sendo executado
            index (int): valor da chamada de sistema
            increment_pc (bool): variável auxiliar
        """

        if index == '0':
            process.state = State.EXIT
            process.end_time = self.global_time
            return

        process.state = State.BLOCKED_SUSPENDED
        # process.blocked_time = randint(1, 8)
        process.blocked_time = 1
        print(f"Blocked Time: {process.blocked_time}")
        if index == '1':
            pass
        elif index == '2':
            pass
        
        if increment_pc:
            process.last_pc += 1
    
    def __decrement_blocked_times(self) -> None:
        """ Decrementa o tempo de bloqueio de cada processo em BLOCKED ou BLOCKED/SUSPENDED """

        func = lambda p : p.state == State.BLOCKED or p.state == State.BLOCKED_SUSPENDED
        blocked_processes = filter(func, self.p_list)

        for process in blocked_processes:
            process.blocked_time -= 1

        self.__do_state_change()

    def __get_min_process_index(self, lst: List) -> None:
        """ Método que que pega o processo que tem menor prioridade de uma lista.

        Args:
            lst (List): list de processos
        """

        return min(range(len(lst)), key=lst.__getitem__)

    def __handle_queues(self, state_changeable_processes: List, queue: List, states: Tuple) -> List[Process]:
        """ Método responsável por fazer o escalonamento das filas de READY e BLOCKED.

        Args:
            state_changeable_processes (List): estados que talvez podem mudar de fila
            queue (List): fila que estamos escalonando (READY ou BLOCKED) 
            states (Tuple): estados que estão em vigor. (READY, READY/SUSPENDED) ou (BLOCKED, BLOCKED/SUSPENDED)

        Returns:
            List[Process]: fila com os processos escalonados
        """

        block_or_ready = 0
        blocked_or_ready_suspend = 1
        queue = [p for p in queue if p.state == states[block_or_ready]] #cleaning

        for process in state_changeable_processes:
            processes_pid = {p.pid for p in queue}

            if process.pid in processes_pid: continue # if processe alredy in queue

            if len(queue) < self.memory_capacity:
                process.state = states[block_or_ready]
                queue.append(process) # Round Robin, adiciona no final da fila
                queue.sort(reverse=True) # Porém, reorganiza por prioridade (injustiça)
                continue

            min_process_idx = self.__get_min_process_index(queue)
            min_process = queue[min_process_idx]

            if process.priority.value > min_process.priority.value:
                del queue[min_process_idx]
                min_process.state = states[blocked_or_ready_suspend]
                process.state = states[block_or_ready]
                queue.append(process)
                continue

            process.state = states[blocked_or_ready_suspend]

        return queue

    def __should_exit(self, process: Process) -> bool:
        """ Método que verifica se um processo deveria ir para o estado de EXIT.
        Verifica se o último PC do processo é mairo do que sua área de código.

        Args:
            process (Process): processo a ser verificado

        Returns:
            bool
        """

        if process.last_pc > len(process.instructions)-1:
            process.state = State.EXIT
            process.end_time = self.global_time
            return True

        return False

    def __do_state_change(self) -> None:
        """ Método que faz o escalonamento de ambas as filas READY e BLOCKED. """

        # READY LIST
        states_not_ready = [State.EXIT, State.RUNNING]
        func_ready = lambda p : p.arrival_time <= self.global_time and p.blocked_time <= 0 and p.state not in states_not_ready
        states = (State.READY, State.READY_SUSPENDED)
        ready_states = list(filter(func_ready, self.p_list))
        self.ready_list = self.__handle_queues(ready_states, self.ready_list, states)


        # BLOCKED LIST
        states = (State.BLOCKED, State.BLOCKED_SUSPENDED)
        func_blocked_suspended = lambda p : p.state == State.BLOCKED_SUSPENDED
        blocked_suspended_states = list(filter(func_blocked_suspended, self.p_list))
        self.blocked_list = self.__handle_queues(blocked_suspended_states, self.blocked_list, states)

        print_queues(self.p_list)


    def exec_processes(self) -> None:
        " Método que de fato executa um processo, seguindo o quantum do sistema. "

        while self.ready_list or self.blocked_list:
            print_queues(self.p_list)
            process = self.ready_list[0] if self.ready_list else None

            if process:                
                state_breaker = [State.EXIT, State.BLOCKED_SUSPENDED]
                process.state = State.RUNNING
                self.__do_state_change()
                
                next_state = State.READY_SUSPENDED

                if process.start_time < 0: process.start_time = self.global_time
                
                for _ in range(self.quantum):
                    input(">>")
                    process.process_time += 1

                    calc_waiting_time(self.p_list)
                    self.__decrement_blocked_times()

                    self.global_time += 1

                    self.__do_state_change()

                    print(f'Running: {process}')
                    self.run_process(process)

                    if process.state in state_breaker or self.__should_exit(process):
                        next_state = process.state
                        input(">>")
                        break

                process.state = next_state
            else:
                time.sleep(2)
                self.global_time += 1
                self.__decrement_blocked_times()
                
            self.__do_state_change()
        calc_turnaround_time(self.p_list)
        print_queues(self.p_list)
        print("\n\n")
        print_statistics(self.p_list)


if __name__ == "__main__":
    os_ = OS()
    process = 'input.json'

    os_.read_input_file(process)
    os_.exec_processes()