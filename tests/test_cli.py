"""cli — 出力整形とエンドツーエンドの単体テスト。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gd_bench.cli import MARK, main, render  # noqa: E402
from gd_bench.scan import scan_repo  # noqa: E402


def test_mark_covers_all_kinds():
    for kind in ["untyped_array", "typed_array", "packed_array", "dict_as_array"]:
        assert kind in MARK


def test_render_text():
    r = {
        "root": "/tmp/game",
        "files_scanned": 2,
        "files_with_findings": 1,
        "status_counts": {"untyped_array": 1},
        "findings": [
            {"file": "/tmp/game/main.gd", "line": 1, "kind": "untyped_array",
             "snippet": "var items = [1]", "note": "prefer Array[T]"},
        ],
    }
    out = render(r, json_output=False)
    assert "gd-bench — scanned /tmp/game" in out
    assert "🐢 UNTYPED ARRAY" in out
    assert "main.gd:1" in out


def test_render_json():
    r = {"root": "/x", "files_scanned": 0, "files_with_findings": 0,
         "status_counts": {}, "findings": []}
    out = render(r, json_output=True)
    assert '"root": "/x"' in out


def test_e2e_main(tmp_path, capsys):
    d = tmp_path / "proj"
    d.mkdir()
    (d / "main.gd").write_text(
        "var a = [1, 2]\nvar b: Array[int] = [3]\n", encoding="utf-8")
    rc = main([str(d)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "untyped_array" in captured.out
    assert "typed_array" in captured.out
