"""scan — 配列型検出の単体テスト（純関数・ネットワークなし）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gd_bench.scan import scan_source, scan_repo  # noqa: E402


def test_detects_untyped_array():
    src = "var items = [1, 2, 3]\n"
    fs = scan_source(src)
    assert len(fs) == 1
    assert fs[0].kind == "untyped_array"
    assert fs[0].line_no == 1


def test_detects_typed_array():
    src = "var items: Array[int] = [1, 2, 3]\n"
    fs = scan_source(src)
    assert len(fs) == 1
    assert fs[0].kind == "typed_array"


def test_detects_packed_array():
    src = "var points: PackedVector2Array = PackedVector2Array()\n"
    fs = scan_source(src)
    assert len(fs) == 1
    assert fs[0].kind == "packed_array"


def test_detects_dict_as_array():
    src = "var cache = {}\nvar x = 1\n	cache[0] = x\n"
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" in kinds


def test_dict_non_sequential_not_flagged():
    # {} 宣言されていない変数への添字代入は検出しない
    src = "var arr: Array[int] = []\n	arr[0] = 1\n"
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" not in kinds


def test_comments_ignored():
    src = "# var items = [1, 2, 3]\n"
    assert scan_source(src) == []


def test_multiple_findings_sorted_by_line():
    src = (
        "var a = [1]\n"
        "var b: Array[int] = [2]\n"
        "var c: PackedInt32Array = PackedInt32Array()\n"
    )
    fs = scan_source(src)
    lines = [f.line_no for f in fs]
    assert lines == [1, 2, 3]
    assert [f.kind for f in fs] == ["untyped_array", "typed_array", "packed_array"]


def test_scan_repo_stats(tmp_path):
    d = tmp_path / "game"
    d.mkdir()
    (d / "main.gd").write_text("var items = [1, 2, 3]\n", encoding="utf-8")
    (d / "other.txt").write_text("var items = [1]\n", encoding="utf-8")  # .gd 以外は無視
    (d / ".godot").mkdir()
    (d / ".godot" / "skip.gd").write_text("var x = [1]\n", encoding="utf-8")  # 除外ディレクトリ
    r = scan_repo(d)
    assert r["files_scanned"] == 1
    assert r["status_counts"] == {"untyped_array": 1}
    assert r["files_with_findings"] == 1
