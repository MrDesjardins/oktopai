"""Build a provenance-preserving train/validation/test JSONL dataset."""
from pathlib import Path
import argparse, hashlib, json

ROOT=Path(__file__).resolve().parents[1]
def stable_split(identifier: str) -> str:
    value=int(hashlib.sha256(identifier.encode()).hexdigest()[:8],16)%100
    return "test" if value < 15 else ("validation" if value < 30 else "train")
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--domain",required=True); parser.add_argument("--output",type=Path,default=ROOT/".oktopai/datasets"); parser.add_argument("--name",default=None,help="Output dataset stem, useful for versioned datasets"); parser.add_argument("--include-benchmark",action="store_true"); parser.add_argument("--include-teacher",action="store_true"); parser.add_argument("--teacher",type=Path,default=ROOT/".oktopai/teacher-traces.jsonl"); parser.add_argument("--include-synthetic",action="store_true"); parser.add_argument("--synthetic",type=Path,default=ROOT/".oktopai/datasets/typescript-synthetic-v1.jsonl"); args=parser.parse_args()
    source=ROOT/"training/seed_examples.jsonl"; records=[]
    benchmark_tasks={item["id"]: item for item in json.loads((ROOT/"benchmarks/tasks.json").read_text()).get("tasks", [])}
    for line in source.read_text().splitlines():
        item=json.loads(line)
        if item["domain"]==args.domain:
            item["split"]=item.get("split") if item.get("split") in {"train","validation","test"} else stable_split(item["id"]); records.append(item)
    if args.include_benchmark:
        report=ROOT/".oktopai/benchmark-report.json"
        if report.exists():
            data=json.loads(report.read_text())
            for item in data.get("records",[]):
                task=benchmark_tasks.get(item.get("task_id"), {})
                if task.get("domain") != args.domain:
                    continue
                for run in item.get("runs",[]):
                    if run.get("verification",{}).get("status")=="verified" and run.get("output"):
                        records.append({"id":"benchmark-"+item["task_id"],"domain":args.domain,"split":"validation","provenance":{"source":"local-benchmark","task_id":item["task_id"]},"messages":[{"role":"user","content":item["task_id"]}],"completion":run["output"]})
    if args.include_teacher:
        teacher_path=args.teacher
        if teacher_path.exists():
            for line in teacher_path.read_text().splitlines():
                item=json.loads(line)
                if item.get("domain")==args.domain: item["split"]="train"; records.append(item)
    if args.include_synthetic and args.synthetic.exists():
        for line in args.synthetic.read_text().splitlines():
            item=json.loads(line)
            if item.get("domain")==args.domain: records.append(item)
    args.output.mkdir(parents=True,exist_ok=True); path=args.output/((args.name or args.domain)+".jsonl"); path.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in records)+("\n" if records else "")); print(json.dumps({"domain":args.domain,"records":len(records),"path":str(path),"splits":{split:sum(x["split"]==split for x in records) for split in ["train","validation","test"]}},indent=2))
if __name__ == "__main__": main()
