import argparse, json, os, platform, time
from pathlib import Path
from .experts import ExpertRegistry
from .signals import detect_signals
from .router import Router
from .sessions import Session
from .telemetry import Telemetry
from .runtimes.ollama import OllamaRuntime
from .runtimes.base import RuntimeUnavailable
from .lifecycle import LifecycleManager
from .daemon import run as run_daemon

ROOT=Path(__file__).resolve().parents[2]; CONFIG=ROOT/"config/experts.toml"; DATA=ROOT/".oktopai"
def services():
    registry=ExpertRegistry.from_toml(CONFIG); telemetry=Telemetry(DATA/"events.jsonl"); runtime=OllamaRuntime(telemetry=telemetry); return registry,telemetry,runtime
def main(argv=None):
    parser=argparse.ArgumentParser(prog="oktopai"); sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("inspect"); sub.add_parser("models"); benchmark=sub.add_parser("benchmark"); benchmark.add_argument("--live",action="store_true",help="generate with an already-installed local model") ; sub.add_parser("events")
    daemon=sub.add_parser("daemon"); daemon.add_argument("--max-warm",type=int,default=1)
    preload=sub.add_parser("preload"); preload.add_argument("prompt"); preload.add_argument("--file"); preload.add_argument("--expert"); preload.add_argument("--max-warm",type=int,default=1)
    route=sub.add_parser("route"); route.add_argument("prompt"); route.add_argument("--file"); route.add_argument("--expert")
    ask=sub.add_parser("ask"); ask.add_argument("prompt"); ask.add_argument("--file"); ask.add_argument("--expert"); ask.add_argument("--session",default=str(DATA/"session.json")); ask.add_argument("--max-warm",type=int,default=1)
    args=parser.parse_args(argv); registry,telemetry,runtime=services()
    if args.command=="daemon": run_daemon(registry,runtime,telemetry,args.max_warm); return 0
    if args.command=="inspect":
        memory="unknown"
        try: memory=f"{int(os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/1024**3)} GiB"
        except (AttributeError, OSError): pass
        print(json.dumps({"python":platform.python_version(),"platform":platform.platform(),"cpu":platform.processor() or "unknown","memory":memory,"config":str(CONFIG),"runtime":"ollama","host":runtime.host,"capabilities":runtime.capabilities().__dict__,"gpu":"unavailable to WSL nvidia-smi"},indent=2)); return 0
    if args.command=="models":
        try:
            installed=runtime.list_models(); loaded=runtime.loaded_models()
            print(json.dumps({"runtime":"ollama","capabilities":runtime.capabilities().__dict__,"installed":installed,"loaded":loaded,"logical_experts":[{"name":e.name,"model":e.model,"model_kind":e.model_kind,"base_model":e.base_model,"adapter":e.adapter} for e in registry.experts.values()]},indent=2))
        except RuntimeUnavailable as exc: print(f"Runtime unavailable: {exc}"); return 2
        return 0
    if args.command=="events":
        path=DATA/"events.jsonl"
        if not path.exists(): print("No events recorded."); return 0
        for line in path.read_text().splitlines():
            event=json.loads(line); print(f"{event['timestamp']}  {event['kind']}: {json.dumps(event['data'], sort_keys=True)}")
        return 0
    if args.command in ("route","ask","preload"):
        try:
            content=Path(args.file).read_text() if getattr(args,"file",None) else None
        except OSError as exc:
            print(f"Cannot read file '{args.file}': {exc}"); return 2
        signals=detect_signals(args.prompt,args.file,content,Path.cwd()); decision=Router(registry).route(args.prompt,signals,args.expert)
        if args.command=="route": print(json.dumps({"selected":decision.selected,"score":decision.score,"confidence":decision.confidence,"reasons":decision.reasons,"alternatives":[c.__dict__ for c in decision.alternatives]},indent=2)); return 0
        if args.command=="preload":
            try:
                life=LifecycleManager(runtime,registry,telemetry,args.max_warm); warm=life.ensure_warm(decision.selected)
                print(json.dumps({"selected":decision.selected,"model":warm.model,"cold":warm.cold,"latency_ms":warm.latency_ms,"evicted":warm.evicted},indent=2)); return 0
            except RuntimeUnavailable as exc: print(f"Cannot preload locally: {exc}"); return 2
        session=Session.load(Path(args.session)); session.add_user(args.prompt); 
        if args.file: session.add_file(args.file,content or "")
        life=LifecycleManager(runtime,registry,telemetry,args.max_warm); telemetry.emit("route_decision",expert=decision.selected,model=registry.get(decision.selected).model,score=decision.score,confidence=decision.confidence)
        try:
            warm=life.ensure_warm(decision.selected); result=runtime.generate(registry.get(decision.selected).model,session.prompt(registry.get(decision.selected).system_prompt),registry.get(decision.selected).warm_retention_seconds); life.mark_used(decision.selected); session.add_assistant(result.text); session.expert_history.append(decision.selected); session.save(Path(args.session)); print(result.text); telemetry.emit("generation_completed",expert=decision.selected,model=registry.get(decision.selected).model,load_ms=warm.latency_ms,first_token_ms=result.first_token_ms,generation_ms=result.generation_ms,cold=result.cold); return 0
        except RuntimeUnavailable as exc: print(f"Cannot answer locally: {exc}\nRouting succeeded with expert '{decision.selected}', but no local model runtime is available."); return 2
    if args.command=="benchmark":
        cases=[("Fix this TypeScript generic", "typescript"),("Why does this React component rerender?", "react"),("Explain this Next.js server/client component issue", "nextjs"),("Generate a unit test", "testing"),("Refactor this function", "general-coding")]; route_start=time.perf_counter(); rows=[]
        raw=[]
        for prompt,expected in cases:
            d=Router(registry).route(prompt,detect_signals(prompt)); row={"prompt":prompt,"expected":expected,"selected":d.selected,"correct":d.selected==expected,"confidence":d.confidence}
            rows.append(row)
        routing_latency_ms=(time.perf_counter()-route_start)*1000; cold_start_ms=[]; warm_start_ms=[]; total_response_ms=[]
        if args.live:
            life=LifecycleManager(runtime,registry,telemetry,max_warm_models=1)
            for row in rows:
                try:
                    expert=registry.get(row["selected"]); warm=life.ensure_warm(expert.name); started=time.perf_counter(); result=runtime.generate(expert.model,[{"role":"system","content":expert.system_prompt},{"role":"user","content":row["prompt"]}],expert.warm_retention_seconds); response_ms=(time.perf_counter()-started)*1000
                    row.update({"output":result.text,"cold":result.cold,"load_ms":warm.latency_ms,"generation_ms":result.generation_ms,"total_response_ms":response_ms})
                    (cold_start_ms if warm.cold else warm_start_ms).append(warm.latency_ms); total_response_ms.append(response_ms); raw.append(row)
                except RuntimeUnavailable as exc: row["runtime_error"]=str(exc); raw.append(row)
        report={"routing_latency_ms":routing_latency_ms,"routing_accuracy":sum(row["correct"] for row in rows)/len(rows),"cases":rows,"cold_start_ms":cold_start_ms or None,"warm_start_ms":warm_start_ms or None,"total_response_ms":total_response_ms or None,"raw_outputs":str(DATA/"benchmark-outputs.jsonl"),"note":"Live timing fields are populated only with --live and an already-installed local model."}
        DATA.mkdir(parents=True,exist_ok=True); (DATA/"benchmark-routing.json").write_text(json.dumps(report,indent=2)); (DATA/"benchmark-outputs.jsonl").write_text("\n".join(json.dumps(row) for row in raw) + ("\n" if raw else "")); print(json.dumps(report,indent=2)); return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
