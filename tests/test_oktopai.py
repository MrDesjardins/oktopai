from pathlib import Path
from dataclasses import replace
import tempfile
import unittest
from oktopai.experts import ExpertRegistry
from oktopai.router import Router
from oktopai.signals import detect_signals
from oktopai.sessions import Session
from oktopai.lifecycle import LifecycleManager
from oktopai.benchmarking import verify_output, load_tasks

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

if __name__ == "__main__": unittest.main()
