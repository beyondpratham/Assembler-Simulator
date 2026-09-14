from flask import Flask, jsonify, render_template, request

from simple_risc import assemble, isa, simulate
from simple_risc.errors import AssemblerError, SimulatorError

app = Flask(__name__)

EXAMPLE_PROGRAM = (
    "var product\n"
    "mov R1 $10\n"
    "mov R2 $100\n"
    "mul R1 R2 R3\n"
    "st R3 product\n"
    "hlt\n"
)

MAX_RESPONSE_ROWS = 2000
MAX_WEB_CYCLES = 20_000


@app.get("/")
def index():
    return render_template("index.html", example=EXAMPLE_PROGRAM)


@app.post("/api/run")
def run():
    payload = request.get_json(force=True, silent=True)
    if not isinstance(payload, dict):
        payload = {}
    source = payload.get("source", "")
    if not isinstance(source, str):
        source = ""

    try:
        binary = assemble(source)
    except AssemblerError as exc:
        return jsonify({"stage": "assemble", "error": exc.message, "line": exc.line})

    try:
        trace, memory, accesses = simulate(binary, max_cycles=MAX_WEB_CYCLES)
    except SimulatorError as exc:
        return jsonify({"stage": "simulate", "error": exc.message, "binary": binary})

    return jsonify(
        {
            "stage": "done",
            "binary": binary,
            "trace": [
                {
                    "pc": snap["pc"],
                    "registers": snap["registers"],
                    "flags": snap["flags"],
                    "flags_binary": format(snap["flags"], f"0{isa.WORD_BITS}b"),
                }
                for snap in trace[:MAX_RESPONSE_ROWS]
            ],
            "trace_total": len(trace),
            "memory": memory,
            "accesses": accesses[:MAX_RESPONSE_ROWS],
            "accesses_total": len(accesses),
        }
    )


if __name__ == "__main__":
    app.run(debug=False)
