"""Prepare candidate supervised/distillation records from verified local runs.

Only records with explicit verification evidence are selected by default.
This script does not upload data or train a model.
"""
from pathlib import Path
import argparse, json

ROOT = Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--input",type=Path,default=ROOT/".oktopai/benchmark-report.json"); parser.add_argument("--output",type=Path,default=ROOT/".oktopai/training-candidates.jsonl"); parser.add_argument("--include-fixture",action="store_true"); parser.add_argument("--domain"); args=parser.parse_args()
    report=json.loads(args.input.read_text()); tasks={task["id"]:task for task in json.loads((ROOT/"benchmarks/tasks.json").read_text())["tasks"]}; records=[]
    for item in report.get("records",[]):
        for run in item.get("runs",[]):
            verification=run.get("verification",{}); allowed=verification.get("status")=="verified" or (args.include_fixture and verification.get("status")=="fixture_pass")
            domain=tasks.get(item["task_id"],{}).get("domain")
            if allowed and run.get("output") and (not args.domain or domain == args.domain):
                records.append({"task_id":item["task_id"],"domain":domain,"model":run.get("model"),"messages":[{"role":"user","content":tasks.get(item["task_id"],{}).get("prompt",item["task_id"])}],"completion":run["output"],"evidence":verification,"source":"local-benchmark"})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in records)+("\n" if records else "")); print(f"prepared {len(records)} candidates at {args.output}")
if __name__ == "__main__": main()
