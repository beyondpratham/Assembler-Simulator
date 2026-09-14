import sys

from . import isa
from .assembler import assemble
from .errors import AssemblerError, SimulatorError
from .simulator import run as simulate


def format_trace_line(snapshot):
    pc_bin = format(snapshot["pc"], f"0{isa.ADDR_BITS}b")
    reg_bins = " ".join(
        format(snapshot["registers"][name], f"0{isa.WORD_BITS}b") for name in isa.GP_REGISTER_NAMES
    )
    flags_bin = format(snapshot["flags"], f"0{isa.WORD_BITS}b")
    return f"{pc_bin} {reg_bins} {flags_bin}"


def assemble_main():
    source = sys.stdin.read()
    try:
        binary = assemble(source)
    except AssemblerError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("\n".join(binary))
    return 0


def simulate_main():
    lines = sys.stdin.read().splitlines()
    try:
        trace, memory, _accesses = simulate(lines)
    except SimulatorError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("\n".join(format_trace_line(snapshot) for snapshot in trace))
    print("\n".join(memory))
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("assemble", "simulate"):
        print("usage: python -m simple_risc.cli {assemble|simulate}", file=sys.stderr)
        return 2
    return assemble_main() if argv[0] == "assemble" else simulate_main()


if __name__ == "__main__":
    sys.exit(main())
