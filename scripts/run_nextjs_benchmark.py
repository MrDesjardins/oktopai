"""Benchmark local Next.js/TypeScript repair with one model or hot-swapped experts.

The fixture is copied to a temporary directory. Model responses must be JSON:
{"files":{"relative/path.tsx":"complete file contents"}}. Changes are
allowlisted to fixture files, then typecheck/build are run when dependencies
are available. No npm install occurs unless --install is explicitly supplied.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, tempfile, time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from oktopai.runtimes.ollama import OllamaRuntime
from oktopai.runtimes.base import RuntimeUnavailable

ROOT=Path(__file__).resolve().parents[1]; FIXTURE=ROOT/"benchmarks/nextjs_fixture"; ALLOWED={"app/page.tsx","lib/getValue.ts","next.config.mjs"}
PROMPTS={"nextjs":"Return JSON only in the form {\"files\":{\"app/page.tsx\":\"COMPLETE FILE CONTENT\"}}. Fix app/page.tsx for the Next.js App Router. Preserve behavior and add the required client boundary. Every file value MUST be a plain string containing the complete file, never a diff, patch, or nested object. Include only changed allowlisted files.","typescript":"Return JSON only in the form {\"files\":{\"lib/getValue.ts\":\"COMPLETE FILE CONTENT\"}}. Fix lib/getValue.ts with a type-safe generic indexed access signature. Every file value MUST be a plain string containing the complete file, never a diff, patch, or nested object. Include only changed allowlisted files.","single":"Return JSON only in the form {\"files\":{\"app/page.tsx\":\"COMPLETE FILE CONTENT\",\"lib/getValue.ts\":\"COMPLETE FILE CONTENT\"}}. Fix both issues. Every file value MUST be a plain string containing complete file contents, never a diff, patch, or nested object."}
def parse_files(text):
    start=text.find("{"); end=text.rfind("}")
    if start<0 or end<=start: raise ValueError("model did not return JSON")
    data=json.loads(text[start:end+1]); files=data.get("files",{})
    if not isinstance(files,dict): raise ValueError("model files field was not an object")
    normalized={}
    for path,content in files.items():
        clean=str(path).replace("\\","/").lstrip("./")
        for prefix in ("project/", "benchmarks/nextjs_fixture/"):
            if clean.startswith(prefix): clean=clean[len(prefix):]
        if clean not in ALLOWED: raise ValueError(f"model returned non-allowlisted file: {path}")
        if isinstance(content, dict) and isinstance(content.get("content"), str): content=content["content"]
        if not isinstance(content, str): raise ValueError(f"model returned non-text content for: {path}")
        normalized[clean]=content
    return normalized
def copy_fixture(destination):
    shutil.copytree(FIXTURE,destination,ignore=shutil.ignore_patterns("node_modules",".next"))
    return destination
def run_command(command,cwd):
    try:
        result=subprocess.run(command,cwd=cwd,text=True,capture_output=True,timeout=180)
        return {"available":True,"returncode":result.returncode,"output":(result.stdout+result.stderr)[-4000:]}
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc: return {"available":False,"error":str(exc)}
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--model",default="oktopai-nextjs"); parser.add_argument("--mode",choices=["single","swapped"],default="swapped"); parser.add_argument("--oracle",action="store_true",help="apply known-correct reference files without a model"); parser.add_argument("--install",action="store_true"); parser.add_argument("--build",action="store_true"); args=parser.parse_args()
    runtime=OllamaRuntime(); report={"mode":"oracle" if args.oracle else args.mode,"model":args.model,"fixture":str(FIXTURE),"runs":[]}; started=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="oktopai-nextjs-") as temporary:
        project=copy_fixture(Path(temporary)/"project")
        if args.install: run_command(["npm","install"],project)
        calls=[] if args.oracle else ([ ("single",args.model)] if args.mode=="single" else [("nextjs","oktopai-nextjs"),("typescript","oktopai-typescript")])
        files={}
        if args.oracle:
            files={"app/page.tsx":"\"use client\";\n\nimport { useState } from \"react\";\n\nexport default function Page() {\n  const [open, setOpen] = useState(false);\n  return <button onClick={() => setOpen(!open)}>{String(open)}</button>;\n}\n","lib/getValue.ts":"export function getValue<T, K extends keyof T>(obj: T, key: K): T[K] {\n  return obj[key];\n}\n"}
            report["runs"].append({"role":"oracle","model":None,"files":list(files),"verified_reference":True})
        for role,model in calls:
            context="\n".join(f"FILE {path}:\n{(project/path).read_text()}" for path in ALLOWED if (project/path).exists())
            raw_output=""
            try:
                request=[{"role":"system","content":"You are a local coding specialist. Follow the requested JSON patch protocol exactly."},{"role":"user","content":PROMPTS[role]+"\n\n"+context}]
                result=runtime.generate(model,request,300); raw_output=result.text; patch=parse_files(raw_output); files.update(patch)
                report["runs"].append({"role":role,"model":model,"generation_ms":result.generation_ms,"prompt_tokens":result.prompt_tokens,"completion_tokens":result.completion_tokens,"tokens_per_second":result.tokens_per_second,"cold":result.cold,"files":list(patch),"output":result.text})
            except (RuntimeUnavailable,ValueError,json.JSONDecodeError) as exc: report["runs"].append({"role":role,"model":model,"error":str(exc),"raw_output":raw_output})
        for path,content in files.items(): (project/path).write_text(content)
        report["static_correctness"]={"client_boundary":"use client" in (project/"app/page.tsx").read_text(),"generic_keyof":"keyof T" in (project/"lib/getValue.ts").read_text() and "T[K]" in (project/"lib/getValue.ts").read_text()}
        report["static_correctness"]["all_passed"]=all(report["static_correctness"].values())
        if args.build:
            report["typecheck"]=run_command(["npm","run","typecheck"],project); report["build"]=run_command(["npm","run","build"],project)
        report["total_ms"]=(time.perf_counter()-started)*1000
    output=ROOT/".oktopai"/("nextjs-benchmark-"+report["mode"]+".json"); output.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2)); return 0 if report["static_correctness"]["all_passed"] else 1
if __name__ == "__main__": raise SystemExit(main())
