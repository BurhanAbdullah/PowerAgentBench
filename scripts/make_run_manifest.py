from __future__ import annotations

import argparse
from pathlib import Path

from poweragentbench.run_manifest import build_manifest, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a reproducible PowerAgentBench run manifest.")
    parser.add_argument("--output", type=Path, default=Path("results/run_manifest.json"))
    parser.add_argument("--benchmark", default="PowerAgentBench")
    parser.add_argument("--track", default="steady_n2")
    parser.add_argument("--case-source", choices=["case39", "synthetic"], default="case39")
    parser.add_argument("--cases", type=int, default=8)
    parser.add_argument("--seed-start", type=int, default=1000)
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--budget", type=int, default=80)
    parser.add_argument("--report-k", type=int, default=20)
    parser.add_argument("--rating-scale", type=float, default=0.85)
    args = parser.parse_args()

    manifest = build_manifest(
        benchmark=args.benchmark,
        track=args.track,
        cases=args.cases,
        seed_start=args.seed_start,
        k=args.k,
        validation_budget=args.budget,
        report_k=args.report_k,
        case_source=args.case_source,
        config={"rating_scale": args.rating_scale},
    )
    path = write_manifest(args.output, manifest)
    print(f"wrote {path}")
    print(f"manifest_sha256={manifest['manifest_sha256']}")


if __name__ == "__main__":
    main()
