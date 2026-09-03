from pathlib import Path
from dataclasses import replace
import tempfile
import unittest
import json
from oktopai.experts import ExpertRegistry
from oktopai.router import Router
from oktopai.signals import detect_signals
from oktopai.sessions import Session
from oktopai.lifecycle import LifecycleManager
from oktopai.benchmarking import verify_output, load_tasks
from oktopai.trajectory import (
    TRAJECTORY_SCHEMA,
    apply_replacements,
    bounded_file_excerpt,
    build_patch_emitter_request,
    diagnostic_file_location,
    diagnostic_file_locations,
    normalize_trajectory,
    validate_trajectory,
)

ROOT = Path(__file__).parents[1]

class OktopaiTests(unittest.TestCase):
    def registry(self): return ExpertRegistry.from_toml(ROOT / "config/experts.toml")
    def test_typescript_route_is_deterministic(self):
        r = Router(self.registry()); s = detect_signals("Fix this TypeScript generic", "src/types.ts")
        self.assertEqual(r.route("Fix this TypeScript generic", s).selected, "typescript")
        self.assertEqual(r.route("Fix this TypeScript generic", s), r.route("Fix this TypeScript generic", s))
    def test_repository_signals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "package.json").write_text('{"dependencies":{"next":"1","react":"1"}}'); (root / "next.config.mjs").write_text("")
            s = detect_signals("Why does this component rerender?", "app/page.tsx", "import React from 'react'", root)
            self.assertIn("react", s.dependencies); self.assertIn("react", s.imports); self.assertIn("next.config.mjs", s.config_files)
    def test_override(self):
        d = Router(self.registry()).route("anything", detect_signals("anything"), "testing")
        self.assertEqual(d.selected, "testing"); self.assertTrue(d.override)
    def test_shared_model_lifecycle_reuses(self):
        class Fake:
            def __init__(self): self.loaded=set(); self.preloads=[]; self.unloads=[]
            def list_models(self): return []
            def is_loaded(self, m): return m in self.loaded
            def preload(self, m, keep_alive=900): self.loaded.add(m); self.preloads.append(m); return 1
            def unload(self, m): self.loaded.discard(m); self.unloads.append(m); return 1
        registry = self.registry(); registry.experts["react"] = replace(registry.experts["react"], model="oktopai-typescript")
        f = Fake(); l = LifecycleManager(f, registry, max_warm_models=1)
        l.ensure_warm("typescript"); l.ensure_warm("react")
        self.assertEqual(f.preloads, ["oktopai-typescript"]); self.assertEqual(f.unloads, [])
    def test_lru_eviction_for_distinct_models(self):
        class Fake:
            def __init__(self): self.loaded=set(); self.unloads=[]
            def list_models(self): return []
            def is_loaded(self, m): return m in self.loaded
            def preload(self, m, keep_alive=900): self.loaded.add(m); return 1
            def unload(self, m): self.loaded.discard(m); self.unloads.append(m); return 1
        registry = self.registry(); experts = list(registry.experts.values())
        registry.experts[experts[1].name] = experts[1].__class__(**{**experts[1].__dict__, "model": "model-a"})
        registry.experts[experts[2].name] = experts[2].__class__(**{**experts[2].__dict__, "model": "model-b"})
        fake = Fake(); lifecycle = LifecycleManager(fake, registry, max_warm_models=1)
        lifecycle.ensure_warm(experts[1].name); lifecycle.ensure_warm(experts[2].name)
        self.assertEqual(fake.unloads, ["model-a"])
    def test_session_reconstruction_and_budget(self):
        s = Session(context_budget=30); s.add_user("hello"); s.add_file("x.ts", "const value = 123456789")
        self.assertEqual(s.prompt("system")[0]["role"], "system"); self.assertIn("truncated", s.prompt("system")[0]["content"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.json"; s.save(path); self.assertEqual(Session.load(path).messages, s.messages)
    def test_missing_runtime_is_actionable(self):
        from oktopai.runtimes.base import RuntimeUnavailable
        from oktopai.runtimes.ollama import OllamaRuntime
        with self.assertRaises(RuntimeUnavailable) as caught: OllamaRuntime("http://127.0.0.1:1").list_models()
        self.assertIn("ollama", str(caught.exception).lower())
    def test_benchmark_checklist_and_python_verification(self):
        result = verify_output("Use keyof T and T[K]", {"required":["keyof","T[K]"],"forbidden":["any"],"mode":"checklist"})
        self.assertEqual(result.status, "checklist_pass")
        result = verify_output("```python\ndef answer():\n    return 1\n```", {"required":["def answer"],"mode":"python_compile"})
        self.assertEqual(result.status, "verified"); self.assertTrue(result.executable)
        result = verify_output("```sql\nSELECT c.id, c.name FROM customers c LEFT JOIN orders o ON o.customer_id = c.id WHERE o.id IS NULL ORDER BY c.id;\n```", {"required":["IS NULL"],"expected_rows":[(0, "Zero"), (2, "Grace")],"mode":"sql_fixture"})
        self.assertEqual(result.status, "verified"); self.assertTrue(result.executable)
    def test_benchmark_dataset_is_versioned(self):
        tasks = load_tasks(ROOT / "benchmarks/tasks.json")
        self.assertGreaterEqual(len(tasks), 8); self.assertTrue(all("id" in task and "checks" in task for task in tasks))

    def test_trajectory_contract_rejects_unsafe_commands(self):
        record = {"task": "x", "repository_facts": {}, "trajectory": [
            {"event": "diagnose", "tool": "run", "args": {"command": "rm -rf ."}},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": ""}},
            {"event": "final", "content": "done"},
        ]}
        self.assertTrue(any(issue.code == "unsafe_command" for issue in validate_trajectory(record)))

    def test_trajectory_contract_rejects_shell_chaining_and_path_traversal(self):
        record = {"task": "x", "repository_facts": {}, "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "..\\secret.ts"}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit && rm -rf tmp"}},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": "const x = 1;"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "done"},
        ]}
        codes = {issue.code for issue in validate_trajectory(record)}
        self.assertIn("unsafe_path", codes)
        self.assertIn("unsafe_command", codes)

    def test_trajectory_edit_content_preserves_real_newlines(self):
        record = {"task": "x", "repository_facts": {}, "trajectory": [
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": "const x = 1;\n"}},
            {"event": "final", "content": "done"},
        ]}
        self.assertEqual(record["trajectory"][0]["args"]["content"][-1], "\n")
        self.assertNotIn("\\n", record["trajectory"][0]["args"]["content"])

    def test_trajectory_requires_successful_post_edit_verification(self):
        record = {"task": "x", "repository_facts": {}, "trajectory": [
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": "const x = 1;"}},
            {"event": "final", "content": "done"},
        ]}
        self.assertTrue(any(issue.code == "missing_successful_verification" for issue in validate_trajectory(record)))

    def test_trajectory_requires_diagnosis_before_and_after_edit(self):
        record = {"task": "x", "repository_facts": {}, "trajectory": [
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": "const x = 1;"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "done"},
        ]}
        codes = {issue.code for issue in validate_trajectory(record)}
        self.assertIn("missing_pre_edit_diagnosis", codes)
        self.assertIn("missing_post_edit_diagnosis", codes)

    def test_trajectory_rejects_truncated_large_file_content(self):
        record = {"task": "x", "repository_facts": {}, "repository_files": {"src/main.tsx": "x" * 1024}, "trajectory": [
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/main.tsx", "content": "const x = 1;"}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "done"},
        ]}
        self.assertTrue(any(issue.code == "incomplete_edit_content" for issue in validate_trajectory(record)))

    def test_exact_replacements_are_once_only(self):
        self.assertEqual(apply_replacements("const x = 1;", [{"old": "1", "new": "2"}]), "const x = 2;")
        with self.assertRaises(ValueError):
            apply_replacements("x x", [{"old": "x", "new": "y"}])
        with self.assertRaises(ValueError):
            apply_replacements("x", [{"old": "z", "new": "y"}])
        with self.assertRaises(ValueError):
            apply_replacements("x", [{"old": "x", "new": "x"}])

    def test_validator_rejects_noop_replacement(self):
        record = {"repository_facts": {}, "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "src/index.ts"}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "replacements": [{"old": "bad", "new": "bad"}]}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "done"},
        ]}
        issues = validate_trajectory(record)
        self.assertTrue(any(issue.code == "invalid_replacement" for issue in issues))

    def test_replacement_trajectory_replays_through_synthetic_verifier(self):
        from scripts.verify_trajectory import replay
        record = {"task": "replace", "repository_facts": {}, "repository_files": {"src/index.ts": 'const x: number = "bad";\n'}, "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "src/index.ts"}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "replacements": [{"old": '"bad"', "new": "1"}]}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "Replaced the invalid literal and verified compilation."},
        ]}
        self.assertEqual(replay(record, str(ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc")), [])

    def test_trajectory_normalizer_only_moves_unambiguous_arguments(self):
        value = {"trajectory": [{"event": "diagnose", "command": "tsc --noEmit", "path": "ignored"}]}
        normalized = normalize_trajectory(value)
        self.assertEqual(normalized["trajectory"][0]["tool"], "run")
        self.assertEqual(normalized["trajectory"][0]["args"]["command"], "tsc --noEmit")
        self.assertEqual(normalized["trajectory"][0]["args"]["path"], "ignored")
        self.assertNotIn("command", normalized["trajectory"][0])

    def test_trajectory_normalizer_cleans_known_model_serialization(self):
        value = {"trajectory": [{"event": "diagnose", "tool": "run", "command": "tsc --noEmit using tsconfig.json"}, {"event": "edit", "tool": "apply_patch", "path": "src/index.ts", "content": "const x = 1;\\n"}]}
        normalized = normalize_trajectory(value)
        self.assertEqual(normalized["trajectory"][0]["args"]["command"], "tsc --noEmit")
        self.assertEqual(normalized["trajectory"][1]["args"]["content"], "const x = 1;\n")

    def test_trajectory_schema_requires_nested_tool_arguments(self):
        self.assertIn("args.replacements", TRAJECTORY_SCHEMA["edit"])
        self.assertIn("exactly once", TRAJECTORY_SCHEMA["replacements"])
        self.assertIn("exact-replacements", TRAJECTORY_SCHEMA["large_file_edit"])
        self.assertIn("complete target file", TRAJECTORY_SCHEMA["edit_content_completeness"])
        self.assertIn("args.command", TRAJECTORY_SCHEMA["diagnose"])
        self.assertIn("exit_code 0", TRAJECTORY_SCHEMA["verification"])
        self.assertIn("first key", TRAJECTORY_SCHEMA["outer_envelope"])

    def test_trajectory_evaluator_family_summary(self):
        from scripts.evaluate_trajectory_adapter import summarize_results
        results = [{"family": "union", "adapter": {"parsed": {}, "raw_contract_valid": True, "contract_valid": True, "normalization_applied": False}}]
        self.assertEqual(summarize_results(results, "adapter")["union"]["contract_valid"], 1)

    def test_source_trajectory_admission_requires_license_and_snapshot(self):
        from scripts.inventory_trajectory_datasets import is_admissible_source_record
        record = {"trajectory": [{"event": "inspect"}], "repository_files": {"src/index.ts": ""}, "provenance": {"kind": "public-github", "repository": "org/repo"}}
        self.assertFalse(is_admissible_source_record(record))
        record["provenance"]["license_spdx_id"] = "MIT"
        self.assertTrue(is_admissible_source_record(record))

    def test_patch_emitter_context_is_bounded_and_numbered(self):
        source = "".join(f"const line{n} = {n};\n" for n in range(1, 40))
        excerpt = bounded_file_excerpt(source, 20, radius=2, max_chars=200)
        self.assertIn("18: const line18", excerpt)
        self.assertIn("20: const line20", excerpt)
        self.assertLessEqual(len(excerpt), 200)
        self.assertNotIn("1: const line1", excerpt)

    def test_patch_emitter_request_excludes_complete_snapshot(self):
        record = {
            "task": "Fix the type error.",
            "repository_facts": {"compiler": "typescript"},
            "repository_files": {"src/index.ts": "const value: number = 'bad';\n"},
        }
        diagnostic = "src/index.ts(1,7): error TS2322: Type 'string' is not assignable to type 'number'."
        self.assertEqual(diagnostic_file_location(diagnostic), ("src/index.ts", 1, 7))
        request = build_patch_emitter_request(record, diagnostic)
        self.assertIn("file_context", request["target"])
        self.assertNotIn("repository_files", request)
        self.assertIn("1: const value", request["target"]["file_context"])

    def test_patch_emitter_request_bounds_large_snapshot_content(self):
        source = "".join(f"const unchanged{n} = {n};\n" for n in range(500))
        record = {"task": "Fix the type error.", "repository_facts": {"large_file": True}, "repository_files": {"src/index.ts": source}}
        request = build_patch_emitter_request(record, "src/index.ts(250,7): error TS2322: repair required", radius=4, max_chars=400)
        prompt = json.dumps(request)
        self.assertLess(len(prompt), 1600)
        self.assertNotIn("const unchanged1 = 1;", prompt)
        self.assertIn("250: const unchanged249", prompt)

    def test_patch_emitter_context_covers_all_diagnostic_locations(self):
        source = "".join(f"const line{n} = {n};\n" for n in range(1, 30))
        diagnostic = "src/index.ts(10,2): error TS2322: first\nsrc/index.ts(14,3): error TS2345: second"
        self.assertEqual(diagnostic_file_locations(diagnostic), [("src/index.ts", 10, 2), ("src/index.ts", 14, 3)])
        request = build_patch_emitter_request({"task": "x", "repository_files": {"src/index.ts": source}}, diagnostic)
        self.assertIn("8: const line8", request["target"]["file_context"])
        self.assertIn("16: const line16", request["target"]["file_context"])
        self.assertEqual(request["target"]["diagnostic_locations"], [{"line": 10, "column": 2}, {"line": 14, "column": 3}])
        self.assertIn("earlier expression", request["target"]["source_localization_rule"])
        self.assertIn("downstream", request["patch_emitter_contract"]["diagnostic_alignment"])

if __name__ == "__main__": unittest.main()
