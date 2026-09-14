import sys
import webbrowser
from pathlib import Path

from invoke import task

ROOT = Path(__file__).parent


@task
def assemble(c, file):
    """Assemble a .asm file and print the resulting binary."""
    from simple_risc import assemble as do_assemble
    from simple_risc.errors import AssemblerError

    source = Path(file).read_text()
    try:
        binary = do_assemble(source)
    except AssemblerError as exc:
        print(f"Assembler error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print("\n".join(binary))


@task
def simulate(c, file):
    """Simulate a binary (.bin) file and print the execution trace and memory dump."""
    from simple_risc import simulate as do_simulate
    from simple_risc.cli import format_trace_line
    from simple_risc.errors import SimulatorError

    lines = Path(file).read_text().splitlines()
    try:
        trace, memory, _accesses = do_simulate(lines)
    except SimulatorError as exc:
        print(f"Simulator error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print("\n".join(format_trace_line(snap) for snap in trace))
    print("\n".join(memory))


@task
def exec_file(c, file):
    """Assemble and simulate a .asm file in one step."""
    from simple_risc import assemble as do_assemble
    from simple_risc import simulate as do_simulate
    from simple_risc.cli import format_trace_line
    from simple_risc.errors import AssemblerError, SimulatorError

    source = Path(file).read_text()
    try:
        binary = do_assemble(source)
    except AssemblerError as exc:
        print(f"Assembler error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    try:
        trace, memory, _accesses = do_simulate(binary)
    except SimulatorError as exc:
        print(f"Simulator error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print("\n".join(format_trace_line(snap) for snap in trace))
    print("\n".join(memory))


@task
def test(c):
    """Run the pytest suite."""
    c.run(f'"{sys.executable}" -m pytest', pty=False)


@task
def run(c, host="127.0.0.1", port=5000, open_browser=True):
    """Start the local web app so you can assemble/simulate programs in a browser."""
    webapp_dir = str(ROOT / "webapp")
    if webapp_dir not in sys.path:
        sys.path.insert(0, webapp_dir)
    from app import app

    if open_browser:
        webbrowser.open(f"http://{host}:{port}/")
    app.run(host=host, port=port, debug=False)
