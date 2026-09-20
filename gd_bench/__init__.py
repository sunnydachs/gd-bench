"""gd_bench — GDScript 配列型パフォーマンス診断CLI（読み取り専用スキャナ + ベンチ生成）。

 GDScriptの「配列型の選択」は公式ドキュメントでも矛盾した記述がある（godot-docs #10300）。
 このツールは .gd ファイルから配列型の使用を検出し、パフォーマンス観点の指摘と
 実測マイクロベンチの生成を提供する。
"""
from gd_bench import cli

__all__ = ["cli"]
__version__ = "0.1.0"
