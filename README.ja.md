# gd-bench

**GDScript の配列型パフォーマンス問題を検出し、Godot マイクロベンチを生成する CLI。読み取り専用・決定論的・依存ゼロ。**

[English](README.md) | 日本語

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-17%20passing-brightgreen.svg)](tests/)

<!-- Sync with README.md as of the initial commit (see git log for the latest sync point) -->

## なぜ存在するか

GDScript の「配列型の選択」は、公式ドキュメント内でも記述が矛盾している（[godot-docs #10300](https://github.com/godotengine/godot-docs/issues/10300) 修正議論中）:

- GDScript リファレンス（旧記載）: 「Packed arrays は atomic で generic arrays より**遅い**」
- クラスリファレンス: 「Packed arrays は同型の typed arrays 比で **faster** + 低メモリ」

実際のパフォーマンスは操作次第で変わるため、このツールは「指摘 → 実測ベンチ」の 2 段構えで答える。書き換え前に必ず計測できる。

## 検出する 4 パターン

| 種類 | 例 | 指摘 |
|---|---|---|
| UNTYPED ARRAY | `var x = [1, 2, 3]` | Variant soup — 反復が最も遅い |
| TYPED ARRAY | `var x: Array[int] = ...` | コンパイル時チェックあり。Packed* なら同型要素でより速い |
| PACKED ARRAY | `var x: PackedInt32Array = ...` | 連続メモリ・速い（良い） |
| DICT AS ARRAY | `var d = {}` + `d[i] = ...` | 連番キーの辞書は素の Array より ~2x 遅い |

## 使い方

```bash
pip install gd-bench

gd-bench .                 # カレントの .gd をスキャン
gd-bench . --json          # 機械可読出力
gd-bench . --gen-bench     # 検出箇所の Godot マイクロベンチを ./gd-bench-out/ に生成
gd-bench . --bench-n 50000 # ベンチの要素数を変更（default 100000）
```

生成されたベンチは Godot 4 の headless で走る:

```bash
godot --headless --script gd-bench-out/bench_gd_untyped_array_4.gd
# gd-bench: untyped_array
#   untyped_array: 8231 usec
#   typed_array: 5120 usec
#   ratio: 1.61x
```

## 設計原則

- **読み取り専用**: ソースを書き換えない。報告とベンチ生成のみ
- **決定論的**: LLM 不使用。同じ入力なら必ず同じ報告・同じベンチが出る
- **依存ゼロ**: Python 標準ライブラリのみ（regex + dataclasses）

## ライセンス

MIT
