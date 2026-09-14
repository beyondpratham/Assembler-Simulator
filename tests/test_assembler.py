from pathlib import Path

import pytest

from simple_risc import AssemblerError, assemble

FIXTURES = Path(__file__).parent / "fixtures"


def read(path):
    return path.read_text()


def read_lines(path):
    return [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]


@pytest.mark.parametrize("name", ["test1", "test2"])
def test_simple_bin_matches_reference(name):
    source = read(FIXTURES / "assembly/simpleBin" / name)
    expected = read_lines(FIXTURES / "bin/simple" / name)
    assert assemble(source) == expected


def test_hard_bin_matches_reference():
    source = read(FIXTURES / "assembly/hardBin/test1")
    expected = read_lines(FIXTURES / "bin/hard/test1")
    assert assemble(source) == expected


def test_error_gen_test1_raises():
    with pytest.raises(AssemblerError):
        assemble(read(FIXTURES / "assembly/errorGen/test1"))


def test_error_gen_test2_raises():
    with pytest.raises(AssemblerError):
        assemble(read(FIXTURES / "assembly/errorGen/test2"))


def test_worked_example_from_spec():
    source = "var X\nmov R1 $10\nmov R2 $100\nmul R3 R1 R2\nst R3 X\nhlt\n"
    assert assemble(source) == [
        "1001000100001010",
        "1001001001100100",
        "1011000011001010",
        "1010101100000101",
        "0101000000000000",
    ]


def test_missing_hlt():
    with pytest.raises(AssemblerError):
        assemble("mov R0 $1\n")


def test_hlt_not_last():
    with pytest.raises(AssemblerError):
        assemble("hlt\nmov R0 $1\n")


def test_duplicate_hlt():
    with pytest.raises(AssemblerError):
        assemble("hlt\nhlt\n")


def test_undefined_label():
    with pytest.raises(AssemblerError):
        assemble("jmp nowhere\nhlt\n")


def test_undefined_variable():
    with pytest.raises(AssemblerError):
        assemble("ld R0 missing\nhlt\n")


def test_variable_declared_after_code_is_rejected():
    with pytest.raises(AssemblerError):
        assemble("mov R0 $1\nvar X\nhlt\n")


def test_immediate_out_of_range():
    with pytest.raises(AssemblerError):
        assemble("mov R0 $256\nhlt\n")


def test_flags_illegal_as_arithmetic_operand():
    with pytest.raises(AssemblerError):
        assemble("add R0 R1 FLAGS\nhlt\n")


def test_flags_illegal_as_mov_destination():
    with pytest.raises(AssemblerError):
        assemble("mov R0 FLAGS\nhlt\n")


def test_flags_legal_as_mov_source():
    assert assemble("mov FLAGS R0\nhlt\n") == ["1001100000111000", "0101000000000000"]


def test_standalone_label_line_does_not_crash():
    binary = assemble("loop:\nmov R0 $1\njmp loop\nhlt\n")
    assert len(binary) == 3


def test_label_sharing_a_line_with_an_instruction():
    binary = assemble("loop: mov R0 $1\njmp loop\nhlt\n")
    assert len(binary) == 3


def test_duplicate_label():
    with pytest.raises(AssemblerError):
        assemble("a: mov R0 $1\na: mov R0 $2\nhlt\n")


def test_label_and_variable_name_clash():
    with pytest.raises(AssemblerError):
        assemble("var a\na: mov R0 $1\nhlt\n")


def test_typo_in_register_name():
    with pytest.raises(AssemblerError):
        assemble("mov RX $1\nhlt\n")


def test_unknown_mnemonic():
    with pytest.raises(AssemblerError):
        assemble("addd R0 R1 R2\nhlt\n")


def test_leading_bom_is_ignored():
    assert assemble("﻿mov R0 $1\nhlt\n") == ["1001000000000001", "0101000000000000"]
