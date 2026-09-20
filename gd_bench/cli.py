"""cli — gd-bench コマンドライン入口（読み取り専用・決定論的）。

usage:
  gd-bench [ROOT]              # .gd ファイルの配列型使用を検出
  gd-bench [ROOT] --json       # 機械可読出力
  gd-bench [ROOT] --gen-bench  # 検出箇所に対応する Godot マイクロベンチを生成
"""
import argparse
import json
from pathlib import Path

from gd_bench import bench, scan

MARK = {
    "untyped_array": "🐢 UNTYPED ARRAY",
    "typed_array": "🔧 TYPED ARRAY",
    "packed_array": "✅ PACKED ARRAY",
    "dict_as_array": "📦 DICT AS ARRAY",
}


def render(report: dict, json_output: bool) -> str:
    if json_output:
        return json.dumps(report, ensure_ascii=False, indent=2)

    lines = [
        f"gd-bench — scanned {report['root']}",
        f"  files: {report['files_scanned']} scanned | with findings: {report['files_with_findings']}",
        "",
    ]
    if not report["findings"]:
        lines.append("no array-type pitfalls detected.")
    for f in report["findings"]:
        lines.append(f"{f['file']}:{f['line']}  {MARK.get(f['kind'], f['kind'])}")
        lines.append(f"    {f['snippet']}")
        lines.append(f"    -> {f['note']}")
    lines.append("")
    lines.append(f"summary: {json.dumps(report['status_counts'], ensure_ascii=False)}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="gd-bench",
        description="Detect GDScript array-type performance pitfalls. Read-only, deterministic.")
    ap.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--gen-bench", action="store_true",
                    help="generate Godot micro-benchmarks for detected pitfalls (./gd-bench-out/)")
    ap.add_argument("--bench-n", type=int, default=100_000, help="elements per benchmark (default: 100000)")
    args = ap.parse_args(argv)

    report = scan.scan_repo(args.root, )
    if args.gen_bench:
        out_dir = Path("./gd-bench-out")
        out_dir.mkdir(parents=True, exist_ok=True)
        generated = 0
        for f in report["findings"]:
            script = bench.bench_for_finding(f, n=args.bench_n)
            if not script:
                continue
            name = bench.bench_name(f["kind"], f["line"])
            (out_dir / name).write_text(script, encoding="utf-8")
            generated += 1
        print(f"[bench] generated {generated} benchmark script(s) in {out_dir}/")
        print(f"[bench] run with: godot --headless --script <script>.gd")

    print(render(report, json_output=args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
