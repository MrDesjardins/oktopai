"""Generate local teacher traces from installed oktopai specialist aliases.

Teacher traces are raw candidates, not automatically trusted training labels.
"""
from pathlib import Path
import argparse, json, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from oktopai.experts import ExpertRegistry
from oktopai.runtimes.ollama import OllamaRuntime
from oktopai.runtimes.base import RuntimeUnavailable

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--domain",default="typescript"); parser.add_argument("--output",type=Path,default=ROOT/".oktopai/teacher-traces.jsonl"); parser.add_argument("--model"); parser.add_argument("--input",type=Path,default=ROOT/"training/seed_examples.jsonl"); parser.add_argument("--limit",type=int); args=parser.parse_args()
    registry=ExpertRegistry.from_toml(ROOT/"config/experts.toml"); expert=registry.get(args.domain if args.domain in registry.experts else "general-coding"); model=args.model or expert.model; runtime=OllamaRuntime(); records=[]
    candidates=[]
    for line in args.input.read_text().splitlines():
        item=json.loads(line)
        if item.get("domain")==args.domain: candidates.append(item)
    for seed in candidates[:args.limit] if args.limit else candidates:
        user_content = seed.get("messages", [{"content": seed.get("prompt", "")}])[-1]["content"]
        if seed.get("source_code"):
            user_content += "\n\nSource fixture:\n```typescript\n" + seed["source_code"] + "\n```"
        messages=[{"role":"system","content":expert.system_prompt+" Return a concise, correct answer grounded in the task."},{"role":"user","content":user_content}]
        try:
            result=runtime.generate(model,messages,300); records.append({"id":"teacher-"+seed["id"],"domain":args.domain,"split":"candidate","provenance":{"source":"local-ollama-teacher","model":model,"seed_id":seed["id"],"source_provenance":seed.get("provenance")},"messages":messages,"completion":result.text,"generation_ms":result.generation_ms,"tokens_per_second":result.tokens_per_second}); print(f"{seed['id']}: {result.generation_ms:.0f} ms")
        except RuntimeUnavailable as exc: print(exc,file=sys.stderr); return 2
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in records)+("\n" if records else "")); print(f"saved {len(records)} teacher traces to {args.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
