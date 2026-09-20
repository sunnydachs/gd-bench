# gd-bench

**Detect GDScript array-type performance pitfalls and generate Godot micro-benchmarks for them. Read-only scanner, deterministic, zero-dep.**

English | [日本語](README.ja.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-17%20passing-brightgreen.svg)](tests/)

<!-- Sync with README.ja.md as of the initial commit (see git log for the latest sync point) -->

## Why it exists

The "array-type choice" in GDScript is contradicted inside the official
documentation itself ([godot-docs #10300](https://github.com/godotengine/godot-docs/issues/10300),
still being discussed):

- GDScript reference (older wording): "Packed arrays are atomic and **slower**
  than generic arrays"
- Class reference: "Packed arrays are **faster** than typed arrays of the same
  element type + lower memory"

Actual performance depends on the operation, so this tool answers with a
two-step approach: **finding → measured benchmark**. You can always measure
before you rewrite.

## The 4 patterns it detects

| Kind | Example | Note |
|---|---|---|
| UNTYPED ARRAY | `var x = [1, 2, 3]` | Variant soup — slowest to iterate |
| TYPED ARRAY | `var x: Array[int] = ...` | Compile-time checks; Packed* is faster for the same element type |
| PACKED ARRAY | `var x: PackedInt32Array = ...` | Contiguous memory, fast (good) |
| DICT AS ARRAY | `var d = {}` + `d[i] = ...` | Sequential-key Dictionary is ~2x slower than a plain Array |

## Usage

```bash
pip install gd-bench

gd-bench .                 # scan the current .gd files
gd-bench . --json          # machine-readable output
gd-bench . --gen-bench     # generate Godot micro-benchmarks into ./gd-bench-out/
gd-bench . --bench-n 50000 # change benchmark size (default 100000)
```

Generated benchmarks run on Godot 4 headless:

```bash
godot --headless --script gd-bench-out/bench_gd_untyped_array_4.gd
# gd-bench: untyped_array
#   untyped_array: 8231 usec
#   typed_array: 5120 usec
#   ratio: 1.61x
```

## Design principles

- **Read-only**: never rewrites your source. Reporting and benchmark generation only
- **Deterministic**: no LLM. Same input always produces the same report and benchmarks
- **Zero-dependency**: Python standard library only (regex + dataclasses)

## License

MIT
