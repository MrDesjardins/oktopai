"""Generate a large, deterministic TypeScript specialist corpus.

The records are programmatically synthesized from type-safe templates. They are
not presented as human data or teacher truth; every record carries generator
provenance and can be compiler-verified before training.
"""
from pathlib import Path
import argparse, hashlib, json, random, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "typescript-synthetic-v1"


def record(index: int, family: str, prompt: str, completion: str, source: str) -> dict:
    digest = hashlib.sha256(f"{VERSION}:{index}:{family}:{source}".encode()).hexdigest()[:16]
    bucket = int(digest[:8], 16) % 100
    split = "test" if bucket < 10 else ("validation" if bucket < 25 else "train")
    return {"id": f"{VERSION}-{index:05d}", "domain": "typescript", "family": family, "split": split, "provenance": {"source": "programmatic-template", "generator": VERSION, "license": "CC0-like project seed", "synthetic": True}, "messages": [{"role": "system", "content": "You are a precise TypeScript specialist. Return compiler-valid code."}, {"role": "user", "content": prompt}], "completion": completion, "source_code": source}


def make(index: int, family_index: int) -> dict:
    n = index + 1
    name = f"Value{n}"
    if family_index == 0:
        source = f"function get{name}<T>(obj: T, key: string) {{ return obj[key]; }}"
        completion = f"function get{name}<T, K extends keyof T>(obj: T, key: K): T[K] {{ return obj[key]; }}"
        return record(index, "generic-indexed-access", f"Fix this generic indexed access without using any:\n\n{source}", completion, source)
    if family_index == 1:
        source = f"function length{name}(value: string | string[] | null) {{ return value.length; }}"
        completion = f"function length{name}(value: string | string[] | null): number {{ if (value === null) return 0; return value.length; }}"
        return record(index, "null-narrowing", f"Narrow this union safely without assertions:\n\n{source}", completion, source)
    if family_index == 2:
        source = f"type Result{name} = {{ kind: 'ok'; value: string }} | {{ kind: 'error'; message: string }};"
        completion = source + f" function format{name}(result: Result{name}): string {{ return result.kind === 'ok' ? result.value : result.message; }}"
        return record(index, "discriminated-union", "Use the discriminant to format this union safely.", completion, source)
    if family_index == 3:
        source = f"const scores{name}: Record<string, number> = {{ tests: 1 }};"
        completion = source + f" const score{name}: number = scores{name}.tests;"
        return record(index, "record-dictionary", "Type this string-keyed numeric dictionary and read a known value.", completion, source)
    if family_index == 4:
        source = f"function first{name}<T>(items: T[]) {{ return items[0]; }}"
        completion = f"function first{name}<T>(items: readonly T[]): T | undefined {{ return items[0]; }}"
        return record(index, "readonly-generic", "Accept a readonly generic array and return its optional first item.", completion, source)
    if family_index == 5:
        source = f"async function load{name}() {{ return 'ready'; }}"
        completion = f"async function load{name}(): Promise<string> {{ return 'ready'; }}"
        return record(index, "async-return", "Add the precise Promise return type to this async function.", completion, source)
    if family_index == 6:
        source = f"function parse{name}(value: string | number) {{ return typeof value === 'string' ? Number(value) : value; }}"
        completion = f"function parse{name}(value: string): number;\nfunction parse{name}(value: number): number;\nfunction parse{name}(value: string | number): number {{ return typeof value === 'string' ? Number(value) : value; }}"
        return record(index, "overload-signature", "Add overload signatures and a compatible implementation.", completion, source)
    if family_index == 7:
        source = f"type Optional{name}<T> = T;"
        completion = f"type Optional{name}<T> = {{ [K in keyof T]?: T[K] }};"
        return record(index, "mapped-type", "Define a mapped type that makes every property optional.", completion, source)
    if family_index == 8:
        source = f"function isText{name}(value: unknown) {{ return typeof value === 'string'; }}"
        completion = f"function isText{name}(value: unknown): value is string {{ return typeof value === 'string'; }}"
        return record(index, "type-predicate", "Add a type predicate so this string guard narrows unknown.", completion, source)
    source = f"function keys{name}<T>(obj: T) {{ return Object.keys(obj); }}"
    completion = f"function keys{name}<T extends object>(obj: T): string[] {{ return Object.keys(obj); }}"
    return record(index, "object-constraint", "Constrain this generic helper to objects and declare its return type.", completion, source)


def verify(records: list[dict]) -> dict:
    tsc = shutil.which("tsc")
    fixture_tsc = ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc"
    tsc = tsc or (str(fixture_tsc) if fixture_tsc.exists() else None)
    if not tsc:
        return {"available": False, "verified": None, "error": "tsc is not installed"}
    with tempfile.TemporaryDirectory(prefix="oktopai-ts-synthetic-") as directory:
        source = "\n".join(item["completion"] for item in records)
        path = Path(directory) / "synthetic.ts"
        path.write_text(source)
        result = subprocess.run([tsc, "--noEmit", "--strict", "--target", "ES2020", str(path)], capture_output=True, text=True)
        return {"available": True, "verified": result.returncode == 0, "stderr": result.stderr[-1000:], "stdout": result.stdout[-3000:]}


def main() -> int:
    global VERSION
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--output", type=Path, default=ROOT / ".oktopai/datasets/typescript-synthetic-v1.jsonl")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    VERSION = args.version
    if args.count < 1:
        raise SystemExit("--count must be positive")
    random.seed(17)
    records = [make(index, index % 10) for index in range(args.count)]
    verification = verify(records) if args.verify else {"available": None, "verified": None}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n")
    print(json.dumps({"version": VERSION, "records": len(records), "output": str(args.output), "families": 10, "splits": {split: sum(item["split"] == split for item in records) for split in ("train", "validation", "test")}, "verification": verification}, indent=2))
    if verification.get("available") and not verification.get("verified"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
