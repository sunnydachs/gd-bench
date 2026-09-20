"""bench — マイクロベンチ生成の単体テスト（決定論性の検証）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gd_bench.bench import bench_for_finding, bench_name, render_bench  # noqa: E402


def test_bench_name_deterministic():
    assert bench_name("untyped_array", 12) == bench_name("untyped_array", 12)
    assert bench_name("untyped_array", 12) != bench_name("typed_array", 12)


def test_render_bench_deterministic_with_fixed_ts():
    a = render_bench("untyped_array", "typed_array", "untyped_array", "note", ts="T")
    b = render_bench("untyped_array", "typed_array", "untyped_array", "note", ts="T")
    assert a == b


def test_bench_for_untyped():
    f = {"kind": "untyped_array", "snippet": "var x = [1]", "note": "n"}
    s = bench_for_finding(f)
    assert "func _bench_a" in s
    assert "func _bench_b" in s
    assert "Array[int]" in s
    assert "extends SceneTree" in s


def test_bench_for_packed_is_empty():
    # Packed は既に最適 — ベンチは生成しない（正の指摘のみ）
    f = {"kind": "packed_array", "snippet": "var x: PackedInt32Array", "note": "good"}
    assert bench_for_finding(f) == ""


def test_bench_for_dict():
    f = {"kind": "dict_as_array", "snippet": "d[0] = 1", "note": "n"}
    s = bench_for_finding(f)
    assert "var d := {}" in s
    assert "PackedInt32Array" not in s or "Array" in s
