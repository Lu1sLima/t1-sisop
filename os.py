from process import Process, Priority
from typing import List
import re
import os

class OS():
    def __init__(self):
        self.acc: float = 0.0
        self.pc: int = None
        self.escalonator = []
        self.quantum = 0

    def __parse_code(self, code_string) -> List[str]:
        code_string = code_string.strip()
        labels = {}
        instructions = []

        for i, code in enumerate(code_string.split('\n')):
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

    def read_process(self, filename: str):
        file_path = os.path.join('process_files', filename)
        with open(file_path, 'r') as process_file:
            content = process_file.read()
            code = re.search('(?s)(?<=.code).*?(?=.endcode)', content).group()
            data = re.search('(?s)(?<=.data).*?(?=.enddata)', content).group()

            instructions, labels = self.__parse_code(code)
            data_dict = self.__parse_data(data)

            self.escalonator.append(Process(instructions, labels, data_dict, Priority.HIGH))

if __name__ == "__main__":
    os_ = OS()

    os_.read_process('p1.txt')