"""scan — .gd ファイルから配列型の使用を検出する（純関数・読み取り専用）。

GDScript はインデントベースの言語で、ast 的なパーサはない。ここでは
行ベースの決定論的パターンマッチ（正規表現）で配列型の使用を検出する。
LLM は使わない。同じ入力なら必ず同じ報告が出る。

検出する 4 種類のパターン（パフォーマンス観点）:

  UNTYPED ARRAY     — var x = [1, 2, 3]（型ヒント無し。Variant soup、反復が最も遅い）
  TYPED ARRAY       — var x: Array[int] = ...（コンパイル時チェックあり。中間）
  PACKED ARRAY      — var x: PackedInt32Array = ...（連続メモリ・最速）
  DICT AS ARRAY     — var d = {}; d[i] = ... のインデックス連番使用（Array で十分な可能性）

参考（godot-docs #10300 の矛盾）:
  - クラスリファレンス: 「Packed arrays は generally faster（同型の typed array 比）+ 低メモリ」
  - GDScript リファレンス（旧・修正議論中）: 「Packed は atomic で generic arrays より遅い」
"""
import re
from dataclasses import dataclass

PACKED_TYPES = [
    "PackedByteArray", "PackedInt32Array", "PackedInt64Array",
    "PackedFloat32Array", "PackedFloat64Array",
    "PackedStringArray", "PackedVector2Array", "PackedVector3Array",
    "PackedVector4Array", "PackedColorArray",
]

# var宣言（型ヒントあり/なし両方）。インデント・タブは問わない。
RE_VAR_TYPED = re.compile(r"^\s*var\s+\w+\s*:\s*Array\s*\[\s*\w+\s*\]")
RE_VAR_UNTYPED_ARRAY = re.compile(r"^\s*var\s+\w+\s*=\s*\[")
RE_VAR_PACKED = re.compile(r"^\s*var\s+\w+\s*:\s*(" + "|".join(PACKED_TYPES) + r")\b")
# Dictionary を Array 代わりに使う（連番キーへの代入）。d[0] = / d[i] = 形式。
RE_DICT_INDEXED = re.compile(r"^\s*(\w+)\[(\d+|\w+)\]\s*=")
RE_DICT_DECL = re.compile(r"^\s*var\s+(\w+)\s*(?::\s*Dictionary)?\s*=\s*\{\}")


@dataclass
class Finding:
    line_no: int
    kind: str          # untyped_array | typed_array | packed_array | dict_as_array
    snippet: str
    file: str = ""     # ソースパス（scan_repo が付与）
    note: str = ""

    def as_dict(self) -> dict:
        return {"file": self.file, "line": self.line_no, "kind": self.kind,
                "snippet": self.snippet, "note": self.note}


NOTES = {
    "untyped_array": "untyped Array holds Variants — slowest to iterate; prefer Array[T] or Packed*",
    "typed_array": "Array[T] gives compile-time checks; still Variant-backed — Packed* is faster for same element type",
    "packed_array": "Packed* arrays are contiguous & fast — good",
    "dict_as_array": "Dictionary with sequential keys — plain Array is ~2x faster and uses half the memory",
}


def scan_source(source: str, source_path: str = "<text>") -> list:
    """1 つの .gd ソースから配列型の使用を検出する（純関数）。

    返り値: [Finding, ...]（行番号昇順）
    """
    out = []
    # dict_as_array 用: 連番代入のレシーバが {} で宣言された変数かを追跡
    dict_vars = set()
    # ループ変数のバインディング: "for i in range(...)" で回っている int 変数
    # （その変数が辞書のキーに使われていたら連番キーの可能性が高い）
    loop_vars = set()
    for i, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        m = RE_DICT_DECL.match(line)
        if m:
            dict_vars.add(m.group(1))
            continue
        # "for x in range(...)": x は int ループ変数（連番キーの可能性）。
        # "for x in <collection>:" は要素列挙（キーはオブジェクト/名前）なので対象外。
        lm = re.match(r"^\s*for\s+(\w+)\s+in\s+range\s*\(", line)
        if lm:
            loop_vars.add(lm.group(1))
            continue
        if RE_VAR_PACKED.match(line):
            out.append(Finding(i, "packed_array", stripped, NOTES["packed_array"]))
            continue
        if RE_VAR_TYPED.match(line):
            out.append(Finding(i, "typed_array", stripped, NOTES["typed_array"]))
            continue
        if RE_VAR_UNTYPED_ARRAY.match(line):
            out.append(Finding(i, "untyped_array", stripped, NOTES["untyped_array"]))
            continue
        dm = RE_DICT_INDEXED.match(line)
        if dm and dm.group(1) in dict_vars:
            key = dm.group(2)
            # 連番キー判定（保守的）: int リテラル、または range() ループ変数のみ。
            # 名前付きキー（String id 等）は正当な Dictionary 使用なので検出しない。
            if re.fullmatch(r"\d+", key) or key in loop_vars:
                out.append(Finding(i, "dict_as_array", stripped, NOTES["dict_as_array"]))
    return out


def find_gd_files(root, max_files: int = 3000) -> list:
    """リポジトリから .gd ファイルを収集する（vcs/キャッシュ等は除外）。"""
    from pathlib import Path
    skip = {".git", ".venv", "venv", "node_modules", "__pycache__",
            "build", "dist", ".tox", ".godot"}
    out = []
    for p in sorted(Path(root).rglob("*.gd")):
        if any(part in skip for part in p.parts):
            continue
        out.append(p)
        if len(out) >= max_files:
            break
    return out


def scan_repo(root, max_files: int = 3000) -> dict:
    """リポジトリ全体をスキャンし、統計 + findings を返す（読み取り専用）。"""
    files = find_gd_files(root, max_files)
    findings = []
    per_file = {}
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fs = scan_source(text, source_path=p.as_posix())
        if fs:
            for f in fs:
                f.file = p.as_posix()
            per_file[p.as_posix()] = [f.as_dict() for f in fs]
            findings.extend(fs)

    counts = {}
    for f in findings:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    return {
        "root": str(root),
        "files_scanned": len(files),
        "files_with_findings": len(per_file),
        "status_counts": counts,
        "findings": [f.as_dict() for f in findings],
        "per_file": per_file,
    }
