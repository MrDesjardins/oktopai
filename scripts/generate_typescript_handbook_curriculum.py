#!/usr/bin/env python3
"""Generate a broad, deterministic TypeScript Handbook curriculum.

The records are synthetic supervised examples. They are compiler-checked but
are not presented as human or teacher data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "typescript-handbook-v1"
DOCS = "https://www.typescriptlang.org/docs/handbook/"


def templates(s: str) -> list[tuple[str, str, str, str, str]]:
    return [
        ("primitives", f"function label{s}(value: String): String {{ return value; }}", f"function label{s}(value: string): string {{ return value; }}", "Use primitive TypeScript types, not boxed object types.", "2/everyday-types.html"),
        ("arrays", f"function total{s}(values: Array<number>) {{ return values.reduce((a, b) => a + b, 0); }}", f"function total{s}(values: number[]): number {{ return values.reduce((a, b) => a + b, 0); }}", "Type an array and declare its numeric return value.", "2/everyday-types.html"),
        ("tuples", f"function pair{s}(): (string | number)[] {{ return ['ok', 200]; }}", f"function pair{s}(): [string, number] {{ return ['ok', 200]; }}", "Use a tuple when positions have distinct types.", "2/objects.html"),
        ("literal", f"function direction{s}(value: string) {{ return value; }}", f"function direction{s}(value: 'up' | 'down'): 'up' | 'down' {{ return value; }}", "Constrain a value with string literal types.", "2/everyday-types.html"),
        ("optional-properties", f"type Config{s} = {{ name: string; enabled: boolean }};", f"type Config{s} = {{ name: string; enabled?: boolean }};", "Model an optional configuration property.", "2/objects.html"),
        ("union", f"function stringify{s}(value: string | number) {{ return value.toUpperCase(); }}", f"function stringify{s}(value: string | number): string {{ return typeof value === 'string' ? value.toUpperCase() : value.toString(); }}", "Narrow a string-or-number union before using a member.", "2/narrowing.html"),
        ("unknown", f"function parse{s}(value: unknown) {{ return value.trim(); }}", f"function parse{s}(value: unknown): string {{ return typeof value === 'string' ? value.trim() : ''; }}", "Handle unknown input without using any.", "2/everyday-types.html"),
        ("predicate", f"function isUser{s}(value: unknown) {{ return !!value; }}", f"function isUser{s}(value: unknown): value is {{ id: string }} {{ return typeof value === 'object' && value !== null && 'id' in value && typeof value.id === 'string'; }}", "Write a user-defined type predicate.", "2/narrowing.html"),
        ("discriminated-union", f"type Event{s} = {{ kind: 'text'; value: string }} | {{ kind: 'count'; value: number }};\nfunction read{s}(event: Event{s}) {{ return event.value.toUpperCase(); }}", f"type Event{s} = {{ kind: 'text'; value: string }} | {{ kind: 'count'; value: number }};\nfunction read{s}(event: Event{s}): string {{ return event.kind === 'text' ? event.value : String(event.value); }}", "Use a discriminant to safely handle a union.", "2/narrowing.html"),
        ("never", f"type State{s} = {{ kind: 'idle' }} | {{ kind: 'done' }};\nfunction assertNever{s}(state: State{s}): never {{ throw new Error(String(state)); }}", f"type State{s} = {{ kind: 'idle' }} | {{ kind: 'done' }};\nfunction assertNever{s}(state: never): never {{ throw new Error('unreachable'); }}", "Use never for an unreachable exhaustive branch.", "2/narrowing.html"),
        ("functions", f"function map{s}(value: string, fn: Function) {{ return fn(value); }}", f"function map{s}<T>(value: string, fn: (value: string) => T): T {{ return fn(value); }}", "Type a callback precisely instead of using Function.", "2/functions.html"),
        ("overloads", f"function parseId{s}(value: string | number) {{ return value; }}", f"function parseId{s}(value: string): string;\nfunction parseId{s}(value: number): number;\nfunction parseId{s}(value: string | number): string | number {{ return value; }}", "Add overload signatures with a compatible implementation.", "2/functions.html"),
        ("generic-constraint", f"function length{s}<T>(value: T): number {{ return value.length; }}", f"function length{s}<T extends {{ length: number }}>(value: T): number {{ return value.length; }}", "Constrain a generic before accessing a property.", "2/generics.html"),
        ("keyof", f"function get{s}<T>(obj: T, key: string) {{ return obj[key]; }}", f"function get{s}<T, K extends keyof T>(obj: T, key: K): T[K] {{ return obj[key]; }}", "Use keyof and indexed access for a type-safe property getter.", "2/indexed-access-types.html"),
        ("conditional", f"type Element{s}<T> = T;", f"type Element{s}<T> = T extends readonly (infer U)[] ? U : T;", "Use a conditional type with infer to unwrap arrays.", "2/conditional-types.html"),
        ("mapped", f"type Optional{s}<T> = T;", f"type Optional{s}<T> = {{ [K in keyof T]?: T[K] }};", "Create a homomorphic mapped type with optional properties.", "2/mapped-types.html"),
        ("template-literal", f"type Changed{s} = string;", f"type Changed{s}<K extends string> = `${{K}}Changed`;", "Build a string template literal type.", "2/template-literal-types.html"),
        ("utility", f"type Update{s} = {{ id: string; name: string; }};", f"type Update{s} = Partial<{{ id: string; name: string }}>;", "Use a standard utility type for partial updates.", "utility-types.html"),
        ("classes", f"class Box{s} {{ value: any; }}", f"class Box{s}<T> {{ constructor(public value: T) {{}} }}", "Make a class generic and avoid any.", "2/classes.html"),
        ("async", f"async function load{s}() {{ return 'ready'; }}", f"async function load{s}(): Promise<string> {{ return 'ready'; }}", "Declare the Promise return type of an async function.", "2/objects.html"),
        ("declaration", f"declare function fetch{s}(url: string): any;", f"declare function fetch{s}(url: string): Promise<{{ ok: boolean }}>;", "Write a precise declaration for an external API.", "declaration-files/by-example.html"),
        ("jsdoc-javascript", f"// @ts-check\n/** @param {{number}} value */\nfunction double{s}(value) {{ return value + 'x'; }}", f"// @ts-check\n/** @param {{number}} value */\nfunction double{s}(value) {{ return value * 2; }}", "Fix a checked JavaScript function using JSDoc types.", "type-checking-javascript-files.html"),
        ("jsdoc-object", f"// @ts-check\n/** @param {{ {{ name: string }} }} user */\nfunction greet{s}(user) {{ return user.name.toUpperCase(); }}", f"// @ts-check\n/** @param {{ {{ name: string }} }} user */\nfunction greet{s}(user) {{ return `Hello ${{user.name}}`; }}", "Preserve a JSDoc object contract in JavaScript.", "jsdoc-supported-types.html"),
        ("js-null-narrowing", f"// @ts-check\n/** @param {{string|null}} value */\nfunction trim{s}(value) {{ return value.trim(); }}", f"// @ts-check\n/** @param {{string|null}} value */\nfunction trim{s}(value) {{ return value === null ? '' : value.trim(); }}", "Narrow nullable JavaScript input under checkJs.", "type-checking-javascript-files.html"),
    ]


def build(index: int) -> dict:
    suffix = f"{index + 1:07d}"
    family, source, completion, instruction, doc = templates(suffix)[index % 24]
    language = "javascript" if family.startswith("js") else "typescript"
    digest = hashlib.sha256(f"{VERSION}:{index}:{source}".encode()).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return {
        "id": f"{VERSION}-{index:07d}",
        "domain": "typescript",
        "language": language,
        "family": family,
        "split": "test" if bucket < 10 else ("validation" if bucket < 25 else "train"),
        "messages": [{"role": "system", "content": f"Return only compiler-valid {language} code in one fenced code block."}, {"role": "user", "content": f"{instruction}\n\n```{language}\n{source}\n```"}],
        "completion": f"```{language}\n{completion}\n```",
        "source_code": source,
        "provenance": {"kind": "handbook-topic-template", "generator": VERSION, "documentation": DOCS + doc, "synthetic": True, "license": "CC0-like project seed"},
    }


def verify(records: list[dict]) -> dict:
    tsc = shutil.which("tsc") or str(ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc")
    if not Path(tsc).exists():
        return {"available": False}
    outcomes = {}
    for language in ("typescript", "javascript"):
        selected = [r for r in records if r["language"] == language]
        if not selected:
            continue
        with tempfile.TemporaryDirectory(prefix=f"oktopai-{language}-") as directory:
            extension = ".ts" if language == "typescript" else ".js"
            path = Path(directory) / f"curriculum{extension}"
            code = "\n\n".join(r["completion"].split("\n", 1)[1].rsplit("\n", 1)[0] for r in selected)
            path.write_text(code, encoding="utf-8")
            command = [tsc, "--noEmit", "--strict", "--target", "ES2020", str(path)]
            if language == "javascript":
                command = [tsc, "--noEmit", "--allowJs", "--checkJs", "--target", "ES2020", str(path)]
            result = subprocess.run(command, capture_output=True, text=True)
            outcomes[language] = {"records": len(selected), "verified": result.returncode == 0, "stderr": result.stderr[-2000:]}
    return {"available": True, "languages": outcomes, "verified": all(item["verified"] for item in outcomes.values())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    records = [build(index) for index in range(args.count)]
    verification = verify(records) if args.verify else {"available": None}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "records": len(records), "output": str(args.output), "verification": verification}, indent=2))
    return 0 if verification.get("verified", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
