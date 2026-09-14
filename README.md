# Simple RISC Assembler & Simulator

[![Tests](https://github.com/beyondpratham/Assembler-Simulator/actions/workflows/tests.yml/badge.svg)](https://github.com/beyondpratham/Assembler-Simulator/actions/workflows/tests.yml)

A from-scratch assembler and simulator for a small 16-bit RISC ISA, with a
browser UI for assembling and stepping through a program.

## Quick start

Everything runs inside a virtual environment — nothing is installed system-wide.

```powershell
git clone https://github.com/beyondpratham/Assembler-Simulator.git
cd Assembler-Simulator
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\invoke run
```

`invoke run` starts a local server and opens it in your browser. Paste or
edit assembly on the left, click **Run**, and see the assembled binary, a
step-by-step register/flag trace, a memory-access scatter chart, and the
final 256-word memory dump.

## Commands

All commands use `invoke` (`inv` for short) from the project root, via the venv:

| Command | What it does |
|---|---|
| `invoke run` | Launch the web app on `localhost:5000` |
| `invoke assemble --file program.asm` | Assemble a file, print the binary |
| `invoke simulate --file program.bin` | Simulate a binary, print the trace + memory dump |
| `invoke exec-file --file program.asm` | Assemble and simulate a file in one step |
| `invoke test` | Run the pytest suite |

The library can also be used directly, or as a traditional stdin/stdout CLI:

```powershell
.venv\Scripts\python -m simple_risc.cli assemble < program.asm
.venv\Scripts\python -m simple_risc.cli simulate < program.bin
```

```python
from simple_risc import assemble, Simulator

binary = assemble(source_text)
sim = Simulator()
sim.load(binary)
trace = sim.run()  # list of {pc, registers, flags, halted} snapshots
```

## Project layout

```
src/simple_risc/     the library: isa.py, assembler.py, simulator.py, cli.py
webapp/               Flask frontend (templates/, static/)
tests/                pytest suite, with hand-crafted assembly/binary fixtures
tasks.py              invoke tasks (see Commands above)
.github/workflows/    CI: runs the test suite on every push/PR
```

## The ISA

7 general-purpose registers (`R0`-`R6`) plus a `FLAGS` register, each 16 bits.
Memory is Von Neumann style: 256 addressable 16-bit words holding code and
data together, code always starting at address 0. Programs declare 16-bit
variables up front with `var name` (all `var` lines must come before any
label or instruction), and mark jump targets with `label:`. Variables and
labels resolve to addresses right after the code, in declaration order:

```
var product
mov R1 $10
mov R2 $100
mul R1 R2 R3
st R3 product
hlt
```

`FLAGS` bits (bit 0 → 3): `E` equal, `G` greater than, `L` less than, `V`
overflow. Only `cmp` (sets `L`/`G`/`E`) and `add`/`sub`/`mul` (set `V`) affect
`FLAGS`; every other instruction resets it to 0 as it executes.

<details>
<summary><strong>Full instruction reference</strong></summary>

Every instruction is 16 bits, in one of six encodings:

| Format | Layout (MSB → LSB) |
|---|---|
| A — 3 register | `opcode(5) unused(2) reg1(3) reg2(3) reg3(3)` |
| B — register + immediate | `opcode(5) reg1(3) imm(8)` |
| C — 2 register | `opcode(5) unused(5) reg1(3) reg2(3)` |
| D — register + memory address | `opcode(5) reg1(3) addr(8)` |
| E — memory address only | `opcode(5) unused(3) addr(8)` |
| F — halt | `opcode(5) unused(11)` |

Registers encode as `R0`-`R6` → `000`-`110`, `FLAGS` → `111`.

| Mnemonic | Opcode | Fmt | Syntax | Semantics |
|---|---|---|---|---|
| add | `10000` | A | `add reg1 reg2 reg3` | `reg3 = reg1 + reg2`, sets `V` on overflow |
| sub | `10001` | A | `sub reg1 reg2 reg3` | `reg3 = reg1 - reg2`; if `reg2 > reg1`, `reg3 = 0` and `V` is set |
| mov | `10010` | B | `mov reg1 $imm` | `reg1 = imm` (8-bit value, zero-extended) |
| mov | `10011` | C | `mov reg1 reg2` | `reg2 = reg1`; `reg1` may be `FLAGS` to read it, `reg2` may not be `FLAGS` |
| ld | `10100` | D | `ld reg1 var` | `reg1 = mem[var]` |
| st | `10101` | D | `st reg1 var` | `mem[var] = reg1` |
| mul | `10110` | A | `mul reg1 reg2 reg3` | `reg3 = reg1 * reg2`, sets `V` on overflow |
| div | `10111` | C | `div reg1 reg2` | `R0 = reg1 // reg2`, `R1 = reg1 % reg2` |
| rs | `11000` | B | `rs reg1 $imm` | `reg1 >>= imm` |
| ls | `11001` | B | `ls reg1 $imm` | `reg1 <<= imm` |
| xor | `11010` | A | `xor reg1 reg2 reg3` | `reg3 = reg1 ^ reg2` |
| or | `11011` | A | `or reg1 reg2 reg3` | `reg3 = reg1 \| reg2` |
| and | `11100` | A | `and reg1 reg2 reg3` | `reg3 = reg1 & reg2` |
| not | `11101` | C | `not reg1 reg2` | `reg2 = ~reg1` |
| cmp | `11110` | C | `cmp reg1 reg2` | sets `L`/`G`/`E` in `FLAGS` |
| jmp | `11111` | E | `jmp label` | unconditional jump |
| jlt | `01100` | E | `jlt label` | jump if `L` is set |
| jgt | `01101` | E | `jgt label` | jump if `G` is set |
| je | `01111` | E | `je label` | jump if `E` is set |
| hlt | `01010` | F | `hlt` | stop execution; must appear exactly once, as the last instruction |

</details>

## Testing

```powershell
.venv\Scripts\invoke test
```

36 tests cover the assembler (against fixture files spanning simple and
complex programs, plus hand-written error cases) and the simulator
(arithmetic, overflow, flags, jumps, division, memory).

## License

[MIT](LICENSE)
