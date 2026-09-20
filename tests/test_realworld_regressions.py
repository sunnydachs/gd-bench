"""scan — 実OSSプロジェクトで見つけた誤検出パターンの回帰テスト（2026-09-20 実測）。

GodotProjectZero (TinyTakinTeller, 2.1kスター級) の BulletUpHell アドオンで
35/36 の dict_as_array が String キー（正当な Dictionary 使用）だった誤検出を
受けて、保守的ルール（int リテラル or range() ループ変数のみ検出）の回帰テスト。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gd_bench.scan import scan_source  # noqa: E402


def test_named_string_key_dict_not_flagged():
    """String id をキーにする Dictionary は正当な使用 — 検出してはならない。

    実例: BulletUpHell/BuHSpawner.gd — arrayInstances[id] = instance (id: String)
    """
    src = (
        "var arrayInstances: Dictionary = {}\n"
        "\n"
        "func new_instance(id: String, instance) -> void:\n"
        "\tarrayInstances[id] = instance\n"
    )
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" not in kinds, kinds


def test_int_literal_keys_flagged():
    """d[0] =, d[1] = の int リテラル連番は本物の dict-as-array。"""
    src = (
        "var cache = {}\n"
        "\tcache[0] = 10\n"
    )
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" in kinds, kinds


def test_range_loop_var_keys_flagged():
    """range() ループ変数をキーに使う辞書は連番 — 検出する。

    実例: spreadsheet_import.gd — result[i] = {} (for i in range(prop_types.size()))
    ※ GDScript には range(n) と for i in n: の両方の int ループ書式があるが、
    後者は要素列挙と構文上区別できないため、検出は range() のみに保守的に絞る
    （46件の誤検出を消すために 1件の検出を手放すトレードオフ）。
    """
    src = (
        "var result = {}\n"
        "for i in range(prop_types.size()):\n"
        "\tresult[i] = {}\n"
    )
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" in kinds, kinds


def test_int_bounds_loop_var_keys_not_flagged():
    """for i in N: 形式（rangeなしのintループ）は要素列挙と区別できないので検出しない。

    実例: open-rts UnitMovementUtils.gd — for i in N: だが要素列挙との区別が
    静的に不可能。保守的な検出方針では偽陰性を受け入れる。
    """
    src = (
        "var result = {}\n"
        "for i in prop_types.size():\n"
        "\tresult[i] = {}\n"
    )
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" not in kinds, kinds


def test_object_iteration_key_not_flagged():
    """for unit in units: の unit は要素（オブジェクト）であって連番キーではない。

    実例: open-rts FogOfWar.gd — units_synced[unit] = 1 (unit は Node)
    """
    src = (
        "var units_synced = {}\n"
        "for unit in get_tree().get_nodes_in_group('units'):\n"
        "\tunits_synced[unit] = 1\n"
    )
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" not in kinds, kinds


def test_non_range_var_keys_not_flagged():
    """range() と無関係な変数名のキー（名前付きの可能性）は保守的に検出しない。"""
    src = (
        "var registry = {}\n"
        "registry[user_id] = profile\n"
    )
    fs = scan_source(src)
    kinds = [f.kind for f in fs]
    assert "dict_as_array" not in kinds, kinds
