"""Retain local teacher traces whose extracted TypeScript compiles."""
from pathlib import Path
import argparse, json, re, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tsc = shutil.which("tsc") or str(ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc")
    accepted=[]
    for line in args.input.read_text().splitlines():
        item=json.loads(line)
        blocks=re.findall(r"```(?:typescript|ts)?\s*\n(.*?)```", item.get("completion", ""), re.DOTALL | re.IGNORECASE)
        if not blocks:
            continue
        with tempfile.TemporaryDirectory(prefix="oktopai-teacher-") as directory:
            path=Path(directory)/"candidate.ts"
            path.write_text("\n".join(blocks))
            result=subprocess.run([tsc,"--noEmit","--strict","--target","ES2020",str(path)],capture_output=True,text=True)
        item["split"]="train"
        item["provenance"]["verified_by"]="local-tsc"
        item["provenance"]["verification_status"]="verified" if result.returncode==0 else "rejected"
        if result.returncode==0:
            accepted.append(item)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text("\n".join(json.dumps(item,ensure_ascii=False) for item in accepted)+("\n" if accepted else ""))
    print(json.dumps({"input":str(args.input),"accepted":len(accepted),"output":str(args.output)},indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
