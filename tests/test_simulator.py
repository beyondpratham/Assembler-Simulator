import pytest

from simple_risc import Simulator, SimulatorError, assemble
from simple_risc import isa


def run(source):
    sim = Simulator()
    sim.load(assemble(source))
    trace = sim.run()
    return trace, sim.memory


def test_addition():
    trace, _ = run("mov R0 $5\nmov R1 $3\nadd R0 R1 R2\nhlt\n")
    assert trace[-1]["registers"]["R2"] == 8
    assert trace[-1]["flags"] == 0


def test_addition_overflow_wraps_and_sets_v_flag():
    source = (
        "mov R0 $255\nls R0 $8\n"
        "mov R1 $255\nls R1 $8\n"
        "add R0 R1 R2\nhlt\n"
    )
    trace, _ = run(source)
    add_snapshot = trace[4]
    assert add_snapshot["registers"]["R2"] == (65280 + 65280) % 65536
    assert add_snapshot["flags"] & isa.FLAG_V


def test_subtraction_underflow_clamps_to_zero_and_sets_v_flag():
    trace, _ = run("mov R0 $3\nmov R1 $4\nsub R0 R1 R2\nhlt\n")
    sub_snapshot = trace[2]
    assert sub_snapshot["registers"]["R2"] == 0
    assert sub_snapshot["flags"] & isa.FLAG_V


def test_cmp_sets_flags_and_conditional_jump_is_taken():
    source = (
        "mov R0 $1\nmov R1 $2\ncmp R0 R1\n"
        "jlt less\nmov R2 $99\njmp end\n"
        "less: mov R2 $7\n"
        "end: hlt\n"
    )
    trace, _ = run(source)
    assert trace[-1]["registers"]["R2"] == 7


def test_flags_reset_after_non_affecting_instruction():
    source = "mov R0 $1\nmov R1 $2\ncmp R0 R1\nxor R2 R2 R3\nmov FLAGS R4\nhlt\n"
    trace, _ = run(source)
    cmp_snapshot = trace[2]
    assert cmp_snapshot["flags"] == isa.FLAG_L
    final_snapshot = trace[-1]
    assert final_snapshot["registers"]["R4"] == 0


def test_mov_flags_reads_value_before_it_resets():
    source = "mov R0 $1\nmov R1 $2\ncmp R0 R1\nmov FLAGS R2\nhlt\n"
    trace, _ = run(source)
    assert trace[-2]["registers"]["R2"] == isa.FLAG_L


def test_not_inverts_bits():
    trace, _ = run("mov R0 $0\nnot R0 R1\nhlt\n")
    assert trace[-2]["registers"]["R1"] == 0xFFFF


def test_divide_writes_quotient_to_r0_and_remainder_to_r1():
    trace, _ = run("mov R2 $17\nmov R3 $5\ndiv R2 R3\nhlt\n")
    final = trace[-1]["registers"]
    assert final["R0"] == 3
    assert final["R1"] == 2


def test_divide_by_zero_raises():
    with pytest.raises(SimulatorError):
        run("mov R0 $5\nmov R1 $0\ndiv R0 R1\nhlt\n")


def test_variable_load_and_store_round_trip():
    trace, memory = run("var X\nmov R0 $42\nst R0 X\nmov R1 $0\nld R1 X\nhlt\n")
    assert trace[-2]["registers"]["R1"] == 42
    assert len(memory) == isa.MEM_SIZE


def test_memory_dump_is_always_256_words():
    _, memory = run("mov R0 $1\nhlt\n")
    assert len(memory) == 256
    assert all(len(word) == 16 for word in memory)


def test_pc_trace_matches_addresses_executed():
    trace, _ = run("mov R0 $1\nmov R1 $2\nhlt\n")
    assert [snap["pc"] for snap in trace] == [0, 1, 2]


def test_unconditional_jump():
    trace, _ = run("jmp target\nmov R0 $99\ntarget: mov R0 $1\nhlt\n")
    assert trace[-1]["registers"]["R0"] == 1
