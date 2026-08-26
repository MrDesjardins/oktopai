# Tool-using specialist models

## Decision

Oktopai specialists are not only code-completion models. A useful specialist
must inspect a repository, choose the smallest appropriate tool, interpret its
result, make a bounded change, and verify the result. This is a core
requirement for TypeScript and will be reused for Python, CSS, SQL, Next.js,
and other specialists.

The target is compatibility with agent hosts such as OpenCode, Codex-style
loops, and oktopai itself. Oktopai remains host-neutral: the specialist emits
structured tool intentions and arguments, while the host owns permissions,
execution, cancellation, and output sanitization.

## TypeScript tool contract

The initial TypeScript specialist should learn a stable vocabulary:

| Tool class | Examples | Expected evidence |
| --- | --- | --- |
| Inspect | list/read files, search symbols/imports, inspect `package.json` and lockfiles | relevant paths, versions, dependencies |
| Diagnose | `tsc --noEmit`, project typecheck, eslint, test runner | exact command, exit code, diagnostics |
| Edit | apply a minimal patch or create a file | changed paths and concise diff |
| Validate | rerun compiler, focused test, lint, then broader checks | commands and pass/fail results |
| Explain | summarize cause, fix, risks, and next action | claims linked to evidence |

The model should prefer repository-local scripts and package-manager commands,
identify the package manager from lockfiles, respect workspace boundaries,
avoid destructive commands, and ask for approval when a command could delete
data, publish code, or access a network resource.

## Training records

Tool-use records preserve more than a final answer:

```json
{
  "task": "Fix the generic constraint error in src/types.ts",
  "repository_facts": {"package_manager": "pnpm", "strict": true},
  "trajectory": [
    {"tool": "read_file", "args": {"path": "src/types.ts"}, "result_summary": "..."},
    {"tool": "run", "args": {"command": "pnpm exec tsc --noEmit"}, "exit_code": 1},
    {"tool": "apply_patch", "args": {"path": "src/types.ts", "patch": "..."}},
    {"tool": "run", "args": {"command": "pnpm exec tsc --noEmit"}, "exit_code": 0}
  ],
  "final": "The constraint was widened because ...",
  "verification": {"compiler": "pass", "tests": "pass"}
}
```

Raw teacher trajectories are candidates, not truth. The verifier rejects
fabricated tool results, missing files, invalid patches, failed compilation,
and claims unsupported by command output. Rejected traces remain useful as
negative or preference data when their failure reason is known.

## Dataset curriculum

1. Single-tool tasks: inspect a file, explain a diagnostic, or choose a command.
2. Two-step repairs: inspect then patch; patch then compile.
3. Multi-step repairs: diagnose, edit several files, and run focused tests.
4. Recovery tasks: respond to failed commands, stale assumptions, or bad imports.
5. Host integration: operate through an OpenCode/agent-style schema and stop
   when verification passes.
6. Preference pairs: compare minimal verified repairs against verbose, unsafe,
   tool-inventing, or unverified alternatives.

Balance records across generics, narrowing, module resolution, configuration,
monorepos, migrations, React/Next.js TypeScript, tests, and package managers.
Hold out entire repositories and task templates, not just random rows.

## Evaluation gates

Every specialist benchmark reports both code quality and tool behavior:

- tool-selection accuracy and unnecessary-tool rate;
- first useful action and total trajectory latency;
- strict compiler, lint, and focused-test pass rates;
- patch minimality and files changed;
- recovery rate after an intentionally failed command;
- unsafe-command and unsupported-claim rates;
- final answer grounded in captured evidence;
- single-model versus hot-swapped specialist performance.

Token/second is useful but secondary to verified task completion. Parallel
requests can improve aggregate throughput, while one agent trajectory usually
needs ordered tool calls. Report both per-request and end-to-end repair timing.

## Architecture boundary

The model does not receive unrestricted shell access by default. Oktopai or
the host adapter provides typed tools, enforces an allowlist, redacts secrets,
caps output, and records every event. The same specialist can therefore run
under OpenCode, Codex-like hosts, or a future oktopai agent loop without being
trained around one proprietary API.

## Future specialists

- Python: `pytest`, `ruff`, `mypy`, package metadata, and virtual-environment facts.
- CSS: browser/snapshot fixtures, style lint, accessibility, and computed layout.
- SQL: schema inspection, explain plans, dialect checks, and safe read-only execution.
- Next.js: TypeScript compiler, framework build, server/client checks, and tests.

The adapter is judged as a tool-using policy over a shared interface, not just
as a domain-flavored text generator.
