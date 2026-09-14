from . import isa
from .errors import SimulatorError


class Simulator:
    def __init__(self):
        self.memory = ["0" * isa.WORD_BITS for _ in range(isa.MEM_SIZE)]
        self.registers = {name: 0 for name in isa.GP_REGISTER_NAMES}
        self.flags = 0
        self.pc = 0
        self.halted = False
        self.cycle = 0
        self.access_trace = []

    def load(self, binary_lines):
        lines = [ln.strip() for ln in binary_lines if ln.strip()]
        if len(lines) > isa.MEM_SIZE:
            raise SimulatorError(f"program has {len(lines)} words, exceeding memory size {isa.MEM_SIZE}")
        for i, line in enumerate(lines):
            if len(line) != isa.WORD_BITS or any(c not in "01" for c in line):
                raise SimulatorError(f"word {i} ('{line}') is not a valid {isa.WORD_BITS}-bit binary value")
            self.memory[i] = line

    def _reg_get(self, code):
        name = isa.REGISTER_CODES[code]
        return self.flags if name == "FLAGS" else self.registers[name]

    def _reg_set(self, code, value):
        name = isa.REGISTER_CODES[code]
        if name == "FLAGS":
            raise SimulatorError("cannot write directly to FLAGS register", self.pc)
        self.registers[name] = value & 0xFFFF

    def _record_access(self, address, kind):
        self.access_trace.append({"cycle": self.cycle, "address": address, "kind": kind})

    def step(self):
        if self.halted:
            raise SimulatorError("machine is halted", self.pc)

        word = self.memory[self.pc]
        self._record_access(self.pc, "fetch")
        opcode = word[:5]
        new_pc = self.pc + 1
        new_flags = 0

        if opcode in isa.ARITHMETIC_OPCODES:
            r1, r2, r3 = word[7:10], word[10:13], word[13:16]
            a, b = self._reg_get(r1), self._reg_get(r2)
            if opcode == isa.ADD:
                raw, overflow = (a + b) % 65536, (a + b) >= 65536
            elif opcode == isa.MUL:
                raw, overflow = (a * b) % 65536, (a * b) >= 65536
            else:
                raw, overflow = (a - b, False) if a >= b else (0, True)
            self._reg_set(r3, raw)
            if overflow:
                new_flags |= isa.FLAG_V

        elif opcode == isa.MOV_IMM:
            r1, imm = word[5:8], int(word[8:16], 2)
            self._reg_set(r1, imm)

        elif opcode == isa.MOV_REG:
            r1, r2 = word[10:13], word[13:16]
            self._reg_set(r2, self._reg_get(r1))

        elif opcode == isa.LD:
            r1, addr = word[5:8], int(word[8:16], 2)
            self._record_access(addr, "read")
            self._reg_set(r1, int(self.memory[addr], 2))

        elif opcode == isa.ST:
            r1, addr = word[5:8], int(word[8:16], 2)
            self._record_access(addr, "write")
            self.memory[addr] = format(self._reg_get(r1), f"0{isa.WORD_BITS}b")

        elif opcode == isa.DIV:
            r1, r2 = word[10:13], word[13:16]
            divisor = self._reg_get(r2)
            if divisor == 0:
                raise SimulatorError("division by zero", self.pc)
            dividend = self._reg_get(r1)
            self.registers["R0"] = dividend // divisor
            self.registers["R1"] = dividend % divisor

        elif opcode in (isa.RS, isa.LS):
            r1, imm = word[5:8], int(word[8:16], 2)
            value = self._reg_get(r1)
            shifted = value >> imm if opcode == isa.RS else value << imm
            self._reg_set(r1, shifted)

        elif opcode in (isa.XOR, isa.OR, isa.AND):
            r1, r2, r3 = word[7:10], word[10:13], word[13:16]
            a, b = self._reg_get(r1), self._reg_get(r2)
            if opcode == isa.XOR:
                result = a ^ b
            elif opcode == isa.OR:
                result = a | b
            else:
                result = a & b
            self._reg_set(r3, result)

        elif opcode == isa.NOT:
            r1, r2 = word[10:13], word[13:16]
            self._reg_set(r2, (~self._reg_get(r1)) & 0xFFFF)

        elif opcode == isa.CMP:
            r1, r2 = word[10:13], word[13:16]
            a, b = self._reg_get(r1), self._reg_get(r2)
            if a < b:
                new_flags |= isa.FLAG_L
            elif a > b:
                new_flags |= isa.FLAG_G
            else:
                new_flags |= isa.FLAG_E

        elif opcode in isa.JUMP_OPCODES:
            addr = int(word[8:16], 2)
            take = (
                opcode == isa.JMP
                or (opcode == isa.JLT and self.flags & isa.FLAG_L)
                or (opcode == isa.JGT and self.flags & isa.FLAG_G)
                or (opcode == isa.JE and self.flags & isa.FLAG_E)
            )
            if take:
                new_pc = addr
                self._record_access(addr, "jump-target")

        elif opcode == isa.HLT:
            self.halted = True

        else:
            raise SimulatorError(f"invalid opcode '{opcode}' in memory", self.pc)

        snapshot = {
            "pc": self.pc,
            "registers": dict(self.registers),
            "flags": new_flags,
            "halted": self.halted,
        }
        self.flags = new_flags
        self.pc = new_pc
        self.cycle += 1
        return snapshot

    def run(self, max_cycles=100_000):
        trace = []
        for _ in range(max_cycles):
            trace.append(self.step())
            if self.halted:
                return trace
        raise SimulatorError(f"exceeded {max_cycles} cycles without reaching hlt")


def run(binary_lines, max_cycles=100_000):
    sim = Simulator()
    sim.load(binary_lines)
    trace = sim.run(max_cycles=max_cycles)
    return trace, sim.memory, sim.access_trace
