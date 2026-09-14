import re

from . import isa
from .errors import AssemblerError

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _to_bin(value, width):
    return format(value, f"0{width}b")


def _is_valid_name(name):
    if not _NAME_RE.match(name):
        return False
    return name not in isa.MNEMONICS and name not in isa.REGISTERS


def _require_register(token, line_no, allow_flags=False):
    if token == "FLAGS":
        if allow_flags:
            return isa.REGISTERS["FLAGS"]
        raise AssemblerError("illegal use of FLAGS register", line_no)
    if token not in isa.REGISTERS:
        raise AssemblerError(f"'{token}' is not a valid register", line_no)
    return isa.REGISTERS[token]


def _parse_immediate(token, line_no, label="immediate"):
    if not token.startswith("$"):
        raise AssemblerError(f"expected an immediate value like '$10', got '{token}'", line_no)
    digits = token[1:]
    if not digits.isdigit():
        raise AssemblerError(f"'{token}' is not a valid {label}", line_no)
    value = int(digits)
    if not (0 <= value <= isa.IMM_MAX):
        raise AssemblerError(f"{label} '{token}' out of range (0-{isa.IMM_MAX})", line_no)
    return value


class Assembler:
    def __init__(self):
        self.labels = {}
        self.variables = {}
        self.instructions = []

    def assemble(self, source):
        self._layout(source.lstrip("﻿"))
        return [self._encode(line_no, tokens) for line_no, tokens, _addr in self.instructions]

    def _layout(self, source):
        var_order = []
        seen_code = False
        addr = 0

        for line_no, raw_line in enumerate(source.splitlines(), start=1):
            tokens = raw_line.split()
            if not tokens:
                continue

            if tokens[0] == "var":
                if seen_code or self.labels:
                    raise AssemblerError("variables must be declared at the beginning of the program", line_no)
                if len(tokens) != 2:
                    raise AssemblerError("invalid variable declaration, expected 'var name'", line_no)
                name = tokens[1]
                if not _is_valid_name(name):
                    raise AssemblerError(f"'{name}' is not a valid variable name", line_no)
                if name in self.variables:
                    raise AssemblerError(f"duplicate variable '{name}'", line_no)
                self.variables[name] = None
                var_order.append(name)
                continue

            if tokens[0].endswith(":"):
                label = tokens[0][:-1]
                if not _is_valid_name(label):
                    raise AssemblerError(f"'{label}' is not a valid label name", line_no)
                if label in self.variables:
                    raise AssemblerError(f"'{label}' is already used as a variable name", line_no)
                if label in self.labels:
                    raise AssemblerError(f"duplicate label '{label}'", line_no)
                self.labels[label] = addr
                tokens = tokens[1:]
                if not tokens:
                    continue

            mnemonic = tokens[0]
            if mnemonic not in isa.MNEMONIC_FORMATS and mnemonic != "mov":
                raise AssemblerError(f"unknown instruction '{mnemonic}'", line_no)

            seen_code = True
            self.instructions.append((line_no, tokens, addr))
            addr += 1

        if not self.instructions or self.instructions[-1][1][0] != "hlt":
            raise AssemblerError("program must end with a single 'hlt' instruction")

        hlt_lines = [ln for ln, tok, _ in self.instructions if tok[0] == "hlt"]
        if len(hlt_lines) > 1:
            raise AssemblerError(f"'hlt' may only appear once (found at lines {', '.join(map(str, hlt_lines))})")

        n_instr = len(self.instructions)
        if n_instr > isa.MEM_SIZE:
            raise AssemblerError(f"program has {n_instr} instructions, exceeding the {isa.MEM_SIZE} instruction limit")
        if n_instr + len(var_order) > isa.MEM_SIZE:
            raise AssemblerError("program plus variables exceed the 256-word address space")

        for offset, name in enumerate(var_order):
            self.variables[name] = _to_bin(n_instr + offset, isa.ADDR_BITS)

    def _resolve_var(self, name, line_no):
        if name in self.labels:
            raise AssemblerError(f"'{name}' is a label, not a variable", line_no)
        if name not in self.variables:
            raise AssemblerError(f"undefined variable '{name}'", line_no)
        return self.variables[name]

    def _resolve_label(self, name, line_no):
        if name in self.variables:
            raise AssemblerError(f"'{name}' is a variable, not a label", line_no)
        if name not in self.labels:
            raise AssemblerError(f"undefined label '{name}'", line_no)
        return _to_bin(self.labels[name], isa.ADDR_BITS)

    def _encode(self, line_no, tokens):
        mnemonic = tokens[0]
        args = tokens[1:]

        if mnemonic == "mov":
            return self._encode_mov(line_no, args)

        fmt = isa.MNEMONIC_FORMATS[mnemonic]
        opcode = isa.MNEMONIC_TO_OPCODE[mnemonic]

        if fmt is isa.Format.RRR:
            if len(args) != 3:
                raise AssemblerError(f"'{mnemonic}' expects 3 registers", line_no)
            r1, r2, r3 = (_require_register(a, line_no) for a in args)
            return opcode + "00" + r1 + r2 + r3

        if fmt is isa.Format.RR:
            if len(args) != 2:
                raise AssemblerError(f"'{mnemonic}' expects 2 registers", line_no)
            r1, r2 = (_require_register(a, line_no) for a in args)
            return opcode + "00000" + r1 + r2

        if fmt is isa.Format.RI:
            if len(args) != 2:
                raise AssemblerError(f"'{mnemonic}' expects a register and an immediate", line_no)
            r1 = _require_register(args[0], line_no)
            imm = _parse_immediate(args[1], line_no)
            return opcode + r1 + _to_bin(imm, 8)

        if fmt is isa.Format.RM:
            if len(args) != 2:
                raise AssemblerError(f"'{mnemonic}' expects a register and a variable", line_no)
            r1 = _require_register(args[0], line_no)
            addr = self._resolve_var(args[1], line_no)
            return opcode + r1 + addr

        if fmt is isa.Format.M:
            if len(args) != 1:
                raise AssemblerError(f"'{mnemonic}' expects a label", line_no)
            addr = self._resolve_label(args[0], line_no)
            return opcode + "000" + addr

        if fmt is isa.Format.NONE:
            if len(args) != 0:
                raise AssemblerError("'hlt' takes no operands", line_no)
            return opcode + "0" * 11

        raise AssemblerError("General Syntax Error", line_no)

    def _encode_mov(self, line_no, args):
        if len(args) != 2:
            raise AssemblerError("'mov' expects 2 operands", line_no)
        first_tok, second_tok = args

        if second_tok.startswith("$"):
            r1 = _require_register(first_tok, line_no)
            imm = _parse_immediate(second_tok, line_no)
            return isa.MOV_IMM + r1 + _to_bin(imm, 8)

        r_src = _require_register(first_tok, line_no, allow_flags=True)
        r_dst = _require_register(second_tok, line_no)
        return isa.MOV_REG + "00000" + r_src + r_dst


def assemble(source):
    return Assembler().assemble(source)
