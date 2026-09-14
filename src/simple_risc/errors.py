class AssemblerError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        located = f"line {line}: {message}" if line is not None else message
        super().__init__(located)


class SimulatorError(Exception):
    def __init__(self, message, pc=None):
        self.message = message
        self.pc = pc
        located = f"pc {pc}: {message}" if pc is not None else message
        super().__init__(located)
