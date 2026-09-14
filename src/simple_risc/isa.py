from enum import Enum


class Format(Enum):
    RRR = "A"
    RI = "B"
    RR = "C"
    RM = "D"
    M = "E"
    NONE = "F"


REGISTERS = {
    "R0": "000",
    "R1": "001",
    "R2": "010",
    "R3": "011",
    "R4": "100",
    "R5": "101",
    "R6": "110",
    "FLAGS": "111",
}

GP_REGISTER_NAMES = [name for name in REGISTERS if name != "FLAGS"]
REGISTER_CODES = {code: name for name, code in REGISTERS.items()}

WORD_BITS = 16
ADDR_BITS = 8
MEM_SIZE = 256
IMM_MAX = 255
ADDR_MAX = 255

FLAG_E = 1 << 0
FLAG_G = 1 << 1
FLAG_L = 1 << 2
FLAG_V = 1 << 3

ADD = "10000"
SUB = "10001"
MOV_IMM = "10010"
MOV_REG = "10011"
LD = "10100"
ST = "10101"
MUL = "10110"
DIV = "10111"
RS = "11000"
LS = "11001"
XOR = "11010"
OR = "11011"
AND = "11100"
NOT = "11101"
CMP = "11110"
JMP = "11111"
JLT = "01100"
JGT = "01101"
JE = "01111"
HLT = "01010"

MNEMONIC_FORMATS = {
    "add": Format.RRR,
    "sub": Format.RRR,
    "mul": Format.RRR,
    "xor": Format.RRR,
    "or": Format.RRR,
    "and": Format.RRR,
    "div": Format.RR,
    "not": Format.RR,
    "cmp": Format.RR,
    "ld": Format.RM,
    "st": Format.RM,
    "rs": Format.RI,
    "ls": Format.RI,
    "jmp": Format.M,
    "jlt": Format.M,
    "jgt": Format.M,
    "je": Format.M,
    "hlt": Format.NONE,
}

MNEMONICS = set(MNEMONIC_FORMATS) | {"mov", "var"}

OPCODE_TO_MNEMONIC = {
    ADD: "add",
    SUB: "sub",
    MOV_IMM: "mov",
    MOV_REG: "mov",
    LD: "ld",
    ST: "st",
    MUL: "mul",
    DIV: "div",
    RS: "rs",
    LS: "ls",
    XOR: "xor",
    OR: "or",
    AND: "and",
    NOT: "not",
    CMP: "cmp",
    JMP: "jmp",
    JLT: "jlt",
    JGT: "jgt",
    JE: "je",
    HLT: "hlt",
}

ARITHMETIC_OPCODES = {ADD, SUB, MUL}
JUMP_OPCODES = {JMP, JLT, JGT, JE}

MNEMONIC_TO_OPCODE = {name: opcode for opcode, name in OPCODE_TO_MNEMONIC.items() if name != "mov"}
